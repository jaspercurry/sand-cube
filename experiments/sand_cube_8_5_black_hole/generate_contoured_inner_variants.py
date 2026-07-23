"""Generate 1 in curve-to-seat variants with contoured inner front walls."""

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
    Circle,
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
    extrude,
    export_step,
    fillet,
    import_step,
    loft,
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


OUT = ROOT / "build" / "sand_cube_200_wall_7_black_hole"
RECESS_DEPTH = 1.0 * 25.4
DRIVER_SEAT_EXTRA_DEPTH = 1.0
FRONT_FACE_EDGE_CLEARANCE = 1.5
BAFFLE_OUTER_D = CUBE_OUTER - 2 * (EDGE_FILLET_R + FRONT_FACE_EDGE_CLEARANCE)
FINAL_190_CUBE_OUTER = 190.0
FINAL_190_OUTER_SKIN_T = 2.0
FINAL_190_VOID_T = 3.0
FINAL_190_INNER_SKIN_T = 2.0
FINAL_190_EDGE_FILLET_R = 2.0
FINAL_200_CUBE_OUTER = 200.0
FINAL_200_EDGE_FILLET_R = 7.0
FINAL_200_FILL_ENTRY_D = 9.15
SEAT_LAND_OD = 158.0
DRIVER_FACE_OPENING_DIA = 130.5
DRIVER_MOUNT_FACE_RAW_Y = 110.5
DRIVER_INSERT_STEP = ROOT / "objects" / "M4x6mm_threaded_brass_insert.step"
BINDING_POST_STEP = ROOT / "objects" / "Dayton Audio Binding Posts.stp"
BINDING_POST_MOUNT_SEAT_RAW_Z = 12.08
BINDING_POST_THREAD_MAJOR_D = 8.5
BINDING_POST_MEASURED_THROUGH_D = 7.08
DRIVER_INSERT_LENGTH = 6.0
HEAT_SET_INSERT_BORE_DIA = 4.8
DRIVER_INSERT_BORE_DEPTH = 6.5
PR_INSERT_BORE_DEPTH = 6.5
FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR = 0.30
WOOFER_ASSEMBLY_CLEARANCE = 0.0
FILL_PORT_Z = CUBE_OUTER / 2 - base_p.outer_skin_t - base_p.void_t / 2
FINAL_190_FILL_PORT_Z = (
    FINAL_190_CUBE_OUTER / 2 - FINAL_190_OUTER_SKIN_T - FINAL_190_VOID_T / 2
)
FINAL_200_FILL_PORT_Z = (
    FINAL_200_CUBE_OUTER / 2
    - FINAL_190_OUTER_SKIN_T
    - FINAL_200_FILL_ENTRY_D / 2
)
GX16_X = -75.0
GX16_Z = -75.0
GX16_HEX_ROTATION = 15.0
GX16_STEP_ROTATION = GX16_HEX_ROTATION + 30.0
GX16_NUT_DISPLAY_T = 3.2
BINDING_POST_GROMMET_CLEARANCE_D = 8.7
DRIVER_SEAT_EDGE_FILLET_R = 0.4
INTERNAL_SEAM_FILLET_R = 1.5
SAND_VOID_EDGE_FILLET_R = 1.0
BRIDGE_POST_ROOT_FILLET_R = 1.5
HARDWARE_CLEARANCE = 0.05
FILL_PORT_SUPPORT_SKIN_EMBED = 0.5
LONGITUDINAL_BRACE_END_BLEND_L = 10.0
LONGITUDINAL_BRACE_BLEND_RAIL_EMBED = 0.5


@dataclass(frozen=True)
class Variant:
    name: str
    wall_t: float
    recess_depth: float = RECESS_DEPTH
    driver_seat_extra_depth: float = DRIVER_SEAT_EXTRA_DEPTH
    cube_outer: float = CUBE_OUTER
    edge_fillet_r: float = EDGE_FILLET_R
    outer_skin_t: float = base_p.outer_skin_t
    void_t: float = base_p.void_t
    inner_skin_t: float = base_p.inner_skin_t
    front_face_edge_clearance: float = FRONT_FACE_EDGE_CLEARANCE
    baffle_outer_d: float | None = None
    front_baffle_seam_rotation_deg: float = 0.0
    direct_curve_to_driver_seat: bool = False
    driver_mount_divots: bool = False
    driver_mount_divot_d: float = 2.0
    driver_mount_divot_depth: float = 1.0
    fill_port_threaded: bool = True
    fill_port_transition_length: float = 0.0
    fill_port_transition_support_wall: float = 0.0
    fill_port_x: float = base_p.fill_port_x
    fill_port_z: float = FILL_PORT_Z
    gx16_x: float = GX16_X
    gx16_z: float = GX16_Z
    fill_thread_major_d: float = base_p.fill_thread_major_d
    fill_thread_pitch: float = base_p.fill_thread_pitch
    fill_thread_core_d: float = base_p.fill_thread_core_d
    fill_thread_length: float = base_p.fill_thread_length
    fill_entry_d: float = base_p.fill_entry_d
    fill_entry_depth: float = base_p.fill_entry_depth
    top_island_w: float = base_p.top_island_w
    top_island_y: float = base_p.top_island_y
    top_island_d: float = base_p.top_island_d
    top_island_corner_r: float = 0.0
    top_island_hole_margin: float | None = None
    binding_post_spacing: float = base_p.binding_post_spacing
    binding_post_y: float = base_p.binding_post_y
    binding_post_hole_d: float = BINDING_POST_GROMMET_CLEARANCE_D
    binding_post_diamond_pilot: bool = False
    binding_post_diamond_pilot_diagonal: float = 0.0
    binding_post_forward_shift: float = 0.0
    front_bracket_holes: bool = True
    bracket_hole_spacing: float = base_p.bracket_hole_spacing
    bracket_hole_y: float = base_p.bracket_hole_y
    bracket_hole_d: float = base_p.bracket_hole_d
    solid_bottom: bool = False
    skin_bridge_posts: bool = True
    window_brace: bool = False
    window_brace_center_y: float = 0.0
    window_brace_width: float = 10.0
    window_brace_height: float = 10.0
    window_brace_corner_r: float = 5.0
    window_brace_skin_embed: float = 1.0
    vertical_center_brace: bool = False
    vertical_brace_rear_y: float | None = None
    vertical_brace_width: float = 10.0
    vertical_brace_height: float = 10.0
    vertical_brace_skin_embed: float = 1.0
    horizontal_waist_brace: bool = False
    horizontal_brace_rear_y: float | None = None
    horizontal_brace_width: float = 10.0
    horizontal_brace_height: float = 10.0
    horizontal_brace_skin_embed: float = 1.0
    bottom_tripod_indent_positions: tuple[tuple[float, float], ...] = ()
    bottom_tripod_indent_d: float = 5.0
    bottom_tripod_indent_depth: float = 1.0


LEGACY_FINAL_VARIANT = Variant("final_wall_10", 10.0)
FINAL_190_VARIANT = Variant(
    "final_190_wall_7",
    7.0,
    cube_outer=FINAL_190_CUBE_OUTER,
    edge_fillet_r=FINAL_190_EDGE_FILLET_R,
    outer_skin_t=FINAL_190_OUTER_SKIN_T,
    void_t=FINAL_190_VOID_T,
    inner_skin_t=FINAL_190_INNER_SKIN_T,
    fill_port_z=FINAL_190_FILL_PORT_Z,
    gx16_x=-74.0,
    gx16_z=-74.0,
    fill_thread_major_d=4.6,
    fill_thread_pitch=0.8,
    fill_thread_core_d=3.4,
    fill_thread_length=8.0,
    fill_entry_d=4.8,
    fill_entry_depth=0.8,
    top_island_y=47.5,
    top_island_d=95.0,
)
FINAL_200_VARIANT = Variant(
    "final_200_wall_7",
    7.0,
    recess_depth=RECESS_DEPTH * 2 / 3,
    driver_seat_extra_depth=2.25,
    cube_outer=FINAL_200_CUBE_OUTER,
    edge_fillet_r=FINAL_200_EDGE_FILLET_R,
    outer_skin_t=FINAL_190_OUTER_SKIN_T,
    void_t=FINAL_190_VOID_T,
    inner_skin_t=FINAL_190_INNER_SKIN_T,
    front_baffle_seam_rotation_deg=90.0,
    direct_curve_to_driver_seat=True,
    driver_mount_divots=True,
    driver_mount_divot_d=2.0,
    driver_mount_divot_depth=1.0,
    fill_port_threaded=False,
    fill_port_transition_length=10.0,
    fill_port_transition_support_wall=1.2,
    fill_port_x=88.0,
    fill_port_z=FINAL_200_FILL_PORT_Z,
    gx16_x=-74.0,
    gx16_z=-74.0,
    fill_thread_major_d=4.6,
    fill_thread_pitch=0.8,
    fill_thread_core_d=3.4,
    fill_thread_length=8.0,
    fill_entry_d=FINAL_200_FILL_ENTRY_D,
    fill_entry_depth=0.8,
    top_island_w=68.0,
    top_island_y=30.0,
    top_island_d=28.0,
    top_island_corner_r=5.0,
    top_island_hole_margin=10.35,
    binding_post_spacing=40.0,
    binding_post_y=30.0,
    binding_post_hole_d=7.3,
    binding_post_diamond_pilot=True,
    binding_post_diamond_pilot_diagonal=6.8,
    binding_post_forward_shift=20.0,
    front_bracket_holes=False,
    bracket_hole_spacing=43.0,
    bracket_hole_y=25.5,
    bracket_hole_d=6.0,
    solid_bottom=True,
    skin_bridge_posts=False,
    window_brace=True,
    window_brace_center_y=0.0,
    window_brace_width=10.0,
    window_brace_height=10.0,
    window_brace_corner_r=5.0,
    window_brace_skin_embed=1.0,
    vertical_center_brace=True,
    vertical_brace_width=10.0,
    vertical_brace_height=10.0,
    vertical_brace_skin_embed=1.0,
    horizontal_waist_brace=True,
    horizontal_brace_width=10.0,
    horizontal_brace_height=10.0,
    horizontal_brace_skin_embed=1.0,
    bottom_tripod_indent_positions=(
        (-60.0, -70.0),
        (60.0, -70.0),
        (0.0, 70.0),
    ),
    bottom_tripod_indent_d=2.0,
    bottom_tripod_indent_depth=1.0,
)
FINAL_VARIANT = FINAL_200_VARIANT


def _wall_stack_t(params) -> float:
    return params.outer_skin_t + params.void_t + params.inner_skin_t


