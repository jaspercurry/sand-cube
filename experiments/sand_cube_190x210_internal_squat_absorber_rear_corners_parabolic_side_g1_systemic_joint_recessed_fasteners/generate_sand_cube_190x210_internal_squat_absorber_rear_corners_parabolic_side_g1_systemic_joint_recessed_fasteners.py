"""Generate the systemic-diaphragm, recessed-fastener G1 closure.

The rear-corner absorber, parabolic G1 exterior, driver collar, port, braces,
fill routing, service tower, horn, and hardware remain inherited.  This
experiment replaces only the split front joint.  Each printed half receives
one continuous structural diaphragm instead of a collection of corner caps,
rings, and isolated webs.
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
from cad_runner.outputs import job_output_path


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_single_land_corner_fasteners"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_single_land_corner_fasteners as previous  # noqa: E402


source = previous.source
closure = previous.closure
base = previous.base
parent = previous.parent

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_systemic_joint_recessed_fasteners"
)
NAME = "sand_cube_190x210_parabolic_g1_systemic_joint_recessed_fasteners"

# One perimeter still owns the gasket reference, land, diaphragm opening, and
# printable bucket ramp.  There are no independent corner patches.
PATH_HALF_SIZE_MM = previous.PATH_HALF_SIZE_MM
SEAL_LAND_WIDTH_MM = previous.SEAL_LAND_WIDTH_MM
GASKET_WIDTH_MM = previous.GASKET_WIDTH_MM
GASKET_EDGE_MARGIN_MM = previous.GASKET_EDGE_MARGIN_MM
SAND_CAP_THICKNESS_MM = 3.0
BAFFLE_DIAPHRAGM_THICKNESS_MM = 3.0
BUCKET_DIAPHRAGM_OPENING_SIZE_MM = 160.0
BUCKET_DIAPHRAGM_OPENING_RADIUS_MM = 6.0
WALL_STACK_DIAPHRAGM_EXPANSION_MM = 1.0
DRIVER_COLLAR_OUTER_RADIUS_MM = 79.0
DRIVER_COLLAR_OVERLAP_MM = 1.0
BAFFLE_DIAPHRAGM_OPENING_RADIUS_MM = (
    DRIVER_COLLAR_OUTER_RADIUS_MM - DRIVER_COLLAR_OVERLAP_MM
)

# A conventional M4 pan/socket/cheese head up to 9.0 mm diameter fits the
# counterbore.  The screw crosses the dry 90-degree land/socket corner at the
# shallowest solved angle that retains a 6.5 mm-deep, fully backed nut seat
# without occupying the inherited nominal acoustic-domain envelope.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -72.0
FASTENER_SURFACE_ABS_Z_MM = 95.0
FASTENER_ANGLE_FROM_FACE_NORMAL_DEG = 48.0
NUT_AXIS_DISTANCE_MM = 14.0
SCREW_NOMINAL_D_MM = previous.SCREW_NOMINAL_D_MM
SCREW_CLEARANCE_D_MM = previous.SCREW_CLEARANCE_D_MM
SCREW_HEAD_REFERENCE_D_MM = 9.0
SCREW_HEAD_REFERENCE_THICKNESS_MM = 3.0
HEAD_COUNTERBORE_D_MM = 9.8
HEAD_COUNTERBORE_DEPTH_MM = 3.6
BUCKET_SLEEVE_D_MM = 12.5
BUCKET_SLEEVE_AXIS_START_MM = 3.35
BUCKET_SLEEVE_AXIS_END_MM = 8.5
BAFFLE_RELIEF_D_MM = 13.1
BAFFLE_RELIEF_AXIS_START_MM = 4.15
BAFFLE_RELIEF_AXIS_END_MM = 9.1
SQUARE_NUT_WIDTH_MM = previous.SQUARE_NUT_WIDTH_MM
SQUARE_NUT_THICKNESS_MM = previous.SQUARE_NUT_THICKNESS_MM
SQUARE_NUT_POCKET_WIDTH_MM = previous.SQUARE_NUT_POCKET_WIDTH_MM
SQUARE_NUT_POCKET_THICKNESS_MM = previous.SQUARE_NUT_POCKET_THICKNESS_MM
NUT_SLOT_WIDTH_MM = previous.NUT_SLOT_WIDTH_MM
NUT_SLOT_THICKNESS_MM = previous.NUT_SLOT_THICKNESS_MM
NUT_SLOT_SIDE_TRAVEL_MM = previous.NUT_SLOT_SIDE_TRAVEL_MM
NUT_CASSETTE_WIDTH_X_MM = 18.0
NUT_CASSETTE_FRONT_WALL_MM = previous.NUT_CASSETTE_FRONT_WALL_MM
NUT_CASSETTE_RADIAL_HALF_MM = 4.6
NUT_BEARING_SHOULDER_MM = previous.NUT_BEARING_SHOULDER_MM
NUT_BEARING_AUDIT_THICKNESS_MM = previous.NUT_BEARING_AUDIT_THICKNESS_MM
BUCKET_GUSSET_WIDTH_X_MM = 13.0

MAX_ALLOWED_INTERFERENCE_MM3 = previous.MAX_ALLOWED_INTERFERENCE_MM3
MINIMUM_GASKET_SUPPORT_RATIO = previous.MINIMUM_GASKET_SUPPORT_RATIO
MINIMUM_NUT_BEARING_SUPPORT_RATIO = previous.MINIMUM_NUT_BEARING_SUPPORT_RATIO
MINIMUM_HEAD_BEARING_SUPPORT_RATIO = 0.90
FAIRING_AREA_TOLERANCE_MM2 = previous.FAIRING_AREA_TOLERANCE_MM2

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


def _outer_slab(y0_mm: float, y1_mm: float, clip: Solid) -> Solid:
    y_mid = (y0_mm + y1_mm) / 2.0
    slab = Pos(0.0, y_mid, 0.0) * Box(
        base.P.cube_outer + 4.0,
        abs(y1_mm - y0_mm),
        base.P.cube_outer + 4.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        slab.intersect(clip).clean().fix(),
        feature="envelope-clipped systemic diaphragm slab",
    )


def _baffle_diaphragm(nominal_envelope: Solid) -> Solid:
    """One bed-contact plate joins the nested perimeter to the driver collar."""
    y0 = source.BAFFLE_BED_Y - BAFFLE_DIAPHRAGM_THICKNESS_MM
    y1 = source.BAFFLE_BED_Y
    slab = _outer_slab(y0, y1, nominal_envelope)
    opening = source._cylinder_between(
        Vector(0.0, y0 - 0.10, 0.0),
        Vector(0.0, y1 + 0.10, 0.0),
        diameter=2.0 * BAFFLE_DIAPHRAGM_OPENING_RADIUS_MM,
    )
    return _single_solid(
        slab.cut(opening).clean().fix(),
        feature="single continuous collar-to-perimeter baffle diaphragm",
    )


def _systemic_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="systemic nested-seam baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="systemic rear-bed bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    bucket = _cut_one(
        bucket,
        previous.previous._broad_interface_reset(
            source.BAFFLE_BED_Y - previous.BAFFLE_LAND_THICKNESS_MM - 0.15,
            source.SHOULDER_Y + 0.20,
        ),
        feature="bucket with inherited experimental joint removed",
    )

    gasket = previous._single_face_band(
        GASKET_WIDTH_MM,
        source.BAFFLE_BED_Y,
        source.SHOULDER_Y,
        feature="five-millimeter systemic gasket reference",
    )
    curved_land_seed = previous._single_face_band(
        SEAL_LAND_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM,
        feature="systemic diaphragm curved land seed",
    )
    bucket_diaphragm = curved_land_seed
    baffle_diaphragm = _baffle_diaphragm(nominal)
    live_sand_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    expanded_wall_stack = _single_solid(
        live_sand_void
        .offset_3d([], WALL_STACK_DIAPHRAGM_EXPANSION_MM)
        .clean()
        .fix(),
        feature="systemically expanded live wall-stack envelope",
    )
    wall_stack_slab = Pos(
        0.0,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        SAND_CAP_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    wall_stack_opening = source._rounded_rectangle_prism(
        BUCKET_DIAPHRAGM_OPENING_SIZE_MM,
        BUCKET_DIAPHRAGM_OPENING_RADIUS_MM,
        source.SHOULDER_Y - 0.10,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM + 0.10,
    )
    wall_stack_sheet = _single_solid(
        expanded_wall_stack
        .intersect(wall_stack_slab)
        .cut(wall_stack_opening)
        .clean()
        .fix(),
        feature="one expanded full wall-stack sealing diaphragm",
    )
    bucket_ramp = previous._unified_bucket_ramp()

    fill_passages: list[Solid] = []
    fill_supports: list[Solid] = []
    fill_audit: dict[str, Any] = {}
    centerline = previous._perimeter_wire(
        offset_mm=0.0,
        y_mm=source.SHOULDER_Y,
    )
    for x_sign, label in ((-1.0, "left"), (1.0, "right")):
        fill = previous.previous._front_fill_feature(x_sign)
        passage = fill["passage"]
        support = fill["support"]
        mouth = Vector(
            x_sign * previous.previous.FRONT_FILL_ABS_XZ_MM,
            source.SHOULDER_Y,
            previous.previous.FRONT_FILL_ABS_XZ_MM,
        )
        path_distance = min(edge.distance_to(mouth) for edge in centerline.edges())
        support_clearance = (
            path_distance
            - base.P.fill_entry_d / 2.0
            - previous.previous.FRONT_FILL_SUPPORT_WALL_MM
            - SEAL_LAND_WIDTH_MM / 2.0
        )
        if support_clearance < previous.FILL_TO_LAND_CLEARANCE_MM - 0.01:
            raise ValueError(
                f"The {label} fill support has only "
                f"{support_clearance:.3f} mm gasket-land clearance"
            )
        if float(fill["passage_to_void_mm3"]) <= 0.01:
            raise ValueError(f"The {label} fill passage misses the live sand void")
        fill_passages.append(passage)
        fill_supports.append(support)
        fill_audit[label] = {
            "mouth_center_mm": [mouth.X, mouth.Y, mouth.Z],
            "entry_diameter_mm": base.P.fill_entry_d,
            "support_wall_mm": previous.previous.FRONT_FILL_SUPPORT_WALL_MM,
            "support_to_seal_land_clearance_mm": support_clearance,
            "passage_to_live_sand_void_mm3": fill["passage_to_void_mm3"],
            "print_slope_from_axis_deg": fill["slope_deg"],
            "continuous_diaphragm_penetration": True,
        }

    passages = Compound(children=fill_passages)
    wall_stack_sheet = _single_solid(
        wall_stack_sheet.cut(passages).clean().fix(),
        feature="systemic full wall-stack sealing sheet",
    )
    bucket_diaphragm = _single_solid(
        bucket_diaphragm.cut(passages).clean().fix(),
        feature="systemic broad bucket sealing plate",
    )
    ramp_parts = bucket_ramp.cut(passages).clean().fix().solids()
    if not ramp_parts:
        raise ValueError("Fill passages consumed the systemic bucket ramp")
    for passage, support, label in zip(
        fill_passages,
        fill_supports,
        ("left", "right"),
    ):
        bucket = _cut_one(
            bucket,
            passage,
            feature=f"bucket with unobstructed {label} sand fill passage",
        )
        bucket = _fuse_one(
            bucket,
            support,
            feature=f"bucket diaphragm with hollow {label} fill support",
        )
    bucket = _fuse_one(
        bucket,
        wall_stack_sheet,
        feature="bucket with one continuous full wall-stack sheet",
    )
    bucket = _fuse_one(
        bucket,
        bucket_diaphragm,
        feature="bucket with one broad continuous gasket diaphragm",
    )
    for index, ramp_part in enumerate(ramp_parts, start=1):
        if _shape_volume(ramp_part.intersect(bucket)) <= 0.01:
            continue
        bucket = _fuse_one(
            bucket,
            ramp_part,
            feature=f"bucket with systemic printable ramp part {index}",
        )

    baffle = _fuse_one(
        baffle,
        baffle_diaphragm,
        feature="baffle with one continuous bed-side structural diaphragm",
    )

    gasket_probe = previous._single_face_band(
        GASKET_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + 0.25,
        feature="systemic gasket support probe",
    )
    gasket_support_ratio = _shape_volume(
        gasket_probe.intersect(bucket)
    ) / gasket_probe.volume
    if gasket_support_ratio < MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            f"Systemic gasket support ratio is {gasket_support_ratio:.6f}"
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
            "Systemic joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3"
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
        raise ValueError("Systemic diaphragms changed the authoritative G1 fairing")

    bucket_added_outside_envelope = _shape_volume(
        bucket_diaphragm.cut(base._outer_envelope())
    )
    if bucket_added_outside_envelope > 0.001:
        raise ValueError(
            "The bucket joint system exceeds the authoritative exterior by "
            f"{bucket_added_outside_envelope:.6f} mm3"
        )

    _FILL_AUDIT.clear()
    _FILL_AUDIT.update(fill_audit)
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "installation_motion": "straight drop-on along the split normal",
            "bucket_joint_system_count": 1,
            "baffle_joint_system_count": 1,
            "bucket_joint_constituents": [
                "expanded live wall-stack diaphragm",
                "single curved gasket land",
                "continuous bed-grown printable ramp",
            ],
            "corner_patch_count": 0,
            "isolated_baffle_web_count": 0,
            "bucket_diaphragm_thickness_mm": SAND_CAP_THICKNESS_MM,
            "baffle_diaphragm_thickness_mm": BAFFLE_DIAPHRAGM_THICKNESS_MM,
            "baffle_diaphragm_opening_diameter_mm": (
                2.0 * BAFFLE_DIAPHRAGM_OPENING_RADIUS_MM
            ),
            "driver_collar_overlap_mm": DRIVER_COLLAR_OVERLAP_MM,
            "seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "gasket_width_mm": GASKET_WIDTH_MM,
            "gasket_edge_margin_each_side_mm": GASKET_EDGE_MARGIN_MM,
            "gasket_bucket_support_ratio": gasket_support_ratio,
            "bucket_added_outside_authoritative_envelope_mm3": (
                bucket_added_outside_envelope
            ),
            "bucket_ramp_from_print_axis_deg": math.degrees(
                math.atan2(
                    SEAL_LAND_WIDTH_MM - previous.SEAL_RAMP_ROOT_WIDTH_MM,
                    previous.SEAL_RAMP_DEPTH_MM,
                )
            ),
            "bucket_ramp_root_width_mm": previous.SEAL_RAMP_ROOT_WIDTH_MM,
            "rear_fill_port_count": 0,
            "front_hidden_fill_port_count": 2,
        }
    )
    previous._FILL_AUDIT.clear()
    previous._FILL_AUDIT.update(_FILL_AUDIT)
    previous._JOINT_AUDIT.clear()
    previous._JOINT_AUDIT.update(_JOINT_AUDIT)

    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": Compound(
            children=[
                wall_stack_sheet,
                bucket_diaphragm,
                *ramp_parts,
                *fill_supports,
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
        "front_fill_passages": passages,
        "front_fill_supports": Compound(children=fill_supports),
        "bucket_diaphragm": bucket_diaphragm,
        "baffle_diaphragm": baffle_diaphragm,
    }


def _fastener_direction(z_sign: float) -> Vector:
    angle = math.radians(FASTENER_ANGLE_FROM_FACE_NORMAL_DEG)
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
        FASTENER_ANGLE_FROM_FACE_NORMAL_DEG
        if z_sign < 0.0
        else 180.0 - FASTENER_ANGLE_FROM_FACE_NORMAL_DEG
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
        feature="systemic square-nut pocket",
    )
    slot_center = nut_center + Vector(NUT_SLOT_SIDE_TRAVEL_MM / 2.0, 0.0, 0.0)
    slot = _oriented_prism(
        slot_center,
        z_sign=z_sign,
        width_x_mm=NUT_SLOT_SIDE_TRAVEL_MM + 0.8,
        width_in_plane_mm=NUT_SLOT_WIDTH_MM,
        thickness_on_axis_mm=NUT_SLOT_THICKNESS_MM,
        feature="systemic side-loaded square-nut slot",
    )
    return (
        _single_solid(
            pocket.fuse(slot).clean().fix(),
            feature="unified side-loaded square-nut access",
        ),
        nut_center + Vector(NUT_SLOT_SIDE_TRAVEL_MM, 0.0, 0.0),
    )


def _bucket_gusset(z_sign: float) -> Solid:
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
            (rear_y - 2.5, dry_land_z + 1.25),
        )
    else:
        points = (
            (rear_y, -outer_z),
            (rear_y - 2.5, -dry_land_z - 1.25),
            (underside_y, -dry_land_z),
            (underside_y, -outer_z),
        )
    return previous._yz_prism(points, BUCKET_GUSSET_WIDTH_X_MM)


def _baffle_nut_cassette(
    nut_center: Vector,
    *,
    z_sign: float,
    nominal_envelope: Solid,
) -> Solid:
    s = z_sign
    bed_y = source.BAFFLE_BED_Y
    front_y = nut_center.Y - NUT_CASSETTE_FRONT_WALL_MM
    radial_outer = min(94.0, abs(nut_center.Z) + NUT_CASSETTE_RADIAL_HALF_MM)
    radial_inner = abs(nut_center.Z) - NUT_CASSETTE_RADIAL_HALF_MM
    if s > 0.0:
        points = (
            (bed_y, 77.0),
            (bed_y, 94.0),
            (front_y, radial_outer),
            (front_y, radial_inner),
        )
    else:
        points = (
            (bed_y, -77.0),
            (front_y, -radial_inner),
            (front_y, -radial_outer),
            (bed_y, -94.0),
        )
    wedge = previous._yz_prism(points, NUT_CASSETTE_WIDTH_X_MM)
    direction = _fastener_direction(z_sign)
    spine = source._cylinder_between(
        nut_center
        - direction
        * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + NUT_BEARING_SHOULDER_MM),
        nut_center
        + direction
        * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + 0.8),
        diameter=BUCKET_SLEEVE_D_MM,
    )
    return _single_solid(
        wedge.fuse(spine).intersect(nominal_envelope).clean().fix(),
        feature="systemic bed-grown baffle nut cassette",
    )


def _recessed_fastener_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]
    hardware_parts: list[Solid] = []
    cutter_parts: list[Solid] = []
    support_parts: list[Solid] = []
    cassette_parts: list[Solid] = []
    fastener_audits: dict[str, Any] = {}
    gasket_keep_clear = previous._single_face_band(
        GASKET_WIDTH_MM + 0.50,
        source.BAFFLE_BED_Y - 0.10,
        source.SHOULDER_Y + 0.10,
        feature="systemic fastener gasket keep-clear envelope",
    )
    authoritative_outer = base._outer_envelope()

    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        direction = _fastener_direction(z_sign)
        surface = _fastener_surface(z_sign)
        nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

        gusset = _single_solid(
            _bucket_gusset(z_sign)
            .intersect(authoritative_outer)
            .cut(common["clearance_envelope"])
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"envelope-clipped {label} corner gusset",
        )
        sleeve = _single_solid(
            source._cylinder_between(
                surface + direction * BUCKET_SLEEVE_AXIS_START_MM,
                surface + direction * BUCKET_SLEEVE_AXIS_END_MM,
                diameter=BUCKET_SLEEVE_D_MM,
            )
            .intersect(authoritative_outer)
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"envelope-clipped {label} compact screw sleeve",
        )
        gusset_root = _shape_volume(gusset.intersect(bucket))
        sleeve_root = _shape_volume(sleeve.intersect(bucket))
        if min(gusset_root, sleeve_root) <= 0.01:
            raise ValueError(
                f"The {label} screw support is not fully rooted: "
                f"gusset={gusset_root:.6f}, sleeve={sleeve_root:.6f} mm3"
            )
        support = Compound(children=[gusset, sleeve])
        support_root = gusset_root + sleeve_root
        support_outside = _shape_volume(support.cut(authoritative_outer))
        if support_outside > 0.001:
            raise ValueError(
                f"The {label} screw support protrudes {support_outside:.6f} mm3"
            )
        bucket = _fuse_one(
            bucket,
            gusset,
            feature=f"bucket with internal {label} printable gusset",
        )
        bucket = _fuse_one(
            bucket,
            sleeve,
            feature=f"bucket with compact internal {label} screw sleeve",
        )
        support_parts.extend((gusset, sleeve))

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
            raise ValueError(f"The {label} straight-drop relief is empty")
        relief = _single_solid(
            max(
                relief_candidates,
                key=lambda candidate: _shape_volume(candidate.intersect(sleeve)),
            ),
            feature=f"open {label} compact-sleeve baffle relief",
        )
        baffle = _cut_one(
            baffle,
            relief,
            feature=f"baffle with open straight-drop {label} relief",
        )

        cassette = _baffle_nut_cassette(
            nut_center,
            z_sign=z_sign,
            nominal_envelope=common["nominal_envelope"],
        )
        cassette = _single_solid(
            cassette.cut(relief).clean().fix(),
            feature=f"{label} nut cassette with open assembly relief",
        )
        cassette_root = _shape_volume(cassette.intersect(baffle))
        if cassette_root <= 0.01:
            raise ValueError(f"The {label} nut cassette has no baffle root")
        baffle = _fuse_one(
            baffle,
            cassette,
            feature=f"baffle with bed-grown {label} nut cassette",
        )
        cassette_parts.append(cassette)

        head_counterbore = _single_solid(
            source._cylinder_between(
                surface - direction * 0.8,
                surface + direction * HEAD_COUNTERBORE_DEPTH_MM,
                diameter=HEAD_COUNTERBORE_D_MM,
            ).clean().fix(),
            feature=f"recessed {label} conventional-head counterbore",
        )
        through_bore = source._cylinder_between(
            surface + direction * (HEAD_COUNTERBORE_DEPTH_MM - 0.1),
            nut_center + direction * 3.2,
            diameter=SCREW_CLEARANCE_D_MM,
        )
        nut_access, slot_mouth = _side_loaded_nut_access(
            nut_center,
            z_sign=z_sign,
        )

        bucket = _cut_one(
            bucket,
            head_counterbore,
            feature=f"bucket with inward-only recessed {label} head pocket",
        )
        bucket = _cut_one(
            bucket,
            through_bore,
            feature=f"bucket with sealed dry-side {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            through_bore,
            feature=f"baffle with {label} screw passage",
        )
        baffle = _cut_one(
            baffle,
            nut_access,
            feature=f"baffle with side-loaded {label} square-nut access",
        )

        backstop_center = nut_center - direction * (
            SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
            + NUT_BEARING_SHOULDER_MM / 2.0
        )
        backstop = _single_solid(
            _oriented_prism(
                backstop_center,
                z_sign=z_sign,
                width_x_mm=11.0,
                width_in_plane_mm=11.0,
                thickness_on_axis_mm=NUT_BEARING_SHOULDER_MM,
                feature=f"{label} nut bearing backstop",
            )
            .intersect(common["nominal_envelope"])
            .cut(relief)
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"envelope-clipped {label} nut backstop",
        )
        backstop_root = _shape_volume(backstop.intersect(baffle))
        if backstop_root <= 0.01:
            raise ValueError(f"The {label} nut backstop has no baffle root")
        baffle = _fuse_one(
            baffle,
            backstop,
            feature=f"baffle with structural {label} nut backstop",
        )

        screw_head = source._cylinder_between(
            surface + direction * 0.25,
            surface
            + direction
            * (0.25 + SCREW_HEAD_REFERENCE_THICKNESS_MM),
            diameter=SCREW_HEAD_REFERENCE_D_MM,
        )
        screw_shank = source._cylinder_between(
            surface + direction * HEAD_COUNTERBORE_DEPTH_MM,
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
        cutter_parts.extend((relief, head_counterbore, through_bore, nut_access))

        bearing_center = nut_center - direction * (
            SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
            + NUT_BEARING_AUDIT_THICKNESS_MM / 2.0
        )
        bearing_probe = _single_solid(
            _oriented_prism(
                bearing_center,
                z_sign=z_sign,
                width_x_mm=SQUARE_NUT_WIDTH_MM,
                width_in_plane_mm=SQUARE_NUT_WIDTH_MM,
                thickness_on_axis_mm=NUT_BEARING_AUDIT_THICKNESS_MM,
                feature=f"{label} nut bearing probe",
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} nut bearing audit annulus",
        )
        nut_bearing_ratio = _shape_volume(
            bearing_probe.intersect(backstop)
        ) / bearing_probe.volume
        if nut_bearing_ratio < MINIMUM_NUT_BEARING_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} nut bearing support ratio is "
                f"{nut_bearing_ratio:.6f}"
            )

        head_bearing_center = surface + direction * (
            HEAD_COUNTERBORE_DEPTH_MM + 0.15
        )
        head_bearing_probe = _single_solid(
            source._cylinder_between(
                head_bearing_center,
                head_bearing_center + direction * 0.30,
                diameter=SCREW_HEAD_REFERENCE_D_MM,
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} screw-head bearing probe",
        )
        head_bearing_ratio = _shape_volume(
            head_bearing_probe.intersect(bucket)
        ) / head_bearing_probe.volume
        if head_bearing_ratio < MINIMUM_HEAD_BEARING_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} head bearing support ratio is "
                f"{head_bearing_ratio:.6f}"
            )

        hard_gasket_overlap = _shape_volume(
            Compound(children=[support, cassette, backstop]).intersect(gasket)
        )
        cutter_gasket_overlap = _shape_volume(
            Compound(
                children=[relief, head_counterbore, through_bore, nut_access]
            ).intersect(gasket)
        )
        if max(hard_gasket_overlap, cutter_gasket_overlap) > 0.001:
            raise ValueError(
                f"The {label} fastener interrupts the gasket: "
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
            "angle_from_face_normal_deg": FASTENER_ANGLE_FROM_FACE_NORMAL_DEG,
            "axis_at_gasket_plane_mm": [
                seam_axis_point.X,
                seam_axis_point.Y,
                seam_axis_point.Z,
            ],
            "nut_center_mm": [nut_center.X, nut_center.Y, nut_center.Z],
            "nut_depth_forward_of_baffle_bed_mm": (
                source.BAFFLE_BED_Y - nut_center.Y
            ),
            "head_capacity_d_mm": SCREW_HEAD_REFERENCE_D_MM,
            "head_counterbore_d_mm": HEAD_COUNTERBORE_D_MM,
            "head_counterbore_depth_mm": HEAD_COUNTERBORE_DEPTH_MM,
            "bucket_sleeve_d_mm": BUCKET_SLEEVE_D_MM,
            "support_outside_authoritative_envelope_mm3": support_outside,
            "bucket_support_root_mm3": support_root,
            "baffle_cassette_root_mm3": cassette_root,
            "nut_backstop_root_mm3": backstop_root,
            "nut_bearing_support_ratio": nut_bearing_ratio,
            "head_bearing_support_ratio": head_bearing_ratio,
            "side_slot_mouth_center_mm": [
                slot_mouth.X,
                slot_mouth.Y,
                slot_mouth.Z,
            ],
            "hard_gasket_overlap_mm3": hard_gasket_overlap,
            "cutter_gasket_overlap_mm3": cutter_gasket_overlap,
            "support_connected_to_land_and_vertical_wall": True,
            "straight_drop_on_relief_open": True,
        }

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    if bucket_baffle_overlap > MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            "Recessed-fastener bucket/baffle interference is "
            f"{bucket_baffle_overlap:.6f} mm3"
        )

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("Recessed fasteners changed the authoritative G1 fairing")

    reference_bbox = reference_baffle.bounding_box()
    final_bbox = baffle.bounding_box()
    baffle_exterior_deltas = {
        "min_x": final_bbox.min.X - reference_bbox.min.X,
        "max_x": final_bbox.max.X - reference_bbox.max.X,
        "min_y": final_bbox.min.Y - reference_bbox.min.Y,
        "max_y": final_bbox.max.Y - reference_bbox.max.Y,
        "min_z": final_bbox.min.Z - reference_bbox.min.Z,
        "max_z": final_bbox.max.Z - reference_bbox.max.Z,
    }
    reference_bucket_bbox = reference_bucket.bounding_box()
    final_bucket_bbox = bucket.bounding_box()
    bucket_exterior_deltas = {
        "min_x": final_bucket_bbox.min.X - reference_bucket_bbox.min.X,
        "max_x": final_bucket_bbox.max.X - reference_bucket_bbox.max.X,
        "min_y": final_bucket_bbox.min.Y - reference_bucket_bbox.min.Y,
        "max_y": final_bucket_bbox.max.Y - reference_bucket_bbox.max.Y,
        "min_z": final_bucket_bbox.min.Z - reference_bucket_bbox.min.Z,
        "max_z": final_bucket_bbox.max.Z - reference_bucket_bbox.max.Z,
    }
    if max(abs(value) for value in bucket_exterior_deltas.values()) > 1e-5:
        raise ValueError(
            "Recessed fasteners changed bucket exterior bounds: "
            f"{bucket_exterior_deltas}"
        )

    _FASTENER_AUDIT.clear()
    _FASTENER_AUDIT.update(fastener_audits)
    previous._FASTENER_AUDIT.clear()
    previous._FASTENER_AUDIT.update(_FASTENER_AUDIT)
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
            "Two recessed M4 screws cross the dry land/socket corners and "
            "load side-inserted square nuts in the baffle diaphragm"
        ),
        "service_notes": (
            "Load the two square nuts from the hidden side, drop the baffle "
            "straight onto the compact reliefs, then tighten the recessed "
            "top and bottom screws"
        ),
        "closure_passage_mode": (
            "two sealed dry-side corner passages outside the gasket"
        ),
        "geometry": {
            "fastener_count": 2,
            "upper_hook_count": 0,
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "maximum_reference_head_d_mm": SCREW_HEAD_REFERENCE_D_MM,
            "head_counterbore_d_mm": HEAD_COUNTERBORE_D_MM,
            "head_counterbore_depth_mm": HEAD_COUNTERBORE_DEPTH_MM,
            "bucket_sleeve_d_mm": BUCKET_SLEEVE_D_MM,
            "baffle_open_relief_d_mm": BAFFLE_RELIEF_D_MM,
            "square_nut_nominal_width_mm": SQUARE_NUT_WIDTH_MM,
            "square_nut_nominal_thickness_mm": SQUARE_NUT_THICKNESS_MM,
            "square_nut_pocket_width_mm": SQUARE_NUT_POCKET_WIDTH_MM,
            "square_nut_pocket_thickness_mm": SQUARE_NUT_POCKET_THICKNESS_MM,
            "nut_slot_loading_direction": "sideways along enclosure X",
            "straight_drop_on_insertion_path": True,
            "authoritative_fairing_face_exactly_preserved": True,
            "baffle_exterior_bounds_difference_mm": baffle_exterior_deltas,
            "bucket_exterior_bounds_difference_mm": bucket_exterior_deltas,
            "external_bucket_humps": False,
            "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
            "fasteners": fastener_audits,
        },
    }


def generate() -> dict[str, Any]:
    original_out = previous.OUT
    original_name = previous.NAME
    original_common = previous._single_land_common_joint
    original_concept = previous._corner_fastener_concept
    simplified = previous.previous
    centered = simplified.centered
    original_configure_viewer = centered._configure_viewer

    def configure_staged_viewer(
        viewer_dir: Path,
        *,
        cutaway: bool,
    ) -> None:
        original_configure_viewer(
            job_output_path(viewer_dir),
            cutaway=cutaway,
        )

    previous.OUT = OUT
    previous.NAME = NAME
    previous._single_land_common_joint = _systemic_common_joint
    previous._corner_fastener_concept = _recessed_fastener_concept
    centered._configure_viewer = configure_staged_viewer
    try:
        diagnostics = previous.generate()
    finally:
        previous.OUT = original_out
        previous.NAME = original_name
        previous._single_land_common_joint = original_common
        previous._corner_fastener_concept = original_concept
        centered._configure_viewer = original_configure_viewer

    closure_diagnostics = diagnostics.pop("single_land_corner_fastener_closure")
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["front_fill"] = dict(_FILL_AUDIT)
    closure_diagnostics["corner_fasteners"] = dict(_FASTENER_AUDIT)
    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete systemic-diaphragm recessed-fastener experiment"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_systemic_joint_recessed_fasteners"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_systemic_joint_recessed_fasteners"
        ),
        "parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics[
        "systemic_joint_recessed_fastener_closure"
    ] = closure_diagnostics
    diagnostics["preserved_full_detail_contract"].update(
        {
            "external_parabolic_g1_package_unchanged": True,
            "driver_collar_preserved": True,
            "straight_drop_on_baffle": True,
            "single_continuous_bucket_diaphragm": True,
            "single_continuous_baffle_diaphragm": True,
            "corner_seal_patch_count": 0,
            "recessed_head_pockets_inside_original_exterior": True,
        }
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
