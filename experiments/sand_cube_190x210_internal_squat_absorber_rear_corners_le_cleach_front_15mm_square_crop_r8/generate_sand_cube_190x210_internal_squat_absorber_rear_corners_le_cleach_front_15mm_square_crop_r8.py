"""Generate a square-cropped Le Cleac'h face, then apply the cabinet R8.

This study deliberately does not subtract a horn-shaped cutter from the
already-filleted baseline envelope. It starts with a sharp 190 mm square,
trims it with an exact Le Cleac'h 2007 recurrence, and only then constructs the
rounded cabinet perimeter. That makes the curved perimeter blend belong to the
new face and eliminates the exposed legacy-fillet crescent.
"""

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

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import copy
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Face,
    GeomType,
    Pos,
    Solid,
    Unit,
    export_step,
    fillet,
    import_step,
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
)
from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Vec
from OCP.TColgp import TColgp_HArray1OfPnt
from OCP.TopoDS import TopoDS


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners"
)
SOLVER_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_inverse_le_cleach_front"
)
for module_dir in (SOURCE_EXPERIMENT, SOLVER_EXPERIMENT):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners as prior  # noqa: E402
import solve_inverse_le_cleach_front as inverse  # noqa: E402
from src.features.horn import _le_cleach_2007_points_for_cutoff  # noqa: E402


base = prior.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8"
)

NAME = "sand_cube_190x210_exact_le_cleach_15mm_square_crop_post_r8_preview"
FRONT_Y = 10.0 - base.D.depth / 2.0
TARGET_FINISHED_CORNER_PULLBACK_MM = 15.0
SOLVED_RAW_HORN_CORNER_PULLBACK_MM = 11.6943
SOLVED_CUTOFF_HZ = 441.5201401068668
SOLVED_WAVEFRONT_T = 2.3294469224433434
THROAT_HALF_ANGLE_DEG = 60.0
NOMINAL_EDGE_FILLET_R_MM = base.D.edge_fillet_r
CAD_EDGE_FILLET_R_MM = NOMINAL_EDGE_FILLET_R_MM - 0.001
RAW_SQUARE_CORNER_RADIUS_MM = math.hypot(
    base.D.width / 2.0,
    base.D.height / 2.0,
)
CUTTER_RADIUS_MM = RAW_SQUARE_CORNER_RADIUS_MM + 1.0
CUTTER_FRONT_OVERTRAVEL_MM = 1.0
MAXIMUM_SPLINE_CONSTRAINTS = 401
PROFILE_TOLERANCE_MM = 1e-4


@dataclass(frozen=True)
class ExtendedHornProfile:
    points: tuple[tuple[float, float], ...]
    crest_radius_mm: float
    crest_axial_mm: float
    edge_midpoint_setback_mm: float
    physical_corner_setback_mm: float
    raw_square_corner_setback_mm: float
    cutter_radius_setback_mm: float
    terminal_angle_deg: float
    spreadsheet_row_step_mm: float
    recurrence_sample_count: int


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _extended_horn_profile() -> tuple[inverse.FaceTargets, ExtendedHornProfile]:
    """Evaluate the exact recurrence through the sacrificial sharp corner."""
    targets = inverse._face_targets()
    raw_points, terminal_angle_deg, row_step_mm = (
        _le_cleach_2007_points_for_cutoff(
            throat_d=targets.driver_cutout_diameter_mm,
            mouth_inner_r=CUTTER_RADIUS_MM,
            cutoff_hz=SOLVED_CUTOFF_HZ,
            wavefront_t=SOLVED_WAVEFRONT_T,
            throat_angle_deg=THROAT_HALF_ANGLE_DEG,
        )
    )
    crest_radius, crest_axial, _crest_index = inverse._quadratic_crest(
        raw_points
    )

    def setback(radius_mm: float) -> float:
        return crest_axial - inverse._interpolated_axial(raw_points, radius_mm)

    physical_corner_setback = setback(targets.physical_corner_radius_mm)
    if abs(crest_radius - targets.black_hole_radius_mm) > PROFILE_TOLERANCE_MM:
        raise ValueError("Extended horn crest misses the black-hole perimeter")
    if (
        abs(
            physical_corner_setback
            - SOLVED_RAW_HORN_CORNER_PULLBACK_MM
        )
        > PROFILE_TOLERANCE_MM
    ):
        raise ValueError("Extended horn misses its inverse-compensated target")

    retained_points: list[tuple[float, float]] = [
        (targets.black_hole_radius_mm, 0.0)
    ]
    retained_points.extend(
        (radius, crest_axial - axial)
        for radius, axial in raw_points
        if targets.black_hole_radius_mm + 1e-9 < radius < CUTTER_RADIUS_MM
    )
    retained_points.append((CUTTER_RADIUS_MM, setback(CUTTER_RADIUS_MM)))

    return targets, ExtendedHornProfile(
        points=tuple(retained_points),
        crest_radius_mm=crest_radius,
        crest_axial_mm=crest_axial,
        edge_midpoint_setback_mm=setback(targets.edge_midpoint_radius_mm),
        physical_corner_setback_mm=physical_corner_setback,
        raw_square_corner_setback_mm=setback(RAW_SQUARE_CORNER_RADIUS_MM),
        cutter_radius_setback_mm=setback(CUTTER_RADIUS_MM),
        terminal_angle_deg=terminal_angle_deg,
        spreadsheet_row_step_mm=row_step_mm,
        recurrence_sample_count=len(raw_points),
    )