def _baffle_outer_d(params, variant: Variant) -> float:
    if variant.baffle_outer_d is not None:
        return variant.baffle_outer_d
    return params.cube_outer - 2 * (
        params.edge_fillet_r + variant.front_face_edge_clearance
    )


def _recess_depth(variant: Variant) -> float:
    return variant.recess_depth


def _driver_seat_depth(variant: Variant) -> float:
    return variant.recess_depth + variant.driver_seat_extra_depth


def _front_curve_endpoint_depth(variant: Variant) -> float:
    if variant.direct_curve_to_driver_seat:
        return _driver_seat_depth(variant)
    return _recess_depth(variant)


def _front_tool_global_oriented(tool: Part, params, variant: Variant) -> Part:
    oriented = Rot(0, 0, variant.front_baffle_seam_rotation_deg) * tool
    return _front_tool_global(oriented, params)


def _plain_wall_stack_cavity_l(params) -> float:
    cavity_side = params.cube_outer - 2 * _wall_stack_t(params)
    return cavity_side**3 / 1_000_000


def _bridge_post_root_fillet_r(params) -> float:
    return min(BRIDGE_POST_ROOT_FILLET_R, params.void_t * 0.25)


def _front_curve_controls(
    *,
    r_outer: float,
    r_inner: float,
    depth: float,
    endpoint_depth: float | None = None,
) -> tuple[tuple[float, float], ...]:
    radial_span = r_outer - r_inner
    curve_endpoint_depth = depth if endpoint_depth is None else endpoint_depth
    return (
        (r_outer, 0.0),
        (r_outer - radial_span * base_p.baffle_tangent_in, 0.0),
        (r_inner, depth * FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR),
        (r_inner, curve_endpoint_depth),
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
    endpoint_depth: float | None = None,
) -> float:
    controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
        endpoint_depth=endpoint_depth,
    )
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
    endpoint_depth: float | None = None,
) -> tuple[tuple[float, float], ...]:
    front_controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
        endpoint_depth=endpoint_depth,
    )
    seat_t = _curve_t_at_radius(
        radius=r_seat,
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
        endpoint_depth=endpoint_depth,
    )
    trimmed = _split_cubic_left(front_controls, seat_t)
    return tuple((radius, z + wall_t) for radius, z in trimmed)


def _front_depth_at_radius(
    *,
    radius: float,
    r_outer: float,
    r_inner: float,
    depth: float,
    endpoint_depth: float | None = None,
) -> float:
    controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=depth,
        endpoint_depth=endpoint_depth,
    )
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


