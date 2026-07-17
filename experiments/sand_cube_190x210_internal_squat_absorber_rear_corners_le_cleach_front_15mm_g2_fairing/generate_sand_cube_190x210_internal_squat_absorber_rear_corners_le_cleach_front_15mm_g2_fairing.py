"""Generate an enclosure-only preview with a custom G2 front fairing.

The preceding unified-R8 experiment remains unchanged.  This sibling replaces
the constant-radius front roll with a degree-five Hermite/Bezier fairing.  Its
inner end matches the exact Le Cleac'h crest slope and meridional curvature;
its outer end is tangent to the cabinet side with zero meridional curvature.

The outer XZ silhouette is a high-order superellipse fitted through the nominal
R8 side midpoint and diagonal corner.  Unlike a line-plus-circle rounded
rectangle, that perimeter is curvature-continuous and therefore does not put a
curvature kink into the fourfold fairing.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from build123d import (
    Axis,
    Compound,
    Edge,
    Face,
    Shell,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    fillet,
    import_step,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
from OCP.Geom import Geom_BSplineCurve, Geom_BSplineSurface
from OCP.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt
from OCP.TColStd import (
    TColStd_Array1OfInteger,
    TColStd_Array1OfReal,
)
from OCP.gp import gp_Pnt


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8 as parent  # noqa: E402


cad = parent.parent
base = parent.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_g2_fairing"
)

NAME = "sand_cube_190x210_le_cleach_15mm_custom_g2_fairing_preview"
FRONT_Y = parent.FRONT_Y
FRONT_OVERTRAVEL_MM = 1.0
INNER_CREST_RADIUS_MM = base.BLACK_HOLE_OUTER_D / 2.0
EDGE_MIDPOINT_PULLBACK_MM = 8.0
CORNER_PULLBACK_MM = 15.0
PREVIEW_REAR_EDGE_FILLET_R_MM = 4.0
ANGULAR_SAMPLE_COUNT = 128
U_DEGREE = 3
V_DEGREE = 5

# Quadratic interpolation of the exact target-15 Le Cleac'h recurrence at its
# r=87 mm rolled-back crest.  This is d2(setback)/dr2; the first derivative is
# zero at the crest by construction.
LE_CLEACH_CREST_CURVATURE_PER_MM = 0.01048040745485664

HALF_WIDTH_MM = base.D.width / 2.0
R8_CORNER_COORDINATE_MM = (
    HALF_WIDTH_MM
    - base.D.edge_fillet_r
    + base.D.edge_fillet_r / math.sqrt(2.0)
)
SUPERELLIPSE_EXPONENT = math.log(0.5) / math.log(
    R8_CORNER_COORDINATE_MM / HALF_WIDTH_MM
)


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _outer_radius(theta: float) -> float:
    """Ray radius of the G2 superellipse matching the nominal R8 corner."""
    cosine = abs(math.cos(theta))
    sine = abs(math.sin(theta))
    return HALF_WIDTH_MM / (
        cosine**SUPERELLIPSE_EXPONENT
        + sine**SUPERELLIPSE_EXPONENT
    ) ** (1.0 / SUPERELLIPSE_EXPONENT)


def _pullback(theta: float) -> float:
    """C-infinity fourfold setback: 8 mm on-axis and 15 mm diagonally."""
    corner_weight = math.sin(2.0 * theta) ** 2
    return EDGE_MIDPOINT_PULLBACK_MM + (
        CORNER_PULLBACK_MM - EDGE_MIDPOINT_PULLBACK_MM
    ) * corner_weight


def _bezier_control_rings() -> list[list[tuple[float, float, float]]]:
    """Six control rings for exact quintic endpoint value/derivative data."""
    rings: list[list[tuple[float, float, float]]] = [
        [] for _ in range(V_DEGREE + 1)
    ]
    for index in range(ANGULAR_SAMPLE_COUNT):
        theta = math.tau * index / ANGULAR_SAMPLE_COUNT
        cosine = math.cos(theta)
        sine = math.sin(theta)
        outer_radius = _outer_radius(theta)
        radial_span = outer_radius - INNER_CREST_RADIUS_MM
        pullback = _pullback(theta)

        p0 = np.asarray(
            (
                INNER_CREST_RADIUS_MM * cosine,
                FRONT_Y,
                INNER_CREST_RADIUS_MM * sine,
            ),
            dtype=float,
        )
        p1 = np.asarray(
            (
                outer_radius * cosine,
                FRONT_Y + pullback,
                outer_radius * sine,
            ),
            dtype=float,
        )
        v0 = np.asarray(
            (radial_span * cosine, 0.0, radial_span * sine),
            dtype=float,
        )
        v1 = np.asarray((0.0, pullback, 0.0), dtype=float)
        a0 = np.asarray(
            (
                0.0,
                LE_CLEACH_CREST_CURVATURE_PER_MM * radial_span**2,
                0.0,
            ),
            dtype=float,
        )
        a1 = np.zeros(3, dtype=float)

        controls = (
            p0,
            p0 + v0 / 5.0,
            p0 + 2.0 * v0 / 5.0 + a0 / 20.0,
            p1 - 2.0 * v1 / 5.0 + a1 / 20.0,
            p1 - v1 / 5.0,
            p1,
        )
        for ring, point in zip(rings, controls):
            ring.append(tuple(float(value) for value in point))
    return rings


def _periodic_interpolation_poles(
    targets: list[tuple[float, float, float]],
) -> np.ndarray:
    """Solve the uniform periodic cubic interpolation system exactly."""
    count = len(targets)
    matrix = np.zeros((count, count), dtype=float)
    for row in range(count):
        matrix[row, row] = 1.0
        matrix[row, (row + 1) % count] = 4.0
        matrix[row, (row + 2) % count] = 1.0
    return np.linalg.solve(matrix, 6.0 * np.asarray(targets, dtype=float))


def _u_basis() -> tuple[
    TColStd_Array1OfReal,
    TColStd_Array1OfInteger,
]:
    knots = TColStd_Array1OfReal(1, ANGULAR_SAMPLE_COUNT + 1)
    multiplicities = TColStd_Array1OfInteger(1, ANGULAR_SAMPLE_COUNT + 1)
    for index in range(ANGULAR_SAMPLE_COUNT + 1):
        knots.SetValue(index + 1, float(index))
        multiplicities.SetValue(index + 1, 1)
    return knots, multiplicities


def _v_basis(degree: int) -> tuple[
    TColStd_Array1OfReal,
    TColStd_Array1OfInteger,
]:
    knots = TColStd_Array1OfReal(1, 2)
    knots.SetValue(1, 0.0)
    knots.SetValue(2, 1.0)
    multiplicities = TColStd_Array1OfInteger(1, 2)
    multiplicities.SetValue(1, degree + 1)
    multiplicities.SetValue(2, degree + 1)
    return knots, multiplicities


def _surface_from_poles(
    pole_rings: list[np.ndarray],
    *,
    v_degree: int,
) -> Geom_BSplineSurface:
    poles = TColgp_Array2OfPnt(
        1,
        ANGULAR_SAMPLE_COUNT,
        1,
        len(pole_rings),
    )
    for v_index, ring in enumerate(pole_rings, 1):
        for u_index, point in enumerate(ring, 1):
            poles.SetValue(u_index, v_index, gp_Pnt(*point))
    u_knots, u_multiplicities = _u_basis()
    v_knots, v_multiplicities = _v_basis(v_degree)
    return Geom_BSplineSurface(
        poles,
        u_knots,
        v_knots,
        u_multiplicities,
        v_multiplicities,
        U_DEGREE,
        v_degree,
        True,
        False,
    )


def _face_from_surface(surface: Geom_BSplineSurface, *, feature: str) -> Face:
    maker = BRepBuilderAPI_MakeFace(surface, 1e-7)
    if not maker.IsDone():
        raise ValueError(f"Unable to make {feature} face")
    face = Face.cast(maker.Face())
    if face is None or face.area <= 0.0 or not _is_valid(face):
        raise ValueError(f"{feature} face is empty or invalid")
    return face


def _curve_from_poles(poles: np.ndarray) -> Geom_BSplineCurve:
    pole_array = TColgp_Array1OfPnt(1, ANGULAR_SAMPLE_COUNT)
    for index, point in enumerate(poles, 1):
        pole_array.SetValue(index, gp_Pnt(*point))
    knots, multiplicities = _u_basis()
    return Geom_BSplineCurve(
        pole_array,
        knots,
        multiplicities,
        U_DEGREE,
        True,
    )


def _face_from_curve(curve: Geom_BSplineCurve, *, feature: str) -> Face:
    edge_maker = BRepBuilderAPI_MakeEdge(curve)
    if not edge_maker.IsDone():
        raise ValueError(f"Unable to make {feature} edge")
    edge = Edge.cast(edge_maker.Edge())
    if edge is None:
        raise ValueError(f"Unable to cast {feature} edge")
    face = Face(Wire([edge]))
    if face.area <= 0.0 or not _is_valid(face):
        raise ValueError(f"{feature} face is empty or invalid")
    return face


def _outer_body(outer_poles: np.ndarray) -> tuple[Any, dict[str, Any]]:
    front_poles = outer_poles.copy()
    front_poles[:, 1] = FRONT_Y
    front_face = _face_from_curve(
        _curve_from_poles(front_poles),
        feature="G2 rounded-square front section",
    )
    extruded = base._require_single_solid(
        Solid.extrude(front_face, Vector(0.0, base.D.depth, 0.0)),
        feature="G2 rounded-square cabinet prism",
    )
    rear_edges = [
        edge
        for edge in extruded.edges()
        if edge.is_closed and edge.center().Y > FRONT_Y + base.D.depth - 0.01
    ]
    if len(rear_edges) != 1:
        raise ValueError(
            f"Expected one rear-perimeter edge, found {len(rear_edges)}"
        )
    finished = base._require_single_solid(
        fillet(
            rear_edges,
            radius=PREVIEW_REAR_EDGE_FILLET_R_MM,
        ).clean().fix(),
        feature="G2 body with preview rear edge roll",
    )
    bbox = finished.bounding_box()
    return finished, {
        "rear_fillet_edge_count": len(rear_edges),
        "preview_rear_edge_fillet_radius_mm": (
            PREVIEW_REAR_EDGE_FILLET_R_MM
        ),
        "rear_edge_note": (
            "isolated preview compromise; front G2 fairing is unaffected"
        ),
        "body_width_mm": bbox.size.X,
        "body_depth_mm": bbox.size.Y,
        "body_height_mm": bbox.size.Z,
    }


def _g2_cutter() -> tuple[Solid, Face, dict[str, Any]]:
    control_targets = _bezier_control_rings()
    control_poles = [
        _periodic_interpolation_poles(ring) for ring in control_targets
    ]
    fairing_surface = _surface_from_poles(
        control_poles,
        v_degree=V_DEGREE,
    )
    fairing_face = _face_from_surface(
        fairing_surface,
        feature="quintic G2 fairing",
    )

    front_outer_poles = control_poles[-1].copy()
    front_outer_poles[:, 1] = FRONT_Y - FRONT_OVERTRAVEL_MM
    curtain_surface = _surface_from_poles(
        [front_outer_poles, control_poles[-1]],
        v_degree=1,
    )
    curtain_face = _face_from_surface(
        curtain_surface,
        feature="G2 fairing outer curtain",
    )

    fairing_boundaries = [edge for edge in fairing_face.edges() if edge.is_closed]
    curtain_boundaries = [edge for edge in curtain_face.edges() if edge.is_closed]
    if len(fairing_boundaries) != 2 or len(curtain_boundaries) != 2:
        raise ValueError("Unexpected periodic fairing boundary topology")
    inner_edge = min(fairing_boundaries, key=lambda edge: edge.length)
    front_edge = min(curtain_boundaries, key=lambda edge: edge.center().Y)
    inner_disk = Face(Wire([copy.copy(inner_edge)]))
    front_disk = Face(Wire([copy.copy(front_edge)]))

    shell = Shell([fairing_face, curtain_face, inner_disk, front_disk])
    cutter = Solid(shell).clean().fix()
    cutter = base._require_single_solid(
        cutter,
        feature="closed G2 front-material cutter",
    )
    if not _is_valid(cutter) or cutter.volume <= 0.0:
        raise ValueError("G2 front-material cutter is invalid")

    interpolation_error = 0.0
    for index, target in enumerate(control_targets[-1]):
        point = fairing_surface.Value(float(index), 1.0)
        interpolation_error = max(
            interpolation_error,
            point.Distance(gp_Pnt(*target)),
        )
    return cutter, fairing_face, {
        "angular_sample_count": ANGULAR_SAMPLE_COUNT,
        "u_degree": fairing_surface.UDegree(),
        "v_degree": fairing_surface.VDegree(),
        "surface_continuity": str(fairing_surface.Continuity()),
        "maximum_outer_ring_interpolation_error_mm": interpolation_error,
        "fairing_face_area_mm2": fairing_face.area,
        "cutter_volume_mm3": cutter.volume,
    }


def _front_intersection_y(shape: Any, x: float, z: float) -> float:
    intersections = shape.find_intersection_points(
        Axis((x, FRONT_Y - 100.0, z), (0.0, 1.0, 0.0))
    )
    if not intersections:
        raise ValueError(f"No cabinet intersection at X={x:.6f}, Z={z:.6f}")
    return intersections[0][0].Y


def _finished_measurement(outer: Any) -> dict[str, float]:
    diagonal_y = _front_intersection_y(
        outer,
        R8_CORNER_COORDINATE_MM,
        R8_CORNER_COORDINATE_MM,
    )
    edge_y = _front_intersection_y(outer, 0.0, HALF_WIDTH_MM)
    crest_y = _front_intersection_y(
        outer,
        0.0,
        INNER_CREST_RADIUS_MM,
    )
    return {
        "corner_xz_coordinate_mm": R8_CORNER_COORDINATE_MM,
        "corner_front_y_mm": diagonal_y,
        "finished_corner_pullback_mm": diagonal_y - FRONT_Y,
        "edge_midpoint_pullback_mm": edge_y - FRONT_Y,
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
        feature="point-bridged custom-G2 enclosure shell",
    )
    shell -= base._black_hole_visible_tool()
    shell -= base._black_hole_inner_relief()
    return base._require_single_solid(
        shell.clean().fix(),
        feature="custom-G2 shell with baseline black-hole recess",
    )


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
        ("g2_fairing_enclosure.step", "viewer", True),
        ("g2_fairing_enclosure_cutaway.step", "cutaway_viewer", False),
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
        cad._set_viewer_edge_mode(viewer_dir, face_only=face_only)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    original_outer = base._outer_envelope()
    cutter, fairing_face, fairing_topology = _g2_cutter()

    outer_boundary_targets = [
        (
            _outer_radius(math.tau * index / ANGULAR_SAMPLE_COUNT)
            * math.cos(math.tau * index / ANGULAR_SAMPLE_COUNT),
            FRONT_Y,
            _outer_radius(math.tau * index / ANGULAR_SAMPLE_COUNT)
            * math.sin(math.tau * index / ANGULAR_SAMPLE_COUNT),
        )
        for index in range(ANGULAR_SAMPLE_COUNT)
    ]
    outer_boundary_poles = _periodic_interpolation_poles(
        outer_boundary_targets
    )
    body, body_topology = _outer_body(outer_boundary_poles)
    sculpted_outer = base._require_single_solid(
        (body - cutter).clean().fix(),
        feature="custom-G2 sculpted outer envelope",
    )

    measurement = _finished_measurement(sculpted_outer)
    if abs(measurement["finished_corner_pullback_mm"] - 15.0) > 0.02:
        raise ValueError("Custom-G2 corner misses the 15 mm target")
    if abs(measurement["edge_midpoint_pullback_mm"] - 8.0) > 0.02:
        raise ValueError("Custom-G2 edge midpoint misses the 8 mm target")

    cavity = base._rectangular_cavity()
    sand_void = base._sand_void()
    cavity_outside_outer_mm3 = _shape_volume(cavity - sculpted_outer)
    sand_void_outside_outer_mm3 = _shape_volume(sand_void - sculpted_outer)
    if cavity_outside_outer_mm3 > 1e-6 or sand_void_outside_outer_mm3 > 1e-6:
        raise ValueError("Custom-G2 surface breaches a protected void")

    enclosure = _aesthetic_shell(sculpted_outer)
    original_aesthetic_shell = cad._aesthetic_shell(original_outer)
    cutaway = cad._center_cutaway(enclosure)
    if not _is_valid(sculpted_outer) or not _is_valid(enclosure):
        raise ValueError("Custom-G2 enclosure geometry is invalid")

    exports = {
        "g2_fairing_enclosure.step": enclosure,
        "g2_fairing_enclosure_cutaway.step": cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    diagnostics = {
        "name": NAME,
        "status": "enclosure-only exact-end-condition custom-G2 preview",
        "isolation": {
            "experiment_dir": (
                "experiments/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_g2_fairing"
            ),
            "output_dir": (
                "build/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_g2_fairing"
            ),
            "unified_r8_experiment_modified": False,
            "authoritative_rear_corner_variant_modified": False,
            "shared_upstream_generators_modified": False,
        },
        "construction": {
            "fairing": (
                "periodic cubic in angle x exact quintic Hermite/Bezier "
                "in the front-to-side direction"
            ),
            "inner_endpoint": {
                "radius_mm": INNER_CREST_RADIUS_MM,
                "slope_dsetback_dr": 0.0,
                "curvature_d2setback_dr2_per_mm": (
                    LE_CLEACH_CREST_CURVATURE_PER_MM
                ),
                "source": "exact target-15 Le Cleac'h 2007 recurrence crest",
            },
            "outer_endpoint": {
                "tangent": "cabinet depth axis",
                "meridional_curvature_per_mm": 0.0,
                "join_class": "G2 to the ruled cabinet side",
            },
            "fourfold_pullback_law": "8 + 7 sin^2(2 theta) mm",
            "outer_perimeter": {
                "type": "G2 high-order superellipse",
                "exponent": SUPERELLIPSE_EXPONENT,
                "side_half_extent_mm": HALF_WIDTH_MM,
                "matched_r8_diagonal_coordinate_mm": (
                    R8_CORNER_COORDINATE_MM
                ),
            },
            "body_topology": body_topology,
            "fairing_topology": fairing_topology,
        },
        "finished_front": {
            **measurement,
            "target_corner_pullback_mm": CORNER_PULLBACK_MM,
            "target_edge_midpoint_pullback_mm": (
                EDGE_MIDPOINT_PULLBACK_MM
            ),
            "black_hole_outer_diameter_mm": base.BLACK_HOLE_OUTER_D,
            "front_cap_depth_mm": base.BLACK_HOLE_SEAT_DEPTH,
            "minimum_nominal_remaining_corner_cap_mm": (
                base.BLACK_HOLE_SEAT_DEPTH
                - measurement["finished_corner_pullback_mm"]
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
            "fairing_face_area_mm2": fairing_face.area,
        },
        "clearance_and_interference": {
            "cavity_outside_new_outer_envelope_mm3": (
                cavity_outside_outer_mm3
            ),
            "sand_void_outside_new_outer_envelope_mm3": (
                sand_void_outside_outer_mm3
            ),
            "inter_part_checks_applicable": False,
            "reason": "enclosure-only aesthetic preview",
        },
        "baseline_functional_metrics": {
            "port_physical_length_mm": 526.4,
            "modeled_natural_tuning_hz": 39.21,
            "modeled_net_enclosure_volume_l": 4.398,
            "changed_by_preview": False,
        },
        "printability": {
            "minimum_front_cap_mm": (
                base.BLACK_HOLE_SEAT_DEPTH
                - measurement["finished_corner_pullback_mm"]
            ),
            "new_undercuts": False,
            "support_assessment": (
                "same enclosure orientation as the unified-R8 preview; "
                "the fairing is monotone and introduces no re-entrant lip"
            ),
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
            "cutaway_viewer": str(
                OUT / "cutaway_viewer" / "index.html"
            ),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
