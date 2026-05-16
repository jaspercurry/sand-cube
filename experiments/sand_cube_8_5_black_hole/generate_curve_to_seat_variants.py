"""Generate curve-to-driver-seat variants with no cylindrical throat gap."""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Bezier,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Compound,
    Location,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    Rot,
    Unit,
    add,
    export_step,
    fillet,
    make_face,
    revolve,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from generate_variants import (  # noqa: E402
    CUBE_OUTER,
    EDGE_FILLET_R,
    _bolt_circle_bores,
    _gx16_connector_island,
    _gx16_rear_cutout,
    _grid3_for_span,
    _oriented_cylinder,
    _primary_shape,
    _sand_fill_port_cutout,
    _skin_bridge_posts,
    _top_binding_post_cutouts,
    _top_bracket_cutouts,
    _top_reinforcement_island,
)
from params import p as base_p  # noqa: E402


OUT = ROOT / "build" / "sand_cube_8_5_black_hole" / "curve_to_seat"
BAFFLE_OUTER_D = CUBE_OUTER - 2 * EDGE_FILLET_R


@dataclass(frozen=True)
class Variant:
    name: str
    recess_depth: float


def _curve_controls(
    *,
    r_outer: float,
    r_inner: float,
    depth: float,
) -> tuple[tuple[float, float], ...]:
    """Scale the original Sand Cube black-hole profile to the larger face."""
    radial_span = r_outer - r_inner
    return (
        (r_outer, 0.0),
        (r_outer - radial_span * base_p.baffle_tangent_in, 0.0),
        (r_inner, depth * (1 - base_p.baffle_tangent_out)),
        (r_inner, depth),
    )


def _bezier_point(
    controls: tuple[tuple[float, float], ...],
    t: float,
) -> tuple[float, float]:
    mt = 1 - t
    return (
        mt**3 * controls[0][0]
        + 3 * mt**2 * t * controls[1][0]
        + 3 * mt * t**2 * controls[2][0]
        + t**3 * controls[3][0],
        mt**3 * controls[0][1]
        + 3 * mt**2 * t * controls[1][1]
        + 3 * mt * t**2 * controls[2][1]
        + t**3 * controls[3][1],
    )


def _front_depth_at_radius(
    *,
    radius: float,
    r_outer: float,
    r_inner: float,
    depth: float,
) -> float:
    controls = _curve_controls(r_outer=r_outer, r_inner=r_inner, depth=depth)
    low = 0.0
    high = 1.0
    for _ in range(64):
        mid = (low + high) / 2
        r_mid, _depth_mid = _bezier_point(controls, mid)
        if r_mid > radius:
            low = mid
        else:
            high = mid
    return _bezier_point(controls, (low + high) / 2)[1]


def _curve_to_seat_tool(params, variant: Variant) -> Part:
    r_outer = BAFFLE_OUTER_D / 2
    r_inner = params.driver_cutout_dia / 2
    controls = _curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=variant.recess_depth,
    )
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Bezier(*controls)
                # Stop the central opening at the driver-seat plane. The
                # acoustic cavity starts immediately behind this plane, so no
                # straight cylindrical throat continues after the curve.
                Polyline(
                    (r_inner, variant.recess_depth),
                    (0.0, variant.recess_depth),
                    (0.0, -2.0),
                    (r_outer, -2.0),
                    (r_outer, 0.0),
                )
            make_face()
        assert sketch.sketch.area > 0, "Curve-to-seat sketch must be positive"
        revolve(axis=Axis.Z)
    return tool.part


def _front_tool_global(tool: Part, params) -> Part:
    half = params.cube_outer / 2
    return Pos(0, -half, 0) * Rot(-90, 0, 0) * tool