def _cad_constraint_points(
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if len(points) <= MAXIMUM_SPLINE_CONSTRAINTS:
        return points
    stride = math.ceil(
        (len(points) - 1) / (MAXIMUM_SPLINE_CONSTRAINTS - 1)
    )
    constrained = points[::stride]
    if constrained[-1] != points[-1]:
        constrained = [*constrained, points[-1]]
    return constrained


def _setback_spline_edge(profile: ExtendedHornProfile) -> Any:
    cad_points = _cad_constraint_points(list(profile.points))
    point_array = TColgp_HArray1OfPnt(1, len(cad_points))
    for index, (radius, setback) in enumerate(cad_points, 1):
        point_array.SetValue(index, gp_Pnt(radius, FRONT_Y + setback, 0.0))

    interpolator = GeomAPI_Interpolate(point_array, False, 1e-7)
    angle = math.radians(profile.terminal_angle_deg)
    interpolator.Load(
        gp_Vec(1.0, 0.0, 0.0),
        gp_Vec(math.sin(angle), -math.cos(angle), 0.0),
        True,
    )
    interpolator.Perform()
    if not interpolator.IsDone():
        raise ValueError("Unable to interpolate the square-crop horn surface")
    return BRepBuilderAPI_MakeEdge(interpolator.Curve()).Edge()


def _line_edge(
    start: tuple[float, float],
    end: tuple[float, float],
) -> Any:
    return BRepBuilderAPI_MakeEdge(
        gp_Pnt(start[0], start[1], 0.0),
        gp_Pnt(end[0], end[1], 0.0),
    ).Edge()


def _front_material_cutter(profile: ExtendedHornProfile) -> Solid:
    spline_edge = _setback_spline_edge(profile)
    front_tool_y = FRONT_Y - CUTTER_FRONT_OVERTRAVEL_MM
    inner_radius, inner_setback = profile.points[0]
    outer_radius, outer_setback = profile.points[-1]
    inner_front = (inner_radius, front_tool_y)
    outer_front = (outer_radius, front_tool_y)
    inner_surface = (inner_radius, FRONT_Y + inner_setback)
    outer_surface = (outer_radius, FRONT_Y + outer_setback)

    wire_maker = BRepBuilderAPI_MakeWire()
    wire_maker.Add(_line_edge(inner_front, outer_front))
    wire_maker.Add(_line_edge(outer_front, outer_surface))
    wire_maker.Add(TopoDS.Edge_s(spline_edge.Reversed()))
    wire_maker.Add(_line_edge(inner_surface, inner_front))
    if not wire_maker.IsDone():
        raise ValueError("Unable to close the square-crop cutter profile")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make the square-crop cutter face")
    profile_face = Face.cast(face_maker.Face())
    if profile_face is None or profile_face.area <= 0.0:
        raise ValueError("Square-crop cutter profile has non-positive area")

    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 1.0, 0.0)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve the square-crop cutter")
    cutter = Solid.cast(revolved.Shape())
    if cutter is None or not _is_valid(cutter) or cutter.volume <= 0.0:
        raise ValueError("Square-crop cutter is not a valid solid")
    return cutter


def _selected_front_edges(shape: Any, *, top_bottom: bool) -> list[Any]:
    if top_bottom:
        edges = [
            edge
            for edge in shape.edges()
            if edge.geom_type == GeomType.BSPLINE
            and abs(edge.center().Z) > base.D.height / 2.0 - 5.0
        ]
        expected = 2
    else:
        edges = [
            edge
            for edge in shape.edges()
            if edge.geom_type == GeomType.BSPLINE
            and abs(edge.center().X) > base.D.width / 2.0 - 5.0
            and edge.center().Y < FRONT_Y + 5.0
        ]
        # The Le Cleac'h revolution seam splits the positive-X boundary.
        expected = 4
    if len(edges) != expected:
        raise ValueError(
            f"Expected {expected} front perimeter edges, found {len(edges)}"
        )
    return edges


