"""Measure the exact exported Variant R baffle bed-contact contract."""

from __future__ import annotations

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
from pathlib import Path

from build123d import GeomType, import_step


ROOT = Path(__file__).resolve().parents[3]
BAFFLE_STEP = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
    / "simple_tongue_groove_baffle.step"
)
REFERENCE_STEP = (
    ROOT
    / "workbench"
    / "designs"
    / "canonical_working_set"
    / "enclosures"
    / "removable_front_baffle"
    / "links"
    / "flat_bottom_baffle.step"
)
OUT = (
    ROOT
    / "build"
    / "workbench"
    / "variant_r_flat_bottom_synthesis"
    / "print_contact"
)
DIAGNOSTICS_PATH = OUT / "diagnostics.json"
STEP_CONTACT_TOLERANCE_MM = 0.01


def _measure(path: Path) -> dict:
    imported = import_step(path)
    solids = imported.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(
            f"{path.name} is not one valid solid: "
            f"count={len(solids)}, validity={[solid.is_valid for solid in solids]}"
        )
    baffle = solids[0]
    bounds = baffle.bounding_box()
    # The exterior B-spline's geometric-surface box extends below its trimmed
    # topology. Use actual B-rep vertices to establish the physical contact
    # plane; the solid/face bounding boxes remain useful only as conservative
    # extents.
    tolerance = STEP_CONTACT_TOLERANCE_MM
    vertex_z_values = [vertex.Z for vertex in baffle.vertices()]
    bed_z = min(vertex_z_values)
    bottom_faces = []
    horizontal_planar_faces = []
    for face in baffle.faces():
        face_bounds = face.bounding_box()
        if (
            face.geom_type == GeomType.PLANE
            and face_bounds.size.Z <= tolerance
        ):
            horizontal_planar_faces.append(face)
        if (
            face.geom_type == GeomType.PLANE
            and face_bounds.size.Z <= tolerance
            and abs(face_bounds.min.Z - bed_z) <= tolerance
            and abs(face_bounds.max.Z - bed_z) <= tolerance
        ):
            bottom_faces.append(face)

    face_records = []
    for face in bottom_faces:
        face_bounds = face.bounding_box()
        face_records.append(
            {
                "geometry": str(face.geom_type),
                "area_mm2": face.area,
                "x_span_mm": face_bounds.size.X,
                "y_span_mm": face_bounds.size.Y,
                "bounds_min_mm": [
                    face_bounds.min.X,
                    face_bounds.min.Y,
                    face_bounds.min.Z,
                ],
                "bounds_max_mm": [
                    face_bounds.max.X,
                    face_bounds.max.Y,
                    face_bounds.max.Z,
                ],
            }
        )
    horizontal_planar_face_records = []
    for face in horizontal_planar_faces:
        face_bounds = face.bounding_box()
        horizontal_planar_face_records.append(
            {
                "geometry": str(face.geom_type),
                "area_mm2": face.area,
                "x_span_mm": face_bounds.size.X,
                "y_span_mm": face_bounds.size.Y,
                "z_mm": (face_bounds.min.Z + face_bounds.max.Z) / 2.0,
            }
        )
    horizontal_planar_face_records.sort(
        key=lambda record: record["z_mm"],
    )
    broad_planar_faces = [
        record
        for record in horizontal_planar_face_records
        if record["x_span_mm"] >= 100.0 and record["area_mm2"] >= 100.0
    ]
    designated_planar_print_face = (
        min(broad_planar_faces, key=lambda record: record["z_mm"])
        if broad_planar_faces
        else None
    )
    bottom_edges = []
    horizontal_line_edges = []
    for edge in baffle.edges():
        edge_bounds = edge.bounding_box()
        if (
            edge.geom_type == GeomType.LINE
            and edge_bounds.size.Z <= tolerance
        ):
            horizontal_line_edges.append(edge)
        if (
            edge_bounds.size.Z <= tolerance
            and abs(edge_bounds.min.Z - bed_z) <= tolerance
            and abs(edge_bounds.max.Z - bed_z) <= tolerance
        ):
            bottom_edges.append(edge)
    edge_records = []
    for edge in bottom_edges:
        edge_bounds = edge.bounding_box()
        edge_records.append(
            {
                "geometry": str(edge.geom_type),
                "length_mm": edge.length,
                "x_span_mm": edge_bounds.size.X,
                "y_span_mm": edge_bounds.size.Y,
                "bounds_min_mm": [
                    edge_bounds.min.X,
                    edge_bounds.min.Y,
                    edge_bounds.min.Z,
                ],
                "bounds_max_mm": [
                    edge_bounds.max.X,
                    edge_bounds.max.Y,
                    edge_bounds.max.Z,
                ],
            }
        )
    horizontal_line_edge_records = []
    for edge in horizontal_line_edges:
        edge_bounds = edge.bounding_box()
        horizontal_line_edge_records.append(
            {
                "geometry": str(edge.geom_type),
                "length_mm": edge.length,
                "x_span_mm": edge_bounds.size.X,
                "y_span_mm": edge_bounds.size.Y,
                "bounds_min_mm": [
                    edge_bounds.min.X,
                    edge_bounds.min.Y,
                    edge_bounds.min.Z,
                ],
                "bounds_max_mm": [
                    edge_bounds.max.X,
                    edge_bounds.max.Y,
                    edge_bounds.max.Z,
                ],
            }
        )
    horizontal_line_edge_records.sort(
        key=lambda record: record["x_span_mm"],
        reverse=True,
    )
    full_width_face = (
        max(face_records, key=lambda record: record["x_span_mm"])
        if face_records
        else None
    )
    full_width_edge = (
        max(edge_records, key=lambda record: record["x_span_mm"])
        if edge_records
        else None
    )
    total_area = sum(record["area_mm2"] for record in face_records)
    aggregate_x_span = (
        max(record["bounds_max_mm"][0] for record in edge_records)
        - min(record["bounds_min_mm"][0] for record in edge_records)
        if edge_records
        else 0.0
    )
    return {
        "artifact": str(path.relative_to(ROOT)),
        "baffle_bounds_min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "baffle_bounds_max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "conservative_surface_bounds_min_z_mm": bounds.min.Z,
        "trimmed_topology_min_vertex_z_mm": bed_z,
        "bed_z_mm": bed_z,
        "surface_bounds_below_trimmed_bed_mm": bed_z - bounds.min.Z,
        "planar_bottom_face_count": len(bottom_faces),
        "total_planar_bottom_area_mm2": total_area,
        "largest_planar_bottom_face": full_width_face,
        "horizontal_planar_faces": horizontal_planar_face_records,
        "designated_planar_print_face": designated_planar_print_face,
        "topology_below_designated_plane_mm": (
            designated_planar_print_face["z_mm"] - bed_z
            if designated_planar_print_face is not None
            else None
        ),
        "bottom_edge_count": len(bottom_edges),
        "aggregate_bottom_edge_x_span_mm": aggregate_x_span,
        "largest_bottom_edge": full_width_edge,
        "bottom_edges": edge_records,
        "widest_horizontal_line_edges": horizontal_line_edge_records[:12],
    }


