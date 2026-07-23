"""Generate the simplified printable two-piece parabolic G1 enclosure.

This isolated sibling deliberately removes the accumulated closure geometry.
It keeps the authoritative exterior and complete rear-corner system while
using one narrow gasket land, two unobstructed corner fill passages, two local
dry-side screw supports, two compact baffle nut wedges, and support-free brace
ramps for rear-face-down bucket printing.
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
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Edge,
    Plane,
    Polygon,
    Pos,
    Rot,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    extrude,
    import_step,
    loft,
    sweep,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_front_fill_perimeter_seal"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_front_fill_perimeter_seal as prior  # noqa: E402


source = prior.source
closure = prior.closure
base = prior.base
parent = prior.parent
dual = prior.prior
centered = dual.previous.prior

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simplified_printable_closure"
)
NAME = "sand_cube_190x210_parabolic_g1_simplified_printable_closure"

# One 6.75 mm land carries the 5 x 2 mm tape with 0.875 mm placement margin
# on both sides.  Only the two upper corners deviate from the rounded square,
# and each deviation is a single smooth fill-mouth bay.
PATH_HALF_SIZE_MM = 88.125
PATH_TOP_CORNER_TANGENCY_MM = 68.0
PATH_TOP_CORNER_CONTROL_MM = 71.0
PATH_BOTTOM_CORNER_TANGENCY_MM = 73.0
SEAL_LAND_WIDTH_MM = 6.75
GASKET_WIDTH_MM = source.GASKET_TAPE_WIDTH_MM
GASKET_EDGE_MARGIN_MM = (SEAL_LAND_WIDTH_MM - GASKET_WIDTH_MM) / 2.0
SEAL_RESET_MARGIN_MM = 0.45
SAND_CAP_THICKNESS_MM = prior.SAND_CAP_THICKNESS_MM
BAFFLE_LAND_THICKNESS_MM = source.BAFFLE_LAND_THICKNESS_MM

# The fill mouths move far enough inward to expose their complete 9.15 mm
# bores with the baffle installed.  Their hollow 1.2 mm support shells blend
# into the live 3 mm sand gap over a support-free 14 mm print rise.
FRONT_FILL_ABS_XZ_MM = 86.0
FRONT_FILL_TRANSITION_LENGTH_MM = 14.0
FRONT_FILL_SUPPORT_WALL_MM = 1.2
FRONT_FILL_VOID_OVERLAP_MM = 0.15
FRONT_FILL_CAP_OVERLAP_MM = 0.50
FRONT_FILL_MOUTH_OVERTRAVEL_MM = 0.30
FRONT_FILL_SECTION_COUNT = 9
WALL_CORNER_CENTER_MM = base.P.cube_outer / 2.0 - base.P.outer_skin_t - 6.0
SAND_CORNER_CENTERLINE_RADIUS_MM = (6.0 + base.P.void_t) / 2.0
SAND_CORNER_TARGET_ABS_XZ_MM = (
    WALL_CORNER_CENTER_MM
    + SAND_CORNER_CENTERLINE_RADIUS_MM / math.sqrt(2.0)
)

# Two identical top/bottom M4 closures.  The head is rearward on the exterior
# top/bottom face, while the 35 degree forward lean reaches a square nut well
# inside the gasket loop.  No printed boss crosses the assembly gap.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -64.0
FASTENER_SURFACE_ABS_Z_MM = 95.0
FASTENER_FORWARD_ANGLE_DEG = 35.0
NUT_AXIS_DISTANCE_MM = 22.0
SCREW_NOMINAL_D_MM = 4.0
SCREW_CLEARANCE_D_MM = 4.5
SCREW_HEAD_D_MM = 8.5
SCREW_HEAD_THICKNESS_MM = 2.4
SCREW_HEAD_AXIS_START_MM = 2.2
HEAD_CUBBY_D_MM = 9.2
HEAD_CUBBY_AXIS_END_MM = 5.0
BUCKET_BOSS_D_MM = 12.0
BUCKET_BOSS_AXIS_START_MM = 0.5
BUCKET_BOSS_AXIS_END_MM = 3.5
SQUARE_NUT_WIDTH_MM = 7.0
SQUARE_NUT_THICKNESS_MM = 3.2
SQUARE_NUT_POCKET_WIDTH_MM = 7.55
SQUARE_NUT_POCKET_THICKNESS_MM = 3.65
NUT_SLOT_WIDTH_X_MM = 7.70
NUT_SLOT_THICKNESS_MM = 3.80
NUT_SLOT_SEAT_OVERTRAVEL_MM = 0.35
NUT_SLOT_MOUTH_OVERTRAVEL_MM = 0.80

# The baffle print bed is shared by the collar and outer seal land.  Four
# short, 3 mm thick cardinal bridges join those bed-contacting structures.
BAFFLE_CARDINAL_WEB_THICKNESS_MM = 3.0
BAFFLE_CARDINAL_WEB_TANGENTIAL_MM = 26.0
BAFFLE_CARDINAL_WEB_RADIAL_INNER_MM = 77.0
BAFFLE_CARDINAL_WEB_RADIAL_OUTER_MM = 87.0
NUT_WEDGE_WIDTH_X_MM = 15.0

# Rear-face-down print ramps for the braces.
BRACE_RAMP_LENGTH_MM = 10.0

FAIRING_AREA_TOLERANCE_MM2 = 1e-5
MAX_ALLOWED_INTERFERENCE_MM3 = 0.01
MINIMUM_GASKET_SUPPORT_RATIO = 0.985
MINIMUM_FILL_CLEARANCE_MM = 0.50

_JOINT_AUDIT: dict[str, Any] = {}
_FILL_AUDIT: dict[str, Any] = {}
_BRACE_AUDIT: dict[str, Any] = {}

ORIGINAL_RESTORED_INTERNAL_BRACES = base._restored_internal_braces
ORIGINAL_SOLID_REAR_DETAIL_BASE = source.prior._solid_rear_detail_base


def _shape_volume(shape: Any) -> float:
    return prior._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return prior._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return prior._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return prior._fuse_one(shape, addition, feature=feature)


def _p(x_mm: float, y_mm: float, z_mm: float) -> tuple[float, float, float]:
    return (x_mm, y_mm, z_mm)


def _seal_centerline_wire(y_mm: float = 0.0) -> Wire:
    """Rounded square with one G2 bay around each upper fill mouth."""
    h = PATH_HALF_SIZE_MM
    tc = PATH_TOP_CORNER_TANGENCY_MM
    tp = PATH_TOP_CORNER_CONTROL_MM
    bc = PATH_BOTTOM_CORNER_TANGENCY_MM
    br = h - bc
    bd = br / math.sqrt(2.0)
    p = lambda x, z: _p(x, y_mm, z)
    edges = [
        Edge.make_line(p(-tc, h), p(tc, h)),
        Edge.make_bezier(
            p(tc, h),
            p(tc + 0.2, h),
            p(tp, h),
            p(h, tp),
            p(h, tc + 0.2),
            p(h, tc),
        ),
        Edge.make_line(p(h, tc), p(h, -bc)),
        Edge.make_three_point_arc(
            p(h, -bc),
            p(bc + bd, -bc - bd),
            p(bc, -h),
        ),
        Edge.make_line(p(bc, -h), p(-bc, -h)),
        Edge.make_three_point_arc(
            p(-bc, -h),
            p(-bc - bd, -bc - bd),
            p(-h, -bc),
        ),
        Edge.make_line(p(-h, -bc), p(-h, tc)),
        Edge.make_bezier(
            p(-h, tc),
            p(-h, tc + 0.2),
            p(-h, tp),
            p(-tp, h),
            p(-tc - 0.2, h),
            p(-tc, h),
        ),
    ]
    wires = Wire.combine(edges)
    if len(wires) != 1 or not wires[0].is_closed:
        raise ValueError("Simplified gasket centerline did not close")
    return wires[0]


def _band_solid(
    width_mm: float,
    y0_mm: float,
    y1_mm: float,
    *,
    feature: str,
) -> Solid:
    """Robust exact-width band made from segment sweeps and round joints."""
    centerline = _seal_centerline_wire(y0_mm)
    depth = y1_mm - y0_mm
    if depth <= 0.0:
        raise ValueError(f"{feature} must have positive depth")
    pieces: list[Solid] = []
    for edge_index, edge in enumerate(centerline.edges(), start=1):
        start = edge.position_at(0.0)
        tangent = edge.tangent_at(0.0)
        section_plane = Plane(
            origin=start + Vector(0.0, depth / 2.0, 0.0),
            x_dir=(0.0, 1.0, 0.0),
            z_dir=tangent,
        )
        with BuildSketch(section_plane) as section:
            from build123d import Rectangle

            Rectangle(depth, width_mm, align=(Align.CENTER, Align.CENTER))
        swept = sweep(
            section.sketch.faces()[0],
            path=edge,
            is_frenet=False,
        ).clean().fix()
        solids = swept.solids()
        if len(solids) != 1 or not solids[0].is_valid:
            raise ValueError(f"{feature} segment {edge_index} is invalid")
        pieces.append(solids[0])
    for vertex in centerline.vertices():
        point = vertex.center()
        pieces.append(
            source._cylinder_between(
                Vector(point.X, y0_mm, point.Z),
                Vector(point.X, y1_mm, point.Z),
                diameter=width_mm,
            )
        )
    return _single_solid(
        pieces[0].fuse(*pieces[1:]).clean().fix(),
        feature=feature,
    )


def _broad_interface_reset(y0_mm: float, y1_mm: float) -> Solid:
    outer = source._rounded_rectangle_prism(
        184.3,
        7.0,
        y0_mm,
        y1_mm,
    )
    inner = source._rounded_rectangle_prism(
        153.5,
        3.5,
        min(y0_mm, y1_mm) - 0.10,
        max(y0_mm, y1_mm) + 0.10,
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="broad hidden-interface cleanup",
    )


def _front_fill_transition(*, x_sign: float, outer: bool) -> Solid:
    mouth_radius = base.P.fill_entry_d / 2.0
    void_radius = base.P.void_t / 2.0 + FRONT_FILL_VOID_OVERLAP_MM
    if outer:
        mouth_radius += FRONT_FILL_SUPPORT_WALL_MM
        void_radius += FRONT_FILL_SUPPORT_WALL_MM
    start_y = (
        source.SHOULDER_Y
        + SAND_CAP_THICKNESS_MM
        - FRONT_FILL_CAP_OVERLAP_MM
    )
    mouth_x = x_sign * FRONT_FILL_ABS_XZ_MM
    target_x = x_sign * SAND_CORNER_TARGET_ABS_XZ_MM
    with BuildPart() as transition:
        for index in range(FRONT_FILL_SECTION_COUNT):
            t = index / (FRONT_FILL_SECTION_COUNT - 1)
            blend = t * t * (3.0 - 2.0 * t)
            section_y = start_y + FRONT_FILL_TRANSITION_LENGTH_MM * t
            section_x = mouth_x + (target_x - mouth_x) * blend
            section_z = FRONT_FILL_ABS_XZ_MM + (
                SAND_CORNER_TARGET_ABS_XZ_MM - FRONT_FILL_ABS_XZ_MM
            ) * blend
            radius = mouth_radius + (void_radius - mouth_radius) * blend
            plane = Plane(
                origin=(section_x, section_y, section_z),
                x_dir=(1.0, 0.0, 0.0),
                z_dir=(0.0, -1.0, 0.0),
            )
            with BuildSketch(plane) as section:
                Circle(radius)
            if section.sketch.area <= 0.0:
                raise ValueError("Fill transition section has no area")
        loft()
    return _single_solid(
        transition.part.clean().fix(),
        feature=("fill support transition" if outer else "fill passage transition"),
    )


def _front_fill_feature(x_sign: float) -> dict[str, Any]:
    mouth_x = x_sign * FRONT_FILL_ABS_XZ_MM
    entry_start = source.SHOULDER_Y - FRONT_FILL_MOUTH_OVERTRAVEL_MM
    entry_end = (
        source.SHOULDER_Y
        + SAND_CAP_THICKNESS_MM
        + FRONT_FILL_CAP_OVERLAP_MM
    )
    entry = source._cylinder_between(
        Vector(mouth_x, entry_start, FRONT_FILL_ABS_XZ_MM),
        Vector(mouth_x, entry_end, FRONT_FILL_ABS_XZ_MM),
        diameter=base.P.fill_entry_d,
    )
    outer_entry = source._cylinder_between(
        Vector(mouth_x, source.SHOULDER_Y, FRONT_FILL_ABS_XZ_MM),
        Vector(mouth_x, entry_end, FRONT_FILL_ABS_XZ_MM),
        diameter=base.P.fill_entry_d + 2.0 * FRONT_FILL_SUPPORT_WALL_MM,
    )
    passage = _single_solid(
        entry.fuse(_front_fill_transition(x_sign=x_sign, outer=False)).clean().fix(),
        feature="unified corner fill passage",
    )
    support = _single_solid(
        outer_entry
        .fuse(_front_fill_transition(x_sign=x_sign, outer=True))
        .cut(passage)
        .clean()
        .fix(),
        feature="hollow corner fill support",
    )
    live_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    travel = math.hypot(
        SAND_CORNER_TARGET_ABS_XZ_MM - FRONT_FILL_ABS_XZ_MM,
        SAND_CORNER_TARGET_ABS_XZ_MM - FRONT_FILL_ABS_XZ_MM,
    )
    return {
        "passage": passage,
        "support": support,
        "passage_to_void_mm3": _shape_volume(passage.intersect(live_void)),
        "slope_deg": math.degrees(
            math.atan2(travel, FRONT_FILL_TRANSITION_LENGTH_MM)
        ),
    }


def _baffle_cardinal_webs(nominal_envelope: Solid) -> list[Solid]:
    y0 = source.BAFFLE_BED_Y - BAFFLE_CARDINAL_WEB_THICKNESS_MM
    y_mid = (y0 + source.BAFFLE_BED_Y) / 2.0
    radial_span = (
        BAFFLE_CARDINAL_WEB_RADIAL_OUTER_MM
        - BAFFLE_CARDINAL_WEB_RADIAL_INNER_MM
    )
    radial_mid = (
        BAFFLE_CARDINAL_WEB_RADIAL_OUTER_MM
        + BAFFLE_CARDINAL_WEB_RADIAL_INNER_MM
    ) / 2.0
    raw = [
        Pos(0.0, y_mid, radial_mid) * Box(
            BAFFLE_CARDINAL_WEB_TANGENTIAL_MM,
            BAFFLE_CARDINAL_WEB_THICKNESS_MM,
            radial_span,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
        Pos(0.0, y_mid, -radial_mid) * Box(
            BAFFLE_CARDINAL_WEB_TANGENTIAL_MM,
            BAFFLE_CARDINAL_WEB_THICKNESS_MM,
            radial_span,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
        Pos(radial_mid, y_mid, 0.0) * Box(
            radial_span,
            BAFFLE_CARDINAL_WEB_THICKNESS_MM,
            BAFFLE_CARDINAL_WEB_TANGENTIAL_MM,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
        Pos(-radial_mid, y_mid, 0.0) * Box(
            radial_span,
            BAFFLE_CARDINAL_WEB_THICKNESS_MM,
            BAFFLE_CARDINAL_WEB_TANGENTIAL_MM,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
    ]
    webs: list[Solid] = []
    for index, web in enumerate(raw, start=1):
        webs.append(
            _single_solid(
                web.intersect(nominal_envelope).clean().fix(),
                feature=f"bed-contacting baffle cardinal web {index}",
            )
        )
    return webs


def _simplified_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="simplified nested-seam baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="simplified rear-bed bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    bucket = _cut_one(
        bucket,
        _broad_interface_reset(
            source.BAFFLE_BED_Y - BAFFLE_LAND_THICKNESS_MM - 0.15,
            source.SHOULDER_Y + 0.20,
        ),
        feature="bucket with all inherited seal structures removed",
    )
    # The inherited full-detail monocoque contains no closure ring on the
    # baffle side; those rings were added by later experiments.  Keep this
    # authoritative collar/fairing solid intact and add only the new land and
    # four local bridges below.  Cutting a broad reset here would needlessly
    # sever the very collar-to-land roots this variant is meant to preserve.

    gasket = _band_solid(
        GASKET_WIDTH_MM,
        source.BAFFLE_BED_Y,
        source.SHOULDER_Y,
        feature="five-millimeter simplified gasket reference",
    )
    bucket_land = _band_solid(
        SEAL_LAND_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM,
        feature="single simplified bucket gasket land",
    )
    baffle_land = _band_solid(
        SEAL_LAND_WIDTH_MM,
        source.BAFFLE_BED_Y - BAFFLE_LAND_THICKNESS_MM,
        source.BAFFLE_BED_Y,
        feature="single simplified baffle gasket land",
    )
    cap = prior._front_sand_cap()
    bucket_ramp = prior._linear_inner_wall_ramp(baffle_side=False)

    fill_passages: list[Solid] = []
    fill_supports: list[Solid] = []
    fill_audit: dict[str, Any] = {}
    centerline = _seal_centerline_wire(source.SHOULDER_Y)
    for x_sign, label in ((-1.0, "left"), (1.0, "right")):
        fill = _front_fill_feature(x_sign)
        passage = fill["passage"]
        support = fill["support"]
        mouth = Vector(
            x_sign * FRONT_FILL_ABS_XZ_MM,
            source.SHOULDER_Y,
            FRONT_FILL_ABS_XZ_MM,
        )
        path_distance = min(edge.distance_to(mouth) for edge in centerline.edges())
        support_clearance = (
            path_distance
            - base.P.fill_entry_d / 2.0
            - FRONT_FILL_SUPPORT_WALL_MM
            - SEAL_LAND_WIDTH_MM / 2.0
        )
        if support_clearance < MINIMUM_FILL_CLEARANCE_MM:
            raise ValueError(
                f"The {label} fill support has only "
                f"{support_clearance:.3f} mm land clearance"
            )
        if float(fill["passage_to_void_mm3"]) <= 0.01:
            raise ValueError(f"The {label} fill passage misses the sand void")
        fill_passages.append(passage)
        fill_supports.append(support)
        fill_audit[label] = {
            "mouth_center_mm": [mouth.X, mouth.Y, mouth.Z],
            "entry_diameter_mm": base.P.fill_entry_d,
            "support_wall_mm": FRONT_FILL_SUPPORT_WALL_MM,
            "support_to_seal_land_clearance_mm": support_clearance,
            "passage_to_live_sand_void_mm3": fill["passage_to_void_mm3"],
            "print_slope_from_axis_deg": fill["slope_deg"],
        }

    passages = Compound(children=fill_passages)
    cap = _single_solid(
        cap.cut(passages).clean().fix(),
        feature="front sand cap with two clean fill entries",
    )
    ramp_parts = bucket_ramp.cut(passages).clean().fix().solids()
    if not ramp_parts:
        raise ValueError("Fill passages consumed the bucket seal ramp")

    for passage, support, label in zip(
        fill_passages,
        fill_supports,
        ("left", "right"),
    ):
        bucket = _cut_one(
            bucket,
            passage,
            feature=f"bucket with unobstructed {label} fill bore",
        )
        bucket = _fuse_one(
            bucket,
            support,
            feature=f"bucket with hollow {label} fill support",
        )
    bucket = _fuse_one(bucket, cap, feature="bucket with sealed front sand gap")
    bucket = _fuse_one(
        bucket,
        bucket_land,
        feature="bucket with one continuous gasket land",
    )
    for index, ramp_part in enumerate(ramp_parts, start=1):
        if _shape_volume(ramp_part.intersect(bucket)) <= 0.01:
            continue
        bucket = _fuse_one(
            bucket,
            ramp_part,
            feature=f"bucket with flush printable seal ramp part {index}",
        )

    cardinal_webs = _baffle_cardinal_webs(nominal)
    web_roots: list[float] = []
    for index, web in enumerate(cardinal_webs, start=1):
        root = _shape_volume(web.intersect(baffle))
        if root <= 0.01:
            raise ValueError(f"Baffle cardinal web {index} has no root")
        web_roots.append(root)
        baffle = _fuse_one(
            baffle,
            web,
            feature=f"baffle with collar-to-land cardinal web {index}",
        )
    baffle = _fuse_one(
        baffle,
        baffle_land,
        feature="baffle with one cardinally supported outer gasket land",
    )

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(
        bucket_baffle_overlap,
        gasket_bucket_overlap,
        gasket_baffle_overlap,
    ) > MAX_ALLOWED_INTERFERENCE_MM3:
        overlap_sources = {
            "reference_bucket_reference_baffle": _shape_volume(
                reference_bucket.intersect(reference_baffle)
            ),
            "bucket_baffle_land": _shape_volume(bucket.intersect(baffle_land)),
            "bucket_cardinal_webs": _shape_volume(
                bucket.intersect(Compound(children=cardinal_webs))
            ),
            "baffle_bucket_land": _shape_volume(baffle.intersect(bucket_land)),
            "baffle_cap": _shape_volume(baffle.intersect(cap)),
            "baffle_ramp": _shape_volume(
                baffle.intersect(Compound(children=ramp_parts))
            ),
            "baffle_fill_supports": _shape_volume(
                baffle.intersect(Compound(children=fill_supports))
            ),
        }
        raise ValueError(
            "Simplified joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3; "
            f"sources={overlap_sources}"
        )

    gasket_audit = _band_solid(
        GASKET_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + 0.25,
        feature="simplified gasket support audit",
    )
    gasket_support_ratio = _shape_volume(
        gasket_audit.intersect(bucket)
    ) / gasket_audit.volume
    if gasket_support_ratio < MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            f"Simplified gasket support ratio is {gasket_support_ratio:.6f}"
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
        raise ValueError("Simplification changed the authoritative G1 fairing")

    _FILL_AUDIT.clear()
    _FILL_AUDIT.update(fill_audit)
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "installation_motion": "straight drop-on along the split normal",
            "cross_seam_nub_count": 0,
            "receiver_socket_count": 0,
            "redundant_baffle_inner_ring_count": 0,
            "seal_path": "rounded square with two single-curve upper fill bays",
            "seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "gasket_width_mm": GASKET_WIDTH_MM,
            "gasket_edge_margin_each_side_mm": GASKET_EDGE_MARGIN_MM,
            "fastener_bypass_count": 0,
            "angular_gasket_detour_count": 0,
            "fill_bay_count": 2,
            "gasket_bucket_support_ratio": gasket_support_ratio,
            "baffle_cardinal_collar_connection_count": 4,
            "baffle_cardinal_web_thickness_mm": BAFFLE_CARDINAL_WEB_THICKNESS_MM,
            "baffle_cardinal_web_roots_mm3": web_roots,
            "bucket_seal_ramp_from_print_axis_deg": math.degrees(
                math.atan2(
                    (
                        prior.SEAL_LAND_INNER_SIZE_MM
                        - prior.RAMP_ROOT_OUTER_SIZE_MM
                    )
                    / 2.0,
                    prior.RAMP_DEPTH_MM,
                )
            ),
            "rear_fill_port_count": 0,
            "front_hidden_fill_port_count": 2,
        }
    )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": Compound(children=[cap, bucket_land, *ramp_parts]),
        "nominal_envelope": nominal,
        "clearance_envelope": clearance,
        "reference_bucket": reference_bucket,
        "reference_baffle": reference_baffle,
        "fairing_area_mm2": fairing_faces[0].area,
        "fairing_area_difference_mm2": fairing_faces[0].area - target_area,
        "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket_overlap,
        "gasket_baffle_overlap_mm3": gasket_baffle_overlap,
        "front_fill_passages": passages,
        "front_fill_supports": Compound(children=fill_supports),
    }


def _fastener_direction(z_sign: float) -> Vector:
    angle = math.radians(FASTENER_FORWARD_ANGLE_DEG)
    return Vector(0.0, -math.sin(angle), -z_sign * math.cos(angle)).normalized()


def _fastener_surface(z_sign: float) -> Vector:
    return Vector(
        FASTENER_X_MM,
        FASTENER_SURFACE_Y_MM,
        z_sign * FASTENER_SURFACE_ABS_Z_MM,
    )


def _fastener_rotation_x(z_sign: float) -> float:
    return (
        FASTENER_FORWARD_ANGLE_DEG
        if z_sign < 0.0
        else 180.0 - FASTENER_FORWARD_ANGLE_DEG
    )


def _oriented_square_prism(
    center: Vector,
    *,
    z_sign: float,
    width_mm: float,
    thickness_mm: float,
    feature: str,
) -> Solid:
    raw = Box(
        width_mm,
        width_mm,
        thickness_mm,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        Pos(center.X, center.Y, center.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw,
        feature=feature,
    )


def _nut_access_slot(
    nut_center: Vector,
    *,
    z_sign: float,
) -> tuple[Solid, Vector]:
    angle = math.radians(FASTENER_FORWARD_ANGLE_DEG)
    insertion = Vector(
        0.0,
        math.cos(angle),
        -z_sign * math.sin(angle),
    ).normalized()
    mouth_y = source.BAFFLE_BED_Y - 0.20
    travel = (mouth_y - nut_center.Y) / insertion.Y
    start = nut_center - insertion * NUT_SLOT_SEAT_OVERTRAVEL_MM
    end = nut_center + insertion * (travel + NUT_SLOT_MOUTH_OVERTRAVEL_MM)
    midpoint = (start + end) * 0.5
    raw = Box(
        NUT_SLOT_WIDTH_X_MM,
        (end - start).length,
        NUT_SLOT_THICKNESS_MM,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    slot = (
        Pos(midpoint.X, midpoint.Y, midpoint.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw
    )
    return (
        _single_solid(slot, feature="straight rear-access square-nut slot"),
        nut_center + insertion * travel,
    )


def _bucket_d_gusset(z_sign: float) -> Solid:
    """Local printable load path from outer skin to seal-shoulder base."""
    s = z_sign
    shoulder_root_y = source.SHOULDER_Y + SAND_CAP_THICKNESS_MM
    rear_skin_root_y = FASTENER_SURFACE_Y_MM + 4.0
    plane = Plane(origin=(0.0, 0.0, 0.0), x_dir=(0.0, 1.0, 0.0), z_dir=(1.0, 0.0, 0.0))
    with BuildPart() as gusset:
        with BuildSketch(plane):
            Polygon(
                (rear_skin_root_y, s * 94.0),
                (rear_skin_root_y, s * 95.0),
                (shoulder_root_y, s * 95.0),
                (shoulder_root_y, s * 91.35),
            )
        extrude(amount=7.0, both=True)
    placed = Pos(
        0.0,
        (rear_skin_root_y + shoulder_root_y) / 2.0,
        s * (95.0 + 91.35) / 2.0,
    ) * gusset.part
    return _single_solid(
        placed.clean().fix(),
        feature="local tapered D screw gusset",
    )


def _baffle_nut_wedge(z_sign: float, nominal_envelope: Solid) -> Solid:
    """Support-free bed-grown wedge surrounding the square-nut seat."""
    s = z_sign
    nut_center = _fastener_surface(z_sign) + _fastener_direction(z_sign) * NUT_AXIS_DISTANCE_MM
    bed_y = source.BAFFLE_BED_Y
    front_y = nut_center.Y - 5.0
    plane = Plane(origin=(0.0, 0.0, 0.0), x_dir=(0.0, 1.0, 0.0), z_dir=(1.0, 0.0, 0.0))
    if s > 0.0:
        points = (
            (bed_y, 68.5),
            (bed_y, 82.5),
            (front_y, nut_center.Z - 7.0),
            (front_y, nut_center.Z + 7.0),
        )
    else:
        points = (
            (bed_y, -68.5),
            (front_y, nut_center.Z + 7.0),
            (front_y, nut_center.Z - 7.0),
            (bed_y, -82.5),
        )
    with BuildPart() as wedge:
        with BuildSketch(plane):
            Polygon(*points)
        extrude(amount=NUT_WEDGE_WIDTH_X_MM / 2.0, both=True)
    point_zs = [point[1] for point in points]
    placed = Pos(
        0.0,
        (bed_y + front_y) / 2.0,
        (min(point_zs) + max(point_zs)) / 2.0,
    ) * wedge.part
    bed_root = Pos(
        0.0,
        bed_y - BAFFLE_CARDINAL_WEB_THICKNESS_MM / 2.0,
        s * 75.5,
    ) * Box(
        NUT_WEDGE_WIDTH_X_MM,
        BAFFLE_CARDINAL_WEB_THICKNESS_MM,
        14.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    unified = placed.fuse(bed_root).clean().fix()
    clipped = unified.intersect(nominal_envelope).clean().fix()
    return _single_solid(clipped, feature="bed-grown baffle square-nut wedge")


def _simplified_dual_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]
    hardware_parts: list[Solid] = []
    cutter_parts: list[Solid] = []
    gussets: list[Solid] = []
    wedges: list[Solid] = []
    fastener_audits: dict[str, Any] = {}
    gasket_keep_clear = _band_solid(
        GASKET_WIDTH_MM + 0.50,
        source.BAFFLE_BED_Y - 0.10,
        source.SHOULDER_Y + 0.10,
        feature="fastener gasket keep-clear envelope",
    )

    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        direction = _fastener_direction(z_sign)
        surface = _fastener_surface(z_sign)
        nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

        gusset = _single_solid(
            _bucket_d_gusset(z_sign)
            .intersect(base._outer_envelope())
            .cut(common["clearance_envelope"])
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"bucket-owned {label} D screw gusset",
        )
        gusset_root = _shape_volume(gusset.intersect(bucket))
        if gusset_root <= 0.01:
            raise ValueError(f"The {label} D gusset has no bucket root")
        bucket = _fuse_one(
            bucket,
            gusset,
            feature=f"bucket with local {label} D screw gusset",
        )
        gussets.append(gusset)

        raw_boss_owned = (
            source._cylinder_between(
                surface + direction * BUCKET_BOSS_AXIS_START_MM,
                surface + direction * BUCKET_BOSS_AXIS_END_MM,
                diameter=BUCKET_BOSS_D_MM,
            )
            .intersect(base._outer_envelope())
            .cut(common["clearance_envelope"])
            .cut(gasket_keep_clear)
        )
        boss_candidates = [
            candidate.clean().fix()
            for candidate in raw_boss_owned.solids()
            if candidate.volume > 1e-6
            and _shape_volume(candidate.intersect(bucket)) > 0.01
        ]
        if not boss_candidates:
            raise ValueError(f"The {label} head boss has no bucket-owned part")
        boss = _single_solid(
            max(boss_candidates, key=lambda candidate: candidate.volume),
            feature=f"bucket-owned compact {label} head boss",
        )
        bucket = _fuse_one(
            bucket,
            boss,
            feature=f"bucket with compact {label} head boss",
        )

        wedge = _baffle_nut_wedge(z_sign, common["nominal_envelope"])
        wedge_root = _shape_volume(wedge.intersect(baffle))
        if wedge_root <= 0.01:
            raise ValueError(f"The {label} nut wedge has no baffle root")
        baffle = _fuse_one(
            baffle,
            wedge,
            feature=f"baffle with compact {label} nut wedge",
        )
        wedges.append(wedge)

        head_cubby = _single_solid(
            source._cylinder_between(
                surface - direction * 0.8,
                surface + direction * HEAD_CUBBY_AXIS_END_MM,
                diameter=HEAD_CUBBY_D_MM,
            )
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"gasket-clear {label} screw-head cubby",
        )
        through_bore = source._cylinder_between(
            surface + direction * 3.2,
            nut_center + direction * 3.2,
            diameter=SCREW_CLEARANCE_D_MM,
        )
        nut_pocket = _oriented_square_prism(
            nut_center,
            z_sign=z_sign,
            width_mm=SQUARE_NUT_POCKET_WIDTH_MM,
            thickness_mm=SQUARE_NUT_POCKET_THICKNESS_MM,
            feature=f"{label} square-nut pocket",
        )
        nut_slot, slot_mouth = _nut_access_slot(nut_center, z_sign=z_sign)
        nut_access = _single_solid(
            nut_pocket.fuse(nut_slot).clean().fix(),
            feature=f"unified {label} square-nut access",
        )

        bucket = _cut_one(
            bucket,
            head_cubby,
            feature=f"bucket with flush {label} head cubby",
        )
        bucket = _cut_one(
            bucket,
            through_bore,
            feature=f"bucket with {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            through_bore,
            feature=f"baffle with {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            nut_access,
            feature=f"baffle with open {label} square-nut slot",
        )

        screw_head = source._cylinder_between(
            surface + direction * SCREW_HEAD_AXIS_START_MM,
            surface
            + direction
            * (SCREW_HEAD_AXIS_START_MM + SCREW_HEAD_THICKNESS_MM),
            diameter=SCREW_HEAD_D_MM,
        )
        screw_shank = source._cylinder_between(
            surface + direction * 3.0,
            nut_center + direction * 2.5,
            diameter=SCREW_NOMINAL_D_MM,
        )
        nut = _oriented_square_prism(
            nut_center,
            z_sign=z_sign,
            width_mm=SQUARE_NUT_WIDTH_MM,
            thickness_mm=SQUARE_NUT_THICKNESS_MM,
            feature=f"{label} M4 square-nut reference",
        )
        hardware_parts.extend((screw_head, screw_shank, nut))
        cutter_parts.extend((head_cubby, through_bore, nut_access))

        hard_gasket_overlap = _shape_volume(
            Compound(children=[gusset, boss, wedge]).intersect(gasket)
        )
        hard_overlap_sources = {
            "gusset": _shape_volume(gusset.intersect(gasket)),
            "boss": _shape_volume(boss.intersect(gasket)),
            "wedge": _shape_volume(wedge.intersect(gasket)),
        }
        cutter_gasket_overlap = _shape_volume(
            Compound(children=[head_cubby, through_bore, nut_access]).intersect(gasket)
        )
        if max(hard_gasket_overlap, cutter_gasket_overlap) > 0.001:
            raise ValueError(
                f"The {label} fastener interrupts the gasket: "
                f"hard={hard_gasket_overlap:.6f}, "
                f"cut={cutter_gasket_overlap:.6f} mm3; "
                f"sources={hard_overlap_sources}"
            )
        fastener_audits[label] = {
            "surface_center_mm": [surface.X, surface.Y, surface.Z],
            "direction": [direction.X, direction.Y, direction.Z],
            "forward_angle_deg": FASTENER_FORWARD_ANGLE_DEG,
            "nut_center_mm": [nut_center.X, nut_center.Y, nut_center.Z],
            "slot_mouth_center_mm": [slot_mouth.X, slot_mouth.Y, slot_mouth.Z],
            "bucket_gusset_root_mm3": gusset_root,
            "baffle_wedge_root_mm3": wedge_root,
            "hard_gasket_overlap_mm3": hard_gasket_overlap,
            "cutter_gasket_overlap_mm3": cutter_gasket_overlap,
            "cross_seam_printed_boss": False,
            "straight_drop_on_path_clear": True,
        }

    # Boolean unions can reintroduce tolerance-scale ownership slivers at the
    # curved split.  Finish with the two authoritative envelopes so the drop-on
    # assembly contract is geometric, not dependent on operation history.
    bucket = _single_solid(
        bucket.cut(common["clearance_envelope"]).clean().fix(),
        feature="finally envelope-trimmed closure bucket",
    )
    baffle = _single_solid(
        baffle.intersect(common["nominal_envelope"]).clean().fix(),
        feature="finally envelope-trimmed closure baffle",
    )

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("Fastener simplification changed the G1 fairing")
    reference_bbox = reference_baffle.bounding_box()
    final_bbox = baffle.bounding_box()
    exterior_deltas = {
        "min_x": final_bbox.min.X - reference_bbox.min.X,
        "max_x": final_bbox.max.X - reference_bbox.max.X,
        "min_y": final_bbox.min.Y - reference_bbox.min.Y,
        "max_y": final_bbox.max.Y - reference_bbox.max.Y,
        "min_z": final_bbox.min.Z - reference_bbox.min.Z,
        "max_z": final_bbox.max.Z - reference_bbox.max.Z,
    }
    if max(abs(value) for value in exterior_deltas.values()) > 1e-5:
        raise ValueError(
            f"Simplified fasteners changed exterior bounds: {exterior_deltas}"
        )

    hardware = Compound(children=hardware_parts)
    cutters = Compound(children=cutter_parts)
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": cutters,
        "head_tongue": Compound(children=gussets),
        "nut_load_pad": Compound(children=wedges),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": 1.2,
        "description": (
            "Two identical dry-side M4 screws in local tapered bucket gussets "
            "drawing on rear-loaded square nuts in bed-grown baffle wedges"
        ),
        "service_notes": (
            "Slide each square nut down its open inner-face slot, drop the "
            "baffle straight onto the bucket, then tighten the flush top and "
            "bottom screws"
        ),
        "closure_passage_mode": (
            "two dry-side screw passages entirely ahead of the gasket plane"
        ),
        "geometry": {
            "fastener_count": 2,
            "upper_hook_count": 0,
            "hook_receiver_count": 0,
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "head_d_mm": SCREW_HEAD_D_MM,
            "head_cubby_d_mm": HEAD_CUBBY_D_MM,
            "bucket_boss_d_mm": BUCKET_BOSS_D_MM,
            "cross_seam_bucket_boss_count": 0,
            "baffle_boss_socket_count": 0,
            "square_nut_nominal_width_mm": SQUARE_NUT_WIDTH_MM,
            "square_nut_nominal_thickness_mm": SQUARE_NUT_THICKNESS_MM,
            "square_nut_pocket_width_mm": SQUARE_NUT_POCKET_WIDTH_MM,
            "square_nut_pocket_thickness_mm": SQUARE_NUT_POCKET_THICKNESS_MM,
            "nut_slots_open_on_inner_print_face": True,
            "straight_drop_on_insertion_path": True,
            "gasket_fastener_bypass_required": False,
            "outer_fairing_area_difference_mm2": fairing_faces[0].area - target_area,
            "authoritative_fairing_face_exactly_preserved": True,
            "baffle_exterior_bounds_difference_mm": exterior_deltas,
            "external_baffle_blisters": False,
            "bottom_head_protrusion_mm": 0.0,
            "top_head_protrusion_mm": 0.0,
            "fasteners": fastener_audits,
        },
    }


def _printable_transverse_brace() -> Solid:
    variant = base.RESTORED_FEATURE_VARIANT
    cavity_size = base.D.width - 2.0 * base.D.wall_stack_t
    outer_size = cavity_size + 2.0 * variant.window_brace_skin_embed
    full_inner_size = cavity_size - 2.0 * variant.window_brace_height
    front_y = variant.window_brace_center_y - variant.window_brace_width / 2.0
    rear_y = front_y + BRACE_RAMP_LENGTH_MM
    outer = Pos(0.0, (front_y + rear_y) / 2.0, 0.0) * Box(
        outer_size,
        rear_y - front_y,
        outer_size,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    inner = source._lofted_rounded_rectangle(
        (
            (full_inner_size, variant.window_brace_corner_r, front_y - 0.10),
            (cavity_size, variant.window_brace_corner_r, rear_y + 0.10),
        ),
        feature="support-free transverse brace cavity",
        ruled=True,
    )
    frame = _single_solid(
        outer.cut(inner).clean().fix(),
        feature="support-free tapered transverse frame",
    )
    floor_top_z = -base.D.height / 2.0 + base.D.wall_stack_t
    rail_inner_z = (
        base.D.width / 2.0
        - base.D.wall_stack_t
        - variant.window_brace_height
    )
    cutter_top_z = -rail_inner_z + 0.05
    center_floor_opening = Pos(
        0.0,
        (front_y + rear_y) / 2.0,
        (floor_top_z - 20.0 + cutter_top_z) / 2.0,
    ) * Box(
        full_inner_size,
        rear_y - front_y + 4.0,
        cutter_top_z - (floor_top_z - 20.0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        frame.cut(center_floor_opening).clean().fix(),
        feature="tapered U brace with floor-reaching side legs",
    )


def _printable_longitudinal_rails() -> Compound:
    variant = base.RESTORED_FEATURE_VARIANT
    driver_seat_y = -base.D.depth / 2.0 + 10.0 + base.BLACK_HOLE_SEAT_DEPTH
    buttress_tail_y = (
        driver_seat_y
        - base.D.front_brace_baffle_embed
        + base.D.front_brace_blend_length
    )
    front_y = buttress_tail_y - 0.50
    rear_y = base.REAR_INNER_Y
    ramp_front_y = rear_y - BRACE_RAMP_LENGTH_MM
    cavity_half = base.D.width / 2.0 - base.D.wall_stack_t
    radial_height = variant.vertical_brace_height
    skin_embed = variant.vertical_brace_skin_embed
    tangential_width = variant.vertical_brace_width
    radial_center = cavity_half - radial_height / 2.0 + skin_embed / 2.0
    main = Pos(0.0, (front_y + ramp_front_y) / 2.0, radial_center) * Box(
        tangential_width,
        # One millimetre of true volume overlap with the tapered ramp avoids
        # a coincident-face union while keeping the same visible envelope.
        ramp_front_y - front_y + 2.0,
        radial_height + skin_embed,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    with BuildPart() as rear_ramp:
        # Use the canonical plane object here.  A numerically equivalent
        # custom plane can be re-centred by BuildPart during extrusion.
        with BuildSketch(Plane.YZ):
            Polygon(
                (rear_y, cavity_half),
                (rear_y, cavity_half + skin_embed),
                (ramp_front_y, cavity_half + skin_embed),
                (ramp_front_y, cavity_half - radial_height),
            )
        extrude(amount=tangential_width / 2.0, both=True)
    # BuildSketch normalizes this local polygon about the sketch origin; put
    # the resulting trapezoidal prism back at its specified Y/Z envelope.
    placed_rear_ramp = Pos(
        0.0,
        (rear_y + ramp_front_y) / 2.0,
        (
            cavity_half
            + skin_embed
            + cavity_half
            - radial_height
        )
        / 2.0,
    ) * rear_ramp.part
    top = _single_solid(
        main.fuse(placed_rear_ramp).clean().fix(),
        feature="rear-ramped longitudinal top rail",
    )
    return Compound(
        children=[
            top,
            Rot(0.0, 90.0, 0.0) * top,
            Rot(0.0, -90.0, 0.0) * top,
        ]
    )


def _simplified_internal_braces(port_clearance: Any) -> Compound:
    original = ORIGINAL_RESTORED_INTERNAL_BRACES(port_clearance)
    enclosure_clip = base._outer_envelope()
    tube_clearances = (
        port_clearance,
        base._internal_tower_mount_saddle(
            clearance=base.D.tube_install_clearance
        ),
        base._bottom_tab_brace_clearance(),
        base._rear_tab_brace_clearance(),
    )
    variant = base.RESTORED_FEATURE_VARIANT
    transverse_front_y = (
        variant.window_brace_center_y - variant.window_brace_width / 2.0
    )
    transverse_rear_y = transverse_front_y + BRACE_RAMP_LENGTH_MM
    preserved: list[Solid] = []
    longitudinal_masks: list[Solid] = []
    replaced_transverse_count = 0
    for solid in original.solids():
        bbox = solid.bounding_box()
        is_transverse = (
            bbox.min.Y >= transverse_front_y - 0.01
            and bbox.max.Y <= transverse_rear_y + 0.01
            and bbox.size.Y <= BRACE_RAMP_LENGTH_MM + 0.02
            and max(bbox.size.X, bbox.size.Z) > 100.0
        )
        is_skinny_longitudinal = (
            bbox.min.Y < -40.0
            and bbox.max.Y > 20.0
            and (
            (
                bbox.size.X <= 12.0
                and bbox.min.Z > 70.0
            )
            or (
                bbox.size.Z <= 12.0
                and (bbox.min.X > 70.0 or bbox.max.X < -70.0)
            )
            )
        )
        if is_transverse:
            replaced_transverse_count += 1
        elif is_skinny_longitudinal:
            longitudinal_masks.append(copy.copy(solid))
        else:
            preserved.append(copy.copy(solid))
    if replaced_transverse_count == 0 or len(longitudinal_masks) < 3:
        raise ValueError(
            "Unable to identify the authoritative transverse and longitudinal "
            "brace pieces"
        )

    retained: list[Solid] = []
    for brace in _printable_transverse_brace().solids():
        current = list(brace.intersect(enclosure_clip).solids())
        for clearance in tube_clearances:
            current = [
                cut_solid.clean().fix()
                for solid in current
                for cut_solid in solid.cut(clearance).solids()
                if cut_solid.volume > 1e-6
            ]
        for solid in current:
            if solid.volume > 1e-6:
                retained.append(solid)

    # The authoritative masks already contain all port, mounting-ear,
    # absorber, and tower clearances.  Intersecting the tapered replacements
    # with those masks cannot create a new notch or close an existing one.
    for rail in _printable_longitudinal_rails().solids():
        rail_bbox = rail.bounding_box()
        if rail_bbox.min.Z > 70.0:
            masks = [
                mask
                for mask in longitudinal_masks
                if mask.bounding_box().min.Z > 70.0
                and mask.bounding_box().size.X <= 12.0
            ]
        elif rail_bbox.min.X > 70.0:
            masks = [
                mask
                for mask in longitudinal_masks
                if mask.bounding_box().min.X > 70.0
            ]
        else:
            masks = [
                mask
                for mask in longitudinal_masks
                if mask.bounding_box().max.X < -70.0
            ]
        if not masks:
            raise ValueError("A tapered longitudinal rail has no baseline mask")
        longitudinal_allowed = (
            masks[0] if len(masks) == 1 else Compound(children=masks)
        )
        retained.extend(
            piece.clean().fix()
            for piece in rail.intersect(longitudinal_allowed).solids()
            if piece.volume > 1e-6
        )
    retained.extend(preserved)
    if not retained:
        raise ValueError("Simplified brace network is empty")
    floor_top_z = -base.D.height / 2.0 + base.D.wall_stack_t
    side_leg_bottoms = [
        solid.bounding_box().min.Z
        for solid in retained
        if solid.bounding_box().size.Z > 100.0
    ]
    _BRACE_AUDIT.clear()
    _BRACE_AUDIT.update(
        {
            "construction": "rear-ramped rails and tapered U-frame",
            "print_orientation": "enclosure rear face on print bed",
            "support_free_ramp_length_mm": BRACE_RAMP_LENGTH_MM,
            "replaced_transverse_piece_count": replaced_transverse_count,
            "tapered_longitudinal_mask_count": len(longitudinal_masks),
            "authoritative_nonrail_braces_preserved": len(preserved),
            "transverse_side_legs_reach_floor": bool(side_leg_bottoms)
            and min(side_leg_bottoms) <= floor_top_z + 0.10,
            "allowed_relief": (
                "physical airway, upper tube saddle, and removable-tube "
                "mounting ears only"
            ),
            "saddle_clearance_recut": True,
            "tab_clearance_recut": True,
        }
    )
    return Compound(children=retained)


def _solid_rear_without_artifacts(
    port_clearance: Any,
    port_install_clearance: Any,
    *,
    include_gx16: bool = True,
    include_fill_ports: bool = True,
) -> Any:
    del include_fill_ports
    result = _single_solid(
        ORIGINAL_SOLID_REAR_DETAIL_BASE(
            port_clearance,
            port_install_clearance,
            include_gx16=include_gx16,
            include_fill_ports=False,
        ),
        feature="rear enclosure without fill blisters",
    )
    additions: list[Solid] = []
    outer_envelope = base._outer_envelope()
    for fill_x in (-base.P.fill_port_x, base.P.fill_port_x):
        clipped = base._sand_fill_rear_bore(fill_x).intersect(outer_envelope).clean().fix()
        additions.extend(clipped.solids())
    if additions:
        result = _fuse_one(
            result,
            Compound(children=additions),
            feature="rear wall with former fill bores closed",
        )
        # Re-establish the exact acoustic boundary after the closure union so
        # no cylindrical half-moon can remain proud of the inner rear face.
        result = _single_solid(
            result.cut(base._acoustic_domain()).clean().fix(),
            feature="artifact-free solid rear acoustic face",
        )
    return result


def _update_contract(diagnostics: dict[str, Any]) -> None:
    diagnostics["enclosure"]["restored_original_features"]["sand_fill_ports"] = {
        "count": 0,
        "rear_entries_removed": True,
        "rear_wall_is_solid": True,
        "former_rear_bore_artifacts_removed": True,
        "replacement_front_hidden_entries": {
            "count": 2,
            "mouth_centers_xz_mm": [
                [-FRONT_FILL_ABS_XZ_MM, FRONT_FILL_ABS_XZ_MM],
                [FRONT_FILL_ABS_XZ_MM, FRONT_FILL_ABS_XZ_MM],
            ],
            "entry_diameter_mm": base.P.fill_entry_d,
            "fully_unobstructed_by_installed_baffle": True,
            "outside_gasket_path": True,
        },
    }


def _build_robust_viewer_cutaway() -> Path:
    """Replace the fragile face-only cutaway with clipped valid solids."""
    full_system = import_step(OUT / "centered_captive_nut_full_system.step")
    bbox = full_system.bounding_box()
    clip_max_x = -0.02
    margin = 2.0
    clip = Pos(
        (bbox.min.X - margin + clip_max_x) / 2.0,
        (bbox.min.Y + bbox.max.Y) / 2.0,
        (bbox.min.Z + bbox.max.Z) / 2.0,
    ) * Box(
        clip_max_x - (bbox.min.X - margin),
        bbox.size.Y + 2.0 * margin,
        bbox.size.Z + 2.0 * margin,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    pieces: list[Solid] = []
    for solid in full_system.solids():
        pieces.extend(
            piece.clean().fix()
            for piece in solid.intersect(clip).solids()
            if piece.volume > 1e-6
        )
    if not pieces or not all(piece.is_valid for piece in pieces):
        raise ValueError("Robust solid cutaway did not produce valid solids")
    cutaway = Compound(children=pieces)
    path = OUT / "simplified_printable_closure_cutaway.step"
    export_step(cutaway, path, unit=Unit.MM, write_pcurves=True)
    imported = import_step(path)
    if len(imported.solids()) != len(pieces) or not all(
        solid.is_valid for solid in imported.solids()
    ):
        raise ValueError("Robust cutaway STEP round trip failed")
    return path


def _export_print_orientations() -> None:
    bucket = _single_solid(
        import_step(OUT / "centered_captive_nut_bucket.step"),
        feature="round-tripped simplified bucket",
    )
    baffle = _single_solid(
        import_step(OUT / "centered_captive_nut_baffle.step"),
        feature="round-tripped simplified baffle",
    )
    exports = {
        "simplified_bucket_print_orientation.step": (
            source._print_oriented_bucket(bucket)
        ),
        "simplified_baffle_print_orientation.step": (
            source._print_oriented_baffle(baffle)
        ),
    }
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        if len(imported.solids()) != len(shape.solids()) or not all(
            solid.is_valid for solid in imported.solids()
        ):
            raise ValueError(f"Print-orientation STEP round trip failed: {filename}")


def _generate_simplified_viewers() -> None:
    _build_robust_viewer_cutaway()
    _export_print_orientations()
    specs = (
        ("centered_captive_nut_assembled.step", "viewer", False),
        ("centered_captive_nut_exploded.step", "exploded_viewer", False),
        (
            "simplified_printable_closure_cutaway.step",
            "cutaway_viewer",
            True,
        ),
        ("centered_captive_nut_bucket.step", "bucket_viewer", False),
        ("centered_captive_nut_baffle.step", "baffle_viewer", False),
        (
            "simplified_bucket_print_orientation.step",
            "bucket_print_viewer",
            False,
        ),
        (
            "simplified_baffle_print_orientation.step",
            "baffle_print_viewer",
            False,
        ),
    )
    for filename, viewer_name, cutaway in specs:
        viewer_dir = OUT / viewer_name
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / filename),
                "--out",
                str(viewer_dir),
            ],
            check=True,
        )
        centered._configure_viewer(viewer_dir, cutaway=cutaway)


def generate() -> dict[str, Any]:
    original_out = prior.OUT
    original_name = prior.NAME
    original_common = prior._perimeter_common_joint
    original_concept = prior._reinforced_dual_concept
    original_rear = source.prior._solid_rear_detail_base
    original_braces = base._restored_internal_braces
    original_printable_braces = source._printable_restored_internal_braces
    original_centered_viewers = centered._generate_viewers

    prior.OUT = OUT
    prior.NAME = NAME
    prior._perimeter_common_joint = _simplified_common_joint
    prior._reinforced_dual_concept = _simplified_dual_concept
    source.prior._solid_rear_detail_base = _solid_rear_without_artifacts
    # centered_captive_nut installs this source-level callable onto ``base``
    # inside its own generate() function.  Patch both references so the
    # complete inheritance chain actually uses the simplified brace set.
    source._printable_restored_internal_braces = _simplified_internal_braces
    base._restored_internal_braces = _simplified_internal_braces
    centered._generate_viewers = lambda: None
    try:
        diagnostics = prior.generate()
    finally:
        prior.OUT = original_out
        prior.NAME = original_name
        prior._perimeter_common_joint = original_common
        prior._reinforced_dual_concept = original_concept
        source.prior._solid_rear_detail_base = original_rear
        source._printable_restored_internal_braces = original_printable_braces
        base._restored_internal_braces = original_braces
        centered._generate_viewers = original_centered_viewers

    closure_diagnostics = diagnostics.pop("front_fill_perimeter_seal_closure")
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["front_fill"] = dict(_FILL_AUDIT)
    closure_diagnostics["printable_bracing"] = dict(_BRACE_AUDIT)
    diagnostics["name"] = NAME
    diagnostics["status"] = "complete simplified printable closure experiment"
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_simplified_printable_closure"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_simplified_printable_closure"
        ),
        "parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["simplified_printable_closure"] = closure_diagnostics
    _update_contract(diagnostics)
    diagnostics["preserved_full_detail_contract"].update(
        {
            "rear_sand_fill_ports": 0,
            "front_hidden_corner_sand_fill_ports": 2,
            "solid_rear_wall": True,
            "gx16_rear_opening_preserved": True,
            "external_parabolic_g1_package_unchanged": True,
            "driver_collar_preserved": True,
            "straight_drop_on_baffle": True,
        }
    )
    _generate_simplified_viewers()
    diagnostics["simplified_printable_closure"]["viewer_workflow"] = {
        "inherited_face_cutaway_skipped": True,
        "robust_solid_cutaway_generated": True,
        "assembled_viewer": "viewer/index.html",
        "cutaway_viewer": "cutaway_viewer/index.html",
        "bucket_viewer": "bucket_viewer/index.html",
        "baffle_viewer": "baffle_viewer/index.html",
        "bucket_print_viewer": "bucket_print_viewer/index.html",
        "baffle_print_viewer": "baffle_print_viewer/index.html",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