def _trim_then_fillet_outer(
    profile: ExtendedHornProfile,
) -> tuple[Any, Solid, dict[str, int]]:
    """Cut the horn into a sharp square, then construct all R8 blends."""
    sharp_box = Pos(0.0, 10.0, 0.0) * Box(
        base.D.width,
        base.D.depth,
        base.D.height,
    )
    cutter = _front_material_cutter(profile)
    square_cropped = base._require_single_solid(
        (sharp_box - cutter).clean().fix(),
        feature="sharp square-cropped Le Cleac'h outer envelope",
    )

    top_bottom_edges = _selected_front_edges(square_cropped, top_bottom=True)
    top_bottom_blended = base._require_single_solid(
        fillet(
            top_bottom_edges,
            radius=CAD_EDGE_FILLET_R_MM,
        ).clean().fix(),
        feature="top and bottom post-trim Le Cleac'h R8 blends",
    )

    left_right_edges = _selected_front_edges(
        top_bottom_blended,
        top_bottom=False,
    )
    perimeter_blended = base._require_single_solid(
        fillet(
            left_right_edges,
            radius=CAD_EDGE_FILLET_R_MM,
        ).clean().fix(),
        feature="closed post-trim Le Cleac'h perimeter blend",
    )

    body_edges = [
        edge
        for edge in perimeter_blended.edges()
        if edge.geom_type == GeomType.LINE
    ]
    if len(body_edges) != 12:
        raise ValueError(
            f"Expected 12 remaining sharp cabinet edges, found {len(body_edges)}"
        )
    finished = base._require_single_solid(
        fillet(body_edges, radius=CAD_EDGE_FILLET_R_MM).clean().fix(),
        feature="fully rounded trim-first Le Cleac'h outer envelope",
    )
    return finished, cutter, {
        "top_bottom_front_edge_count": len(top_bottom_edges),
        "left_right_front_edge_count": len(left_right_edges),
        "remaining_body_edge_count": len(body_edges),
    }


def _front_intersection_y(shape: Any, x: float, z: float) -> float:
    intersections = shape.find_intersection_points(
        Axis((x, FRONT_Y - 100.0, z), (0.0, 1.0, 0.0))
    )
    if not intersections:
        raise ValueError(f"No cabinet intersection at X={x:.6f}, Z={z:.6f}")
    return intersections[0][0].Y


def _finished_corner_measurement(outer: Any) -> dict[str, float]:
    corner_coordinate = (
        base.D.width / 2.0
        - CAD_EDGE_FILLET_R_MM
        + CAD_EDGE_FILLET_R_MM / math.sqrt(2.0)
    )
    corner_y = _front_intersection_y(
        outer,
        corner_coordinate,
        corner_coordinate,
    )
    edge_midpoint_y = _front_intersection_y(
        outer,
        0.0,
        base.D.height / 2.0,
    )
    crest_y = _front_intersection_y(
        outer,
        0.0,
        base.BLACK_HOLE_OUTER_D / 2.0,
    )
    return {
        "corner_xz_coordinate_mm": corner_coordinate,
        "corner_front_y_mm": corner_y,
        "finished_corner_pullback_mm": corner_y - FRONT_Y,
        "edge_midpoint_pullback_mm": edge_midpoint_y - FRONT_Y,
        "black_hole_crest_y_mm": crest_y,
    }


def _aesthetic_shell(outer: Any) -> Any:
    separated_skins = outer - base._rectangular_cavity() - base._sand_void()
    shell: Any = Compound(
        children=[copy.copy(solid) for solid in separated_skins.solids()]
    )
    for post in base._bridge_posts():
        shell = shell.fuse(post)
    shell = base._require_single_solid(
        shell.clean().fix(),
        feature="point-bridged square-crop R8 enclosure shell",
    )
    shell -= base._black_hole_visible_tool()
    shell -= base._black_hole_inner_relief()
    return base._require_single_solid(
        shell.clean().fix(),
        feature="square-crop R8 shell with baseline black-hole recess",
    )