def main() -> None:
    candidate = _measure(BAFFLE_STEP)
    reference = _measure(REFERENCE_STEP)
    candidate_face = candidate["designated_planar_print_face"]
    reference_face = reference["designated_planar_print_face"]
    if candidate_face is None or reference_face is None:
        print(
            json.dumps(
                {
                    "candidate": candidate,
                    "accepted_flat_edge_reference": reference,
                },
                indent=2,
            ),
            flush=True,
        )
        raise ValueError(
            "Candidate and reference must both have a broad planar "
            f"bed-contact face: candidate={candidate_face}, "
            f"reference={reference_face}"
        )
    if (
        candidate_face["geometry"] != str(GeomType.PLANE)
        or reference_face["geometry"] != str(GeomType.PLANE)
        or candidate["topology_below_designated_plane_mm"] > 0.01
        or abs(candidate_face["z_mm"] - reference_face["z_mm"]) > 0.01
        or candidate_face["x_span_mm"] < 187.0
        or candidate_face["area_mm2"] < 2200.0
    ):
        raise ValueError(
            "Candidate does not retain the accepted planar full-width "
            f"printing contact: candidate={candidate_face}, "
            f"reference={reference_face}"
        )

    diagnostics = {
        "print_orientation": "narrow lower edge on bed",
        "build_direction_design_coordinates": "+Z",
        "brim_assumed": True,
        "candidate": candidate,
        "accepted_flat_edge_reference": reference,
        "reference_known_below_plane_transition_mm": reference[
            "topology_below_designated_plane_mm"
        ],
        "candidate_below_plane_transition_mm": candidate[
            "topology_below_designated_plane_mm"
        ],
        "minimum_required_planar_contact_x_span_mm": 187.0,
        "minimum_required_planar_contact_area_mm2": 2200.0,
        "reference_contact_span_tolerance_mm": 0.01,
        "step_contact_plane_tolerance_mm": STEP_CONTACT_TOLERANCE_MM,
        "passes_straight_full_width_edge": True,
        "finite_planar_contact_area_required": True,
        "physical_adhesion_uncertainty": (
            "A brim is required; CAD does not validate first-layer adhesion."
        ),
    }
    published = job_output_path(DIAGNOSTICS_PATH)
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
