"""Generate 8.5 in Sand Cube variants with a face-scale black-hole baffle."""

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
    Cylinder,
    Location,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    RegularPolygon,
    Rot,
    Unit,
    add,
    export_step,
    extrude,
    fillet,
    make_face,
    revolve,
)
from bd_warehouse.thread import IsoThread

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from params import p as base_p  # noqa: E402


OUT = ROOT / "build" / "sand_cube_8_5_black_hole"

CUBE_OUTER = 8.5 * 25.4
EDGE_FILLET_R = base_p.edge_fillet_r * 1.5
RECESS_DEPTH = 0.5 * 25.4
AGGRESSIVE_BAFFLE_D = 8.3 * 25.4


@dataclass(frozen=True)
class Variant:
    name: str
    baffle_outer_d: float
    front_wall_t: float


def _oriented_cylinder(
    *,
    diameter: float,
    depth: float,
    axis: str,
    center: tuple[float, float, float],
) -> Part:
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    if axis == "x":
        cyl = Rot(0, 90, 0) * cyl
    elif axis == "y":
        cyl = Rot(90, 0, 0) * cyl
    elif axis != "z":
        raise ValueError(f"Unsupported axis: {axis}")
    return Location(center) * cyl


def _primary_shape(shape):
    if hasattr(shape, "bounding_box"):
        return shape
    return max(shape, key=lambda item: item.volume)


def _external_cube_edges(part: Part, *, cube_outer: float) -> list:
    half = cube_outer / 2
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = (bb.size.X, bb.size.Y, bb.size.Z)
        centers = (
            (bb.min.X + bb.max.X) / 2,
            (bb.min.Y + bb.max.Y) / 2,
            (bb.min.Z + bb.max.Z) / 2,
        )
        pinned_axes = sum(
            abs(abs(center) - half) < 0.01 and size < 0.01
            for center, size in zip(centers, sizes)
        )
        if pinned_axes >= 2 and max(sizes) > cube_outer * 0.55:
            edges.append(edge)
    return edges


def _bolt_circle_bores(
    params,
    *,
    radius: float,
    count: int,
    bore_depth: float,
    bore_open_y: float,
    bore_direction_y: int,
) -> Part:
    bore_center_y = bore_open_y + bore_direction_y * bore_depth / 2
    with BuildPart() as bores:
        for index in range(count):
            angle = math.tau * index / count + (math.tau / 8 if count == 4 else 0)
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            add(
                _oriented_cylinder(
                    diameter=params.insert_bore_d,
                    depth=bore_depth,
                    axis="y",
                    center=(x, bore_center_y, z),
                )
            )
    return bores.part


def _hex_prism_y(
    *,
    across_flats: float,
    depth: float,
    center: tuple[float, float, float],
    rotation: float = 30.0,
) -> Part:
    with BuildPart() as hex_prism:
        with BuildSketch(Plane.XZ):
            RegularPolygon(
                radius=across_flats / 2,
                side_count=6,
                major_radius=False,
                rotation=rotation,
            )
        extrude(amount=depth / 2, both=True)
    return Location(center) * hex_prism.part


def _gx16_rear_cutout(params) -> Part:
    half = params.cube_outer / 2
    panel_inner_y = half - params.gx16_flange_recess_depth - params.gx16_panel_land_t
    inner_face_y = half - params.rear_cap_t
    hex_depth = panel_inner_y - inner_face_y + 0.2
    hex_center_y = inner_face_y + hex_depth / 2 - 0.1
    hex_to_pr_angle = math.degrees(math.atan2(-params.gx16_z, -params.gx16_x))
    with BuildPart() as cutout:
        add(
            _oriented_cylinder(
                diameter=params.gx16_flange_recess_d,
                depth=params.gx16_flange_recess_depth,
                axis="y",
                center=(
                    params.gx16_x,
                    half - params.gx16_flange_recess_depth / 2,
                    params.gx16_z,
                ),
            )
        )
        add(
            _oriented_cylinder(
                diameter=params.gx16_hole_d,
                depth=params.rear_cap_t + 2,
                axis="y",
                center=(params.gx16_x, half - params.rear_cap_t / 2, params.gx16_z),
            )
        )
        add(
            _hex_prism_y(
                across_flats=params.gx16_nut_across_flats,
                depth=hex_depth,
                center=(params.gx16_x, hex_center_y, params.gx16_z),
                rotation=hex_to_pr_angle - 30.0,
            )
        )
    return cutout.part


def _gx16_connector_island(params) -> Part:
    half = params.cube_outer / 2
    return Pos(params.gx16_x, half - params.rear_cap_t / 2, params.gx16_z) * Box(
        params.gx16_island_xy,
        params.rear_cap_t,
        params.gx16_island_xy,
    )


