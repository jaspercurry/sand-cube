"""Generate a forward-leaning centered closure for the nested G1 baffle.

This isolated experiment is a small mechanical revision of the committed
centered captive-nut concept.  The screw head moves rearward on the bucket
bottom and the screw leans forward into a rear-loaded square nut in the
baffle.  Unlike the previous concept, no portion of the authoritative outer
fairing is reassigned to the bucket: the visible baffle remains exact.
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
PRIOR_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_centered_captive_nut"
)
if str(PRIOR_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PRIOR_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_centered_captive_nut as prior  # noqa: E402


closure = prior.closure
source = prior.source
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_forward_captive_square_nut"
)
NAME = "sand_cube_190x210_parabolic_g1_forward_captive_square_nut"

# The sign is intentionally opposite the prior concept: as the screw rises
# from the bottom, its tip moves toward the front baffle (-Y).  Moving the head
# rearward keeps its cubby in bucket-owned material while the nut remains near
# the previous successful hidden baffle seat.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -81.00
FASTENER_SURFACE_Z_MM = -95.0
FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG = 10.0

SCREW_NOMINAL_D_MM = 4.0
SCREW_CLEARANCE_D_MM = 4.5
SCREW_HEAD_D_MM = 8.5
SCREW_HEAD_THICKNESS_MM = 2.4
SCREW_HEAD_BOTTOM_RECESS_MM = 0.25
SCREW_HEAD_AXIS_START_MM = (
    SCREW_HEAD_D_MM
    / 2.0
    * math.sin(
        math.radians(FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG)
    )
    + SCREW_HEAD_BOTTOM_RECESS_MM
) / math.cos(math.radians(FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG))
SCREW_HEAD_AXIS_END_MM = SCREW_HEAD_AXIS_START_MM + SCREW_HEAD_THICKNESS_MM

HEAD_CUBBY_D_MM = 9.0
HEAD_CUBBY_ENTRY_OVERTRAVEL_MM = 0.80
HEAD_CUBBY_SHOULDER_CLEARANCE_MM = 0.25
BAFFLE_HEAD_BEARING_CLEARANCE_MM = 0.45
BUCKET_SUPPORT_D_MM = 12.0
BUCKET_SUPPORT_AXIS_START_MM = SCREW_HEAD_AXIS_END_MM - 0.40
BUCKET_SUPPORT_AXIS_END_MM = 5.70

# A standard square-nut envelope is provisional until a purchased part is
# selected.  The straight rectangular slot is easier to load and inspect than
# the earlier edge-on hex pocket, while still positively preventing rotation.
SQUARE_NUT_WIDTH_MM = 7.0
SQUARE_NUT_THICKNESS_MM = 3.2
SQUARE_NUT_POCKET_WIDTH_MM = 7.5
SQUARE_NUT_POCKET_THICKNESS_MM = 3.6
NUT_AXIS_DISTANCE_MM = 9.0
NUT_ENTRY_SLOT_WIDTH_X_MM = 8.0
NUT_ENTRY_SLOT_DEPTH_Y_MM = 4.4
NUT_ENTRY_TOP_Z_MM = -78.40
NUT_LOAD_PAD_D_MM = 12.0
NUT_LOAD_PAD_AXIS_START_MM = 5.80

MINIMUM_GASKET_PLANE_CLEARANCE_MM = 0.18
MINIMUM_HEAD_RECESS_MM = 0.20
MINIMUM_HEAD_LOAD_WALL_MM = 1.50
MINIMUM_HEAD_BEARING_SUPPORT_RATIO = 0.98
MINIMUM_NUT_LOAD_WALL_MM = 1.35
MINIMUM_NUT_BEARING_SUPPORT_RATIO = 0.99
HEAD_BEARING_AUDIT_THICKNESS_MM = 0.30
NUT_BEARING_AUDIT_THICKNESS_MM = 1.5
MAXIMUM_NUT_ACCESS_ISLAND_MM3 = 500.0
FAIRING_AREA_TOLERANCE_MM2 = 1e-5


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return prior._single_solid(shape, feature=feature)


def _shape_volume(shape: Any) -> float:
    return prior._shape_volume(shape)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return prior._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return prior._fuse_one(shape, addition, feature=feature)


def _fastener_direction() -> Vector:
    angle = math.radians(FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG)
    return Vector(0.0, -math.sin(angle), math.cos(angle)).normalized()


def _fastener_surface() -> Vector:
    return Vector(
        FASTENER_X_MM,
        FASTENER_SURFACE_Y_MM,
        FASTENER_SURFACE_Z_MM,
    )


def _square_prism(
    center: Vector,
    *,
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
        * Rot(FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG, 0.0, 0.0)
        * raw
    )
    return _single_solid(placed, feature=feature)


def _head_cubby() -> Solid:
    direction = _fastener_direction()
    surface = _fastener_surface()
    return source._cylinder_between(
        surface - direction * HEAD_CUBBY_ENTRY_OVERTRAVEL_MM,
        surface
        + direction
        * (SCREW_HEAD_AXIS_END_MM + HEAD_CUBBY_SHOULDER_CLEARANCE_MM),
        diameter=HEAD_CUBBY_D_MM,
    )


def _cut_rear_loaded_nut_access(
    baffle: Solid,
    nut_access: Solid,
) -> tuple[Solid, dict[str, Any]]:
    result = baffle.cut(nut_access)
    solids = sorted(result.solids(), key=lambda item: item.volume, reverse=True)
    if not solids:
        raise ValueError("The square-nut access removed the baffle")
    primary = _single_solid(
        solids[0].clean().fix(),
        feature="primary baffle after rear-loaded square-nut access",
    )
    islands = solids[1:]
    island_volume = sum(item.volume for item in islands)
    access_bbox = nut_access.bounding_box()
    tolerance = 1e-4
    islands_inside_access_envelope = all(
        item.bounding_box().min.X >= access_bbox.min.X - tolerance
        and item.bounding_box().max.X <= access_bbox.max.X + tolerance
        and item.bounding_box().min.Y >= access_bbox.min.Y - tolerance
        and item.bounding_box().max.Y <= access_bbox.max.Y + tolerance
        and item.bounding_box().min.Z >= access_bbox.min.Z - tolerance
        and item.bounding_box().max.Z <= access_bbox.max.Z + tolerance
        for item in islands
    )
    if (
        island_volume > MAXIMUM_NUT_ACCESS_ISLAND_MM3
        or not islands_inside_access_envelope
    ):
        raise ValueError(
            "The square-nut slot detached unexpected baffle material: "
            f"count={len(islands)}, volume={island_volume:.6f} mm3"
        )
    return primary, {
        "detached_internal_island_count": len(islands),
        "detached_internal_island_volume_mm3": island_volume,
        "all_islands_inside_nut_access_envelope": (
            islands_inside_access_envelope
        ),
        "island_removal_is_intentional_slot_opening": True,
    }


def _forward_captive_square_nut_concept(
    common: dict[str, Any],
) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_baffle = copy.copy(baffle)
    direction = _fastener_direction()
    surface = _fastener_surface()
    nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

    head_cubby = _head_cubby()
    head_shoulder_distance = (
        SCREW_HEAD_AXIS_END_MM + HEAD_CUBBY_SHOULDER_CLEARANCE_MM
    )
    baffle_head_clearance = source._cylinder_between(
        surface - direction * HEAD_CUBBY_ENTRY_OVERTRAVEL_MM,
        surface
        + direction
        * (head_shoulder_distance + BAFFLE_HEAD_BEARING_CLEARANCE_MM),
        diameter=HEAD_CUBBY_D_MM,
    )
    through_bore = source._cylinder_between(
        surface + direction * (SCREW_HEAD_AXIS_END_MM - 0.25),
        nut_center
        + direction * (SQUARE_NUT_POCKET_THICKNESS_MM / 2.0 + 1.5),
        diameter=SCREW_CLEARANCE_D_MM,
    )
    nut_pocket = _square_prism(
        nut_center,
        width_mm=SQUARE_NUT_POCKET_WIDTH_MM,
        thickness_mm=SQUARE_NUT_POCKET_THICKNESS_MM,
        feature="M4 captive square-nut pocket",
    )
    nut_entry = closure._centered_box(
        NUT_ENTRY_SLOT_WIDTH_X_MM,
        nut_center.Y - NUT_ENTRY_SLOT_DEPTH_Y_MM / 2.0,
        nut_center.Y + NUT_ENTRY_SLOT_DEPTH_Y_MM / 2.0,
        nut_center.Z - 0.20,
        NUT_ENTRY_TOP_Z_MM,
        x=FASTENER_X_MM,
    )
    nut_access = _single_solid(
        nut_pocket.fuse(nut_entry).clean().fix(),
        feature="unified rear/top-loaded captive square-nut access",
    )

    # Clear the tiny concealed head-edge contact first.  The bucket support is
    # then allowed to occupy that newly hidden volume behind the counterbore
    # shoulder, producing a complete circular bearing face without borrowing
    # any part of the visible fairing.
    baffle = _cut_one(
        baffle,
        baffle_head_clearance,
        feature="hidden baffle clearance for the recessed screw head",
    )

    # Reinforcement is internal and bucket-owned only.  Subtracting the
    # unmodified baffle before fusion prevents the support from borrowing or
    # cutting any portion of the authoritative fairing.
    support_envelope = source._cylinder_between(
        surface + direction * BUCKET_SUPPORT_AXIS_START_MM,
        surface + direction * BUCKET_SUPPORT_AXIS_END_MM,
        diameter=BUCKET_SUPPORT_D_MM,
    )
    bottom_clip = closure._centered_box(
        BUCKET_SUPPORT_D_MM + 1.0,
        -90.0,
        closure.DRY_SIDE_REAR_LIMIT_Y - MINIMUM_GASKET_PLANE_CLEARANCE_MM,
        FASTENER_SURFACE_Z_MM + 0.05,
        -77.0,
        x=FASTENER_X_MM,
    )
    support_envelope = _single_solid(
        support_envelope.intersect(bottom_clip).clean().fix(),
        feature="clipped internal bucket head support envelope",
    )
    bucket_support_result = support_envelope.cut(baffle)
    bucket_support_solids = sorted(
        bucket_support_result.solids(),
        key=lambda item: item.volume,
        reverse=True,
    )
    if not bucket_support_solids:
        raise ValueError("The internal head support has no bucket-side piece")
    bucket_support = _single_solid(
        bucket_support_solids[0].clean().fix(),
        feature="bucket-owned internal head support",
    )
    bucket_support_root_mm3 = _shape_volume(bucket_support.intersect(bucket))
    if bucket_support_root_mm3 <= 0.01:
        raise ValueError("The internal head support has no bucket root")
    bucket = _fuse_one(
        bucket,
        bucket_support,
        feature="bucket with internal centered head support",
    )

    bucket = _cut_one(
        bucket,
        head_cubby,
        feature="bucket with rearward recessed underside head cubby",
    )
    bucket = _cut_one(
        bucket,
        through_bore,
        feature="forward-leaning bucket screw passage",
    )
    baffle = _cut_one(
        baffle,
        through_bore,
        feature="forward-leaning hidden baffle screw passage",
    )
    baffle, nut_access_audit = _cut_rear_loaded_nut_access(
        baffle, nut_access
    )

    nut_load_end = (
        NUT_AXIS_DISTANCE_MM - SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
    )
    nut_load_pad = _single_solid(
        source._cylinder_between(
            surface + direction * NUT_LOAD_PAD_AXIS_START_MM,
            surface + direction * nut_load_end,
            diameter=NUT_LOAD_PAD_D_MM,
        )
        .intersect(bottom_clip)
        .cut(through_bore, nut_access)
        .clean()
        .fix(),
        feature="pre-cut baffle square-nut load pad",
    )
    nut_load_pad_root_mm3 = _shape_volume(nut_load_pad.intersect(baffle))
    if nut_load_pad_root_mm3 <= 0.01:
        raise ValueError("The square-nut load pad has no baffle root")
    baffle = _fuse_one(
        baffle,
        nut_load_pad,
        feature="baffle with hidden square-nut load pad",
    )
    load_reference_baffle = copy.copy(baffle)

    # The screw is removed before opening.  Re-clear only the bucket's hidden
    # pivot volume; the visible baffle is never modified by this operation.
    bucket = closure._cut_concealed_pivot_sweep(bucket, baffle)

    screw_head = source._cylinder_between(
        surface + direction * SCREW_HEAD_AXIS_START_MM,
        surface + direction * SCREW_HEAD_AXIS_END_MM,
        diameter=SCREW_HEAD_D_MM,
    )
    screw_shank = source._cylinder_between(
        surface + direction * (SCREW_HEAD_AXIS_END_MM - 0.20),
        nut_center + direction * (SQUARE_NUT_THICKNESS_MM / 2.0 + 1.0),
        diameter=SCREW_NOMINAL_D_MM,
    )
    nut = _square_prism(
        nut_center,
        width_mm=SQUARE_NUT_WIDTH_MM,
        thickness_mm=SQUARE_NUT_THICKNESS_MM,
        feature="standard M4 square-nut reference",
    )
    hardware = Compound(children=[screw_head, screw_shank, nut])
    cutters = Compound(
        children=[
            head_cubby,
            baffle_head_clearance,
            through_bore,
            nut_access,
        ]
    )

    head_bearing_center = surface + direction * (
        head_shoulder_distance + HEAD_BEARING_AUDIT_THICKNESS_MM / 2.0
    )
    head_bearing_annulus = _single_solid(
        source._cylinder_between(
            head_bearing_center
            - direction * (HEAD_BEARING_AUDIT_THICKNESS_MM / 2.0),
            head_bearing_center
            + direction * (HEAD_BEARING_AUDIT_THICKNESS_MM / 2.0),
            diameter=SCREW_HEAD_D_MM,
        )
        .cut(through_bore)
        .clean()
        .fix(),
        feature="M4 screw-head bearing annulus",
    )
    supported_head_bearing_volume = _shape_volume(
        head_bearing_annulus.intersect(bucket)
    )
    head_bearing_support_ratio = (
        supported_head_bearing_volume / head_bearing_annulus.volume
    )

    nut_bearing_center = nut_center - direction * (
        SQUARE_NUT_POCKET_THICKNESS_MM / 2.0
        + NUT_BEARING_AUDIT_THICKNESS_MM / 2.0
    )
    nut_bearing_annulus = _single_solid(
        _square_prism(
            nut_bearing_center,
            width_mm=SQUARE_NUT_WIDTH_MM,
            thickness_mm=NUT_BEARING_AUDIT_THICKNESS_MM,
            feature="M4 square-nut bearing audit envelope",
        )
        .cut(through_bore)
        .clean()
        .fix(),
        feature="M4 square-nut bearing annulus",
    )
    supported_nut_bearing_volume = _shape_volume(
        nut_bearing_annulus.intersect(load_reference_baffle)
    )
    nut_bearing_support_ratio = (
        supported_nut_bearing_volume / nut_bearing_annulus.volume
    )

    head_recess = screw_head.bounding_box().min.Z - FASTENER_SURFACE_Z_MM
    gasket_plane_clearance = closure.DRY_SIDE_REAR_LIMIT_Y - max(
        cutters.bounding_box().max.Y,
        hardware.bounding_box().max.Y,
        bucket_support.bounding_box().max.Y,
        nut_load_pad.bounding_box().max.Y,
    )
    head_load_wall = BUCKET_SUPPORT_AXIS_END_MM - head_shoulder_distance
    nut_load_wall = nut_load_end - NUT_LOAD_PAD_AXIS_START_MM

    if head_recess < MINIMUM_HEAD_RECESS_MM:
        raise ValueError(
            "The forward-leaning screw head is not fully recessed: "
            f"recess={head_recess:.6f} mm"
        )
    if (
        gasket_plane_clearance + 1e-6
        < MINIMUM_GASKET_PLANE_CLEARANCE_MM
    ):
        raise ValueError(
            "The fastener reaches the gasket plane: "
            f"clearance={gasket_plane_clearance:.6f} mm"
        )
    if head_load_wall < MINIMUM_HEAD_LOAD_WALL_MM:
        raise ValueError(
            "The internal head support is too thin: "
            f"wall={head_load_wall:.6f} mm"
        )
    if head_bearing_support_ratio < MINIMUM_HEAD_BEARING_SUPPORT_RATIO:
        raise ValueError(
            "The screw head lacks bucket-owned bearing area: "
            f"ratio={head_bearing_support_ratio:.6f}"
        )
    if nut_load_wall < MINIMUM_NUT_LOAD_WALL_MM:
        raise ValueError(
            "The captive nut has insufficient material below its loaded "
            f"face: wall={nut_load_wall:.6f} mm"
        )
    if nut_bearing_support_ratio < MINIMUM_NUT_BEARING_SUPPORT_RATIO:
        raise ValueError(
            "The square nut lacks supported baffle bearing area: "
            f"ratio={nut_bearing_support_ratio:.6f}"
        )

    target_area = common["fairing_area_mm2"]
    exact_fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(exact_fairing_faces) != 1:
        nearest = min(
            (abs(face.area - target_area), face.area)
            for face in baffle.faces()
        )
        raise ValueError(
            "The forward closure changed the authoritative fairing; "
            f"nearest area delta={nearest[0]:.9f} mm2"
        )
    fairing_area_difference = exact_fairing_faces[0].area - target_area

    reference_bbox = reference_baffle.bounding_box()
    final_bbox = baffle.bounding_box()
    baffle_exterior_deltas = {
        "min_x": final_bbox.min.X - reference_bbox.min.X,
        "max_x": final_bbox.max.X - reference_bbox.max.X,
        "min_y": final_bbox.min.Y - reference_bbox.min.Y,
        "min_z": final_bbox.min.Z - reference_bbox.min.Z,
        "max_z": final_bbox.max.Z - reference_bbox.max.Z,
    }
    if max(abs(value) for value in baffle_exterior_deltas.values()) > 1e-5:
        raise ValueError(
            "The square-nut closure changes the baffle exterior bounds: "
            f"{baffle_exterior_deltas}"
        )

    gasket_overlap = _shape_volume(cutters.intersect(common["gasket"]))
    if gasket_overlap > 0.001:
        raise ValueError(
            "The forward fastener interrupts the gasket: "
            f"overlap={gasket_overlap:.6f} mm3"
        )

    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": common["gasket"],
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": cutters,
        "head_tongue": bucket_support,
        "nut_load_pad": nut_load_pad,
        "description": (
            "One centered M4 screw with a rearward flush head and a 10-degree "
            "forward lean into a rear/top-loaded captive square nut"
        ),
        "service_notes": (
            "Drop the square M4 nut down the hidden rear slot, engage the two "
            "top hooks, compress the gasket, then tighten the underside screw"
        ),
        "closure_passage_mode": (
            "single centered dry-side passage ahead of the continuous gasket"
        ),
        "geometry": {
            "fastener_count": 1,
            "fastener_x_mm": FASTENER_X_MM,
            "head_surface_y_mm": FASTENER_SURFACE_Y_MM,
            "forward_angle_from_bottom_normal_deg": (
                FASTENER_FORWARD_ANGLE_FROM_BOTTOM_NORMAL_DEG
            ),
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "head_d_mm": SCREW_HEAD_D_MM,
            "head_cubby_d_mm": HEAD_CUBBY_D_MM,
            "minimum_head_recess_below_bottom_mm": head_recess,
            "bucket_head_load_wall_mm": head_load_wall,
            "head_bearing_support_ratio": head_bearing_support_ratio,
            "square_nut_nominal_width_mm": SQUARE_NUT_WIDTH_MM,
            "square_nut_nominal_thickness_mm": SQUARE_NUT_THICKNESS_MM,
            "square_nut_pocket_width_mm": SQUARE_NUT_POCKET_WIDTH_MM,
            "square_nut_pocket_thickness_mm": (
                SQUARE_NUT_POCKET_THICKNESS_MM
            ),
            "nut_entry_direction": (
                "straight downward through hidden rear/top baffle slot"
            ),
            "nut_entry_slot_width_x_mm": NUT_ENTRY_SLOT_WIDTH_X_MM,
            "nut_entry_slot_depth_y_mm": NUT_ENTRY_SLOT_DEPTH_Y_MM,
            "minimum_material_below_loaded_nut_face_mm": nut_load_wall,
            "nut_bearing_support_ratio": nut_bearing_support_ratio,
            "tightening_load_drives_nut_deeper_into_closed_seat": True,
            "minimum_clearance_ahead_of_gasket_plane_mm": (
                gasket_plane_clearance
            ),
            "gasket_overlap_mm3": gasket_overlap,
            "outer_fairing_area_difference_mm2": fairing_area_difference,
            "authoritative_fairing_face_exactly_preserved": True,
            "local_fairing_ownership_reassignment_mm2": 0.0,
            "external_blisters": False,
            "bottom_head_protrusion_mm": 0.0,
            "bucket_support_root_mm3": bucket_support_root_mm3,
            "bucket_support_added_volume_mm3": (
                bucket_support.volume - bucket_support_root_mm3
            ),
            "nut_load_pad_root_mm3": nut_load_pad_root_mm3,
            "nut_load_pad_added_volume_mm3": (
                nut_load_pad.volume - nut_load_pad_root_mm3
            ),
            "nut_access_island_audit": nut_access_audit,
        },
    }


def generate() -> dict[str, Any]:
    original_out = prior.OUT
    original_name = prior.NAME
    original_concept = prior._centered_captive_nut_concept
    prior.OUT = OUT
    prior.NAME = NAME
    prior._centered_captive_nut_concept = _forward_captive_square_nut_concept
    try:
        diagnostics = prior.generate()
    finally:
        prior.OUT = original_out
        prior.NAME = original_name
        prior._centered_captive_nut_concept = original_concept

    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete forward-leaning captive square-nut closure experiment"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_forward_captive_square_nut"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_forward_captive_square_nut"
        ),
        "centered_captive_nut_parent_modified": False,
        "closure_concepts_parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["forward_captive_square_nut_closure"] = diagnostics.pop(
        "centered_captive_nut_closure"
    )
    diagnostics["forward_captive_square_nut_closure"][
        "authoritative_exterior_preserved"
    ] = True
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