def build_variant(variant: Variant) -> tuple[Part, dict[str, object]]:
    params = replace(
        base_p,
        cube_outer=CUBE_OUTER,
        edge_fillet_r=EDGE_FILLET_R,
        front_cap_t=variant.recess_depth,
    )

    half = params.cube_outer / 2
    shell_span = params.cube_outer - 2 * params.outer_skin_t
    cavity_side = params.cube_outer - 2 * (
        params.outer_skin_t + params.void_t + params.inner_skin_t
    )
    front_inner_y = -half + params.front_cap_t
    rear_inner_y = half - params.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    cavity_center_y = (front_inner_y + rear_inner_y) / 2
    through = params.cube_outer + 10

    outer_solid = Box(params.cube_outer, params.cube_outer, params.cube_outer)
    if params.edge_fillet_r > 0:
        outer_solid = fillet(outer_solid.edges(), radius=params.edge_fillet_r)
        outer_solid = _primary_shape(outer_solid)

    acoustic_cavity = Pos(0, cavity_center_y, 0) * Box(
        cavity_side,
        cavity_y,
        cavity_side,
    )
    enclosure = outer_solid - acoustic_cavity

    for x in (-1, 1):
        enclosure -= Pos(
            x * (half - params.outer_skin_t - params.void_t / 2),
            cavity_center_y,
            0,
        ) * Box(
            params.void_t,
            cavity_y,
            shell_span,
        )
    for z in (-1, 1):
        enclosure -= Pos(
            0,
            cavity_center_y,
            z * (half - params.outer_skin_t - params.void_t / 2),
        ) * Box(
            shell_span,
            cavity_y,
            params.void_t,
        )
    enclosure = _primary_shape(enclosure)

    enclosure += _skin_bridge_posts(params, cavity_y_span=cavity_y)
    enclosure = _primary_shape(enclosure)
    enclosure += _gx16_connector_island(params)
    enclosure = _primary_shape(enclosure)
    enclosure += _top_reinforcement_island(params)
    enclosure = _primary_shape(enclosure)

    enclosure -= _front_tool_global(_curve_to_seat_tool(params, variant), params)
    enclosure = _primary_shape(enclosure)

    driver_insert_bores = _bolt_circle_bores(
        params,
        radius=params.driver_bolt_circle_r,
        count=params.driver_screw_count,
        bore_depth=params.driver_insert_bore_depth,
        bore_open_y=front_inner_y,
        bore_direction_y=-1,
    )
    pr_insert_bores = _bolt_circle_bores(
        params,
        radius=params.pr_bolt_circle_r,
        count=params.pr_screw_count,
        bore_depth=params.pr_insert_bore_depth,
        bore_open_y=half - params.pr_recess_depth,
        bore_direction_y=-1,
    )

    # No separate front driver cylinder: the curve tool already opens the
    # driver cutout to the exact rear mounting plane.
    enclosure -= _oriented_cylinder(
        diameter=params.pr_recess_dia,
        depth=params.pr_recess_depth,
        axis="y",
        center=(0, half - params.pr_recess_depth / 2, 0),
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= _oriented_cylinder(
        diameter=params.pr_service_cutout_dia,
        depth=through,
        axis="y",
        center=(0, half, 0),
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= driver_insert_bores
    enclosure = _primary_shape(enclosure)
    enclosure -= pr_insert_bores
    enclosure = _primary_shape(enclosure)
    enclosure -= _gx16_rear_cutout(params)
    enclosure = _primary_shape(enclosure)
    for fill_x in (-params.fill_port_x, params.fill_port_x):
        enclosure -= _sand_fill_port_cutout(params, x=fill_x, z=params.fill_port_z)
        enclosure = _primary_shape(enclosure)
    enclosure -= _top_binding_post_cutouts(params)
    enclosure = _primary_shape(enclosure)
    enclosure -= _top_bracket_cutouts(params)
    enclosure = _primary_shape(enclosure)

    bolt_front_depth = _front_depth_at_radius(
        radius=params.driver_bolt_circle_r,
        r_outer=BAFFLE_OUTER_D / 2,
        r_inner=params.driver_cutout_dia / 2,
        depth=variant.recess_depth,
    )
    insert_tip_depth = variant.recess_depth - params.driver_insert_bore_depth
    insert_front_clearance = insert_tip_depth - bolt_front_depth

    bb = enclosure.bounding_box()
    nominal_cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000
    diagnostics = {
        "name": variant.name,
        "cube_outer_mm": params.cube_outer,
        "cube_outer_in": params.cube_outer / 25.4,
        "edge_fillet_r_mm": params.edge_fillet_r,
        "front_recess_depth_mm": variant.recess_depth,
        "front_recess_depth_in": variant.recess_depth / 25.4,
        "baffle_outer_d_mm": BAFFLE_OUTER_D,
        "driver_cutout_dia_mm": params.driver_cutout_dia,
        "front_seat_y_mm": front_inner_y,
        "nominal_cavity_l": round(nominal_cavity_l, 3),
        "driver_insert": {
            "bolt_circle_r_mm": params.driver_bolt_circle_r,
            "bore_depth_mm": params.driver_insert_bore_depth,
            "front_surface_depth_at_bolt_mm": round(bolt_front_depth, 3),
            "wall_at_bolt_mm": round(variant.recess_depth - bolt_front_depth, 3),
            "clearance_in_front_of_insert_tip_mm": round(insert_front_clearance, 3),
            "pierce_risk": insert_front_clearance < 1.5,
        },
        "bridge_post_grid": {
            "xz_positions_mm": [round(v, 3) for v in _grid3_for_span(cavity_side)],
            "y_positions_mm": [round(v, 3) for v in _grid3_for_span(cavity_y)],
        },
        "bounding_box_mm": [
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ],
        "volume_cm3": round(enclosure.volume / 1000, 3),
        "is_valid": enclosure.is_valid,
        "n_solids": len(enclosure.solids()),
        "n_faces": len(enclosure.faces()),
        "n_edges": len(enclosure.edges()),
    }
    return enclosure, diagnostics


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    variants = [
        Variant("curve_to_seat_depth_0_75", 0.75 * 25.4),
        Variant("curve_to_seat_depth_1_00", 1.0 * 25.4),
        Variant("curve_to_seat_depth_1_25", 1.25 * 25.4),
    ]
    diagnostics: list[dict[str, object]] = []
    comparison_parts: list[Part] = []
    spacing = CUBE_OUTER + 70.0
    offset0 = -spacing * (len(variants) - 1) / 2

    for index, variant in enumerate(variants):
        part, data = build_variant(variant)
        if not data["is_valid"]:
            raise ValueError(f"{variant.name} generated an invalid body")
        export_step(part, OUT / f"{variant.name}.step", unit=Unit.MM)
        diagnostics.append(data)
        comparison_parts.append(Location((offset0 + index * spacing, 0, 0)) * part)

    export_step(
        Compound(comparison_parts),
        OUT / "curve_to_seat_comparison.step",
        unit=Unit.MM,
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