def _sand_fill_port_cutout(params, *, x: float, z: float) -> Part:
    half = params.cube_outer / 2
    port_depth = params.rear_cap_t + 0.8
    thread_center_y = half - params.fill_thread_length / 2 + 0.2
    port_center_y = half - port_depth / 2
    thread = IsoThread(
        major_diameter=params.fill_thread_major_d,
        pitch=params.fill_thread_pitch,
        length=params.fill_thread_length,
        external=False,
        end_finishes=("square", "fade"),
        interference=0.35,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    with BuildPart() as cutout:
        add(
            _oriented_cylinder(
                diameter=params.fill_entry_d,
                depth=params.fill_entry_depth,
                axis="y",
                center=(x, half - params.fill_entry_depth / 2, z),
            )
        )
        add(
            _oriented_cylinder(
                diameter=params.fill_thread_core_d,
                depth=port_depth,
                axis="y",
                center=(x, port_center_y, z),
            )
        )
        add(Location((x, thread_center_y, z)) * Rot(90, 0, 0) * thread)
    return cutout.part


def _grid3_for_span(span: float) -> tuple[float, float, float]:
    current_cavity = base_p.cube_outer - 2 * (
        base_p.outer_skin_t + base_p.void_t + base_p.inner_skin_t
    )
    current_margin = current_cavity / 2 - 60.0
    outer = span / 2 - current_margin
    return (-outer, 0.0, outer)


def _skin_bridge_posts(params, *, cavity_y_span: float) -> Part:
    half = params.cube_outer / 2
    void_center = half - params.outer_skin_t - params.void_t / 2
    cavity_side = params.cube_outer - 2 * (
        params.outer_skin_t + params.void_t + params.inner_skin_t
    )
    grid_xz = _grid3_for_span(cavity_side)
    grid_y = _grid3_for_span(cavity_y_span)

    def in_top_island(x: float, y: float) -> bool:
        return (
            abs(x - params.top_island_x) <= params.top_island_w / 2
            and abs(y - params.top_island_y) <= params.top_island_d / 2
        )

    with BuildPart() as posts:
        for y in grid_y:
            for z in grid_xz:
                for side in (-1, 1):
                    add(
                        _oriented_cylinder(
                            diameter=params.bracing_post_d,
                            depth=params.void_t,
                            axis="x",
                            center=(side * void_center, y, z),
                        )
                    )
        for x in grid_xz:
            for y in grid_y:
                for side in (-1, 1):
                    if side > 0 and in_top_island(x, y):
                        continue
                    add(
                        _oriented_cylinder(
                            diameter=params.bracing_post_d,
                            depth=params.void_t,
                            axis="z",
                            center=(x, y, side * void_center),
                        )
                    )
    return posts.part


def _top_reinforcement_island(params) -> Part:
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    return Pos(params.top_island_x, params.top_island_y, half - top_stack_t / 2) * Box(
        params.top_island_w,
        params.top_island_d,
        top_stack_t,
    )


def _top_binding_post_cutouts(params) -> Part:
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    inner_top_z = half - top_stack_t
    with BuildPart() as cutouts:
        for x in (-params.binding_post_spacing / 2, params.binding_post_spacing / 2):
            add(
                _oriented_cylinder(
                    diameter=params.binding_post_recess_d,
                    depth=params.binding_post_recess_depth,
                    axis="z",
                    center=(
                        x,
                        params.binding_post_y,
                        half - params.binding_post_recess_depth / 2,
                    ),
                )
            )
            add(
                _oriented_cylinder(
                    diameter=params.binding_post_hole_d,
                    depth=top_stack_t + 2.0,
                    axis="z",
                    center=(x, params.binding_post_y, half - top_stack_t / 2),
                )
            )
            add(
                _oriented_cylinder(
                    diameter=params.binding_post_washer_recess_d,
                    depth=params.binding_post_washer_recess_depth,
                    axis="z",
                    center=(
                        x,
                        params.binding_post_y,
                        inner_top_z + params.binding_post_washer_recess_depth / 2,
                    ),
                )
            )
    return cutouts.part


def _top_bracket_cutouts(params) -> Part:
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    inner_top_z = half - top_stack_t
    spacing = params.bracket_hole_spacing / 2
    with BuildPart() as cutouts:
        for x in (-spacing, spacing):
            for y in (
                params.bracket_hole_y - spacing,
                params.bracket_hole_y + spacing,
            ):
                add(
                    _oriented_cylinder(
                        diameter=params.bracket_hole_d,
                        depth=top_stack_t + 2.0,
                        axis="z",
                        center=(x, y, half - top_stack_t / 2),
                    )
                )
                add(
                    _oriented_cylinder(
                        diameter=params.bracket_washer_recess_d,
                        depth=params.bracket_washer_recess_depth,
                        axis="z",
                        center=(
                            x,
                            y,
                            inner_top_z + params.bracket_washer_recess_depth / 2,
                        ),
                    )
                )
    return cutouts.part


def _front_curve_controls(
    *,
    r_outer: float,
    r_inner: float,
    depth: float,
) -> tuple[tuple[float, float], ...]:
    radial_span = r_outer - r_inner
    return (
        (r_outer, 0.0),
        (r_outer - radial_span * 0.65, 0.0),
        (r_inner, depth * 0.22),
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
    controls = _front_curve_controls(r_outer=r_outer, r_inner=r_inner, depth=depth)
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


def _front_black_hole_tool(params, variant: Variant) -> Part:
    r_outer = variant.baffle_outer_d / 2
    r_inner = params.driver_cutout_dia / 2
    floor = RECESS_DEPTH + variant.front_wall_t + 2.0
    controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=RECESS_DEPTH,
    )
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Bezier(*controls)
                Polyline(
                    (r_inner, RECESS_DEPTH),
                    (r_inner, floor),
                    (0.0, floor),
                    (0.0, -2.0),
                    (r_outer, -2.0),
                    (r_outer, 0.0),
                )
            make_face()
        assert sketch.sketch.area > 0, "Front baffle tool sketch must be positive"
        revolve(axis=Axis.Z)
    return tool.part


def _inner_relief_tool(params, variant: Variant) -> Part:
    r_outer = variant.baffle_outer_d / 2
    r_inner = params.driver_cutout_dia / 2
    r_collar = params.driver_mount_collar_od / 2
    outside_r = math.sqrt(2) * params.cube_outer / 2 + 10.0
    cap_depth = RECESS_DEPTH + variant.front_wall_t
    controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=RECESS_DEPTH,
    )

    with BuildPart() as relief:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Polyline(
                    (r_collar, cap_depth),
                    (outside_r, cap_depth),
                    (outside_r, variant.front_wall_t),
                    (r_outer, variant.front_wall_t),
                )
                Bezier(
                    (r_outer, variant.front_wall_t),
                    (controls[1][0], controls[1][1] + variant.front_wall_t),
                    (r_collar, cap_depth - (cap_depth - variant.front_wall_t) * 0.22),
                    (r_collar, cap_depth),
                )
            make_face()
        assert sketch.sketch.area > 0, "Inner relief sketch must be positive"
        revolve(axis=Axis.Z)
    return relief.part


