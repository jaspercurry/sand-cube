"""One-piece compact 6 in sand-filled enclosure."""

from __future__ import annotations

import math

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
    Rot,
    Unit,
    add,
    export_step,
    fillet,
    make_face,
    revolve,
)

from src.features.baffle import black_hole_baffle

from .params import CompactParams, p


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
        raise ValueError(f"Unsupported cylinder axis: {axis}")
    return Location(center) * cyl


def _primary_shape(shape):
    if hasattr(shape, "bounding_box"):
        return shape
    return max(shape, key=lambda item: item.volume)


def _bolt_circle_positions(
    *,
    radius: float,
    count: int,
    phase: float = math.tau / 8,
) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(math.tau * index / count + phase),
            radius * math.sin(math.tau * index / count + phase),
        )
        for index in range(count)
    ]


def _bezier_point(
    controls: tuple[tuple[float, float], ...],
    t: float,
) -> tuple[float, float]:
    points = [*controls]
    while len(points) > 1:
        points = [
            (
                points[index][0] + (points[index + 1][0] - points[index][0]) * t,
                points[index][1] + (points[index + 1][1] - points[index][1]) * t,
            )
            for index in range(len(points) - 1)
        ]
    return points[0]


def _split_cubic_left(
    controls: tuple[tuple[float, float], ...],
    t: float,
) -> tuple[tuple[float, float], ...]:
    p01 = _lerp(controls[0], controls[1], t)
    p12 = _lerp(controls[1], controls[2], t)
    p23 = _lerp(controls[2], controls[3], t)
    p012 = _lerp(p01, p12, t)
    p123 = _lerp(p12, p23, t)
    p0123 = _lerp(p012, p123, t)
    return (controls[0], p01, p012, p0123)


def _lerp(
    start: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t,
    )


def _front_curve_controls(
    params: CompactParams,
) -> tuple[tuple[float, float], ...]:
    r_outer = params.driver_cutout_dia / 2 + params.driver_baffle_blend_r
    r_inner = params.driver_cutout_dia / 2
    depth = params.driver_baffle_blend_depth
    return (
        (r_outer, 0.0),
        (
            r_outer - params.driver_baffle_blend_r * params.driver_baffle_tangent_in,
            0.0,
        ),
        (r_inner, depth * (1 - params.driver_baffle_tangent_out)),
        (r_inner, depth),
    )


def _curve_t_at_radius(
    *,
    controls: tuple[tuple[float, float], ...],
    radius: float,
) -> float:
    low = 0.0
    high = 1.0
    for _ in range(64):
        mid = (low + high) / 2
        mid_r, _mid_depth = _bezier_point(controls, mid)
        if mid_r > radius:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def _bridge_grid(params: CompactParams) -> tuple[float, float, float]:
    outer = min(38.0, params.cavity_side / 2 - 20.0)
    return (-outer, 0.0, outer)


def _bridge_y_grid(params: CompactParams) -> tuple[float, float, float]:
    cavity_center_y = (
        params.enclosure_depth_y / 2 - params.rear_cap_t - params.cavity_y / 2
    )
    outer = min(38.0, params.cavity_y / 2 - 20.0)
    return (
        cavity_center_y - outer,
        cavity_center_y,
        cavity_center_y + outer,
    )


def _filleted_box(
    x_size: float,
    y_size: float,
    z_size: float,
    *,
    radius: float,
) -> Part:
    box = Box(x_size, y_size, z_size, mode=Mode.PRIVATE)
    if radius <= 0:
        return box
    try:
        return _primary_shape(fillet(box.edges(), radius=radius))
    except ValueError:
        return box


def _front_tool_global(tool: Part, params: CompactParams) -> Part:
    front_y = -params.enclosure_depth_y / 2
    return Pos(0, front_y, 0) * Rot(-90, 0, 0) * tool


