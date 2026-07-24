"""Fit, seal and protected-visible-surface audit for the production candidate."""

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

import json
import math
import sys
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


ROOT = _CAD_SAFETY_ROOT
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
import validate_simple_tongue_groove_baffle as validator  # noqa: E402


CANDIDATE = ROOT / "build/workbench/variant_r_no_splice_production/candidate"
OUTPUT = ROOT / "build/workbench/variant_r_no_splice_production/fit-audit.json"


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _distance(shape: Any, point: Vector) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(shape.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        raise ValueError("shape-to-point distance calculation failed")
    return tool.Value()


def _distance_to_face(face: Any, point: Vector) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(face.wrapped, vertex)
    tool.Perform()
    return tool.Value() if tool.IsDone() else math.inf


def _normal(face: Any, point: Vector) -> tuple[float, float, float]:
    surface = BRep_Tool.Surface_s(face.wrapped)
    projection = GeomAPI_ProjectPointOnSurf(
        gp_Pnt(point.X, point.Y, point.Z),
        surface,
    )
    if projection.NbPoints() < 1:
        raise ValueError("surface projection failed")
    u_value, v_value = projection.LowerDistanceParameters()
    properties = BRepLProp_SLProps(
        BRepAdaptor_Surface(face.wrapped),
        u_value,
        v_value,
        1,
        1e-8,
    )
    if not properties.IsNormalDefined():
        raise ValueError("surface normal is undefined")
    normal = properties.Normal()
    vector = [normal.X(), normal.Y(), normal.Z()]
    if face.wrapped.Orientation() == TopAbs_REVERSED:
        vector = [-component for component in vector]
    length = math.sqrt(sum(component * component for component in vector))
    return tuple(component / length for component in vector)


def _angle_deg(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    cosine = abs(sum(a * b for a, b in zip(left, right, strict=True)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _visible_faces(shape: Any) -> list[Any]:
    sole_z_mm = model.BAFFLE_PLANAR_SOLE_Z_MM
    return [
        face
        for face in shape.faces()
        if (
            face.bounding_box().min.Y < -80.0
            and face.bounding_box().max.Z > sole_z_mm + 0.01
            and not (
                face.geom_type == GeomType.PLANE
                and face.bounding_box().size.Z <= 0.02
                and abs(face.center().Z - sole_z_mm) <= 0.02
            )
        )
    ]


def _protected_surface_deviation(source: Any, target: Any) -> dict[str, Any]:
    source_faces = _visible_faces(source)
    target_faces = _visible_faces(target)
    points: list[tuple[Any, Vector]] = []
    seen: set[tuple[float, float, float]] = set()
    for face in source_faces:
        candidates = [face.center()]
        for edge in face.edges():
            candidates.extend(edge.position_at(value) for value in (0.25, 0.5, 0.75))
        for point in candidates:
            if point.Z <= model.BAFFLE_PLANAR_SOLE_Z_MM + 0.01:
                continue
            key = (round(point.X, 5), round(point.Y, 5), round(point.Z, 5))
            if key not in seen:
                seen.add(key)
                points.append((face, point))

    distances = [_distance(target, point) for _face, point in points]
    normal_changes = []
    ambiguous = 0
    for source_face in source_faces:
        for u_value in (0.25, 0.5, 0.75):
            for v_value in (0.25, 0.5, 0.75):
                point = source_face.position_at(u_value, v_value)
                if (
                    point.Z <= model.BAFFLE_PLANAR_SOLE_Z_MM + 0.01
                    or _distance_to_face(source_face, point) > 1e-7
                ):
                    continue
                ranked = sorted(
                    (
                        (_distance_to_face(face, point), face)
                        for face in target_faces
                    ),
                    key=lambda item: item[0],
                )
                if not ranked or ranked[0][0] > 0.01:
                    continue
                if (
                    len(ranked) > 1
                    and ranked[1][0] - ranked[0][0] <= 1e-7
                ):
                    ambiguous += 1
                    continue
                normal_changes.append(
                    _angle_deg(
                        _normal(source_face, point),
                        _normal(ranked[0][1], point),
                    )
                )
    return {
        "source_visible_face_count": len(source_faces),
        "target_visible_face_count": len(target_faces),
        "point_sample_count": len(points),
        "interior_normal_sample_count": len(normal_changes),
        "ambiguous_normal_sample_count": ambiguous,
        "maximum_point_deviation_mm": max(distances, default=0.0),
        "mean_point_deviation_mm": (
            sum(distances) / len(distances) if distances else 0.0
        ),
        "maximum_sampled_normal_change_deg": max(
            normal_changes,
            default=0.0,
        ),
        "mean_sampled_normal_change_deg": (
            sum(normal_changes) / len(normal_changes)
            if normal_changes
            else 0.0
        ),
    }


def main() -> None:
    paths = {
        "bucket": CANDIDATE / "production_candidate_bucket.step",
        "baffle": CANDIDATE / "production_candidate_baffle.step",
        "gasket": CANDIDATE / "production_candidate_gasket.step",
        "assembly": CANDIDATE / "production_candidate_assembly.step",
        "donor_bucket": CANDIDATE / "continuous_donor_bucket.step",
        "donor_baffle": CANDIDATE / "continuous_donor_baffle.step",
    }
    diagnostics_path = CANDIDATE / "candidate_diagnostics.json"
    missing = [
        str(path)
        for path in (*paths.values(), diagnostics_path)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"missing production-candidate inputs: {missing}")
    shapes = {name: import_step(path) for name, path in paths.items()}
    for name in ("bucket", "baffle", "gasket", "donor_bucket", "donor_baffle"):
        if len(shapes[name].solids()) != 1 or not shapes[name].is_valid:
            raise ValueError(f"{name} is not one valid imported solid")
    assembly_solids = tuple(shapes["assembly"].solids())
    if len(assembly_solids) != 3 or not all(
        solid.is_valid for solid in assembly_solids
    ):
        raise ValueError("candidate assembly is not three valid solids")

    source_diagnostics = json.loads(diagnostics_path.read_text())
    apply, restore, _originals = validator._patch_seam()
    apply()
    try:
        flat_bottom = validator._flat_bottom_audit(shapes)
        print_contact = validator._baffle_print_contact_audit(shapes["baffle"])
    finally:
        restore()

    overlap = {
        "bucket_baffle_mm3": _shape_volume(
            shapes["bucket"].intersect(shapes["baffle"])
        ),
        "gasket_bucket_mm3": _shape_volume(
            shapes["gasket"].intersect(shapes["bucket"])
        ),
        "gasket_baffle_mm3": _shape_volume(
            shapes["gasket"].intersect(shapes["baffle"])
        ),
    }
    if max(overlap.values()) > 0.001:
        raise ValueError(f"candidate pairwise overlap exceeds contract: {overlap}")

    support = {
        "bucket_ratio": source_diagnostics["joint_audit"][
            "gasket_bucket_support_ratio"
        ],
        "baffle_ratio": source_diagnostics["joint_audit"][
            "gasket_baffle_support_ratio"
        ],
    }
    if support != {"bucket_ratio": 1.0, "baffle_ratio": 1.0}:
        raise ValueError(f"candidate gasket support is not full: {support}")

    deviation = {
        "baffle_to_continuous_donor": _protected_surface_deviation(
            shapes["baffle"],
            shapes["donor_baffle"],
        ),
        "continuous_donor_to_baffle": _protected_surface_deviation(
            shapes["donor_baffle"],
            shapes["baffle"],
        ),
        "bucket_to_continuous_donor": _protected_surface_deviation(
            shapes["bucket"],
            shapes["donor_bucket"],
        ),
        "continuous_donor_to_bucket": _protected_surface_deviation(
            shapes["donor_bucket"],
            shapes["bucket"],
        ),
    }
    if max(
        record["maximum_point_deviation_mm"] for record in deviation.values()
    ) > 0.01:
        raise ValueError(f"protected visible-surface deviation failed: {deviation}")

    result = {
        "scope": "production candidate fit, seal and protected-surface audit",
        "single_valid_solid": {
            "bucket": True,
            "baffle": True,
            "gasket": True,
        },
        "assembly_three_valid_solids": True,
        "pairwise_overlap": overlap,
        "flat_bottom_and_seal_continuity": flat_bottom,
        "baffle_print_contact": print_contact,
        "gasket_support": support,
        "protected_visible_surface_deviation": deviation,
        "named_wall_thickness_mm": {
            "baffle_structure": model.BAFFLE_STRUCTURE_THICKNESS_MM,
            "sand_cap": model.SAND_CAP_THICKNESS_MM,
            "bucket_shoulder": model.BUCKET_SHOULDER_THICKNESS_MM,
        },
        "bottom_ownership": source_diagnostics["construction"],
        "topology": source_diagnostics["topology"],
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
