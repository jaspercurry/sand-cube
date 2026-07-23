"""Generate the lightweight, coherently sealed and braced G1 enclosure."""

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
from cad_runner.outputs import job_output_path

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
    Compound,
    Edge,
    Face,
    Pos,
    RegularPolygon,
    Rot,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    extrude,
    import_step,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_systemic_joint_recessed_fasteners"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_systemic_joint_recessed_fasteners as previous  # noqa: E402


single = previous.previous
simplified = single.previous
source = previous.source
closure = previous.closure
base = previous.base
parent = previous.parent
centered = simplified.centered
rear_source = source.prior.parent.source
serviceable = rear_source.serviceable
absorber = rear_source.prior

OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
NAME = "sand_cube_190x210_parabolic_g1_lightweight_coherent_closure"

# The exact inherited gasket perimeter is retained except for a 1.3 mm deeper
# smooth top/bottom fastener bypass.  Each nut-loading mouth is cut directly
# into the printer-bed gasket/collar face in the screw bore's center plane.
PATH_HALF_SIZE_MM = single.PATH_HALF_SIZE_MM
SEAL_LAND_WIDTH_MM = single.SEAL_LAND_WIDTH_MM
GASKET_WIDTH_MM = single.GASKET_WIDTH_MM
GASKET_EDGE_MARGIN_MM = single.GASKET_EDGE_MARGIN_MM
SERVICE_BYPASS_HALF_WIDTH_MM = single.SCREW_BYPASS_HALF_WIDTH_MM
SERVICE_BYPASS_DEPTH_MM = 5.30

SAND_CAP_THICKNESS_MM = 3.0
FRONT_BULKHEAD_THICKNESS_MM = SAND_CAP_THICKNESS_MM
FRONT_BULKHEAD_SUPPORT_DROP_MM = 4.0
FRONT_BULKHEAD_ROOT_DEPTH_MM = 0.50
FRONT_BULKHEAD_FILL_CLEARANCE_MM = 0.0
FINAL_FILL_PASSAGE_CLEARANCE_MM = 0.05
BAFFLE_STRUCTURE_THICKNESS_MM = 3.0
BRIDGE_INNER_RADIUS_MM = 77.5
BRIDGE_OUTER_RADIUS_MM = 88.75
BRIDGE_INNER_HALF_WIDTH_MM = 14.0
BRIDGE_OUTER_HALF_WIDTH_MM = 20.0
CORNER_CLOSURE_LAND_OVERLAP_MM = 0.30
CORNER_CLOSURE_CLIP_OVERLAP_MM = 0.50

FASTENER_X_MM = previous.FASTENER_X_MM
FASTENER_SURFACE_Y_MM = previous.FASTENER_SURFACE_Y_MM
FASTENER_SURFACE_ABS_Z_MM = previous.FASTENER_SURFACE_ABS_Z_MM
FASTENER_ANGLE_FROM_FACE_NORMAL_DEG = (
    previous.FASTENER_ANGLE_FROM_FACE_NORMAL_DEG
)
NUT_AXIS_DISTANCE_MM = previous.NUT_AXIS_DISTANCE_MM
SCREW_NOMINAL_D_MM = previous.SCREW_NOMINAL_D_MM
SCREW_CLEARANCE_D_MM = previous.SCREW_CLEARANCE_D_MM
SCREW_HEAD_REFERENCE_D_MM = previous.SCREW_HEAD_REFERENCE_D_MM
SCREW_HEAD_REFERENCE_THICKNESS_MM = (
    previous.SCREW_HEAD_REFERENCE_THICKNESS_MM
)
HEAD_COUNTERBORE_D_MM = previous.HEAD_COUNTERBORE_D_MM
HEAD_COUNTERBORE_DEPTH_MM = previous.HEAD_COUNTERBORE_DEPTH_MM
BUCKET_SLEEVE_D_MM = previous.BUCKET_SLEEVE_D_MM
BUCKET_SLEEVE_AXIS_END_MM = previous.BUCKET_SLEEVE_AXIS_END_MM
SCREW_BLISTER_AXIS_START_MM = -0.80
BAFFLE_RELIEF_D_MM = previous.BAFFLE_RELIEF_D_MM
BAFFLE_RELIEF_AXIS_START_MM = previous.BAFFLE_RELIEF_AXIS_START_MM
BAFFLE_RELIEF_AXIS_END_MM = previous.BAFFLE_RELIEF_AXIS_END_MM
M4_NUT_PITCH_MM = 0.70
M4_NUT_ACROSS_FLATS_MM = 7.0
M4_NUT_HEIGHT_MM = 3.2
M4_NUT_ACROSS_CORNERS_MM = 2.0 * M4_NUT_ACROSS_FLATS_MM / math.sqrt(3.0)
M4_NUT_POCKET_ACROSS_FLATS_MM = 7.40
M4_NUT_POCKET_HEIGHT_MM = 3.60
NUT_LOADING_SLOT_WIDTH_MM = 7.50
NUT_LOADING_SLOT_HEIGHT_MM = 3.60
NUT_LOADING_FACE_ENTRY_X_MM = FASTENER_X_MM
NUT_LOADING_FACE_INWARD_OFFSET_MM = 1.0
NUT_LOADING_SEAT_OVERTRAVEL_MM = 0.25
NUT_LOADING_FACE_OVERTRAVEL_MM = 0.80
NUT_BLOCK_WIDTH_X_MM = 18.0
NUT_BLOCK_DEPTH_Y_MM = 12.0
NUT_BLOCK_HEIGHT_Z_MM = 18.0
NUT_BEARING_AUDIT_THICKNESS_MM = previous.NUT_BEARING_AUDIT_THICKNESS_MM

MAX_ALLOWED_INTERFERENCE_MM3 = previous.MAX_ALLOWED_INTERFERENCE_MM3
MINIMUM_GASKET_SUPPORT_RATIO = previous.MINIMUM_GASKET_SUPPORT_RATIO
MINIMUM_NUT_BEARING_SUPPORT_RATIO = previous.MINIMUM_NUT_BEARING_SUPPORT_RATIO
MINIMUM_HEAD_BEARING_SUPPORT_RATIO = previous.MINIMUM_HEAD_BEARING_SUPPORT_RATIO
FAIRING_AREA_TOLERANCE_MM2 = previous.FAIRING_AREA_TOLERANCE_MM2

CURRENT_SYSTEMIC_NET_VOLUME_L = 4.347153782665813
CURRENT_SYSTEMIC_CLOSURE_DISPLACEMENT_MM3 = 59036.13648536992

_JOINT_AUDIT: dict[str, Any] = {}
_FILL_AUDIT: dict[str, Any] = {}
_FASTENER_AUDIT: dict[str, Any] = {}
_BRACE_AUDIT: dict[str, Any] = {}


def _shape_volume(shape: Any) -> float:
    return previous._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return previous._single_solid(shape, feature=feature)


def _cut_one(shape: Solid, cutter: Any, *, feature: str) -> Solid:
    return previous._cut_one(shape, cutter, feature=feature)


def _fuse_one(shape: Solid, addition: Any, *, feature: str) -> Solid:
    return previous._fuse_one(shape, addition, feature=feature)


def _xz_prism(
    points: tuple[tuple[float, float], ...],
    y0_mm: float,
    y1_mm: float,
    *,
    feature: str,
) -> Solid:
    def wire_at_y(y_mm: float) -> Wire:
        edges = [
            Edge.make_line(
                (points[index][0], y_mm, points[index][1]),
                (
                    points[(index + 1) % len(points)][0],
                    y_mm,
                    points[(index + 1) % len(points)][1],
                ),
            )
            for index in range(len(points))
        ]
        wires = Wire.combine(edges)
        if len(wires) != 1 or not wires[0].is_closed:
            raise ValueError(f"{feature} profile did not close")
        return wires[0]

    return _single_solid(
        Solid.make_loft(
            [wire_at_y(y0_mm), wire_at_y(y1_mm)],
            ruled=True,
        ).clean().fix(),
        feature=feature,
    )


def _baffle_tapered_bridges(nominal_envelope: Solid) -> list[Solid]:
    y0 = source.BAFFLE_BED_Y - BAFFLE_STRUCTURE_THICKNESS_MM
    y1 = source.BAFFLE_BED_Y
    top_points = (
        (-BRIDGE_INNER_HALF_WIDTH_MM, BRIDGE_INNER_RADIUS_MM),
        (BRIDGE_INNER_HALF_WIDTH_MM, BRIDGE_INNER_RADIUS_MM),
        (BRIDGE_OUTER_HALF_WIDTH_MM, BRIDGE_OUTER_RADIUS_MM),
        (-BRIDGE_OUTER_HALF_WIDTH_MM, BRIDGE_OUTER_RADIUS_MM),
    )
    top = _xz_prism(
        top_points,
        y0,
        y1,
        feature="broad tapered baffle collar bridge",
    )
    bridges: list[Solid] = []
    for index, angle_deg in enumerate((0.0, 90.0, 180.0, -90.0), start=1):
        bridge = _single_solid(
            ((Rot(0.0, angle_deg, 0.0) * top) & nominal_envelope)
            .clean().fix(),
            feature=f"envelope-clipped tapered baffle bridge {index}",
        )
        bridges.append(bridge)
    return bridges