def _sand_void_cutouts(params: CompactParams) -> Part:
    """Cut only the side/top/bottom sand voids, not the front/rear caps."""
    half = params.cube_outer / 2
    # Keep sand voids clear of the exterior corner fillets. If these panels run
    # into the rounded-edge zone, the outer fillet opens visible slots.
    shell_span = params.cube_outer - 2 * (params.edge_fillet_r + 0.5)
    void_center = half - params.outer_skin_t - params.void_t / 2
    cavity_center_y = (
        params.enclosure_depth_y / 2 - params.rear_cap_t - params.cavity_y / 2
    )
    with BuildPart() as voids:
        for side in (-1, 1):
            add(
                Pos(side * void_center, cavity_center_y, 0)
                * _filleted_box(
                    params.void_t,
                    params.cavity_y,
                    shell_span,
                    radius=params.sand_void_fillet_r,
                )
            )
            add(
                Pos(0, cavity_center_y, side * void_center)
                * _filleted_box(
                    shell_span,
                    params.cavity_y,
                    params.void_t,
                    radius=params.sand_void_fillet_r,
                )
            )
    return voids.part


def _cutout_collars(params: CompactParams) -> Part:
    """Local solid sleeves sealing sand voids around functional rear cutouts."""
    rear_face_y = params.enclosure_depth_y / 2
    rear_y = rear_face_y - params.rear_cap_t / 2
    with BuildPart() as collars:
        add(
            _oriented_cylinder(
                diameter=params.pr_recess_dia + params.cutout_collar_extra_d / 2,
                depth=params.rear_cap_t,
                axis="y",
                center=(0, rear_y, 0),
            )
        )
        add(
            _oriented_cylinder(
                diameter=params.gx16_collar_od,
                depth=params.rear_cap_t,
                axis="y",
                center=(params.gx16_x, rear_y, params.gx16_z),
            )
        )
        for x in (-params.fill_port_x, params.fill_port_x):
            add(
                _oriented_cylinder(
                    diameter=params.fill_entry_d + 3.0,
                    depth=params.rear_cap_t,
                    axis="y",
                    center=(x, rear_y, params.fill_port_z),
                )
            )
    return collars.part


def _skin_bridge_posts(params: CompactParams) -> Part:
    """Point-like bridges in the side/top/bottom sand voids."""
    half = params.cube_outer / 2
    rear_face_y = params.enclosure_depth_y / 2
    void_center = half - params.outer_skin_t - params.void_t / 2
    grid = _bridge_grid(params)
    cavity_y_grid = _bridge_y_grid(params)
    bridge_depth = params.void_t + 0.4
    rear_keepout_r = params.pr_recess_dia / 2 + params.bracing_post_d

    def near_rear_cutout(y: float, z: float) -> bool:
        rear_zone = y > rear_face_y - params.rear_cap_t - 6.0
        gx16_near = (
            math.hypot(y - rear_face_y, z - params.gx16_z)
            < params.gx16_collar_od / 2 + params.bracing_post_d
        )
        return rear_zone and gx16_near

    def near_top_fill(x: float, y: float) -> bool:
        rear_zone = y > rear_face_y - params.rear_cap_t - 6.0
        return rear_zone and any(
            abs(x - port_x) < params.fill_entry_d / 2 + params.bracing_post_d
            for port_x in (-params.fill_port_x, params.fill_port_x)
        )

    with BuildPart() as posts:
        for side in (-1, 1):
            for y in cavity_y_grid:
                for z in grid:
                    if side > 0 and abs(z) < 0.01:
                        continue
                    if side > 0 and near_rear_cutout(y, z):
                        continue
                    add(
                        _oriented_cylinder(
                            diameter=params.bracing_post_d,
                            depth=bridge_depth,
                            axis="x",
                            center=(side * void_center, y, z),
                        )
                    )
        for side in (-1, 1):
            for x in grid:
                for y in cavity_y_grid:
                    if side < 0 and abs(x) < 0.01:
                        continue
                    if side > 0 and near_top_fill(x, y):
                        continue
                    add(
                        _oriented_cylinder(
                            diameter=params.bracing_post_d,
                            depth=bridge_depth,
                            axis="z",
                            center=(x, y, side * void_center),
                        )
                    )
    return posts.part


def _front_baffle_cutout(params: CompactParams) -> Part:
    return _front_tool_global(
        black_hole_baffle(
            face_thickness=params.front_cap_t,
            driver_cutout_dia=params.driver_cutout_dia,
            blend_radius=params.driver_baffle_blend_r,
            blend_depth=params.driver_baffle_blend_depth,
            tangent_in=params.driver_baffle_tangent_in,
            tangent_out=params.driver_baffle_tangent_out,
        ),
        params,
    )


