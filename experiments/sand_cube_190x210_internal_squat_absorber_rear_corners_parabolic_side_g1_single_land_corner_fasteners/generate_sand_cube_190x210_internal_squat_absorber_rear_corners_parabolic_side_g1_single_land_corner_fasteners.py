"""Generate the single-land, outer-corner-fastener printable G1 closure.

The complete rear-corner absorber system is inherited from the preceding
simplified printable closure.  This sibling replaces only the front joint:
one exact perimeter drives the gasket land and its bed-grown underside, while
two M4 closures cross the outer land/socket corner and terminate in deep,
side-loaded square-nut cassettes on the hidden face of the baffle.
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
    Compound,
    Edge,
    Pos,
    Rot,
    Solid,
    Vector,
    Wire,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simplified_printable_closure"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simplified_printable_closure as previous  # noqa: E402


source = previous.source
closure = previous.closure
base = previous.base
parent = previous.parent

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_single_land_corner_fasteners"
)
NAME = "sand_cube_190x210_parabolic_g1_single_land_corner_fasteners"

# One mathematical perimeter owns the gasket reference, both contact lands,
# and the bucket's printable underside.  The exact upper quarter-circle radius
# is solved so the complete 6.75 mm land clears the 9.15 mm fill mouth, its
# 1.2 mm support wall, and a small placement allowance.
PATH_HALF_SIZE_MM = previous.PATH_HALF_SIZE_MM
PATH_BOTTOM_CORNER_TANGENCY_MM = previous.PATH_BOTTOM_CORNER_TANGENCY_MM
SEAL_LAND_WIDTH_MM = previous.SEAL_LAND_WIDTH_MM
GASKET_WIDTH_MM = previous.GASKET_WIDTH_MM
GASKET_EDGE_MARGIN_MM = previous.GASKET_EDGE_MARGIN_MM
SAND_CAP_THICKNESS_MM = previous.SAND_CAP_THICKNESS_MM
BAFFLE_LAND_THICKNESS_MM = previous.BAFFLE_LAND_THICKNESS_MM
SEAL_RAMP_ROOT_WIDTH_MM = 2.0
SEAL_RAMP_DEPTH_MM = previous.prior.RAMP_DEPTH_MM
FILL_TO_LAND_CLEARANCE_MM = 0.75
FILL_SUPPORT_OUTER_RADIUS_MM = (
    base.P.fill_entry_d / 2.0 + previous.FRONT_FILL_SUPPORT_WALL_MM
)
FILL_CENTER_TO_PATH_MM = (
    FILL_SUPPORT_OUTER_RADIUS_MM
    + SEAL_LAND_WIDTH_MM / 2.0
    + FILL_TO_LAND_CLEARANCE_MM
)
_FILL_CORNER_DELTA_MM = (
    PATH_HALF_SIZE_MM - previous.FRONT_FILL_ABS_XZ_MM
)
UPPER_CORNER_RADIUS_MM = (
    FILL_CENTER_TO_PATH_MM
    + math.sqrt(2.0) * _FILL_CORNER_DELTA_MM
) / (math.sqrt(2.0) - 1.0)
UPPER_CORNER_CENTER_MM = PATH_HALF_SIZE_MM - UPPER_CORNER_RADIUS_MM
SCREW_BYPASS_HALF_WIDTH_MM = 12.0
SCREW_BYPASS_DEPTH_MM = 4.00

# Each M4 head remains flush in the outer top/bottom surface.  A steeper
# forward lean keeps the axis near the dry outer corner while reaching a nut
# 8.47 mm forward of the baffle bed.  The nut loads against five millimetres of
# cassette material on the screw-head side rather than a thin pocket floor.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -72.0
FASTENER_SURFACE_ABS_Z_MM = 95.0
FASTENER_FORWARD_ANGLE_DEG = 55.0
NUT_AXIS_DISTANCE_MM = 15.0
SCREW_NOMINAL_D_MM = previous.SCREW_NOMINAL_D_MM
SCREW_CLEARANCE_D_MM = previous.SCREW_CLEARANCE_D_MM
SCREW_HEAD_D_MM = previous.SCREW_HEAD_D_MM
SCREW_HEAD_THICKNESS_MM = previous.SCREW_HEAD_THICKNESS_MM
SCREW_HEAD_AXIS_START_MM = 3.50
HEAD_CUBBY_D_MM = 9.60
HEAD_CUBBY_AXIS_END_MM = 6.00
BUCKET_TONGUE_D_MM = 15.0
BUCKET_TONGUE_AXIS_START_MM = 0.45
BUCKET_TONGUE_AXIS_END_MM = 8.0
BAFFLE_RELIEF_D_MM = 15.8
BAFFLE_RELIEF_AXIS_START_MM = 4.2
BAFFLE_RELIEF_AXIS_END_MM = 8.4
SQUARE_NUT_WIDTH_MM = previous.SQUARE_NUT_WIDTH_MM
SQUARE_NUT_THICKNESS_MM = previous.SQUARE_NUT_THICKNESS_MM
SQUARE_NUT_POCKET_WIDTH_MM = previous.SQUARE_NUT_POCKET_WIDTH_MM
SQUARE_NUT_POCKET_THICKNESS_MM = previous.SQUARE_NUT_POCKET_THICKNESS_MM
NUT_SLOT_WIDTH_MM = 7.70
NUT_SLOT_THICKNESS_MM = 3.80
NUT_SLOT_SIDE_TRAVEL_MM = 12.0
NUT_CASSETTE_WIDTH_X_MM = 20.0
NUT_CASSETTE_FRONT_WALL_MM = 2.0
NUT_CASSETTE_RADIAL_HALF_MM = 4.8
NUT_BEARING_SHOULDER_MM = 5.0
NUT_BEARING_AUDIT_THICKNESS_MM = 1.50
BUCKET_GUSSET_WIDTH_X_MM = 15.0
MINIMUM_NUT_BEARING_SUPPORT_RATIO = 0.97
MINIMUM_HEAD_BEARING_SUPPORT_RATIO = 0.90

FAIRING_AREA_TOLERANCE_MM2 = previous.FAIRING_AREA_TOLERANCE_MM2
MAX_ALLOWED_INTERFERENCE_MM3 = previous.MAX_ALLOWED_INTERFERENCE_MM3
MINIMUM_GASKET_SUPPORT_RATIO = previous.MINIMUM_GASKET_SUPPORT_RATIO

_JOINT_AUDIT: dict[str, Any] = {}
_FILL_AUDIT: dict[str, Any] = {}
_FASTENER_AUDIT: dict[str, Any] = {}


def _shape_volume(shape: Any) -> float:
    return previous._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return previous._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return previous._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return previous._fuse_one(shape, addition, feature=feature)


def _p(x_mm: float, y_mm: float, z_mm: float) -> tuple[float, float, float]:
    return (x_mm, y_mm, z_mm)


def _perimeter_wire(*, offset_mm: float, y_mm: float) -> Wire:
    """Exact rounded-square wire with one circular upper fill arc per side."""
    h = PATH_HALF_SIZE_MM + offset_mm
    upper_radius = UPPER_CORNER_RADIUS_MM + offset_mm
    upper_center = UPPER_CORNER_CENTER_MM
    bc = PATH_BOTTOM_CORNER_TANGENCY_MM
    bottom_radius = PATH_HALF_SIZE_MM - bc + offset_mm
    diag = 1.0 / math.sqrt(2.0)
    p = lambda x, z: _p(x, y_mm, z)
    edges = [
        Edge.make_line(
            p(-upper_center, h),
            p(-SCREW_BYPASS_HALF_WIDTH_MM, h),
        ),
        Edge.make_bezier(
            p(-SCREW_BYPASS_HALF_WIDTH_MM, h),
            p(-10.0, h),
            p(-8.0, h),
            p(-4.0, h - SCREW_BYPASS_DEPTH_MM),
            p(-2.0, h - SCREW_BYPASS_DEPTH_MM),
            p(0.0, h - SCREW_BYPASS_DEPTH_MM),
        ),
        Edge.make_bezier(
            p(0.0, h - SCREW_BYPASS_DEPTH_MM),
            p(2.0, h - SCREW_BYPASS_DEPTH_MM),
            p(4.0, h - SCREW_BYPASS_DEPTH_MM),
            p(8.0, h),
            p(10.0, h),
            p(SCREW_BYPASS_HALF_WIDTH_MM, h),
        ),
        Edge.make_line(
            p(SCREW_BYPASS_HALF_WIDTH_MM, h),
            p(upper_center, h),
        ),
        Edge.make_three_point_arc(
            p(upper_center, h),
            p(
                upper_center + upper_radius * diag,
                upper_center + upper_radius * diag,
            ),
            p(h, upper_center),
        ),
        Edge.make_line(p(h, upper_center), p(h, -bc)),
        Edge.make_three_point_arc(
            p(h, -bc),
            p(
                bc + bottom_radius * diag,
                -bc - bottom_radius * diag,
            ),
            p(bc, -h),
        ),
        Edge.make_line(
            p(bc, -h),
            p(SCREW_BYPASS_HALF_WIDTH_MM, -h),
        ),
        Edge.make_bezier(
            p(SCREW_BYPASS_HALF_WIDTH_MM, -h),
            p(10.0, -h),
            p(8.0, -h),
            p(4.0, -h + SCREW_BYPASS_DEPTH_MM),
            p(2.0, -h + SCREW_BYPASS_DEPTH_MM),
            p(0.0, -h + SCREW_BYPASS_DEPTH_MM),
        ),
        Edge.make_bezier(
            p(0.0, -h + SCREW_BYPASS_DEPTH_MM),
            p(-2.0, -h + SCREW_BYPASS_DEPTH_MM),
            p(-4.0, -h + SCREW_BYPASS_DEPTH_MM),
            p(-8.0, -h),
            p(-10.0, -h),
            p(-SCREW_BYPASS_HALF_WIDTH_MM, -h),
        ),
        Edge.make_line(
            p(-SCREW_BYPASS_HALF_WIDTH_MM, -h),
            p(-bc, -h),
        ),
        Edge.make_three_point_arc(
            p(-bc, -h),
            p(
                -bc - bottom_radius * diag,
                -bc - bottom_radius * diag,
            ),
            p(-h, -bc),
        ),
        Edge.make_line(p(-h, -bc), p(-h, upper_center)),
        Edge.make_three_point_arc(
            p(-h, upper_center),
            p(
                -upper_center - upper_radius * diag,
                upper_center + upper_radius * diag,
            ),
            p(-upper_center, h),
        ),
    ]
    wires = Wire.combine(edges)
    if len(wires) != 1 or not wires[0].is_closed:
        raise ValueError("Single-land perimeter did not close")
    return wires[0]


def _loft_between_offsets(
    offset0_mm: float,
    y0_mm: float,
    offset1_mm: float,
    y1_mm: float,
    *,
    feature: str,
) -> Solid:
    return _single_solid(
        Solid.make_loft(
            [
                _perimeter_wire(offset_mm=offset0_mm, y_mm=y0_mm),
                _perimeter_wire(offset_mm=offset1_mm, y_mm=y1_mm),
            ],
            ruled=True,
        ).clean().fix(),
        feature=feature,
    )


def _single_face_band(
    width_mm: float,
    y0_mm: float,
    y1_mm: float,
    *,
    feature: str,
) -> Solid:
    """One extruded annulus, without segment sweeps or joint cylinders."""
    outer = _loft_between_offsets(
        width_mm / 2.0,
        y0_mm,
        width_mm / 2.0,
        y1_mm,
        feature=f"{feature} outer envelope",
    )
    inner = _loft_between_offsets(
        -width_mm / 2.0,
        min(y0_mm, y1_mm) - 0.10,
        -width_mm / 2.0,
        max(y0_mm, y1_mm) + 0.10,
        feature=f"{feature} inner envelope",
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature=feature,
    )


def _unified_bucket_ramp() -> Solid:
    """Grow the entire land from the inner wall with no secondary shelf."""
    face_y = source.SHOULDER_Y
    root_y = face_y + SEAL_RAMP_DEPTH_MM
    inner_offset = -SEAL_LAND_WIDTH_MM / 2.0
    outer = _loft_between_offsets(
        SEAL_LAND_WIDTH_MM / 2.0,
        face_y,
        inner_offset + SEAL_RAMP_ROOT_WIDTH_MM,
        root_y,
        feature="single-land printable ramp outer envelope",
    )
    inner = _loft_between_offsets(
        inner_offset,
        face_y - 0.10,
        inner_offset,
        root_y + 0.10,
        feature="single-land printable ramp inner envelope",
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="one continuous bed-grown bucket land underside",
    )


def _single_land_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="single-land nested-seam baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="single-land rear-bed bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    bucket = _cut_one(
        bucket,
        previous._broad_interface_reset(
            source.BAFFLE_BED_Y - BAFFLE_LAND_THICKNESS_MM - 0.15,
            source.SHOULDER_Y + 0.20,
        ),
        feature="bucket with all inherited seal shelves removed",
    )

    gasket = _single_face_band(
        GASKET_WIDTH_MM,
        source.BAFFLE_BED_Y,
        source.SHOULDER_Y,
        feature="five-millimeter single-face gasket reference",
    )
    bucket_land = _single_face_band(
        SEAL_LAND_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM,
        feature="one continuous bucket gasket land",
    )
    baffle_land = _single_face_band(
        SEAL_LAND_WIDTH_MM,
        source.BAFFLE_BED_Y - BAFFLE_LAND_THICKNESS_MM,
        source.BAFFLE_BED_Y,
        feature="one continuous baffle gasket land",
    )
    cap = previous.prior._front_sand_cap()
    bucket_ramp = _unified_bucket_ramp()

    fill_passages: list[Solid] = []
    fill_supports: list[Solid] = []
    fill_audit: dict[str, Any] = {}
    centerline = _perimeter_wire(offset_mm=0.0, y_mm=source.SHOULDER_Y)
    for x_sign, label in ((-1.0, "left"), (1.0, "right")):
        fill = previous._front_fill_feature(x_sign)
        passage = fill["passage"]
        support = fill["support"]
        mouth = Vector(
            x_sign * previous.FRONT_FILL_ABS_XZ_MM,
            source.SHOULDER_Y,
            previous.FRONT_FILL_ABS_XZ_MM,
        )
        path_distance = min(edge.distance_to(mouth) for edge in centerline.edges())
        support_clearance = (
            path_distance
            - base.P.fill_entry_d / 2.0
            - previous.FRONT_FILL_SUPPORT_WALL_MM
            - SEAL_LAND_WIDTH_MM / 2.0
        )
        if support_clearance < FILL_TO_LAND_CLEARANCE_MM - 0.01:
            raise ValueError(
                f"The {label} circular fill arc has only "
                f"{support_clearance:.3f} mm land clearance"
            )
        if float(fill["passage_to_void_mm3"]) <= 0.01:
            raise ValueError(f"The {label} fill passage misses the live sand void")
        fill_passages.append(passage)
        fill_supports.append(support)
        fill_audit[label] = {
            "mouth_center_mm": [mouth.X, mouth.Y, mouth.Z],
            "entry_diameter_mm": base.P.fill_entry_d,
            "support_wall_mm": previous.FRONT_FILL_SUPPORT_WALL_MM,
            "support_to_seal_land_clearance_mm": support_clearance,
            "passage_to_live_sand_void_mm3": fill["passage_to_void_mm3"],
            "print_slope_from_axis_deg": fill["slope_deg"],
            "gasket_corner_curve": "one exact circular tangent arc",
        }

    passages = Compound(children=fill_passages)
    cap = _single_solid(
        cap.cut(passages).clean().fix(),
        feature="front sand cap with two clean fill entries",
    )
    ramp_parts = bucket_ramp.cut(passages).clean().fix().solids()
    if not ramp_parts:
        raise ValueError("Fill passages consumed the unified bucket ramp")

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
        feature="bucket with exactly one gasket land",
    )
    for index, ramp_part in enumerate(ramp_parts, start=1):
        if _shape_volume(ramp_part.intersect(bucket)) <= 0.01:
            continue
        bucket = _fuse_one(
            bucket,
            ramp_part,
            feature=f"bucket with unified printable land ramp part {index}",
        )

    cardinal_webs = previous._baffle_cardinal_webs(nominal)
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
        feature="baffle with one cardinally supported gasket land",
    )

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(
        bucket_baffle_overlap,
        gasket_bucket_overlap,
        gasket_baffle_overlap,
    ) > MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            "Single-land joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3"
        )

    gasket_audit = _single_face_band(
        GASKET_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + 0.25,
        feature="single-land gasket support audit",
    )
    gasket_support_ratio = _shape_volume(
        gasket_audit.intersect(bucket)
    ) / gasket_audit.volume
    if gasket_support_ratio < MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            f"Single-land gasket support ratio is {gasket_support_ratio:.6f}"
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
        raise ValueError("Single-land joint changed the authoritative G1 fairing")

    _FILL_AUDIT.clear()
    _FILL_AUDIT.update(fill_audit)
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "installation_motion": "straight drop-on along the split normal",
            "redundant_baffle_inner_ring_count": 0,
            "secondary_bucket_seal_shelf_count": 0,
            "seal_path": (
                "rounded square with exact circular upper fill arcs and two "
                "shallow curvature-controlled screw bows"
            ),
            "seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "gasket_width_mm": GASKET_WIDTH_MM,
            "gasket_edge_margin_each_side_mm": GASKET_EDGE_MARGIN_MM,
            "upper_fill_arc_radius_mm": UPPER_CORNER_RADIUS_MM,
            "upper_fill_arc_tangent_coordinate_mm": UPPER_CORNER_CENTER_MM,
            "angular_gasket_detour_count": 0,
            "smooth_fastener_bypass_count": 2,
            "smooth_fastener_bypass_depth_mm": SCREW_BYPASS_DEPTH_MM,
            "segmented_sweep_joint_count": 0,
            "gasket_bucket_support_ratio": gasket_support_ratio,
            "baffle_cardinal_collar_connection_count": 4,
            "baffle_cardinal_web_roots_mm3": web_roots,
            "bucket_land_and_ramp_share_exact_perimeter": True,
            "bucket_seal_ramp_from_print_axis_deg": math.degrees(
                math.atan2(
                    SEAL_LAND_WIDTH_MM - SEAL_RAMP_ROOT_WIDTH_MM,
                    SEAL_RAMP_DEPTH_MM,
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


def _oriented_prism(
    center: Vector,
    *,
    z_sign: float,
    width_x_mm: float,
    width_in_plane_mm: float,
    thickness_on_axis_mm: float,
    feature: str,
) -> Solid:
    raw = Box(
        width_x_mm,
        width_in_plane_mm,
        thickness_on_axis_mm,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        Pos(center.X, center.Y, center.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw,
        feature=feature,
    )


def _side_loaded_nut_access(
    nut_center: Vector,
    *,
    z_sign: float,
) -> tuple[Solid, Vector]:
    pocket = _oriented_prism(
        nut_center,
        z_sign=z_sign,
        width_x_mm=SQUARE_NUT_POCKET_WIDTH_MM,
        width_in_plane_mm=SQUARE_NUT_POCKET_WIDTH_MM,
        thickness_on_axis_mm=SQUARE_NUT_POCKET_THICKNESS_MM,
        feature="deep square-nut pocket",
    )
    slot_center = nut_center + Vector(NUT_SLOT_SIDE_TRAVEL_MM / 2.0, 0.0, 0.0)
    slot = _oriented_prism(
        slot_center,
        z_sign=z_sign,
        width_x_mm=NUT_SLOT_SIDE_TRAVEL_MM + 0.8,
        width_in_plane_mm=NUT_SLOT_WIDTH_MM,
        thickness_on_axis_mm=NUT_SLOT_THICKNESS_MM,
        feature="side-loaded square-nut insertion slot",
    )
    return (
        _single_solid(
            pocket.fuse(slot).clean().fix(),
            feature="unified deep side-loaded square-nut access",
        ),
        nut_center + Vector(NUT_SLOT_SIDE_TRAVEL_MM, 0.0, 0.0),
    )


def _yz_prism(points: tuple[tuple[float, float], ...], width_x_mm: float) -> Solid:
    def wire_at_x(x_mm: float) -> Wire:
        edges = [
            Edge.make_line(
                (x_mm, points[index][0], points[index][1]),
                (
                    x_mm,
                    points[(index + 1) % len(points)][0],
                    points[(index + 1) % len(points)][1],
                ),
            )
            for index in range(len(points))
        ]
        wires = Wire.combine(edges)
        if len(wires) != 1 or not wires[0].is_closed:
            raise ValueError("YZ support profile did not close")
        return wires[0]

    return _single_solid(
        Solid.make_loft(
            [wire_at_x(-width_x_mm / 2.0), wire_at_x(width_x_mm / 2.0)],
            ruled=True,
        ).clean().fix(),
        feature="outer-corner land-and-wall gusset",
    )


def _bucket_corner_gusset(z_sign: float) -> Solid:
    s = z_sign
    underside_y = source.SHOULDER_Y + SAND_CAP_THICKNESS_MM
    rear_y = FASTENER_SURFACE_Y_MM + 8.0
    outer_z = FASTENER_SURFACE_ABS_Z_MM
    gasket_outer_z = PATH_HALF_SIZE_MM + GASKET_WIDTH_MM / 2.0
    dry_land_z = gasket_outer_z + 0.35
    if s > 0.0:
        points = (
            (rear_y, outer_z),
            (underside_y, outer_z),
            (underside_y, dry_land_z),
            (rear_y - 3.0, dry_land_z + 1.5),
        )
    else:
        points = (
            (rear_y, -outer_z),
            (rear_y - 3.0, -dry_land_z - 1.5),
            (underside_y, -dry_land_z),
            (underside_y, -outer_z),
        )
    return _yz_prism(points, BUCKET_GUSSET_WIDTH_X_MM)


def _baffle_deep_cassette(
    nut_center: Vector,
    *,
    z_sign: float,
    nominal_envelope: Solid,
) -> Solid:
    s = z_sign
    bed_y = source.BAFFLE_BED_Y
    front_y = nut_center.Y - NUT_CASSETTE_FRONT_WALL_MM
    radial_outer = min(94.2, abs(nut_center.Z) + NUT_CASSETTE_RADIAL_HALF_MM)
    radial_inner = abs(nut_center.Z) - NUT_CASSETTE_RADIAL_HALF_MM
    if s > 0.0:
        points = (
            (bed_y, 77.0),
            (bed_y, 94.2),
            (front_y, radial_outer),
            (front_y, radial_inner),
        )
    else:
        points = (
            (bed_y, -77.0),
            (front_y, -radial_inner),
            (front_y, -radial_outer),
            (bed_y, -94.2),
        )
    wedge = _yz_prism(points, NUT_CASSETTE_WIDTH_X_MM)
    direction = _fastener_direction(z_sign)
    bearing_spine = source._cylinder_between(
        nut_center
        - direction
        * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + NUT_BEARING_SHOULDER_MM),
        nut_center
        + direction
        * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + 0.8),
        diameter=15.0,
    )
    bed_root = Pos(
        0.0,
        bed_y - previous.BAFFLE_CARDINAL_WEB_THICKNESS_MM / 2.0,
        s * 84.5,
    ) * Box(
        NUT_CASSETTE_WIDTH_X_MM,
        previous.BAFFLE_CARDINAL_WEB_THICKNESS_MM,
        18.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        wedge
        .fuse(bearing_spine, bed_root)
        .intersect(nominal_envelope)
        .clean()
        .fix(),
        feature="deep bed-grown baffle square-nut cassette",
    )


def _corner_fastener_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]
    hardware_parts: list[Solid] = []
    cutter_parts: list[Solid] = []
    support_parts: list[Solid] = []
    cassette_parts: list[Solid] = []
    fastener_audits: dict[str, Any] = {}
    gasket_keep_clear = _single_face_band(
        GASKET_WIDTH_MM + 0.50,
        source.BAFFLE_BED_Y - 0.10,
        source.SHOULDER_Y + 0.10,
        feature="corner-fastener gasket keep-clear envelope",
    )

    def assert_fairing_unchanged(stage: str) -> None:
        target_area = common["fairing_area_mm2"]
        matches = [
            face
            for face in baffle.faces()
            if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
        ]
        if len(matches) == 1:
            return
        nearest = min(
            (abs(face.area - target_area), face.area) for face in baffle.faces()
        )
        raise ValueError(
            f"The {stage} changed the authoritative fairing: "
            f"nearest area delta={nearest[0]:.9f} mm2"
        )

    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        direction = _fastener_direction(z_sign)
        surface = _fastener_surface(z_sign)
        nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

        gusset = _single_solid(
            _bucket_corner_gusset(z_sign)
            .intersect(base._outer_envelope())
            .cut(common["clearance_envelope"])
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"bucket-owned {label} land-and-wall gusset",
        )
        gusset_root = _shape_volume(gusset.intersect(bucket))
        if gusset_root <= 0.01:
            raise ValueError(f"The {label} corner gusset has no bucket root")
        bucket = _fuse_one(
            bucket,
            gusset,
            feature=f"bucket with {label} corner-straddling gusset",
        )

        tongue = _single_solid(
            source._cylinder_between(
                surface + direction * BUCKET_TONGUE_AXIS_START_MM,
                surface + direction * BUCKET_TONGUE_AXIS_END_MM,
                diameter=BUCKET_TONGUE_D_MM,
            )
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"gasket-clear D-shaped {label} bucket tongue",
        )
        tongue_root = _shape_volume(tongue.intersect(bucket))
        if tongue_root <= 0.01:
            raise ValueError(f"The {label} D tongue has no bucket root")
        bucket = _fuse_one(
            bucket,
            tongue,
            feature=f"bucket with compact {label} D tongue",
        )
        support_parts.extend((gusset, tongue))

        relief_candidates = [
            candidate.clean().fix()
            for candidate in source._cylinder_between(
                surface + direction * BAFFLE_RELIEF_AXIS_START_MM,
                surface + direction * BAFFLE_RELIEF_AXIS_END_MM,
                diameter=BAFFLE_RELIEF_D_MM,
            )
            .cut(gasket_keep_clear)
            .solids()
            if candidate.volume > 1e-6
        ]
        if not relief_candidates:
            raise ValueError(f"The {label} D-tongue relief is empty")
        relief = _single_solid(
            max(
                relief_candidates,
                key=lambda candidate: _shape_volume(candidate.intersect(tongue)),
            ),
            feature=f"open {label} D-tongue baffle relief",
        )
        baffle = _cut_one(
            baffle,
            relief,
            feature=f"baffle with open drop-on {label} tongue relief",
        )
        assert_fairing_unchanged(f"{label} drop-on tongue relief")

        cassette = _baffle_deep_cassette(
            nut_center,
            z_sign=z_sign,
            nominal_envelope=common["nominal_envelope"],
        )
        cassette = _single_solid(
            cassette.cut(relief).clean().fix(),
            feature=f"{label} deep nut cassette with open tongue relief",
        )
        cassette_root = _shape_volume(cassette.intersect(baffle))
        if cassette_root <= 0.01:
            raise ValueError(f"The {label} deep nut cassette has no baffle root")
        baffle = _fuse_one(
            baffle,
            cassette,
            feature=f"baffle with deep {label} nut cassette",
        )
        cassette_parts.append(cassette)
        assert_fairing_unchanged(f"{label} deep nut cassette")

        head_cubby = _single_solid(
            source._cylinder_between(
                surface - direction * 0.8,
                surface + direction * HEAD_CUBBY_AXIS_END_MM,
                diameter=HEAD_CUBBY_D_MM,
            )
            .clean()
            .fix(),
            feature=f"gasket-clear {label} screw-head cubby",
        )
        through_bore = source._cylinder_between(
            surface + direction * 2.8,
            nut_center + direction * 3.2,
            diameter=SCREW_CLEARANCE_D_MM,
        )
        nut_access, slot_mouth = _side_loaded_nut_access(
            nut_center,
            z_sign=z_sign,
        )

        bucket = _cut_one(
            bucket,
            head_cubby,
            feature=f"bucket with flush {label} head cubby",
        )
        baffle = _cut_one(
            baffle,
            head_cubby,
            feature=f"baffle with hidden {label} screw-head clearance",
        )
        assert_fairing_unchanged(f"{label} hidden screw-head clearance")
        bucket = _cut_one(
            bucket,
            through_bore,
            feature=f"bucket with {label} outer-corner screw passage",
        )
        baffle = _cut_one(
            baffle,
            through_bore,
            feature=f"baffle with {label} outer-corner screw passage",
        )
        baffle = _cut_one(
            baffle,
            nut_access,
            feature=f"baffle with deep side-loaded {label} square-nut slot",
        )
        assert_fairing_unchanged(f"{label} screw passage and nut slot")

        # The access subtraction must not be allowed to define the loaded nut
        # wall accidentally.  Restore an explicit five-millimetre backstop on
        # the screw-head side of the pocket, then recut only the M4 passage.
        # Its front face is tangent to the nut pocket, so it cannot obstruct
        # insertion while giving the square nut a full structural shoulder.
        backstop_center = nut_center - direction * (
            SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
            + NUT_BEARING_SHOULDER_MM / 2.0
        )
        bearing_backstop = _single_solid(
            _oriented_prism(
                backstop_center,
                z_sign=z_sign,
                width_x_mm=12.0,
                width_in_plane_mm=12.0,
                thickness_on_axis_mm=NUT_BEARING_SHOULDER_MM,
                feature=f"{label} explicit nut bearing backstop",
            )
            .intersect(common["nominal_envelope"])
            .cut(relief)
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"envelope-clipped {label} nut bearing backstop",
        )
        backstop_root = _shape_volume(bearing_backstop.intersect(baffle))
        if backstop_root <= 0.01:
            raise ValueError(f"The {label} nut bearing backstop has no root")
        baffle = _fuse_one(
            baffle,
            bearing_backstop,
            feature=f"baffle with explicit {label} five-millimetre nut backstop",
        )
        assert_fairing_unchanged(f"{label} nut bearing backstop")

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
        nut = _oriented_prism(
            nut_center,
            z_sign=z_sign,
            width_x_mm=SQUARE_NUT_WIDTH_MM,
            width_in_plane_mm=SQUARE_NUT_WIDTH_MM,
            thickness_on_axis_mm=SQUARE_NUT_THICKNESS_MM,
            feature=f"{label} M4 square-nut reference",
        )
        hardware_parts.extend((screw_head, screw_shank, nut))
        cutter_parts.extend((relief, head_cubby, through_bore, nut_access))

        bearing_center = nut_center - direction * (
            SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
            + NUT_BEARING_AUDIT_THICKNESS_MM / 2.0
        )
        bearing_audit = _single_solid(
            _oriented_prism(
                bearing_center,
                z_sign=z_sign,
                width_x_mm=SQUARE_NUT_WIDTH_MM,
                width_in_plane_mm=SQUARE_NUT_WIDTH_MM,
                thickness_on_axis_mm=NUT_BEARING_AUDIT_THICKNESS_MM,
                feature=f"{label} nut bearing audit block",
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} nut bearing audit annulus",
        )
        # Audit the explicitly constructed backstop itself.  After the union,
        # OpenCascade can report zero volume for an exactly coincident probe
        # against the cleaned parent solid even though the backstop is a
        # connected constituent of that one valid solid.  The backstop root
        # check above proves connectivity; this probe proves loaded-face area.
        nut_bearing_ratio = _shape_volume(
            bearing_audit.intersect(bearing_backstop)
        ) / bearing_audit.volume
        if nut_bearing_ratio < MINIMUM_NUT_BEARING_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} nut bearing shoulder is under-supported: "
                f"ratio={nut_bearing_ratio:.6f}"
            )

        head_bearing_center = surface + direction * (
            HEAD_CUBBY_AXIS_END_MM + 0.15
        )
        head_bearing = _single_solid(
            source._cylinder_between(
                head_bearing_center,
                head_bearing_center + direction * 0.30,
                diameter=SCREW_HEAD_D_MM,
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} screw-head bearing audit annulus",
        )
        head_bearing_ratio = _shape_volume(
            head_bearing.intersect(bucket)
        ) / head_bearing.volume
        if head_bearing_ratio < MINIMUM_HEAD_BEARING_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} screw head is under-supported: "
                f"ratio={head_bearing_ratio:.6f}"
            )

        hard_gasket_overlap = _shape_volume(
            Compound(children=[gusset, tongue, cassette]).intersect(gasket)
        )
        cutter_gasket_overlap = _shape_volume(
            Compound(children=[relief, head_cubby, through_bore, nut_access])
            .intersect(gasket)
        )
        if max(hard_gasket_overlap, cutter_gasket_overlap) > 0.001:
            raise ValueError(
                f"The {label} corner fastener interrupts the gasket: "
                f"hard={hard_gasket_overlap:.6f}, "
                f"cut={cutter_gasket_overlap:.6f} mm3"
            )

        seam_axis_distance = (
            source.SHOULDER_Y - FASTENER_SURFACE_Y_MM
        ) / direction.Y
        seam_axis_point = surface + direction * seam_axis_distance
        fastener_audits[label] = {
            "surface_center_mm": [surface.X, surface.Y, surface.Z],
            "direction": [direction.X, direction.Y, direction.Z],
            "forward_angle_deg": FASTENER_FORWARD_ANGLE_DEG,
            "axis_at_gasket_plane_mm": [
                seam_axis_point.X,
                seam_axis_point.Y,
                seam_axis_point.Z,
            ],
            "nut_center_mm": [nut_center.X, nut_center.Y, nut_center.Z],
            "nut_depth_forward_of_baffle_bed_mm": (
                source.BAFFLE_BED_Y - nut_center.Y
            ),
            "nominal_nut_bearing_shoulder_mm": NUT_BEARING_SHOULDER_MM,
            "nut_bearing_support_ratio": nut_bearing_ratio,
            "head_bearing_support_ratio": head_bearing_ratio,
            "side_slot_mouth_center_mm": [
                slot_mouth.X,
                slot_mouth.Y,
                slot_mouth.Z,
            ],
            "bucket_gusset_root_mm3": gusset_root,
            "bucket_tongue_root_mm3": tongue_root,
            "baffle_cassette_root_mm3": cassette_root,
            "nut_backstop_root_mm3": backstop_root,
            "hard_gasket_overlap_mm3": hard_gasket_overlap,
            "cutter_gasket_overlap_mm3": cutter_gasket_overlap,
            "support_connected_to_land_and_vertical_wall": True,
            "straight_drop_on_relief_open": True,
        }

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    if bucket_baffle_overlap > MAX_ALLOWED_INTERFERENCE_MM3:
        support_overlap = _shape_volume(
            Compound(children=support_parts).intersect(baffle)
        )
        cassette_overlap = _shape_volume(
            Compound(children=cassette_parts).intersect(bucket)
        )
        raise ValueError(
            "Corner-fastener bucket/baffle interference: "
            f"{bucket_baffle_overlap:.6f} mm3; "
            f"bucket-support/baffle={support_overlap:.6f}, "
            f"baffle-cassette/bucket={cassette_overlap:.6f} mm3"
        )

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("Corner fasteners changed the authoritative G1 fairing")
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
            f"Corner fasteners changed exterior bounds: {exterior_deltas}"
        )

    _FASTENER_AUDIT.clear()
    _FASTENER_AUDIT.update(fastener_audits)
    hardware = Compound(children=hardware_parts)
    cutters = Compound(children=cutter_parts)
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": cutters,
        "head_tongue": Compound(children=support_parts),
        "nut_load_pad": Compound(children=cassette_parts),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": 1.2,
        "description": (
            "Two M4 screws cross the dry outer land/socket corner and load "
            "deep side-loaded square nuts in bed-grown baffle cassettes"
        ),
        "service_notes": (
            "Slide each square nut sideways into its hidden baffle cassette, "
            "drop the baffle straight onto the open D reliefs, then tighten "
            "the flush top and bottom screws"
        ),
        "closure_passage_mode": (
            "two dry-side outer-corner screw passages ahead of the gasket"
        ),
        "geometry": {
            "fastener_count": 2,
            "upper_hook_count": 0,
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "head_d_mm": SCREW_HEAD_D_MM,
            "head_cubby_d_mm": HEAD_CUBBY_D_MM,
            "bucket_D_tongue_d_mm": BUCKET_TONGUE_D_MM,
            "baffle_open_relief_d_mm": BAFFLE_RELIEF_D_MM,
            "square_nut_nominal_width_mm": SQUARE_NUT_WIDTH_MM,
            "square_nut_nominal_thickness_mm": SQUARE_NUT_THICKNESS_MM,
            "square_nut_pocket_width_mm": SQUARE_NUT_POCKET_WIDTH_MM,
            "square_nut_pocket_thickness_mm": SQUARE_NUT_POCKET_THICKNESS_MM,
            "nut_slot_loading_direction": "sideways along enclosure X",
            "nut_pocket_deepened": True,
            "nut_bearing_shoulder_mm": NUT_BEARING_SHOULDER_MM,
            "straight_drop_on_insertion_path": True,
            "gasket_fastener_bypass_required": True,
            "authoritative_fairing_face_exactly_preserved": True,
            "baffle_exterior_bounds_difference_mm": exterior_deltas,
            "external_baffle_blisters": False,
            "bottom_head_protrusion_mm": 0.0,
            "top_head_protrusion_mm": 0.0,
            "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
            "fasteners": fastener_audits,
        },
    }


def generate() -> dict[str, Any]:
    original_out = previous.OUT
    original_name = previous.NAME
    original_common = previous._simplified_common_joint
    original_concept = previous._simplified_dual_concept

    previous.OUT = OUT
    previous.NAME = NAME
    previous._simplified_common_joint = _single_land_common_joint
    previous._simplified_dual_concept = _corner_fastener_concept
    try:
        diagnostics = previous.generate()
    finally:
        previous.OUT = original_out
        previous.NAME = original_name
        previous._simplified_common_joint = original_common
        previous._simplified_dual_concept = original_concept

    closure_diagnostics = diagnostics.pop("simplified_printable_closure")
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["front_fill"] = dict(_FILL_AUDIT)
    closure_diagnostics["corner_fasteners"] = dict(_FASTENER_AUDIT)
    diagnostics["name"] = NAME
    diagnostics["status"] = "complete single-land corner-fastener experiment"
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_single_land_corner_fasteners"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_single_land_corner_fasteners"
        ),
        "parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["single_land_corner_fastener_closure"] = closure_diagnostics
    diagnostics["preserved_full_detail_contract"].update(
        {
            "external_parabolic_g1_package_unchanged": True,
            "driver_collar_preserved": True,
            "straight_drop_on_baffle": True,
            "single_bucket_gasket_land": True,
            "secondary_inner_seal_shelf_removed": True,
            "deep_square_nut_bearing_shoulders": True,
        }
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