def _front_tool_global(tool: Part, params) -> Part:
    half = params.cube_outer / 2
    return Pos(0, -half, 0) * Rot(-90, 0, 0) * tool


def build_variant(variant: Variant) -> tuple[Part, dict[str, object]]:
    params = replace(
        base_p,
        cube_outer=CUBE_OUTER,
        edge_fillet_r=EDGE_FILLET_R,
        front_cap_t=RECESS_DEPTH + variant.front_wall_t,
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

    enclosure -= _front_tool_global(_front_black_hole_tool(params, variant), params)
    enclosure = _primary_shape(enclosure)

    relief = _front_tool_global(_inner_relief_tool(params, variant), params)
    relief_clip = Pos(
        0,
        -half + params.front_cap_t / 2,
        0,
    ) * Box(cavity_side, params.front_cap_t + 0.5, cavity_side)
    enclosure -= relief & relief_clip
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

    enclosure -= _oriented_cylinder(
        diameter=params.driver_cutout_dia,
        depth=through,
        axis="y",
        center=(0, -half, 0),
    )
    enclosure = _primary_shape(enclosure)
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
        r_outer=variant.baffle_outer_d / 2,
        r_inner=params.driver_cutout_dia / 2,
        depth=RECESS_DEPTH,
    )
    seat_depth = params.front_cap_t
    insert_tip_depth = seat_depth - params.driver_insert_bore_depth
    insert_front_clearance = insert_tip_depth - bolt_front_depth

    bb = enclosure.bounding_box()
    nominal_cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000
    diagnostics = {
        "name": variant.name,
        "cube_outer_mm": params.cube_outer,
        "cube_outer_in": params.cube_outer / 25.4,
        "edge_fillet_r_mm": params.edge_fillet_r,
        "front_wall_t_mm": variant.front_wall_t,
        "front_recess_depth_mm": RECESS_DEPTH,
        "baffle_outer_d_mm": variant.baffle_outer_d,
        "driver_cutout_dia_mm": params.driver_cutout_dia,
        "driver_mount_collar_od_mm": params.driver_mount_collar_od,
        "front_seat_y_mm": front_inner_y,
        "nominal_cavity_l": round(nominal_cavity_l, 3),
        "driver_insert": {
            "bolt_circle_r_mm": params.driver_bolt_circle_r,
            "bore_depth_mm": params.driver_insert_bore_depth,
            "front_surface_depth_at_bolt_mm": round(bolt_front_depth, 3),
            "wall_at_bolt_mm": round(seat_depth - bolt_front_depth, 3),
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
    conservative_d = CUBE_OUTER - 2 * EDGE_FILLET_R
    variants = [
        Variant("conservative_wall_10", conservative_d, 10.0),
        Variant("conservative_wall_12", conservative_d, 12.0),
        Variant("aggressive_wall_10", AGGRESSIVE_BAFFLE_D, 10.0),
        Variant("aggressive_wall_12", AGGRESSIVE_BAFFLE_D, 12.0),
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
        OUT / "sand_cube_8_5_black_hole_comparison.step",
        unit=Unit.MM,
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