def _center_cutaway(shell: Any) -> Any:
    bbox = shell.bounding_box()
    margin = 2.0
    clip = Pos(
        (bbox.min.X - margin) / 2.0,
        (bbox.min.Y + bbox.max.Y) / 2.0,
        (bbox.min.Z + bbox.max.Z) / 2.0,
    ) * Box(
        -bbox.min.X + margin,
        bbox.size.Y + 2.0 * margin,
        bbox.size.Z + 2.0 * margin,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    cutaway = (shell & clip).clean().fix()
    solids = [copy.copy(solid) for solid in cutaway.solids()]
    if not solids or not all(_is_valid(solid) for solid in solids):
        raise ValueError("Square-crop R8 cutaway is empty or invalid")
    return Compound(children=solids)


def _set_viewer_edge_mode(viewer_dir: Path, *, face_only: bool) -> None:
    model_data = viewer_dir / "model-data.js"
    payload = model_data.read_bytes()
    original_payload = payload
    payload = payload.replace(b'"black_edges":true', b'"black_edges":false')
    payload = payload.replace(b'"render_edges":true', b'"render_edges":false')
    if face_only:
        payload = payload.replace(b'"state":[1,1]', b'"state":[1,0]')
    if payload == original_payload:
        raise ValueError(f"Could not set viewer edge mode in {model_data}")
    model_data.write_bytes(payload)


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
                _is_valid(solid) for solid in imported_solids
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
        ("square_crop_r8_enclosure.step", "viewer", True),
        ("square_crop_r8_enclosure_cutaway.step", "cutaway_viewer", False),
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
        _set_viewer_edge_mode(viewer_dir, face_only=face_only)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    targets, profile = _extended_horn_profile()
    original_outer = base._outer_envelope()
    sculpted_outer, cutter, edge_counts = _trim_then_fillet_outer(profile)
    finished_measurement = _finished_corner_measurement(sculpted_outer)
    if (
        abs(
            finished_measurement["finished_corner_pullback_mm"]
            - TARGET_FINISHED_CORNER_PULLBACK_MM
        )
        > 0.01
    ):
        raise ValueError("Finished R8 corner misses the 15 mm pullback target")

    cavity = base._rectangular_cavity()
    sand_void = base._sand_void()
    cavity_outside_outer_mm3 = _shape_volume(cavity - sculpted_outer)
    sand_void_outside_outer_mm3 = _shape_volume(sand_void - sculpted_outer)
    if cavity_outside_outer_mm3 > 1e-6 or sand_void_outside_outer_mm3 > 1e-6:
        raise ValueError("Post-trim R8 surface breaches a protected void")

    enclosure = _aesthetic_shell(sculpted_outer)
    original_aesthetic_shell = _aesthetic_shell(original_outer)
    cutaway = _center_cutaway(enclosure)
    if not _is_valid(sculpted_outer) or not _is_valid(enclosure):
        raise ValueError("Square-crop R8 enclosure geometry is invalid")

    exports = {
        "square_crop_r8_enclosure.step": enclosure,
        "square_crop_r8_enclosure_cutaway.step": cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    finished_pullback = finished_measurement["finished_corner_pullback_mm"]
    diagnostics = {
        "name": NAME,
        "status": "enclosure-only square-crop-first, post-trim R8 preview",
        "isolation": {
            "experiment_dir": (
                "experiments/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8"
            ),
            "output_dir": (
                "build/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8"
            ),
            "authoritative_rear_corner_variant_modified": False,
            "earlier_aesthetic_experiments_modified": False,
            "shared_upstream_generators_modified": False,
        },
        "construction": {
            "order": [
                "exact Le Cleac'h recurrence through raw square corner",
                "crop sharp 190 x 190 square with revolved surface",
                "apply top and bottom curved perimeter blends",
                "apply left and right curved perimeter blends",
                "apply remaining cabinet edge blends",
            ],
            "preexisting_filleted_outer_envelope_used": False,
            "raw_square_corner_radius_mm": RAW_SQUARE_CORNER_RADIUS_MM,
            "exact_recurrence_cutter_radius_mm": CUTTER_RADIUS_MM,
            "nominal_edge_fillet_radius_mm": NOMINAL_EDGE_FILLET_R_MM,
            "cad_edge_fillet_radius_mm": CAD_EDGE_FILLET_R_MM,
            "edge_counts": edge_counts,
        },
        "le_cleach_solution": {
            "source": "exact Le Cleac'h 2007 spreadsheet recurrence B24:H4028",
            "solved_cutoff_hz": SOLVED_CUTOFF_HZ,
            "solved_wavefront_t": SOLVED_WAVEFRONT_T,
            "wavefront_t_family": "sinh",
            "virtual_throat_diameter_mm": targets.driver_cutout_diameter_mm,
            "throat_half_angle_deg": THROAT_HALF_ANGLE_DEG,
            "crest_radius_mm": profile.crest_radius_mm,
            "raw_horn_physical_corner_setback_mm": (
                profile.physical_corner_setback_mm
            ),
            "raw_square_corner_setback_mm": (
                profile.raw_square_corner_setback_mm
            ),
            "raw_edge_midpoint_setback_mm": (
                profile.edge_midpoint_setback_mm
            ),
            "terminal_angle_at_cutter_deg": profile.terminal_angle_deg,
            "recurrence_sample_count": profile.recurrence_sample_count,
            "cad_spline_constraint_count": len(
                _cad_constraint_points(list(profile.points))
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
            "cutter_valid": _is_valid(cutter),
            "outer_envelope_valid": _is_valid(sculpted_outer),
            "enclosure_valid": _is_valid(enclosure),
            "cutaway_all_solids_valid": all(
                _is_valid(solid) for solid in cutaway.solids()
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