def _front_inner_relief_tool(params: CompactParams) -> Part:
    """Cavity-side relief that follows the visible baffle curve.

    The relief leaves a flat rear driver-seat annulus around the cutout and
    insert bores, then removes front-cap material outside that land.
    """
    r_outer = params.driver_cutout_dia / 2 + params.driver_baffle_blend_r
    r_seat = params.driver_seat_land_od / 2
    outside_r = math.sqrt(2) * params.cube_outer / 2 + 8.0
    seat_depth = params.front_cap_t
    front_controls = _front_curve_controls(params)
    seat_t = _curve_t_at_radius(controls=front_controls, radius=r_seat)
    inner_controls = tuple(
        (radius, depth + params.driver_baffle_wall_t)
        for radius, depth in _split_cubic_left(front_controls, seat_t)
    )

    with BuildPart() as relief:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Polyline(
                    (r_seat, seat_depth),
                    (outside_r, seat_depth),
                    (outside_r, params.driver_baffle_wall_t),
                    (r_outer, params.driver_baffle_wall_t),
                )
                Bezier(*inner_controls)
                Polyline(
                    inner_controls[-1],
                    (r_seat, seat_depth),
                )
            make_face()
        assert sketch.sketch.area > 0, "Front inner relief sketch must be positive"
        revolve(axis=Axis.Z)
    return relief.part


def _front_inner_relief_cutout(params: CompactParams) -> Part:
    front_y = -params.enclosure_depth_y / 2
    relief = _front_tool_global(_front_inner_relief_tool(params), params)
    relief_clip = Pos(0, front_y + params.front_cap_t / 2, 0) * Box(
        params.cavity_side,
        params.front_cap_t + 0.5,
        params.cavity_side,
        mode=Mode.PRIVATE,
    )
    return relief & relief_clip


def _driver_rear_mount_bores(params: CompactParams) -> Part:
    front_inner_y = (
        params.enclosure_depth_y / 2
        - params.rear_cap_t
        - params.cavity_y
    )
    bore_center_y = front_inner_y - params.driver_insert_bore_depth / 2
    with BuildPart() as bores:
        for x, z in _bolt_circle_positions(
            radius=params.driver_bolt_circle_dia / 2,
            count=params.driver_screw_count,
        ):
            add(
                _oriented_cylinder(
                    diameter=params.driver_insert_bore_d,
                    depth=params.driver_insert_bore_depth,
                    axis="y",
                    center=(x, bore_center_y, z),
                )
            )
    return bores.part


def _pr_cutouts(params: CompactParams) -> Part:
    rear_face_y = params.enclosure_depth_y / 2
    through = params.rear_cap_t + 2.0
    with BuildPart() as cutouts:
        add(
            _oriented_cylinder(
                diameter=params.pr_recess_dia,
                depth=params.pr_recess_depth,
                axis="y",
                center=(0, rear_face_y - params.pr_recess_depth / 2, 0),
            )
        )
        add(
            _oriented_cylinder(
                diameter=params.pr_cutout_dia,
                depth=through,
                axis="y",
                center=(0, rear_face_y - params.rear_cap_t / 2, 0),
            )
        )
        for x, z in _bolt_circle_positions(
            radius=params.pr_bolt_circle_dia / 2,
            count=params.pr_screw_count,
        ):
            add(
                _oriented_cylinder(
                    diameter=params.pr_screw_clearance_d,
                    depth=through,
                    axis="y",
                    center=(x, rear_face_y - params.rear_cap_t / 2, z),
                )
            )
    return cutouts.part


def _gx16_cutout(params: CompactParams) -> Part:
    rear_face_y = params.enclosure_depth_y / 2
    through = params.rear_cap_t + 2.0
    with BuildPart() as cutout:
        add(
            _oriented_cylinder(
                diameter=params.gx16_flange_recess_d,
                depth=params.gx16_flange_recess_depth,
                axis="y",
                center=(
                    params.gx16_x,
                    rear_face_y - params.gx16_flange_recess_depth / 2,
                    params.gx16_z,
                ),
            )
        )
        add(
            _oriented_cylinder(
                diameter=params.gx16_hole_d,
                depth=through,
                axis="y",
                center=(
                    params.gx16_x,
                    rear_face_y - params.rear_cap_t / 2,
                    params.gx16_z,
                ),
            )
        )
    return cutout.part


