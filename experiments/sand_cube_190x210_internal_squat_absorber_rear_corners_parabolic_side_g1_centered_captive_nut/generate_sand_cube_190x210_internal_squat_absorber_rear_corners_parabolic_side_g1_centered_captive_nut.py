"""Generate a centered captive-nut closure for the nested G1 baffle.

The committed nested-seam concept set remains unchanged.  This isolated
experiment keeps the authoritative unsplit parabolic exterior, the continuous
5 x 2 mm gasket, and the two concealed upper hooks.  One centered M4 screw
enters through a flush underside cubby and draws a top-loaded captive hex nut
deeper into a hidden baffle seat.  The complete passage stays on the dry side
of the gasket loop.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from build123d import (
    Compound,
    Pos,
    RegularPolygon,
    Rot,
    Solid,
    Unit,
    Vector,
    export_step,
    extrude,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_nested_seam_closure_concepts"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts as closure  # noqa: E402


source = closure.source
parent = closure.parent
base = closure.base
cad = closure.cad
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_centered_captive_nut"
)
NAME = "sand_cube_190x210_parabolic_g1_centered_captive_nut"

# One centered M4 screw.  The angle is measured from the bottom-face normal.
# A shallow 10-degree rearward path makes the underside counterbore nearly
# circular and puts the captive nut in thicker hidden baffle material.  A
# short bucket tongue owns the complete screw-head bearing face.
FASTENER_X_MM = 0.0
FASTENER_SURFACE_Y_MM = -84.50
FASTENER_SURFACE_Z_MM = -95.0
FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG = 10.0
SCREW_NOMINAL_D_MM = 4.0
SCREW_CLEARANCE_D_MM = 4.5
SCREW_HEAD_D_MM = 8.5
SCREW_HEAD_THICKNESS_MM = 2.4
SCREW_HEAD_BOTTOM_RECESS_MM = 0.25
SCREW_HEAD_AXIS_START_MM = (
    SCREW_HEAD_D_MM
    / 2.0
    * math.sin(math.radians(FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG))
    + SCREW_HEAD_BOTTOM_RECESS_MM
) / math.cos(math.radians(FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG))
SCREW_HEAD_AXIS_END_MM = (
    SCREW_HEAD_AXIS_START_MM + SCREW_HEAD_THICKNESS_MM
)

# A true angled flat-bottom counterbore gives the screw head a perpendicular
# bearing shoulder.  At ten degrees its underside opening is visually almost
# circular while the head remains fully below the flat bottom face.
HEAD_CUBBY_D_MM = 9.2
HEAD_CUBBY_ENTRY_OVERTRAVEL_MM = 0.80
HEAD_CUBBY_SHOULDER_CLEARANCE_MM = 0.25

# The local interface doglegs around the head: this hidden tongue reassigns
# existing shell material to the bucket, rather than adding an exterior boss.
# It ends before the baffle-owned captive-nut load face.  A small diametral and
# axial clearance lets the baffle pivot without creating a visible front wart.
BUCKET_HEAD_TONGUE_D_MM = 13.0
BUCKET_HEAD_TONGUE_ENTRY_OVERTRAVEL_MM = 0.60
BUCKET_HEAD_TONGUE_END_MM = 5.40
BUCKET_HEAD_TONGUE_CLEARANCE_D_MM = 13.5
BUCKET_HEAD_TONGUE_CLEARANCE_END_MM = 5.60

# Standard M4 hex-nut envelope and FDM fit allowance.  Across-flats dimensions
# are used so the pocket prevents rotation without relying on friction.
NUT_AF_MM = 7.0
NUT_THICKNESS_MM = 3.2
NUT_POCKET_AF_MM = 7.4
NUT_POCKET_THICKNESS_MM = 3.6
NUT_AXIS_DISTANCE_MM = 9.0
NUT_ENTRY_SLOT_WIDTH_X_MM = 8.8
NUT_ENTRY_SLOT_DEPTH_Y_MM = 4.0
NUT_ENTRY_TOP_Z_MM = -78.40
NUT_LOAD_PAD_D_MM = 12.0
NUT_LOAD_PAD_TONGUE_GAP_MM = 0.10

MINIMUM_TARGET_DRY_SIDE_CLEARANCE_MM = 2.0
MINIMUM_HEAD_RECESS_MM = 0.20
MINIMUM_HEAD_LOAD_WALL_MM = 1.5
MINIMUM_NUT_LOAD_WALL_MM = 1.4
HEAD_BEARING_AUDIT_THICKNESS_MM = 1.0
MINIMUM_HEAD_BEARING_SUPPORT_RATIO = 0.98
NUT_BEARING_AUDIT_THICKNESS_MM = 1.5
MINIMUM_NUT_BEARING_SUPPORT_RATIO = 0.99
MAXIMUM_NUT_ACCESS_ISLAND_MM3 = 500.0
MAXIMUM_LOCAL_FAIRING_REASSIGNMENT_MM2 = 150.0


def _is_valid(shape: Any) -> bool:
    return closure._is_valid(shape)


def _shape_volume(shape: Any) -> float:
    return closure._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return closure._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return closure._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return closure._fuse_one(shape, addition, feature=feature)


def _fastener_direction() -> Vector:
    angle = math.radians(FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG)
    return Vector(0.0, math.sin(angle), math.cos(angle)).normalized()


def _fastener_surface() -> Vector:
    return Vector(
        FASTENER_X_MM,
        FASTENER_SURFACE_Y_MM,
        FASTENER_SURFACE_Z_MM,
    )


def _hex_prism(
    center: Vector,
    *,
    across_flats_mm: float,
    thickness_mm: float,
    feature: str,
) -> Solid:
    circumradius = across_flats_mm / math.sqrt(3.0)
    sketch = RegularPolygon(
        circumradius,
        6,
        major_radius=True,
        rotation=30.0,
    )
    raw = _single_solid(
        extrude(sketch, amount=thickness_mm / 2.0, both=True),
        feature=feature,
    )
    angle_x = -FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG
    return _single_solid(
        Pos(center.X, center.Y, center.Z) * Rot(angle_x, 0.0, 0.0) * raw,
        feature=feature,
    )


def _head_cubby() -> Solid:
    direction = _fastener_direction()
    surface = _fastener_surface()
    return source._cylinder_between(
        surface - direction * HEAD_CUBBY_ENTRY_OVERTRAVEL_MM,
        surface
        + direction
        * (
            SCREW_HEAD_AXIS_END_MM
            + HEAD_CUBBY_SHOULDER_CLEARANCE_MM
        ),
        diameter=HEAD_CUBBY_D_MM,
    )


def _bucket_head_tongue(full_base: Solid) -> tuple[Solid, Solid]:
    """Return the bucket-owned head tongue and its baffle fit envelope."""
    direction = _fastener_direction()
    surface = _fastener_surface()
    nominal_envelope = source._cylinder_between(
        surface
        - direction * BUCKET_HEAD_TONGUE_ENTRY_OVERTRAVEL_MM,
        surface + direction * BUCKET_HEAD_TONGUE_END_MM,
        diameter=BUCKET_HEAD_TONGUE_D_MM,
    )
    tongue = _single_solid(
        nominal_envelope.intersect(full_base).clean().fix(),
        feature="hidden bucket-owned screw-head tongue",
    )
    clearance = source._cylinder_between(
        surface
        - direction * BUCKET_HEAD_TONGUE_ENTRY_OVERTRAVEL_MM,
        surface + direction * BUCKET_HEAD_TONGUE_CLEARANCE_END_MM,
        diameter=BUCKET_HEAD_TONGUE_CLEARANCE_D_MM,
    )
    return tongue, clearance


def _cut_top_loaded_nut_access(
    baffle: Solid,
    nut_access: Solid,
) -> tuple[Solid, dict[str, Any]]:
    """Open the vertical nut slot and audit its detached internal island."""
    result = baffle.cut(nut_access)
    solids = sorted(result.solids(), key=lambda item: item.volume, reverse=True)
    if not solids:
        raise ValueError("The top-loaded nut access removed the baffle")
    primary = _single_solid(
        solids[0].clean().fix(),
        feature="primary baffle after top-loaded nut access",
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
            "The top-loaded nut slot detached unexpected baffle material: "
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


def _centered_captive_nut_concept(
    common: dict[str, Any],
) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    direction = _fastener_direction()
    surface = _fastener_surface()
    nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

    # Reassign a small, already-existing portion of the one-piece shell to the
    # bucket so the screw head bears on the bucket and the nut bears on the
    # baffle.  The larger baffle envelope provides the hidden fit clearance.
    head_tongue, head_tongue_clearance = _bucket_head_tongue(
        common["full_base"]
    )
    baffle = _cut_one(
        baffle,
        head_tongue_clearance,
        feature="baffle clearance for hidden bucket head tongue",
    )
    bucket = _fuse_one(
        bucket,
        head_tongue,
        feature="bucket with hidden screw-head tongue",
    )

    head_cubby = _head_cubby()
    through_bore = source._cylinder_between(
        surface + direction * (SCREW_HEAD_AXIS_END_MM - 0.25),
        nut_center + direction * (NUT_POCKET_THICKNESS_MM / 2.0 + 1.5),
        diameter=SCREW_CLEARANCE_D_MM,
    )
    nut_pocket = _hex_prism(
        nut_center,
        across_flats_mm=NUT_POCKET_AF_MM,
        thickness_mm=NUT_POCKET_THICKNESS_MM,
        feature="M4 captive-nut hex pocket",
    )
    nut_bbox = nut_pocket.bounding_box()
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
        feature="unified top-loaded captive-nut access",
    )

    # Cut the passage into the reallocated center material.  A separate thin
    # baffle-owned pad is added below only after the nut cavity is valid.
    bucket = _cut_one(
        bucket,
        head_cubby,
        feature="bucket with recessed underside head cubby",
    )
    bucket = _cut_one(
        bucket,
        through_bore,
        feature="centered bucket screw passage",
    )
    baffle = _cut_one(
        baffle,
        through_bore,
        feature="centered baffle screw passage",
    )
    baffle, nut_access_audit = _cut_top_loaded_nut_access(
        baffle, nut_access
    )

    nut_pad_start = (
        BUCKET_HEAD_TONGUE_CLEARANCE_END_MM
        + NUT_LOAD_PAD_TONGUE_GAP_MM
    )
    nut_pad_end = NUT_AXIS_DISTANCE_MM - NUT_POCKET_THICKNESS_MM / 2.0
    nut_load_pad = _single_solid(
        source._cylinder_between(
            surface + direction * nut_pad_start,
            surface + direction * nut_pad_end,
            diameter=NUT_LOAD_PAD_D_MM,
        )
        .cut(through_bore, nut_access)
        .clean()
        .fix(),
        feature="pre-cut baffle captive-nut load pad",
    )
    nut_load_pad_root_mm3 = _shape_volume(
        nut_load_pad.intersect(baffle)
    )
    if nut_load_pad_root_mm3 <= 0.01:
        raise ValueError("The captive-nut load pad has no baffle root")
    baffle = _fuse_one(
        baffle,
        nut_load_pad,
        feature="baffle with captive-nut load pad",
    )
    load_reference_baffle = copy.copy(baffle)

    # The screw is removed before the baffle pivots open.  Re-clear the bucket
    # with the final reinforced baffle so the concealed hook motion remains the
    # same validated 0-to-15-degree sweep as the parent closure.
    bucket = closure._cut_concealed_pivot_sweep(bucket, baffle)

    screw_head = source._cylinder_between(
        surface + direction * SCREW_HEAD_AXIS_START_MM,
        surface + direction * SCREW_HEAD_AXIS_END_MM,
        diameter=SCREW_HEAD_D_MM,
    )
    screw_shank = source._cylinder_between(
        surface + direction * (SCREW_HEAD_AXIS_END_MM - 0.20),
        nut_center + direction * (NUT_THICKNESS_MM / 2.0 + 1.0),
        diameter=SCREW_NOMINAL_D_MM,
    )
    nut = _hex_prism(
        nut_center,
        across_flats_mm=NUT_AF_MM,
        thickness_mm=NUT_THICKNESS_MM,
        feature="standard M4 captive-nut reference",
    )
    hardware = Compound(children=[screw_head, screw_shank, nut])
    cutters = Compound(
        children=[head_cubby, through_bore, nut_access]
    )

    head_shoulder_distance = (
        SCREW_HEAD_AXIS_END_MM + HEAD_CUBBY_SHOULDER_CLEARANCE_MM
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

    bearing_center = nut_center - direction * (
        NUT_POCKET_THICKNESS_MM / 2.0
        + NUT_BEARING_AUDIT_THICKNESS_MM / 2.0
    )
    bearing_annulus = _single_solid(
        _hex_prism(
            bearing_center,
            across_flats_mm=NUT_AF_MM,
            thickness_mm=NUT_BEARING_AUDIT_THICKNESS_MM,
            feature="M4 nut bearing-face audit envelope",
        )
        .cut(through_bore)
        .clean()
        .fix(),
        feature="M4 nut bearing annulus",
    )
    supported_bearing_volume = _shape_volume(
        bearing_annulus.intersect(load_reference_baffle)
    )
    bearing_support_ratio = supported_bearing_volume / bearing_annulus.volume

    head_recess = screw_head.bounding_box().min.Z - FASTENER_SURFACE_Z_MM
    dry_side_clearance = closure.DRY_SIDE_REAR_LIMIT_Y - max(
        cutters.bounding_box().max.Y,
        hardware.bounding_box().max.Y,
    )
    head_load_wall = BUCKET_HEAD_TONGUE_END_MM - head_shoulder_distance
    nut_load_wall = (
        NUT_AXIS_DISTANCE_MM
        - NUT_POCKET_THICKNESS_MM / 2.0
        - BUCKET_HEAD_TONGUE_CLEARANCE_END_MM
        - NUT_LOAD_PAD_TONGUE_GAP_MM
    )
    if head_recess < MINIMUM_HEAD_RECESS_MM:
        raise ValueError(
            "The angled screw head is not fully recessed: "
            f"recess={head_recess:.6f} mm"
        )
    if dry_side_clearance < MINIMUM_TARGET_DRY_SIDE_CLEARANCE_MM:
        raise ValueError(
            "The centered fastener is too close to the gasket plane: "
            f"clearance={dry_side_clearance:.6f} mm"
        )
    if head_load_wall < MINIMUM_HEAD_LOAD_WALL_MM:
        raise ValueError(
            "The bucket-owned screw-head shoulder is too thin: "
            f"wall={head_load_wall:.6f} mm"
        )
    if head_bearing_support_ratio < MINIMUM_HEAD_BEARING_SUPPORT_RATIO:
        raise ValueError(
            "The M4 screw head does not have enough bucket-owned bearing "
            f"area: ratio={head_bearing_support_ratio:.6f}"
        )
    if nut_load_wall < MINIMUM_NUT_LOAD_WALL_MM:
        raise ValueError(
            "The captive nut has insufficient material below its loaded face: "
            f"wall={nut_load_wall:.6f} mm"
        )
    if bearing_support_ratio < MINIMUM_NUT_BEARING_SUPPORT_RATIO:
        raise ValueError(
            "The standard M4 nut does not have enough supported bearing "
            f"area: ratio={bearing_support_ratio:.6f}"
        )

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if (
            target_area - MAXIMUM_LOCAL_FAIRING_REASSIGNMENT_MM2
            <= face.area
            <= target_area + 1e-5
        )
    ]
    if len(fairing_faces) != 1:
        raise ValueError(
            "The centered closure changed more than the local underside "
            "head-tongue patch of the exterior fairing"
        )
    fairing_area_difference = fairing_faces[0].area - target_area

    tongue_outside_source_volume = _shape_volume(
        head_tongue.cut(common["full_base"])
    )
    if tongue_outside_source_volume > 0.001:
        raise ValueError(
            "The local bucket tongue changes the authoritative exterior: "
            f"outside_volume={tongue_outside_source_volume:.6f} mm3"
        )
    tongue_clearance_gasket_overlap = _shape_volume(
        head_tongue_clearance.intersect(common["gasket"])
    )
    if tongue_clearance_gasket_overlap > 0.001:
        raise ValueError(
            "The hidden head-tongue fit reaches the gasket: "
            f"overlap={tongue_clearance_gasket_overlap:.6f} mm3"
        )

    for name, finished, reference in (
        ("baffle", baffle, common["reference_baffle"]),
    ):
        final_bbox = finished.bounding_box()
        reference_bbox = reference.bounding_box()
        exterior_deltas = {
            "min_x": final_bbox.min.X - reference_bbox.min.X,
            "max_x": final_bbox.max.X - reference_bbox.max.X,
            "min_y": final_bbox.min.Y - reference_bbox.min.Y,
            "min_z": final_bbox.min.Z - reference_bbox.min.Z,
            "max_z": final_bbox.max.Z - reference_bbox.max.Z,
        }
        if max(abs(value) for value in exterior_deltas.values()) > 1e-5:
            raise ValueError(
                f"The {name} closure changes the authoritative exterior: "
                f"{exterior_deltas}"
            )

    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": common["gasket"],
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": cutters,
        "head_tongue": head_tongue,
        "nut_load_pad": nut_load_pad,
        "description": (
            "One centered M4 screw in a flush underside cubby drawing a "
            "top-loaded captive hex nut deeper into a hidden baffle seat"
        ),
        "service_notes": (
            "Drop the M4 nut into the hidden upper slot, engage the two top "
            "hooks, compress the gasket, then tighten one underside screw"
        ),
        "closure_passage_mode": (
            "single centered passage entirely ahead of the continuous gasket"
        ),
        "geometry": {
            "fastener_count": 1,
            "fastener_x_mm": FASTENER_X_MM,
            "angle_from_bottom_normal_deg": (
                FASTENER_ANGLE_FROM_BOTTOM_NORMAL_DEG
            ),
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "head_d_mm": SCREW_HEAD_D_MM,
            "head_cubby_d_mm": HEAD_CUBBY_D_MM,
            "head_cubby_depth_along_axis_mm": head_shoulder_distance,
            "minimum_head_recess_below_bottom_mm": head_recess,
            "bucket_head_tongue_d_mm": BUCKET_HEAD_TONGUE_D_MM,
            "bucket_head_tongue_clearance_d_mm": (
                BUCKET_HEAD_TONGUE_CLEARANCE_D_MM
            ),
            "bucket_head_load_wall_mm": head_load_wall,
            "head_bearing_support_ratio": head_bearing_support_ratio,
            "nut_nominal_af_mm": NUT_AF_MM,
            "nut_nominal_thickness_mm": NUT_THICKNESS_MM,
            "nut_pocket_af_mm": NUT_POCKET_AF_MM,
            "nut_pocket_thickness_mm": NUT_POCKET_THICKNESS_MM,
            "nut_entry_direction": (
                "edge-on top-down in +Z, then rotate into hex seat"
            ),
            "nut_entry_slot_width_x_mm": NUT_ENTRY_SLOT_WIDTH_X_MM,
            "nut_entry_slot_depth_y_mm": NUT_ENTRY_SLOT_DEPTH_Y_MM,
            "minimum_material_below_loaded_nut_face_mm": nut_load_wall,
            "nut_load_pad_d_mm": NUT_LOAD_PAD_D_MM,
            "nut_load_pad_root_mm3": nut_load_pad_root_mm3,
            "nut_load_pad_added_volume_mm3": (
                nut_load_pad.volume - nut_load_pad_root_mm3
            ),
            "nut_bearing_audit_thickness_mm": (
                NUT_BEARING_AUDIT_THICKNESS_MM
            ),
            "nut_bearing_support_ratio": bearing_support_ratio,
            "tightening_load_drives_nut_deeper_into_closed_seat": True,
            "added_exterior_reinforcement_volume_mm3": 0.0,
            "reassigns_existing_center_load_mass_to_bucket": True,
            "tongue_outside_source_volume_mm3": (
                tongue_outside_source_volume
            ),
            "tongue_clearance_gasket_overlap_mm3": (
                tongue_clearance_gasket_overlap
            ),
            "minimum_dry_side_clearance_mm": dry_side_clearance,
            "outer_fairing_area_difference_mm2": (
                fairing_area_difference
            ),
            "fairing_change_is_local_underside_head_tongue_patch": True,
            "external_blisters": False,
            "bottom_head_protrusion_mm": 0.0,
            "nut_access_island_audit": nut_access_audit,
        },
    }


def _configure_viewer(viewer_dir: Path, *, cutaway: bool = False) -> None:
    source._configure_viewer(viewer_dir, cutaway=cutaway)


def _generate_viewers() -> None:
    specs = (
        ("centered_captive_nut_assembled.step", "viewer", False),
        ("centered_captive_nut_exploded.step", "exploded_viewer", False),
        ("centered_captive_nut_cutaway.step", "cutaway_viewer", True),
        ("centered_captive_nut_joint_section.step", "joint_section_viewer", True),
        ("centered_captive_nut_bucket.step", "bucket_viewer", False),
        ("centered_captive_nut_baffle.step", "baffle_viewer", False),
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
        _configure_viewer(viewer_dir, cutaway=cutaway)


def _export_and_check(exports: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        source_solids = shape.solids()
        imported_solids = imported.solids()
        source_faces = shape.faces()
        imported_faces = imported.faces()
        check = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(source_solids) == len(imported_solids),
            "source_face_count": len(source_faces),
            "imported_face_count": len(imported_faces),
            "face_count_matches": len(source_faces) == len(imported_faces),
            "all_imported_solids_valid": all(
                _is_valid(solid) for solid in imported_solids
            ),
            "all_imported_faces_valid": all(
                _is_valid(face) for face in imported_faces
            ),
        }
        checks[filename] = check
        if not all(
            (
                check["solid_count_matches"],
                check["face_count_matches"],
                check["all_imported_solids_valid"],
                check["all_imported_faces_valid"],
            )
        ):
            raise ValueError(f"STEP round trip failed for {filename}: {check}")
    return checks


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    closure.OUT = OUT
    source.OUT = OUT
    for module in (
        parent,
        parent.source,
        parent.source.prior,
        parent.source.serviceable,
        parent.source.header,
        base,
    ):
        module.OUT = OUT
    base.D = replace(base.D, name=NAME)
    parent.NAME = NAME
    parent.OUT = OUT
    parent._GEOMETRY_CACHE = None
    parent._DETAIL_CUT_AUDITS.clear()
    parent._full_detail_base = source.prior._solid_rear_detail_base

    base._restored_internal_braces = source._printable_restored_internal_braces
    try:
        diagnostics = parent.generate()
    finally:
        base._restored_internal_braces = source.ORIGINAL_RESTORED_INTERNAL_BRACES

    full_base = _single_solid(
        import_step(OUT / "sand_cube_190x210_single_oval_port_base.step"),
        feature="round-tripped full-detail centered-fastener source enclosure",
    )
    common = closure._add_common_joint(full_base)
    common["full_base"] = full_base
    concept = _centered_captive_nut_concept(common)
    gasket = common["gasket"]
    acoustic_domain = base._acoustic_domain()

    validation = closure._validate_concept(
        "centered_captive_nut", concept, gasket, acoustic_domain
    )
    inherited_assembly = import_step(
        OUT / "sand_cube_190x210_single_oval_port_assembly.step"
    )
    retained = source._retained_assembly_solids(inherited_assembly, full_base)
    inherited_check = source._new_to_inherited_interference(
        concept["bucket"],
        concept["baffle"],
        gasket,
        retained,
        full_base,
    )
    if inherited_check["new_excess_interference_mm3"] > 0.01:
        raise ValueError(
            "Centered closure interferes with the inherited assembly: "
            f"{inherited_check}"
        )

    pivot = source._pivot_sweep(concept["bucket"], concept["baffle"])
    if max(pivot["interference_mm3"].values()) > 0.001:
        raise ValueError(f"Centered closure obstructs the pivot: {pivot}")

    reference_occupancy_mm3 = closure._acoustic_occupancy(
        common["reference_bucket"],
        common["reference_baffle"],
        None,
        acoustic_domain,
    )
    concept_occupancy_mm3 = closure._acoustic_occupancy(
        concept["bucket"],
        concept["baffle"],
        gasket,
        acoustic_domain,
    )
    added_mm3 = concept_occupancy_mm3 - reference_occupancy_mm3
    baseline_net_l = diagnostics["volume_accounting"][
        "final_modeled_net_box_volume_l"
    ]
    baseline_tuning_hz = diagnostics["port"]["lengths"][
        "calculated_tuning_hz"
    ]
    modeled_net_l = baseline_net_l - added_mm3 / 1_000_000.0
    modeled_tuning_hz = baseline_tuning_hz * math.sqrt(
        baseline_net_l / modeled_net_l
    )

    bucket = concept["bucket"]
    baffle = concept["baffle"]
    hardware = concept["hardware"]
    assembled = Compound(
        children=[bucket, gasket, baffle, *hardware.solids()]
    )
    exploded = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(gasket).moved(Pos(0.0, -16.0, 0.0)),
            copy.copy(baffle).moved(Pos(0.0, -38.0, 0.0)),
            *[
                copy.copy(solid).moved(Pos(0.0, -19.0, 0.0))
                for solid in hardware.solids()
            ],
        ]
    )
    full_system = Compound(
        children=[bucket, gasket, baffle, *retained]
    )
    inherited_cutaway = import_step(
        OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
    )
    shell_cutaway = source._true_cutaway(
        bucket, baffle, gasket, inherited_cutaway
    )
    cutaway = Compound(
        children=[shell_cutaway, *[copy.copy(s) for s in hardware.solids()]]
    )
    joint_section = Compound(
        children=[
            source._true_cutaway(
                bucket,
                baffle,
                gasket,
                Compound(children=[]),
            ),
            *[copy.copy(s) for s in hardware.solids()],
        ]
    )

    exports = {
        "centered_captive_nut_bucket.step": bucket,
        "centered_captive_nut_baffle.step": baffle,
        "centered_captive_nut_hardware_reference.step": hardware,
        "centered_captive_nut_assembled.step": assembled,
        "centered_captive_nut_exploded.step": exploded,
        "centered_captive_nut_full_system.step": full_system,
        "centered_captive_nut_cutaway.step": cutaway,
        "centered_captive_nut_joint_section.step": joint_section,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    diagnostics["name"] = NAME
    diagnostics["status"] = "complete centered captive-nut closure experiment"
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_centered_captive_nut"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_centered_captive_nut"
        ),
        "closure_concepts_parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["centered_captive_nut_closure"] = {
        "description": concept["description"],
        "service_notes": concept["service_notes"],
        "geometry": concept["geometry"],
        "validation": validation,
        "pivot_sweep_interference_mm3": pivot["interference_mm3"],
        "new_to_inherited_interference_mm3": inherited_check,
        "added_acoustic_displacement_mm3": added_mm3,
        "modeled_net_volume_l": modeled_net_l,
        "modeled_natural_tuning_hz": modeled_tuning_hz,
        "port_length_mm": diagnostics["port"]["lengths"][
            "physical_centerline_length_mm"
        ],
        "port_length_change_mm": 0.0,
        "gasket_width_mm": source.GASKET_TAPE_WIDTH_MM,
        "gasket_uncompressed_thickness_mm": (
            source.GASKET_UNCOMPRESSED_THICKNESS_MM
        ),
        "gasket_modeled_closed_gap_mm": source.GASKET_CLOSED_GAP_MM,
        "gasket_continuous_and_uninterrupted": True,
        "authoritative_exterior_preserved": True,
    }
    diagnostics["geometry"]["centered_captive_nut_step_roundtrip"] = (
        step_roundtrip
    )
    diagnostics["files"].update(
        {filename: str(OUT / filename) for filename in exports}
    )
    diagnostics["files"].update(
        {
            "centered_captive_nut_viewer": str(OUT / "viewer" / "index.html"),
            "centered_captive_nut_exploded_viewer": str(
                OUT / "exploded_viewer" / "index.html"
            ),
            "centered_captive_nut_cutaway_viewer": str(
                OUT / "cutaway_viewer" / "index.html"
            ),
            "centered_captive_nut_joint_section_viewer": str(
                OUT / "joint_section_viewer" / "index.html"
            ),
            "centered_captive_nut_bucket_viewer": str(
                OUT / "bucket_viewer" / "index.html"
            ),
            "centered_captive_nut_baffle_viewer": str(
                OUT / "baffle_viewer" / "index.html"
            ),
        }
    )
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