def _baffle_corner_closure_panels(
    original_baffle: Solid,
    original_bucket: Solid,
) -> tuple[list[Solid], dict[str, float], list[float]]:
    """Fill four seal-radius gaps within the original baffle perimeter."""
    y0 = source.BAFFLE_BED_Y - BAFFLE_STRUCTURE_THICKNESS_MM
    y1 = source.BAFFLE_BED_Y
    y_mid = (y0 + y1) / 2.0
    original_rear_faces = [
        face
        for face in original_baffle.faces()
        if face.bounding_box().size.Y < 0.01
        and abs(face.center().Y - source.BAFFLE_BED_Y) < 0.01
    ]
    if len(original_rear_faces) != 1:
        raise ValueError(
            "Expected one original planar rear baffle face, found "
            f"{len(original_rear_faces)}"
        )
    original_rear_face = original_rear_faces[0]
    original_outer_wire = original_rear_face.outer_wire()
    original_perimeter_face = Face(original_outer_wire)
    outer_baffle_face = _single_solid(
        Solid.extrude(
            original_perimeter_face,
            Vector(0.0, -BAFFLE_STRUCTURE_THICKNESS_MM, 0.0),
        ).clean().fix(),
        feature="original-perimeter baffle corner-fill envelope",
    )
    retained_land_envelope = single._loft_between_offsets(
        SEAL_LAND_WIDTH_MM / 2.0 - CORNER_CLOSURE_LAND_OVERLAP_MM,
        y0 - 0.10,
        SEAL_LAND_WIDTH_MM / 2.0 - CORNER_CLOSURE_LAND_OVERLAP_MM,
        y1 + 0.10,
        feature="corner-closure land overlap envelope",
    )
    outside_land_cut = outer_baffle_face.cut(retained_land_envelope)
    outside_land = Compound(children=list(outside_land_cut.solids()))

    original_bounds = original_outer_wire.bounding_box()
    outer_limit = max(
        abs(original_bounds.min.X),
        abs(original_bounds.max.X),
        abs(original_bounds.min.Z),
        abs(original_bounds.max.Z),
    ) + 0.10
    corner_specs = (
        (-1.0, 1.0, single.UPPER_CORNER_CENTER_MM, "top-left"),
        (1.0, 1.0, single.UPPER_CORNER_CENTER_MM, "top-right"),
        (-1.0, -1.0, single.PATH_BOTTOM_CORNER_TANGENCY_MM, "bottom-left"),
        (1.0, -1.0, single.PATH_BOTTOM_CORNER_TANGENCY_MM, "bottom-right"),
    )
    panels: list[Solid] = []
    bucket_trim_volumes: list[float] = []
    for x_sign, z_sign, tangency, label in corner_specs:
        inner_limit = tangency - CORNER_CLOSURE_CLIP_OVERLAP_MM
        span = outer_limit - inner_limit
        center_abs = (outer_limit + inner_limit) / 2.0
        clip = Pos(
            x_sign * center_abs,
            y_mid,
            z_sign * center_abs,
        ) * Box(
            span,
            BAFFLE_STRUCTURE_THICKNESS_MM + 0.20,
            span,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        raw_panel = _single_solid(
            (outside_land & clip).clean().fix(),
            feature=f"{label} original-perimeter corner-gap fill",
        )
        bucket_trim_volumes.append(
            _shape_volume(raw_panel.intersect(original_bucket))
        )
        panel = _single_solid(
            raw_panel.cut(original_bucket).clean().fix(),
            feature=f"{label} bucket-conformal corner-gap fill",
        )
        if abs(panel.bounding_box().size.Y - BAFFLE_STRUCTURE_THICKNESS_MM) > 0.01:
            raise ValueError(f"The {label} closure changed the baffle thickness")
        panels.append(panel)
    return (
        panels,
        {
            "min_x": original_bounds.min.X,
            "max_x": original_bounds.max.X,
            "min_z": original_bounds.min.Z,
            "max_z": original_bounds.max.Z,
        },
        bucket_trim_volumes,
    )


def _front_bulkhead() -> tuple[Solid, Solid, Solid, dict[str, Any]]:
    """One planar face plate plus one constant-height support wedge.

    The plate closes and supports the gasket at the bucket shoulder.  The
    wedge follows the canonical gasket inner edge and lands on the exact
    acoustic-cavity boundary four millimetres lower in the print direction.
    """
    face_y = source.SHOULDER_Y
    plate_rear_y = face_y + FRONT_BULKHEAD_THICKNESS_MM
    inner_edge_offset = -SEAL_LAND_WIDTH_MM / 2.0

    exact_outer = parent._build_parabolic_conformal_geometry()[
        "sculpted_outer"
    ]
    plate_slab = Pos(
        0.0,
        face_y + FRONT_BULKHEAD_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        FRONT_BULKHEAD_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    plate_blank = _single_solid(
        (exact_outer & plate_slab).clean().fix(),
        feature="front bulkhead slab clipped to exact sculpted outer",
    )
    inner_opening = _single_solid(
        Solid.extrude(
            Face(
                single._perimeter_wire(
                    offset_mm=inner_edge_offset,
                    y_mm=face_y - 0.10,
                )
            ),
            Vector(0.0, FRONT_BULKHEAD_THICKNESS_MM + 0.20, 0.0),
        )
        .clean()
        .fix(),
        feature="front bulkhead canonical gasket-face inner opening",
    )

    wedge_top_y = plate_rear_y - 0.10
    wedge_landing_y = plate_rear_y + FRONT_BULKHEAD_SUPPORT_DROP_MM
    wedge_root_y = wedge_landing_y + FRONT_BULKHEAD_ROOT_DEPTH_MM
    wedge_slab = Pos(
        0.0,
        (wedge_top_y + wedge_root_y) / 2.0,
        0.0,
    ) * Box(
        220.0,
        wedge_root_y - wedge_top_y,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    wedge_blank = _single_solid(
        (exact_outer & wedge_slab).clean().fix(),
        feature="support wedge clipped to exact sculpted outer",
    )

    cavity = base._rectangular_cavity()
    cavity_front_y = cavity.bounding_box().min.Y
    cavity_front_faces = [
        face
        for face in cavity.faces()
        if abs(face.center().Y - cavity_front_y) <= 1e-6
    ]
    if not cavity_front_faces:
        raise ValueError("Unable to locate the actual inner-wall front section")
    cavity_front_face = max(cavity_front_faces, key=lambda face: face.area)
    cavity_landing_wire = cavity_front_face.outer_wire().moved(
        Pos(0.0, wedge_landing_y - cavity_front_y, 0.0)
    )
    cavity_root_wire = cavity_front_face.outer_wire().moved(
        Pos(0.0, wedge_root_y + 0.10 - cavity_front_y, 0.0)
    )
    gasket_edge_wire = single._perimeter_wire(
        offset_mm=inner_edge_offset,
        y_mm=wedge_top_y - 0.10,
    )
    opening_builder = BRepOffsetAPI_ThruSections(True, False, 1e-7)
    opening_builder.CheckCompatibility(True)
    opening_builder.AddWire(gasket_edge_wire.wrapped)
    opening_builder.AddWire(cavity_landing_wire.wrapped)
    opening_builder.AddWire(cavity_root_wire.wrapped)
    opening_builder.Build()
    if not opening_builder.IsDone():
        raise ValueError("Unable to loft the bulkhead opening to the inner skin")
    wedge_opening = Solid.cast(opening_builder.Shape())
    if wedge_opening is None:
        raise ValueError("Unable to cast the bulkhead inner-skin opening")
    wedge_opening = _single_solid(
        wedge_opening.clean().fix(),
        feature="front bulkhead opening lofted to actual inner skin",
    )
    support_wedge = _single_solid(
        wedge_blank.cut(wedge_opening).clean().fix(),
        feature="actual-inner-skin front bulkhead support wedge",
    )

    fill_keepouts: list[Solid] = []
    keepout_diameter = (
        base.P.fill_entry_d
        + 2.0 * simplified.FRONT_FILL_SUPPORT_WALL_MM
        + 2.0 * FRONT_BULKHEAD_FILL_CLEARANCE_MM
    )
    for x_sign in (-1.0, 1.0):
        mouth_x = x_sign * simplified.FRONT_FILL_ABS_XZ_MM
        fill_keepouts.append(
            _single_solid(
                source._cylinder_between(
                    Vector(
                        mouth_x,
                        face_y - 0.10,
                        simplified.FRONT_FILL_ABS_XZ_MM,
                    ),
                    Vector(
                        mouth_x,
                        wedge_root_y + 0.10,
                        simplified.FRONT_FILL_ABS_XZ_MM,
                    ),
                    diameter=keepout_diameter,
                ),
                feature="full-depth fill-support approach keepout",
            )
        )
    fill_keepout = Compound(children=fill_keepouts)
    face_plate = _single_solid(
        plate_blank.cut(inner_opening).cut(fill_keepout).clean().fix(),
        feature="single planar front bulkhead face",
    )
    support_wedge = _single_solid(
        support_wedge.cut(fill_keepout).clean().fix(),
        feature="inner-skin support wedge clear of both fill supports",
    )
    coherent_bulkhead = _single_solid(
        face_plate.fuse(support_wedge, tol=0.01).clean().fix(),
        feature="single face-plate and support-wedge front bulkhead",
    )

    cavity_half_width = cavity_front_face.bounding_box().max.X
    cardinal_run = abs(
        PATH_HALF_SIZE_MM + inner_edge_offset - cavity_half_width
    )
    cardinal_angle = math.degrees(
        math.atan2(cardinal_run, FRONT_BULKHEAD_SUPPORT_DROP_MM)
    )
    if cardinal_angle > 45.0:
        raise ValueError(
            "The front bulkhead support wedge cardinal slope exceeds 45 "
            f"degrees from the print axis: {cardinal_angle:.3f} degrees"
        )
    fill_keepout_intrusion = _shape_volume(
        support_wedge.intersect(fill_keepout)
    )
    if fill_keepout_intrusion > 0.01:
        raise ValueError(
            "The completed front bulkhead re-entered a fill-support keepout "
            f"by {fill_keepout_intrusion:.6f} mm3"
        )
    outside_volume = _shape_volume(coherent_bulkhead.cut(exact_outer))
    if outside_volume > 0.01:
        raise ValueError(
            "The front bulkhead escaped the sculpted outer by "
            f"{outside_volume:.6f} mm3"
        )
    return face_plate, support_wedge, coherent_bulkhead, {
        "plate_thickness_mm": FRONT_BULKHEAD_THICKNESS_MM,
        "support_drop_mm": FRONT_BULKHEAD_SUPPORT_DROP_MM,
        "root_depth_mm": FRONT_BULKHEAD_ROOT_DEPTH_MM,
        "support_cardinal_run_mm": cardinal_run,
        "support_cardinal_angle_from_print_axis_deg": cardinal_angle,
        "root_target": "exact rounded acoustic-cavity boundary",
        "fill_keepout_diameter_mm": keepout_diameter,
        "fill_keepout_intrusion_mm3": fill_keepout_intrusion,
        "outside_sculpted_outer_mm3": outside_volume,
    }


def _projected_service_opening_clearance() -> Solid:
    """Clear obsolete fixed-front structure from the removable opening.

    The inherited monocoque has four woofer-collar brace roots that grow
    forward into its fixed front.  Variant A replaces that fixed front with a
    removable baffle, so the canonical gasket-land inner edge is projected
    straight back only as far as the new bulkhead wedge lands on the inner
    skin.  Deeper brace rails remain untouched.
    """
    y0 = (
        source.BAFFLE_BED_Y
        - BAFFLE_STRUCTURE_THICKNESS_MM
        - 0.20
    )
    y1 = (
        source.SHOULDER_Y
        + FRONT_BULKHEAD_THICKNESS_MM
        + FRONT_BULKHEAD_SUPPORT_DROP_MM
        + FRONT_BULKHEAD_ROOT_DEPTH_MM
        + 0.10
    )
    inner_wire = single._perimeter_wire(
        offset_mm=-SEAL_LAND_WIDTH_MM / 2.0,
        y_mm=y0,
    )
    return _single_solid(
        Solid.extrude(Face(inner_wire), Vector(0.0, y1 - y0, 0.0))
        .clean()
        .fix(),
        feature="canonical projected removable service opening",
    )


def _lightweight_common_joint(full_base: Solid) -> dict[str, Any]:
    nominal = closure._nested_split_envelope(clearance_mm=0.0)
    clearance = closure._nested_split_envelope(
        clearance_mm=closure.SOCKET_NORMAL_CLEARANCE_MM
    )
    baffle = _single_solid(
        (full_base & nominal).clean().fix(),
        feature="lightweight nested-seam baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance).clean().fix(),
        feature="coherent rear-bed bucket",
    )
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)

    bucket = _cut_one(
        bucket,
        simplified._broad_interface_reset(
            source.BAFFLE_BED_Y
            - BAFFLE_STRUCTURE_THICKNESS_MM
            - 0.15,
            source.SHOULDER_Y + 0.20,
        ),
        feature="bucket with inherited closure material removed",
    )
    service_opening_clearance = _projected_service_opening_clearance()
    inherited_service_opening_intrusion = _shape_volume(
        bucket.intersect(service_opening_clearance)
    )
    bucket = _cut_one(
        bucket,
        service_opening_clearance,
        feature="bucket with obsolete fixed-front brace roots removed",
    )

    gasket = single._single_face_band(
        GASKET_WIDTH_MM,
        source.BAFFLE_BED_Y,
        source.SHOULDER_Y,
        feature="five-millimeter coherent gasket reference",
    )
    baffle_land = single._single_face_band(
        SEAL_LAND_WIDTH_MM,
        source.BAFFLE_BED_Y - BAFFLE_STRUCTURE_THICKNESS_MM,
        source.BAFFLE_BED_Y,
        feature="continuous coherent baffle gasket land",
    )
    fill_passages: list[Solid] = []
    fill_supports: list[Solid] = []
    fill_audit: dict[str, Any] = {}
    centerline = single._perimeter_wire(
        offset_mm=0.0,
        y_mm=source.SHOULDER_Y,
    )
    final_fill_clearances: list[Solid] = []
    for x_sign, label in ((-1.0, "left"), (1.0, "right")):
        fill = simplified._front_fill_feature(x_sign)
        passage = fill["passage"]
        support = fill["support"]
        mouth = Vector(
            x_sign * simplified.FRONT_FILL_ABS_XZ_MM,
            source.SHOULDER_Y,
            simplified.FRONT_FILL_ABS_XZ_MM,
        )
        path_distance = min(
            edge.distance_to(mouth) for edge in centerline.edges()
        )
        support_clearance = (
            path_distance
            - base.P.fill_entry_d / 2.0
            - simplified.FRONT_FILL_SUPPORT_WALL_MM
            - SEAL_LAND_WIDTH_MM / 2.0
        )
        if support_clearance < single.FILL_TO_LAND_CLEARANCE_MM - 0.01:
            raise ValueError(
                f"The {label} fill support has only "
                f"{support_clearance:.3f} mm gasket-land clearance"
            )
        if float(fill["passage_to_void_mm3"]) <= 0.01:
            raise ValueError(f"The {label} fill passage misses the sand void")
        fill_passages.append(passage)
        fill_supports.append(support)
        fill_audit[label] = {
            "mouth_center_mm": [mouth.X, mouth.Y, mouth.Z],
            "entry_diameter_mm": base.P.fill_entry_d,
            "support_wall_mm": simplified.FRONT_FILL_SUPPORT_WALL_MM,
            "support_to_seal_land_clearance_mm": support_clearance,
            "passage_to_live_sand_void_mm3": fill[
                "passage_to_void_mm3"
            ],
            "print_slope_from_axis_deg": fill["slope_deg"],
        }

    passages = Compound(children=fill_passages)
    face_plate, support_wedge, coherent_bulkhead, bulkhead_audit = (
        _front_bulkhead()
    )
    rooted_bulkhead_bucket_root = _shape_volume(
        coherent_bulkhead.intersect(bucket)
    )
    if rooted_bulkhead_bucket_root <= 0.01:
        raise ValueError("The single front bulkhead has no bucket-wall root")

    for passage, support, label in zip(
        fill_passages,
        fill_supports,
        ("left", "right"),
    ):
        bucket = _cut_one(
            bucket,
            passage,
            feature=f"bucket with unobstructed {label} sand-fill passage",
        )
        bucket = _fuse_one(
            bucket,
            support,
            feature=f"bucket with hollow {label} fill support",
        )
    bucket = _single_solid(
        bucket.fuse(coherent_bulkhead, tol=0.01).clean().fix(),
        feature="bucket with planar face plate and inner-skin support wedge",
    )
    # Reapply the authoritative bores after every closure/support union so
    # Boolean seam tolerances cannot leave a skin across either fill passage.
    for x_sign, label in ((-1.0, "left"), (1.0, "right")):
        mouth_x = x_sign * simplified.FRONT_FILL_ABS_XZ_MM
        final_clearance = _single_solid(
            source._cylinder_between(
                Vector(
                    mouth_x,
                    source.SHOULDER_Y
                    - simplified.FRONT_FILL_MOUTH_OVERTRAVEL_MM,
                    simplified.FRONT_FILL_ABS_XZ_MM,
                ),
                Vector(
                    mouth_x,
                    source.SHOULDER_Y
                    + SAND_CAP_THICKNESS_MM
                    + simplified.FRONT_FILL_CAP_OVERLAP_MM,
                    simplified.FRONT_FILL_ABS_XZ_MM,
                ),
                diameter=(
                    base.P.fill_entry_d
                    + 2.0 * FINAL_FILL_PASSAGE_CLEARANCE_MM
                ),
            ),
            feature=f"{label} final fill-mouth clearance cylinder",
        )
        bucket = _cut_one(
            bucket,
            final_clearance,
            feature=f"bucket with final clear {label} sand-fill passage",
        )
        final_fill_clearances.append(final_clearance)
    unclosed_bucket_bulkhead_volume = _shape_volume(
        coherent_bulkhead.cut(bucket)
    )
    if unclosed_bucket_bulkhead_volume > 0.01:
        raise ValueError(
            "The bucket does not contain the complete front bulkhead: "
            f"{unclosed_bucket_bulkhead_volume:.6f} mm3"
        )
    fill_passage_blockage = _shape_volume(passages.intersect(bucket))
    if fill_passage_blockage > 0.01:
        raise ValueError(
            "The front bulkhead obstructs a sand-fill bore by "
            f"{fill_passage_blockage:.6f} mm3"
        )
    protected_front = Pos(
        0.0,
        source.SHOULDER_Y + FRONT_BULKHEAD_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        FRONT_BULKHEAD_THICKNESS_MM + 0.20,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    exact_outer = parent._build_parabolic_conformal_geometry()[
        "sculpted_outer"
    ]
    protected_front_excess = _shape_volume(
        bucket.cut(exact_outer).intersect(protected_front)
    )
    if protected_front_excess > 0.01:
        raise ValueError(
            "The bucket front escaped the exact sculpted exterior by "
            f"{protected_front_excess:.6f} mm3"
        )
    final_service_opening_intrusion = _shape_volume(
        bucket.intersect(service_opening_clearance)
    )
    if final_service_opening_intrusion > 0.01:
        raise ValueError(
            "The removable service opening is not clear through the "
            "bulkhead support depth: "
            f"{final_service_opening_intrusion:.6f} mm3"
        )

    baffle = _fuse_one(
        baffle,
        baffle_land,
        feature="baffle with continuous perimeter gasket backing",
    )
    bridges = _baffle_tapered_bridges(nominal)
    bridge_roots: list[float] = []
    for index, bridge in enumerate(bridges, start=1):
        root = _shape_volume(bridge.intersect(baffle))
        if root <= 0.01:
            raise ValueError(f"Baffle bridge {index} has no collar/land root")
        bridge_roots.append(root)
        baffle = _fuse_one(
            baffle,
            bridge,
            feature=f"baffle with broad tapered bridge {index}",
        )

    (
        corner_panels,
        original_corner_bounds,
        corner_bucket_trim_volumes,
    ) = _baffle_corner_closure_panels(reference_baffle, reference_bucket)
    corner_land_roots: list[float] = []
    corner_rim_roots: list[float] = []
    for index, panel in enumerate(corner_panels, start=1):
        land_root = _shape_volume(panel.intersect(baffle_land))
        rim_root = _shape_volume(panel.intersect(reference_baffle))
        if land_root <= 0.01:
            raise ValueError(f"Baffle corner closure {index} misses the seal land")
        if rim_root <= 0.01:
            raise ValueError(f"Baffle corner closure {index} misses the outer rim")
        corner_land_roots.append(land_root)
        corner_rim_roots.append(rim_root)
        baffle = _fuse_one(
            baffle,
            panel,
            feature=f"baffle with bounded corner-gap fill {index}",
        )

    unclosed_corner_volume = _shape_volume(
        Compound(children=corner_panels).cut(baffle)
    )
    if unclosed_corner_volume > 0.01:
        raise ValueError(
            "The baffle still has an unclosed corner-face volume of "
            f"{unclosed_corner_volume:.6f} mm3"
        )

    gasket_bucket_probe = single._single_face_band(
        GASKET_WIDTH_MM,
        source.SHOULDER_Y,
        source.SHOULDER_Y + 0.25,
        feature="bucket gasket-support probe",
    )
    gasket_baffle_probe = single._single_face_band(
        GASKET_WIDTH_MM,
        source.BAFFLE_BED_Y - 0.25,
        source.BAFFLE_BED_Y,
        feature="baffle gasket-support probe",
    )
    gasket_bucket_support_ratio = _shape_volume(
        gasket_bucket_probe.intersect(bucket)
    ) / gasket_bucket_probe.volume
    gasket_baffle_support_ratio = _shape_volume(
        gasket_baffle_probe.intersect(baffle)
    ) / gasket_baffle_probe.volume
    if min(
        gasket_bucket_support_ratio,
        gasket_baffle_support_ratio,
    ) < MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            "The coherent gasket lacks full support: "
            f"bucket={gasket_bucket_support_ratio:.6f}, "
            f"baffle={gasket_baffle_support_ratio:.6f}"
        )

    bucket_baffle_intersection = bucket.intersect(baffle)
    bucket_baffle_overlap = _shape_volume(bucket_baffle_intersection)
    gasket_bucket_overlap = _shape_volume(gasket.intersect(bucket))
    gasket_baffle_overlap = _shape_volume(gasket.intersect(baffle))
    if max(
        bucket_baffle_overlap,
        gasket_bucket_overlap,
        gasket_baffle_overlap,
    ) > MAX_ALLOWED_INTERFERENCE_MM3:
        overlap_box = Compound(
            children=list(bucket_baffle_intersection.solids())
        ).bounding_box()
        component_overlaps = {
            "reference_bucket": _shape_volume(reference_bucket.intersect(baffle)),
            "support_wedge": _shape_volume(support_wedge.intersect(baffle)),
            "fill_supports": [
                _shape_volume(support.intersect(baffle))
                for support in fill_supports
            ],
            "reference_baffle": _shape_volume(bucket.intersect(reference_baffle)),
            "baffle_land": _shape_volume(bucket.intersect(baffle_land)),
            "bridges": [
                _shape_volume(bucket.intersect(bridge)) for bridge in bridges
            ],
            "corner_closures": [
                _shape_volume(bucket.intersect(panel))
                for panel in corner_panels
            ],
        }
        raise ValueError(
            "Coherent joint interference: "
            f"bucket/baffle={bucket_baffle_overlap:.6f}, "
            f"gasket/bucket={gasket_bucket_overlap:.6f}, "
            f"gasket/baffle={gasket_baffle_overlap:.6f} mm3; "
            f"bbox_min={overlap_box.min}, bbox_max={overlap_box.max}; "
            f"components={component_overlaps}"
        )

    live_void = max(base._sand_void().solids(), key=lambda solid: solid.volume)
    target_slab = Pos(
        0.0,
        source.SHOULDER_Y + SAND_CAP_THICKNESS_MM / 2.0,
        0.0,
    ) * Box(
        220.0,
        SAND_CAP_THICKNESS_MM,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    cap_target = live_void & target_slab
    unclosed_sand_cap = cap_target.cut(bucket)
    for passage, support in zip(fill_passages, fill_supports):
        passage_audit_envelope = _single_solid(
            passage.fuse(support).clean().fix(),
            feature="sand-fill passage audit envelope",
        )
        unclosed_sand_cap = Compound(
            children=list(unclosed_sand_cap.solids())
        ).cut(passage_audit_envelope)
    unclosed_sand_cap_mm3 = _shape_volume(unclosed_sand_cap)
    if unclosed_sand_cap_mm3 > 0.05:
        unclosed_box = Compound(
            children=list(unclosed_sand_cap.solids())
        ).bounding_box()
        raise ValueError(
            "The coherent sand cap left an opening of "
            f"{unclosed_sand_cap_mm3:.6f} mm3; "
            f"bbox_min={unclosed_box.min}, bbox_max={unclosed_box.max}"
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
        raise ValueError("The lightweight structure changed the G1 fairing")

    structure = Compound(children=[baffle_land, *bridges, *corner_panels])
    _FILL_AUDIT.clear()
    _FILL_AUDIT.update(fill_audit)
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(
        {
            "installation_motion": "straight drop-on along split normal",
            "bucket_joint_system_count": 1,
            "baffle_joint_system_count": 1,
            "baffle_full_diaphragm_count": 0,
            "baffle_tapered_bridge_count": len(bridges),
            "baffle_bridge_roots_mm3": bridge_roots,
            "baffle_corner_closure_count": len(corner_panels),
            "baffle_corner_closure_land_roots_mm3": corner_land_roots,
            "baffle_corner_closure_rim_roots_mm3": corner_rim_roots,
            "baffle_corner_bucket_conformal_trim_mm3": (
                corner_bucket_trim_volumes
            ),
            "baffle_corner_closure_volume_mm3": sum(
                panel.volume for panel in corner_panels
            ),
            "baffle_corner_closure_thickness_mm": (
                BAFFLE_STRUCTURE_THICKNESS_MM
            ),
            "baffle_corner_closure_scope": (
                "four local fills between the unchanged seal radius and "
                "the original rear-face outer wire"
            ),
            "original_rear_face_outer_bounds_mm": original_corner_bounds,
            "bucket_corner_clearance_cut_count": 0,
            "unclosed_corner_face_volume_mm3": unclosed_corner_volume,
            "baffle_structure_volume_mm3": structure.volume,
            "baffle_structure_thickness_mm": BAFFLE_STRUCTURE_THICKNESS_MM,
            "bucket_bulkhead_constituents": [
                "one exact-envelope planar face plate",
                "one constant-height inner support wedge",
            ],
            "bucket_bulkhead_single_solid": True,
            "bucket_bulkhead_thickness_mm": bulkhead_audit[
                "plate_thickness_mm"
            ],
            "outside_gasket_corner_closure_count": 0,
            "unclosed_outside_gasket_corner_volume_mm3": (
                unclosed_bucket_bulkhead_volume
            ),
            "front_bulkhead_support_drop_mm": bulkhead_audit[
                "support_drop_mm"
            ],
            "front_bulkhead_root_target": bulkhead_audit[
                "root_target"
            ],
            "front_bulkhead_root_depth_mm": bulkhead_audit[
                "root_depth_mm"
            ],
            "front_bulkhead_fill_keepout_diameter_mm": bulkhead_audit[
                "fill_keepout_diameter_mm"
            ],
            "front_bulkhead_fill_keepout_intrusion_mm3": bulkhead_audit[
                "fill_keepout_intrusion_mm3"
            ],
            "front_bulkhead_outside_sculpted_outer_mm3": (
                bulkhead_audit["outside_sculpted_outer_mm3"]
            ),
            "protected_front_excess_mm3": protected_front_excess,
            "inherited_fixed_front_brace_root_intrusion_mm3": (
                inherited_service_opening_intrusion
            ),
            "final_projected_service_opening_intrusion_mm3": (
                final_service_opening_intrusion
            ),
            "projected_service_opening_clear": True,
            "rooted_bulkhead_bucket_root_mm3": (
                rooted_bulkhead_bucket_root
            ),
            "front_bulkhead_support_cardinal_run_mm": (
                bulkhead_audit["support_cardinal_run_mm"]
            ),
            "front_bulkhead_support_cardinal_angle_from_print_axis_deg": (
                bulkhead_audit[
                    "support_cardinal_angle_from_print_axis_deg"
                ]
            ),
            "front_bulkhead_cardinal_slope_under_45_deg": True,
            "fill_passage_blockage_mm3": fill_passage_blockage,
            "seal_land_width_mm": SEAL_LAND_WIDTH_MM,
            "gasket_width_mm": GASKET_WIDTH_MM,
            "gasket_edge_margin_each_side_mm": GASKET_EDGE_MARGIN_MM,
            "gasket_bucket_support_ratio": gasket_bucket_support_ratio,
            "gasket_baffle_support_ratio": gasket_baffle_support_ratio,
            "unclosed_non_fill_sand_cap_mm3": unclosed_sand_cap_mm3,
            "bucket_ramp_from_print_axis_deg": bulkhead_audit[
                "support_cardinal_angle_from_print_axis_deg"
            ],
            "gasket_fastener_bypass_depth_mm": SERVICE_BYPASS_DEPTH_MM,
            "front_hidden_fill_port_count": 2,
        }
    )

    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "shoulder": Compound(
            children=[coherent_bulkhead, *fill_supports]
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
        "front_fill_final_clearances": tuple(final_fill_clearances),
        "front_fill_supports": Compound(children=fill_supports),
        "bucket_bulkhead": coherent_bulkhead,
        "bucket_front_transition": support_wedge,
        "baffle_structure": structure,
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


def _oriented_hex_prism(
    center: Vector,
    *,
    z_sign: float,
    across_flats_mm: float,
    thickness_on_axis_mm: float,
    feature: str,
    rotation_about_axis_deg: float = 0.0,
) -> Solid:
    """Hex prism whose centerline is exactly the fastener axis."""
    sketch = RegularPolygon(
        across_flats_mm / 2.0,
        6,
        major_radius=False,
        rotation=rotation_about_axis_deg,
    )
    raw = _single_solid(
        extrude(sketch, amount=thickness_on_axis_mm / 2.0, both=True),
        feature=feature,
    )
    return _single_solid(
        Pos(center.X, center.Y, center.Z)
        * Rot(_fastener_rotation_x(z_sign), 0.0, 0.0)
        * raw,
        feature=feature,
    )


def _oriented_screw_plane_slot(
    start: Vector,
    end: Vector,
    *,
    z_sign: float,
    width_in_plane_mm: float,
    thickness_on_axis_mm: float,
    feature: str,
) -> tuple[Solid, float]:
    """Straight slot centered in the screw bore's X section plane."""
    travel = end - start
    if abs(travel.X) > 1e-9:
        raise ValueError("The nut-loading slot left the screw center plane")
    travel_unit = travel.normalized()
    direct_rotation_x_deg = math.degrees(
        math.atan2(-travel_unit.Y, travel_unit.Z)
    )
    rotation_about_axis_deg = -90.0 * z_sign
    center = (start + end) * 0.5
    raw = Box(
        width_in_plane_mm,
        thickness_on_axis_mm,
        travel.length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    slot = _single_solid(
        Pos(center.X, center.Y, center.Z)
        * Rot(direct_rotation_x_deg, 0.0, 0.0)
        * raw,
        feature=feature,
    )
    return slot, rotation_about_axis_deg


def _nut_loading_access(
    nut_center: Vector,
    *,
    z_sign: float,
) -> tuple[Solid, Vector, Solid, Solid, float, float]:
    """Shortest screw-plane slot from the bed face to the M4 hex seat."""
    screw_direction = _fastener_direction(z_sign)
    face_dy = source.BAFFLE_BED_Y - nut_center.Y
    face_dz = -(screw_direction.Y * face_dy) / screw_direction.Z
    face_center = Vector(
        nut_center.X,
        source.BAFFLE_BED_Y,
        nut_center.Z
        + face_dz
        - z_sign * NUT_LOADING_FACE_INWARD_OFFSET_MM,
    )
    travel = face_center - nut_center
    travel_unit = travel.normalized()
    start = nut_center - travel_unit * NUT_LOADING_SEAT_OVERTRAVEL_MM
    end = face_center + travel_unit * NUT_LOADING_FACE_OVERTRAVEL_MM
    slot, slot_rotation_deg = _oriented_screw_plane_slot(
        start,
        end,
        z_sign=z_sign,
        width_in_plane_mm=NUT_LOADING_SLOT_WIDTH_MM,
        thickness_on_axis_mm=NUT_LOADING_SLOT_HEIGHT_MM,
        feature="shortest gasket-clear screw-plane bed-face M4 nut slot",
    )
    pocket = _oriented_hex_prism(
        nut_center,
        z_sign=z_sign,
        across_flats_mm=M4_NUT_POCKET_ACROSS_FLATS_MM,
        thickness_on_axis_mm=M4_NUT_POCKET_HEIGHT_MM,
        rotation_about_axis_deg=slot_rotation_deg,
        feature="terminal M4 hex-nut locating seat",
    )
    access = _single_solid(
        pocket.fuse(slot).clean().fix(),
        feature="screw-plane bed-face slot with terminal M4 hex seat",
    )
    nominal_slot, nominal_rotation_deg = _oriented_screw_plane_slot(
        nut_center,
        end,
        z_sign=z_sign,
        width_in_plane_mm=M4_NUT_ACROSS_FLATS_MM,
        thickness_on_axis_mm=M4_NUT_HEIGHT_MM,
        feature="nominal M4 hex-nut insertion sweep",
    )
    if abs(nominal_rotation_deg - slot_rotation_deg) > 1e-9:
        raise ValueError("Nominal and clearance M4 slot rotations diverged")
    nominal_seat = _oriented_hex_prism(
        nut_center,
        z_sign=z_sign,
        across_flats_mm=M4_NUT_ACROSS_FLATS_MM,
        thickness_on_axis_mm=M4_NUT_HEIGHT_MM,
        rotation_about_axis_deg=slot_rotation_deg,
        feature="nominal seated GB6170 M4 hex nut",
    )
    nominal_sweep = _single_solid(
        nominal_seat.fuse(nominal_slot).clean().fix(),
        feature="nominal M4 hex-nut screw-plane insertion sweep",
    )
    slot_axis_dot = abs(travel_unit.dot(screw_direction))
    return (
        access,
        face_center,
        nominal_sweep,
        pocket,
        slot_rotation_deg,
        slot_axis_dot,
    )


def _baffle_nut_housing(
    nut_center: Vector,
    *,
    z_sign: float,
    nominal_envelope: Solid,
) -> Solid:
    housing = Pos(
        nut_center.X,
        source.BAFFLE_BED_Y - NUT_BLOCK_DEPTH_Y_MM / 2.0,
        nut_center.Z,
    ) * Box(
        NUT_BLOCK_WIDTH_X_MM,
        NUT_BLOCK_DEPTH_Y_MM,
        NUT_BLOCK_HEIGHT_Z_MM,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return _single_solid(
        (housing & nominal_envelope).clean().fix(),
        feature="single bed-grown rectangular M4 nut block",
    )


def _accessible_fastener_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]
    hardware_parts: list[Solid] = []
    cutter_parts: list[Solid] = []
    support_parts: list[Solid] = []
    housing_parts: list[Solid] = []
    swept_nut_references: list[Any] = []
    fastener_audits: dict[str, Any] = {}
    gasket_keep_clear = single._single_face_band(
        GASKET_WIDTH_MM + 0.50,
        source.BAFFLE_BED_Y - 0.10,
        source.SHOULDER_Y + 0.10,
        feature="fastener gasket keep-clear envelope",
    )
    authoritative_outer = base._outer_envelope()
    service_face_probe = Pos(
        0.0,
        source.BAFFLE_BED_Y,
        0.0,
    ) * Box(
        220.0,
        0.30,
        220.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        direction = _fastener_direction(z_sign)
        surface = _fastener_surface(z_sign)
        nut_center = surface + direction * NUT_AXIS_DISTANCE_MM

        blister = _single_solid(
            (source._cylinder_between(
                surface + direction * SCREW_BLISTER_AXIS_START_MM,
                surface + direction * BUCKET_SLEEVE_AXIS_END_MM,
                diameter=BUCKET_SLEEVE_D_MM,
            ) & authoritative_outer)
            .cut(gasket_keep_clear)
            .clean()
            .fix(),
            feature=f"flush-clipped {label} tilted cylindrical screw blister",
        )
        blister_root = _shape_volume(blister.intersect(bucket))
        if blister_root <= 0.01:
            raise ValueError(
                f"The {label} cylindrical screw blister lacks a bucket root"
            )
        bucket = _fuse_one(
            bucket,
            blister,
            feature=f"bucket with one {label} cylindrical screw blister",
        )
        support_parts.append(blister)

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
            raise ValueError(f"The {label} assembly relief is empty")
        relief = _single_solid(
            max(
                relief_candidates,
                key=lambda candidate: _shape_volume(
                    candidate.intersect(blister)
                ),
            ),
            feature=f"open {label} cylindrical-blister baffle relief",
        )
        baffle = _cut_one(
            baffle,
            relief,
            feature=f"baffle with open straight-drop {label} relief",
        )

        housing = _baffle_nut_housing(
            nut_center,
            z_sign=z_sign,
            nominal_envelope=common["nominal_envelope"],
        )
        housing = _single_solid(
            housing.cut(relief).cut(gasket_keep_clear).clean().fix(),
            feature=f"{label} single nut block with assembly relief",
        )
        housing_root = _shape_volume(housing.intersect(baffle))
        if housing_root <= 0.01:
            raise ValueError(f"The {label} nut housing has no baffle root")
        baffle = _fuse_one(
            baffle,
            housing,
            feature=f"baffle with single continuous {label} M4 nut block",
        )
        housing_parts.append(housing)

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
        (
            nut_access,
            slot_mouth,
            swept_nut,
            hex_seat,
            slot_rotation_deg,
            insertion_axis_dot,
        ) = _nut_loading_access(
            nut_center,
            z_sign=z_sign,
        )
        swept_nut_references.extend(swept_nut.solids())
        mouth_breakthrough_mm3 = _shape_volume(
            nut_access & service_face_probe & baffle
        )
        if mouth_breakthrough_mm3 <= 0.01:
            raise ValueError(
                f"The {label} M4 slot does not open on the baffle service face"
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
            feature=f"baffle with straight face-entry {label} M4 nut slot",
        )

        screw_head = source._cylinder_between(
            surface + direction * 0.25,
            surface + direction * (0.25 + SCREW_HEAD_REFERENCE_THICKNESS_MM),
            diameter=SCREW_HEAD_REFERENCE_D_MM,
        )
        screw_shank = source._cylinder_between(
            surface + direction * HEAD_COUNTERBORE_DEPTH_MM,
            nut_center + direction * 2.5,
            diameter=SCREW_NOMINAL_D_MM,
        )
        nut = _oriented_hex_prism(
            nut_center,
            z_sign=z_sign,
            across_flats_mm=M4_NUT_ACROSS_FLATS_MM,
            thickness_on_axis_mm=M4_NUT_HEIGHT_MM,
            feature=f"{label} GB6170 M4 hex-nut reference",
            rotation_about_axis_deg=slot_rotation_deg,
        )
        hardware_parts.extend((screw_head, screw_shank, nut))
        cutter_parts.extend((relief, head_counterbore, through_bore, nut_access))

        bearing_center = nut_center - direction * (
            M4_NUT_POCKET_HEIGHT_MM / 2.0
            + NUT_BEARING_AUDIT_THICKNESS_MM / 2.0
        )
        bearing_probe = _single_solid(
            _oriented_hex_prism(
                bearing_center,
                z_sign=z_sign,
                across_flats_mm=M4_NUT_ACROSS_FLATS_MM,
                thickness_on_axis_mm=NUT_BEARING_AUDIT_THICKNESS_MM,
                feature=f"{label} nut bearing probe",
                rotation_about_axis_deg=slot_rotation_deg,
            )
            .cut(through_bore)
            .clean()
            .fix(),
            feature=f"{label} nut bearing audit annulus",
        )
        nut_bearing_ratio = _shape_volume(
            bearing_probe.intersect(baffle)
        ) / bearing_probe.volume
        if nut_bearing_ratio < MINIMUM_NUT_BEARING_SUPPORT_RATIO:
            raise ValueError(
                f"The {label} nut bearing ratio is {nut_bearing_ratio:.6f}"
            )

        nominal_nut_outside_seat_mm3 = _shape_volume(nut.cut(hex_seat))
        insertion_obstruction_mm3 = _shape_volume(swept_nut.intersect(baffle))
        slot_cut_through_block_mm3 = _shape_volume(nut_access.intersect(housing))
        slot_angle_from_perpendicular_deg = math.degrees(
            math.asin(min(1.0, insertion_axis_dot))
        )
        axis_center_error_mm = (
            nut_center - (surface + direction * NUT_AXIS_DISTANCE_MM)
        ).length
        screw_plane_alignment_error_mm = max(
            abs(slot_mouth.X - surface.X),
            abs(slot_mouth.X - nut_center.X),
        )
        if nominal_nut_outside_seat_mm3 > 0.001:
            raise ValueError(
                f"The {label} M4 nut does not fit its hex seat: "
                f"{nominal_nut_outside_seat_mm3:.6f} mm3 outside"
            )
        if insertion_obstruction_mm3 > 0.001:
            raise ValueError(
                f"The {label} M4 nut insertion path is obstructed by "
                f"{insertion_obstruction_mm3:.6f} mm3"
            )
        if slot_cut_through_block_mm3 <= 0.01:
            raise ValueError(f"The {label} M4 slot does not open through its block")
        if axis_center_error_mm > 1e-9:
            raise ValueError(
                f"The {label} M4 nut seat is not coaxial: "
                f"center={axis_center_error_mm:.12f}"
            )
        if slot_angle_from_perpendicular_deg > 5.0:
            raise ValueError(
                f"The {label} direct M4 slot is excessively skewed from the "
                f"nut face: {slot_angle_from_perpendicular_deg:.6f} degrees"
            )
        if screw_plane_alignment_error_mm > 1e-9:
            raise ValueError(
                f"The {label} M4 loading slot leaves the screw center plane: "
                f"{screw_plane_alignment_error_mm:.12f} mm"
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
                f"The {label} head bearing ratio is {head_bearing_ratio:.6f}"
            )

        hard_gasket_overlap = _shape_volume(
            Compound(children=[blister, housing]).intersect(gasket)
        )
        cutter_gasket_overlap = _shape_volume(
            Compound(
                children=[relief, head_counterbore, through_bore, nut_access]
            ).intersect(gasket)
        )
        if max(hard_gasket_overlap, cutter_gasket_overlap) > 0.001:
            cutter_gasket_components = {
                "relief": _shape_volume(relief.intersect(gasket)),
                "head_counterbore": _shape_volume(
                    head_counterbore.intersect(gasket)
                ),
                "through_bore": _shape_volume(through_bore.intersect(gasket)),
                "nut_access": _shape_volume(nut_access.intersect(gasket)),
            }
            raise ValueError(
                f"The {label} fastener interrupts the gasket: "
                f"hard={hard_gasket_overlap:.6f}, "
                f"cut={cutter_gasket_overlap:.6f} mm3; "
                f"components={cutter_gasket_components}"
            )

        path_point = Vector(slot_mouth.X, source.BAFFLE_BED_Y, slot_mouth.Z)
        centerline = single._perimeter_wire(
            offset_mm=0.0,
            y_mm=source.BAFFLE_BED_Y,
        )
        mouth_center_to_gasket_centerline_mm = min(
            edge.distance_to(path_point) for edge in centerline.edges()
        )
        fastener_audits[label] = {
            "surface_center_mm": [surface.X, surface.Y, surface.Z],
            "direction": [direction.X, direction.Y, direction.Z],
            "angle_from_face_normal_deg": FASTENER_ANGLE_FROM_FACE_NORMAL_DEG,
            "nut_center_mm": [nut_center.X, nut_center.Y, nut_center.Z],
            "nut_depth_forward_of_baffle_bed_mm": (
                source.BAFFLE_BED_Y - nut_center.Y
            ),
            "slot_mouth_center_mm": [
                slot_mouth.X,
                slot_mouth.Y,
                slot_mouth.Z,
            ],
            "slot_mouth_breakthrough_mm3": mouth_breakthrough_mm3,
            "slot_cut_through_block_mm3": slot_cut_through_block_mm3,
            "slot_mouth_to_gasket_centerline_mm": (
                mouth_center_to_gasket_centerline_mm
            ),
            "loading_slot_construction": (
                "one shortest straight printer-bed-face prism in the screw "
                "center plane"
            ),
            "loading_slot_rotation_about_screw_axis_deg": (
                slot_rotation_deg
            ),
            "loading_slot_axis_dot_screw_axis": insertion_axis_dot,
            "loading_slot_angle_from_perpendicular_deg": (
                slot_angle_from_perpendicular_deg
            ),
            "loading_slot_perpendicular_to_screw_axis": False,
            "loading_slot_screw_plane_alignment_error_mm": (
                screw_plane_alignment_error_mm
            ),
            "loading_slot_in_screw_bore_cross_section": True,
            "loading_slot_shortest_gasket_clear_path_from_bed_face": True,
            "terminal_seat_shape": "hexagonal",
            "terminal_hex_center_error_from_screw_axis_mm": (
                axis_center_error_mm
            ),
            "nominal_nut_outside_hex_seat_mm3": (
                nominal_nut_outside_seat_mm3
            ),
            "nominal_nut_insertion_obstruction_mm3": (
                insertion_obstruction_mm3
            ),
            "bucket_support_construction": (
                "one flush-clipped tilted cylindrical blister"
            ),
            "bucket_gusset_count": 0,
            "bucket_blister_diameter_mm": BUCKET_SLEEVE_D_MM,
            "bucket_blister_root_mm3": blister_root,
            "baffle_housing_root_mm3": housing_root,
            "baffle_housing_construction": "one bed-grown rectangular block",
            "separate_baffle_backstop_count": 0,
            "nut_bearing_support_ratio": nut_bearing_ratio,
            "head_bearing_support_ratio": head_bearing_ratio,
            "hard_gasket_overlap_mm3": hard_gasket_overlap,
            "cutter_gasket_overlap_mm3": cutter_gasket_overlap,
        }

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    if bucket_baffle_overlap > MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            "Accessible-fastener bucket/baffle interference is "
            f"{bucket_baffle_overlap:.6f} mm3"
        )

    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        raise ValueError("Nut slots changed the authoritative G1 fairing")

    def bbox_deltas(reference: Solid, final: Solid) -> dict[str, float]:
        reference_bbox = reference.bounding_box()
        final_bbox = final.bounding_box()
        return {
            "min_x": final_bbox.min.X - reference_bbox.min.X,
            "max_x": final_bbox.max.X - reference_bbox.max.X,
            "min_y": final_bbox.min.Y - reference_bbox.min.Y,
            "max_y": final_bbox.max.Y - reference_bbox.max.Y,
            "min_z": final_bbox.min.Z - reference_bbox.min.Z,
            "max_z": final_bbox.max.Z - reference_bbox.max.Z,
        }

    baffle_exterior_deltas = bbox_deltas(reference_baffle, baffle)
    bucket_exterior_deltas = bbox_deltas(reference_bucket, bucket)
    if max(abs(value) for value in baffle_exterior_deltas.values()) > 1e-5:
        raise ValueError(
            f"Fasteners changed baffle bounds: {baffle_exterior_deltas}"
        )
    if max(abs(value) for value in bucket_exterior_deltas.values()) > 1e-5:
        raise ValueError(
            f"Fasteners changed bucket bounds: {bucket_exterior_deltas}"
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
        "nut_load_pad": Compound(children=housing_parts),
        "nut_loading_sweep_reference": Compound(
            children=swept_nut_references
        ),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": 1.2,
        "description": (
            "Two flush-clipped cylindrical bucket blisters carry shallow "
            "recessed M4 head pockets and coaxial shank bores to GB6170 "
            "hex nuts loaded from the baffle service face"
        ),
        "service_notes": (
            "Slide each M4 hex nut through the visible service-face mouth "
            "until it seats in the terminal hex, install the baffle straight "
            "on, and tighten the recessed top and bottom screws"
        ),
        "closure_passage_mode": (
            "two fully housed dry-side passages outside the gasket"
        ),
        "geometry": {
            "fastener_count": 2,
            "screw_nominal_d_mm": SCREW_NOMINAL_D_MM,
            "screw_clearance_d_mm": SCREW_CLEARANCE_D_MM,
            "head_counterbore_d_mm": HEAD_COUNTERBORE_D_MM,
            "head_counterbore_depth_mm": HEAD_COUNTERBORE_DEPTH_MM,
            "nut_standard": "GB6170 M4 x 0.7",
            "m4_nut_pitch_mm": M4_NUT_PITCH_MM,
            "m4_nut_across_flats_mm": M4_NUT_ACROSS_FLATS_MM,
            "m4_nut_across_corners_mm": M4_NUT_ACROSS_CORNERS_MM,
            "m4_nut_height_mm": M4_NUT_HEIGHT_MM,
            "m4_nut_pocket_across_flats_mm": (
                M4_NUT_POCKET_ACROSS_FLATS_MM
            ),
            "m4_nut_pocket_height_mm": M4_NUT_POCKET_HEIGHT_MM,
            "nut_loading_slot_width_mm": NUT_LOADING_SLOT_WIDTH_MM,
            "nut_loading_slot_height_mm": NUT_LOADING_SLOT_HEIGHT_MM,
            "nut_loading_face_entry_x_mm": NUT_LOADING_FACE_ENTRY_X_MM,
            "nut_loading_face_inward_offset_mm": (
                NUT_LOADING_FACE_INWARD_OFFSET_MM
            ),
            "nut_loading_direction": (
                "from printer-bed gasket/collar face in the screw bore center "
                "plane directly to the nut seat"
            ),
            "nut_slots_open_on_baffle_service_face": True,
            "gasket_path_deviation_mm": 0.0,
            "straight_drop_on_insertion_path": True,
            "authoritative_fairing_face_exactly_preserved": True,
            "baffle_exterior_bounds_difference_mm": baffle_exterior_deltas,
            "bucket_exterior_bounds_difference_mm": bucket_exterior_deltas,
            "external_bucket_humps": False,
            "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
            "fasteners": fastener_audits,
        },
    }


def _cut_into_parts(shape: Any, cutters: tuple[Any, ...]) -> list[Solid]:
    current = [copy.copy(solid) for solid in shape.solids()]
    for cutter in cutters:
        current = [
            part.clean().fix()
            for solid in current
            for part in solid.cut(cutter).solids()
            if part.volume > 1e-6
        ]
    return current


def _coherent_internal_braces(port_clearance: Any) -> Compound:
    enclosure_clip = base._outer_envelope()
    saddle = base._internal_tower_mount_saddle(
        clearance=base.D.tube_install_clearance
    )
    service_keepout = serviceable._service_flange_keepout(clearance=0.30)
    bottom_tabs = base._bottom_tab_brace_clearance()
    rear_tabs = base._rear_tab_brace_clearance()
    absorber_clearance = absorber._place_local(
        absorber._local_absorber_installation_envelope()
    )
    named_cutters = {
        "port_installation_envelope": port_clearance,
        "tower_saddle": saddle,
        "tower_flange_installation": service_keepout,
        "bottom_tube_ears": bottom_tabs,
        "rear_tube_ears": rear_tabs,
        "absorber_installation_envelope": absorber_clearance,
    }
    cutters = tuple(named_cutters.values())

    logical_shapes: list[tuple[str, Any, tuple[Any, ...]]] = []
    logical_shapes.append(
        (
            "transverse_tapered_u_frame",
            simplified._printable_transverse_brace() & enclosure_clip,
            cutters,
        )
    )
    for index, rail in enumerate(
        simplified._printable_longitudinal_rails().solids(),
        start=1,
    ):
        logical_shapes.append(
            (
                f"continuous_longitudinal_rail_{index}",
                rail & enclosure_clip,
                cutters,
            )
        )
    for index, root in enumerate(base._front_brace_blends().solids(), start=1):
        logical_shapes.append(
            (
                f"conformal_front_root_{index}",
                root,
                (port_clearance, absorber_clearance),
            )
        )
    logical_shapes.append(
        (
            "rear_tube_cradle",
            base._rear_cradle_brace(port_clearance),
            (absorber_clearance,),
        )
    )
    logical_shapes.append(
        (
            "tower_d_cradle",
            serviceable._d_cradle(),
            (port_clearance, absorber_clearance),
        )
    )

    retained: list[Solid] = []
    logical_audit: dict[str, Any] = {}
    for name, raw, local_cutters in logical_shapes:
        raw_solids = [solid for solid in raw.solids() if solid.volume > 1e-6]
        if not raw_solids:
            raise ValueError(f"The direct brace {name} is empty before clearances")
        raw_compound = Compound(children=raw_solids)
        parts = _cut_into_parts(raw_compound, local_cutters)
        if not parts:
            raise ValueError(f"Named clearances consumed the direct brace {name}")
        retained.extend(parts)
        cut_contacts = {
            cutter_name: _shape_volume(raw_compound.intersect(cutter))
            for cutter_name, cutter in named_cutters.items()
            if any(cutter is local_cutter for local_cutter in local_cutters)
        }
        logical_audit[name] = {
            "raw_solid_count": len(raw_solids),
            "final_piece_count": len(parts),
            "raw_volume_mm3": raw_compound.volume,
            "final_volume_mm3": sum(part.volume for part in parts),
            "named_clearance_contacts_mm3": cut_contacts,
            "unclassified_clearance_count": 0,
        }

    if not retained:
        raise ValueError("The coherent direct brace network is empty")

    variant = base.RESTORED_FEATURE_VARIANT
    cavity_half = base.D.width / 2.0 - base.D.wall_stack_t
    floor_top_z = -base.D.height / 2.0 + base.D.wall_stack_t
    transverse = Compound(
        children=[
            part
            for name, _, local_cutters in logical_shapes[:1]
            for part in _cut_into_parts(logical_shapes[0][1], local_cutters)
        ]
    )
    wall_probes = {
        "left_wall": Pos(-cavity_half, 0.0, 0.0)
        * Box(0.4, 40.0, 180.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "right_wall": Pos(cavity_half, 0.0, 0.0)
        * Box(0.4, 40.0, 180.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "roof": Pos(0.0, 0.0, cavity_half)
        * Box(180.0, 40.0, 0.4, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "floor": Pos(0.0, 0.0, floor_top_z)
        * Box(180.0, 40.0, 0.4, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
    }
    transverse_contacts = {
        name: _shape_volume(transverse.intersect(probe))
        for name, probe in wall_probes.items()
    }
    if min(transverse_contacts.values()) <= 0.01:
        raise ValueError(
            f"The transverse U-frame misses a boundary: {transverse_contacts}"
        )

    _BRACE_AUDIT.clear()
    _BRACE_AUDIT.update(
        {
            "construction": (
                "direct tapered U-frame, three direct longitudinal rails, "
                "four conformal front roots, rear cradle, and tower D-cradle"
            ),
            "legacy_mask_intersection_count": 0,
            "bounding_box_role_classification_count": 0,
            "named_clearance_count": len(named_cutters),
            "named_clearances": list(named_cutters),
            "logical_braces": logical_audit,
            "transverse_boundary_contacts_mm3": transverse_contacts,
            "transverse_side_legs_reach_floor": (
                transverse.bounding_box().min.Z <= floor_top_z + 0.10
            ),
            "support_free_ramp_length_mm": simplified.BRACE_RAMP_LENGTH_MM,
            "print_orientation": "solid rear face on print bed",
            "unclassified_notch_count": 0,
            "retained_piece_count": len(retained),
            "window_brace_center_y_mm": variant.window_brace_center_y,
        }
    )
    return Compound(children=retained)


def _section_compound(shape: Any, clip: Solid, *, feature: str) -> Compound:
    pieces = [
        piece.clean().fix()
        for solid in shape.solids()
        for piece in (solid & clip).solids()
        if piece.volume > 1e-6
    ]
    if not pieces or not all(piece.is_valid for piece in pieces):
        raise ValueError(f"{feature} did not produce valid section solids")
    return Compound(children=pieces)


def _export_and_check(path: Path, shape: Any) -> dict[str, Any]:
    export_step(shape, path, unit=Unit.MM, write_pcurves=True)
    imported = import_step(path)
    check = {
        "source_solid_count": len(shape.solids()),
        "imported_solid_count": len(imported.solids()),
        "all_imported_solids_valid": all(
            solid.is_valid for solid in imported.solids()
        ),
    }
    if (
        check["source_solid_count"] != check["imported_solid_count"]
        or not check["all_imported_solids_valid"]
    ):
        raise ValueError(f"STEP section round trip failed: {path.name}: {check}")
    return check


def _generate_close_sections() -> dict[str, Any]:
    assembled = import_step(OUT / "centered_captive_nut_assembled.step")
    bucket = import_step(OUT / "centered_captive_nut_bucket.step")
    baffle = import_step(OUT / "centered_captive_nut_baffle.step")
    hardware = import_step(OUT / "centered_captive_nut_hardware_reference.step")

    specs = {
        "left_fill_close_section.step": (
            bucket,
            Pos(-91.0, -67.0, 86.0)
            * Box(
                10.0,
                36.0,
                20.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
            "left_fill_section_viewer",
        ),
        "gasket_corner_close_section.step": (
            assembled,
            Pos(86.0, -73.0, -86.0)
            * Box(
                22.0,
                34.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
            "gasket_corner_section_viewer",
        ),
        "top_screw_tunnel_close_section.step": (
            assembled,
            Pos(-4.9, -80.0, 87.0)
            * Box(
                10.0,
                32.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
            "screw_tunnel_section_viewer",
        ),
        "top_nut_slot_close_section.step": (
            Compound(children=[*baffle.solids(), *hardware.solids()]),
            Pos(-4.9, -83.0, 86.0)
            * Box(
                10.0,
                28.0,
                24.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
            "nut_slot_section_viewer",
        ),
    }
    checks: dict[str, Any] = {}
    for filename, (shape, clip, viewer_name) in specs.items():
        section = _section_compound(
            shape,
            clip,
            feature=filename,
        )
        path = OUT / filename
        checks[filename] = _export_and_check(path, section)
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(path),
                "--out",
                str(OUT / viewer_name),
            ],
            check=True,
        )
        centered._configure_viewer(
            job_output_path(OUT / viewer_name),
            cutaway=True,
        )
    return checks


def _make_installed_volume_authoritative(
    diagnostics: dict[str, Any],
    closure_key: str,
) -> None:
    closure_diagnostics = diagnostics[closure_key]
    baseline_net_l = diagnostics["volume_accounting"][
        "final_modeled_net_box_volume_l"
    ]
    installed_net_l = float(closure_diagnostics["modeled_net_volume_l"])
    installed_tuning_hz = float(
        closure_diagnostics["modeled_natural_tuning_hz"]
    )
    diagnostics["volume_accounting"].update(
        {
            "baseline_without_installed_front_closure_l": baseline_net_l,
            "installed_bucket_and_baffle_included": True,
            "front_closure_displacement_l": (
                baseline_net_l - installed_net_l
            ),
            "final_modeled_net_box_volume_l": installed_net_l,
            "authoritative_volume_state": (
                "bucket and removable baffle installed and gasket closed"
            ),
        }
    )
    diagnostics["port"]["lengths"][
        "calculated_tuning_hz"
    ] = installed_tuning_hz
    diagnostics["alignment"]["calculated_tuning_hz"] = installed_tuning_hz
    recovered_l = installed_net_l - CURRENT_SYSTEMIC_NET_VOLUME_L
    closure_diagnostics["volume_recovery"] = {
        "current_systemic_baseline_net_l": CURRENT_SYSTEMIC_NET_VOLUME_L,
        "improved_installed_net_l": installed_net_l,
        "recovered_volume_l": recovered_l,
        "recovered_volume_mm3": recovered_l * 1_000_000.0,
        "current_systemic_closure_displacement_mm3": (
            CURRENT_SYSTEMIC_CLOSURE_DISPLACEMENT_MM3
        ),
    }


def generate() -> dict[str, Any]:
    original_out = previous.OUT
    original_name = previous.NAME
    original_common = previous._systemic_common_joint
    original_fasteners = previous._recessed_fastener_concept
    original_braces = simplified._simplified_internal_braces
    original_bypass_half_width = single.SCREW_BYPASS_HALF_WIDTH_MM
    original_bypass_depth = single.SCREW_BYPASS_DEPTH_MM

    previous.OUT = OUT
    previous.NAME = NAME
    previous._systemic_common_joint = _lightweight_common_joint
    previous._recessed_fastener_concept = _accessible_fastener_concept
    simplified._simplified_internal_braces = _coherent_internal_braces
    single.SCREW_BYPASS_HALF_WIDTH_MM = SERVICE_BYPASS_HALF_WIDTH_MM
    single.SCREW_BYPASS_DEPTH_MM = SERVICE_BYPASS_DEPTH_MM
    try:
        diagnostics = previous.generate()
    finally:
        previous.OUT = original_out
        previous.NAME = original_name
        previous._systemic_common_joint = original_common
        previous._recessed_fastener_concept = original_fasteners
        simplified._simplified_internal_braces = original_braces
        single.SCREW_BYPASS_HALF_WIDTH_MM = original_bypass_half_width
        single.SCREW_BYPASS_DEPTH_MM = original_bypass_depth

    closure_diagnostics = diagnostics.pop(
        "systemic_joint_recessed_fastener_closure"
    )
    closure_diagnostics["joint"] = dict(_JOINT_AUDIT)
    closure_diagnostics["front_fill"] = dict(_FILL_AUDIT)
    closure_diagnostics["corner_fasteners"] = dict(_FASTENER_AUDIT)
    closure_diagnostics["coherent_bracing"] = dict(_BRACE_AUDIT)
    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete lightweight coherent closure and direct-brace experiment"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_lightweight_coherent_closure"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_lightweight_coherent_closure"
        ),
        "systemic_baseline_modified": False,
        "shared_upstream_generators_modified": False,
    }
    closure_key = "lightweight_coherent_closure"
    diagnostics[closure_key] = closure_diagnostics
    diagnostics["preserved_full_detail_contract"].update(
        {
            "external_parabolic_g1_package_unchanged": True,
            "driver_collar_preserved": True,
            "nested_external_mating_geometry_unchanged": True,
            "recessed_external_fastener_locations_unchanged": True,
            "baffle_full_diaphragm_removed": True,
            "coherent_direct_brace_network": True,
            "hidden_face_nut_loading_slots_accessible": True,
        }
    )
    _make_installed_volume_authoritative(diagnostics, closure_key)
    diagnostics[closure_key]["close_section_roundtrip"] = (
        _generate_close_sections()
    )
    diagnostics[closure_key]["viewer_workflow"].update(
        {
            "left_fill_section_viewer": "left_fill_section_viewer/index.html",
            "gasket_corner_section_viewer": (
                "gasket_corner_section_viewer/index.html"
            ),
            "screw_tunnel_section_viewer": (
                "screw_tunnel_section_viewer/index.html"
            ),
            "nut_slot_section_viewer": "nut_slot_section_viewer/index.html",
        }
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


if __name__ == "__main__":
    generate()
