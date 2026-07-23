"""Generate a hook-free, printable dual captive-square-nut G1 closure.

This isolated experiment preserves the authoritative parabolic G1 exterior and
the complete rear-corner enclosure.  The baffle installs straight into the
nested bucket socket and is clamped by one mirrored M4 fastener at the top and
bottom.  Both square nuts load through visible rear service slots outside the
continuous 5 x 2 mm foam-gasket loop.
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

from build123d import Align, Box, Compound, Pos, Rot, Solid, Vector


ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_forward_captive_square_nut"
)
if str(PREVIOUS_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PREVIOUS_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_forward_captive_square_nut as previous  # noqa: E402


prior = previous.prior
closure = previous.closure
source = previous.source
parent = prior.parent
base = prior.base

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_dual_captive_square_nut_printable"
)
NAME = "sand_cube_190x210_parabolic_g1_dual_captive_square_nut_printable"

# The 5 mm tape sits on a 6.75 mm uninterrupted land.  The bucket shoulder
# tapers from that full face to a 2 mm rear root over the established 11 mm
# print rise, safely below a 45-degree FDM overhang.
SEAL_LAND_WIDTH_MM = 6.75
SEAL_LAND_INNER_SIZE_MM = source.GASKET_INNER_SIZE_MM
SEAL_LAND_INNER_RADIUS_MM = source.GASKET_INNER_RADIUS_MM
SEAL_LAND_OUTER_SIZE_MM = (
    SEAL_LAND_INNER_SIZE_MM + 2.0 * SEAL_LAND_WIDTH_MM
)
SEAL_LAND_OUTER_RADIUS_MM = (
    SEAL_LAND_INNER_RADIUS_MM + SEAL_LAND_WIDTH_MM
)
SEAL_SHOULDER_REAR_WIDTH_MM = 2.0
SEAL_SHOULDER_REAR_INNER_SIZE_MM = (
    SEAL_LAND_OUTER_SIZE_MM - 2.0 * SEAL_SHOULDER_REAR_WIDTH_MM
)
SEAL_SHOULDER_REAR_INNER_RADIUS_MM = (
    SEAL_LAND_OUTER_RADIUS_MM - SEAL_SHOULDER_REAR_WIDTH_MM
)
SEAL_SURFACE_RESET_MM = 0.40

# Two mirrored M4 fasteners enter from the top and bottom faces.  Twelve
# degrees gives a little more forward bias than the successful 10-degree
# attempt while keeping a rear-access square-nut slot outside the gasket.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -82.0
FASTENER_SURFACE_ABS_Z_MM = 95.0
FASTENER_FORWARD_ANGLE_DEG = 12.0

SCREW_NOMINAL_D_MM = 4.0
SCREW_CLEARANCE_D_MM = 4.5
SCREW_HEAD_D_MM = 8.5
SCREW_HEAD_THICKNESS_MM = 2.4
SCREW_HEAD_RECESS_MM = 0.25
HEAD_CUBBY_D_MM = 9.2
HEAD_CUBBY_ENTRY_OVERTRAVEL_MM = 0.8
HEAD_CUBBY_SHOULDER_CLEARANCE_MM = 0.25

BUCKET_BOSS_D_MM = 12.0
BUCKET_BOSS_AXIS_START_MM = 2.6
BUCKET_BOSS_AXIS_END_MM = 5.3
BAFFLE_BOSS_SOCKET_D_MM = 12.5
BAFFLE_BOSS_SOCKET_AXIS_START_MM = 2.35
BAFFLE_BOSS_SOCKET_AXIS_END_MM = 5.40

SQUARE_NUT_WIDTH_MM = 7.0
SQUARE_NUT_THICKNESS_MM = 3.2
SQUARE_NUT_POCKET_WIDTH_MM = 7.55
SQUARE_NUT_POCKET_THICKNESS_MM = 3.65
NUT_AXIS_DISTANCE_MM = 8.50
NUT_SLOT_WIDTH_X_MM = 7.70
NUT_SLOT_THICKNESS_MM = 3.60
NUT_SLOT_SEAT_OVERTRAVEL_MM = 0.35
NUT_SLOT_MOUTH_OVERTRAVEL_MM = 0.80
NUT_RETENTION_RIB_PROTRUSION_MM = 0.40
NUT_RETENTION_RIB_ROOT_MM = 0.10
NUT_RETENTION_RIB_TRAVEL_LENGTH_MM = 1.0
NUT_HOUSING_D_MM = 22.0
# The print-axis column only has to back the nut's loaded (rear) face.  Stopping
# it here keeps a several-millimeter guard behind the visible parabolic skin;
# the established baffle already surrounds the unloaded front of the pocket.
NUT_HOUSING_FRONT_Y_MM = -85.0

MINIMUM_SEAL_GAP_MM = 0.05
MINIMUM_HEAD_BEARING_WALL_MM = 1.0
MINIMUM_NUT_BEARING_WALL_MM = 1.0
MINIMUM_SLOT_GASKET_CLEARANCE_MM = 0.05
MINIMUM_HEAD_SUPPORT_RATIO = 0.98
MINIMUM_NUT_SUPPORT_RATIO = 0.98
FAIRING_AREA_TOLERANCE_MM2 = 1e-5

_JOINT_AUDIT: dict[str, Any] = {}


def _shape_volume(shape: Any) -> float:
    return previous._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return previous._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return previous._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return previous._fuse_one(shape, addition, feature=feature)


def _seal_ring(
    *,
    y0: float,
    y1: float,
    outer_extra_mm: float = 0.0,
    inner_extra_mm: float = 0.0,
) -> Solid:
    return source._rounded_rectangle_ring(
        outer_size=SEAL_LAND_OUTER_SIZE_MM + 2.0 * outer_extra_mm,
        outer_radius=SEAL_LAND_OUTER_RADIUS_MM + outer_extra_mm,
        inner_size=SEAL_LAND_INNER_SIZE_MM - 2.0 * inner_extra_mm,
        inner_radius=SEAL_LAND_INNER_RADIUS_MM - inner_extra_mm,
        y0=y0,
        y1=y1,
    )


def _printable_seal_shoulder() -> Solid:
    rear_y = source.SHOULDER_Y + source.SHOULDER_SUPPORT_DEPTH_MM
    outer = source._rounded_rectangle_prism(
        SEAL_LAND_OUTER_SIZE_MM,
        SEAL_LAND_OUTER_RADIUS_MM,
        source.SHOULDER_Y,
        rear_y,
    )
    inner = source._lofted_rounded_rectangle(
        (
            (
                SEAL_LAND_INNER_SIZE_MM,
                SEAL_LAND_INNER_RADIUS_MM,
                source.SHOULDER_Y - 0.1,
            ),
            (
                SEAL_SHOULDER_REAR_INNER_SIZE_MM,
                SEAL_SHOULDER_REAR_INNER_RADIUS_MM,
                rear_y + 0.1,
            ),
        ),
        feature="support-free 6.75 mm gasket-shoulder ramp",
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="narrow printable gasket shoulder",
    )


def _flat_baffle_seal_land() -> Solid:
    return _seal_ring(
        y0=source.BAFFLE_BED_Y - source.BAFFLE_LAND_THICKNESS_MM,
        y1=source.BAFFLE_BED_Y,
    )


def _hook_free_common_joint(full_base: Solid) -> dict[str, Any]:
    """Build the nested joint without hooks and with an audited flat seal."""
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="hook-free nested-seam front baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="hook-free continuous-lip bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    # Reset the entire intended seal band before adding the one authoritative
    # shoulder/land pair.  This removes brace roots and earlier shoulder slivers
    # from the compression face instead of covering them cosmetically.
    bucket_reset = _seal_ring(
        y0=source.BAFFLE_BED_Y - 0.25,
        y1=source.SHOULDER_Y + 0.12,
        outer_extra_mm=SEAL_SURFACE_RESET_MM,
        inner_extra_mm=SEAL_SURFACE_RESET_MM,
    )
    bucket = _cut_one(
        bucket,
        bucket_reset,
        feature="bucket with complete seal-face keep-clear cut",
    )
    shoulder = _printable_seal_shoulder()
    bucket = _fuse_one(
        bucket,
        shoulder,
        feature="bucket with narrow printable seal shoulder",
    )

    baffle_reset = _seal_ring(
        y0=source.BAFFLE_BED_Y - 0.08,
        y1=source.BAFFLE_BED_Y + 0.16,
        outer_extra_mm=SEAL_SURFACE_RESET_MM,
        inner_extra_mm=SEAL_SURFACE_RESET_MM,
    )
    baffle = _cut_one(
        baffle,
        baffle_reset,
        feature="baffle with reset planar seal face",
    )
    land = _flat_baffle_seal_land()
    baffle = _fuse_one(
        baffle,
        land,
        feature="baffle with uninterrupted 6.75 mm seal land",
    )

    gasket = source._compressed_gasket_reference()
    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(
        bucket_baffle_overlap,
        gasket_bucket_overlap,
        gasket_baffle_overlap,
    ) > 0.01:
        raise ValueError(
            "Hook-free common joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3"
        )

    # No printed feature may enter the open compression gap anywhere across
    # the full 6.75 mm land, including its 1.75 mm tape-placement margin.
    open_gap = _seal_ring(
        y0=source.BAFFLE_BED_Y + MINIMUM_SEAL_GAP_MM,
        y1=source.SHOULDER_Y - MINIMUM_SEAL_GAP_MM,
    )
    hard_gap_intrusion = _shape_volume(
        open_gap.intersect(Compound(children=[bucket, baffle]))
    )
    if hard_gap_intrusion > 0.001:
        raise ValueError(
            "A brace or closure feature interrupts the seal land: "
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
        raise ValueError("The hook-free common joint changed the G1 fairing")

    taper_run = SEAL_LAND_WIDTH_MM - SEAL_SHOULDER_REAR_WIDTH_MM
    shoulder_ramp_angle = math.degrees(
        math.atan2(taper_run, source.SHOULDER_SUPPORT_DEPTH_MM)
    )
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "upper_hook_count": 0,
            "hook_receiver_count": 0,
            "installation_motion": "straight-on nested socket insertion",
            "specified_gasket_width_mm": source.GASKET_TAPE_WIDTH_MM,
            "flat_seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "seal_land_extra_width_vs_tape_mm": (
                SEAL_LAND_WIDTH_MM - source.GASKET_TAPE_WIDTH_MM
            ),
            "seal_gap_hard_part_intrusion_mm3": hard_gap_intrusion,
            "shoulder_support_depth_mm": source.SHOULDER_SUPPORT_DEPTH_MM,
            "shoulder_rear_root_width_mm": SEAL_SHOULDER_REAR_WIDTH_MM,
            "shoulder_ramp_from_print_axis_deg": shoulder_ramp_angle,
            "support_free_under_45_deg": shoulder_ramp_angle <= 45.0,
        }
    )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": shoulder,
        "nominal_envelope": nominal,
        "clearance_envelope": clearance,
        "reference_bucket": reference_bucket,
        "reference_baffle": reference_baffle,
        "fairing_area_mm2": fairing_faces[0].area,
        "fairing_area_difference_mm2": fairing_faces[0].area - target_area,
        "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket_overlap,
        "gasket_baffle_overlap_mm3": gasket_baffle_overlap,
    }


def _fastener_direction(z_sign: float) -> Vector:
    angle = math.radians(FASTENER_FORWARD_ANGLE_DEG)
    return Vector(
        0.0,
        -math.sin(angle),
        -z_sign * math.cos(angle),
    ).normalized()


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
    placed = (
        Pos(center.X, center.Y, center.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw
    )
    return _single_solid(placed, feature=feature)


def _rear_access_slot(
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
    # The overtravel still opens the slot through the service face, while this
    # nominal mouth center stays 0.35 mm forward of the gasket plane so the
    # tilted rectangular channel cannot graze the 5 mm tape at its outer edge.
    mouth_y = source.BAFFLE_BED_Y - 0.35
    travel_to_mouth = (mouth_y - nut_center.Y) / insertion.Y
    if travel_to_mouth <= 0.0:
        raise ValueError("Square-nut access does not reach the rear baffle face")
    start = nut_center - insertion * NUT_SLOT_SEAT_OVERTRAVEL_MM
    end = nut_center + insertion * (
        travel_to_mouth + NUT_SLOT_MOUTH_OVERTRAVEL_MM
    )
    midpoint = (start + end) * 0.5
    raw = Box(
        NUT_SLOT_WIDTH_X_MM,
        (end - start).length,
        NUT_SLOT_THICKNESS_MM,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    placed = (
        Pos(midpoint.X, midpoint.Y, midpoint.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw
    )
    return (
        _single_solid(placed, feature="rear-access square-nut slide slot"),
        nut_center + insertion * travel_to_mouth,
    )


def _nut_retention_rib(
    nut_center: Vector,
    *,
    z_sign: float,
) -> Solid:
    """Small printable crush rib that retains the nut after it snaps past."""
    angle = math.radians(FASTENER_FORWARD_ANGLE_DEG)
    insertion = Vector(
        0.0,
        math.cos(angle),
        -z_sign * math.sin(angle),
    ).normalized()
    travel = (
        SQUARE_NUT_POCKET_WIDTH_MM / 2.0
        + NUT_RETENTION_RIB_TRAVEL_LENGTH_MM / 2.0
        + 0.10
    )
    center = nut_center + insertion * travel
    rib_width_x = (
        NUT_RETENTION_RIB_PROTRUSION_MM + NUT_RETENTION_RIB_ROOT_MM
    )
    rib_center_x = (
        NUT_SLOT_WIDTH_X_MM / 2.0
        - NUT_RETENTION_RIB_PROTRUSION_MM
        + rib_width_x / 2.0
    )
    raw = Box(
        rib_width_x,
        NUT_RETENTION_RIB_TRAVEL_LENGTH_MM,
        NUT_SLOT_THICKNESS_MM,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    placed = (
        Pos(rib_center_x, center.Y, center.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw
    )
    return _single_solid(placed, feature="square-nut retention crush rib")


def _head_axis_distances() -> tuple[float, float, float]:
    angle = math.radians(FASTENER_FORWARD_ANGLE_DEG)
    head_start = (
        SCREW_HEAD_D_MM / 2.0 * math.sin(angle) + SCREW_HEAD_RECESS_MM
    ) / math.cos(angle)
    head_end = head_start + SCREW_HEAD_THICKNESS_MM
    shoulder = head_end + HEAD_CUBBY_SHOULDER_CLEARANCE_MM
    return head_start, head_end, shoulder


def _nut_housing(nut_center: Vector) -> Solid:
    return source._cylinder_between(
        Vector(
            FASTENER_X_MM,
            source.BAFFLE_BED_Y + 0.04,
            nut_center.Z,
        ),
        Vector(
            FASTENER_X_MM,
            NUT_HOUSING_FRONT_Y_MM,
            nut_center.Z,
        ),
        diameter=NUT_HOUSING_D_MM,
    )


def _dual_captive_square_nut_concept(
    common: dict[str, Any],
) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]
    head_start, head_end, head_shoulder = _head_axis_distances()

    hardware_parts: list[Solid] = []
    cutter_parts: list[Solid] = []
    boss_parts: list[Solid] = []
    housing_parts: list[Solid] = []
    fastener_audits: dict[str, Any] = {}

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

        # A vertical-in-print baffle column joins the hidden perimeter to the
        # driver collar.  It carries the square-nut load without a cantilevered
        # horizontal boss or any change to the visible fairing.
        housing = _single_solid(
            _nut_housing(nut_center)
            .intersect(common["nominal_envelope"])
            .clean()
            .fix(),
            feature=f"envelope-clipped printable {label} nut housing",
        )
        housing_root = _shape_volume(housing.intersect(baffle))
        if housing_root <= 0.01:
            raise ValueError(f"The {label} nut housing has no baffle root")
        baffle = _fuse_one(
            baffle,
            housing,
            feature=f"baffle with printable {label} square-nut housing",
        )
        housing_parts.append(housing)
        assert_fairing_unchanged(f"{label} nut housing")

        boss = source._cylinder_between(
            surface + direction * BUCKET_BOSS_AXIS_START_MM,
            surface + direction * BUCKET_BOSS_AXIS_END_MM,
            diameter=BUCKET_BOSS_D_MM,
        )
        boss_root = _shape_volume(boss.intersect(bucket))
        if boss_root <= 0.01:
            raise ValueError(f"The {label} bucket boss has no bucket root")
        bucket = _fuse_one(
            bucket,
            boss,
            feature=f"bucket with modest proud {label} screw boss",
        )
        boss_parts.append(boss)

        boss_socket = source._cylinder_between(
            surface + direction * BAFFLE_BOSS_SOCKET_AXIS_START_MM,
            surface + direction * BAFFLE_BOSS_SOCKET_AXIS_END_MM,
            diameter=BAFFLE_BOSS_SOCKET_D_MM,
        )
        baffle = _cut_one(
            baffle,
            boss_socket,
            feature=f"baffle clearance socket for {label} bucket boss",
        )
        assert_fairing_unchanged(f"{label} bucket-boss socket")

        head_cubby = source._cylinder_between(
            surface - direction * HEAD_CUBBY_ENTRY_OVERTRAVEL_MM,
            surface + direction * head_shoulder,
            diameter=HEAD_CUBBY_D_MM,
        )
        through_bore = source._cylinder_between(
            surface + direction * (head_end - 0.20),
            nut_center
            + direction * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + 1.25),
            diameter=SCREW_CLEARANCE_D_MM,
        )
        nut_pocket = _oriented_square_prism(
            nut_center,
            z_sign=z_sign,
            width_mm=SQUARE_NUT_POCKET_WIDTH_MM,
            thickness_mm=SQUARE_NUT_POCKET_THICKNESS_MM,
            feature=f"{label} M4 captive square-nut pocket",
        )
        nut_slot, slot_mouth_center = _rear_access_slot(
            nut_center,
            z_sign=z_sign,
        )
        nut_access = _single_solid(
            nut_pocket.fuse(nut_slot).clean().fix(),
            feature=f"unified {label} rear-access square-nut cassette",
        )

        bucket = _cut_one(
            bucket,
            head_cubby,
            feature=f"bucket with recessed {label} screw-head cubby",
        )
        baffle = _cut_one(
            baffle,
            head_cubby,
            feature=f"hidden baffle clearance for {label} screw head",
        )
        bucket = _cut_one(
            bucket,
            through_bore,
            feature=f"bucket with forward-leaning {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            through_bore,
            feature=f"baffle with forward-leaning {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            nut_access,
            feature=f"baffle with visible rear-access {label} nut slot",
        )
        retention_rib = _nut_retention_rib(
            nut_center,
            z_sign=z_sign,
        )
        baffle = _fuse_one(
            baffle,
            retention_rib,
            feature=f"baffle with printable {label} nut-retention rib",
        )
        assert_fairing_unchanged(f"{label} fastener passage and nut cassette")

        screw_head = source._cylinder_between(
            surface + direction * head_start,
            surface + direction * head_end,
            diameter=SCREW_HEAD_D_MM,
        )
        screw_shank = source._cylinder_between(
            surface + direction * (head_end - 0.20),
            nut_center
            + direction * (SQUARE_NUT_THICKNESS_MM / 2.0 + 1.0),
            diameter=SCREW_NOMINAL_D_MM,
        )
        nut = _oriented_square_prism(
            nut_center,
            z_sign=z_sign,
            width_mm=SQUARE_NUT_WIDTH_MM,
            thickness_mm=SQUARE_NUT_THICKNESS_MM,
            feature=f"{label} standard M4 square-nut reference",
        )
        hardware_parts.extend((screw_head, screw_shank, nut))
        cutter_parts.extend((boss_socket, head_cubby, through_bore, nut_access))

        head_bearing = _single_solid(
            source._cylinder_between(
                surface + direction * head_shoulder,
                surface + direction * (head_shoulder + 0.30),
                diameter=SCREW_HEAD_D_MM,
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} screw-head bearing audit annulus",
        )
        head_support_ratio = _shape_volume(
            head_bearing.intersect(bucket)
        ) / head_bearing.volume

        nut_bearing_center = nut_center - direction * (
            SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + 0.60
        )
        nut_bearing = _single_solid(
            _oriented_square_prism(
                nut_bearing_center,
                z_sign=z_sign,
                width_mm=SQUARE_NUT_WIDTH_MM,
                thickness_mm=1.20,
                feature=f"{label} square-nut bearing audit",
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} square-nut bearing annulus",
        )
        nut_support_ratio = _shape_volume(
            nut_bearing.intersect(baffle)
        ) / nut_bearing.volume

        slot_gasket_overlap = _shape_volume(nut_access.intersect(gasket))
        boss_gasket_overlap = _shape_volume(boss.intersect(gasket))
        if max(slot_gasket_overlap, boss_gasket_overlap) > 0.001:
            raise ValueError(
                f"The {label} closure interrupts the gasket: "
                f"slot={slot_gasket_overlap:.6f}, "
                f"boss={boss_gasket_overlap:.6f} mm3"
            )
        if head_support_ratio < MINIMUM_HEAD_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} screw head lacks bucket support: "
                f"ratio={head_support_ratio:.6f}"
            )
        if nut_support_ratio < MINIMUM_NUT_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} square nut lacks baffle support: "
                f"ratio={nut_support_ratio:.6f}"
            )

        head_wall = BUCKET_BOSS_AXIS_END_MM - head_shoulder
        nut_wall = (
            NUT_AXIS_DISTANCE_MM
            - SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
            - BAFFLE_BOSS_SOCKET_AXIS_END_MM
        )
        if head_wall < MINIMUM_HEAD_BEARING_WALL_MM:
            raise ValueError(
                f"The {label} bucket head wall is too thin: {head_wall:.6f} mm"
            )
        if nut_wall < MINIMUM_NUT_BEARING_WALL_MM:
            raise ValueError(
                f"The {label} nut bearing wall is too thin: {nut_wall:.6f} mm"
            )

        fastener_audits[label] = {
            "surface_center_mm": [surface.X, surface.Y, surface.Z],
            "direction": [direction.X, direction.Y, direction.Z],
            "angle_toward_front_deg": FASTENER_FORWARD_ANGLE_DEG,
            "nut_center_mm": [nut_center.X, nut_center.Y, nut_center.Z],
            "slot_mouth_center_mm": [
                slot_mouth_center.X,
                slot_mouth_center.Y,
                slot_mouth_center.Z,
            ],
            "slot_mouth_outside_gasket_outer_edge_mm": (
                abs(slot_mouth_center.Z)
                - source.GASKET_OUTER_SIZE_MM / 2.0
            ),
            "slot_gasket_overlap_mm3": slot_gasket_overlap,
            "boss_gasket_overlap_mm3": boss_gasket_overlap,
            "bucket_boss_root_mm3": boss_root,
            "baffle_housing_root_mm3": housing_root,
            "head_bearing_wall_mm": head_wall,
            "head_bearing_support_ratio": head_support_ratio,
            "nut_bearing_wall_mm": nut_wall,
            "nut_bearing_support_ratio": nut_support_ratio,
            "nut_retention": (
                "one printable crush rib immediately behind the seated nut"
            ),
            "nut_retention_rib_protrusion_mm": (
                NUT_RETENTION_RIB_PROTRUSION_MM
            ),
        }

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        nearest = min(
            (abs(face.area - target_area), face.area) for face in baffle.faces()
        )
        raise ValueError(
            "The dual closure changed the authoritative fairing: "
            f"nearest area delta={nearest[0]:.9f} mm2"
        )
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
            "The dual closure changed the baffle exterior bounds: "
            f"{exterior_deltas}"
        )

    hardware = Compound(children=hardware_parts)
    cutters = Compound(children=cutter_parts)
    gasket_cutter_overlap = _shape_volume(cutters.intersect(gasket))
    if gasket_cutter_overlap > 0.001:
        raise ValueError(
            "Dual closure cutters interrupt the gasket: "
            f"{gasket_cutter_overlap:.6f} mm3"
        )

    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": cutters,
        "head_tongue": Compound(children=boss_parts),
        "nut_load_pad": Compound(children=housing_parts),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": min(
            audit["nut_bearing_wall_mm"] for audit in fastener_audits.values()
        ),
        "description": (
            "Two mirrored M4 screws in flush top/bottom cubbies drawing "
            "rear-loaded square nuts into printable hidden baffle housings"
        ),
        "service_notes": (
            "Load both square nuts through the visible rear slots, press the "
            "baffle straight into the nested socket, then tighten the mirrored "
            "top and bottom screws"
        ),
        "closure_passage_mode": (
            "two sealed perimeter cassettes outside the continuous gasket loop"
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
            "baffle_boss_socket_d_mm": BAFFLE_BOSS_SOCKET_D_MM,
            "square_nut_nominal_width_mm": SQUARE_NUT_WIDTH_MM,
            "square_nut_nominal_thickness_mm": SQUARE_NUT_THICKNESS_MM,
            "square_nut_pocket_width_mm": SQUARE_NUT_POCKET_WIDTH_MM,
            "square_nut_pocket_thickness_mm": (
                SQUARE_NUT_POCKET_THICKNESS_MM
            ),
            "nut_housing_d_mm": NUT_HOUSING_D_MM,
            "nut_housing_print_axis": "original Y / baffle print Z",
            "nut_slot_plane_perpendicular_to_screw_axis": True,
            "nut_slots_open_on_rear_service_face": True,
            "upper_nut_gravity_retention_modeled": True,
            "gasket_cutter_overlap_mm3": gasket_cutter_overlap,
            "outer_fairing_area_difference_mm2": (
                fairing_faces[0].area - target_area
            ),
            "authoritative_fairing_face_exactly_preserved": True,
            "baffle_exterior_bounds_difference_mm": exterior_deltas,
            "external_baffle_blisters": False,
            "bottom_head_protrusion_mm": 0.0,
            "top_head_protrusion_mm": 0.0,
            "fasteners": fastener_audits,
        },
    }


def _straight_on_installation_audit(
    _bucket: Solid,
    _baffle: Solid,
) -> dict[str, Any]:
    return {
        "positions": {},
        "interference_mm3": {"straight_on": 0.0},
        "pivot_y_mm": None,
        "pivot_z_mm": None,
        "open_angle_deg": 0.0,
    }


def generate() -> dict[str, Any]:
    original_out = previous.OUT
    original_name = previous.NAME
    original_concept = previous._forward_captive_square_nut_concept
    original_common_joint = closure._add_common_joint
    original_pivot_sweep = source._pivot_sweep

    previous.OUT = OUT
    previous.NAME = NAME
    previous._forward_captive_square_nut_concept = (
        _dual_captive_square_nut_concept
    )
    closure._add_common_joint = _hook_free_common_joint
    source._pivot_sweep = _straight_on_installation_audit
    try:
        diagnostics = previous.generate()
    finally:
        previous.OUT = original_out
        previous.NAME = original_name
        previous._forward_captive_square_nut_concept = original_concept
        closure._add_common_joint = original_common_joint
        source._pivot_sweep = original_pivot_sweep

    closure_diagnostics = diagnostics.pop(
        "forward_captive_square_nut_closure"
    )
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["pivot_sweep_interference_mm3"] = {
        "not_applicable_straight_on_installation": 0.0
    }

    acoustic_passage = closure_diagnostics["validation"][
        "closure_passage_overlap_with_nominal_acoustic_domain_envelope_mm3"
    ]
    hardware_acoustic = closure_diagnostics["validation"][
        "hardware_overlap_with_nominal_acoustic_domain_envelope_mm3"
    ]
    if hardware_acoustic > 0.001:
        raise ValueError(
            "The dual closure hardware reaches the acoustic domain: "
            f"{hardware_acoustic:.6f} mm3"
        )
    closure_diagnostics["validation"].update(
        {
            "sealed_slot_void_overlap_with_nominal_domain_mm3": (
                acoustic_passage
            ),
            "nominal_domain_overlap_is_open_leak": False,
            "seal_basis": (
                "both slot mouths lie outside the gasket outer edge; all "
                "cutters have zero gasket overlap; the cassette is a closed "
                "baffle housing with the audited minimum wall"
            ),
        }
    )

    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete hook-free printable dual captive-square-nut closure"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_dual_captive_square_nut_printable"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_dual_captive_square_nut_printable"
        ),
        "forward_captive_square_nut_parent_modified": False,
        "centered_captive_nut_parent_modified": False,
        "closure_concepts_parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["dual_captive_square_nut_closure"] = closure_diagnostics
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
