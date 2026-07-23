"""Read-only B-rep topology, continuity, and protected-surface audit."""

from __future__ import annotations


# This guard must remain before all native CAD/threaded-library imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

from build123d import GeomType, Vector, import_step
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepLProp import BRepLProp_SLProps
from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCP.TopAbs import TopAbs_REVERSED
from OCP.gp import gp_Pnt


ROOT = Path(__file__).resolve().parents[3]
CURRENT_ROOT = (
    ROOT
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
CANDIDATE_ROOT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/trimmed_candidate"
)
UNSPLICED_ROOT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/candidate"
)
CANONICAL_ROOT = (
    ROOT
    / "workbench/designs/canonical_working_set/enclosures/"
    "removable_front_baffle/links"
)
INPUTS = {
    "current_bucket": CURRENT_ROOT / "simple_tongue_groove_bucket.step",
    "current_baffle": CURRENT_ROOT / "simple_tongue_groove_baffle.step",
    "candidate_bucket": CANDIDATE_ROOT / "trimmed_unspliced_bucket.step",
    "candidate_baffle": CANDIDATE_ROOT / "trimmed_unspliced_baffle.step",
    "unspliced_bucket": UNSPLICED_ROOT / "unspliced_exact_edge_bucket.step",
    "unspliced_baffle": UNSPLICED_ROOT / "unspliced_exact_edge_baffle.step",
    "earlier_flat_baffle": CANONICAL_ROOT / "flat_bottom_baffle.step",
    "accepted_sculpted_bucket": CANONICAL_ROOT / "near_perfect_bucket.step",
}
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/"
    "exported_topology_audit.json"
)
SOLE_Z_MM = -91.495


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _normal(face: Any, point: Vector) -> tuple[float, float, float]:
    surface = BRep_Tool.Surface_s(face.wrapped)
    projection = GeomAPI_ProjectPointOnSurf(
        gp_Pnt(point.X, point.Y, point.Z),
        surface,
    )
    if projection.NbPoints() < 1:
        raise ValueError("Unable to project point onto face surface")
    u_value, v_value = projection.LowerDistanceParameters()
    properties = BRepLProp_SLProps(
        BRepAdaptor_Surface(face.wrapped),
        u_value,
        v_value,
        1,
        1e-8,
    )
    if not properties.IsNormalDefined():
        raise ValueError("Surface normal is undefined")
    normal = properties.Normal()
    vector = [normal.X(), normal.Y(), normal.Z()]
    if face.wrapped.Orientation() == TopAbs_REVERSED:
        vector = [-component for component in vector]
    length = math.sqrt(sum(component * component for component in vector))
    return tuple(component / length for component in vector)