def _fill_port_cutouts(params: CompactParams) -> Part:
    rear_face_y = params.enclosure_depth_y / 2
    through = params.rear_cap_t + 1.0
    with BuildPart() as cutouts:
        for x in (-params.fill_port_x, params.fill_port_x):
            add(
                _oriented_cylinder(
                    diameter=params.fill_entry_d,
                    depth=params.fill_entry_depth,
                    axis="y",
                    center=(
                        x,
                        rear_face_y - params.fill_entry_depth / 2,
                        params.fill_port_z,
                    ),
                )
            )
            add(
                _oriented_cylinder(
                    diameter=params.fill_port_d,
                    depth=through,
                    axis="y",
                    center=(x, rear_face_y - params.rear_cap_t / 2, params.fill_port_z),
                )
            )
    return cutouts.part


def build(params: CompactParams = p) -> tuple[Part, dict[str, object]]:
    """Build the corrected one-piece compact enclosure."""
    half = params.cube_outer / 2
    rear_face_y = params.enclosure_depth_y / 2
    cavity_center_y = rear_face_y - params.rear_cap_t - params.cavity_y / 2
    outer = Box(params.cube_outer, params.enclosure_depth_y, params.cube_outer)
    if params.edge_fillet_r > 0:
        outer = _primary_shape(fillet(outer.edges(), radius=params.edge_fillet_r))

    acoustic_cavity = _filleted_box(
        params.cavity_side,
        params.cavity_y,
        params.cavity_side,
        radius=params.internal_fillet_r,
    )
    acoustic_cavity = Pos(0, cavity_center_y, 0) * acoustic_cavity
    enclosure = _primary_shape(outer - acoustic_cavity)
    enclosure -= _sand_void_cutouts(params)
    enclosure = _primary_shape(enclosure)
    enclosure += _skin_bridge_posts(params)
    enclosure = _primary_shape(enclosure)
    enclosure += _cutout_collars(params)
    enclosure = _primary_shape(enclosure)

    enclosure -= _front_baffle_cutout(params)
    enclosure = _primary_shape(enclosure)
    pre_relief_volume = enclosure.volume
    enclosure -= _front_inner_relief_cutout(params)
    enclosure = _primary_shape(enclosure)
    front_inner_relief_cm3 = (pre_relief_volume - enclosure.volume) / 1000

    for tool in (
        _driver_rear_mount_bores(params),
        _pr_cutouts(params),
        _gx16_cutout(params),
        _fill_port_cutouts(params),
    ):
        enclosure -= tool
        enclosure = _primary_shape(enclosure)

    bb = enclosure.bounding_box()
    gross_cavity_l = params.cavity_side * params.cavity_y * params.cavity_side
    gross_cavity_l /= 1_000_000
    estimated_net_l = (
        gross_cavity_l - params.driver_displacement_l - params.pr_intrusion_l
    )
    estimated_net_l_with_front_relief = estimated_net_l + front_inner_relief_cm3 / 1000
    pr_radius = params.pr_recess_dia / 2
    gx16_center_r = math.hypot(params.gx16_x, params.gx16_z)
    fill_center_r = math.hypot(params.fill_port_x, params.fill_port_z)
    diagnostics = {
        "name": "compact_6in_one_piece_enclosure",
        "orientation": {
            "front_driver_face": "-Y",
            "rear_pr_face_prints_down": "+Y face in CAD",
            "gx16_face": "+Y rear lower-left corner",
            "fill_ports_face": "+Y rear upper corners into top sand void",
        },
        "wall_stack_mm": {
            "outer_skin": params.outer_skin_t,
            "sand_void": params.void_t,
            "inner_skin": params.inner_skin_t,
            "total": params.sandwich_t,
            "front_cap": params.front_cap_t,
            "rear_cap": params.rear_cap_t,
        },
        "cube_outer_mm": params.cube_outer,
        "enclosure_depth_y_mm": params.enclosure_depth_y,
        "cube_outer_in": params.cube_outer / 25.4,
        "enclosure_depth_y_in": params.enclosure_depth_y / 25.4,
        "edge_fillet_r_mm": params.edge_fillet_r,
        "internal_fillet_r_mm": params.internal_fillet_r,
        "cavity_side_mm": params.cavity_side,
        "cavity_y_mm": params.cavity_y,
        "gross_cavity_l": round(gross_cavity_l, 3),
        "estimated_net_l_after_driver_pr": round(estimated_net_l, 3),
        "estimated_net_l_with_front_relief": round(
            estimated_net_l_with_front_relief,
            3,
        ),
        "driver": {
            "model": "Dayton Audio ND105-8",
            "mounting": "rear-mounted from acoustic cavity side",
            "visible_black_hole_baffle": True,
            "cavity_side_relief": True,
            "cavity_side_relief_added_l": round(front_inner_relief_cm3 / 1000, 3),
            "cavity_side_relief_removed_cm3": round(front_inner_relief_cm3, 3),
            "baffle_wall_t_mm": params.driver_baffle_wall_t,
            "seat_land_od_mm": params.driver_seat_land_od,
            "baffle_outer_dia_mm": params.driver_cutout_dia
            + 2 * params.driver_baffle_blend_r,
            "baffle_depth_mm": params.driver_baffle_blend_depth,
            "cutout_dia_mm": params.driver_cutout_dia,
            "overall_dia_mm": params.driver_overall_dia,
            "bolt_circle_dia_mm": params.driver_bolt_circle_dia,
            "bolt_circle_status": "first-pass assumption; verify against drawing or part",
        },
        "passive_radiator": {
            "model": "Dayton Audio DSA135-PR",
            "cutout_dia_mm": params.pr_cutout_dia,
            "overall_dia_mm": params.pr_overall_dia,
            "bolt_circle_dia_mm": params.pr_bolt_circle_dia,
            "bolt_circle_status": "first-pass assumption; verify against drawing or part",
            "edge_clearance_per_side_mm": round(
                (params.cube_outer - params.pr_overall_dia) / 2,
                3,
            ),
        },
        "gx16": {
            "hole_d_mm": params.gx16_hole_d,
            "face": "+Y rear",
            "center_xz_mm": [params.gx16_x, params.gx16_z],
            "gap_to_pr_recess_edge_mm": round(
                gx16_center_r - pr_radius - params.gx16_flange_recess_d / 2,
                3,
            ),
        },
        "fill_ports": {
            "threaded": False,
            "hole_d_mm": params.fill_port_d,
            "positions_xz_mm": [
                [-params.fill_port_x, params.fill_port_z],
                [params.fill_port_x, params.fill_port_z],
            ],
            "gap_to_pr_recess_edge_mm": round(
                fill_center_r - pr_radius - params.fill_entry_d / 2,
                3,
            ),
        },
        "checks": {
            "outer_dim_x_ok": math.isclose(bb.size.X, params.cube_outer, abs_tol=0.01),
            "outer_dim_y_ok": math.isclose(
                bb.size.Y,
                params.enclosure_depth_y,
                abs_tol=0.01,
            ),
            "outer_dim_z_ok": math.isclose(bb.size.Z, params.cube_outer, abs_tol=0.01),
            "valid": enclosure.is_valid,
            "single_solid": len(enclosure.solids()) == 1,
            "positive_estimated_net_l": estimated_net_l_with_front_relief > 0,
            "pr_fits_face": params.pr_overall_dia < params.cube_outer,
            "gx16_clears_pr_recess": gx16_center_r
            > pr_radius + params.gx16_flange_recess_d / 2,
            "fill_ports_clear_pr_recess": fill_center_r
            > pr_radius + params.fill_entry_d / 2,
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
        "origin_to_rear_face_mm": rear_face_y,
    }
    return enclosure, diagnostics


def export_enclosure(path, params: CompactParams = p) -> dict[str, object]:
    part, diagnostics = build(params)
    export_step(part, path, unit=Unit.MM)
    return diagnostics


def assembly_preview(enclosure: Part, horn: Part) -> Compound:
    return Compound(children=[enclosure, horn])
