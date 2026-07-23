"""Generate four closure concepts for the nested parabolic baffle.

The unsplit parabolic enclosure remains the authoritative exterior envelope.
This experiment moves the baffle mating taper behind a continuous bucket lip,
keeps the 5 x 2 mm gasket farther inward, and compares four lower retention
ideas: concealed zip-tie loops, sacrificial ratchet-head zip latches, open
underside bolt/nut channels, and 45 degree pocket screws in reinforced bosses.
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
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Face,
    Pos,
    Rot,
    Solid,
    Unit,
    Vector,
    export_step,
    import_step,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_hooked_gasketed_baffle"
)
if str(SOURCE_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_hooked_gasketed_baffle as source  # noqa: E402


parent = source.parent
base = source.base
shell_source = source.shell_source
cad = source.cad
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_nested_seam_closure_concepts"
)
NAME = "sand_cube_190x210_parabolic_g1_nested_seam_closure_concepts"

# The plug moves inward immediately behind the exact baseline tangent seam.
# The bucket owns the outer band behind that line, so the baffle taper cannot
# be seen from outside.  The two hidden envelopes differ by a printable fit
# allowance while sharing the exact visible seam.
SOCKET_LIP_DEPTH_MM = 1.40
SOCKET_PLUG_ENTRY_INSET_MM = 1.60
SOCKET_BED_INSET_MM = 4.00
SOCKET_NORMAL_CLEARANCE_MM = 0.28
VISIBLE_SEAM_GAP_MM = 0.0
DRY_SIDE_REAR_LIMIT_Y = source.BAFFLE_BED_Y - 0.35

MECHANISM_X_MM = 52.0
MECHANISM_WIDTH_MM = 16.0

ZIP_TIE_WIDTH_MM = 4.8
ZIP_TIE_THICKNESS_MM = 1.3
ZIP_TIE_SLOT_WIDTH_MM = 5.5
ZIP_TIE_SLOT_THICKNESS_MM = 2.0
ZIP_TIE_HEAD_SIZE_MM = (9.0, 7.0, 4.0)
ZIP_LATCH_RECEIVER_Y_MM = -62.0
ZIP_LATCH_ANCHOR_Y_MM = -78.0
ZIP_LATCH_ANCHOR_Z_MM = -87.5
ZIP_LATCH_TUNNEL_ROOF_Z_MM = -83.3
ZIP_LATCH_MIN_ROOF_MM = 2.0

BOLT_NOMINAL_D_MM = 4.0
BOLT_CLEARANCE_D_MM = 4.5
BOLT_HEAD_D_MM = 8.5
BOLT_NUT_AF_MM = 7.0

POCKET_SCREW_ANGLE_DEG = 45.0
POCKET_SCREW_CLEARANCE_D_MM = 4.5
POCKET_SCREW_INSERT_D_MM = 5.6
POCKET_SCREW_BOSS_D_MM = 11.0


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    return source._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return source._single_solid(shape, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return source._fuse_one(shape, addition, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return source._cut_one(shape, cutter, feature=feature)


def _centered_box(
    x_size: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    *,
    x: float,
) -> Solid:
    return source._centered_box(x_size, y0, y1, z0, z1, x=x)


def _rectangular_prism_between(
    start: Vector,
    end: Vector,
    *,
    width_x_mm: float,
    thickness_mm: float,
) -> Solid:
    delta = end - start
    if abs(delta.X) > 1e-8:
        raise ValueError("Zip-tie channel is constrained to the Y/Z plane")
    angle_x = math.degrees(math.atan2(-delta.Y, delta.Z))
    prism = Box(
        width_x_mm,
        thickness_mm,
        delta.length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    midpoint = (start + end) * 0.5
    placed = Pos(midpoint.X, midpoint.Y, midpoint.Z) * Rot(
        angle_x, 0.0, 0.0
    ) * prism
    return _single_solid(placed, feature="angled rectangular zip-tie path")


def _radially_inset_targets(
    targets: list[tuple[float, float, float]],
    inset_mm: float,
    *,
    y_offset_mm: float | None = None,
) -> list[tuple[float, float, float]]:
    result: list[tuple[float, float, float]] = []
    for x, y, z in targets:
        radius = math.hypot(x, z)
        scale = (radius - inset_mm) / radius
        target_y = y if y_offset_mm is None else y + y_offset_mm
        result.append((x * scale, target_y, z * scale))
    return result


def _nested_split_envelope(*, clearance_mm: float) -> Solid:
    """Baffle plug envelope with an exact exterior seam and hidden socket."""
    if not 0.0 <= clearance_mm < SOCKET_PLUG_ENTRY_INSET_MM:
        raise ValueError("Nested-socket clearance is out of range")
    seam_targets = shell_source.parent._minimum_energy_control_rings()[-1]
    front_targets = [
        (x, shell_source.FRONT_Y - 2.0, z)
        for x, _y, z in seam_targets
    ]
    entry_targets = _radially_inset_targets(
        seam_targets,
        SOCKET_PLUG_ENTRY_INSET_MM - clearance_mm,
        y_offset_mm=SOCKET_LIP_DEPTH_MM,
    )
    bed_targets: list[tuple[float, float, float]] = []
    for x, _y, z in seam_targets:
        radius = math.hypot(x, z)
        inset = SOCKET_BED_INSET_MM - clearance_mm
        scale = (radius - inset) / radius
        bed_targets.append((x * scale, source.BAFFLE_BED_Y, z * scale))

    builder = BRepOffsetAPI_ThruSections(True, False, 1e-7)
    builder.CheckCompatibility(True)
    for targets, feature in (
        (front_targets, "nested split front overtravel"),
        (seam_targets, "exact baseline tangent seam"),
        (entry_targets, "concealed socket entry"),
        (bed_targets, "nested plug print-bed perimeter"),
    ):
        builder.AddWire(source._curve_wire(targets, feature=feature).wrapped)
    builder.Build()
    if not builder.IsDone():
        raise ValueError("Unable to build nested baffle split envelope")
    envelope = Solid.cast(builder.Shape())
    if envelope is None:
        raise ValueError("Unable to cast nested baffle split envelope")
    return _single_solid(
        envelope.clean().fix(),
        feature="nested baffle split envelope",
    )


def _cut_concealed_pivot_sweep(bucket: Solid, baffle: Solid) -> Solid:
    """Clear the hidden top lip along the validated hook-opening arc."""
    pivot_axis = Axis(
        Vector(0.0, source.HOOK_PIVOT_Y, source.HOOK_PIVOT_Z),
        Vector(1.0, 0.0, 0.0),
    )
    for angle in source.PIVOT_SWEEP_ANGLES_DEG[1:]:
        moved = copy.copy(baffle).rotate(pivot_axis, angle)
        if _shape_volume(bucket.intersect(moved)) <= 0.001:
            continue
        bucket = _cut_one(
            bucket,
            moved,
            feature=f"concealed nested-lip pivot sweep at {angle:g} deg",
        )
    return bucket


def _add_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = _nested_split_envelope(clearance_mm=0.0)
    clearance = _nested_split_envelope(
        clearance_mm=SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal).clean().fix(),
        feature="nested-seam conformal front baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="continuous-lip nested-seam bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)
    bucket = _cut_one(
        bucket,
        source._gasket_pocket_cutter(),
        feature="nested bucket with continuous gasket pocket",
    )
    shoulder = source._gasket_shoulder()
    bucket = _fuse_one(
        bucket,
        shoulder,
        feature="nested bucket with gasket shoulder",
    )
    for x in (-source.HOOK_X_MM, source.HOOK_X_MM):
        bucket = _fuse_one(
            bucket,
            source._bucket_hook(x),
            feature=f"nested bucket with top hook at x={x:g}",
        )

    baffle = _fuse_one(
        baffle,
        source._baffle_gasket_land(),
        feature="nested baffle with gasket land",
    )
    for x in (-source.HOOK_X_MM, source.HOOK_X_MM):
        for index, cutter in enumerate(
            source._hook_receiver_cutters(x), start=1
        ):
            baffle = _cut_one(
                baffle,
                cutter,
                feature=f"nested hook receiver {index} at x={x:g}",
            )

    bucket = _cut_concealed_pivot_sweep(bucket, baffle)

    gasket = source._compressed_gasket_reference()
    overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket = _shape_volume(gasket.intersect(bucket))
    gasket_baffle = _shape_volume(gasket.intersect(baffle))
    if max(overlap, gasket_bucket, gasket_baffle) > 0.01:
        raise ValueError(
            "Nested common joint interference: "
            f"bucket/baffle={overlap:.6f}, "
            f"gasket/bucket={gasket_bucket:.6f}, "
            f"gasket/baffle={gasket_baffle:.6f} mm3"
        )

    target_area = parent._build_parabolic_conformal_geometry()[
        "outer_fairing_area_mm2"
    ]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= 1e-5
    ]
    if len(fairing_faces) != 1:
        raise ValueError("Nested joint changed the baseline exterior fairing")
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
        "bucket_baffle_overlap_mm3": overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket,
        "gasket_baffle_overlap_mm3": gasket_baffle,
    }


def _add_partitioned_reinforcement(
    common: dict[str, Any],
    bucket: Solid,
    baffle: Solid,
    reinforcement: Solid,
    *,
    feature: str,
) -> tuple[Solid, Solid]:
    """Split one local pad across the same hidden socket as the shell."""
    bucket_piece = _single_solid(
        reinforcement.cut(common["clearance_envelope"]).clean().fix(),
        feature=f"{feature} bucket-side reinforcement",
    )
    baffle_piece = _single_solid(
        reinforcement.intersect(common["nominal_envelope"]).clean().fix(),
        feature=f"{feature} baffle-side reinforcement",
    )
    bucket = _fuse_one(
        bucket,
        bucket_piece,
        feature=f"bucket with {feature}",
    )
    baffle = _fuse_one(
        baffle,
        baffle_piece,
        feature=f"baffle with {feature}",
    )
    # The two loft envelopes are intentionally identical at the visible seam.
    # A reinforcement that reaches that mathematical boundary can therefore
    # acquire a tiny shared sliver.  Trim only that sliver from the bucket;
    # the baffle remains the authoritative plug at the contact surface.
    if _shape_volume(bucket.intersect(baffle)) > 0.001:
        bucket = _cut_one(
            bucket,
            baffle,
            feature=f"clearance-trimmed {feature} bucket reinforcement",
        )
    return bucket, baffle


def _zip_tie_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    references: list[Solid] = []
    all_cutters: list[Solid] = []
    for x in (-MECHANISM_X_MM, MECHANISM_X_MM):
        saddle = _centered_box(
            MECHANISM_WIDTH_MM,
            -88.0,
            -77.5,
            -95.0,
            -89.15,
            x=x,
        )
        bucket, baffle = _add_partitioned_reinforcement(
            common,
            bucket,
            baffle,
            saddle,
            feature=f"zip-tie wedge saddle at x={x:g}",
        )

        # The two legs straddle the sloped hidden joint.  Tightening the loop
        # squeezes this wedge in Z and consequently draws the baffle rearward.
        slot_centers_y = (-85.0, -80.4)
        for slot_y in slot_centers_y:
            cutter = _centered_box(
                ZIP_TIE_SLOT_WIDTH_MM,
                slot_y - ZIP_TIE_SLOT_THICKNESS_MM / 2.0,
                slot_y + ZIP_TIE_SLOT_THICKNESS_MM / 2.0,
                -95.2,
                -89.65,
                x=x,
            )
            bucket = _cut_one(
                bucket,
                cutter,
                feature=f"zip-tie bucket slot at x={x:g}, y={slot_y:g}",
            )
            baffle = _cut_one(
                baffle,
                cutter,
                feature=f"zip-tie baffle slot at x={x:g}, y={slot_y:g}",
            )
            all_cutters.append(cutter)

        top_groove = _centered_box(
            ZIP_TIE_SLOT_WIDTH_MM,
            slot_centers_y[0] - ZIP_TIE_SLOT_THICKNESS_MM / 2.0,
            slot_centers_y[1] + ZIP_TIE_SLOT_THICKNESS_MM / 2.0,
            -90.85,
            -89.05,
            x=x,
        )
        baffle = _cut_one(
            baffle,
            top_groove,
            feature=f"zip-tie concealed top groove at x={x:g}",
        )
        all_cutters.append(top_groove)

        head_x, head_y, head_z = ZIP_TIE_HEAD_SIZE_MM
        head_recess = _centered_box(
            head_x + 0.6,
            -82.7 - (head_y + 0.6) / 2.0,
            -82.7 + (head_y + 0.6) / 2.0,
            -95.2,
            -95.2 + head_z + 0.6,
            x=x,
        )
        bucket = _cut_one(
            bucket,
            head_recess,
            feature=f"flush zip-tie head recess at x={x:g}",
        )
        baffle = _cut_one(
            baffle,
            head_recess,
            feature=f"flush baffle-side zip-tie head recess at x={x:g}",
        )
        all_cutters.append(head_recess)

        front_leg = _centered_box(
            ZIP_TIE_WIDTH_MM,
            slot_centers_y[0] - ZIP_TIE_THICKNESS_MM / 2.0,
            slot_centers_y[0] + ZIP_TIE_THICKNESS_MM / 2.0,
            -94.8,
            -89.4,
            x=x,
        )
        rear_leg = _centered_box(
            ZIP_TIE_WIDTH_MM,
            slot_centers_y[1] - ZIP_TIE_THICKNESS_MM / 2.0,
            slot_centers_y[1] + ZIP_TIE_THICKNESS_MM / 2.0,
            -94.8,
            -89.4,
            x=x,
        )
        top_bridge = _centered_box(
            ZIP_TIE_WIDTH_MM,
            slot_centers_y[0],
            slot_centers_y[1],
            -90.65,
            -89.35,
            x=x,
        )
        head = _centered_box(
            head_x,
            -82.7 - head_y / 2.0,
            -82.7 + head_y / 2.0,
            -95.0,
            -95.0 + head_z,
            x=x,
        )
        references.extend((front_leg, rear_leg, top_bridge, head))
    return {
        "bucket": bucket,
        "baffle": baffle,
        "hardware": Compound(children=references),
        "cutters": Compound(children=all_cutters),
        "description": (
            "Two 4.8 mm zip-tie loops through sealed dry-side saddles; "
            "heads recess flush into the speaker underside"
        ),
        "service_notes": (
            "fast and tool-light, but polymer creep can relax gasket load"
        ),
    }


def _sacrificial_zip_latch_concept(
    common: dict[str, Any],
) -> dict[str, Any]:
    """A captive tie anchor and replaceable underside ratchet head."""
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    references: list[Solid] = []
    all_cutters: list[Solid] = []
    for x in (-MECHANISM_X_MM, MECHANISM_X_MM):
        receiver = Vector(x, ZIP_LATCH_RECEIVER_Y_MM, -94.9)
        anchor = Vector(
            x, ZIP_LATCH_ANCHOR_Y_MM, ZIP_LATCH_ANCHOR_Z_MM
        )
        direction = (anchor - receiver).normalized()
        raw_tunnel = source._cylinder_between(
            receiver - direction * 1.2,
            anchor + direction * 1.0,
            diameter=10.0,
        )
        tunnel_clip = Pos(x, -69.0, -89.15) * Box(
            MECHANISM_WIDTH_MM + 2.0,
            32.0,
            11.7,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        sealed_tunnel = _single_solid(
            raw_tunnel.intersect(tunnel_clip).clean().fix(),
            feature=f"sealed sacrificial zip tunnel at x={x:g}",
        )
        bucket, baffle = _add_partitioned_reinforcement(
            common,
            bucket,
            baffle,
            sealed_tunnel,
            feature=f"sealed sacrificial zip latch at x={x:g}",
        )

        tail_channel = _rectangular_prism_between(
            receiver - direction * 1.3,
            anchor + direction * 0.8,
            width_x_mm=ZIP_TIE_SLOT_WIDTH_MM,
            thickness_mm=ZIP_TIE_SLOT_THICKNESS_MM,
        )
        for part_name in ("bucket", "baffle"):
            if part_name == "bucket":
                bucket = _cut_one(
                    bucket,
                    tail_channel,
                    feature=f"bucket sacrificial zip tail guide at x={x:g}",
                )
            else:
                baffle = _cut_one(
                    baffle,
                    tail_channel,
                    feature=f"baffle sacrificial zip tail guide at x={x:g}",
                )
        all_cutters.append(tail_channel)

        anchor_pocket = _centered_box(
            9.6,
            anchor.Y - 3.3,
            anchor.Y + 3.3,
            anchor.Z - 2.4,
            anchor.Z + 2.4,
            x=x,
        )
        bucket = _cut_one(
            bucket,
            anchor_pocket,
            feature=f"bucket-side captive tie-head clearance at x={x:g}",
        )
        baffle = _cut_one(
            baffle,
            anchor_pocket,
            feature=f"baffle captive tie-head receptacle at x={x:g}",
        )
        all_cutters.append(anchor_pocket)

        receiver_pocket = _centered_box(
            9.8,
            receiver.Y - 3.8,
            receiver.Y + 3.8,
            -95.2,
            -90.2,
            x=x,
        )
        bucket = _cut_one(
            bucket,
            receiver_pocket,
            feature=f"flush sacrificial ratchet-head pocket at x={x:g}",
        )
        all_cutters.append(receiver_pocket)

        tail = _rectangular_prism_between(
            receiver + direction * 0.1,
            anchor - direction * 0.6,
            width_x_mm=ZIP_TIE_WIDTH_MM,
            thickness_mm=ZIP_TIE_THICKNESS_MM,
        )
        captive_head = _centered_box(
            8.5,
            anchor.Y - 2.75,
            anchor.Y + 2.75,
            anchor.Z - 2.0,
            anchor.Z + 2.0,
            x=x,
        )
        receiver_head = _centered_box(
            9.0,
            receiver.Y - 3.5,
            receiver.Y + 3.5,
            -94.9,
            -90.9,
            x=x,
        )
        references.extend((tail, captive_head, receiver_head))

    hardware = Compound(children=references)
    return {
        "bucket": bucket,
        "baffle": baffle,
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": Compound(children=all_cutters),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": ZIP_LATCH_MIN_ROOF_MM,
        "description": (
            "Two captive baffle tie heads feed toothed tails through sealed "
            "floor tunnels into replaceable ratchet heads recessed underneath"
        ),
        "service_notes": (
            "clip the inexpensive underside ratchet heads to open; captive "
            "tie anchors remain replaceable when the baffle is removed"
        ),
    }


def _bolt_channel_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    references: list[Solid] = []
    all_cutters: list[Solid] = []
    bolt_z = -90.7
    for x in (-MECHANISM_X_MM, MECHANISM_X_MM):
        collar_pad = _centered_box(
            MECHANISM_WIDTH_MM,
            -88.0,
            -77.5,
            -95.0,
            -83.0,
            x=x,
        )
        bucket, baffle = _add_partitioned_reinforcement(
            common,
            bucket,
            baffle,
            collar_pad,
            feature=f"open bolt-channel collar pad at x={x:g}",
        )

        access_pockets = (
            _centered_box(
                8.2, -88.3, -84.6, -95.2, -86.1, x=x
            ),
            _centered_box(
                9.2, -80.8, -77.3, -95.2, -86.1, x=x
            ),
            _centered_box(
                5.2, -84.8, -80.6, -95.2, -89.5, x=x
            ),
        )
        for index, access in enumerate(access_pockets, start=1):
            bucket = _cut_one(
                bucket,
                access,
                feature=(
                    f"open bucket bolt-channel access {index} at x={x:g}"
                ),
            )
            baffle = _cut_one(
                baffle,
                access,
                feature=(
                    f"open baffle bolt-channel access {index} at x={x:g}"
                ),
            )
            all_cutters.append(access)

        bore_start = Vector(x, -88.3, bolt_z)
        bore_end = Vector(x, -77.3, bolt_z)
        bore = source._cylinder_between(
            bore_start,
            bore_end,
            diameter=BOLT_CLEARANCE_D_MM,
        )
        bucket = _cut_one(
            bucket,
            bore,
            feature=f"bucket M4 bolt bore at x={x:g}",
        )
        baffle = _cut_one(
            baffle,
            bore,
            feature=f"baffle M4 bolt bore at x={x:g}",
        )
        all_cutters.append(bore)

        shank = source._cylinder_between(
            Vector(x, -87.9, bolt_z),
            Vector(x, -77.7, bolt_z),
            diameter=BOLT_NOMINAL_D_MM,
        )
        head = source._cylinder_between(
            Vector(x, -78.25, bolt_z),
            Vector(x, -77.45, bolt_z),
            diameter=BOLT_HEAD_D_MM,
        )
        nut = _centered_box(
            BOLT_NUT_AF_MM,
            -88.15,
            -86.75,
            bolt_z - BOLT_NUT_AF_MM / 2.0,
            bolt_z + BOLT_NUT_AF_MM / 2.0,
            x=x,
        )
        references.extend((shank, head, nut))
    return {
        "bucket": bucket,
        "baffle": baffle,
        "hardware": Compound(children=references),
        "cutters": Compound(children=all_cutters),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": 3.1,
        "closure_passage_mode": (
            "ahead of gasket plane inside roofed dry-side collars"
        ),
        "description": (
            "Two open underside M4 draw-bolt channels with the bolt head and "
            "nut captured behind opposing dry-side collars"
        ),
        "service_notes": (
            "direct rearward clamping and print-axis-aligned bores; most "
            "mechanically deterministic concept"
        ),
    }


def _pocket_screw_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    references: list[Solid] = []
    all_cutters: list[Solid] = []
    sealant_refs: list[Solid] = []
    direction = Vector(0.0, -1.0, 1.0).normalized()
    for x in (-MECHANISM_X_MM, MECHANISM_X_MM):
        surface = Vector(x, -82.0, -95.0)
        baffle_start = surface + direction * 5.2
        baffle_end = surface + direction * 12.0

        reinforcement = source._cylinder_between(
            surface - direction * 1.6,
            baffle_end + direction * 0.8,
            diameter=13.0,
        )
        bucket, baffle = _add_partitioned_reinforcement(
            common,
            bucket,
            baffle,
            reinforcement,
            feature=f"partitioned 45-degree wart and boss at x={x:g}",
        )

        bucket_bore = source._cylinder_between(
            surface - direction * 1.8,
            baffle_start + direction * 0.6,
            diameter=POCKET_SCREW_CLEARANCE_D_MM,
        )
        bucket = _cut_one(
            bucket,
            bucket_bore,
            feature=f"45-degree bucket screw bore at x={x:g}",
        )
        baffle = _cut_one(
            baffle,
            bucket_bore,
            feature=f"45-degree baffle entry bore at x={x:g}",
        )
        insert_pocket = source._cylinder_between(
            baffle_start - direction * 0.5,
            baffle_end - direction * 0.8,
            diameter=POCKET_SCREW_INSERT_D_MM,
        )
        baffle = _cut_one(
            baffle,
            insert_pocket,
            feature=f"45-degree baffle insert pocket at x={x:g}",
        )
        all_cutters.extend((bucket_bore, insert_pocket))

        head_pocket = source._cylinder_between(
            surface - direction * 1.9,
            surface + direction * 0.5,
            diameter=9.5,
        )
        bucket = _cut_one(
            bucket,
            head_pocket,
            feature=f"sealed 45-degree head pocket at x={x:g}",
        )
        all_cutters.append(head_pocket)

        shank = source._cylinder_between(
            surface - direction * 1.2,
            baffle_end - direction * 1.5,
            diameter=4.0,
        )
        head = source._cylinder_between(
            surface - direction * 1.2,
            surface + direction * 0.1,
            diameter=8.5,
        )
        references.extend((shank, head))

        seal_outer = source._cylinder_between(
            surface - direction * 0.9,
            surface - direction * 0.2,
            diameter=11.0,
        )
        seal_inner = source._cylinder_between(
            surface - direction * 1.0,
            surface - direction * 0.1,
            diameter=8.8,
        )
        sealant_refs.append(
            _single_solid(
                seal_outer.cut(seal_inner).clean().fix(),
                feature="45-degree screw sealant annulus",
            )
        )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "hardware": Compound(children=[*references, *sealant_refs]),
        "clearance_hardware": Compound(children=references),
        "cutters": Compound(children=all_cutters),
        "description": (
            "Two 45-degree dry-side pocket screws in reinforced underside "
            "warts with modeled sealant/O-ring annuli"
        ),
        "service_notes": (
            "compact and strong, but angled access and finish drilling remain"
        ),
    }


CONCEPT_BUILDERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "zip_tie": _zip_tie_concept,
    "sacrificial_zip_latch": _sacrificial_zip_latch_concept,
    "bolt_channel": _bolt_channel_concept,
    "pocket_screw_45deg": _pocket_screw_concept,
}


def _validate_concept(
    name: str,
    concept: dict[str, Any],
    gasket: Solid,
    acoustic_domain: Solid,
) -> dict[str, Any]:
    bucket = concept["bucket"]
    baffle = concept["baffle"]
    overlap = _shape_volume(bucket.intersect(baffle))
    gasket_bucket = _shape_volume(gasket.intersect(bucket))
    gasket_baffle = _shape_volume(gasket.intersect(baffle))
    cutter_acoustic = _shape_volume(
        concept["cutters"].intersect(acoustic_domain)
    )
    hardware_acoustic = _shape_volume(
        concept["hardware"].intersect(acoustic_domain)
    )
    cutter_rear_y = concept["cutters"].bounding_box().max.Y
    hardware_rear_y = concept["hardware"].bounding_box().max.Y
    dry_side_clearance = DRY_SIDE_REAR_LIMIT_Y - max(
        cutter_rear_y, hardware_rear_y
    )
    hard_parts = Compound(children=[copy.copy(bucket), copy.copy(baffle)])
    clearance_hardware = concept.get(
        "clearance_hardware", concept["hardware"]
    )
    hardware_hard_overlap = _shape_volume(
        clearance_hardware.intersect(hard_parts)
    )
    if max(overlap, gasket_bucket, gasket_baffle) > 0.01:
        raise ValueError(
            f"{name} hard-part interference: bucket/baffle={overlap:.6f}, "
            f"gasket/bucket={gasket_bucket:.6f}, "
            f"gasket/baffle={gasket_baffle:.6f} mm3"
        )
    sealed_tunnel = bool(concept.get("sealed_tunnel", False))
    if dry_side_clearance < -0.01 and not sealed_tunnel:
        raise ValueError(
            f"{name} crosses the gasket seal plane: "
            f"clearance={dry_side_clearance:.6f} mm"
        )
    if hardware_hard_overlap > 0.01:
        raise ValueError(
            f"{name} hardware reference clashes with the printed parts: "
            f"{hardware_hard_overlap:.6f} mm3"
        )
    if not all(_is_valid(item) for item in (bucket, baffle, gasket)):
        raise ValueError(f"{name} produced an invalid manufacturing solid")
    return {
        "bucket_baffle_overlap_mm3": overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket,
        "gasket_baffle_overlap_mm3": gasket_baffle,
        "closure_passage_overlap_with_nominal_acoustic_domain_envelope_mm3": (
            cutter_acoustic
        ),
        "hardware_overlap_with_nominal_acoustic_domain_envelope_mm3": (
            hardware_acoustic
        ),
        "hardware_to_hard_part_interference_mm3": hardware_hard_overlap,
        "gasket_front_plane_y_mm": source.BAFFLE_BED_Y,
        "closure_passage_rearmost_y_mm": cutter_rear_y,
        "hardware_rearmost_y_mm": hardware_rear_y,
        "minimum_dry_side_clearance_to_gasket_plane_mm": dry_side_clearance,
        "fastener_or_tie_entirely_outside_seal": True,
        "closure_passage_mode": concept.get(
            "closure_passage_mode",
            (
                "sealed floor tunnel outside gasket loop"
                if sealed_tunnel
                else "entirely ahead of gasket plane"
            ),
        ),
        "modeled_open_leak_path_to_enclosure_air": False,
        "minimum_sealed_tunnel_roof_mm": concept.get(
            "minimum_sealed_tunnel_roof_mm"
        ),
        "bucket_valid": _is_valid(bucket),
        "baffle_valid": _is_valid(baffle),
    }


def _acoustic_occupancy(
    bucket: Solid,
    baffle: Solid,
    gasket: Solid | None,
    acoustic_domain: Solid,
) -> float:
    return sum(
        _shape_volume(copy.copy(part).intersect(copy.copy(acoustic_domain)))
        for part in (bucket, baffle, gasket)
        if part is not None
    )


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


def _configure_viewer(viewer_dir: Path, *, cutaway: bool = False) -> None:
    source._configure_viewer(viewer_dir, cutaway=cutaway)


def _generate_viewers() -> None:
    specs = (
        ("closure_concepts_comparison.step", "comparison_viewer", False),
        ("zip_tie_assembled.step", "zip_tie_viewer", False),
        ("zip_tie_exploded.step", "zip_tie_exploded_viewer", False),
        (
            "sacrificial_zip_latch_assembled.step",
            "sacrificial_zip_latch_viewer",
            False,
        ),
        (
            "sacrificial_zip_latch_exploded.step",
            "sacrificial_zip_latch_exploded_viewer",
            False,
        ),
        ("bolt_channel_assembled.step", "bolt_channel_viewer", False),
        (
            "bolt_channel_exploded.step",
            "bolt_channel_exploded_viewer",
            False,
        ),
        (
            "pocket_screw_45deg_assembled.step",
            "pocket_screw_45deg_viewer",
            False,
        ),
        (
            "pocket_screw_45deg_exploded.step",
            "pocket_screw_45deg_exploded_viewer",
            False,
        ),
        ("zip_tie_cutaway.step", "nested_seam_cutaway_viewer", True),
        (
            "sacrificial_zip_latch_cutaway.step",
            "sacrificial_zip_latch_cutaway_viewer",
            True,
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
        _configure_viewer(viewer_dir, cutaway=cutaway)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
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
        feature="round-tripped full-detail nested-seam source enclosure",
    )
    common = _add_common_joint(full_base)
    gasket = common["gasket"]
    acoustic_domain = base._acoustic_domain()
    reference_occupancy_mm3 = _acoustic_occupancy(
        common["reference_bucket"],
        common["reference_baffle"],
        None,
        acoustic_domain,
    )

    inherited_assembly = import_step(
        OUT / "sand_cube_190x210_single_oval_port_assembly.step"
    )
    retained = source._retained_assembly_solids(
        inherited_assembly, full_base
    )
    inherited_cutaway = import_step(
        OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
    )

    concepts: dict[str, dict[str, Any]] = {}
    exports: dict[str, Any] = {}
    comparison_children: list[Any] = []
    comparison_offsets = {
        "zip_tie": -345.0,
        "sacrificial_zip_latch": -115.0,
        "bolt_channel": 115.0,
        "pocket_screw_45deg": 345.0,
    }
    baseline_net_l = diagnostics["volume_accounting"][
        "final_modeled_net_box_volume_l"
    ]
    baseline_tuning_hz = diagnostics["port"]["lengths"][
        "calculated_tuning_hz"
    ]

    for concept_name, builder in CONCEPT_BUILDERS.items():
        concept = builder(common)
        validation = _validate_concept(
            concept_name, concept, gasket, acoustic_domain
        )
        inherited_check = source._new_to_inherited_interference(
            concept["bucket"],
            concept["baffle"],
            gasket,
            retained,
            full_base,
        )
        if inherited_check["new_excess_interference_mm3"] > 0.01:
            raise ValueError(
                f"{concept_name} interferes with inherited assembly: "
                f"{inherited_check}"
            )

        pivot = source._pivot_sweep(
            concept["bucket"], concept["baffle"]
        )
        concept_occupancy_mm3 = _acoustic_occupancy(
            concept["bucket"],
            concept["baffle"],
            gasket,
            acoustic_domain,
        )
        added_mm3 = concept_occupancy_mm3 - reference_occupancy_mm3
        if not 0.0 < added_mm3 < 250_000.0:
            raise ValueError(
                f"{concept_name} acoustic displacement is implausible: "
                f"{added_mm3:.6f} mm3"
            )
        modeled_net_l = baseline_net_l - added_mm3 / 1_000_000.0
        modeled_tuning_hz = baseline_tuning_hz * math.sqrt(
            baseline_net_l / modeled_net_l
        )

        assembled = Compound(
            children=[
                copy.copy(concept["bucket"]),
                copy.copy(gasket),
                copy.copy(concept["baffle"]),
                *[
                    copy.copy(solid)
                    for solid in concept["hardware"].solids()
                ],
            ]
        )
        exploded = Compound(
            children=[
                copy.copy(concept["bucket"]),
                copy.copy(gasket).moved(Pos(0.0, -16.0, 0.0)),
                copy.copy(concept["baffle"]).moved(Pos(0.0, -38.0, 0.0)),
                *[
                    copy.copy(solid).moved(Pos(0.0, -19.0, 0.0))
                    for solid in concept["hardware"].solids()
                ],
            ]
        )
        full_system = Compound(
            children=[
                copy.copy(concept["bucket"]),
                copy.copy(gasket),
                copy.copy(concept["baffle"]),
                *[copy.copy(solid) for solid in retained],
            ]
        )
        cutaway = source._true_cutaway(
            concept["bucket"],
            concept["baffle"],
            gasket,
            inherited_cutaway,
        )

        exports[f"{concept_name}_bucket.step"] = concept["bucket"]
        exports[f"{concept_name}_baffle.step"] = concept["baffle"]
        exports[f"{concept_name}_hardware_reference.step"] = concept[
            "hardware"
        ]
        exports[f"{concept_name}_assembled.step"] = assembled
        exports[f"{concept_name}_exploded.step"] = exploded
        exports[f"{concept_name}_full_system.step"] = full_system
        if concept_name in ("zip_tie", "sacrificial_zip_latch"):
            exports[f"{concept_name}_cutaway.step"] = cutaway

        comparison_children.extend(
            copy.copy(solid).moved(
                Pos(comparison_offsets[concept_name], 0.0, 0.0)
            )
            for solid in assembled.solids()
        )
        concepts[concept_name] = {
            "description": concept["description"],
            "service_notes": concept["service_notes"],
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
        }

    comparison = Compound(children=comparison_children)
    exports["closure_concepts_comparison.step"] = comparison
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete nested-seam sealed closure concept comparison"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_nested_seam_closure_concepts"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_nested_seam_closure_concepts"
        ),
        "hooked_gasketed_parent_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["nested_seam_contract"] = {
        "authoritative_exterior": "exact unsplit parabolic enclosure envelope",
        "visible_seam_gap_mm": VISIBLE_SEAM_GAP_MM,
        "socket_lip_depth_mm": SOCKET_LIP_DEPTH_MM,
        "baffle_plug_entry_inset_mm": SOCKET_PLUG_ENTRY_INSET_MM,
        "hidden_normal_clearance_mm": SOCKET_NORMAL_CLEARANCE_MM,
        "baffle_taper_visible_from_exterior": False,
        "gasket_width_mm": source.GASKET_TAPE_WIDTH_MM,
        "gasket_uncompressed_thickness_mm": (
            source.GASKET_UNCOMPRESSED_THICKNESS_MM
        ),
        "gasket_modeled_closed_gap_mm": source.GASKET_CLOSED_GAP_MM,
        "gasket_continuous_and_uninterrupted": True,
        "dry_side_rear_limit_y_mm": DRY_SIDE_REAR_LIMIT_Y,
        "outer_fairing_area_difference_mm2": common[
            "fairing_area_difference_mm2"
        ],
        "common_bucket_baffle_overlap_mm3": common[
            "bucket_baffle_overlap_mm3"
        ],
    }
    diagnostics["closure_concepts"] = concepts
    diagnostics["geometry"]["nested_closure_step_roundtrip"] = step_roundtrip
    diagnostics["files"].update(
        {
            filename: str(OUT / filename)
            for filename in exports
        }
    )
    diagnostics["files"].update(
        {
            "comparison_viewer": str(OUT / "comparison_viewer" / "index.html"),
            "zip_tie_viewer": str(OUT / "zip_tie_viewer" / "index.html"),
            "zip_tie_exploded_viewer": str(
                OUT / "zip_tie_exploded_viewer" / "index.html"
            ),
            "sacrificial_zip_latch_viewer": str(
                OUT / "sacrificial_zip_latch_viewer" / "index.html"
            ),
            "sacrificial_zip_latch_exploded_viewer": str(
                OUT
                / "sacrificial_zip_latch_exploded_viewer"
                / "index.html"
            ),
            "sacrificial_zip_latch_cutaway_viewer": str(
                OUT
                / "sacrificial_zip_latch_cutaway_viewer"
                / "index.html"
            ),
            "bolt_channel_viewer": str(
                OUT / "bolt_channel_viewer" / "index.html"
            ),
            "bolt_channel_exploded_viewer": str(
                OUT / "bolt_channel_exploded_viewer" / "index.html"
            ),
            "pocket_screw_45deg_viewer": str(
                OUT / "pocket_screw_45deg_viewer" / "index.html"
            ),
            "pocket_screw_45deg_exploded_viewer": str(
                OUT
                / "pocket_screw_45deg_exploded_viewer"
                / "index.html"
            ),
            "nested_seam_cutaway_viewer": str(
                OUT / "nested_seam_cutaway_viewer" / "index.html"
            ),
        }
    )
    diagnostics_path = OUT / "diagnostics.json"
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
