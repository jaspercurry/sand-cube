"""Generate a body-first cabinet with one unified front R8 operation.

The exact Le Cleac'h face is square-cropped first. All non-front cabinet edges
are rounded next, and all front-perimeter edges are then filleted together.
This avoids the staged front-corner patches of the preceding experiment.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from build123d import (
    Box,
    GeomType,
    Pos,
    Unit,
    export_step,
    fillet,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8 as parent  # noqa: E402


base = parent.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8"
)

NAME = "sand_cube_190x210_exact_le_cleach_15mm_square_crop_unified_r8_preview"
FRONT_Y = parent.FRONT_Y
TARGET_FINISHED_CORNER_PULLBACK_MM = 15.0
SOLVED_RAW_HORN_CORNER_PULLBACK_MM = 10.0914
SOLVED_CUTOFF_HZ = 414.24707854954
SOLVED_WAVEFRONT_T = 2.515005837684834
CAD_EDGE_FILLET_R_MM = parent.CAD_EDGE_FILLET_R_MM

# The parent owns the exact recurrence, cutter, measurement, shell, and viewer
# helpers. Override only the inverse-solved horn inputs in this process; no
# parent or shared source file is modified.
parent.SOLVED_RAW_HORN_CORNER_PULLBACK_MM = (
    SOLVED_RAW_HORN_CORNER_PULLBACK_MM
)
parent.SOLVED_CUTOFF_HZ = SOLVED_CUTOFF_HZ
parent.SOLVED_WAVEFRONT_T = SOLVED_WAVEFRONT_T


def _shape_volume(shape: Any) -> float:
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _unified_outer(
    profile: parent.ExtendedHornProfile,
) -> tuple[Any, Any, dict[str, Any]]:
    """Round the body first, then fillet the entire front perimeter at once."""
    sharp_box = Pos(0.0, 10.0, 0.0) * Box(
        base.D.width,
        base.D.depth,
        base.D.height,
    )
    cutter = parent._front_material_cutter(profile)
    square_cropped = base._require_single_solid(
        (sharp_box - cutter).clean().fix(),
        feature="sharp square-cropped unified-fillet outer envelope",
    )

    body_edges = [
        edge
        for edge in square_cropped.edges()
        if edge.geom_type == GeomType.LINE
    ]
    if len(body_edges) != 8:
        raise ValueError(
            f"Expected eight non-front cabinet edges, found {len(body_edges)}"
        )
    body_rounded = base._require_single_solid(
        fillet(body_edges, radius=CAD_EDGE_FILLET_R_MM).clean().fix(),
        feature="body-first cabinet R8 edges",
    )

    front_edges = [
        edge
        for edge in body_rounded.edges()
        if edge.geom_type == GeomType.BSPLINE
        and edge.center().Y < FRONT_Y + 5.0
    ]
    if len(front_edges) != 6:
        raise ValueError(
            f"Expected six unified front-perimeter edges, found {len(front_edges)}"
        )
    finished = base._require_single_solid(
        fillet(front_edges, radius=CAD_EDGE_FILLET_R_MM).clean().fix(),
        feature="simultaneous closed front-perimeter R8 blend",
    )

    topology = _side_boundary_topology(finished)
    if topology["front_boundary_bspline_count"] != 2:
        raise ValueError("Unified side silhouette contains transition segments")
    return finished, cutter, {
        "non_front_body_edge_count": len(body_edges),
        "simultaneous_front_edge_count": len(front_edges),
        **topology,
    }


def _side_boundary_topology(outer: Any) -> dict[str, Any]:
    side_faces = [
        face
        for face in outer.faces()
        if face.geom_type == GeomType.PLANE
        and abs(face.center().X - base.D.width / 2.0) < 0.01
    ]
    if not side_faces:
        raise ValueError("Unable to locate positive-X outer side face")
    side_face = max(side_faces, key=lambda face: face.area)
    front_curves = [
        edge
        for edge in side_face.edges()
        if edge.geom_type == GeomType.BSPLINE
    ]
    short_curves = [edge for edge in front_curves if edge.length < 20.0]
    return {
        "outer_side_face_edge_count": len(side_face.edges()),
        "front_boundary_bspline_count": len(front_curves),
        "front_boundary_segment_lengths_mm": [
            edge.length for edge in front_curves
        ],
        "short_corner_transition_curve_count": len(short_curves),
        "revolution_seam_half_count": sum(
            edge.length > 80.0 for edge in front_curves
        ),
    }


def _export_and_check(exports: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        imported_solids = imported.solids()
        source_count = len(shape.solids())
        checks[filename] = {
            "source_solid_count": source_count,
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(imported_solids) == source_count,
            "all_imported_solids_valid": all(
                parent._is_valid(solid) for solid in imported_solids
            ),
        }
        if (
            not checks[filename]["solid_count_matches"]
            or not checks[filename]["all_imported_solids_valid"]
        ):
            raise ValueError(f"STEP round-trip failed for {filename}")
    return checks


def _generate_viewers() -> None:
    for source, viewer_name, face_only in (
        ("unified_r8_enclosure.step", "viewer", True),
        ("unified_r8_enclosure_cutaway.step", "cutaway_viewer", False),
    ):
        viewer_dir = OUT / viewer_name
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source),
                "--out",
                str(viewer_dir),
            ],
            check=True,
        )
        parent._set_viewer_edge_mode(viewer_dir, face_only=face_only)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    targets, profile = parent._extended_horn_profile()
    original_outer = base._outer_envelope()
    sculpted_outer, cutter, topology = _unified_outer(profile)
    finished_measurement = parent._finished_corner_measurement(sculpted_outer)
    finished_pullback = finished_measurement["finished_corner_pullback_mm"]
    if (
        abs(finished_pullback - TARGET_FINISHED_CORNER_PULLBACK_MM)
        > 0.01
    ):
        raise ValueError("Unified R8 corner misses the 15 mm pullback target")

    cavity = base._rectangular_cavity()
    sand_void = base._sand_void()
    cavity_outside_outer_mm3 = _shape_volume(cavity - sculpted_outer)
    sand_void_outside_outer_mm3 = _shape_volume(sand_void - sculpted_outer)
    if cavity_outside_outer_mm3 > 1e-6 or sand_void_outside_outer_mm3 > 1e-6:
        raise ValueError("Unified R8 surface breaches a protected void")

    enclosure = parent._aesthetic_shell(sculpted_outer)
    original_aesthetic_shell = parent._aesthetic_shell(original_outer)
    cutaway = parent._center_cutaway(enclosure)
    if not parent._is_valid(sculpted_outer) or not parent._is_valid(enclosure):
        raise ValueError("Unified R8 enclosure geometry is invalid")

    exports = {
        "unified_r8_enclosure.step": enclosure,
        "unified_r8_enclosure_cutaway.step": cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    diagnostics = {
        "name": NAME,
        "status": "enclosure-only body-first unified-front-R8 preview",
        "isolation": {
            "experiment_dir": (
                "experiments/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8"
            ),
            "output_dir": (
                "build/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8"
            ),
            "authoritative_rear_corner_variant_modified": False,
            "earlier_aesthetic_experiments_modified": False,
            "shared_upstream_generators_modified": False,
        },
        "construction": {
            "order": [
                "exact Le Cleac'h recurrence through raw square corner",
                "crop sharp 190 x 190 square",
                "fillet all eight non-front cabinet edges",
                "fillet all six front-perimeter edges simultaneously",
            ],
            "preexisting_filleted_outer_envelope_used": False,
            "staged_front_fillets_used": False,
            "nominal_edge_fillet_radius_mm": parent.NOMINAL_EDGE_FILLET_R_MM,
            "cad_edge_fillet_radius_mm": CAD_EDGE_FILLET_R_MM,
            "side_boundary_topology": topology,
        },
        "le_cleach_solution": {
            "source": "exact Le Cleac'h 2007 spreadsheet recurrence B24:H4028",
            "solved_cutoff_hz": SOLVED_CUTOFF_HZ,
            "solved_wavefront_t": SOLVED_WAVEFRONT_T,
            "wavefront_t_family": "sinh",
            "virtual_throat_diameter_mm": targets.driver_cutout_diameter_mm,
            "throat_half_angle_deg": parent.THROAT_HALF_ANGLE_DEG,
            "crest_radius_mm": profile.crest_radius_mm,
            "raw_horn_physical_corner_setback_mm": (
                profile.physical_corner_setback_mm
            ),
            "raw_square_corner_setback_mm": (
                profile.raw_square_corner_setback_mm
            ),
            "terminal_angle_at_cutter_deg": profile.terminal_angle_deg,
            "recurrence_sample_count": profile.recurrence_sample_count,
            "cad_spline_constraint_count": len(
                parent._cad_constraint_points(list(profile.points))
            ),
            "spreadsheet_row_step_mm": profile.spreadsheet_row_step_mm,
        },
        "finished_front": {
            **finished_measurement,
            "target_finished_corner_pullback_mm": (
                TARGET_FINISHED_CORNER_PULLBACK_MM
            ),
            "finished_corner_pullback_error_mm": (
                finished_pullback - TARGET_FINISHED_CORNER_PULLBACK_MM
            ),
            "black_hole_outer_diameter_mm": base.BLACK_HOLE_OUTER_D,
            "front_cap_depth_mm": base.BLACK_HOLE_SEAT_DEPTH,
            "minimum_nominal_remaining_corner_cap_mm": (
                base.BLACK_HOLE_SEAT_DEPTH - finished_pullback
            ),
            "inner_acoustic_surface_modified": False,
            "modeled_acoustic_volume_change_l": 0.0,
            "outer_envelope_material_removed_cm3": (
                original_outer.volume - sculpted_outer.volume
            )
            / 1000.0,
            "finished_shell_material_removed_cm3": (
                original_aesthetic_shell.volume - enclosure.volume
            )
            / 1000.0,
        },
        "clearance_and_interference": {
            "cavity_outside_new_outer_envelope_mm3": cavity_outside_outer_mm3,
            "sand_void_outside_new_outer_envelope_mm3": (
                sand_void_outside_outer_mm3
            ),
            "inter_part_checks_applicable": False,
            "reason": "enclosure-only preview; functional assemblies omitted",
        },
        "baseline_functional_metrics": {
            "port_physical_length_mm": 526.4,
            "modeled_natural_tuning_hz": 39.21,
            "modeled_net_enclosure_volume_l": 4.398,
            "changed_by_preview": False,
        },
        "geometry": {
            "cutter_valid": parent._is_valid(cutter),
            "outer_envelope_valid": parent._is_valid(sculpted_outer),
            "enclosure_valid": parent._is_valid(enclosure),
            "cutaway_all_solids_valid": all(
                parent._is_valid(solid) for solid in cutaway.solids()
            ),
            "enclosure_solid_count": len(enclosure.solids()),
            "cutaway_solid_count": len(cutaway.solids()),
            "step_roundtrip": step_roundtrip,
        },
        "omitted_from_preview": [
            "woofer",
            "internal port and absorber",
            "serviceable tower and flare",
            "horn and compression driver",
            "GX16 and fill hardware",
            "internal brace network",
        ],
        "files": {
            **{filename: str(OUT / filename) for filename in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "index.html"),
            "cutaway_viewer": str(OUT / "cutaway_viewer" / "index.html"),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
