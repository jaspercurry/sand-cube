"""Generate 1 in curve-to-seat variants with contoured inner front walls."""

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
    import_step,
    make_face,
    revolve,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from generate_curve_to_seat_variants import (  # noqa: E402
    CUBE_OUTER,
    EDGE_FILLET_R,
    _bezier_point,
    _front_tool_global,
)
from generate_variants import (  # noqa: E402
    _bolt_circle_bores,
    _gx16_connector_island,
    _grid3_for_span,
    _hex_prism_y,
    _oriented_cylinder,
    _primary_shape,
    _sand_fill_port_cutout,
    _skin_bridge_posts,
    _top_reinforcement_island,
)
from params import p as base_p  # noqa: E402


OUT = ROOT / "build" / "sand_cube_8_5_black_hole" / "contoured_inner"
RECESS_DEPTH = 1.0 * 25.4
DRIVER_SEAT_EXTRA_DEPTH = 1.0
DRIVER_SEAT_DEPTH = RECESS_DEPTH + DRIVER_SEAT_EXTRA_DEPTH
FRONT_FACE_EDGE_CLEARANCE = 1.5
BAFFLE_OUTER_D = CUBE_OUTER - 2 * (EDGE_FILLET_R + FRONT_FACE_EDGE_CLEARANCE)
SEAT_LAND_OD = 158.0
DRIVER_FACE_OPENING_DIA = 130.5
DRIVER_MOUNT_FACE_RAW_Y = 110.5
DRIVER_INSERT_STEP = ROOT / "objects" / "M4x6mm_threaded_brass_insert.step"
DRIVER_INSERT_LENGTH = 6.0
DRIVER_INSERT_BORE_DEPTH = 6.5
PR_INSERT_BORE_DEPTH = 6.5
FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR = 0.30
WOOFER_ASSEMBLY_CLEARANCE = 0.0
FILL_PORT_Z = CUBE_OUTER / 2 - base_p.outer_skin_t - base_p.void_t / 2
GX16_X = -75.0
GX16_Z = -75.0
GX16_HEX_ROTATION = 15.0
GX16_STEP_ROTATION = GX16_HEX_ROTATION + 30.0
DRIVER_SEAT_EDGE_FILLET_R = 0.4
INTERNAL_SEAM_FILLET_R = 1.5
SAND_VOID_EDGE_FILLET_R = 1.0
BRIDGE_POST_ROOT_FILLET_R = 1.5
HARDWARE_CLEARANCE = 0.05


@dataclass(frozen=True)
class Variant:
    name: str
    wall_t: float


def _front_curve_controls(
    *,
    r_outer: float,
    r_inner: float,
    depth: float,
) -> tuple[tuple[float, float], ...]:
    radial_span = r_outer - r_inner
    return (
        (r_outer, 0.0),
        (r_outer - radial_span * base_p.baffle_tangent_in, 0.0),
        (r_inner, depth * FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR),
        (r_inner, depth),
    )


def _lerp(
    start: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t,
    )


def _split_cubic_left(
    controls: tuple[tuple[float, float], ...],
    t: float,
) -> tuple[tuple[float, float], ...]:
    """Return Bezier controls for the original curve trimmed to [0, t]."""
    p01 = _lerp(controls[0], controls[1], t)
    p12 = _lerp(controls[1], controls[2], t)
    p23 = _lerp(controls[2], controls[3], t)
    p012 = _lerp(p01, p12, t)
    p123 = _lerp(p12, p23, t)
    p0123 = _lerp(p012, p123, t)
    return (controls[0], p01, p012, p0123)


def _curve_t_at_radius(
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
    return (low + high) / 2


def _inner_curve_controls(
    *,
    r_outer: float,
    r_inner: float,
    r_seat: float,
    depth: float,
    wall_t: float,
) -> tuple[tuple[float, float], ...]:
    front_controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
    )
    seat_t = _curve_t_at_radius(
        radius=r_seat,
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
    )
    trimmed = _split_cubic_left(front_controls, seat_t)
    return tuple((radius, z + wall_t) for radius, z in trimmed)


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


