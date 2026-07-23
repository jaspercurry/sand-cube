"""Generate a perimeter-sealed, front-filled dual-fastener G1 enclosure.

This isolated sibling preserves the approved parabolic G1 exterior and the
complete mirrored captive-square-nut closure.  It replaces the rear sand-fill
entries with two baffle-hidden front entries, closes the exposed front ends of
the 2-3-2 wall void, expands the gasket onto that closed wall stack, and gives
the baffle flange and both nut housings a continuous printable load path.
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
import sys
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Plane,
    Polygon,
    Pos,
    Rot,
    Solid,
    Vector,
    extrude,
    loft,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_dual_captive_square_nut_printable"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_dual_captive_square_nut_printable as prior  # noqa: E402


source = prior.source
closure = prior.closure
base = prior.base
parent = prior.parent

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_front_fill_perimeter_seal"
)
NAME = "sand_cube_190x210_parabolic_g1_front_fill_perimeter_seal"

# The exact hidden baffle-bed cross section is 183.8655 mm across at its
# cardinal extrema.  A 183 mm structural flange therefore reaches the edge
# without crossing the visible seam.  The 5 mm tape is centered on a 6.75 mm
# land, leaving 0.875 mm placement margin on both sides.
SEAL_LAND_OUTER_SIZE_MM = 183.0
SEAL_LAND_OUTER_RADIUS_MM = 18.5
SEAL_LAND_WIDTH_MM = 6.75
SEAL_LAND_INNER_SIZE_MM = (
    SEAL_LAND_OUTER_SIZE_MM - 2.0 * SEAL_LAND_WIDTH_MM
)
SEAL_LAND_INNER_RADIUS_MM = (
    SEAL_LAND_OUTER_RADIUS_MM - SEAL_LAND_WIDTH_MM
)
GASKET_EDGE_MARGIN_MM = (
    SEAL_LAND_WIDTH_MM - source.GASKET_TAPE_WIDTH_MM
) / 2.0
GASKET_OUTER_SIZE_MM = (
    SEAL_LAND_OUTER_SIZE_MM - 2.0 * GASKET_EDGE_MARGIN_MM
)
GASKET_OUTER_RADIUS_MM = (
    SEAL_LAND_OUTER_RADIUS_MM - GASKET_EDGE_MARGIN_MM
)
GASKET_INNER_SIZE_MM = (
    GASKET_OUTER_SIZE_MM - 2.0 * source.GASKET_TAPE_WIDTH_MM
)
GASKET_INNER_RADIUS_MM = (
    GASKET_OUTER_RADIUS_MM - source.GASKET_TAPE_WIDTH_MM
)
GASKET_EXPANDED_CENTER_ABS_Z_MM = (
    GASKET_OUTER_SIZE_MM + GASKET_INNER_SIZE_MM
) / 4.0
GASKET_BYPASS_CENTER_ABS_Z_MM = source.GASKET_OUTER_SIZE_MM / 2.0 - (
    source.GASKET_TAPE_WIDTH_MM / 2.0
)
GASKET_BYPASS_INNER_HALF_X_MM = 18.0
GASKET_BYPASS_OUTER_HALF_X_MM = 42.0
GASKET_BYPASS_REMOVAL_HALF_X_MM = 42.5

SEAL_FACE_RESET_MM = 0.40
BAFFLE_FLANGE_THICKNESS_MM = source.BAFFLE_LAND_THICKNESS_MM

# The revised ramp is the inverse of the inherited shoulder: its inner face
# remains exactly flush with the inner enclosure wall while its outer face
# grows linearly from a 2 mm root to the expanded seal flange.  That removes
# the rounded/lipped inner transition while remaining comfortably support-free.
RAMP_INNER_SIZE_MM = source.GASKET_INNER_SIZE_MM
RAMP_INNER_RADIUS_MM = source.GASKET_INNER_RADIUS_MM
RAMP_ROOT_WIDTH_MM = 2.0
RAMP_ROOT_OUTER_SIZE_MM = RAMP_INNER_SIZE_MM + 2.0 * RAMP_ROOT_WIDTH_MM
RAMP_ROOT_OUTER_RADIUS_MM = RAMP_INNER_RADIUS_MM + RAMP_ROOT_WIDTH_MM
RAMP_DEPTH_MM = source.SHOULDER_SUPPORT_DEPTH_MM

# Three millimeters of material close the exact front cross section of the
# live 2-3-2 sand void.  A small expansion embeds it into both skins instead
# of depending on a face-only union.
SAND_CAP_THICKNESS_MM = 3.0
SAND_CAP_SKIN_EMBED_MM = 0.16

# Two front fill entries are hidden by the installed baffle and sit safely
# inside the enlarged gasket.  Their straight entries retain the established
# 9.15 mm fill diameter, then taper to the 3 mm sand void over a 16 mm print
# rise.  The resulting centerline slope is under 45 degrees from print Z.
FRONT_FILL_X_MM = 65.0
FRONT_FILL_Z_MM = 78.0
FRONT_FILL_TRANSITION_LENGTH_MM = 16.0
FRONT_FILL_SUPPORT_WALL_MM = 1.2
FRONT_FILL_CAP_OVERLAP_MM = 0.5
FRONT_FILL_MOUTH_OVERTRAVEL_MM = 0.30
FRONT_FILL_SECTION_COUNT = 9

# A broad triangular web grows from the seal-flange print bed to the driver
# collar.  It contains the existing nut housing without changing any screw,
# head-cubby, boss, passage, nut, or service-slot coordinate.
LOAD_WEB_WIDTH_X_MM = 20.0
LOAD_WEB_FRONT_Y_MM = source.BAFFLE_BED_Y - 15.2
LOAD_WEB_BASE_INNER_Z_MM = 70.0
LOAD_WEB_BASE_OUTER_Z_MM = 92.0
LOAD_WEB_TIP_Z_MM = 80.0

MINIMUM_GASKET_SUPPORT_RATIO = 0.985
MINIMUM_FILL_SUPPORT_ROOT_MM3 = 5.0
MINIMUM_FILL_TO_GASKET_CLEARANCE_MM = 2.0
FAIRING_AREA_TOLERANCE_MM2 = 1e-5

_JOINT_AUDIT: dict[str, Any] = {}
_FRONT_FILL_AUDIT: dict[str, Any] = {}

ORIGINAL_DUAL_CONCEPT = prior._dual_captive_square_nut_concept
ORIGINAL_SOLID_REAR_DETAIL_BASE = source.prior._solid_rear_detail_base


def _shape_volume(shape: Any) -> float:
    return prior._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return prior._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return prior._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return prior._fuse_one(shape, addition, feature=feature)


def _ring(
    *,
    outer_size: float,
    outer_radius: float,
    inner_size: float,
    inner_radius: float,
    y0: float,
    y1: float,
) -> Solid:
    return source._rounded_rectangle_ring(
        outer_size=outer_size,
        outer_radius=outer_radius,
        inner_size=inner_size,
        inner_radius=inner_radius,
        y0=y0,
        y1=y1,
    )


def _oriented_path_segment(
    start_xz: tuple[float, float],
    end_xz: tuple[float, float],
    *,
    width_mm: float,
    y0: float,
    y1: float,
) -> Solid:
    dx = end_xz[0] - start_xz[0]
    dz = end_xz[1] - start_xz[1]
    length = math.hypot(dx, dz)
    angle = -math.degrees(math.atan2(dz, dx))
    raw = Box(
        length + 0.20,
        y1 - y0,
        width_mm,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        (
            Pos(
                (start_xz[0] + end_xz[0]) / 2.0,
                (y0 + y1) / 2.0,
                (start_xz[1] + end_xz[1]) / 2.0,
            )
            * Rot(0.0, angle, 0.0)
            * raw
        ),
        feature="straight gasket-bypass path segment",
    )


def _bypass_path(*, width_mm: float, y0: float, y1: float) -> Compound:
    paths: list[Solid] = []
    for z_sign in (-1.0, 1.0):
        pieces: list[Solid] = []
        points = (
            (
                -GASKET_BYPASS_OUTER_HALF_X_MM,
                z_sign * GASKET_EXPANDED_CENTER_ABS_Z_MM,
            ),
            (
                -GASKET_BYPASS_INNER_HALF_X_MM,
                z_sign * GASKET_BYPASS_CENTER_ABS_Z_MM,
            ),
            (
                GASKET_BYPASS_INNER_HALF_X_MM,
                z_sign * GASKET_BYPASS_CENTER_ABS_Z_MM,
            ),
            (
                GASKET_BYPASS_OUTER_HALF_X_MM,
                z_sign * GASKET_EXPANDED_CENTER_ABS_Z_MM,
            ),
        )
        for start, end in zip(points, points[1:]):
            pieces.append(
                _oriented_path_segment(
                    start,
                    end,
                    width_mm=width_mm,
                    y0=y0,
                    y1=y1,
                )
            )
        for x_mm, z_mm in points[1:-1]:
            pieces.append(
                source._cylinder_between(
                    Vector(x_mm, y0, z_mm),
                    Vector(x_mm, y1, z_mm),
                    diameter=width_mm,
                )
            )
        joined: Any = copy.copy(pieces[0])
        for piece in pieces[1:]:
            joined = joined.fuse(piece)
        paths.append(
            _single_solid(
                joined.clean().fix(),
                feature=(
                    "top gasket bypass"
                    if z_sign > 0.0
                    else "bottom gasket bypass"
                ),
            )
        )

    return Compound(children=paths)


def _expanded_gasket_reference() -> Solid:
    expanded = _ring(
        outer_size=GASKET_OUTER_SIZE_MM,
        outer_radius=GASKET_OUTER_RADIUS_MM,
        inner_size=GASKET_INNER_SIZE_MM,
        inner_radius=GASKET_INNER_RADIUS_MM,
        y0=source.BAFFLE_BED_Y,
        y1=source.SHOULDER_Y,
    )
    removal_parts = []
    for z_sign in (-1.0, 1.0):
        removal_parts.append(
            Pos(
                0.0,
                (source.BAFFLE_BED_Y + source.SHOULDER_Y) / 2.0,
                z_sign * GASKET_EXPANDED_CENTER_ABS_Z_MM,
            )
            * Box(
                2.0 * GASKET_BYPASS_REMOVAL_HALF_X_MM,
                source.GASKET_CLOSED_GAP_MM + 0.20,
                18.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
        )
    trimmed: Any = expanded
    for removal in removal_parts:
        trimmed = trimmed.cut(removal)
    bypass = _bypass_path(
        width_mm=source.GASKET_TAPE_WIDTH_MM,
        y0=source.BAFFLE_BED_Y,
        y1=source.SHOULDER_Y,
    )
    return _single_solid(
        trimmed.fuse(bypass).clean().fix(),
        feature="expanded gasket with fixed-fastener bypasses",
    )


def _seal_bypass_support(*, baffle_side: bool) -> Compound:
    if baffle_side:
        y0 = source.BAFFLE_BED_Y - BAFFLE_FLANGE_THICKNESS_MM
        y1 = source.BAFFLE_BED_Y
    else:
        y0 = source.SHOULDER_Y
        y1 = source.SHOULDER_Y + SAND_CAP_THICKNESS_MM
    return _bypass_path(
        width_mm=SEAL_LAND_WIDTH_MM,
        y0=y0,
        y1=y1,
    )


def _seal_reset_ring(y0: float, y1: float) -> Solid:
    return _ring(
        outer_size=SEAL_LAND_OUTER_SIZE_MM + 2.0 * SEAL_FACE_RESET_MM,
        outer_radius=SEAL_LAND_OUTER_RADIUS_MM + SEAL_FACE_RESET_MM,
        inner_size=SEAL_LAND_INNER_SIZE_MM - 2.0 * SEAL_FACE_RESET_MM,
        inner_radius=SEAL_LAND_INNER_RADIUS_MM - SEAL_FACE_RESET_MM,
        y0=y0,
        y1=y1,
    )


def _linear_inner_wall_ramp(*, baffle_side: bool) -> Solid:
    """Straight ruled ramp with a flush, constant inner-wall boundary."""
    if baffle_side:
        face_y = source.BAFFLE_BED_Y - BAFFLE_FLANGE_THICKNESS_MM
        root_y = source.BAFFLE_BED_Y - RAMP_DEPTH_MM
    else:
        face_y = source.SHOULDER_Y
        root_y = source.SHOULDER_Y + RAMP_DEPTH_MM

    outer = source._lofted_rounded_rectangle(
        (
            (
                SEAL_LAND_INNER_SIZE_MM,
                SEAL_LAND_INNER_RADIUS_MM,
                face_y,
            ),
            (
                RAMP_ROOT_OUTER_SIZE_MM,
                RAMP_ROOT_OUTER_RADIUS_MM,
                root_y,
            ),
        ),
        feature=(
            "straight baffle seal-flange ramp"
            if baffle_side
            else "straight bucket seal-face ramp"
        ),
    )
    inner = source._rounded_rectangle_prism(
        RAMP_INNER_SIZE_MM,
        RAMP_INNER_RADIUS_MM,
        min(face_y, root_y) - 0.10,
        max(face_y, root_y) + 0.10,
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature=(
            "flush triangular baffle ramp"
            if baffle_side
            else "flush triangular bucket ramp"
        ),
    )


def _front_sand_cap() -> Solid:
    live_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    expanded_void = _single_solid(
        live_void.offset_3d([], SAND_CAP_SKIN_EMBED_MM).clean().fix(),
        feature="skin-embedded live sand-void envelope",
    )
    slab = Pos(
        0.0,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        SAND_CAP_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        expanded_void.intersect(slab).clean().fix(),
        feature="three-millimeter front sand-void closure cap",
    )


def _continuous_bucket_seal_plate() -> Solid:
    """Planar wall-stack plate supporting every millimeter of gasket tape."""
    return _ring(
        outer_size=SEAL_LAND_OUTER_SIZE_MM,
        outer_radius=SEAL_LAND_OUTER_RADIUS_MM,
        inner_size=SEAL_LAND_INNER_SIZE_MM,
        inner_radius=SEAL_LAND_INNER_RADIUS_MM,
        y0=source.SHOULDER_Y,
        y1=source.SHOULDER_Y + SAND_CAP_THICKNESS_MM,
    )


def _front_fill_transition(
    *,
    x_mm: float,
    outer: bool,
) -> Solid:
    mouth_radius = base.P.fill_entry_d / 2.0
    void_radius = base.P.void_t / 2.0
    if outer:
        mouth_radius += FRONT_FILL_SUPPORT_WALL_MM
        void_radius += FRONT_FILL_SUPPORT_WALL_MM

    start_y = (
        source.SHOULDER_Y
        + SAND_CAP_THICKNESS_MM
        - FRONT_FILL_CAP_OVERLAP_MM
    )
    end_y = start_y + FRONT_FILL_TRANSITION_LENGTH_MM
    void_center_z = (
        base.P.cube_outer / 2.0
        - base.P.outer_skin_t
        - base.P.void_t / 2.0
    )
    with BuildPart() as transition:
        for section_index in range(FRONT_FILL_SECTION_COUNT):
            t = section_index / (FRONT_FILL_SECTION_COUNT - 1)
            blend = t * t * (3.0 - 2.0 * t)
            section_y = start_y + FRONT_FILL_TRANSITION_LENGTH_MM * t
            section_z = FRONT_FILL_Z_MM + (
                void_center_z - FRONT_FILL_Z_MM
            ) * blend
            section_radius = mouth_radius + (
                void_radius - mouth_radius
            ) * blend
            plane = Plane(
                origin=(x_mm, section_y, section_z),
                x_dir=(1.0, 0.0, 0.0),
                z_dir=(0.0, -1.0, 0.0),
            )
            with BuildSketch(plane) as section:
                Circle(section_radius)
            if section.sketch.area <= 0.0:
                raise ValueError("Front fill transition section has no area")
        loft()
    return _single_solid(
        transition.part.clean().fix(),
        feature=(
            "front fill support transition"
            if outer
            else "front fill void transition"
        ),
    )


def _front_fill_feature(x_mm: float) -> dict[str, Solid | float]:
    entry_start = source.SHOULDER_Y - FRONT_FILL_MOUTH_OVERTRAVEL_MM
    entry_end = (
        source.SHOULDER_Y
        + SAND_CAP_THICKNESS_MM
        + FRONT_FILL_CAP_OVERLAP_MM
    )
    entry = source._cylinder_between(
        Vector(x_mm, entry_start, FRONT_FILL_Z_MM),
        Vector(x_mm, entry_end, FRONT_FILL_Z_MM),
        diameter=base.P.fill_entry_d,
    )
    outer_entry = source._cylinder_between(
        Vector(x_mm, source.SHOULDER_Y, FRONT_FILL_Z_MM),
        Vector(x_mm, entry_end, FRONT_FILL_Z_MM),
        diameter=(
            base.P.fill_entry_d + 2.0 * FRONT_FILL_SUPPORT_WALL_MM
        ),
    )
    transition = _front_fill_transition(x_mm=x_mm, outer=False)
    outer_transition = _front_fill_transition(x_mm=x_mm, outer=True)
    passage = _single_solid(
        entry.fuse(transition).clean().fix(),
        feature="unified concealed front sand-fill passage",
    )
    support = _single_solid(
        outer_entry
        .fuse(outer_transition)
        .cut(passage)
        .clean()
        .fix(),
        feature="printable concealed front sand-fill blister",
    )
    live_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    passage_to_void = _shape_volume(passage.intersect(live_void))
    slope = math.degrees(
        math.atan2(
            abs(
                base.P.cube_outer / 2.0
                - base.P.outer_skin_t
                - base.P.void_t / 2.0
                - FRONT_FILL_Z_MM
            ),
            FRONT_FILL_TRANSITION_LENGTH_MM,
        )
    )
    return {
        "passage": passage,
        "support": support,
        "passage_to_void_mm3": passage_to_void,
        "centerline_slope_from_print_axis_deg": slope,
    }


def _solid_rear_without_fill_ports(
    port_clearance: Any,
    port_install_clearance: Any,
    *,
    include_gx16: bool = True,
    include_fill_ports: bool = True,
) -> Any:
    """Preserve the GX opening but make the rear wall solid at both fill ports."""
    del include_fill_ports
    filled = _single_solid(
        ORIGINAL_SOLID_REAR_DETAIL_BASE(
            port_clearance,
            port_install_clearance,
            include_gx16=include_gx16,
            include_fill_ports=False,
        ),
        feature="solid-rear enclosure without inherited fill blisters",
    )
    # The conformal shell's native blank is cut by both rear bores before its
    # include_fill_ports switch.  Restore those exact cylindrical volumes here
    # so the exported rear face is physically solid, not just blister-free.
    for fill_x in (-base.P.fill_port_x, base.P.fill_port_x):
        filled = _fuse_one(
            filled,
            base._sand_fill_rear_bore(fill_x),
            feature="solid rear wall with former fill bore restored",
        )
    return filled


def _perimeter_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="front-fill nested-seam baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="front-fill rear-bed bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    bucket = _cut_one(
        bucket,
        _seal_reset_ring(
            source.BAFFLE_BED_Y - 0.25,
            source.SHOULDER_Y + 0.15,
        ),
        feature="bucket with expanded seal compression gap reset",
    )
    bucket = _cut_one(
        bucket,
        _bypass_path(
            width_mm=SEAL_LAND_WIDTH_MM + 2.0 * SEAL_FACE_RESET_MM,
            y0=source.BAFFLE_BED_Y - 0.25,
            y1=source.SHOULDER_Y + 0.15,
        ),
        feature="bucket with fixed-fastener bypass gap reset",
    )
    baffle = _cut_one(
        baffle,
        _seal_reset_ring(
            source.BAFFLE_BED_Y - BAFFLE_FLANGE_THICKNESS_MM - 0.10,
            source.BAFFLE_BED_Y + 0.16,
        ),
        feature="baffle with expanded planar seal face reset",
    )
    cap = _front_sand_cap()
    bucket = _fuse_one(
        bucket,
        cap,
        feature="bucket with permanently capped front sand gap",
    )
    seal_plate = _continuous_bucket_seal_plate()
    bucket = _fuse_one(
        bucket,
        seal_plate,
        feature="bucket with continuous three-millimeter gasket plate",
    )
    bucket_bypass_support = _seal_bypass_support(baffle_side=False)
    bucket = _fuse_one(
        bucket,
        bucket_bypass_support,
        feature="bucket with fixed-fastener gasket-bypass support",
    )
    bucket_ramp = _linear_inner_wall_ramp(baffle_side=False)
    bucket = _fuse_one(
        bucket,
        bucket_ramp,
        feature="bucket with flush triangular seal-face ramp",
    )

    fill_passages: list[Solid] = []
    fill_supports: list[Solid] = []
    fill_audits: dict[str, Any] = {}
    gasket = _expanded_gasket_reference()
    for x_mm, label in ((-FRONT_FILL_X_MM, "left"), (FRONT_FILL_X_MM, "right")):
        fill = _front_fill_feature(x_mm)
        passage = fill["passage"]
        support = fill["support"]
        assert isinstance(passage, Solid)
        assert isinstance(support, Solid)
        support_root = _shape_volume(support.intersect(bucket))
        if support_root < MINIMUM_FILL_SUPPORT_ROOT_MM3:
            raise ValueError(
                f"The {label} front-fill blister lacks a bucket root: "
                f"{support_root:.6f} mm3"
            )
        bucket = _fuse_one(
            bucket,
            support,
            feature=f"bucket with printable {label} front-fill blister",
        )
        bucket = _cut_one(
            bucket,
            passage,
            feature=f"bucket with concealed {label} front-fill passage",
        )
        gasket_overlap = _shape_volume(passage.intersect(gasket))
        if gasket_overlap > 0.001:
            raise ValueError(
                f"The {label} front-fill passage interrupts the gasket by "
                f"{gasket_overlap:.6f} mm3"
            )
        passage_to_void = float(fill["passage_to_void_mm3"])
        if passage_to_void <= 0.01:
            raise ValueError(
                f"The {label} front-fill passage does not reach the sand void"
            )
        fill_passages.append(passage)
        fill_supports.append(support)
        fill_audits[label] = {
            "mouth_center_mm": [x_mm, source.SHOULDER_Y, FRONT_FILL_Z_MM],
            "entry_diameter_mm": base.P.fill_entry_d,
            "support_wall_mm": FRONT_FILL_SUPPORT_WALL_MM,
            "passage_to_live_sand_void_mm3": passage_to_void,
            "support_root_mm3": support_root,
            "gasket_overlap_mm3": gasket_overlap,
            "centerline_slope_from_print_axis_deg": float(
                fill["centerline_slope_from_print_axis_deg"]
            ),
        }

    bed_slab = Pos(
        0.0,
        source.BAFFLE_BED_Y - BAFFLE_FLANGE_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        BAFFLE_FLANGE_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    flange_outer = _single_solid(
        nominal.intersect(bed_slab).clean().fix(),
        feature="exact-perimeter baffle-bed flange blank",
    )
    flange_inner = source._rounded_rectangle_prism(
        SEAL_LAND_INNER_SIZE_MM,
        SEAL_LAND_INNER_RADIUS_MM,
        source.BAFFLE_BED_Y - BAFFLE_FLANGE_THICKNESS_MM - 0.10,
        source.BAFFLE_BED_Y + 0.10,
    )
    flange = _single_solid(
        flange_outer.cut(flange_inner).clean().fix(),
        feature="exact-perimeter hollow baffle seal flange",
    )
    baffle = _fuse_one(
        baffle,
        flange,
        feature="baffle with perimeter-connected seal flange",
    )
    baffle_bypass_support = _seal_bypass_support(baffle_side=True)
    baffle = _fuse_one(
        baffle,
        baffle_bypass_support,
        feature="baffle with fixed-fastener gasket-bypass support",
    )
    baffle_ramp = _linear_inner_wall_ramp(baffle_side=True)
    baffle_ramp = _single_solid(
        baffle_ramp.intersect(nominal).clean().fix(),
        feature="envelope-clipped straight baffle flange ramp",
    )
    baffle = _fuse_one(
        baffle,
        baffle_ramp,
        feature="baffle with hollow straight seal-flange taper",
    )

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(
        bucket_baffle_overlap,
        gasket_bucket_overlap,
        gasket_baffle_overlap,
    ) > 0.01:
        raise ValueError(
            "Front-fill common-joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3"
        )

    gasket_audit = _ring(
        outer_size=GASKET_OUTER_SIZE_MM,
        outer_radius=GASKET_OUTER_RADIUS_MM,
        inner_size=GASKET_INNER_SIZE_MM,
        inner_radius=GASKET_INNER_RADIUS_MM,
        y0=source.SHOULDER_Y,
        y1=source.SHOULDER_Y + 0.25,
    )
    gasket_support_ratio = _shape_volume(
        gasket_audit.intersect(bucket)
    ) / gasket_audit.volume
    if gasket_support_ratio < MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            "Expanded gasket lacks continuous bucket support: "
            f"ratio={gasket_support_ratio:.6f}"
        )

    open_gap = _ring(
        outer_size=GASKET_OUTER_SIZE_MM,
        outer_radius=GASKET_OUTER_RADIUS_MM,
        inner_size=GASKET_INNER_SIZE_MM,
        inner_radius=GASKET_INNER_RADIUS_MM,
        y0=source.BAFFLE_BED_Y + 0.05,
        y1=source.SHOULDER_Y - 0.05,
    )
    hard_gap_intrusion = _shape_volume(
        open_gap.intersect(Compound(children=[bucket, baffle]))
    )
    if hard_gap_intrusion > 0.001:
        raise ValueError(
            "A hard feature interrupts the enlarged gasket gap by "
            f"{hard_gap_intrusion:.6f} mm3"
        )

    target_area = parent._build_parabolic_conformal_geometry()[
        "outer_fairing_area_mm2"
    ]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("The expanded common joint changed the G1 fairing")

    live_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    cap_target_slab = Pos(
        0.0,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        SAND_CAP_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    cap_target = live_void.intersect(cap_target_slab)
    intentional_passages = Compound(children=fill_passages)
    unclosed_cap = cap_target.cut(bucket.fuse(intentional_passages))
    unclosed_cap_mm3 = _shape_volume(unclosed_cap)
    if unclosed_cap_mm3 > 0.05:
        raise ValueError(
            "The front sand cap left an unintended opening of "
            f"{unclosed_cap_mm3:.6f} mm3"
        )

    ramp_angle = math.degrees(
        math.atan2(
            (
                SEAL_LAND_INNER_SIZE_MM
                - RAMP_ROOT_OUTER_SIZE_MM
            ) / 2.0,
            RAMP_DEPTH_MM - BAFFLE_FLANGE_THICKNESS_MM,
        )
    )
    fill_clearance = (
        GASKET_INNER_SIZE_MM / 2.0
        - FRONT_FILL_Z_MM
        - base.P.fill_entry_d / 2.0
    )
    if fill_clearance < MINIMUM_FILL_TO_GASKET_CLEARANCE_MM:
        raise ValueError(
            "Front fill mouths are too close to the gasket: "
            f"{fill_clearance:.6f} mm"
        )

    _FRONT_FILL_AUDIT.clear()
    _FRONT_FILL_AUDIT.update(fill_audits)
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "upper_hook_count": 0,
            "hook_receiver_count": 0,
            "installation_motion": "straight-on nested socket insertion",
            "structural_flange_outer_size_mm": SEAL_LAND_OUTER_SIZE_MM,
            "structural_flange_inner_size_mm": SEAL_LAND_INNER_SIZE_MM,
            "flat_seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "specified_gasket_width_mm": source.GASKET_TAPE_WIDTH_MM,
            "gasket_outer_size_mm": GASKET_OUTER_SIZE_MM,
            "gasket_inner_size_mm": GASKET_INNER_SIZE_MM,
            "gasket_edge_margin_each_side_mm": GASKET_EDGE_MARGIN_MM,
            "gasket_fixed_fastener_bypass_count": 2,
            "gasket_bypass_inner_half_width_mm": (
                GASKET_BYPASS_INNER_HALF_X_MM
            ),
            "gasket_bypass_center_abs_z_mm": (
                GASKET_BYPASS_CENTER_ABS_Z_MM
            ),
            "gasket_bucket_support_ratio": gasket_support_ratio,
            "seal_gap_hard_part_intrusion_mm3": hard_gap_intrusion,
            "sand_cap_thickness_mm": SAND_CAP_THICKNESS_MM,
            "unclosed_non_fill_sand_gap_mm3": unclosed_cap_mm3,
            "straight_ramp_root_width_mm": RAMP_ROOT_WIDTH_MM,
            "straight_ramp_depth_mm": RAMP_DEPTH_MM,
            "straight_ramp_from_print_axis_deg": ramp_angle,
            "straight_ramp_support_free_under_45_deg": ramp_angle <= 45.0,
            "inner_ramp_face_flush_with_inner_wall": True,
            "rounded_inner_lip_removed": True,
            "rear_fill_port_count": 0,
            "front_hidden_fill_port_count": 2,
            "minimum_fill_mouth_to_gasket_clearance_mm": fill_clearance,
        }
    )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": Compound(
            children=[
                cap,
                seal_plate,
                bucket_bypass_support,
                bucket_ramp,
                baffle_ramp,
                flange,
                baffle_bypass_support,
            ]
        ),
        "nominal_envelope": nominal,
        "clearance_envelope": clearance,
        "reference_bucket": reference_bucket,
        "reference_baffle": reference_baffle,
        "fairing_area_mm2": fairing_faces[0].area,
        "fairing_area_difference_mm2": fairing_faces[0].area - target_area,
        "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket_overlap,
        "gasket_baffle_overlap_mm3": gasket_baffle_overlap,
        "front_fill_passages": Compound(children=fill_passages),
        "front_fill_supports": Compound(children=fill_supports),
    }


def _load_web(z_sign: float, nominal_envelope: Solid) -> Solid:
    plane = Plane(
        origin=(0.0, 0.0, 0.0),
        x_dir=(0.0, 1.0, 0.0),
        z_dir=(1.0, 0.0, 0.0),
    )
    with BuildPart() as web:
        with BuildSketch(plane):
            Polygon(
                (
                    source.BAFFLE_BED_Y,
                    z_sign * LOAD_WEB_BASE_INNER_Z_MM,
                ),
                (
                    source.BAFFLE_BED_Y,
                    z_sign * LOAD_WEB_BASE_OUTER_Z_MM,
                ),
                (
                    LOAD_WEB_FRONT_Y_MM,
                    z_sign * LOAD_WEB_TIP_Z_MM,
                ),
            )
        extrude(amount=LOAD_WEB_WIDTH_X_MM / 2.0, both=True)
    placed = Pos(
        0.0,
        (source.BAFFLE_BED_Y + LOAD_WEB_FRONT_Y_MM) / 2.0,
        z_sign
        * (LOAD_WEB_BASE_INNER_Z_MM + LOAD_WEB_BASE_OUTER_Z_MM)
        / 2.0,
    ) * web.part
    clipped = placed.intersect(nominal_envelope).clean().fix()
    return _single_solid(clipped, feature="envelope-clipped nut load web")


def _reinforced_dual_concept(common: dict[str, Any]) -> dict[str, Any]:
    concept = ORIGINAL_DUAL_CONCEPT(common)
    baffle = copy.copy(concept["baffle"])
    webs: list[Solid] = []
    web_roots: dict[str, float] = {}
    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        raw_web = _load_web(z_sign, common["nominal_envelope"])
        root = _shape_volume(raw_web.intersect(baffle))
        if root <= 0.01:
            raise ValueError(f"The {label} nut load web has no baffle root")
        cut_web = raw_web.cut(concept["cutters"]).clean().fix()
        web_solids = sorted(
            cut_web.solids(), key=lambda solid: solid.volume, reverse=True
        )
        if not web_solids:
            raise ValueError(f"The {label} load web was consumed by clearances")
        retained_web_solids: list[Solid] = []
        pending = [copy.copy(solid) for solid in web_solids]
        while pending:
            added_this_pass = False
            next_pending: list[Solid] = []
            for web_solid in pending:
                if _shape_volume(web_solid.intersect(baffle)) > 0.01:
                    baffle = _fuse_one(
                        baffle,
                        web_solid,
                        feature=(
                            f"baffle with continuous {label} "
                            "seal-to-collar load web"
                        ),
                    )
                    retained_web_solids.append(web_solid)
                    added_this_pass = True
                else:
                    next_pending.append(web_solid)
            if not added_this_pass:
                break
            pending = next_pending
        if not retained_web_solids:
            raise ValueError(
                f"No clearance-cut {label} load-web solid joins the baffle"
            )
        webs.extend(retained_web_solids)
        web_roots[label] = root

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("The reinforced load webs changed the G1 fairing")

    gasket_overlap = _shape_volume(baffle.intersect(common["gasket"]))
    if gasket_overlap > 0.01:
        raise ValueError(
            "Reinforced baffle interrupts the gasket by "
            f"{gasket_overlap:.6f} mm3"
        )
    hardware_overlap = _shape_volume(
        baffle.intersect(concept["clearance_hardware"])
    )
    if hardware_overlap > 0.01:
        raise ValueError(
            "Reinforced baffle collides with closure hardware by "
            f"{hardware_overlap:.6f} mm3"
        )

    concept["baffle"] = baffle
    concept["nut_load_pad"] = Compound(
        children=[concept["nut_load_pad"], *webs]
    )
    concept["description"] = (
        "Unchanged mirrored captive-square-nut fasteners carried by "
        "perimeter-connected printable baffle webs"
    )
    concept["geometry"].update(
        {
            "screw_structure_coordinates_unchanged": True,
            "seal_to_collar_load_web_count": 2,
            "load_web_width_x_mm": LOAD_WEB_WIDTH_X_MM,
            "load_web_front_y_mm": LOAD_WEB_FRONT_Y_MM,
            "load_web_roots_mm3": web_roots,
            "load_web_gasket_overlap_mm3": gasket_overlap,
            "load_web_hardware_overlap_mm3": hardware_overlap,
            "front_fill_ports": dict(_FRONT_FILL_AUDIT),
        }
    )
    return concept


def _update_fill_port_contract(diagnostics: dict[str, Any]) -> None:
    """Replace inherited rear-fill metadata with the modeled front service."""
    diagnostics["enclosure"]["restored_original_features"][
        "sand_fill_ports"
    ] = {
        "count": 0,
        "rear_entries_removed": True,
        "rear_wall_is_solid": True,
        "replacement_front_hidden_entries": {
            "count": 2,
            "mouth_centers_xz_mm": [
                [-FRONT_FILL_X_MM, FRONT_FILL_Z_MM],
                [FRONT_FILL_X_MM, FRONT_FILL_Z_MM],
            ],
            "entry_diameter_mm": base.P.fill_entry_d,
            "transition_length_mm": FRONT_FILL_TRANSITION_LENGTH_MM,
            "support_wall_mm": FRONT_FILL_SUPPORT_WALL_MM,
            "concealed_by_installed_baffle": True,
        },
    }
    diagnostics["enclosure"]["construction"] = (
        "The established 190 x 210 x 190 enclosure, centered black-hole "
        "face, GX16, solid floor, 2-3-2 walls, and port-relieved brace "
        "network are retained.  The rear sand-fill entries are closed and "
        "replaced by two baffle-hidden front entries through a capped wall "
        "stack."
    )


def generate() -> dict[str, Any]:
    original_out = prior.OUT
    original_name = prior.NAME
    original_common_joint = prior._hook_free_common_joint
    original_concept = prior._dual_captive_square_nut_concept
    original_solid_rear = source.prior._solid_rear_detail_base

    prior.OUT = OUT
    prior.NAME = NAME
    prior._hook_free_common_joint = _perimeter_common_joint
    prior._dual_captive_square_nut_concept = _reinforced_dual_concept
    source.prior._solid_rear_detail_base = _solid_rear_without_fill_ports
    try:
        diagnostics = prior.generate()
    finally:
        prior.OUT = original_out
        prior.NAME = original_name
        prior._hook_free_common_joint = original_common_joint
        prior._dual_captive_square_nut_concept = original_concept
        source.prior._solid_rear_detail_base = original_solid_rear

    closure_diagnostics = diagnostics.pop("dual_captive_square_nut_closure")
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["front_fill"] = dict(_FRONT_FILL_AUDIT)

    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete front-fill perimeter-sealed dual captive-square-nut closure"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_front_fill_perimeter_seal"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_front_fill_perimeter_seal"
        ),
        "dual_captive_square_nut_parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["front_fill_perimeter_seal_closure"] = closure_diagnostics
    _update_fill_port_contract(diagnostics)
    diagnostics["preserved_full_detail_contract"].update(
        {
            "sand_fill_ports_and_internal_blisters": 0,
            "rear_sand_fill_ports": 0,
            "front_hidden_sand_fill_ports": 2,
            "solid_rear_wall": True,
            "gx16_rear_opening_preserved": True,
        }
    )
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