def _angle_deg(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> float:
    cosine = sum(a * b for a, b in zip(first, second))
    cosine = max(-1.0, min(1.0, abs(cosine)))
    return math.degrees(math.acos(cosine))


def _distance(shape: Any, point: Vector) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(shape.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        raise ValueError("Shape-to-point distance calculation failed")
    return tool.Value()


def _distance_to_face(face: Any, point: Vector) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(face.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        return math.inf
    return tool.Value()


def _adjacent_faces(shape: Any, edge: Any) -> list[Any]:
    return [
        face
        for face in shape.faces()
        if any(candidate.wrapped.IsSame(edge.wrapped) for candidate in face.edges())
    ]


def _edge_record(shape: Any, edge: Any) -> dict[str, Any]:
    bounds = edge.bounding_box()
    center = edge.position_at(0.5)
    faces = _adjacent_faces(shape, edge)
    record: dict[str, Any] = {
        "geom_type": edge.geom_type.name,
        "center_mm": [center.X, center.Y, center.Z],
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "length_mm": edge.length,
        "adjacent_face_count": len(faces),
    }
    if len(faces) == 2:
        normals = [_normal(face, center) for face in faces]
        record["adjacent_face_geom_types"] = [
            face.geom_type.name for face in faces
        ]
        record["adjacent_normals"] = [list(normal) for normal in normals]
        record["normal_change_deg"] = _angle_deg(normals[0], normals[1])
    return record


def _lower_horizontal_edges(shape: Any) -> list[dict[str, Any]]:
    records = []
    for edge in shape.edges():
        bounds = edge.bounding_box()
        if (
            bounds.size.X >= 20.0
            and bounds.size.Z <= 0.02
            and bounds.max.Z <= -70.0
        ):
            records.append(_edge_record(shape, edge))
    return sorted(
        records,
        key=lambda item: (
            round(item["center_mm"][2], 5),
            round(item["center_mm"][1], 5),
            round(item["center_mm"][0], 5),
        ),
    )


def _visible_unrelated_lower_edges(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if (
            record["bounds_mm"]["min"][1] < -80.0
            and record["bounds_mm"]["size"][0] >= 40.0
            and record["center_mm"][2] > SOLE_Z_MM + 0.05
        )
    ]


def _old_splice_edges(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if (
            abs(record["center_mm"][2] + 80.1) <= 0.15
            and record["bounds_mm"]["min"][1] < -80.0
        )
    ]


def _sole_edges(shape: Any) -> list[dict[str, Any]]:
    records = []
    for edge in shape.edges():
        bounds = edge.bounding_box()
        if (
            bounds.size.Z <= 0.02
            and abs(bounds.min.Z - SOLE_Z_MM) <= 0.02
            and abs(bounds.max.Z - SOLE_Z_MM) <= 0.02
        ):
            records.append(_edge_record(shape, edge))
    return records


def _face_type_counts(shape: Any) -> dict[str, int]:
    return dict(sorted(Counter(face.geom_type.name for face in shape.faces()).items()))


def _topology(shape: Any) -> dict[str, Any]:
    bounds = shape.bounding_box()
    lower_edges = _lower_horizontal_edges(shape)
    return {
        "solid_count": len(shape.solids()),
        "all_solids_valid": all(solid.is_valid for solid in shape.solids()),
        "volume_mm3": _shape_volume(shape),
        "face_count": len(shape.faces()),
        "edge_count": len(shape.edges()),
        "vertex_count": len(shape.vertices()),
        "face_geom_type_counts": _face_type_counts(shape),
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "lower_horizontal_edges": lower_edges,
        "visible_unrelated_lower_edges": _visible_unrelated_lower_edges(
            lower_edges
        ),
        "old_splice_edges": _old_splice_edges(lower_edges),
    }


def _visible_faces(shape: Any) -> list[Any]:
    return [
        face
        for face in shape.faces()
        if (
            face.bounding_box().min.Y < -80.0
            and face.bounding_box().max.Z > SOLE_Z_MM + 0.01
            and not (
                face.geom_type == GeomType.PLANE
                and face.bounding_box().size.Z <= 0.02
                and abs(face.center().Z - SOLE_Z_MM) <= 0.02
            )
        )
    ]


def _sample_points(faces: list[Any]) -> list[tuple[Any, Vector]]:
    samples: list[tuple[Any, Vector]] = []
    seen: set[tuple[float, float, float]] = set()
    for face in faces:
        points = [face.center()]
        for edge in face.edges():
            points.extend(edge.position_at(value) for value in (0.25, 0.5, 0.75))
        for point in points:
            if point.Z <= SOLE_Z_MM + 0.01:
                continue
            key = (round(point.X, 5), round(point.Y, 5), round(point.Z, 5))
            if key in seen:
                continue
            seen.add(key)
            samples.append((face, point))
    return samples


def _interior_samples(faces: list[Any]) -> list[tuple[Any, Vector]]:
    samples: list[tuple[Any, Vector]] = []
    for face in faces:
        for u_value in (0.25, 0.5, 0.75):
            for v_value in (0.25, 0.5, 0.75):
                point = face.position_at(u_value, v_value)
                # UV bounds belong to the underlying surface, so a location can
                # fall outside a trimmed face. Keep only points on the face.
                if _distance_to_face(face, point) <= 1e-7:
                    samples.append((face, point))
    return samples


def _surface_deviation(
    source_shape: Any,
    target_shape: Any,
) -> dict[str, Any]:
    source_faces = _visible_faces(source_shape)
    target_faces = _visible_faces(target_shape)
    samples = _sample_points(source_faces)
    interior_samples = _interior_samples(source_faces)
    distances = []
    normal_angles = []
    for _source_face, point in samples:
        distance = _distance(target_shape, point)
        distances.append(distance)
    ambiguous_normal_samples = 0
    for source_face, point in interior_samples:
        ranked_faces = sorted(
            (
                (_distance_to_face(face, point), face)
                for face in target_faces
            ),
            key=lambda item: item[0],
        )
        if not ranked_faces or ranked_faces[0][0] > 0.01:
            continue
        if (
            len(ranked_faces) > 1
            and ranked_faces[1][0] - ranked_faces[0][0] <= 1e-7
        ):
            ambiguous_normal_samples += 1
            continue
        nearest_face = ranked_faces[0][1]
        normal_angles.append(
            _angle_deg(
                _normal(source_face, point),
                _normal(nearest_face, point),
            )
        )
    return {
        "source_visible_face_count": len(source_faces),
        "target_visible_face_count": len(target_faces),
        "sample_count": len(samples),
        "interior_normal_sample_count": len(normal_angles),
        "ambiguous_normal_sample_count": ambiguous_normal_samples,
        "maximum_point_deviation_mm": max(distances, default=0.0),
        "mean_point_deviation_mm": (
            sum(distances) / len(distances) if distances else 0.0
        ),
        "maximum_sampled_normal_change_deg": max(normal_angles, default=0.0),
        "mean_sampled_normal_change_deg": (
            sum(normal_angles) / len(normal_angles) if normal_angles else 0.0
        ),
    }


def main() -> None:
    missing = [str(path) for path in INPUTS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing topology-audit inputs: {missing}")
    shapes = {name: import_step(path) for name, path in INPUTS.items()}
    records = {name: _topology(shape) for name, shape in shapes.items()}
    result = {
        "inputs": {
            name: str(path.relative_to(ROOT)) for name, path in INPUTS.items()
        },
        "topology": records,
        "candidate_baffle_sole_edges": _sole_edges(
            shapes["candidate_baffle"]
        ),
        "protected_visible_surface_deviation": {
            "candidate_baffle_to_unspliced_donor": _surface_deviation(
                shapes["candidate_baffle"],
                shapes["unspliced_baffle"],
            ),
            "unspliced_donor_to_candidate_baffle": _surface_deviation(
                shapes["unspliced_baffle"],
                shapes["candidate_baffle"],
            ),
            "candidate_bucket_to_unspliced_bucket": _surface_deviation(
                shapes["candidate_bucket"],
                shapes["unspliced_bucket"],
            ),
            "unspliced_bucket_to_candidate_bucket": _surface_deviation(
                shapes["unspliced_bucket"],
                shapes["candidate_bucket"],
            ),
        },
        "acceptance_summary": {
            "candidate_baffle_old_splice_edge_count": len(
                records["candidate_baffle"]["old_splice_edges"]
            ),
            "candidate_bucket_old_splice_edge_count": len(
                records["candidate_bucket"]["old_splice_edges"]
            ),
            "candidate_baffle_visible_unrelated_lower_edge_count": len(
                records["candidate_baffle"]["visible_unrelated_lower_edges"]
            ),
            "candidate_bucket_visible_unrelated_lower_edge_count": len(
                records["candidate_bucket"]["visible_unrelated_lower_edges"]
            ),
            "current_baffle_old_splice_edge_count": len(
                records["current_baffle"]["old_splice_edges"]
            ),
            "current_bucket_old_splice_edge_count": len(
                records["current_bucket"]["old_splice_edges"]
            ),
        },
    }
    path = job_output_path(OUTPUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