def _curve_to_micro_seat_tool(params) -> Part:
    r_outer = BAFFLE_OUTER_D / 2
    r_inner = params.driver_cutout_dia / 2
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
                    (r_inner, DRIVER_SEAT_DEPTH),
                    (0.0, DRIVER_SEAT_DEPTH),
                    (0.0, -2.0),
                    (r_outer, -2.0),
                    (r_outer, 0.0),
                )
            make_face()
        assert sketch.sketch.area > 0, "Curve-to-micro-seat sketch must be positive"
        revolve(axis=Axis.Z)
    return tool.part


def _inner_relief_tool(params, variant: Variant) -> Part:
    """Remove front-cap material outside the driver seat land.

    The cut leaves a flat rear annulus for the driver and heat-set inserts from
    the driver opening out to SEAT_LAND_OD, then steps onto an inner surface
    that follows the outside black-hole contour with approximately wall_t of
    plastic thickness.
    """
    r_seat = SEAT_LAND_OD / 2
    r_outer = BAFFLE_OUTER_D / 2
    outside_r = math.sqrt(2) * params.cube_outer / 2 + 8.0
    seat_depth = DRIVER_SEAT_DEPTH

    inner_controls = _inner_curve_controls(
        r_outer=r_outer,
        r_inner=params.driver_cutout_dia / 2,
        r_seat=r_seat,
        depth=RECESS_DEPTH,
        wall_t=variant.wall_t,
    )

    with BuildPart() as relief:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Polyline(
                    (r_seat, seat_depth),
                    (outside_r, seat_depth),
                    (outside_r, variant.wall_t),
                    (r_outer, variant.wall_t),
                )
                Bezier(*inner_controls)
                Polyline(
                    inner_controls[-1],
                    (r_seat, seat_depth),
                )
            make_face()
        assert sketch.sketch.area > 0, "Inner relief sketch must be positive"
        revolve(axis=Axis.Z)
    return relief.part


def _hex_half_extent(rotation: float) -> float:
    apothem = base_p.gx16_nut_across_flats / 2
    circumradius = apothem / math.cos(math.pi / 6)
    return max(
        abs(circumradius * math.cos(math.radians(rotation) + math.tau * i / 6))
        for i in range(6)
    )


def _gx16_rear_cutout_corner(params) -> Part:
    half = params.cube_outer / 2
    panel_inner_y = half - params.gx16_flange_recess_depth - params.gx16_panel_land_t
    inner_face_y = half - params.rear_cap_t
    hex_depth = panel_inner_y - inner_face_y + 0.2
    hex_center_y = inner_face_y + hex_depth / 2 - 0.1
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
                rotation=GX16_HEX_ROTATION,
            )
        )
    return cutout.part


def _top_front_bracket_cutouts(params) -> Part:
    """Front M5 bracket holes only; banana posts serve as rear clamp points."""
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    spacing = params.bracket_hole_spacing / 2
    y = params.bracket_hole_y - spacing
    with BuildPart() as cutouts:
        for x in (-spacing, spacing):
            add(
                _oriented_cylinder(
                    diameter=params.bracket_hole_d,
                    depth=top_stack_t + 2.0,
                    axis="z",
                    center=(x, y, half - top_stack_t / 2),
                )
            )
    return cutouts.part


def _top_binding_post_holes(params) -> Part:
    """Banana post through-holes only, with no cosmetic washer recesses."""
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    with BuildPart() as cutouts:
        for x in (-params.binding_post_spacing / 2, params.binding_post_spacing / 2):
            add(
                _oriented_cylinder(
                    diameter=params.binding_post_hole_d,
                    depth=top_stack_t + 2.0,
                    axis="z",
                    center=(x, params.binding_post_y, half - top_stack_t / 2),
                )
            )
    return cutouts.part


def _driver_seat_lip_edges(part: Part, params) -> list:
    target_y = -params.cube_outer / 2 + DRIVER_SEAT_DEPTH
    target_dia = params.driver_cutout_dia
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        center_y = (bb.min.Y + bb.max.Y) / 2
        if (
            abs(center_y - target_y) < 0.2
            and abs(bb.size.X - target_dia) < 0.5
            and abs(bb.size.Z - target_dia) < 0.5
            and bb.size.Y < 0.2
        ):
            edges.append(edge)
    return edges


