"""Generate a parabolic-side, minimum-bending G1 front fairing preview.

This enclosure-only sibling leaves all preceding Le Cleac'h, unified-R8, and
custom-G2 studies unchanged.  The black-hole crest remains a 174 mm circle.
The outer front boundary follows an exact shallow parabola over the visually
straight portion of every side, followed by a short C1 corner polish to the
15 mm diagonal pullback.

Every circle-to-perimeter meridian is a cubic Hermite/Bezier curve.  Its two
tangent magnitudes are the analytic minimizers of integrated squared second
derivative for the fixed endpoint positions and tangent directions.  This is
therefore a boundary-driven G1 fairing, not a modified acoustic horn law.
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
    Face,
    Shell,
    Solid,
    Unit,
    Wire,
    export_step,
    import_step,
)
from OCP.gp import gp_Pnt


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_g2_fairing"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_g2_fairing as parent  # noqa: E402


cad = parent.cad
base = parent.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_fairing"
)

NAME = "sand_cube_190x210_parabolic_side_minimum_energy_g1_preview"
FRONT_Y = parent.FRONT_Y
INNER_CREST_RADIUS_MM = parent.INNER_CREST_RADIUS_MM
EDGE_MIDPOINT_PULLBACK_MM = parent.EDGE_MIDPOINT_PULLBACK_MM
CORNER_PULLBACK_MM = parent.CORNER_PULLBACK_MM
ANGULAR_SAMPLE_COUNT = parent.ANGULAR_SAMPLE_COUNT
CORNER_COORDINATE_MM = parent.R8_CORNER_COORDINATE_MM
PARABOLA_END_COORDINATE_MM = (
    base.D.width / 2.0 - base.D.edge_fillet_r
)
U_DEGREE = parent.U_DEGREE
V_DEGREE = 3
MINIMUM_ENERGY_TANGENT_SCALE = 1.5


def _shape_volume(shape: Any) -> float:
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _parabola_depth(side_coordinate_mm: float) -> float:
    coordinate = max(0.0, min(side_coordinate_mm, CORNER_COORDINATE_MM))
    return EDGE_MIDPOINT_PULLBACK_MM + (
        CORNER_PULLBACK_MM - EDGE_MIDPOINT_PULLBACK_MM
    ) * (coordinate / CORNER_COORDINATE_MM) ** 2


def _corner_polish_depth(side_coordinate_mm: float) -> float:
    """C1 cubic from the exact side parabola to a flat corner maximum."""
    start = PARABOLA_END_COORDINATE_MM
    end = CORNER_COORDINATE_MM
    if side_coordinate_mm <= start:
        return _parabola_depth(side_coordinate_mm)
    coordinate = min(side_coordinate_mm, end)
    span = end - start
    parameter = (coordinate - start) / span

    start_depth = _parabola_depth(start)
    start_slope = (
        2.0
        * (CORNER_PULLBACK_MM - EDGE_MIDPOINT_PULLBACK_MM)
        * start
        / CORNER_COORDINATE_MM**2
    )
    h00 = 2.0 * parameter**3 - 3.0 * parameter**2 + 1.0
    h10 = parameter**3 - 2.0 * parameter**2 + parameter
    h01 = -2.0 * parameter**3 + 3.0 * parameter**2
    return (
        h00 * start_depth
        + h10 * span * start_slope
        + h01 * CORNER_PULLBACK_MM
    )


def _pullback(theta: float) -> float:
    outer_radius = parent._outer_radius(theta)
    x = outer_radius * math.cos(theta)
    z = outer_radius * math.sin(theta)
    side_coordinate = min(abs(x), abs(z))
    return _corner_polish_depth(side_coordinate)


def _minimum_energy_control_rings() -> list[
    list[tuple[float, float, float]]
]:
    """Return four cubic control rings with analytic G1 energy minimizers."""
    rings: list[list[tuple[float, float, float]]] = [
        [] for _ in range(V_DEGREE + 1)
    ]
    for index in range(ANGULAR_SAMPLE_COUNT):
        theta = math.tau * index / ANGULAR_SAMPLE_COUNT
        cosine = math.cos(theta)
        sine = math.sin(theta)
        outer_radius = parent._outer_radius(theta)
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
        inner_tangent = np.asarray(
            (
                radial_span * cosine,
                0.0,
                radial_span * sine,
            ),
            dtype=float,
        ) * MINIMUM_ENERGY_TANGENT_SCALE
        outer_tangent = np.asarray(
            (0.0, pullback, 0.0),
            dtype=float,
        ) * MINIMUM_ENERGY_TANGENT_SCALE

        controls = (
            p0,
            p0 + inner_tangent / 3.0,
            p1 - outer_tangent / 3.0,
            p1,
        )
        for ring, point in zip(rings, controls):
            ring.append(tuple(float(value) for value in point))
    return rings


def _g1_cutter() -> tuple[Solid, Face, dict[str, Any]]:
    control_targets = _minimum_energy_control_rings()
    control_poles = [
        parent._periodic_interpolation_poles(ring)
        for ring in control_targets
    ]
    fairing_surface = parent._surface_from_poles(
        control_poles,
        v_degree=V_DEGREE,
    )
    fairing_face = parent._face_from_surface(
        fairing_surface,
        feature="parabolic-side minimum-energy G1 fairing",
    )

    front_outer_poles = control_poles[-1].copy()
    front_outer_poles[:, 1] = FRONT_Y - parent.FRONT_OVERTRAVEL_MM
    curtain_surface = parent._surface_from_poles(
        [front_outer_poles, control_poles[-1]],
        v_degree=1,
    )
    curtain_face = parent._face_from_surface(
        curtain_surface,
        feature="parabolic-side G1 outer curtain",
    )

    fairing_boundaries = [
        edge for edge in fairing_face.edges() if edge.is_closed
    ]
    curtain_boundaries = [
        edge for edge in curtain_face.edges() if edge.is_closed
    ]
    if len(fairing_boundaries) != 2 or len(curtain_boundaries) != 2:
        raise ValueError("Unexpected periodic G1 fairing boundary topology")
    inner_edge = min(fairing_boundaries, key=lambda edge: edge.length)
    front_edge = min(curtain_boundaries, key=lambda edge: edge.center().Y)
    inner_disk = Face(Wire([copy.copy(inner_edge)]))
    front_disk = Face(Wire([copy.copy(front_edge)]))

    cutter = Solid(
        Shell([fairing_face, curtain_face, inner_disk, front_disk])
    ).clean().fix()
    cutter = base._require_single_solid(
        cutter,
        feature="closed parabolic-side G1 front-material cutter",
    )
    if not parent._is_valid(cutter) or cutter.volume <= 0.0:
        raise ValueError("Parabolic-side G1 cutter is invalid")

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
        "join_class": "G1 at inner circle and outer cabinet side",
        "meridian_energy": "minimum integral of squared second derivative",
        "minimum_energy_tangent_scale": MINIMUM_ENERGY_TANGENT_SCALE,
        "maximum_outer_ring_interpolation_error_mm": interpolation_error,
        "fairing_face_area_mm2": fairing_face.area,
        "cutter_volume_mm3": cutter.volume,
    }


def _perimeter_diagnostics() -> dict[str, Any]:
    parabola_error = 0.0
    quadrant_depths: list[float] = []
    for index in range(1025):
        theta = math.pi * index / (4.0 * 1024.0)
        outer_radius = parent._outer_radius(theta)
        coordinate = min(
            abs(outer_radius * math.cos(theta)),
            abs(outer_radius * math.sin(theta)),
        )
        depth = _corner_polish_depth(coordinate)
        quadrant_depths.append(depth)
        if coordinate <= PARABOLA_END_COORDINATE_MM:
            parabola_error = max(
                parabola_error,
                abs(depth - _parabola_depth(coordinate)),
            )
    return {
        "equation": "d(s) = 8 + 7 (s / 92.656854)^2 mm",
        "exact_parabola_end_coordinate_mm": PARABOLA_END_COORDINATE_MM,
        "exact_parabola_end_pullback_mm": _parabola_depth(
            PARABOLA_END_COORDINATE_MM
        ),
        "corner_polish_span_mm": (
            CORNER_COORDINATE_MM - PARABOLA_END_COORDINATE_MM
        ),
        "maximum_exact_region_error_mm": parabola_error,
        "quadrant_pullback_monotonic": all(
            left <= right + 1e-10
            for left, right in zip(quadrant_depths, quadrant_depths[1:])
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
        ("parabolic_side_g1_enclosure.step", "viewer", True),
        (
            "parabolic_side_g1_enclosure_cutaway.step",
            "cutaway_viewer",
            False,
        ),
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
    cutter, fairing_face, fairing_topology = _g1_cutter()

    outer_boundary_targets = [
        (
            parent._outer_radius(math.tau * index / ANGULAR_SAMPLE_COUNT)
            * math.cos(math.tau * index / ANGULAR_SAMPLE_COUNT),
            FRONT_Y,
            parent._outer_radius(math.tau * index / ANGULAR_SAMPLE_COUNT)
            * math.sin(math.tau * index / ANGULAR_SAMPLE_COUNT),
        )
        for index in range(ANGULAR_SAMPLE_COUNT)
    ]
    outer_boundary_poles = parent._periodic_interpolation_poles(
        outer_boundary_targets
    )
    body, body_topology = parent._outer_body(outer_boundary_poles)
    body_topology = {
        **body_topology,
        "rear_edge_note": (
            "isolated preview compromise; front G1 fairing is unaffected"
        ),
    }
    sculpted_outer = base._require_single_solid(
        (body - cutter).clean().fix(),
        feature="parabolic-side minimum-energy G1 outer envelope",
    )

    measurement = parent._finished_measurement(sculpted_outer)
    if abs(measurement["finished_corner_pullback_mm"] - 15.0) > 0.02:
        raise ValueError("Parabolic-side G1 corner misses the 15 mm target")
    if abs(measurement["edge_midpoint_pullback_mm"] - 8.0) > 0.02:
        raise ValueError("Parabolic-side G1 midpoint misses the 8 mm target")

    cavity = base._rectangular_cavity()
    sand_void = base._sand_void()
    cavity_outside_outer_mm3 = _shape_volume(cavity - sculpted_outer)
    sand_void_outside_outer_mm3 = _shape_volume(sand_void - sculpted_outer)
    if cavity_outside_outer_mm3 > 1e-6 or sand_void_outside_outer_mm3 > 1e-6:
        raise ValueError("Parabolic-side G1 surface breaches a protected void")

    enclosure = parent._aesthetic_shell(sculpted_outer)
    original_aesthetic_shell = cad._aesthetic_shell(original_outer)
    cutaway = cad._center_cutaway(enclosure)
    if not parent._is_valid(sculpted_outer) or not parent._is_valid(enclosure):
        raise ValueError("Parabolic-side G1 enclosure geometry is invalid")

    exports = {
        "parabolic_side_g1_enclosure.step": enclosure,
        "parabolic_side_g1_enclosure_cutaway.step": cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    diagnostics = {
        "name": NAME,
        "status": "enclosure-only parabolic-side minimum-energy G1 preview",
        "isolation": {
            "experiment_dir": (
                "experiments/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_fairing"
            ),
            "output_dir": (
                "build/"
                "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_fairing"
            ),
            "unified_r8_experiment_modified": False,
            "custom_g2_experiment_modified": False,
            "authoritative_rear_corner_variant_modified": False,
            "shared_upstream_generators_modified": False,
        },
        "construction": {
            "classification": (
                "boundary-driven aesthetic fairing, not an acoustic horn law"
            ),
            "inner_boundary": {
                "radius_mm": INNER_CREST_RADIUS_MM,
                "pullback_mm": 0.0,
                "tangent": "radial in the black-hole crest plane",
            },
            "outer_boundary": {
                "edge_midpoint_pullback_mm": EDGE_MIDPOINT_PULLBACK_MM,
                "corner_pullback_mm": CORNER_PULLBACK_MM,
                **_perimeter_diagnostics(),
            },
            "meridian": {
                "type": "cubic Hermite/Bezier",
                "inner_tangent_magnitude": "1.5 x radial span",
                "outer_tangent_magnitude": "1.5 x local pullback",
                "derivation": (
                    "analytic minimizer of integral ||P''(u)||^2 du "
                    "with fixed endpoints and tangent directions"
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
            "outer_envelope_volume_delta_cm3": (
                sculpted_outer.volume - original_outer.volume
            )
            / 1000.0,
            "finished_shell_volume_delta_cm3": (
                enclosure.volume - original_aesthetic_shell.volume
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
                "monotone cubic fairing with no re-entrant lip"
            ),
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