def _curve_to_micro_seat_tool(params, variant: Variant) -> Part:
    r_outer = _baffle_outer_d(params, variant) / 2
    r_inner = params.driver_cutout_dia / 2
    recess_depth = _recess_depth(variant)
    seat_depth = _driver_seat_depth(variant)
    controls = _front_curve_controls(
        r_outer=r_outer,
        r_inner=r_inner,
        depth=recess_depth,
        endpoint_depth=_front_curve_endpoint_depth(variant),
    )
    seat_profile = [
        (r_inner, seat_depth),
        (0.0, seat_depth),
        (0.0, -2.0),
        (r_outer, -2.0),
        (r_outer, 0.0),
    ]
    if not variant.direct_curve_to_driver_seat:
        seat_profile.insert(0, (r_inner, recess_depth))
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Bezier(*controls)
                Polyline(*seat_profile)
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
    r_outer = _baffle_outer_d(params, variant) / 2
    outside_r = math.sqrt(2) * params.cube_outer / 2 + 8.0
    recess_depth = _recess_depth(variant)
    seat_depth = _driver_seat_depth(variant)

    inner_controls = _inner_curve_controls(
        r_outer=r_outer,
        r_inner=params.driver_cutout_dia / 2,
        r_seat=r_seat,
        depth=recess_depth,
        wall_t=variant.wall_t,
        endpoint_depth=_front_curve_endpoint_depth(variant),
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


def _top_binding_post_holes(params, variant: Variant) -> Part:
    """Banana-post through tools, optionally as self-supporting drill pilots."""
    half = params.cube_outer / 2
    top_stack_t = params.outer_skin_t + params.void_t + params.inner_skin_t
    with BuildPart() as cutouts:
        for x in (-params.binding_post_spacing / 2, params.binding_post_spacing / 2):
            center = (x, params.binding_post_y, half - top_stack_t / 2)
            if variant.binding_post_diamond_pilot:
                side = variant.binding_post_diamond_pilot_diagonal / math.sqrt(2)
                add(
                    Location(center)
                    * (
                        Rot(0, 0, 45)
                        * Box(
                            side,
                            side,
                            top_stack_t + 2.0,
                            mode=Mode.PRIVATE,
                        )
                    )
                )
            else:
                add(
                    _oriented_cylinder(
                        diameter=params.binding_post_hole_d,
                        depth=top_stack_t + 2.0,
                        axis="z",
                        center=center,
                    )
                )
    return cutouts.part


def _fill_port_void_transition(
    params,
    variant: Variant,
    *,
    x: float,
    z: float,
    bore_r: float | None = None,
    void_r: float | None = None,
) -> Part:
    length = variant.fill_port_transition_length
    bore_radius = params.fill_entry_d / 2 if bore_r is None else bore_r
    void_radius = params.void_t / 2 if void_r is None else void_r
    rear_inner_y = params.cube_outer / 2 - params.rear_cap_t
    void_center_z = (
        params.cube_outer / 2 - params.outer_skin_t - params.void_t / 2
    )
    section_count = 7
    with BuildPart() as transition:
        for section_index in range(section_count):
            t = section_index / (section_count - 1)
            blend = t * t * (3.0 - 2.0 * t)
            section_y = rear_inner_y - length * t
            section_z = z + (void_center_z - z) * blend
            section_r = bore_radius + (void_radius - bore_radius) * blend
            section_plane = Plane(
                origin=(x, section_y, section_z),
                x_dir=(1, 0, 0),
                z_dir=(0, -1, 0),
            )
            with BuildSketch(section_plane) as section:
                Circle(section_r)
            assert section.sketch.area > 0, (
                "Fill-port transition section must have positive area"
            )
        loft()

    return transition.part.clean().fix()


def _fill_port_inner_support(
    params,
    variant: Variant,
    *,
    x: float,
    z: float,
) -> Part:
    support_wall = variant.fill_port_transition_support_wall
    outer_transition = _fill_port_void_transition(
        params,
        variant,
        x=x,
        z=z,
        bore_r=params.fill_entry_d / 2 + support_wall,
        void_r=params.void_t / 2 + support_wall,
    )
    half = params.cube_outer / 2
    cavity_top_z = half - _wall_stack_t(params)
    clip_top_z = cavity_top_z + 0.5
    clip_bottom_z = -half - 1.0
    clip_height = clip_top_z - clip_bottom_z
    clip = Pos(0, 0, (clip_top_z + clip_bottom_z) / 2) * Box(
        params.cube_outer + 2.0,
        params.cube_outer + 2.0,
        clip_height,
    )
    cavity_side_x = half - _wall_stack_t(params)
    skin_embed = FILL_PORT_SUPPORT_SKIN_EMBED
    if x >= 0:
        clip_min_x = -half - 1.0
        clip_max_x = cavity_side_x + skin_embed
    else:
        clip_min_x = -cavity_side_x - skin_embed
        clip_max_x = half + 1.0
    side_clip = Pos((clip_min_x + clip_max_x) / 2, 0, 0) * Box(
        clip_max_x - clip_min_x,
        params.cube_outer + 2.0,
        params.cube_outer + 2.0,
    )
    return _primary_shape(outer_transition & clip & side_clip)


def _variant_sand_fill_port_cutout(
    params,
    variant: Variant,
    *,
    x: float,
    z: float,
) -> Part:
    if variant.fill_port_threaded:
        return _sand_fill_port_cutout(params, x=x, z=z)

    port_depth = params.rear_cap_t + 0.8
    bore = _oriented_cylinder(
        diameter=params.fill_entry_d,
        depth=port_depth,
        axis="y",
        center=(x, params.cube_outer / 2 - port_depth / 2, z),
    )
    if variant.fill_port_transition_length <= 0:
        return bore
    return bore + _fill_port_void_transition(
        params,
        variant,
        x=x,
        z=z,
    )


def _bottom_tripod_indent_cutouts(params, variant: Variant) -> Part:
    half = params.cube_outer / 2
    cut_depth = variant.bottom_tripod_indent_depth + 0.2
    cut_center_z = -half + variant.bottom_tripod_indent_depth / 2 - 0.1
    with BuildPart() as cutouts:
        for x, y in variant.bottom_tripod_indent_positions:
            add(
                _oriented_cylinder(
                    diameter=variant.bottom_tripod_indent_d,
                    depth=cut_depth,
                    axis="z",
                    center=(x, y, cut_center_z),
                )
            )
    return cutouts.part


def _driver_mount_cutouts(params, variant: Variant, front_inner_y: float) -> Part:
    if not variant.driver_mount_divots:
        return _bolt_circle_bores(
            params,
            radius=params.driver_bolt_circle_r,
            count=params.driver_screw_count,
            bore_depth=params.driver_insert_bore_depth,
            bore_open_y=front_inner_y,
            bore_direction_y=-1,
        )

    cut_depth = variant.driver_mount_divot_depth + 0.2
    cut_center_y = front_inner_y - variant.driver_mount_divot_depth / 2 + 0.1
    with BuildPart() as cutouts:
        for x, z in _bolt_circle_positions(
            radius=params.driver_bolt_circle_r,
            count=params.driver_screw_count,
        ):
            add(
                _oriented_cylinder(
                    diameter=variant.driver_mount_divot_d,
                    depth=cut_depth,
                    axis="y",
                    center=(x, cut_center_y, z),
                )
            )
    return cutouts.part


def _front_baffle_seam_edges(part: Part, params, variant: Variant) -> list:
    r_outer = _baffle_outer_d(params, variant) / 2
    r_inner = params.driver_cutout_dia / 2
    seam_angle = math.radians(variant.front_baffle_seam_rotation_deg)
    expected_direction = (math.cos(seam_angle), -math.sin(seam_angle))
    edges = []
    for edge in part.edges():
        vertices = edge.vertices()
        if len(vertices) != 2:
            continue
        endpoints = sorted(
            vertices,
            key=lambda vertex: math.hypot(vertex.X, vertex.Z),
        )
        inner, outer = endpoints
        inner_r = math.hypot(inner.X, inner.Z)
        outer_r = math.hypot(outer.X, outer.Z)
        if abs(inner_r - r_inner) > 0.1 or abs(outer_r - r_outer) > 0.1:
            continue
        outer_direction = (outer.X / outer_r, outer.Z / outer_r)
        direction_dot = sum(
            actual * expected
            for actual, expected in zip(outer_direction, expected_direction)
        )
        if direction_dot > 0.999 and abs(outer.Y + params.cube_outer / 2) < 0.1:
            edges.append(edge)
    return edges


def _driver_seat_lip_edges(part: Part, params) -> list:
    target_y = -params.cube_outer / 2 + params.front_cap_t
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


def _box_edges_parallel_to_axis(
    part: Part,
    *,
    axis: str,
    length: float,
) -> list:
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = {"x": bb.size.X, "y": bb.size.Y, "z": bb.size.Z}
        cross_axes = tuple(name for name in ("x", "y", "z") if name != axis)
        if (
            abs(sizes[axis] - length) < 0.01
            and all(sizes[name] < 0.01 for name in cross_axes)
        ):
            edges.append(edge)
    if len(edges) != 4:
        raise ValueError(
            f"Expected four box edges parallel to {axis}, found {len(edges)}"
        )
    return edges


def _variant_top_reinforcement_island(params, variant: Variant) -> Part:
    if variant.top_island_corner_r <= 0:
        return _top_reinforcement_island(params)

    half = params.cube_outer / 2
    top_stack_t = _wall_stack_t(params)
    island = Box(params.top_island_w, params.top_island_d, top_stack_t)
    island = fillet(
        _box_edges_parallel_to_axis(island, axis="z", length=top_stack_t),
        radius=variant.top_island_corner_r,
    )
    return Pos(
        params.top_island_x,
        params.top_island_y,
        half - top_stack_t / 2,
    ) * _primary_shape(island)


def _window_brace(params, variant: Variant) -> Part:
    cavity_side = params.cube_outer - 2 * _wall_stack_t(params)
    outer_side = cavity_side + 2 * variant.window_brace_skin_embed
    inner_side = cavity_side - 2 * variant.window_brace_height
    if inner_side <= 2 * variant.window_brace_corner_r:
        raise ValueError("Window-brace opening is too small for its corner radius")

    outer = Box(outer_side, variant.window_brace_width, outer_side)
    inner = Box(inner_side, variant.window_brace_width + 2.0, inner_side)
    if variant.window_brace_corner_r > 0:
        inner = fillet(
            _box_edges_parallel_to_axis(
                inner,
                axis="y",
                length=variant.window_brace_width + 2.0,
            ),
            radius=variant.window_brace_corner_r,
        )
        inner = _primary_shape(inner)
    brace = _primary_shape(outer - inner)
    return Pos(0, variant.window_brace_center_y, 0) * brace


def _top_longitudinal_brace_end_blend(
    params,
    *,
    tangential_width: float,
    radial_height: float,
    rear_y: float,
) -> Part:
    half = params.cube_outer / 2
    cavity_half = half - _wall_stack_t(params)
    rail_inner_r = cavity_half - radial_height
    front_face_y = -half + params.front_cap_t
    rear_face_y = half - params.rear_cap_t
    ends = [
        (front_face_y, front_face_y + LONGITUDINAL_BRACE_END_BLEND_L, SEAT_LAND_OD / 2),
    ]
    if abs(rear_y - rear_face_y) < 0.001:
        ends.append(
            (
                rear_face_y,
                rear_face_y - LONGITUDINAL_BRACE_END_BLEND_L,
                params.pr_service_cutout_dia / 2,
            )
        )

    blend_parts = []
    for face_y, tail_y, ring_r in ends:
        radial_gap = rail_inner_r - ring_r
        if radial_gap <= 0:
            raise ValueError("Brace end blend must terminate inside the rail edge")
        direction = 1.0 if tail_y > face_y else -1.0
        blend_length = abs(tail_y - face_y)
        closure_back_y = -half if face_y < 0 else face_y
        closure_points = [
            (tail_y, rail_inner_r),
            (
                tail_y,
                rail_inner_r + LONGITUDINAL_BRACE_BLEND_RAIL_EMBED,
            ),
            (
                closure_back_y,
                rail_inner_r + LONGITUDINAL_BRACE_BLEND_RAIL_EMBED,
            ),
            (closure_back_y, ring_r),
        ]
        if closure_back_y != face_y:
            closure_points.append((face_y, ring_r))
        with BuildPart() as blend:
            with BuildSketch(Plane.YZ) as sketch:
                with BuildLine():
                    Bezier(
                        (face_y, ring_r),
                        (face_y, ring_r + radial_gap * 0.55),
                        (
                            tail_y - direction * blend_length * 0.55,
                            rail_inner_r,
                        ),
                        (tail_y, rail_inner_r),
                    )
                    Polyline(*closure_points)
                make_face()
            assert sketch.sketch.area > 0, (
                "Longitudinal brace end-blend sketch must have positive area"
            )
            extrude(amount=tangential_width / 2, both=True)
        blend_parts.append(blend.part)

    result = blend_parts[0]
    for blend_part in blend_parts[1:]:
        result += blend_part
    return result


def _vertical_center_brace(params, variant: Variant) -> Part:
    half = params.cube_outer / 2
    cavity_half = half - _wall_stack_t(params)
    front_y = -half
    rear_inner_y = half - params.rear_cap_t
    rear_y = (
        rear_inner_y
        if variant.vertical_brace_rear_y is None
        else variant.vertical_brace_rear_y
    )
    y_span = rear_y - front_y
    if y_span <= 0:
        raise ValueError("Vertical center brace must extend behind the front wall")

    y_center = (front_y + rear_y) / 2
    rib_z_size = variant.vertical_brace_height + variant.vertical_brace_skin_embed
    rib_z_center = (
        cavity_half
        - variant.vertical_brace_height / 2
        + variant.vertical_brace_skin_embed / 2
    )
    top_rib = Pos(0, y_center, rib_z_center) * Box(
        variant.vertical_brace_width,
        y_span,
        rib_z_size,
    )
    bottom_rib = Pos(0, y_center, -rib_z_center) * Box(
        variant.vertical_brace_width,
        y_span,
        rib_z_size,
    )
    top_blends = _top_longitudinal_brace_end_blend(
        params,
        tangential_width=variant.vertical_brace_width,
        radial_height=variant.vertical_brace_height,
        rear_y=rear_y,
    )
    bottom_blends = Rot(0, 180, 0) * top_blends
    return top_rib + bottom_rib + top_blends + bottom_blends


def _horizontal_waist_brace(params, variant: Variant) -> Part:
    half = params.cube_outer / 2
    cavity_half = half - _wall_stack_t(params)
    front_y = -half
    rear_inner_y = half - params.rear_cap_t
    rear_y = (
        rear_inner_y
        if variant.horizontal_brace_rear_y is None
        else variant.horizontal_brace_rear_y
    )
    y_span = rear_y - front_y
    if y_span <= 0:
        raise ValueError("Horizontal waist brace must extend behind the front wall")

    y_center = (front_y + rear_y) / 2
    rib_x_size = variant.horizontal_brace_height + variant.horizontal_brace_skin_embed
    rib_x_center = (
        cavity_half
        - variant.horizontal_brace_height / 2
        + variant.horizontal_brace_skin_embed / 2
    )
    left_rib = Pos(-rib_x_center, y_center, 0) * Box(
        rib_x_size,
        y_span,
        variant.horizontal_brace_width,
    )
    right_rib = Pos(rib_x_center, y_center, 0) * Box(
        rib_x_size,
        y_span,
        variant.horizontal_brace_width,
    )
    top_blends = _top_longitudinal_brace_end_blend(
        params,
        tangential_width=variant.horizontal_brace_width,
        radial_height=variant.horizontal_brace_height,
        rear_y=rear_y,
    )
    right_blends = Rot(0, 90, 0) * top_blends
    left_blends = Rot(0, -90, 0) * top_blends
    return left_rib + right_rib + left_blends + right_blends


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


def _confirmed_binding_posts(params) -> list[Compound]:
    raw = import_step(BINDING_POST_STEP)
    top_z = params.cube_outer / 2
    z_offset = top_z - BINDING_POST_MOUNT_SEAT_RAW_Z
    return [
        Location((x, params.binding_post_y, z_offset)) * raw
        for x in (-params.binding_post_spacing / 2, params.binding_post_spacing / 2)
    ]


def _gx16_nut_index(gx16):
    candidates = []
    for index, solid in enumerate(gx16.solids()):
        bb = solid.bounding_box()
        if bb.size.X > 20.0 and 2.0 < bb.size.Y < 5.0 and 18.0 < bb.size.Z < 20.0:
            candidates.append(index)
    if len(candidates) != 1:
        raise ValueError(f"Expected one GX16 nut solid, found {len(candidates)}")
    return candidates[0]


def _is_valid_shape(shape) -> bool:
    is_valid = getattr(shape, "is_valid")
    return is_valid() if callable(is_valid) else bool(is_valid)


def _require_single_solid(shape, *, feature: str) -> Part:
    solids = list(shape.solids())
    if len(solids) != 1:
        raise ValueError(f"{feature} produced {len(solids)} solids; expected one")
    solid = solids[0]
    if not _is_valid_shape(solid):
        raise ValueError(f"{feature} produced an invalid solid")
    return solid


def _intersection_volume(left, right) -> float:
    volume = 0.0
    for left_solid in left.solids():
        for right_solid in right.solids():
            overlap = left_solid & right_solid
            if overlap is not None:
                volume += sum(solid.volume for solid in overlap.solids())
    return volume


def _placed_gx16(params):
    half = params.cube_outer / 2
    flange_ring_y = -2.0
    panel_inner_y = half - params.gx16_flange_recess_depth - params.gx16_panel_land_t
    inner_face_y = half - params.rear_cap_t
    hex_depth = panel_inner_y - inner_face_y + 0.2
    hex_center_y = inner_face_y + hex_depth / 2 - 0.1
    raw = import_step(ROOT / "objects" / "GX16.stp")
    nut_index = _gx16_nut_index(raw)
    body_solids = [
        solid for index, solid in enumerate(raw.solids()) if index != nut_index
    ]
    body_solids = [solid for solid in body_solids if _is_valid_shape(solid)]
    if not body_solids:
        raise ValueError("GX16 body import did not contain any valid solids")
    nut = raw.solids()[nut_index]
    nut_bb = nut.bounding_box()
    raw_nut_center_y = (nut_bb.min.Y + nut_bb.max.Y) / 2
    body_y = (half - params.gx16_flange_recess_depth) - flange_ring_y
    placed_body = (
        Location((params.gx16_x, body_y, params.gx16_z))
        * (Rot(0, GX16_STEP_ROTATION, 0) * Compound(body_solids))
    )
    placed_nut = _hex_prism_y(
        across_flats=params.gx16_nut_across_flats,
        depth=GX16_NUT_DISPLAY_T,
        center=(params.gx16_x, hex_center_y, params.gx16_z),
        rotation=GX16_HEX_ROTATION,
    )
    placed_nut -= _oriented_cylinder(
        diameter=params.gx16_hole_d,
        depth=GX16_NUT_DISPLAY_T + 0.4,
        axis="y",
        center=(params.gx16_x, hex_center_y, params.gx16_z),
    )
    placed = Compound(children=[*placed_body.solids(), placed_nut])
    placed_bb = placed.bounding_box()
    return placed, {
        "hex_pocket_center_y_mm": round(hex_center_y, 3),
        "raw_nut_center_y_mm": round(raw_nut_center_y, 3),
        "body_flange_ring_raw_y_mm": flange_ring_y,
        "body_y_offset_mm": round(body_y, 3),
        "nut_display_thickness_mm": GX16_NUT_DISPLAY_T,
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


def _hardware_assembly(
    enclosure: Part,
    params,
    variant: Variant = FINAL_VARIANT,
) -> tuple[Compound, dict[str, object]]:
    woofer = _confirmed_woofer(params)
    driver_insert_solids = (
        []
        if variant.driver_mount_divots
        else list(_confirmed_driver_inserts(params).solids())
    )
    pr_inserts = _confirmed_pr_inserts(params)
    passive_radiator = _confirmed_passive_radiator(params)
    binding_posts = _confirmed_binding_posts(params)
    gx16, gx16_data = _placed_gx16(params)
    assembly = Compound(
        children=[
            enclosure,
            *woofer.solids(),
            *driver_insert_solids,
            *pr_inserts.solids(),
            *passive_radiator.solids(),
            *[
                solid
                for binding_post in binding_posts
                for solid in binding_post.solids()
            ],
            *gx16.solids(),
        ]
    )
    return assembly, {
        "gx16": gx16_data,
        "solid_counts": {
            "enclosure": len(enclosure.solids()),
            "woofer": len(woofer.solids()),
            "driver_inserts": len(driver_insert_solids),
            "pr_inserts": len(pr_inserts.solids()),
            "passive_radiator": len(passive_radiator.solids()),
            "binding_posts": sum(len(post.solids()) for post in binding_posts),
            "gx16": len(gx16.solids()),
            "assembly": len(assembly.solids()),
        },
    }


def _final_params(variant: Variant = FINAL_VARIANT):
    return replace(
        base_p,
        cube_outer=variant.cube_outer,
        outer_skin_t=variant.outer_skin_t,
        void_t=variant.void_t,
        inner_skin_t=variant.inner_skin_t,
        edge_fillet_r=variant.edge_fillet_r,
        front_cap_t=_driver_seat_depth(variant),
        driver_cutout_dia=DRIVER_FACE_OPENING_DIA,
        insert_bore_d=HEAT_SET_INSERT_BORE_DIA,
        driver_insert_bore_depth=DRIVER_INSERT_BORE_DEPTH,
        pr_insert_bore_depth=PR_INSERT_BORE_DEPTH,
        fill_port_x=variant.fill_port_x,
        fill_port_z=variant.fill_port_z,
        fill_thread_major_d=variant.fill_thread_major_d,
        fill_thread_pitch=variant.fill_thread_pitch,
        fill_thread_core_d=variant.fill_thread_core_d,
        fill_thread_length=variant.fill_thread_length,
        fill_entry_d=variant.fill_entry_d,
        fill_entry_depth=variant.fill_entry_depth,
        binding_post_spacing=variant.binding_post_spacing,
        binding_post_y=variant.binding_post_y,
        binding_post_hole_d=variant.binding_post_hole_d,
        bracket_hole_spacing=variant.bracket_hole_spacing,
        bracket_hole_y=variant.bracket_hole_y,
        bracket_hole_d=variant.bracket_hole_d,
        gx16_x=variant.gx16_x,
        gx16_z=variant.gx16_z,
        top_island_w=variant.top_island_w,
        top_island_y=variant.top_island_y,
        top_island_d=variant.top_island_d,
    )


def _volume_summary(variant: Variant) -> dict[str, float]:
    params = _final_params(variant)
    half = params.cube_outer / 2
    cavity_side = params.cube_outer - 2 * _wall_stack_t(params)
    front_inner_y = -half + params.front_cap_t
    rear_inner_y = half - params.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    relief = _front_tool_global_oriented(
        _inner_relief_tool(params, variant),
        params,
        variant,
    )
    relief_clip = Pos(0, -half + params.front_cap_t / 2, 0) * Box(
        cavity_side,
        params.front_cap_t + 0.5,
        cavity_side,
    )
    front_relief_l = _primary_shape(relief & relief_clip).volume / 1_000_000
    nominal_cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000
    return {
        "cube_outer_mm": params.cube_outer,
        "wall_stack_t_mm": _wall_stack_t(params),
        "cavity_side_mm": cavity_side,
        "front_cap_t_mm": params.front_cap_t,
        "rear_cap_t_mm": params.rear_cap_t,
        "cavity_y_mm": cavity_y,
        "plain_wall_stack_cavity_l": _plain_wall_stack_cavity_l(params),
        "nominal_cavity_l": nominal_cavity_l,
        "modeled_front_inner_relief_l": front_relief_l,
        "acoustic_cavity_plus_front_relief_l": nominal_cavity_l + front_relief_l,
    }


def _volume_comparison(variant: Variant) -> dict[str, object]:
    legacy = _volume_summary(LEGACY_FINAL_VARIANT)
    current = _volume_summary(variant)
    delta_l = current["nominal_cavity_l"] - legacy["nominal_cavity_l"]
    return {
        "legacy_variant": LEGACY_FINAL_VARIANT.name,
        "current_variant": variant.name,
        "legacy_nominal_cavity_l": round(legacy["nominal_cavity_l"], 3),
        "current_nominal_cavity_l": round(current["nominal_cavity_l"], 3),
        "delta_l": round(delta_l, 3),
        "delta_percent": round(delta_l / legacy["nominal_cavity_l"] * 100, 1),
        "legacy": {key: round(value, 3) for key, value in legacy.items()},
        "current": {key: round(value, 3) for key, value in current.items()},
    }


def _export_prefix(variant: Variant) -> str:
    if variant.name == "final_200_wall_7":
        return "sand_cube_200_wall_7_black_hole"
    if variant.name == "final_190_wall_7":
        return "sand_cube_190_wall_7_black_hole"
    if variant.name == "final_wall_10":
        return "sand_cube_8_5_black_hole"
    return f"sand_cube_{variant.name}_black_hole"


def _final_export_set(
    enclosure: Part,
    params,
    variant: Variant = FINAL_VARIANT,
) -> tuple[dict[str, Compound | Part], dict[str, object]]:
    enclosure_solid = _primary_shape(enclosure).solids()[0]
    enclosure_body = lambda: copy.copy(enclosure_solid)
    driver_insert_solids = (
        []
        if variant.driver_mount_divots
        else list(_confirmed_driver_inserts(params).solids())
    )
    pr_inserts = _confirmed_pr_inserts(params)
    inserts = [*driver_insert_solids, *pr_inserts.solids()]
    passive_radiator = _confirmed_passive_radiator(params)
    binding_posts = _confirmed_binding_posts(params)
    binding_post_solids = [
        solid for binding_post in binding_posts for solid in binding_post.solids()
    ]
    gx16, gx16_data = _placed_gx16(params)
    woofer = _confirmed_woofer(params)

    enclosure_with_inserts = Compound(children=[enclosure_body(), *inserts])
    enclosure_with_pr_gx16 = Compound(
        children=[
            enclosure_body(),
            *inserts,
            *passive_radiator.solids(),
            *gx16.solids(),
        ]
    )
    complete_assembly = Compound(
        children=[
            enclosure_body(),
            *inserts,
            *passive_radiator.solids(),
            *gx16.solids(),
            *woofer.solids(),
            *binding_post_solids,
        ]
    )
    prefix = _export_prefix(variant)
    woofer_bb = woofer.bounding_box()
    passive_bb = passive_radiator.bounding_box()
    binding_post_enclosure_overlaps = [
        _intersection_volume(binding_post, enclosure)
        for binding_post in binding_posts
    ]
    binding_post_other_hardware_overlaps = [
        _intersection_volume(binding_post, woofer)
        + _intersection_volume(binding_post, passive_radiator)
        + _intersection_volume(binding_post, gx16)
        for binding_post in binding_posts
    ]
    binding_post_to_post_overlap = _intersection_volume(
        binding_posts[0],
        binding_posts[1],
    )
    woofer_enclosure_overlap = _intersection_volume(woofer, enclosure)
    passive_enclosure_overlap = _intersection_volume(passive_radiator, enclosure)
    woofer_passive_overlap = _intersection_volume(woofer, passive_radiator)
    brace_clearance_details = []
    if variant.window_brace:
        brace_clearance_details.append(
            (
                "transverse_window_frame",
                _window_brace(params, variant),
                [
                    variant.window_brace_center_y - variant.window_brace_width / 2,
                    variant.window_brace_center_y + variant.window_brace_width / 2,
                ],
            )
        )
    if variant.vertical_center_brace:
        vertical_rear_y = (
            params.cube_outer / 2 - params.rear_cap_t
            if variant.vertical_brace_rear_y is None
            else variant.vertical_brace_rear_y
        )
        brace_clearance_details.append(
            (
                "vertical_center_plane_rails",
                _vertical_center_brace(params, variant),
                [
                    -params.cube_outer / 2,
                    vertical_rear_y,
                ],
            )
        )
    if variant.horizontal_waist_brace:
        horizontal_rear_y = (
            params.cube_outer / 2 - params.rear_cap_t
            if variant.horizontal_brace_rear_y is None
            else variant.horizontal_brace_rear_y
        )
        brace_clearance_details.append(
            (
                "horizontal_waist_plane_rails",
                _horizontal_waist_brace(params, variant),
                [
                    -params.cube_outer / 2,
                    horizontal_rear_y,
                ],
            )
        )

    brace_hardware_clearance = {"enabled": False, "braces": []}
    if brace_clearance_details:
        brace_data = []
        total_woofer_overlap_mm3 = 0.0
        total_passive_overlap_mm3 = 0.0
        total_binding_post_overlap_mm3 = 0.0
        for name, brace, y_range in brace_clearance_details:
            woofer_overlap_mm3 = sum(
                (brace & solid).volume for solid in woofer.solids()
            )
            passive_overlap_mm3 = sum(
                (brace & solid).volume for solid in passive_radiator.solids()
            )
            total_woofer_overlap_mm3 += woofer_overlap_mm3
            total_passive_overlap_mm3 += passive_overlap_mm3
            binding_post_overlap_mm3 = sum(
                _intersection_volume(binding_post, brace)
                for binding_post in binding_posts
            )
            total_binding_post_overlap_mm3 += binding_post_overlap_mm3
            brace_data.append(
                {
                    "name": name,
                    "y_range_mm": [round(value, 3) for value in y_range],
                    "woofer_overlap_mm3": round(woofer_overlap_mm3, 6),
                    "passive_radiator_overlap_mm3": round(
                        passive_overlap_mm3,
                        6,
                    ),
                    "binding_post_overlap_mm3": round(
                        binding_post_overlap_mm3,
                        6,
                    ),
                }
            )
        if (
            total_woofer_overlap_mm3 > 0.001
            or total_passive_overlap_mm3 > 0.001
        ):
            raise ValueError(
                "Internal braces intersect installed hardware: "
                f"woofer={total_woofer_overlap_mm3:.6f} mm^3, "
                f"passive_radiator={total_passive_overlap_mm3:.6f} mm^3"
            )
        brace_hardware_clearance = {
            "enabled": True,
            "braces": brace_data,
            "total_woofer_overlap_mm3": round(total_woofer_overlap_mm3, 6),
            "total_passive_radiator_overlap_mm3": round(
                total_passive_overlap_mm3,
                6,
            ),
            "total_binding_post_overlap_mm3": round(
                total_binding_post_overlap_mm3,
                6,
            ),
        }

    return {
        f"{prefix}_final_enclosure.step": enclosure,
        f"{prefix}_final_enclosure_with_heat_set_inserts.step": enclosure_with_inserts,
        f"{prefix}_final_enclosure_with_inserts_pr_gx16.step": enclosure_with_pr_gx16,
        f"{prefix}_final_complete_assembly.step": complete_assembly,
    }, {
        "gx16": gx16_data,
        "hardware_y_bbox_clearance": {
            "woofer_bbox_y_mm": [
                round(woofer_bb.min.Y, 3),
                round(woofer_bb.max.Y, 3),
            ],
            "passive_radiator_bbox_y_mm": [
                round(passive_bb.min.Y, 3),
                round(passive_bb.max.Y, 3),
            ],
            "woofer_to_passive_radiator_gap_mm": round(
                passive_bb.min.Y - woofer_bb.max.Y,
                3,
            ),
            "overlap_risk": passive_bb.min.Y < woofer_bb.max.Y,
        },
        "installed_hardware_fit": {
            "woofer_enclosure_overlap_mm3": round(
                woofer_enclosure_overlap,
                6,
            ),
            "passive_radiator_enclosure_overlap_mm3": round(
                passive_enclosure_overlap,
                6,
            ),
            "woofer_passive_radiator_overlap_mm3": round(
                woofer_passive_overlap,
                6,
            ),
            "binding_posts": {
                "source": str(BINDING_POST_STEP.relative_to(ROOT)),
                "count": len(binding_posts),
                "positions_xy_mm": [
                    [-params.binding_post_spacing / 2, params.binding_post_y],
                    [params.binding_post_spacing / 2, params.binding_post_y],
                ],
                "mount_seat": "underside_of_11_mm_body_flange",
                "mount_seat_raw_z_mm": BINDING_POST_MOUNT_SEAT_RAW_Z,
                "mount_seat_installed_z_mm": params.cube_outer / 2,
                "modeled_thread_major_d_mm": BINDING_POST_THREAD_MAJOR_D,
                "measured_max_through_d_mm": BINDING_POST_MEASURED_THROUGH_D,
                "as_printed_pilot_profile": (
                    "diamond"
                    if variant.binding_post_diamond_pilot
                    else "round"
                ),
                "as_printed_pilot_diagonal_mm": (
                    variant.binding_post_diamond_pilot_diagonal
                    if variant.binding_post_diamond_pilot
                    else None
                ),
                "finish_drill_d_mm": params.binding_post_hole_d,
                "post_process_required": variant.binding_post_diamond_pilot,
                "finished_physical_diametral_clearance_mm": round(
                    params.binding_post_hole_d
                    - BINDING_POST_MEASURED_THROUGH_D,
                    3,
                ),
                "finished_physical_interference_expected": (
                    params.binding_post_hole_d < BINDING_POST_MEASURED_THROUGH_D
                ),
                "cad_model_diametral_interference_mm": round(
                    max(
                        0.0,
                        BINDING_POST_THREAD_MAJOR_D - params.binding_post_hole_d,
                    ),
                    3,
                ),
                "enclosure_overlap_mm3_each": [
                    round(volume, 6)
                    for volume in binding_post_enclosure_overlaps
                ],
                "cad_model_interference_detected": any(
                    volume > 0.001
                    for volume in binding_post_enclosure_overlaps
                ),
                "cad_model_note": (
                    "STEP through-section exceeds both the measured physical part "
                    "and the intentionally undersized as-printed drill pilot"
                ),
                "other_hardware_overlap_mm3_each": [
                    round(volume, 6)
                    for volume in binding_post_other_hardware_overlaps
                ],
                "post_to_post_overlap_mm3": round(
                    binding_post_to_post_overlap,
                    6,
                ),
            },
        },
        "internal_brace_hardware_clearance": brace_hardware_clearance,
        "solid_counts": {
            "enclosure": len(enclosure.solids()),
            "driver_inserts": len(driver_insert_solids),
            "pr_inserts": len(pr_inserts.solids()),
            "passive_radiator": len(passive_radiator.solids()),
            "binding_posts": len(binding_post_solids),
            "gx16": len(gx16.solids()),
            "woofer": len(woofer.solids()),
            "enclosure_with_inserts": len(enclosure_with_inserts.solids()),
            "enclosure_with_inserts_pr_gx16": len(enclosure_with_pr_gx16.solids()),
            "complete_assembly": len(complete_assembly.solids()),
        },
    }


def build_variant(variant: Variant) -> tuple[Part, dict[str, object]]:
    params = _final_params(variant)

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
    baffle_outer_d = _baffle_outer_d(params, variant)

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

    side_void_z_span = shell_span
    side_void_z_center = 0.0
    if variant.solid_bottom:
        side_void_z_min = -half + _wall_stack_t(params)
        side_void_z_max = half - params.outer_skin_t
        side_void_z_span = side_void_z_max - side_void_z_min
        side_void_z_center = (side_void_z_min + side_void_z_max) / 2

    for x in (-1, 1):
        enclosure -= Pos(
            x * (half - params.outer_skin_t - params.void_t / 2),
            cavity_center_y,
            side_void_z_center,
        ) * _filleted_box(
            params.void_t,
            cavity_y,
            side_void_z_span,
            radius=SAND_VOID_EDGE_FILLET_R,
        )
    z_void_sides = (1,) if variant.solid_bottom else (-1, 1)
    for z in z_void_sides:
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

    bridge_post_root_edges = []
    bridge_post_root_fillet_r = 0.0
    if variant.skin_bridge_posts:
        enclosure += _skin_bridge_posts(params, cavity_y_span=cavity_y)
        enclosure = _primary_shape(enclosure)
        bridge_post_root_edges = _bridge_post_root_edges(enclosure, params)
        if len(bridge_post_root_edges) < 60:
            raise ValueError(
                "Expected at least 60 bridge-post root edges, "
                f"found {len(bridge_post_root_edges)}"
            )
        bridge_post_root_fillet_r = _bridge_post_root_fillet_r(params)
        enclosure = fillet(
            bridge_post_root_edges,
            radius=bridge_post_root_fillet_r,
        )
        enclosure = _primary_shape(enclosure)
    enclosure += _gx16_connector_island(params)
    enclosure = _primary_shape(enclosure)
    top_reinforcement_island = (
        _variant_top_reinforcement_island(params, variant) & outer_solid
    )
    enclosure += top_reinforcement_island
    enclosure = _primary_shape(enclosure)

    window_brace_cavity_intrusion_l = 0.0
    vertical_brace_cavity_intrusion_l = 0.0
    horizontal_brace_cavity_intrusion_l = 0.0
    internal_brace_cavity_intrusion_l = 0.0
    internal_brace_parts = []
    if variant.window_brace:
        window_brace = _window_brace(params, variant)
        window_brace_cavity_intrusion_l = (
            (window_brace & acoustic_cavity).volume / 1_000_000
        )
        internal_brace_parts.append(window_brace)
    if variant.vertical_center_brace:
        vertical_brace = _vertical_center_brace(params, variant) & outer_solid
        vertical_brace_cavity_intrusion_l = (
            (vertical_brace & acoustic_cavity).volume / 1_000_000
        )
        internal_brace_parts.append(vertical_brace)
    if variant.horizontal_waist_brace:
        horizontal_brace = _horizontal_waist_brace(params, variant) & outer_solid
        horizontal_brace_cavity_intrusion_l = (
            (horizontal_brace & acoustic_cavity).volume / 1_000_000
        )
        internal_brace_parts.append(horizontal_brace)
    if internal_brace_parts:
        internal_braces = internal_brace_parts[0]
        for brace_part in internal_brace_parts[1:]:
            internal_braces += brace_part
        internal_brace_cavity_intrusion_l = (
            (internal_braces & acoustic_cavity).volume / 1_000_000
        )

    front_visible_tool = _front_tool_global_oriented(
        _curve_to_micro_seat_tool(params, variant),
        params,
        variant,
    )
    enclosure -= front_visible_tool
    enclosure = _primary_shape(enclosure)

    relief = _front_tool_global_oriented(
        _inner_relief_tool(params, variant),
        params,
        variant,
    )
    relief_clip = Pos(0, -half + params.front_cap_t / 2, 0) * Box(
        cavity_side,
        params.front_cap_t + 0.5,
        cavity_side,
    )
    enclosure -= relief & relief_clip
    enclosure = _primary_shape(enclosure)

    driver_mount_cutouts = _driver_mount_cutouts(params, variant, front_inner_y)
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
    enclosure -= driver_mount_cutouts
    enclosure = _primary_shape(enclosure)
    enclosure -= pr_insert_bores
    enclosure = _primary_shape(enclosure)
    enclosure -= _gx16_rear_cutout_corner(params)
    enclosure = _primary_shape(enclosure)
    enclosure -= _top_binding_post_holes(params, variant)
    enclosure = _primary_shape(enclosure)
    if variant.front_bracket_holes:
        enclosure -= _top_front_bracket_cutouts(params)
        enclosure = _primary_shape(enclosure)
    if variant.bottom_tripod_indent_positions:
        enclosure -= _bottom_tripod_indent_cutouts(params, variant)
        enclosure = _primary_shape(enclosure)

    if internal_brace_parts:
        internal_braces = _primary_shape(
            (internal_braces & outer_solid) - front_visible_tool
        )
        enclosure += internal_braces
        enclosure = _primary_shape(enclosure)

    seat_lip_edges = _driver_seat_lip_edges(enclosure, params)
    if len(seat_lip_edges) != 1:
        raise ValueError(
            f"Expected one driver-seat lip edge, found {len(seat_lip_edges)}"
        )
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
    if 0 < len(front_inner_wall_seam_edges) < 8:
        raise ValueError(
            "Expected at least 8 front inner wall seam edges, "
            f"found {len(front_inner_wall_seam_edges)}"
        )
    if front_inner_wall_seam_edges:
        enclosure = fillet(front_inner_wall_seam_edges, radius=INTERNAL_SEAM_FILLET_R)
        enclosure = _primary_shape(enclosure)

    for fill_x in (-params.fill_port_x, params.fill_port_x):
        enclosure -= _variant_sand_fill_port_cutout(
            params,
            variant,
            x=fill_x,
            z=params.fill_port_z,
        )
        enclosure = _require_single_solid(
            enclosure,
            feature=f"fill-port cut at x={fill_x}",
        )
    if (
        variant.fill_port_transition_length > 0
        and variant.fill_port_transition_support_wall > 0
    ):
        for fill_x in (-params.fill_port_x, params.fill_port_x):
            enclosure += _fill_port_inner_support(
                params,
                variant,
                x=fill_x,
                z=params.fill_port_z,
            )
            enclosure = _require_single_solid(
                enclosure,
                feature=f"fill-port support at x={fill_x}",
            )
            enclosure -= _variant_sand_fill_port_cutout(
                params,
                variant,
                x=fill_x,
                z=params.fill_port_z,
            )
            enclosure = _require_single_solid(
                enclosure,
                feature=f"fill-port support passage at x={fill_x}",
            )

    front_baffle_seam_edges = _front_baffle_seam_edges(enclosure, params, variant)
    if len(front_baffle_seam_edges) != 1:
        raise ValueError(
            "Expected one visible front-baffle periodic seam edge, "
            f"found {len(front_baffle_seam_edges)}"
        )
    front_baffle_seam_bb = front_baffle_seam_edges[0].bounding_box()

    driver_mount_cut_d = (
        variant.driver_mount_divot_d
        if variant.driver_mount_divots
        else params.insert_bore_d
    )
    driver_mount_cut_depth = (
        variant.driver_mount_divot_depth
        if variant.driver_mount_divots
        else params.driver_insert_bore_depth
    )
    driver_mount_cut_r = driver_mount_cut_d / 2
    driver_mount_clearance_radii = {
        "outer_cut_edge": params.driver_bolt_circle_r + driver_mount_cut_r,
        "centerline": params.driver_bolt_circle_r,
        "inner_cut_edge": params.driver_bolt_circle_r - driver_mount_cut_r,
        "inner_cut_edge_minus_0_4_tolerance": params.driver_bolt_circle_r
        - driver_mount_cut_r
        - 0.4,
    }
    driver_mount_cut_tip_depth = params.front_cap_t - driver_mount_cut_depth
    driver_mount_clearance_points = {}
    for name, radius in driver_mount_clearance_radii.items():
        front_depth = _front_depth_at_radius(
            radius=radius,
            r_outer=baffle_outer_d / 2,
            r_inner=params.driver_cutout_dia / 2,
            depth=_recess_depth(variant),
            endpoint_depth=_front_curve_endpoint_depth(variant),
        )
        driver_mount_clearance_points[name] = {
            "radius_mm": round(radius, 3),
            "front_surface_depth_mm": round(front_depth, 3),
            "cut_tip_cover_mm": round(
                driver_mount_cut_tip_depth - front_depth,
                3,
            ),
        }
    driver_mount_front_clearance = driver_mount_clearance_points[
        "inner_cut_edge"
    ][
        "cut_tip_cover_mm"
    ]

    outer_envelope_overrun_mm3 = sum(
        solid.volume for solid in (enclosure - outer_solid).solids()
    )
    if outer_envelope_overrun_mm3 > 0.001:
        raise ValueError(
            "Finished enclosure extends outside the filleted outer envelope by "
            f"{outer_envelope_overrun_mm3:.6f} mm^3"
        )

    bb = enclosure.bounding_box()
    nominal_cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000
    hex_half_extent = _hex_half_extent(GX16_HEX_ROTATION)
    inner_cavity_half = cavity_side / 2
    pr_mount_y = half - params.pr_recess_depth
    pr_bore_tip_y = pr_mount_y - params.pr_insert_bore_depth
    pr_insert_tip_y = pr_mount_y - DRIVER_INSERT_LENGTH
    pr_inner_face_y = half - params.rear_cap_t
    wall_stack_t = _wall_stack_t(params)
    baffle_edge_clearance = half - baffle_outer_d / 2
    baffle_clearance_after_fillet = baffle_edge_clearance - params.edge_fillet_r
    pr_recess_edge_clearance = half - params.pr_recess_dia / 2
    pr_overall_edge_clearance = (params.cube_outer - params.pr_overall_dia) / 2
    fill_port_cut_r = max(params.fill_entry_d, params.fill_thread_major_d) / 2
    fill_port_low_z = params.fill_port_z - fill_port_cut_r
    fill_port_high_z = params.fill_port_z + fill_port_cut_r
    outer_skin_inner_z = half - params.outer_skin_t
    fill_port_void_center_z = outer_skin_inner_z - params.void_t / 2
    if fill_port_high_z > outer_skin_inner_z + 0.001:
        raise ValueError("Fill-port bore intersects the outer top skin")
    if (
        fill_port_low_z < inner_cavity_half - 0.001
        and variant.fill_port_transition_support_wall <= 0
    ):
        raise ValueError("Fill-port bore enters the cavity without a support shell")
    fill_port_side_fillet_clearance = (
        half
        - params.edge_fillet_r
        - abs(params.fill_port_x)
        - fill_port_cut_r
    )
    if fill_port_side_fillet_clearance < 0:
        raise ValueError("Fill-port entry overlaps the side-corner fillet")
    tripod_indent_r = variant.bottom_tripod_indent_d / 2
    tripod_indent_edge_clearances = [
        min(
            half - params.edge_fillet_r - abs(x) - tripod_indent_r,
            half - params.edge_fillet_r - abs(y) - tripod_indent_r,
        )
        for x, y in variant.bottom_tripod_indent_positions
    ]
    if tripod_indent_edge_clearances and min(tripod_indent_edge_clearances) < 0:
        raise ValueError("Bottom tripod indent overlaps an outer corner fillet")
    driver_rear_y_est = front_inner_y + params.driver_depth + WOOFER_ASSEMBLY_CLEARANCE
    pr_interior_y_est = half + HARDWARE_CLEARANCE - params.pr_depth
    driver_pr_gap_est = pr_interior_y_est - driver_rear_y_est
    rear_pr_intrusion_into_cavity = max(0.0, pr_inner_face_y - pr_interior_y_est)
    volume_summary = _volume_summary(variant)
    top_island_front_y = params.top_island_y - params.top_island_d / 2
    top_island_rear_y = params.top_island_y + params.top_island_d / 2
    top_hole_r = params.binding_post_hole_d / 2
    if variant.binding_post_diamond_pilot and not (
        0
        < variant.binding_post_diamond_pilot_diagonal
        < params.binding_post_hole_d
    ):
        raise ValueError(
            "Binding-post diamond pilot must be positive and smaller than finish hole"
        )
    top_island_margins = {
        "front": params.binding_post_y - top_hole_r - top_island_front_y,
        "back": top_island_rear_y - (params.binding_post_y + top_hole_r),
        "side": params.top_island_w / 2
        - (params.binding_post_spacing / 2 + top_hole_r),
    }
    if variant.top_island_hole_margin is not None and any(
        abs(value - variant.top_island_hole_margin) > 0.001
        for value in top_island_margins.values()
    ):
        raise ValueError(
            "Top island does not preserve the requested uniform hole-edge margin: "
            f"{top_island_margins}"
        )
    diagnostics = {
        "name": variant.name,
        "cube_outer_mm": params.cube_outer,
        "cube_outer_in": params.cube_outer / 25.4,
        "edge_fillet_r_mm": params.edge_fillet_r,
        "outer_envelope": {
            "reinforcement_island_clipped_to_fillet": True,
            "material_outside_filleted_envelope_mm3": round(
                outer_envelope_overrun_mm3,
                6,
            ),
        },
        "wall_stack_mm": {
            "outer_skin": params.outer_skin_t,
            "sand_air_gap": params.void_t,
            "inner_skin": params.inner_skin_t,
            "total_side_top_bottom": wall_stack_t,
            "bottom_is_solid_plastic": variant.solid_bottom,
            "bottom_solid_thickness": wall_stack_t if variant.solid_bottom else None,
            "front_cap": params.front_cap_t,
            "rear_cap": params.rear_cap_t,
        },
        "front_recess_depth_mm": _recess_depth(variant),
        "front_recess_depth_in": _recess_depth(variant) / 25.4,
        "front_curve_endpoint_depth_mm": _front_curve_endpoint_depth(variant),
        "direct_curve_to_driver_seat": variant.direct_curve_to_driver_seat,
        "visible_cylindrical_transition_height_mm": (
            0.0
            if variant.direct_curve_to_driver_seat
            else variant.driver_seat_extra_depth
        ),
        "driver_seat_extra_depth_mm": variant.driver_seat_extra_depth,
        "driver_seat_depth_mm": params.front_cap_t,
        "front_curve_driver_control_depth_factor": (
            FRONT_CURVE_DRIVER_CONTROL_DEPTH_FACTOR
        ),
        "target_wall_t_mm": variant.wall_t,
        "baffle_outer_d_mm": baffle_outer_d,
        "front_face_edge_clearance_mm": variant.front_face_edge_clearance,
        "front_baffle_fit": {
            "radial_clearance_to_cube_edge_mm": round(baffle_edge_clearance, 3),
            "clearance_after_edge_fillet_mm": round(
                baffle_clearance_after_fillet,
                3,
            ),
            "fits_with_requested_clearance": baffle_clearance_after_fillet
            >= variant.front_face_edge_clearance - 0.01,
        },
        "front_baffle_periodic_seam": {
            "topological_edge_only": True,
            "rotation_deg": variant.front_baffle_seam_rotation_deg,
            "location": "bottom_6_oclock",
            "edge_count": len(front_baffle_seam_edges),
            "edge_bbox_mm": [
                [
                    round(front_baffle_seam_bb.min.X, 3),
                    round(front_baffle_seam_bb.min.Y, 3),
                    round(front_baffle_seam_bb.min.Z, 3),
                ],
                [
                    round(front_baffle_seam_bb.max.X, 3),
                    round(front_baffle_seam_bb.max.Y, 3),
                    round(front_baffle_seam_bb.max.Z, 3),
                ],
            ],
            "controls_slicer_z_seam": False,
        },
        "front_inner_relief": {
            "min_cover_to_visible_curve_mm": variant.wall_t,
            "relief_forward_limit_y_mm": round(-half + variant.wall_t, 3),
            "front_face_y_mm": round(-half, 3),
            "pierce_risk": variant.wall_t <= 0,
        },
        "driver_cutout_dia_mm": params.driver_cutout_dia,
        "seat_land_od_mm": SEAT_LAND_OD,
        "front_seat_y_mm": front_inner_y,
        "cavity_side_mm": round(cavity_side, 3),
        "cavity_y_mm": round(cavity_y, 3),
        "plain_wall_stack_cavity_l": round(_plain_wall_stack_cavity_l(params), 3),
        "nominal_cavity_l": round(nominal_cavity_l, 3),
        "modeled_front_inner_relief_l": round(
            volume_summary["modeled_front_inner_relief_l"],
            3,
        ),
        "acoustic_cavity_plus_front_relief_l": round(
            volume_summary["acoustic_cavity_plus_front_relief_l"],
            3,
        ),
        "transverse_window_brace_cavity_displacement_l": round(
            window_brace_cavity_intrusion_l,
            3,
        ),
        "vertical_center_brace_cavity_displacement_l": round(
            vertical_brace_cavity_intrusion_l,
            3,
        ),
        "horizontal_waist_brace_cavity_displacement_l": round(
            horizontal_brace_cavity_intrusion_l,
            3,
        ),
        "total_internal_brace_cavity_displacement_l": round(
            internal_brace_cavity_intrusion_l,
            3,
        ),
        "net_acoustic_volume_after_internal_braces_l": round(
            volume_summary["acoustic_cavity_plus_front_relief_l"]
            - internal_brace_cavity_intrusion_l,
            3,
        ),
        "volume_comparison": _volume_comparison(variant),
        "fill_ports": {
            "x_mm": params.fill_port_x,
            "x_positions_mm": [-params.fill_port_x, params.fill_port_x],
            "z_mm": round(params.fill_port_z, 3),
            "threaded": variant.fill_port_threaded,
            "smooth_bore_d_mm": (
                None if variant.fill_port_threaded else params.fill_entry_d
            ),
            "entry_d_mm": params.fill_entry_d,
            "thread_major_d_mm": (
                params.fill_thread_major_d if variant.fill_port_threaded else None
            ),
            "thread_core_d_mm": (
                params.fill_thread_core_d if variant.fill_port_threaded else None
            ),
            "thread_length_mm": (
                params.fill_thread_length if variant.fill_port_threaded else None
            ),
            "void_transition": {
                "enabled": variant.fill_port_transition_length > 0,
                "profile": "smoothstep_centerline_loft",
                "length_y_mm": variant.fill_port_transition_length,
                "entry_center_z_mm": round(params.fill_port_z, 3),
                "sand_void_center_z_mm": round(fill_port_void_center_z, 3),
                "centerline_rise_mm": round(
                    fill_port_void_center_z - params.fill_port_z,
                    3,
                ),
                "bore_end_d_mm": params.fill_entry_d,
                "full_diameter_through_rear_cap_mm": params.rear_cap_t,
                "sand_void_end_d_mm": params.void_t,
                "masked_skin_lip_removed_per_side_mm": round(
                    (params.fill_entry_d - params.void_t) / 2,
                    3,
                ),
                "outer_skin_bore_overlap_mm": round(
                    max(0.0, fill_port_high_z - outer_skin_inner_z),
                    3,
                ),
                "internal_support_wall_mm": (
                    variant.fill_port_transition_support_wall
                ),
                "support_protrusion_into_cavity_mm": round(
                    max(
                        0.0,
                        inner_cavity_half
                        - (
                            params.fill_port_z
                            - params.fill_entry_d / 2
                            - variant.fill_port_transition_support_wall
                        ),
                    ),
                    3,
                ),
                "passage_clearance_to_side_inner_face_mm": round(
                    inner_cavity_half
                    - abs(params.fill_port_x)
                    - params.fill_entry_d / 2,
                    3,
                ),
                "unclipped_support_overlap_into_side_skin_mm": round(
                    max(
                        0.0,
                        abs(params.fill_port_x)
                        + params.fill_entry_d / 2
                        + variant.fill_port_transition_support_wall
                        - inner_cavity_half,
                    ),
                    3,
                ),
                "support_side_skin_embed_mm": FILL_PORT_SUPPORT_SKIN_EMBED,
                "tangent_at_bore_and_void_ends": True,
            },
            "cut_z_range_mm": [
                round(fill_port_low_z, 3),
                round(fill_port_high_z, 3),
            ],
            "cavity_top_z_mm": round(inner_cavity_half, 3),
            "top_face_z_mm": round(half, 3),
            "outer_skin_inner_z_mm": round(outer_skin_inner_z, 3),
            "nominal_clearance_to_cavity_mm": round(
                fill_port_low_z - inner_cavity_half,
                3,
            ),
            "nominal_clearance_to_top_face_mm": round(half - fill_port_high_z, 3),
            "clearance_to_outer_skin_inner_face_mm": round(
                outer_skin_inner_z - fill_port_high_z,
                3,
            ),
            "side_corner_fillet_tangent_x_mm": round(
                half - params.edge_fillet_r,
                3,
            ),
            "entry_edge_clearance_to_side_corner_fillet_mm": round(
                fill_port_side_fillet_clearance,
                3,
            ),
            "overlaps_side_corner_radius": fill_port_side_fillet_clearance < 0,
            "nominal_intrusion_into_cavity_mm": round(
                max(0.0, inner_cavity_half - fill_port_low_z),
                3,
            ),
            "cavity_intrusion_is_supported": (
                variant.fill_port_transition_support_wall > 0
            ),
            "pierce_risk": (
                fill_port_high_z > outer_skin_inner_z
                or (
                    fill_port_low_z <= inner_cavity_half
                    and variant.fill_port_transition_support_wall <= 0
                )
            ),
            "top_void_z_range_mm": [
                round(half - params.outer_skin_t - params.void_t, 3),
                round(half - params.outer_skin_t, 3),
            ],
        },
        "bottom_tripod_indents": {
            "enabled": bool(variant.bottom_tripod_indent_positions),
            "face": "bottom_z_negative",
            "positions_xy_mm": [
                [round(x, 3), round(y, 3)]
                for x, y in variant.bottom_tripod_indent_positions
            ],
            "diameter_mm": variant.bottom_tripod_indent_d,
            "depth_mm": variant.bottom_tripod_indent_depth,
            "edge_clearance_to_corner_fillet_mm": [
                round(clearance, 3)
                for clearance in tripod_indent_edge_clearances
            ],
            "remaining_solid_bottom_mm": round(
                wall_stack_t - variant.bottom_tripod_indent_depth,
                3,
            ),
            "pierce_risk": variant.bottom_tripod_indent_depth >= wall_stack_t,
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
        "passive_radiator": {
            "overall_dia_mm": params.pr_overall_dia,
            "recess_dia_mm": params.pr_recess_dia,
            "recess_depth_mm": params.pr_recess_depth,
            "edge_clearance_per_side_mm": round(pr_overall_edge_clearance, 3),
            "recess_edge_clearance_per_side_mm": round(
                pr_recess_edge_clearance,
                3,
            ),
            "recess_clearance_after_edge_fillet_mm": round(
                pr_recess_edge_clearance - params.edge_fillet_r,
                3,
            ),
            "fits_rear_face": pr_recess_edge_clearance >= 0,
            "fits_flat_after_edge_fillet": pr_recess_edge_clearance
            >= params.edge_fillet_r + variant.front_face_edge_clearance - 0.01,
        },
        "driver_mounting": {
            "mode": (
                "shallow_locating_divots"
                if variant.driver_mount_divots
                else "heat_set_insert_bores"
            ),
            "bolt_circle_r_mm": params.driver_bolt_circle_r,
            "count": params.driver_screw_count,
            "positions_xz_mm": [
                [round(x, 3), round(z, 3)]
                for x, z in _bolt_circle_positions(
                    radius=params.driver_bolt_circle_r,
                    count=params.driver_screw_count,
                )
            ],
            "cut_dia_mm": driver_mount_cut_d,
            "cut_depth_mm": driver_mount_cut_depth,
            "open_face_y_mm": round(front_inner_y, 3),
            "cut_tip_depth_from_front_mm": round(driver_mount_cut_tip_depth, 3),
            "clearance_points": driver_mount_clearance_points,
            "worst_nominal_cut_tip_cover_mm": driver_mount_front_clearance,
            "driver_heat_set_inserts_exported": not variant.driver_mount_divots,
            "pierce_risk": driver_mount_front_clearance <= 0,
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
        "y_depth_clearance_estimate": {
            "basis": "sourced driver_depth/pr_depth parameters, not STEP bbox",
            "driver_depth_mm": params.driver_depth,
            "passive_radiator_depth_mm": params.pr_depth,
            "driver_rear_y_est_mm": round(driver_rear_y_est, 3),
            "passive_radiator_inner_y_est_mm": round(pr_interior_y_est, 3),
            "driver_to_pr_gap_est_mm": round(driver_pr_gap_est, 3),
            "rear_pr_intrusion_into_cavity_est_mm": round(
                rear_pr_intrusion_into_cavity,
                3,
            ),
            "driver_clearance_to_rear_inner_face_mm": round(
                pr_inner_face_y - driver_rear_y_est,
                3,
            ),
            "risk": driver_pr_gap_est < 10.0,
        },
        "skin_bridge_posts": {
            "enabled": variant.skin_bridge_posts,
            "count": len(bridge_post_root_edges) // 2,
            "xz_positions_mm": (
                [round(v, 3) for v in _grid3_for_span(cavity_side)]
                if variant.skin_bridge_posts
                else []
            ),
            "y_positions_mm": (
                [round(v, 3) for v in _grid3_for_span(cavity_y)]
                if variant.skin_bridge_posts
                else []
            ),
        },
        "window_brace": {
            "enabled": variant.window_brace,
            "orientation": "X-Z perimeter frame",
            "center_y_mm": variant.window_brace_center_y,
            "centered_on_cabinet_y": abs(variant.window_brace_center_y) < 0.001,
            "y_range_mm": [
                round(
                    variant.window_brace_center_y
                    - variant.window_brace_width / 2,
                    3,
                ),
                round(
                    variant.window_brace_center_y
                    + variant.window_brace_width / 2,
                    3,
                ),
            ],
            "width_y_mm": variant.window_brace_width,
            "height_from_cavity_wall_mm": variant.window_brace_height,
            "inner_opening_side_mm": round(
                cavity_side - 2 * variant.window_brace_height,
                3,
            ),
            "inner_corner_r_mm": variant.window_brace_corner_r,
            "skin_embed_mm": variant.window_brace_skin_embed,
            "cavity_displacement_l": round(window_brace_cavity_intrusion_l, 3),
            "radial_clearance_to_driver_frame_mm": round(
                (cavity_side - 2 * variant.window_brace_height - 152.5) / 2,
                3,
            ),
        },
        "vertical_center_brace": {
            "enabled": variant.vertical_center_brace,
            "orientation": "Y-Z center plane; top and bottom rails",
            "center_x_mm": 0.0,
            "y_range_mm": [
                round(-half, 3),
                round(
                    rear_inner_y
                    if variant.vertical_brace_rear_y is None
                    else variant.vertical_brace_rear_y,
                    3,
                ),
            ],
            "width_x_mm": variant.vertical_brace_width,
            "height_from_cavity_wall_mm": variant.vertical_brace_height,
            "skin_embed_mm": variant.vertical_brace_skin_embed,
            "cavity_displacement_l": round(
                vertical_brace_cavity_intrusion_l,
                3,
            ),
            "radial_clearance_to_driver_seat_land_mm": round(
                0.0,
                3,
            ),
            "front_end_blend": {
                "length_y_mm": LONGITUDINAL_BRACE_END_BLEND_L,
                "driver_seat_outer_r_mm": SEAT_LAND_OD / 2,
                "rail_inner_r_mm": round(
                    inner_cavity_half - variant.vertical_brace_height,
                    3,
                ),
                "filled_radial_gap_mm": round(
                    inner_cavity_half
                    - variant.vertical_brace_height
                    - SEAT_LAND_OD / 2,
                    3,
                ),
                "tangent_at_ring_and_rail": True,
                "backfilled_to_contoured_front_surface": True,
            },
            "rear_end_blend": {
                "length_y_mm": LONGITUDINAL_BRACE_END_BLEND_L,
                "passive_radiator_opening_r_mm": params.pr_service_cutout_dia / 2,
                "rail_inner_r_mm": round(
                    inner_cavity_half - variant.vertical_brace_height,
                    3,
                ),
                "filled_radial_gap_mm": round(
                    inner_cavity_half
                    - variant.vertical_brace_height
                    - params.pr_service_cutout_dia / 2,
                    3,
                ),
                "tangent_at_ring_and_rail": True,
            },
            "front_wall_contact": True,
            "front_end_trimmed_to_inner_black_hole_surface": True,
            "rear_wall_contact": (
                variant.vertical_brace_rear_y is None
                or abs(variant.vertical_brace_rear_y - rear_inner_y) < 0.001
            ),
            "rear_end_ahead_of_passive_radiator_est_mm": round(
                pr_interior_y_est
                - (
                    rear_inner_y
                    if variant.vertical_brace_rear_y is None
                    else variant.vertical_brace_rear_y
                ),
                3,
            ),
        },
        "horizontal_waist_brace": {
            "enabled": variant.horizontal_waist_brace,
            "orientation": "X-Y center plane; left and right rails",
            "center_z_mm": 0.0,
            "y_range_mm": [
                round(-half, 3),
                round(
                    rear_inner_y
                    if variant.horizontal_brace_rear_y is None
                    else variant.horizontal_brace_rear_y,
                    3,
                ),
            ],
            "width_z_mm": variant.horizontal_brace_width,
            "height_from_cavity_wall_mm": variant.horizontal_brace_height,
            "skin_embed_mm": variant.horizontal_brace_skin_embed,
            "cavity_displacement_l": round(
                horizontal_brace_cavity_intrusion_l,
                3,
            ),
            "front_wall_contact": True,
            "front_end_trimmed_to_inner_black_hole_surface": True,
            "rear_wall_contact": (
                variant.horizontal_brace_rear_y is None
                or abs(variant.horizontal_brace_rear_y - rear_inner_y) < 0.001
            ),
            "radial_clearance_to_driver_seat_land_mm": round(
                0.0,
                3,
            ),
            "front_end_blend": {
                "length_y_mm": LONGITUDINAL_BRACE_END_BLEND_L,
                "driver_seat_outer_r_mm": SEAT_LAND_OD / 2,
                "rail_inner_r_mm": round(
                    inner_cavity_half - variant.horizontal_brace_height,
                    3,
                ),
                "filled_radial_gap_mm": round(
                    inner_cavity_half
                    - variant.horizontal_brace_height
                    - SEAT_LAND_OD / 2,
                    3,
                ),
                "tangent_at_ring_and_rail": True,
                "backfilled_to_contoured_front_surface": True,
            },
            "rear_end_blend": {
                "length_y_mm": LONGITUDINAL_BRACE_END_BLEND_L,
                "passive_radiator_opening_r_mm": params.pr_service_cutout_dia / 2,
                "rail_inner_r_mm": round(
                    inner_cavity_half - variant.horizontal_brace_height,
                    3,
                ),
                "filled_radial_gap_mm": round(
                    inner_cavity_half
                    - variant.horizontal_brace_height
                    - params.pr_service_cutout_dia / 2,
                    3,
                ),
                "tangent_at_ring_and_rail": True,
            },
        },
        "top_plate": {
            "binding_posts_act_as_rear_clamp_points": True,
            "binding_post_as_printed_profile": (
                "diamond" if variant.binding_post_diamond_pilot else "round"
            ),
            "binding_post_as_printed_pilot_diagonal_mm": (
                variant.binding_post_diamond_pilot_diagonal
                if variant.binding_post_diamond_pilot
                else None
            ),
            "binding_post_finish_drill_d_mm": params.binding_post_hole_d,
            "binding_post_post_process_required": (
                variant.binding_post_diamond_pilot
            ),
            "binding_post_pilot_wall_angle_deg": (
                45.0 if variant.binding_post_diamond_pilot else None
            ),
            "binding_post_print_orientation": (
                "rear_face_down_build_toward_front_negative_y"
                if variant.binding_post_diamond_pilot
                else None
            ),
            "binding_post_holes": [
                [-params.binding_post_spacing / 2, params.binding_post_y],
                [params.binding_post_spacing / 2, params.binding_post_y],
            ],
            "binding_post_forward_shift_mm": variant.binding_post_forward_shift,
            "top_recesses_removed": True,
            "front_bracket_holes_enabled": variant.front_bracket_holes,
            "front_bracket_hole_d_mm": (
                params.bracket_hole_d if variant.front_bracket_holes else None
            ),
            "front_bracket_holes": (
                [
                    [
                        -params.bracket_hole_spacing / 2,
                        params.bracket_hole_y - params.bracket_hole_spacing / 2,
                    ],
                    [
                        params.bracket_hole_spacing / 2,
                        params.bracket_hole_y - params.bracket_hole_spacing / 2,
                    ],
                ]
                if variant.front_bracket_holes
                else []
            ),
            "rear_bracket_holes_removed": True,
            "reinforcement_island_x_range_mm": [
                round(-params.top_island_w / 2, 3),
                round(params.top_island_w / 2, 3),
            ],
            "reinforcement_island_y_range_mm": [
                round(top_island_front_y, 3),
                round(top_island_rear_y, 3),
            ],
            "reinforcement_island_hole_edge_margins_mm": {
                name: round(value, 3)
                for name, value in top_island_margins.items()
            },
            "reinforcement_island_uniform_hole_margin": (
                max(top_island_margins.values())
                - min(top_island_margins.values())
                < 0.001
            ),
            "reinforcement_island_detached_from_rear_face_mm": round(
                half - top_island_rear_y,
                3,
            ),
            "reinforcement_island_corner_r_mm": variant.top_island_corner_r,
        },
        "driver_seat_lip_fillet_r_mm": DRIVER_SEAT_EDGE_FILLET_R,
        "sand_void_edge_fillet": {
            "radius_mm": SAND_VOID_EDGE_FILLET_R,
            "method": "filleted_sand_void_cutout_tools",
        },
        "bridge_post_root_fillet": {
            "enabled": variant.skin_bridge_posts,
            "radius_mm": bridge_post_root_fillet_r,
            "edge_count": len(bridge_post_root_edges),
        },
        "internal_seam_fillet": {
            "radius_mm": INTERNAL_SEAM_FILLET_R,
            "edge_count": len(internal_seam_edges),
        },
        "front_inner_wall_seam_fillet": {
            "radius_mm": INTERNAL_SEAM_FILLET_R,
            "edge_count": len(front_inner_wall_seam_edges),
            "applied": bool(front_inner_wall_seam_edges),
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


def build_final_enclosure() -> tuple[Part, object, dict[str, object]]:
    """Build the current final black-hole enclosure and diagnostics.

    This is the public entry point used by final assembly/export scripts. The
    legacy 8.5 in candidate remains available as ``LEGACY_FINAL_VARIANT``;
    downstream final exports now use ``FINAL_VARIANT``.
    """
    part, data = build_variant(FINAL_VARIANT)
    if not data["is_valid"]:
        raise ValueError(f"{FINAL_VARIANT.name} generated an invalid body")
    params = _final_params(FINAL_VARIANT)
    return part, params, data


def build_final_export_shapes() -> tuple[dict[str, Compound | Part], dict[str, object]]:
    """Return the four validated enclosure/hardware STEP export shapes."""
    part, params, data = build_final_enclosure()
    final_exports, hardware_data = _final_export_set(part, params, FINAL_VARIANT)
    data["final_exports"] = hardware_data
    return final_exports, data


def export_final_enclosure_set(out: Path = OUT) -> dict[str, object]:
    """Write the final enclosure STEP set and diagnostics JSON."""
    out.mkdir(parents=True, exist_ok=True)
    final_exports, data = build_final_export_shapes()
    for filename, shape in final_exports.items():
        export_step(shape, out / filename, unit=Unit.MM)
    (out / "diagnostics.json").write_text(json.dumps([data], indent=2))
    return data


def main() -> None:
    diagnostics = [export_final_enclosure_set(OUT)]
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