def _filleted_box(
    x_size: float,
    y_size: float,
    z_size: float,
    *,
    radius: float,
) -> Part:
    box = Box(x_size, y_size, z_size)
    if radius <= 0:
        return box
    return _primary_shape(fillet(box.edges(), radius=radius))


def _bridge_post_root_edges(part: Part, params) -> list:
    half = params.cube_outer / 2
    void_outer = half - params.outer_skin_t
    void_inner = half - params.outer_skin_t - params.void_t
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = (bb.size.X, bb.size.Y, bb.size.Z)
        centers = (
            (bb.min.X + bb.max.X) / 2,
            (bb.min.Y + bb.max.Y) / 2,
            (bb.min.Z + bb.max.Z) / 2,
        )
        if not (10.0 < edge.length < 40.0):
            continue
        x_post_root = (
            abs(sizes[1] - params.bracing_post_d) < 1.0
            and abs(sizes[2] - params.bracing_post_d) < 1.0
            and sizes[0] < 0.5
            and (
                abs(abs(centers[0]) - void_outer) < 0.5
                or abs(abs(centers[0]) - void_inner) < 0.5
            )
        )
        z_post_root = (
            abs(sizes[0] - params.bracing_post_d) < 1.0
            and abs(sizes[1] - params.bracing_post_d) < 1.0
            and sizes[2] < 0.5
            and (
                abs(abs(centers[2]) - void_outer) < 0.5
                or abs(abs(centers[2]) - void_inner) < 0.5
            )
        )
        if x_post_root or z_post_root:
            edges.append(edge)
    return edges


def _internal_seam_edges(part: Part, params) -> list:
    """Select straight internal skin/cavity seams and avoid functional holes."""
    half = params.cube_outer / 2
    cavity_side = params.cube_outer - 2 * (
        params.outer_skin_t + params.void_t + params.inner_skin_t
    )
    cavity_half = cavity_side / 2
    rear_inner_y = half - params.rear_cap_t
    void_outer = half - params.outer_skin_t
    void_inner = half - params.outer_skin_t - params.void_t
    seam_planes = (
        cavity_half,
        -cavity_half,
        void_outer,
        -void_outer,
        void_inner,
        -void_inner,
    )
    seam_y_planes = (rear_inner_y,)
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = (bb.size.X, bb.size.Y, bb.size.Z)
        centers = (
            (bb.min.X + bb.max.X) / 2,
            (bb.min.Y + bb.max.Y) / 2,
            (bb.min.Z + bb.max.Z) / 2,
        )
        straightish = sum(size < 0.05 for size in sizes) >= 2
        if not straightish or edge.length < 30.0:
            continue
        near_x = any(abs(centers[0] - plane) < 0.35 for plane in seam_planes)
        near_z = any(abs(centers[2] - plane) < 0.35 for plane in seam_planes)
        near_y = any(abs(centers[1] - plane) < 0.35 for plane in seam_y_planes)
        if (near_x and near_z) or (near_y and (near_x or near_z)):
            edges.append(edge)
    return edges


def _front_inner_wall_seam_edges(part: Part, params, variant: Variant) -> list:
    """Select the front contoured wall seams against the inner side walls."""
    half = params.cube_outer / 2
    cavity_side = params.cube_outer - 2 * (
        params.outer_skin_t + params.void_t + params.inner_skin_t
    )
    cavity_half = cavity_side / 2
    front_wall_y = -half + variant.wall_t
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = (bb.size.X, bb.size.Y, bb.size.Z)
        centers = (
            (bb.min.X + bb.max.X) / 2,
            (bb.min.Y + bb.max.Y) / 2,
            (bb.min.Z + bb.max.Z) / 2,
        )
        if edge.length < 20.0 or edge.length > 120.0:
            continue
        if bb.min.Y < front_wall_y - 0.5 or bb.max.Y > front_wall_y + 3.5:
            continue
        near_x_wall = abs(abs(centers[0]) - cavity_half) < 0.35 and sizes[0] < 0.05
        near_z_wall = abs(abs(centers[2]) - cavity_half) < 0.35 and sizes[2] < 0.05
        if near_x_wall or near_z_wall:
            edges.append(edge)
    return edges


