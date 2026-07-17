"""Generate a gasketed, hooked, two-screw parabolic front baffle.

This isolated sibling starts from the complete solid-rear printable-bucket
experiment.  It preserves the exact parabolic G1 exterior and full inherited
system, then replaces only the bucket/baffle joint with a printable rounded
rim, a continuous 5 x 2 mm foam-tape land, two upper hooks, and two underside
fasteners.  The hardware dimensions are deliberately explicit so a purchased
insert can be substituted after a fit coupon without rebuilding the joint.
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
    Align,
    Axis,
    Box,
    BuildSketch,
    Compound,
    Cylinder,
    Edge,
    Face,
    GeomType,
    Plane,
    Pos,
    RectangleRounded,
    Rot,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    fillet,
    import_step,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_printable_bucket"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_printable_bucket as prior  # noqa: E402


parent = prior.parent
base = prior.base
shell_source = prior.shell_source
cad = prior.cad
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_hooked_gasketed_baffle"
)
NAME = "sand_cube_190x210_parabolic_g1_hooked_gasketed_baffle"

# Primary closure contract.
BAFFLE_BED_Y = shell_source.CAVITY_FRONT_Y
PERIMETER_INSET_MM = 4.0
HIDDEN_FIT_CLEARANCE_MM = 0.35
SHADOW_LINE_DEPTH_MM = 0.35
BUCKET_EDGE_FILLET_R_MM = 0.80
ENVELOPE_FRONT_OVERTRAVEL_MM = 2.0
EXPLODED_BAFFLE_OFFSET_MM = 42.0

# The 5 x 2 mm foam is modeled at its intended closed height.  No separate
# compression stops are added; the hook and screw geometry establish the
# nominal closed relationship.
GASKET_TAPE_WIDTH_MM = 5.0
GASKET_UNCOMPRESSED_THICKNESS_MM = 2.0
GASKET_CLOSED_GAP_MM = 1.15
GASKET_COMPRESSION_MM = (
    GASKET_UNCOMPRESSED_THICKNESS_MM - GASKET_CLOSED_GAP_MM
)
GASKET_COMPRESSION_PERCENT = (
    100.0 * GASKET_COMPRESSION_MM / GASKET_UNCOMPRESSED_THICKNESS_MM
)
GASKET_OUTER_SIZE_MM = 166.0
GASKET_OUTER_RADIUS_MM = 10.0
GASKET_INNER_SIZE_MM = GASKET_OUTER_SIZE_MM - 2.0 * GASKET_TAPE_WIDTH_MM
GASKET_INNER_RADIUS_MM = (
    GASKET_OUTER_RADIUS_MM - GASKET_TAPE_WIDTH_MM
)

# A broad shoulder and a 45-degree-safe inner ramp support the bucket rim.
SHOULDER_Y = BAFFLE_BED_Y + GASKET_CLOSED_GAP_MM
SHOULDER_SUPPORT_DEPTH_MM = 11.0
SHOULDER_OUTER_SIZE_MM = 178.0
SHOULDER_OUTER_RADIUS_MM = 12.0
SHOULDER_FRONT_INNER_SIZE_MM = GASKET_INNER_SIZE_MM
SHOULDER_FRONT_INNER_RADIUS_MM = GASKET_INNER_RADIUS_MM
SHOULDER_REAR_INNER_SIZE_MM = 176.0
SHOULDER_REAR_INNER_RADIUS_MM = 8.0
BAFFLE_LAND_OUTER_SIZE_MM = 167.0
BAFFLE_LAND_OUTER_RADIUS_MM = 10.5
BAFFLE_LAND_THICKNESS_MM = 1.4

# Two broad discrete hooks avoid binding across the full 190 mm width.  The
# male hooks stay on the bucket, so neither hook projects below the baffle's
# print-bed plane.
HOOK_X_MM = 43.0
HOOK_WIDTH_MM = 22.0
HOOK_SIDE_CLEARANCE_MM = 0.30
HOOK_SHANK_FRONT_Y = -84.8
HOOK_SHANK_REAR_Y = SHOULDER_Y + 1.25
HOOK_SHANK_BOTTOM_Z = 91.20
HOOK_SHANK_TOP_Z = 94.20
HOOK_TOE_FRONT_Y = HOOK_SHANK_FRONT_Y
HOOK_TOE_REAR_Y = -82.50
HOOK_TOE_BOTTOM_Z = 89.50
HOOK_TOE_TOP_Z = 93.40
HOOK_PIVOT_Y = -84.0
HOOK_PIVOT_Z = 94.0
HOOK_OPEN_ANGLE_DEG = -15.0

# The screws enter from the underside on an angle.  Tightening therefore pulls
# the baffle both upward into the hooks and rearward into the gasket.  The
# bucket pocket is sized for a short M5-class heat-set sleeve with an M4 screw
# passing through it; exact purchased hardware still requires a fit coupon.
FASTENER_X_MM = 52.0
FASTENER_SURFACE_Y = -70.5
FASTENER_SURFACE_Z = -95.0
FASTENER_DIRECTION_Y = -9.0
FASTENER_DIRECTION_Z = 8.0
SCREW_CLEARANCE_D_MM = 4.5
SCREW_HEAD_POCKET_D_MM = 9.2
SCREW_HEAD_POCKET_DEPTH_MM = 2.35
BUCKET_GUIDE_POCKET_D_MM = 7.2
BUCKET_GUIDE_INSERT_OD_MM = 7.0
BUCKET_GUIDE_INSERT_LENGTH_MM = 4.0
BUCKET_GUIDE_INSERT_START_MM = 2.55
BAFFLE_INSERT_POCKET_D_MM = 5.6
BAFFLE_INSERT_OD_MM = 5.4
BAFFLE_INSERT_ID_MM = 3.4
BAFFLE_INSERT_DEPTH_MM = 6.5
BAFFLE_INSERT_WALL_MM = 2.2
BAFFLE_BOSS_EMBED_START_MM = 4.7

PIVOT_SWEEP_ANGLES_DEG = (0.0, -2.0, -5.0, -8.0, -11.0, -15.0)


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    solids = shape.solids()
    if len(solids) != 1 or not _is_valid(solids[0]):
        raise ValueError(
            f"{feature} did not produce one valid solid: {len(solids)}"
        )
    return solids[0]


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return _single_solid(
        shape.fuse(addition).clean().fix(),
        feature=feature,
    )


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return _single_solid(
        shape.cut(cutter).clean().fix(),
        feature=feature,
    )


def _curve_wire(
    targets: list[tuple[float, float, float]],
    *,
    feature: str,
) -> Wire:
    poles = shell_source.legacy._periodic_interpolation_poles(targets)
    curve = shell_source.legacy._curve_from_poles(poles)
    maker = BRepBuilderAPI_MakeEdge(curve)
    if not maker.IsDone():
        raise ValueError(f"Unable to build {feature} edge")
    edge = Edge.cast(maker.Edge())
    if edge is None or not edge.is_closed:
        raise ValueError(f"{feature} is not a closed edge")
    return Wire([edge])


def _split_envelope(
    *,
    hidden_clearance_mm: float,
    shadow_line_depth_mm: float,
) -> Solid:
    """Closed split envelope preserving the exact baffle fairing face."""
    if not 0.0 <= hidden_clearance_mm < PERIMETER_INSET_MM:
        raise ValueError("Hidden clearance must be smaller than the inset")
    seam_targets = shell_source.parent._minimum_energy_control_rings()[-1]
    front_targets = [
        (
            x,
            shell_source.FRONT_Y - ENVELOPE_FRONT_OVERTRAVEL_MM,
            z,
        )
        for x, _y, z in seam_targets
    ]
    shifted_seam_targets = [
        (x, y + shadow_line_depth_mm, z)
        for x, y, z in seam_targets
    ]
    bed_inset = PERIMETER_INSET_MM - hidden_clearance_mm
    bed_targets: list[tuple[float, float, float]] = []
    for x, _y, z in seam_targets:
        radius = math.hypot(x, z)
        scale = (radius - bed_inset) / radius
        bed_targets.append((x * scale, BAFFLE_BED_Y, z * scale))

    builder = BRepOffsetAPI_ThruSections(True, False, 1e-7)
    builder.CheckCompatibility(True)
    for targets, feature in (
        (front_targets, "front split overtravel"),
        (shifted_seam_targets, "shadow-line seam"),
        (bed_targets, "inset print-bed perimeter"),
    ):
        builder.AddWire(_curve_wire(targets, feature=feature).wrapped)
    builder.Build()
    if not builder.IsDone():
        raise ValueError("Unable to build the tapered baffle split envelope")
    envelope = Solid.cast(builder.Shape())
    if envelope is None:
        raise ValueError("Unable to cast the tapered split envelope")
    return _single_solid(
        envelope.clean().fix(),
        feature="tapered baffle split envelope",
    )


def _rounded_rectangle_wire(
    size: float,
    radius: float,
    y: float,
) -> Wire:
    plane = Plane(
        origin=(0.0, y, 0.0),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, 1.0, 0.0),
    )
    with BuildSketch(plane) as sketch:
        RectangleRounded(size, size, radius)
    return sketch.sketch.faces()[0].outer_wire()


def _rounded_rectangle_prism(
    size: float,
    radius: float,
    y0: float,
    y1: float,
) -> Solid:
    if y1 <= y0:
        raise ValueError("Rounded-rectangle prism requires y1 > y0")
    wire = _rounded_rectangle_wire(size, radius, y0)
    face = Face(wire)
    return _single_solid(
        Solid.extrude(face, Vector(0.0, y1 - y0, 0.0)),
        feature="rounded-rectangle prism",
    )


def _rounded_rectangle_ring(
    *,
    outer_size: float,
    outer_radius: float,
    inner_size: float,
    inner_radius: float,
    y0: float,
    y1: float,
) -> Solid:
    outer = _rounded_rectangle_prism(outer_size, outer_radius, y0, y1)
    inner = _rounded_rectangle_prism(
        inner_size,
        inner_radius,
        y0 - 0.1,
        y1 + 0.1,
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="rounded-rectangle ring",
    )


def _lofted_rounded_rectangle(
    sections: tuple[tuple[float, float, float], ...],
    *,
    feature: str,
) -> Solid:
    builder = BRepOffsetAPI_ThruSections(True, False, 1e-7)
    builder.CheckCompatibility(True)
    for size, radius, y in sections:
        builder.AddWire(_rounded_rectangle_wire(size, radius, y).wrapped)
    builder.Build()
    if not builder.IsDone():
        raise ValueError(f"Unable to build {feature}")
    solid = Solid.cast(builder.Shape())
    if solid is None:
        raise ValueError(f"Unable to cast {feature}")
    return _single_solid(solid.clean().fix(), feature=feature)


def _gasket_shoulder() -> Solid:
    rear_y = SHOULDER_Y + SHOULDER_SUPPORT_DEPTH_MM
    outer = _rounded_rectangle_prism(
        SHOULDER_OUTER_SIZE_MM,
        SHOULDER_OUTER_RADIUS_MM,
        SHOULDER_Y,
        rear_y,
    )
    inner = _lofted_rounded_rectangle(
        (
            (
                SHOULDER_FRONT_INNER_SIZE_MM,
                SHOULDER_FRONT_INNER_RADIUS_MM,
                SHOULDER_Y - 0.1,
            ),
            (
                SHOULDER_REAR_INNER_SIZE_MM,
                SHOULDER_REAR_INNER_RADIUS_MM,
                rear_y + 0.1,
            ),
        ),
        feature="support-free gasket-shoulder inner ramp",
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="reinforced gasket shoulder",
    )


def _baffle_gasket_land() -> Solid:
    return _rounded_rectangle_ring(
        outer_size=BAFFLE_LAND_OUTER_SIZE_MM,
        outer_radius=BAFFLE_LAND_OUTER_RADIUS_MM,
        inner_size=GASKET_INNER_SIZE_MM,
        inner_radius=GASKET_INNER_RADIUS_MM,
        y0=BAFFLE_BED_Y - BAFFLE_LAND_THICKNESS_MM,
        y1=BAFFLE_BED_Y,
    )


def _compressed_gasket_reference() -> Solid:
    return _rounded_rectangle_ring(
        outer_size=GASKET_OUTER_SIZE_MM,
        outer_radius=GASKET_OUTER_RADIUS_MM,
        inner_size=GASKET_INNER_SIZE_MM,
        inner_radius=GASKET_INNER_RADIUS_MM,
        y0=BAFFLE_BED_Y,
        y1=SHOULDER_Y,
    )


def _gasket_pocket_cutter() -> Solid:
    lateral_clearance = 0.25
    return _rounded_rectangle_ring(
        outer_size=GASKET_OUTER_SIZE_MM + 2.0 * lateral_clearance,
        outer_radius=GASKET_OUTER_RADIUS_MM + lateral_clearance,
        inner_size=GASKET_INNER_SIZE_MM - 2.0 * lateral_clearance,
        inner_radius=GASKET_INNER_RADIUS_MM - lateral_clearance,
        y0=BAFFLE_BED_Y - 0.1,
        y1=SHOULDER_Y,
    )


def _centered_box(
    x_size: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    *,
    x: float,
) -> Solid:
    return Pos(x, (y0 + y1) / 2.0, (z0 + z1) / 2.0) * Box(
        x_size,
        y1 - y0,
        z1 - z0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )


def _bucket_hook(x: float) -> Solid:
    shank = _centered_box(
        HOOK_WIDTH_MM,
        HOOK_SHANK_FRONT_Y,
        HOOK_SHANK_REAR_Y,
        HOOK_SHANK_BOTTOM_Z,
        HOOK_SHANK_TOP_Z,
        x=x,
    )
    toe_profile = Wire.make_polygon(
        [
            Vector(
                x - HOOK_WIDTH_MM / 2.0,
                HOOK_TOE_REAR_Y,
                HOOK_TOE_TOP_Z,
            ),
            Vector(
                x - HOOK_WIDTH_MM / 2.0,
                HOOK_TOE_FRONT_Y,
                HOOK_TOE_TOP_Z,
            ),
            Vector(
                x - HOOK_WIDTH_MM / 2.0,
                HOOK_TOE_FRONT_Y,
                HOOK_TOE_BOTTOM_Z,
            ),
            Vector(
                x - HOOK_WIDTH_MM / 2.0,
                HOOK_TOE_REAR_Y,
                HOOK_SHANK_BOTTOM_Z,
            ),
        ],
        close=True,
    )
    toe = Solid.extrude(
        Face(toe_profile),
        Vector(HOOK_WIDTH_MM, 0.0, 0.0),
    )
    return _single_solid(
        shank.fuse(toe).clean().fix(),
        feature="bucket top hook",
    )


def _hook_receiver_cutters(x: float) -> list[Solid]:
    clearance = HOOK_SIDE_CLEARANCE_MM
    shank = _centered_box(
        HOOK_WIDTH_MM + 2.0 * clearance,
        HOOK_SHANK_FRONT_Y - clearance,
        BAFFLE_BED_Y + 1.0,
        HOOK_SHANK_BOTTOM_Z - clearance,
        HOOK_SHANK_TOP_Z + clearance,
        x=x,
    )
    toe = _centered_box(
        HOOK_WIDTH_MM + 2.0 * clearance,
        HOOK_TOE_FRONT_Y - clearance,
        HOOK_TOE_REAR_Y + clearance,
        HOOK_TOE_BOTTOM_Z - clearance,
        HOOK_TOE_TOP_Z + clearance,
        x=x,
    )
    closed_cutter = _single_solid(
        shank.fuse(toe).clean().fix(),
        feature="top-hook receiver clearance",
    )
    # The receiver is the swept inverse of the fixed bucket hook over the
    # closing motion, not merely a static pocket.  In baffle coordinates the
    # fixed hook rotates by the opposite of the baffle's opening angle.
    pivot_axis = Axis(
        (0.0, HOOK_PIVOT_Y, HOOK_PIVOT_Z),
        (1.0, 0.0, 0.0),
    )
    return [
        copy.copy(closed_cutter).rotate(pivot_axis, -angle)
        for angle in PIVOT_SWEEP_ANGLES_DEG
    ]


def _fastener_direction() -> Vector:
    direction = Vector(
        0.0,
        FASTENER_DIRECTION_Y,
        FASTENER_DIRECTION_Z,
    )
    return direction.normalized()


def _point_along(start: Vector, distance: float) -> Vector:
    return start + _fastener_direction() * distance


def _cylinder_between(
    start: Vector,
    end: Vector,
    *,
    diameter: float,
) -> Solid:
    delta = end - start
    if abs(delta.X) > 1e-8:
        raise ValueError("Fastener cylinder is constrained to the Y/Z plane")
    length = delta.length
    angle_x = math.degrees(math.atan2(-delta.Y, delta.Z))
    cylinder = Cylinder(
        radius=diameter / 2.0,
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    midpoint = (start + end) * 0.5
    placed = Pos(midpoint.X, midpoint.Y, midpoint.Z) * Rot(
        angle_x,
        0.0,
        0.0,
    ) * cylinder
    return _single_solid(placed, feature="angled fastener cylinder")


def _fastener_points(x: float) -> dict[str, Vector]:
    surface = Vector(x, FASTENER_SURFACE_Y, FASTENER_SURFACE_Z)
    direction = _fastener_direction()
    if abs(direction.Y) < 1e-9:
        raise ValueError("Fastener axis does not reach the baffle plane")
    bed_distance = (BAFFLE_BED_Y - surface.Y) / direction.Y
    if bed_distance <= 0.0:
        raise ValueError("Fastener axis points away from the baffle")
    bed = surface + direction * bed_distance
    return {
        "surface": surface,
        "bed": bed,
        "insert_end": bed + direction * BAFFLE_INSERT_DEPTH_MM,
        "boss_end": bed
        + direction
        * (BAFFLE_INSERT_DEPTH_MM + BAFFLE_INSERT_WALL_MM),
    }


def _baffle_insert_boss(x: float) -> Solid:
    points = _fastener_points(x)
    # Start the added cylindrical reinforcement well inside the existing
    # baffle.  Its oblique circular end face would otherwise cross the bed
    # plane even though its axis starts on-plane, preventing the baffle from
    # lying flat for printing.
    return _cylinder_between(
        points["bed"]
        + _fastener_direction() * BAFFLE_BOSS_EMBED_START_MM,
        points["boss_end"],
        diameter=(
            BAFFLE_INSERT_POCKET_D_MM + 2.0 * BAFFLE_INSERT_WALL_MM
        ),
    )


def _baffle_insert_pocket(x: float) -> Solid:
    points = _fastener_points(x)
    return _cylinder_between(
        points["bed"] - _fastener_direction() * 0.2,
        points["insert_end"],
        diameter=BAFFLE_INSERT_POCKET_D_MM,
    )


def _bucket_fastener_cutters(x: float) -> tuple[Solid, Solid, Solid]:
    points = _fastener_points(x)
    direction = _fastener_direction()
    surface = points["surface"]
    head = _cylinder_between(
        surface - direction * 0.5,
        surface + direction * SCREW_HEAD_POCKET_DEPTH_MM,
        diameter=SCREW_HEAD_POCKET_D_MM,
    )
    guide_start = surface + direction * BUCKET_GUIDE_INSERT_START_MM
    guide = _cylinder_between(
        guide_start,
        guide_start + direction * BUCKET_GUIDE_INSERT_LENGTH_MM,
        diameter=BUCKET_GUIDE_POCKET_D_MM,
    )
    through = _cylinder_between(
        surface - direction * 1.0,
        points["bed"] + direction * 1.0,
        diameter=SCREW_CLEARANCE_D_MM,
    )
    return head, guide, through


def _annular_insert_reference(
    start: Vector,
    end: Vector,
    *,
    outer_diameter: float,
    inner_diameter: float,
) -> Solid:
    outer = _cylinder_between(start, end, diameter=outer_diameter)
    inner = _cylinder_between(
        start - _fastener_direction() * 0.1,
        end + _fastener_direction() * 0.1,
        diameter=inner_diameter,
    )
    return _single_solid(
        outer.cut(inner).clean().fix(),
        feature="annular heat-set insert reference",
    )


def _fastener_references() -> dict[str, Compound]:
    guide_inserts: list[Solid] = []
    baffle_inserts: list[Solid] = []
    screws: list[Solid] = []
    direction = _fastener_direction()
    for x in (-FASTENER_X_MM, FASTENER_X_MM):
        points = _fastener_points(x)
        guide_start = (
            points["surface"]
            + direction * BUCKET_GUIDE_INSERT_START_MM
        )
        guide_inserts.append(
            _annular_insert_reference(
                guide_start,
                guide_start
                + direction * BUCKET_GUIDE_INSERT_LENGTH_MM,
                outer_diameter=BUCKET_GUIDE_INSERT_OD_MM,
                inner_diameter=SCREW_CLEARANCE_D_MM,
            )
        )
        baffle_inserts.append(
            _annular_insert_reference(
                points["bed"] + direction * 0.2,
                points["insert_end"],
                outer_diameter=BAFFLE_INSERT_OD_MM,
                inner_diameter=BAFFLE_INSERT_ID_MM,
            )
        )
        screw_shank = _cylinder_between(
            points["surface"] - direction * 1.8,
            points["insert_end"] - direction * 0.5,
            diameter=4.0,
        )
        screw_head = _cylinder_between(
            points["surface"] - direction * 1.8,
            points["surface"] - direction * 0.2,
            diameter=8.5,
        )
        screws.extend((screw_shank, screw_head))
    return {
        "bucket_guide_inserts": Compound(children=guide_inserts),
        "baffle_inserts": Compound(children=baffle_inserts),
        "screws": Compound(children=screws),
    }


def _round_bucket_opening(bucket: Solid) -> tuple[Solid, dict[str, Any]]:
    # The periodic boolean edge is locally valid but OCCT's fillet builder
    # rejects it before STEP healing.  Round-tripping this one intermediate is
    # deliberate and audited; the final deliverables are round-tripped again.
    OUT.mkdir(parents=True, exist_ok=True)
    healed_path = OUT / "bucket_prefillet_healed_reference.step"
    export_step(bucket, healed_path, unit=Unit.MM, write_pcurves=True)
    healed = _single_solid(
        import_step(healed_path),
        feature="STEP-healed bucket before edge round",
    )
    candidates = [
        edge
        for edge in healed.edges()
        if (
            edge.geom_type == GeomType.BSPLINE
            and edge.is_closed
            and edge.bounding_box().size.X > 180.0
            and edge.bounding_box().size.Z > 180.0
            and edge.bounding_box().max.Y < 0.0
        )
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one bucket opening edge, found {len(candidates)}"
        )
    rounded = _single_solid(
        fillet(candidates, radius=BUCKET_EDGE_FILLET_R_MM).clean().fix(),
        feature="rounded bucket opening",
    )
    return rounded, {
        "selected_edge_length_mm": candidates[0].length,
        "radius_mm": BUCKET_EDGE_FILLET_R_MM,
        "step_healing_volume_change_mm3": healed.volume - bucket.volume,
        "rounding_material_change_mm3": rounded.volume - healed.volume,
    }


def _build_joint(full_base: Solid) -> dict[str, Any]:
    baffle_envelope = _split_envelope(
        hidden_clearance_mm=0.0,
        shadow_line_depth_mm=0.0,
    )
    bucket_envelope = _split_envelope(
        hidden_clearance_mm=HIDDEN_FIT_CLEARANCE_MM,
        shadow_line_depth_mm=SHADOW_LINE_DEPTH_MM,
    )
    baffle = _single_solid(
        full_base.intersect(baffle_envelope).clean().fix(),
        feature="separate parabolic conformal front baffle",
    )
    raw_bucket = _single_solid(
        full_base.cut(bucket_envelope).clean().fix(),
        feature="shadow-line enclosure bucket",
    )
    bucket, edge_round = _round_bucket_opening(raw_bucket)
    bucket = _cut_one(
        bucket,
        _gasket_pocket_cutter(),
        feature="bucket with continuous foam-tape pocket",
    )

    shoulder = _gasket_shoulder()
    bucket = _fuse_one(
        bucket,
        shoulder,
        feature="bucket with reinforced gasket shoulder",
    )
    for x in (-HOOK_X_MM, HOOK_X_MM):
        bucket = _fuse_one(
            bucket,
            _bucket_hook(x),
            feature=f"bucket with top hook at x={x:g}",
        )

    baffle = _fuse_one(
        baffle,
        _baffle_gasket_land(),
        feature="baffle with flat gasket land",
    )
    for x in (-HOOK_X_MM, HOOK_X_MM):
        for sweep_index, receiver_cutter in enumerate(
            _hook_receiver_cutters(x),
            start=1,
        ):
            baffle = _cut_one(
                baffle,
                receiver_cutter,
                feature=(
                    f"baffle top-receiver sweep {sweep_index} at x={x:g}"
                ),
            )
    for x in (-FASTENER_X_MM, FASTENER_X_MM):
        baffle = _fuse_one(
            baffle,
            _baffle_insert_boss(x),
            feature=f"baffle with underside insert boss at x={x:g}",
        )
        baffle = _cut_one(
            baffle,
            _baffle_insert_pocket(x),
            feature=f"baffle insert pocket at x={x:g}",
        )
        for index, cutter in enumerate(_bucket_fastener_cutters(x), start=1):
            bucket = _cut_one(
                bucket,
                cutter,
                feature=f"bucket fastener cutter {index} at x={x:g}",
            )

    gasket = _compressed_gasket_reference()
    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    if bucket_baffle_overlap > 0.01:
        raise ValueError(
            "Closed bucket/baffle interference is "
            f"{bucket_baffle_overlap:.6f} mm3"
        )
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(gasket_bucket_overlap, gasket_baffle_overlap) > 0.01:
        raise ValueError(
            "Compressed gasket overlaps a hard part: "
            f"bucket={gasket_bucket_overlap:.6f}, "
            f"baffle={gasket_baffle_overlap:.6f} mm3"
        )

    target_fairing_area = parent._build_parabolic_conformal_geometry()[
        "outer_fairing_area_mm2"
    ]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_fairing_area) <= 1e-5
    ]
    if len(fairing_faces) != 1:
        raise ValueError(
            "The closure changed the exact exterior fairing face: "
            f"found {len(fairing_faces)} matches"
        )

    large_radii = sorted(
        {
            round(edge.radius, 6)
            for edge in baffle.edges()
            if edge.geom_type == GeomType.CIRCLE and edge.radius > 50.0
        }
    )
    for required_radius in (65.25, 79.0, 87.0):
        if not any(
            abs(radius - required_radius) <= 1e-6
            for radius in large_radii
        ):
            raise ValueError(
                f"Separate baffle lost the R{required_radius:g} interface"
            )

    seam_depths = [
        target[1]
        for target in shell_source.parent._minimum_energy_control_rings()[-1]
    ]
    minimum_print_rise = BAFFLE_BED_Y - max(seam_depths)
    worst_overhang = math.degrees(
        math.atan2(PERIMETER_INSET_MM, minimum_print_rise)
    )
    support_ramp_radial_run = (
        SHOULDER_REAR_INNER_SIZE_MM
        - SHOULDER_FRONT_INNER_SIZE_MM
    ) / 2.0
    support_ramp_angle = math.degrees(
        math.atan2(support_ramp_radial_run, SHOULDER_SUPPORT_DEPTH_MM)
    )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": shoulder,
        "edge_round": edge_round,
        "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
        "gasket_bucket_overlap_mm3": gasket_bucket_overlap,
        "gasket_baffle_overlap_mm3": gasket_baffle_overlap,
        "fairing_face_area_mm2": fairing_faces[0].area,
        "fairing_area_difference_mm2": (
            fairing_faces[0].area - target_fairing_area
        ),
        "large_circular_interface_radii_mm": large_radii,
        "minimum_print_rise_mm": minimum_print_rise,
        "worst_overhang_from_print_axis_deg": worst_overhang,
        "shoulder_ramp_from_print_axis_deg": support_ramp_angle,
    }


def _pivot_sweep(bucket: Solid, baffle: Solid) -> dict[str, Any]:
    pivot_axis = Axis(
        (0.0, HOOK_PIVOT_Y, HOOK_PIVOT_Z),
        (1.0, 0.0, 0.0),
    )
    positions: dict[str, Solid] = {}
    interference: dict[str, float] = {}
    for angle in PIVOT_SWEEP_ANGLES_DEG:
        moved = copy.copy(baffle).rotate(pivot_axis, angle)
        key = f"{angle:g}deg"
        positions[key] = moved
        interference[key] = _shape_volume(bucket.intersect(moved))
    nonzero = {
        key: value for key, value in interference.items() if value > 0.01
    }
    if nonzero:
        raise ValueError(f"Baffle pivot sweep interference: {nonzero}")
    return {
        "positions": positions,
        "interference_mm3": interference,
        "pivot_y_mm": HOOK_PIVOT_Y,
        "pivot_z_mm": HOOK_PIVOT_Z,
        "open_angle_deg": HOOK_OPEN_ANGLE_DEG,
    }


def _closure_acoustic_displacement() -> dict[str, Any]:
    """Finite primitive accounting for material added inside the air domain.

    Subtracting the periodic full shell can return OCCT's oriented complement,
    which is geometrically valid but useless for a finite volume delta.  The
    closure is instead accounted from its explicit added primitives.  Fresh
    deep copies prevent coincident-domain booleans from mutating a later check.
    """
    domain = base._acoustic_domain()
    components: dict[str, Solid] = {
        "gasket_shoulder": _gasket_shoulder(),
        "left_hook": _bucket_hook(-HOOK_X_MM),
        "right_hook": _bucket_hook(HOOK_X_MM),
        "baffle_gasket_land": _baffle_gasket_land(),
        "left_insert_boss": _baffle_insert_boss(-FASTENER_X_MM),
        "right_insert_boss": _baffle_insert_boss(FASTENER_X_MM),
        "compressed_gasket": _compressed_gasket_reference(),
    }

    def domain_volume(shape: Any) -> float:
        return _shape_volume(
            copy.deepcopy(shape).intersect(copy.deepcopy(domain))
        )

    component_volumes = {
        name: domain_volume(shape) for name, shape in components.items()
    }
    overlap_pairs = (
        ("baffle_gasket_land", "left_insert_boss"),
        ("baffle_gasket_land", "right_insert_boss"),
    )
    overlap_volumes: dict[str, float] = {}
    for first, second in overlap_pairs:
        overlap = copy.deepcopy(components[first]).intersect(
            copy.deepcopy(components[second])
        )
        key = f"{first}__{second}"
        overlap_volumes[key] = 0.0 if overlap is None else domain_volume(overlap)
    total = sum(component_volumes.values()) - sum(overlap_volumes.values())
    if not 0.0 < total < 250_000.0:
        raise ValueError(
            f"Closure acoustic displacement is implausible: {total:.6f} mm3"
        )
    return {
        "method": "finite added closure primitives intersected with acoustic domain",
        "component_displacement_mm3": component_volumes,
        "pair_overlap_correction_mm3": overlap_volumes,
        "total_displacement_mm3": total,
    }


def _print_oriented_bucket(bucket: Solid) -> Solid:
    rotated = bucket.rotate(Axis.X, -90.0)
    return copy.copy(rotated).moved(Pos(0.0, 0.0, 115.0))


def _print_oriented_baffle(baffle: Solid) -> Solid:
    rotated = baffle.rotate(Axis.X, -90.0)
    return copy.copy(rotated).moved(Pos(0.0, 0.0, BAFFLE_BED_Y))


def _retained_assembly_solids(
    assembly: Any,
    original_base: Solid,
) -> list[Solid]:
    original_bbox = original_base.bounding_box()
    candidates: list[Solid] = []
    retained: list[Solid] = []
    for solid in assembly.solids():
        bbox = solid.bounding_box()
        if (
            abs(solid.volume - original_base.volume) <= 2.0
            and abs(bbox.size.X - original_bbox.size.X) <= 0.01
            and abs(bbox.size.Y - original_bbox.size.Y) <= 0.01
            and abs(bbox.size.Z - original_bbox.size.Z) <= 0.01
        ):
            candidates.append(solid)
        else:
            retained.append(copy.copy(solid))
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one full base in inherited assembly, found {len(candidates)}"
        )
    return retained


def _new_to_inherited_interference(
    bucket: Solid,
    baffle: Solid,
    gasket: Solid,
    retained: list[Solid],
    original_base: Solid,
) -> dict[str, float]:
    checks: dict[str, float] = {}
    for part_name, part in (
        ("bucket", bucket),
        ("baffle", baffle),
        ("gasket", gasket),
    ):
        checks[f"{part_name}_contact_mm3"] = sum(
            _shape_volume(part.intersect(solid)) for solid in retained
        )
    checks["inherited_baseline_contact_mm3"] = sum(
        _shape_volume(original_base.intersect(solid)) for solid in retained
    )
    checks["closed_closure_contact_mm3"] = sum(
        checks[key]
        for key in (
            "bucket_contact_mm3",
            "baffle_contact_mm3",
            "gasket_contact_mm3",
        )
    )
    checks["new_excess_interference_mm3"] = max(
        0.0,
        checks["closed_closure_contact_mm3"]
        - checks["inherited_baseline_contact_mm3"],
    )
    return checks


def _true_cutaway(
    bucket: Solid,
    baffle: Solid,
    gasket: Solid,
    inherited_cutaway: Any,
) -> Compound:
    def face_half(shape: Solid) -> Compound:
        # The inherited helper clips exactly on X=0.  The new swept receiver
        # faces can retain a few tolerance-scale microns on the positive side
        # of that plane, so this local viewer-only cut is offset 0.02 mm into
        # the discarded half.  No manufacturing solid uses this operation.
        bbox = shape.bounding_box()
        margin = 2.0
        max_x = -0.02
        clip = Pos(
            (bbox.min.X - margin + max_x) / 2.0,
            (bbox.min.Y + bbox.max.Y) / 2.0,
            (bbox.min.Z + bbox.max.Z) / 2.0,
        ) * Box(
            max_x - (bbox.min.X - margin),
            bbox.size.Y + 2.0 * margin,
            bbox.size.Z + 2.0 * margin,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        fragments: list[Face] = []
        for face in shape.faces():
            clipped = face.intersect(clip)
            if clipped is None:
                continue
            fragments.extend(
                fragment
                for fragment in clipped.faces()
                if fragment.area > 1e-8
            )
        cut = Compound(children=fragments)
        if (
            not fragments
            or not all(_is_valid(face) for face in fragments)
            or cut.bounding_box().max.X > -0.019
            or not _is_valid(cut)
        ):
            raise ValueError("Local closure face cutaway is invalid")
        return cut

    bucket_half = face_half(bucket)
    baffle_half = face_half(baffle)
    gasket_half = face_half(gasket)
    return Compound(
        children=[
            *[copy.copy(face) for face in bucket_half.faces()],
            *[copy.copy(face) for face in baffle_half.faces()],
            *[copy.copy(face) for face in gasket_half.faces()],
            *[copy.copy(solid) for solid in inherited_cutaway.solids()],
        ]
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
    cad._set_viewer_edge_mode(viewer_dir, face_only=False)
    model_data = viewer_dir / "model-data.js"
    payload = model_data.read_bytes()
    if cutaway:
        payload = payload.replace(
            b'"reset_camera":"iso"',
            (
                b'"reset_camera":"keep",'
                b'"position":[600.0,-350.0,350.0],'
                b'"target":[0.0,5.0,0.0],"zoom":1.0'
            ),
            1,
        )
        payload = payload.replace(
            b'"color":"#6ab7ff"',
            b'"color":"#e8b024"',
        )
        payload = payload.replace(b'"renderback":false', b'"renderback":true')
    model_data.write_bytes(payload)


def _generate_viewers() -> None:
    viewer_specs = (
        ("hooked_gasketed_baffle_assembled.step", "viewer", False),
        ("hooked_gasketed_baffle_cutaway.step", "cutaway_viewer", True),
        ("hooked_gasketed_baffle_exploded.step", "exploded_viewer", False),
        ("hooked_gasketed_baffle_open.step", "open_viewer", False),
        ("retention_hardware_reference.step", "hardware_viewer", False),
    )
    for source_filename, viewer_name, cutaway in viewer_specs:
        viewer_dir = OUT / viewer_name
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source_filename),
                "--out",
                str(viewer_dir),
            ],
            check=True,
        )
        _configure_viewer(viewer_dir, cutaway=cutaway)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

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
    parent._full_detail_base = prior._solid_rear_detail_base

    diagnostics = parent.generate()
    full_base = _single_solid(
        import_step(OUT / "sand_cube_190x210_single_oval_port_base.step"),
        feature="round-tripped solid-rear full-detail enclosure",
    )
    joint = _build_joint(full_base)
    bucket = joint["bucket"]
    baffle = joint["baffle"]
    gasket = joint["gasket"]
    pivot = _pivot_sweep(bucket, baffle)
    hardware = _fastener_references()

    inherited_assembly = import_step(
        OUT / "sand_cube_190x210_single_oval_port_assembly.step"
    )
    retained = _retained_assembly_solids(inherited_assembly, full_base)
    inherited_checks = _new_to_inherited_interference(
        bucket,
        baffle,
        gasket,
        retained,
        full_base,
    )
    if inherited_checks["new_excess_interference_mm3"] > 0.01:
        raise ValueError(
            "New closure interferes with inherited assembly: "
            f"{inherited_checks}"
        )

    assembled_shell = Compound(
        children=[copy.copy(bucket), copy.copy(gasket), copy.copy(baffle)]
    )
    exploded_shell = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(gasket).moved(Pos(0.0, -18.0, 0.0)),
            copy.copy(baffle).moved(
                Pos(0.0, -EXPLODED_BAFFLE_OFFSET_MM, 0.0)
            ),
            *[
                copy.copy(solid)
                for solid in hardware["bucket_guide_inserts"].solids()
            ],
            *[
                copy.copy(solid).moved(
                    Pos(0.0, -EXPLODED_BAFFLE_OFFSET_MM, 0.0)
                )
                for solid in hardware["baffle_inserts"].solids()
            ],
        ]
    )
    open_shell = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(gasket),
            copy.copy(pivot["positions"][f"{HOOK_OPEN_ANGLE_DEG:g}deg"]),
        ]
    )
    full_system = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(gasket),
            copy.copy(baffle),
            *[copy.copy(solid) for solid in retained],
        ]
    )
    inherited_cutaway = import_step(
        OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
    )
    cutaway = _true_cutaway(
        bucket,
        baffle,
        gasket,
        inherited_cutaway,
    )
    bucket_print = _print_oriented_bucket(bucket)
    baffle_print = _print_oriented_baffle(baffle)
    hardware_reference = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(baffle),
            *[
                copy.copy(solid)
                for group in hardware.values()
                for solid in group.solids()
            ],
        ]
    )

    exports = {
        "hooked_gasketed_bucket.step": bucket,
        "hooked_gasketed_front_baffle.step": baffle,
        "compressed_5x2mm_foam_gasket_reference.step": gasket,
        "hooked_gasketed_bucket_print_orientation.step": bucket_print,
        "hooked_gasketed_baffle_print_orientation.step": baffle_print,
        "hooked_gasketed_baffle_assembled.step": assembled_shell,
        "hooked_gasketed_baffle_exploded.step": exploded_shell,
        "hooked_gasketed_baffle_open.step": open_shell,
        "hooked_gasketed_baffle_full_system.step": full_system,
        "hooked_gasketed_baffle_cutaway.step": cutaway,
        "retention_hardware_reference.step": hardware_reference,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    inherited_interferences = diagnostics["geometry"]["interference_mm3"]
    nonzero_inherited = {
        key: value
        for key, value in inherited_interferences.items()
        if abs(value) > 1e-6
    }
    if nonzero_inherited:
        raise ValueError(
            f"Inherited full-system interference returned: {nonzero_inherited}"
        )

    acoustic_displacement = _closure_acoustic_displacement()
    added_acoustic_material_mm3 = acoustic_displacement[
        "total_displacement_mm3"
    ]
    baseline_net_l = diagnostics["volume_accounting"][
        "final_modeled_net_box_volume_l"
    ]
    modeled_net_l = baseline_net_l - added_acoustic_material_mm3 / 1_000_000.0
    baseline_tuning_hz = diagnostics["port"]["lengths"][
        "calculated_tuning_hz"
    ]
    modeled_tuning_hz = baseline_tuning_hz * math.sqrt(
        baseline_net_l / modeled_net_l
    )
    port_length = diagnostics["port"]["lengths"][
        "physical_centerline_length_mm"
    ]

    bucket_print_bbox = bucket_print.bounding_box()
    baffle_print_bbox = baffle_print.bounding_box()
    fastener_angle_from_bottom_normal_deg = math.degrees(
        math.acos(_fastener_direction().Z)
    )
    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete hooked, gasketed, two-underside-screw printable closure "
        "prototype"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_hooked_gasketed_baffle"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_hooked_gasketed_baffle"
        ),
        "printable_bucket_parent_modified": False,
        "committed_full_system_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["hooked_gasketed_closure"] = {
        "visible_seam": {
            "location": "exact G1 fairing-to-flat-wall tangent boundary",
            "intentional_shadow_line_depth_mm": SHADOW_LINE_DEPTH_MM,
            "hidden_fit_clearance_at_bed_mm": HIDDEN_FIT_CLEARANCE_MM,
            "bucket_edge_fillet": joint["edge_round"],
            "bucket_to_baffle_interference_mm3": joint[
                "bucket_baffle_overlap_mm3"
            ],
        },
        "gasket": {
            "specified_tape_width_mm": GASKET_TAPE_WIDTH_MM,
            "specified_uncompressed_thickness_mm": (
                GASKET_UNCOMPRESSED_THICKNESS_MM
            ),
            "modeled_closed_gap_mm": GASKET_CLOSED_GAP_MM,
            "modeled_compression_mm": GASKET_COMPRESSION_MM,
            "modeled_compression_percent": GASKET_COMPRESSION_PERCENT,
            "continuous_closed_loop": True,
            "interrupted_by_hooks_or_fasteners": False,
            "gasket_to_bucket_interference_mm3": joint[
                "gasket_bucket_overlap_mm3"
            ],
            "gasket_to_baffle_interference_mm3": joint[
                "gasket_baffle_overlap_mm3"
            ],
        },
        "reinforced_bucket_rim": {
            "shoulder_outer_size_mm": SHOULDER_OUTER_SIZE_MM,
            "flat_shoulder_radial_width_at_mid_side_mm": (
                (SHOULDER_OUTER_SIZE_MM - SHOULDER_FRONT_INNER_SIZE_MM)
                / 2.0
            ),
            "support_depth_mm": SHOULDER_SUPPORT_DEPTH_MM,
            "support_ramp_from_print_axis_deg": joint[
                "shoulder_ramp_from_print_axis_deg"
            ],
            "knife_edge_replaced_by_rounded_reinforced_rim": True,
        },
        "upper_retention": {
            "mechanism": "two discrete bucket hooks into rear-open baffle receivers",
            "hook_count": 2,
            "hook_width_mm": HOOK_WIDTH_MM,
            "per_side_clearance_mm": HOOK_SIDE_CLEARANCE_MM,
            "male_hooks_on_bucket_for_flat_baffle_print_bed": True,
            "pivot_axis_y_mm": pivot["pivot_y_mm"],
            "pivot_axis_z_mm": pivot["pivot_z_mm"],
            "demonstrated_open_angle_deg": pivot["open_angle_deg"],
            "pivot_sweep_interference_mm3": pivot["interference_mm3"],
        },
        "underside_fasteners": {
            "count": 2,
            "screw_nominal": "M4",
            "entry_face": "speaker underside",
            "angle_from_bottom_face_normal_deg": (
                fastener_angle_from_bottom_normal_deg
            ),
            "clamping_action": "upward into hooks and rearward into gasket",
            "bucket_guide_concept": (
                "short M5-class heat-set sleeve pocket with M4 clearance"
            ),
            "bucket_guide_pocket_diameter_mm": BUCKET_GUIDE_POCKET_D_MM,
            "bucket_guide_insert_reference_od_mm": (
                BUCKET_GUIDE_INSERT_OD_MM
            ),
            "bucket_guide_insert_length_mm": (
                BUCKET_GUIDE_INSERT_LENGTH_MM
            ),
            "baffle_insert_pocket_diameter_mm": BAFFLE_INSERT_POCKET_D_MM,
            "baffle_insert_depth_mm": BAFFLE_INSERT_DEPTH_MM,
            "hardware_fit_coupon_required": True,
        },
        "preserved_front": {
            "outer_fairing_face_area_mm2": joint[
                "fairing_face_area_mm2"
            ],
            "outer_fairing_area_difference_mm2": joint[
                "fairing_area_difference_mm2"
            ],
            "large_circular_interface_radii_mm": joint[
                "large_circular_interface_radii_mm"
            ],
            "driver_collar_rear_plane_y_mm": BAFFLE_BED_Y,
            "black_hole_and_driver_insert_geometry_preserved": True,
            "conformal_inner_wall_preserved": True,
        },
        "print_orientation": {
            "bucket": "solid exterior rear face on Z=0 bed",
            "baffle": "driver collar and gasket land on Z=0 bed",
            "minimum_baffle_rise_at_pulled_corner_mm": joint[
                "minimum_print_rise_mm"
            ],
            "worst_baffle_overhang_from_print_axis_deg": joint[
                "worst_overhang_from_print_axis_deg"
            ],
            "gasket_shoulder_ramp_from_print_axis_deg": joint[
                "shoulder_ramp_from_print_axis_deg"
            ],
            "bucket_print_bbox_min_z_mm": bucket_print_bbox.min.Z,
            "bucket_print_bbox_max_z_mm": bucket_print_bbox.max.Z,
            "baffle_print_bbox_min_z_mm": baffle_print_bbox.min.Z,
            "baffle_print_bbox_max_z_mm": baffle_print_bbox.max.Z,
            "supports_expected_for_primary_shell_surfaces": False,
            "small_angled_fastener_bore_should_be_drilled_or_fit_coupon_tested": True,
        },
        "new_to_inherited_interference_mm3": inherited_checks,
    }
    diagnostics["preserved_full_detail_contract"].update(
        {
            "dual_skin_2_3_2_walls": "side and roof only",
            "solid_rear_wall": True,
            "separate_front_baffle": True,
            "full_inherited_bracing_and_service_features": True,
        }
    )
    diagnostics["manufacturing_effect"] = {
        "baseline_modeled_net_volume_l": baseline_net_l,
        "added_closure_material_inside_acoustic_domain_mm3": (
            added_acoustic_material_mm3
        ),
        "acoustic_displacement_accounting": acoustic_displacement,
        "modeled_net_volume_l": modeled_net_l,
        "net_volume_change_from_printable_bucket_parent_l": (
            modeled_net_l - baseline_net_l
        ),
        "physical_port_length_mm": port_length,
        "port_length_change_mm": 0.0,
        "baseline_modeled_natural_tuning_hz": baseline_tuning_hz,
        "modeled_natural_tuning_hz": modeled_tuning_hz,
        "tuning_change_hz": modeled_tuning_hz - baseline_tuning_hz,
        "inherited_zero_interference_check_count": len(
            inherited_interferences
        ),
        "new_bucket_baffle_interference_mm3": joint[
            "bucket_baffle_overlap_mm3"
        ],
    }
    diagnostics["geometry"]["hooked_closure_step_roundtrip"] = step_roundtrip
    diagnostics["files"].update(
        {
            **{filename: str(OUT / filename) for filename in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "index.html"),
            "cutaway_viewer": str(
                OUT / "cutaway_viewer" / "index.html"
            ),
            "exploded_viewer": str(
                OUT / "exploded_viewer" / "index.html"
            ),
            "open_viewer": str(OUT / "open_viewer" / "index.html"),
            "hardware_viewer": str(
                OUT / "hardware_viewer" / "index.html"
            ),
        }
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