def _confirmed_woofer(params):
    half = params.cube_outer / 2
    front_mount_y = -half + params.front_cap_t
    return (
        Location(
            (
                0,
                (front_mount_y + WOOFER_ASSEMBLY_CLEARANCE)
                - (-DRIVER_MOUNT_FACE_RAW_Y),
                0,
            )
        )
        * (
            Rot(0, 45, 0)
            * Rot(180, 0, 0)
            * import_step(ROOT / "objects" / "E150HE-44.step")
        )
    )


def _bolt_circle_positions(
    *,
    radius: float,
    count: int,
) -> list[tuple[float, float]]:
    positions = []
    for index in range(count):
        angle = math.tau * index / count + (math.tau / 8 if count == 4 else 0)
        positions.append(
            (
                radius * math.cos(angle),
                radius * math.sin(angle),
            )
        )
    return positions


def _confirmed_driver_inserts(params) -> Compound:
    half = params.cube_outer / 2
    front_mount_y = -half + params.front_cap_t
    insert = import_step(DRIVER_INSERT_STEP)
    inserts = []
    for x, z in _bolt_circle_positions(
        radius=params.driver_bolt_circle_r,
        count=params.driver_screw_count,
    ):
        inserts.extend(
            (
                Location((x, front_mount_y, z))
                * (Rot(90, 0, 0) * insert)
            ).solids()
        )
    return Compound(inserts)


def _confirmed_pr_inserts(params) -> Compound:
    half = params.cube_outer / 2
    pr_mount_y = half - params.pr_recess_depth
    insert = import_step(DRIVER_INSERT_STEP)
    inserts = []
    for x, z in _bolt_circle_positions(
        radius=params.pr_bolt_circle_r,
        count=params.pr_screw_count,
    ):
        inserts.extend(
            (
                Location((x, pr_mount_y, z))
                * (Rot(90, 0, 0) * insert)
            ).solids()
        )
    return Compound(inserts)


def _confirmed_passive_radiator(params):
    half = params.cube_outer / 2
    raw_outer_flange_y = 115.7
    return (
        Location((0, (half + HARDWARE_CLEARANCE) - raw_outer_flange_y, 0))
        * (Rot(0, -30, 0) * import_step(ROOT / "objects" / "E180HE-PR.step"))
    )


def _gx16_nut_index(gx16):
    candidates = []
    for index, solid in enumerate(gx16.solids()):
        bb = solid.bounding_box()
        if bb.size.X > 20.0 and 2.0 < bb.size.Y < 5.0 and 18.0 < bb.size.Z < 20.0:
            candidates.append(index)
    if len(candidates) != 1:
        raise ValueError(f"Expected one GX16 nut solid, found {len(candidates)}")
    return candidates[0]


def _placed_gx16(params):
    half = params.cube_outer / 2
    flange_ring_y = -2.0
    panel_inner_y = half - params.gx16_flange_recess_depth - params.gx16_panel_land_t
    inner_face_y = half - params.rear_cap_t
    hex_depth = panel_inner_y - inner_face_y + 0.2
    hex_center_y = inner_face_y + hex_depth / 2 - 0.1
    raw = import_step(ROOT / "objects" / "GX16.stp")
    nut_index = _gx16_nut_index(raw)
    nut = raw.solids()[nut_index]
    body_solids = [
        solid for index, solid in enumerate(raw.solids()) if index != nut_index
    ]
    nut_bb = nut.bounding_box()
    raw_nut_center_y = (nut_bb.min.Y + nut_bb.max.Y) / 2
    nut_y = hex_center_y - raw_nut_center_y
    body_y = (half - params.gx16_flange_recess_depth) - flange_ring_y
    placed_body = (
        Location((params.gx16_x, body_y, params.gx16_z))
        * (Rot(0, GX16_STEP_ROTATION, 0) * Compound(body_solids))
    )
    placed_nut = (
        Location((params.gx16_x, nut_y, params.gx16_z))
        * (Rot(0, GX16_STEP_ROTATION, 0) * nut)
    )
    placed = Compound(children=[*placed_body.solids(), placed_nut])
    placed_bb = placed.bounding_box()
    return placed, {
        "hex_pocket_center_y_mm": round(hex_center_y, 3),
        "raw_nut_center_y_mm": round(raw_nut_center_y, 3),
        "body_flange_ring_raw_y_mm": flange_ring_y,
        "body_y_offset_mm": round(body_y, 3),
        "nut_y_offset_mm": round(nut_y, 3),
        "pocket_rotation_deg": GX16_HEX_ROTATION,
        "step_rotation_deg": GX16_STEP_ROTATION,
        "rear_face_y_mm": round(half, 3),
        "placed_bbox_min_mm": [
            round(placed_bb.min.X, 3),
            round(placed_bb.min.Y, 3),
            round(placed_bb.min.Z, 3),
        ],
        "placed_bbox_max_mm": [
            round(placed_bb.max.X, 3),
            round(placed_bb.max.Y, 3),
            round(placed_bb.max.Z, 3),
        ],
        "outside_rear_projection_mm": round(placed_bb.max.Y - half, 3),
        "inside_projection_from_inner_face_mm": round(
            inner_face_y - placed_bb.min.Y,
            3,
        ),
    }


def _hardware_assembly(enclosure: Part, params) -> tuple[Compound, dict[str, object]]:
    woofer = _confirmed_woofer(params)
    driver_inserts = _confirmed_driver_inserts(params)
    pr_inserts = _confirmed_pr_inserts(params)
    passive_radiator = _confirmed_passive_radiator(params)
    gx16, gx16_data = _placed_gx16(params)
    assembly = Compound(
        children=[
            enclosure,
            *woofer.solids(),
            *driver_inserts.solids(),
            *pr_inserts.solids(),
            *passive_radiator.solids(),
            *gx16.solids(),
        ]
    )
    return assembly, {
        "gx16": gx16_data,
        "solid_counts": {
            "enclosure": len(enclosure.solids()),
            "woofer": len(woofer.solids()),
            "driver_inserts": len(driver_inserts.solids()),
            "pr_inserts": len(pr_inserts.solids()),
            "passive_radiator": len(passive_radiator.solids()),
            "gx16": len(gx16.solids()),
            "assembly": len(assembly.solids()),
        },
    }


def build_variant(variant: Variant) -> tuple[Part, dict[str, object]]:
    params = replace(
        base_p,
        cube_outer=CUBE_OUTER,
        edge_fillet_r=EDGE_FILLET_R,
        front_cap_t=DRIVER_SEAT_DEPTH,
        driver_cutout_dia=DRIVER_FACE_OPENING_DIA,
        driver_insert_bore_depth=DRIVER_INSERT_BORE_DEPTH,
        pr_insert_bore_depth=PR_INSERT_BORE_DEPTH,
        fill_port_z=FILL_PORT_Z,
        gx16_x=GX16_X,
        gx16_z=GX16_Z,
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

    acoustic_cavity = Box(
        cavity_side,
        cavity_y,
        cavity_side,
    )
    acoustic_cavity = Pos(0, cavity_center_y, 0) * acoustic_cavity
    enclosure = outer_solid - acoustic_cavity

    for x in (-1, 1):
        enclosure -= Pos(
            x * (half - params.outer_skin_t - params.void_t / 2),
            cavity_center_y,
            0,
        ) * _filleted_box(
            params.void_t,
            cavity_y,
            shell_span,
            radius=SAND_VOID_EDGE_FILLET_R,
        )
    for z in (-1, 1):
        enclosure -= Pos(
            0,
            cavity_center_y,
            z * (half - params.outer_skin_t - params.void_t / 2),
        ) * _filleted_box(
            shell_span,
            cavity_y,
            params.void_t,
            radius=SAND_VOID_EDGE_FILLET_R,
        )
    enclosure = _primary_shape(enclosure)

    enclosure += _skin_bridge_posts(params, cavity_y_span=cavity_y)
    enclosure = _primary_shape(enclosure)
    bridge_post_root_edges = _bridge_post_root_edges(enclosure, params)
    if len(bridge_post_root_edges) < 60:
        raise ValueError(
            f"Expected at least 60 bridge-post root edges, found {len(bridge_post_root_edges)}"
        )
    enclosure = fillet(bridge_post_root_edges, radius=BRIDGE_POST_ROOT_FILLET_R)
    enclosure = _primary_shape(enclosure)
    enclosure += _gx16_connector_island(params)
    enclosure = _primary_shape(enclosure)
    enclosure += _top_reinforcement_island(params)
    enclosure = _primary_shape(enclosure)

    enclosure -= _front_tool_global(_curve_to_micro_seat_tool(params), params)
    enclosure = _primary_shape(enclosure)

    relief = _front_tool_global(_inner_relief_tool(params, variant), params)
    relief_clip = Pos(0, -half + DRIVER_SEAT_DEPTH / 2, 0) * Box(
        cavity_side,
        DRIVER_SEAT_DEPTH + 0.5,
        cavity_side,
    )
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
    enclosure -= _gx16_rear_cutout_corner(params)
    enclosure = _primary_shape(enclosure)
    for fill_x in (-params.fill_port_x, params.fill_port_x):
        enclosure -= _sand_fill_port_cutout(params, x=fill_x, z=params.fill_port_z)
        enclosure = _primary_shape(enclosure)
    enclosure -= _top_binding_post_holes(params)
    enclosure = _primary_shape(enclosure)
    enclosure -= _top_front_bracket_cutouts(params)
    enclosure = _primary_shape(enclosure)

    seat_lip_edges = _driver_seat_lip_edges(enclosure, params)
    if len(seat_lip_edges) != 1:
        raise ValueError(f"Expected one driver-seat lip edge, found {len(seat_lip_edges)}")
    enclosure = fillet(seat_lip_edges, radius=DRIVER_SEAT_EDGE_FILLET_R)
    enclosure = _primary_shape(enclosure)

    internal_seam_edges = _internal_seam_edges(enclosure, params)
    if len(internal_seam_edges) < 4:
        raise ValueError(
            f"Expected at least 4 internal seam edges, found {len(internal_seam_edges)}"
        )
    enclosure = fillet(internal_seam_edges, radius=INTERNAL_SEAM_FILLET_R)
    enclosure = _primary_shape(enclosure)

    front_inner_wall_seam_edges = _front_inner_wall_seam_edges(
        enclosure,
        params,
        variant,
    )
    if len(front_inner_wall_seam_edges) < 8:
        raise ValueError(
            "Expected at least 8 front inner wall seam edges, "
            f"found {len(front_inner_wall_seam_edges)}"
        )
    enclosure = fillet(front_inner_wall_seam_edges, radius=INTERNAL_SEAM_FILLET_R)
    enclosure = _primary_shape(enclosure)

    insert_bore_r = params.insert_bore_d / 2
    insert_clearance_radii = {
        "outer_bore_edge": params.driver_bolt_circle_r + insert_bore_r,
        "centerline": params.driver_bolt_circle_r,
        "inner_bore_edge": params.driver_bolt_circle_r - insert_bore_r,
        "inner_bore_edge_minus_0_4_tolerance": params.driver_bolt_circle_r
        - insert_bore_r
        - 0.4,
    }
    bore_tip_depth = DRIVER_SEAT_DEPTH - params.driver_insert_bore_depth
    insert_tip_depth = DRIVER_SEAT_DEPTH - DRIVER_INSERT_LENGTH
    insert_clearance_points = {}
    for name, radius in insert_clearance_radii.items():
        front_depth = _front_depth_at_radius(
            radius=radius,
            r_outer=BAFFLE_OUTER_D / 2,
            r_inner=params.driver_cutout_dia / 2,
            depth=RECESS_DEPTH,
        )
        insert_clearance_points[name] = {
            "radius_mm": round(radius, 3),
            "front_surface_depth_mm": round(front_depth, 3),
            "bore_tip_cover_mm": round(bore_tip_depth - front_depth, 3),
            "insert_tip_cover_mm": round(insert_tip_depth - front_depth, 3),
        }
    insert_front_clearance = insert_clearance_points["inner_bore_edge"][
        "bore_tip_cover_mm"
    ]

    bb = enclosure.bounding_box()
    nominal_cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000
    hex_half_extent = _hex_half_extent(GX16_HEX_ROTATION)
    inner_cavity_half = cavity_side / 2
    pr_mount_y = half - params.pr_recess_depth
    pr_bore_tip_y = pr_mount_y - params.pr_insert_bore_depth
    pr_insert_tip_y = pr_mount_y - DRIVER_INSERT_LENGTH
    pr_inner_face_y = half - params.rear_cap_t
    diagnostics = {
        "name": variant.name,
        "cube_outer_mm": params.cube_outer,
        "cube_outer_in": params.cube_outer / 25.4,
        "edge_fillet_r_mm": params.edge_fillet_r,
        "front_recess_depth_mm": RECESS_DEPTH,
        "front_recess_depth_in": RECESS_DEPTH / 25.4,
        "driver_seat_extra_depth_mm": DRIVER_SEAT_EXTRA_DEPTH,
        "driver_seat_depth_mm": DRIVER_SEAT_DEPTH,
        "front_curve_driver_control_depth_factor": FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR,
        "target_wall_t_mm": variant.wall_t,
        "baffle_outer_d_mm": BAFFLE_OUTER_D,
        "front_face_edge_clearance_mm": FRONT_FACE_EDGE_CLEARANCE,
        "driver_cutout_dia_mm": params.driver_cutout_dia,
        "seat_land_od_mm": SEAT_LAND_OD,
        "front_seat_y_mm": front_inner_y,
        "nominal_cavity_l": round(nominal_cavity_l, 3),
        "fill_ports": {
            "x_mm": params.fill_port_x,
            "z_mm": round(params.fill_port_z, 3),
            "top_void_z_range_mm": [
                round(half - params.outer_skin_t - params.void_t, 3),
                round(half - params.outer_skin_t, 3),
            ],
        },
        "gx16": {
            "x_mm": params.gx16_x,
            "z_mm": params.gx16_z,
            "hex_rotation_deg": GX16_HEX_ROTATION,
            "step_rotation_deg": GX16_STEP_ROTATION,
            "center_distance_from_pr_mm": round(
                math.hypot(params.gx16_x, params.gx16_z),
                3,
            ),
            "gap_to_pr_recess_edge_mm": round(
                math.hypot(params.gx16_x, params.gx16_z)
                - params.pr_recess_dia / 2
                - params.gx16_flange_recess_d / 2,
                3,
            ),
            "island_clearance_to_nearest_cube_side_mm": round(
                min(
                    half - abs(params.gx16_x) - params.gx16_island_xy / 2,
                    half - abs(params.gx16_z) - params.gx16_island_xy / 2,
                ),
                3,
            ),
            "hex_clearance_to_inner_side_bottom_mm": round(
                inner_cavity_half - abs(params.gx16_x) - hex_half_extent,
                3,
            ),
            "island_clearance_to_inner_side_bottom_mm": round(
                inner_cavity_half - abs(params.gx16_x) - params.gx16_island_xy / 2,
                3,
            ),
        },
        "driver_insert": {
            "bolt_circle_r_mm": params.driver_bolt_circle_r,
            "bore_dia_mm": params.insert_bore_d,
            "bore_depth_mm": params.driver_insert_bore_depth,
            "insert_step": str(DRIVER_INSERT_STEP.relative_to(ROOT)),
            "insert_model_length_mm": DRIVER_INSERT_LENGTH,
            "melt_relief_depth_mm": round(
                params.driver_insert_bore_depth - DRIVER_INSERT_LENGTH,
                3,
            ),
            "bore_tip_depth_from_front_mm": round(bore_tip_depth, 3),
            "insert_tip_depth_from_front_mm": round(insert_tip_depth, 3),
            "clearance_points": insert_clearance_points,
            "worst_nominal_bore_tip_cover_mm": insert_front_clearance,
            "pierce_risk": insert_front_clearance < 1.5,
        },
        "pr_insert": {
            "bolt_circle_r_mm": params.pr_bolt_circle_r,
            "count": params.pr_screw_count,
            "bore_dia_mm": params.insert_bore_d,
            "bore_depth_mm": params.pr_insert_bore_depth,
            "insert_step": str(DRIVER_INSERT_STEP.relative_to(ROOT)),
            "insert_model_length_mm": DRIVER_INSERT_LENGTH,
            "melt_relief_depth_mm": round(
                params.pr_insert_bore_depth - DRIVER_INSERT_LENGTH,
                3,
            ),
            "mount_y_mm": round(pr_mount_y, 3),
            "bore_tip_y_mm": round(pr_bore_tip_y, 3),
            "insert_tip_y_mm": round(pr_insert_tip_y, 3),
            "rear_inner_face_y_mm": round(pr_inner_face_y, 3),
            "bore_tip_cover_to_cavity_mm": round(pr_bore_tip_y - pr_inner_face_y, 3),
            "insert_tip_cover_to_cavity_mm": round(
                pr_insert_tip_y - pr_inner_face_y,
                3,
            ),
            "service_cutout_radial_clearance_mm": round(
                params.pr_bolt_circle_r
                - params.insert_bore_d / 2
                - params.pr_service_cutout_dia / 2,
                3,
            ),
            "pierce_risk": (pr_bore_tip_y - pr_inner_face_y) < 1.5,
        },
        "driver_step_fit": {
            "source": "objects/E150HE-44.step",
            "flat_mount_face_raw_y_mm": DRIVER_MOUNT_FACE_RAW_Y,
            "assembly_clearance_mm": WOOFER_ASSEMBLY_CLEARANCE,
            "matched_flange_inner_dia_mm": DRIVER_FACE_OPENING_DIA,
            "step_outer_frame_dia_mm": 152.5,
        },
        "bridge_post_grid": {
            "xz_positions_mm": [round(v, 3) for v in _grid3_for_span(cavity_side)],
            "y_positions_mm": [round(v, 3) for v in _grid3_for_span(cavity_y)],
        },
        "top_plate": {
            "binding_posts_act_as_rear_clamp_points": True,
            "top_recesses_removed": True,
            "front_bracket_holes": [
                [-params.bracket_hole_spacing / 2, params.bracket_hole_y - params.bracket_hole_spacing / 2],
                [params.bracket_hole_spacing / 2, params.bracket_hole_y - params.bracket_hole_spacing / 2],
            ],
            "rear_bracket_holes_removed": True,
        },
        "driver_seat_lip_fillet_r_mm": DRIVER_SEAT_EDGE_FILLET_R,
        "sand_void_edge_fillet": {
            "radius_mm": SAND_VOID_EDGE_FILLET_R,
            "method": "filleted_sand_void_cutout_tools",
        },
        "bridge_post_root_fillet": {
            "radius_mm": BRIDGE_POST_ROOT_FILLET_R,
            "edge_count": len(bridge_post_root_edges),
        },
        "internal_seam_fillet": {
            "radius_mm": INTERNAL_SEAM_FILLET_R,
            "edge_count": len(internal_seam_edges),
        },
        "front_inner_wall_seam_fillet": {
            "radius_mm": INTERNAL_SEAM_FILLET_R,
            "edge_count": len(front_inner_wall_seam_edges),
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
        Variant("final_wall_10", 10.0),
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
        export_step(part, OUT / "sand_cube_8_5_black_hole_final.step", unit=Unit.MM)
        export_step(part, OUT / "sand_cube_8_5_black_hole_enclosure.step", unit=Unit.MM)
        params = replace(
            base_p,
            cube_outer=CUBE_OUTER,
            edge_fillet_r=EDGE_FILLET_R,
            front_cap_t=DRIVER_SEAT_DEPTH,
            driver_cutout_dia=DRIVER_FACE_OPENING_DIA,
            driver_insert_bore_depth=DRIVER_INSERT_BORE_DEPTH,
            pr_insert_bore_depth=PR_INSERT_BORE_DEPTH,
            fill_port_z=FILL_PORT_Z,
            gx16_x=GX16_X,
            gx16_z=GX16_Z,
        )
        assembly, hardware_data = _hardware_assembly(part, params)
        export_step(
            assembly,
            OUT / "sand_cube_8_5_black_hole_hardware_assembly.step",
            unit=Unit.MM,
        )
        data["hardware_assembly"] = hardware_data
        diagnostics.append(data)
        comparison_parts.append(Location((offset0 + index * spacing, 0, 0)) * part)

    export_step(
        Compound(comparison_parts),
        OUT / "contoured_inner_comparison.step",
        unit=Unit.MM,
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
