"""Generate a compact Sand Cube with one low-loss swept circular port.

This fourth isolated experiment uses a 190 x 210 x 190 mm enclosure.  A round
constant-area airway starts at a forward-facing low inlet, follows one broad
horizontal sweep, enters one rotated R70 elbow, and drifts monotonically to the
centered tower.  The complete in-box duct displacement is included while the
route is tuned to a 39 Hz natural alignment.  The tower is the only support for
the DE250's two-hole mounting plate and three curved wraparound spokes.
All dimensions are millimetres unless stated otherwise.
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
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from build123d import (
    Bezier,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Compound,
    Ellipse,
    Line,
    Location,
    Part,
    Plane,
    Polyline,
    Pos,
    RectangleRounded,
    Rot,
    Spline,
    Unit,
    Vector,
    Wire,
    add,
    export_step,
    extrude,
    fillet,
    import_step,
    loft,
    make_face,
    sweep,
)


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.sand_cube_200_hybrid_port import (  # noqa: E402
    generate_sand_cube_200_hybrid_port as folded,
)
from experiments.sand_cube_8_5_black_hole.generate_contoured_inner_variants import (  # noqa: E402
    FINAL_200_FILL_ENTRY_D,
    FINAL_200_VARIANT,
    SEAT_LAND_OD,
    _confirmed_woofer,
    _curve_to_micro_seat_tool,
    _fill_port_inner_support,
    _final_params,
    _front_tool_global_oriented,
    _gx16_connector_island,
    _gx16_rear_cutout_corner,
    _inner_relief_tool,
    _intersection_volume,
    _oriented_cylinder,
    _placed_gx16,
    _primary_shape,
    _require_single_solid,
    _variant_sand_fill_port_cutout,
    _window_brace,
)
from src.enclosure_family.datums import (  # noqa: E402
    ENCLOSURE_190X210_COORDINATES,
)
from src.features.horn import (  # noqa: E402
    build_jmlc_horn,
    jmlc_profile_metadata,
)


common = folded.common
OUT = ROOT / "build" / "sand_cube_190x210_single_oval_port"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_190x210_all_circle_weight_bearing_39hz"
    width: float = ENCLOSURE_190X210_COORDINATES.width_mm
    depth: float = ENCLOSURE_190X210_COORDINATES.depth_mm
    height: float = ENCLOSURE_190X210_COORDINATES.height_mm
    center_y: float = ENCLOSURE_190X210_COORDINATES.center_y_mm
    target_tuning_hz: float = 39.0
    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204

    outer_skin_t: float = 2.0
    sand_gap_t: float = 3.0
    inner_skin_t: float = 2.0
    edge_fillet_r: float = 8.0

    # 44 x 35 mm is within 0.3% of the previous 48 x 32 mm airway area, but its
    # 1.26:1 aspect ratio is appreciably closer to a round tube.
    # Preserve the 44 x 35 mm oval's exact area, but make the constant-area
    # airway round.  A circular bore cannot roll or flatten while the route
    # changes bend planes and has the least wetted perimeter for this area.
    port_width: float = math.sqrt(44.0 * 35.0)
    port_depth: float = math.sqrt(44.0 * 35.0)
    port_wall_t: float = 3.0
    structural_tower_wall_t: float = 5.0
    structural_wall_transition_start_z: float = 84.0
    structural_wall_transition_end_z: float = 87.5
    port_x: float = 0.0
    # The acoustic airway is circular from the inlet through the complete
    # visible riser. Only the printed wall thickens, entirely below the inner
    # roof, to make the external column the sole cabinet-to-driver load path.
    # Pull the complete straight rise 2 mm forward so even the hidden 5 mm
    # structural wall stays clear of the rear 2-3-2 wall stack.
    port_y: float = 82.5
    tower_width: float = math.sqrt(44.0 * 35.0)
    tower_depth: float = math.sqrt(44.0 * 35.0)
    tower_transition_end_z: float = 84.0
    # The external rise is now a true continuation of the internal tube.  The
    # shorter horn moves the DE250 forward far enough that no rearward tower
    # offset is needed for motor clearance.
    upper_tower_y: float = 82.5
    upper_tower_shift_start_z: float = 100.0
    upper_tower_shift_end_z: float = 135.0
    # The 45.243 mm OD lower duct is tangent to the -88 mm inner floor. It sits
    # on the solid floor; the cabinet receives no port-shaped seating channel.
    horizontal_z: float = -65.37858312965142
    bend_centerline_r: float = 70.0
    brace_port_clearance: float = 1.5
    tube_install_clearance: float = 0.30
    # The low inlet now faces the front wall.  Its throat starts on the far
    # left, then one broad circular-plan sweep carries the round airway toward
    # the lower-right R70 rise.  This replaces the short diagonal highlighted
    # in the prior draft without adding an inflection or flattening the tube.
    # Moving the floor-tangent inlet slightly rearward clears the supplied
    # woofer while preserving a forward-facing mouth and broad plan sweep.
    inlet_mouth_y: float = -27.0
    inlet_x: float = -61.0
    inlet_flare_l: float = 15.0
    inlet_mouth_width: float = math.sqrt(46.0 * 43.0)
    inlet_mouth_height: float = math.sqrt(46.0 * 43.0)
    inlet_mouth_center_z: float = (
        -88.0 + math.sqrt(46.0 * 43.0) / 2.0 + 3.0
    )
    inlet_flat_width: float = math.sqrt(44.0 * 35.0)
    inlet_flat_height: float = math.sqrt(44.0 * 35.0)
    inlet_flat_center_z: float = -65.37858312965142
    inlet_end_correction_factor: float = 0.85
    outlet_flare_l: float = 25.0
    outlet_mouth_width: float = math.sqrt(78.0 * 44.0)
    outlet_mouth_depth: float = math.sqrt(78.0 * 44.0)
    outlet_end_correction_factor: float = 0.613

    # The broad lower sweep is solved analytically so its front-facing start
    # and its end tangent meet this R70 elbow exactly.  Above the elbow, a
    # single-plane drift returns monotonically to the centered tower without
    # crossing the centerline or reversing lateral direction.
    lower_elbow_vertical_x: float = 63.0
    lower_elbow_vertical_y: float = 82.0
    upper_drift_control_fraction: tuple[float, ...] = (
        0.0,
        0.0,
        0.0,
        0.22,
        0.50,
        0.78,
        1.0,
        1.0,
        1.0,
    )
    asymmetric_vertical_return_top_z: float = 84.0
    baseline_outlet_top_z: float = 282.549703718656
    # The all-circular forward-clearance route needs 0.5635 mm more vertical
    # centerline than the prior 40 mm-lowered draft to land on the exact 39 Hz
    # Helmholtz target.
    target_outlet_drop: float = 39.4365

    front_brace_blend_length: float = 15.0
    front_brace_baffle_embed: float = 2.0
    front_brace_ring_embed: float = 1.0
    rear_cradle_front_y: float = 98.0
    rear_cradle_depth: float = 11.0
    rear_cradle_height: float = 10.0
    tube_tab_t: float = 4.0
    tube_tab_seating_clearance: float = 0.30
    bottom_tab_width: float = 12.0
    bottom_tab_left_offset_from_tube: float = 20.0
    bottom_tab_right_offset_from_tube: float = 20.0
    bottom_tab_depth: float = 8.0
    bottom_tab_bottom_z: float = -88.0
    rear_tab_width: float = 14.0
    # The return occupies the rear-right corner, so both rear fasteners land on
    # one overlapping two-hole wing extending into the substantial left side
    # of the cradle.  A nominal right-side hole would sit in the swept relief.
    rear_tab_inner_left_offset_from_tube: float = 20.0
    rear_tab_outer_left_offset_from_tube: float = 31.0
    rear_tab_height: float = 8.0
    tube_mount_clearance_d: float = 4.5
    tube_mount_insert_d: float = 4.8
    tube_mount_insert_depth: float = 6.5
    bottom_tube_mount_insert_depth: float = 5.0

    # The weight-bearing circular tower is installed from inside. Its hidden
    # wall thickening finishes below the inner roof; the horizontal plate bears
    # against the underside of the roof and its vertical plate bears against
    # the inside of the rear wall, forming one rigid upper-corner saddle.
    # Split the removable lower duct just below the rear saddle. Both sides of
    # this transverse joint are derived from the same circular airway.
    internal_tower_bottom_z: float = 62.0
    internal_mount_plate_t: float = 4.0
    internal_mount_plate_w: float = 88.0
    internal_mount_roof_front_y: float = 64.0
    internal_mount_roof_depth: float = 44.0
    internal_mount_rear_bottom_z: float = 62.0
    internal_mount_platform_d: float = 14.0
    internal_mount_roof_x: float = 36.0
    internal_mount_roof_y: float = 70.0
    internal_mount_rear_x: float = 36.0
    internal_mount_rear_z: float = 69.0
    internal_mount_clearance_d: float = 4.5
    internal_mount_insert_d: float = 4.8
    internal_mount_insert_depth: float = 6.5

    horn_center_x: float = 0.0
    horn_target_physical_mouth_d: float = 190.0
    horn_profile_mouth_outer_d_input: float = 192.5299283
    horn_reference_wavefront_t: float = 0.242
    horn_reference_axial_length: float = 92.38213681735276
    horn_axial_shorten: float = 10.0
    horn_target_axial_length: float = 82.38213681735276
    # Exact 2007-recurrence solve for the target axial length while retaining
    # the 25.4 mm throat, 8-degree throat tangent, 140-degree rollback, and
    # 186.13 mm acoustic mouth.
    horn_solved_wavefront_t: float = 0.49437398987356584
    de250_official_throat_d: float = 25.0
    horn_center_z: float = 194.9999947914171
    # The exact profile is 10.000 mm shorter. The NURBS/thickened rolled lip
    # changes its forward projection by 0.028 mm; the mounting face also takes
    # the provisional forward clearance released for the structural column.
    # Provisional 4 mm forward shift clears the thicker structural column. The
    # user intentionally released the prior front-flush constraint pending the
    # final horn-placement pass.
    horn_mount_face_y: float = -5.47803490744143
    horn_forward_projection_mm: float = 4.0
    horn_face_t: float = 4.0
    horn_acoustic_hole_d: float = 42.0
    horn_mount_ring_r: float = 50.0
    de250_envelope_r: float = 60.0
    de250_rear_depth: float = 62.0
    horn_spoke_gap: float = 2.0
    horn_spoke_d: float = 10.0
    horn_spoke_root_r: float = 46.0
    horn_spoke_turn_extra_r: float = 5.0

    @property
    def wall_stack_t(self) -> float:
        return self.outer_skin_t + self.sand_gap_t + self.inner_skin_t

    @property
    def port_rx(self) -> float:
        return self.port_width / 2.0

    @property
    def port_rz(self) -> float:
        return self.port_depth / 2.0

    @property
    def outer_rx(self) -> float:
        return self.port_rx + self.port_wall_t

    @property
    def outer_rz(self) -> float:
        return self.port_rz + self.port_wall_t

    @property
    def outer_width(self) -> float:
        return 2.0 * self.outer_rx

    @property
    def outer_depth(self) -> float:
        return 2.0 * self.outer_rz

    @property
    def tower_rx(self) -> float:
        return self.tower_width / 2.0

    @property
    def tower_ry(self) -> float:
        return self.tower_depth / 2.0

    @property
    def tower_outer_rx(self) -> float:
        return self.tower_rx + self.structural_tower_wall_t

    @property
    def tower_outer_ry(self) -> float:
        return self.tower_ry + self.structural_tower_wall_t

    @property
    def port_area_mm2(self) -> float:
        return math.pi * self.port_rx * self.port_rz

    @property
    def port_outer_r(self) -> float:
        # Compatibility with the shared DE250 cup helper: this is the tube's
        # front/rear semi-axis, not the equivalent circular radius.
        return self.outer_rz

    @property
    def inlet_run_direction_xy(self) -> tuple[float, float]:
        # The inlet opening faces the cabinet front; flow enters along +Y.
        return 0.0, 1.0

    @property
    def inlet_throat_x(self) -> float:
        dx, _dy = self.inlet_run_direction_xy
        return self.inlet_x + self.inlet_flare_l * dx

    @property
    def inlet_throat_y(self) -> float:
        _dx, dy = self.inlet_run_direction_xy
        return self.inlet_mouth_y + self.inlet_flare_l * dy

    @property
    def lower_sweep_solution(self) -> tuple[float, float]:
        """Return the exact clockwise plan-sweep turn (rad) and radius.

        The sweep starts at the inlet throat with a +Y tangent.  Its end must
        meet the horizontal tangent point of the following R70 vertical elbow.
        Solving the two endpoint equations leaves one positive broad-radius
        root.  Keeping this derivation parametric prevents a hidden kink if the
        mouth or vertical-rise location moves during later packaging work.
        """

        start_x = self.inlet_throat_x
        start_y = self.inlet_throat_y
        target_x = self.lower_elbow_vertical_x
        target_y = self.lower_elbow_vertical_y
        elbow_r = self.bend_centerline_r

        def radius_difference(phi: float) -> float:
            sin_phi = math.sin(phi)
            cos_phi = math.cos(phi)
            radius_from_x = (
                target_x - start_x - elbow_r * sin_phi
            ) / (1.0 - cos_phi)
            radius_from_y = (
                target_y - start_y - elbow_r * cos_phi
            ) / sin_phi
            return radius_from_x - radius_from_y

        low = math.radians(45.0)
        high = math.radians(120.0)
        low_value = radius_difference(low)
        high_value = radius_difference(high)
        if low_value * high_value >= 0.0:
            raise ValueError("Broad lower sweep has no positive tangent solution")
        for _ in range(80):
            mid = (low + high) / 2.0
            mid_value = radius_difference(mid)
            if low_value * mid_value <= 0.0:
                high = mid
                high_value = mid_value
            else:
                low = mid
                low_value = mid_value
        phi = (low + high) / 2.0
        radius = (
            target_y - start_y - elbow_r * math.cos(phi)
        ) / math.sin(phi)
        if radius <= self.outer_rx:
            raise ValueError("Broad lower sweep radius is too small for the duct")
        return phi, radius

    @property
    def lower_sweep_turn_rad(self) -> float:
        return self.lower_sweep_solution[0]

    @property
    def lower_sweep_radius(self) -> float:
        return self.lower_sweep_solution[1]

    @property
    def lower_sweep_end_direction_xy(self) -> tuple[float, float]:
        phi = self.lower_sweep_turn_rad
        return math.sin(phi), math.cos(phi)

    @property
    def lower_sweep_center_x(self) -> float:
        return self.inlet_throat_x + self.lower_sweep_radius

    @property
    def lower_sweep_center_y(self) -> float:
        return self.inlet_throat_y

    @property
    def bend_center_x(self) -> float:
        dx, _dy = self.lower_sweep_end_direction_xy
        return self.lower_elbow_vertical_x - self.bend_centerline_r * dx

    @property
    def bend_center_y(self) -> float:
        _dx, dy = self.lower_sweep_end_direction_xy
        return self.lower_elbow_vertical_y - self.bend_centerline_r * dy

    @property
    def bend_center_z(self) -> float:
        return self.horizontal_z + self.bend_centerline_r

    @property
    def fixed_outlet_top_z(self) -> float:
        return self.baseline_outlet_top_z - self.target_outlet_drop


D = Design()
BLACK_HOLE_CENTER_Z = 0.0
BLACK_HOLE_EDGE_CLEARANCE = 0.0
BLACK_HOLE_OUTER_D = 2.0 * (
    D.height / 2.0
    - D.edge_fillet_r
    - BLACK_HOLE_EDGE_CLEARANCE
    - BLACK_HOLE_CENTER_Z
)
BLACK_HOLE_VARIANT = replace(
    FINAL_200_VARIANT,
    name="190x210_scaled_black_hole",
    cube_outer=D.width,
    edge_fillet_r=D.edge_fillet_r,
    baffle_outer_d=BLACK_HOLE_OUTER_D,
)
BLACK_HOLE_SEAT_DEPTH = (
    BLACK_HOLE_VARIANT.recess_depth
    + BLACK_HOLE_VARIANT.driver_seat_extra_depth
)
REAR_EXTENSION_Y = D.depth - D.width
REAR_INNER_Y = D.center_y + D.depth / 2.0 - D.wall_stack_t
RESTORED_FILL_X = D.width / 2.0 - 12.0
RESTORED_FILL_Z = D.height / 2.0 - D.outer_skin_t - FINAL_200_FILL_ENTRY_D / 2.0
RESTORED_FEATURE_VARIANT = replace(
    BLACK_HOLE_VARIANT,
    name="190x210_restored_features",
    fill_port_x=RESTORED_FILL_X,
    fill_port_z=RESTORED_FILL_Z,
    fill_entry_d=FINAL_200_FILL_ENTRY_D,
    window_brace=True,
    window_brace_center_y=D.center_y,
    vertical_center_brace=True,
    vertical_brace_rear_y=REAR_INNER_Y,
    vertical_brace_height=10.0,
    horizontal_waist_brace=True,
    horizontal_brace_rear_y=REAR_INNER_Y,
    horizontal_brace_height=10.0,
)
P = replace(
    _final_params(RESTORED_FEATURE_VARIANT),
    front_cap_t=BLACK_HOLE_SEAT_DEPTH,
    rear_cap_t=D.wall_stack_t,
    horn_wavefront_t=D.horn_solved_wavefront_t,
)

# Redirect only the imported helper module's immutable design references in
# this isolated generator process.
folded.D = D
folded.P = P
common.D = D
common.P = P


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _fresh_solids(shape: Any) -> list[Any]:
    return [copy.copy(solid) for solid in shape.solids()]


def _single_solid_after_boolean(shape: Any, *, feature: str) -> Part:
    """Normalize Part/ShapeList boolean results without discarding fragments."""
    solids = _fresh_solids(shape)
    if len(solids) != 1:
        volumes = [solid.volume for solid in solids]
        boxes = [_bbox(solid) for solid in solids]
        raise ValueError(
            f"{feature} must remain one connected solid; got {len(solids)} "
            f"with volumes {volumes} and boxes {boxes}"
        )
    return _require_single_solid(solids[0].clean().fix(), feature=feature)


def _cut_single_solid(base: Part, cutter: Any, *, feature: str) -> Part:
    """Apply a cut and select only a volume-verified result solid.

    OpenCascade can return the untouched tool as a second ShapeList entry when
    a blind cylindrical cut is tangent to an adjacent swept clearance.  Rather
    than silently taking the largest solid, verify the expected subtraction
    volume and retain the unique solid that matches it.
    """
    overlap = _intersection_volume(base, cutter)
    if overlap <= 0.001:
        raise ValueError(f"{feature} does not intersect its intended support")
    expected_volume = base.volume - overlap
    solids = _fresh_solids(base.cut(cutter))
    # Swept circular faces can move the independently evaluated cut/intersection
    # volumes by a few hundredths of a cubic millimetre on a ~1.1e6 mm3 shell.
    # Keep this strict enough to reject any real fragment while allowing that
    # OpenCascade integration noise.
    tolerance = max(0.03, abs(expected_volume) * 3e-8)
    candidates = [
        solid
        for solid in solids
        if abs(solid.volume - expected_volume) <= tolerance
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"{feature} produced {len(solids)} solids and no unique "
            f"volume-verified result; expected {expected_volume:.6f} mm3, "
            f"got {[solid.volume for solid in solids]}"
        )
    return _require_single_solid(candidates[0].clean().fix(), feature=feature)


def _bbox(shape: Any) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min_mm": [round(bb.min.X, 4), round(bb.min.Y, 4), round(bb.min.Z, 4)],
        "max_mm": [round(bb.max.X, 4), round(bb.max.Y, 4), round(bb.max.Z, 4)],
        "size_mm": [round(bb.size.X, 4), round(bb.size.Y, 4), round(bb.size.Z, 4)],
    }


def _build_face_matched_jmlc_horn() -> Part:
    """Build the 190 mm horn from Le Cleac'h's exact 2007 recurrence."""
    return build_jmlc_horn(
        throat_d=P.horn_throat_d,
        mouth_outer_d=D.horn_profile_mouth_outer_d_input,
        wall_t=P.horn_wall_t,
        exit_angle_deg=P.horn_exit_angle_deg,
        wavefront_t=P.horn_wavefront_t,
        throat_angle_deg=P.horn_throat_angle_deg,
        step=P.horn_profile_step,
        lip_r=P.horn_lip_r,
        flange_d=P.horn_flange_d,
        flange_t=P.horn_flange_t,
        bolt_clearance_d=P.horn_bolt_clearance_d,
        bolt_3_bcd=P.horn_bolt_3_bcd,
        bolt_2_bcd=P.horn_bolt_2_bcd,
        rear_spigot_l=P.horn_bracket_t,
        rear_spigot_od=P.horn_spigot_od,
        profile_method="le_cleach_2007",
        include_three_bolt_pattern=False,
        include_two_bolt_pattern=True,
    )


def _placed_face_matched_horn_and_de250() -> tuple[Part, Any, dict[str, Any]]:
    horn_raw = _build_face_matched_jmlc_horn()
    raw_bb = horn_raw.bounding_box()
    physical_mouth_d = max(raw_bb.size.X, raw_bb.size.Y)
    if abs(physical_mouth_d - D.horn_target_physical_mouth_d) > 0.01:
        raise ValueError(
            "Exact JMLC horn mouth does not match the cabinet face: "
            f"{physical_mouth_d:.6f} mm"
        )

    # The only retained bolt pattern is the DE250's two-hole pattern. No axial
    # rotation is applied, so both fasteners remain horizontal in the XZ mount
    # plate after the horn is turned onto its global Y acoustic axis.
    horn = Rot(90.0, 0.0, 0.0) * horn_raw
    horn_bb = horn.bounding_box()
    horn_center_x = (horn_bb.min.X + horn_bb.max.X) / 2.0
    horn_center_z = (horn_bb.min.Z + horn_bb.max.Z) / 2.0
    placed_horn = Location(
        (
            D.horn_center_x - horn_center_x,
            D.horn_mount_face_y - horn_bb.max.Y,
            D.horn_center_z - horn_center_z,
        )
    ) * horn

    de250_import = import_step(ROOT / "objects" / "Compression DriverDE250.step")
    imported_solids = list(de250_import.solids())
    main_driver_solid = max(imported_solids, key=lambda solid: solid.volume)
    central_throat_solids = []
    for solid in imported_solids:
        if solid is main_driver_solid:
            continue
        bb = solid.bounding_box()
        if (
            bb.min.X <= 0.0 <= bb.max.X
            and bb.min.Y <= 0.0 <= bb.max.Y
            and bb.max.Z <= 0.01
        ):
            central_throat_solids.append(solid)
    if len(central_throat_solids) != 1:
        raise ValueError(
            "Expected one central DE250 throat insert in the reference STEP, "
            f"found {len(central_throat_solids)}"
        )
    # The supplied reference STEP also contains three disconnected long bolt
    # placeholders.  They belong to the discarded three-hole arrangement and
    # would falsely collide with the new two-hole plate, so do not present them
    # as part of the physical driver body.
    de250_raw = Compound(
        children=[
            copy.copy(main_driver_solid),
            *(copy.copy(solid) for solid in central_throat_solids),
        ]
    )
    de250 = Location(
        (D.horn_center_x, D.horn_mount_face_y, D.horn_center_z)
    ) * (Rot(90.0, 0.0, 0.0) * de250_raw)

    profile_data = jmlc_profile_metadata(
        throat_d=P.horn_throat_d,
        mouth_outer_d=D.horn_profile_mouth_outer_d_input,
        wall_t=P.horn_wall_t,
        exit_angle_deg=P.horn_exit_angle_deg,
        wavefront_t=P.horn_wavefront_t,
        throat_angle_deg=P.horn_throat_angle_deg,
        step=P.horn_profile_step,
        profile_method="le_cleach_2007",
    )
    if profile_data["profile_method"] != "le_cleach_2007":
        raise ValueError("Face-matched horn did not use the exact 2007 recurrence")
    axial_length_error = (
        float(profile_data["axial_length_mm_exact"])
        - D.horn_target_axial_length
    )
    if abs(axial_length_error) > 0.001:
        raise ValueError(
            "Short Le Cleac'h profile missed its exact axial target: "
            f"{axial_length_error:.6f} mm"
        )
    if P.horn_throat_d + 0.001 < D.de250_official_throat_d:
        raise ValueError(
            "Horn throat is smaller than the official DE250 exit: "
            f"{P.horn_throat_d:.3f} < {D.de250_official_throat_d:.3f} mm"
        )

    return placed_horn, de250, {
        "requested_wording_checked": (
            "No BMC component exists; the supplied and fitted component is B&C DE250."
        ),
        "compression_driver_source": "objects/Compression DriverDE250.step",
        "compression_driver_official_spec": {
            "source": "https://www.bcspeakers.com/en/products/hf-driver/1/8/DE250",
            "exit_diameter_mm": D.de250_official_throat_d,
            "two_bolt_pattern": "2 x M6 on 76 mm BCD",
            "three_bolt_pattern": "3 x M6 on 57 mm BCD",
            "overall_diameter_mm": 120.0,
            "depth_mm": 62.0,
        },
        "compression_driver_reference_cleanup": {
            "physical_body_and_central_throat_retained": True,
            "disconnected_three_hole_bolt_placeholders_removed": (
                len(imported_solids) - 1 - len(central_throat_solids)
            ),
        },
        "horn_source": "exact Le Cleac'h 2007 spreadsheet recurrence",
        "primary_reference": (
            "https://dome-acoustique.fr/gratuit/pavillon_JMLC.zip"
        ),
        "profile": profile_data,
        "profile_inputs": {
            "physical_rolled_envelope_target_d_mm": (
                D.horn_target_physical_mouth_d
            ),
            "calibrated_profile_mouth_outer_d_input_mm": (
                D.horn_profile_mouth_outer_d_input
            ),
            "physical_rolled_envelope_d_mm": physical_mouth_d,
            "acoustic_mouth_inner_d_mm": profile_data["mouth_inner_d_mm"],
            "throat_d_mm": P.horn_throat_d,
            "official_de250_exit_d_mm": D.de250_official_throat_d,
            "horn_minus_driver_exit_diameter_mm": (
                P.horn_throat_d - D.de250_official_throat_d
            ),
            "horn_to_driver_exit_area_ratio": (
                P.horn_throat_d / D.de250_official_throat_d
            ) ** 2,
            "throat_is_not_undersized": True,
            "wavefront_t": P.horn_wavefront_t,
            "reference_wavefront_t": D.horn_reference_wavefront_t,
            "reference_axial_length_mm": D.horn_reference_axial_length,
            "target_axial_shortening_mm": D.horn_axial_shorten,
            "target_axial_length_mm": D.horn_target_axial_length,
            "axial_length_target_error_mm": axial_length_error,
            "throat_half_angle_deg": P.horn_throat_angle_deg,
            "terminal_rollback_angle_deg": P.horn_exit_angle_deg,
            "uniform_scaling_used": False,
        },
        "three_spoke_driver_support_replaces_half_cup": True,
        "clamp_stack_mm": {
            "ring_front_y": D.horn_mount_face_y - D.horn_face_t,
            "ring_rear_y": D.horn_mount_face_y,
            "horn_spigot_rear_y": round(placed_horn.bounding_box().max.Y, 4),
            "de250_mount_face_y": D.horn_mount_face_y,
            "ring_thickness": D.horn_face_t,
        },
        "driver_support": {
            "front_mount_ring_diameter_mm": 2.0 * D.horn_mount_ring_r,
            "retained_horizontal_bolt_hole_count": 2,
            "three_hole_pattern_removed": True,
            "spoke_count": 3,
            "spoke_diameter_mm": D.horn_spoke_d,
            "driver_envelope_radius_mm": D.de250_envelope_r,
            "radial_spoke_clearance_mm": D.horn_spoke_gap,
        },
    }


def _bounding_boxes_overlap(left: Any, right: Any, *, tolerance: float = 0.001) -> bool:
    left_bb = left.bounding_box()
    right_bb = right.bounding_box()
    return not (
        left_bb.max.X < right_bb.min.X - tolerance
        or right_bb.max.X < left_bb.min.X - tolerance
        or left_bb.max.Y < right_bb.min.Y - tolerance
        or right_bb.max.Y < left_bb.min.Y - tolerance
        or left_bb.max.Z < right_bb.min.Z - tolerance
        or right_bb.max.Z < left_bb.min.Z - tolerance
    )


def _bounded_intersection_volume(left: Any, right: Any) -> float:
    if not _bounding_boxes_overlap(left, right):
        return 0.0
    return _intersection_volume(left, right)


def _outer_envelope() -> Part:
    outer = Pos(0.0, D.center_y, 0.0) * Box(D.width, D.depth, D.height)
    outer = fillet(outer.edges(), radius=D.edge_fillet_r)
    return _require_single_solid(outer.clean().fix(), feature="190 x 210 outer envelope")


def _inset_outer_envelope(offset: float) -> Part:
    """Exact concentric inset of the all-edge filleted exterior envelope."""
    if not 0.0 <= offset < min(D.width, D.depth, D.height) / 2.0:
        raise ValueError(f"Invalid outer-envelope inset: {offset:.3f} mm")
    radius = D.edge_fillet_r - offset
    if radius < 0.0:
        raise ValueError(
            f"Inset {offset:.3f} mm exceeds the {D.edge_fillet_r:.3f} mm edge radius"
        )
    inner = Pos(0.0, D.center_y, 0.0) * Box(
        D.width - 2.0 * offset,
        D.depth - 2.0 * offset,
        D.height - 2.0 * offset,
    )
    if radius > 0.0:
        inner = fillet(inner.edges(), radius=radius)
    return _require_single_solid(
        inner.clean().fix(), feature=f"{offset:.3f} mm inset rounded envelope"
    )


def _rectangular_cavity() -> Part:
    front_y = D.center_y - D.depth / 2.0
    front_inner_y = front_y + BLACK_HOLE_SEAT_DEPTH
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    inner_radius = D.edge_fillet_r - D.wall_stack_t
    with BuildPart() as cavity:
        with BuildSketch(Plane.XZ) as section:
            RectangleRounded(
                D.width - 2.0 * D.wall_stack_t,
                D.height - 2.0 * D.wall_stack_t,
                inner_radius,
            )
        extrude(
            amount=(rear_inner_y - front_inner_y) / 2.0,
            both=True,
        )
    rounded_xz_cavity = Pos(
        0.0,
        (front_inner_y + rear_inner_y) / 2.0,
        0.0,
    ) * cavity.part
    return _require_single_solid(
        rounded_xz_cavity.clean().fix(),
        feature="rounded XZ acoustic cavity with flat front and rear seams",
    )


def _black_hole_visible_tool() -> Part:
    return Pos(0.0, 0.0, BLACK_HOLE_CENTER_Z) * _front_tool_global_oriented(
        _curve_to_micro_seat_tool(P, BLACK_HOLE_VARIANT),
        P,
        BLACK_HOLE_VARIANT,
    )


def _black_hole_inner_relief() -> Part:
    front_y = D.center_y - D.depth / 2.0
    relief = Pos(0.0, 0.0, BLACK_HOLE_CENTER_Z) * _front_tool_global_oriented(
        _inner_relief_tool(P, BLACK_HOLE_VARIANT),
        P,
        BLACK_HOLE_VARIANT,
    )
    clip = Pos(0.0, front_y + BLACK_HOLE_SEAT_DEPTH / 2.0, 0.0) * Box(
        D.width - 2.0 * D.wall_stack_t,
        BLACK_HOLE_SEAT_DEPTH + 0.5,
        D.height - 2.0 * D.wall_stack_t,
    )
    return _primary_shape(relief & clip)


def _acoustic_domain() -> Part:
    return _primary_shape(
        (_rectangular_cavity() + _black_hole_inner_relief()).clean().fix()
    )


def _sand_void() -> Part:
    # The side, roof, and rear gaps retain 2-3-2 construction.  The complete
    # 7 mm floor stays solid, matching the original FINAL_200_VARIANT contract.
    # Construct the gap from two concentric filleted envelopes so its outer
    # surface remains exactly 2 mm inside every R8 exterior edge.
    front_y = D.center_y - D.depth / 2.0
    front_inner_y = front_y + BLACK_HOLE_SEAT_DEPTH
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    floor_top_z = -D.height / 2.0 + D.wall_stack_t
    outer_gap_boundary = _inset_outer_envelope(D.outer_skin_t)
    inner_gap_boundary = _inset_outer_envelope(
        D.outer_skin_t + D.sand_gap_t
    )
    concentric_gap_shell = (
        outer_gap_boundary - inner_gap_boundary
    ).clean().fix()

    clip_top_z = D.height / 2.0 + 1.0
    side_roof_clip = Pos(
        0.0,
        (front_inner_y + rear_inner_y) / 2.0,
        (floor_top_z + clip_top_z) / 2.0,
    ) * Box(
        D.width + 2.0,
        rear_inner_y - front_inner_y,
        clip_top_z - floor_top_z,
    )
    side_roof_gap = (concentric_gap_shell & side_roof_clip).clean().fix()

    rear_face_y = D.center_y + D.depth / 2.0
    rear_gap_min_y = rear_face_y - D.outer_skin_t - D.sand_gap_t
    rear_gap_max_y = rear_face_y - D.outer_skin_t
    rear_gap_clip = Pos(
        0.0,
        (rear_gap_min_y + rear_gap_max_y) / 2.0,
        (floor_top_z + clip_top_z) / 2.0,
    ) * Box(
        D.width + 2.0,
        rear_gap_max_y - rear_gap_min_y,
        clip_top_z - floor_top_z,
    )
    rear_gap = (concentric_gap_shell & rear_gap_clip).clean().fix()
    return Compound(
        children=[
            *_fresh_solids(side_roof_gap),
            *_fresh_solids(rear_gap),
        ]
    )


def _ellipse_loft_inlet(
    *,
    z0: float,
    z1: float,
    rx0: float,
    rz0: float,
    rx1: float,
    rz1: float,
) -> Part:
    run_dx, run_dy = D.inlet_run_direction_xy
    lateral = (-run_dy, run_dx, 0.0)
    with BuildPart() as result:
        for index in range(7):
            t = index / 6.0
            blend = t * t * (3.0 - 2.0 * t)
            x = D.inlet_x + D.inlet_flare_l * run_dx * t
            y = D.inlet_mouth_y + D.inlet_flare_l * run_dy * t
            z = z0 + (z1 - z0) * blend
            rx = rx0 + (rx1 - rx0) * blend
            rz = rz0 + (rz1 - rz0) * blend
            section_plane = Plane(
                origin=(x, y, z),
                x_dir=lateral,
                z_dir=(run_dx, run_dy, 0.0),
            )
            with BuildSketch(section_plane) as section:
                Ellipse(rx, rz)
            assert section.sketch.area > 0.0, "Inlet ellipse area must be positive"
        loft()
    return _require_single_solid(result.part.clean().fix(), feature="elliptical inlet flare")


def _ellipse_loft_z(
    *, z0: float, z1: float, y: float, rx0: float, ry0: float, rx1: float, ry1: float
) -> Part:
    with BuildPart() as result:
        for index in range(7):
            t = index / 6.0
            blend = t * t * (3.0 - 2.0 * t)
            z = z0 + (z1 - z0) * t
            rx = rx0 + (rx1 - rx0) * blend
            ry = ry0 + (ry1 - ry0) * blend
            section_plane = Plane(
                origin=(D.port_x, y, z),
                x_dir=(1.0, 0.0, 0.0),
                z_dir=(0.0, 0.0, 1.0),
            )
            with BuildSketch(section_plane) as section:
                Ellipse(rx, ry)
            assert section.sketch.area > 0.0, "Outlet ellipse area must be positive"
        loft()
    return _require_single_solid(result.part.clean().fix(), feature="elliptical outlet flare")


def _tower_shift_state(z: float) -> tuple[float, float]:
    """Return tower center y and dy/dz; this variant resolves to a straight rise."""
    span = D.upper_tower_shift_end_z - D.upper_tower_shift_start_z
    offset = D.upper_tower_y - D.port_y
    if abs(offset) < 1e-12:
        return D.port_y, 0.0
    if z <= D.upper_tower_shift_start_z:
        return D.port_y, 0.0
    if z >= D.upper_tower_shift_end_z:
        return D.upper_tower_y, 0.0
    u = (z - D.upper_tower_shift_start_z) / span
    blend, derivative = _quintic_smoothstep(u)
    return D.port_y + offset * blend, offset * derivative / span


def _tower_centerline_length(z0: float, z1: float) -> float:
    steps = 4000
    total = 0.0
    dz = (z1 - z0) / steps
    for index in range(steps):
        z = z0 + (index + 0.5) * dz
        _y, dy_dz = _tower_shift_state(z)
        total += abs(dz) * math.sqrt(1.0 + dy_dz**2)
    return total


def _tower_ellipse_loft_z(*, z0: float, z1: float, rx: float, ry: float) -> Part:
    # This variant has no upper-tower offset.  Use one analytic extrusion so
    # the separately printed visible riser has no loft stations or frame seams.
    if abs(D.upper_tower_y - D.port_y) < 1e-12:
        section_plane = Plane(
            origin=(D.port_x, D.port_y, z0),
            x_dir=(1.0, 0.0, 0.0),
            z_dir=(0.0, 0.0, 1.0),
        )
        with BuildSketch(section_plane) as section:
            Ellipse(rx, ry)
        assert section.sketch.area > 0.0, "Straight tower section must be positive"
        return _require_single_solid(
            extrude(
                section.sketch.faces()[0],
                amount=z1 - z0,
                dir=(0.0, 0.0, 1.0),
            ).clean().fix(),
            feature="analytic straight central tower",
        )

    stations = {index / 32.0 for index in range(33)}
    for z in (D.upper_tower_shift_start_z, D.upper_tower_shift_end_z):
        if z0 < z < z1:
            stations.add((z - z0) / (z1 - z0))
    sections: list[Any] = []
    for t in sorted(stations):
        z = z0 + (z1 - z0) * t
        y, dy_dz = _tower_shift_state(z)
        tangent = Vector(0.0, dy_dz, 1.0).normalized()
        section_plane = Plane(
            origin=(D.port_x, y, z),
            x_dir=(1.0, 0.0, 0.0),
            z_dir=tangent,
        )
        with BuildSketch(section_plane) as section:
            Ellipse(rx, ry)
        assert section.sketch.area > 0.0, "Shifted tower section must be positive"
        sections.append(section.sketch.faces()[0])
    return _require_single_solid(
        loft(sections, ruled=False).clean().fix(),
        feature="straight central tower",
    )


def _smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _quintic_smoothstep(value: float) -> tuple[float, float]:
    """Return zero-slope/zero-curvature blend and derivative."""
    value = max(0.0, min(1.0, value))
    blend = value**3 * (10.0 - 15.0 * value + 6.0 * value**2)
    derivative = 30.0 * value**2 * (1.0 - value) ** 2
    return blend, derivative


def _upper_drift_path() -> Any:
    """Single-direction planar drift from the rotated elbow to the tower."""
    fractions = D.upper_drift_control_fraction
    if len(fractions) < 4:
        raise ValueError("Upper drift needs at least four Bezier controls")
    if (
        fractions[0] != 0.0
        or fractions[-1] != 1.0
        or fractions[1] != 0.0
        or fractions[-2] != 1.0
        or any(b < a for a, b in zip(fractions, fractions[1:]))
    ):
        raise ValueError(
            "Upper-drift controls must be monotonic with vertical end tangents"
        )
    start = Vector(
        D.lower_elbow_vertical_x,
        D.lower_elbow_vertical_y,
        D.bend_center_z,
    )
    end = Vector(D.port_x, D.port_y, D.asymmetric_vertical_return_top_z)
    controls = [
        (
            start.X + (end.X - start.X) * fraction,
            start.Y + (end.Y - start.Y) * fraction,
            start.Z + (end.Z - start.Z) * index / (len(fractions) - 1),
        )
        for index, fraction in enumerate(fractions)
    ]
    path = Bezier(*controls)
    samples = [path.position_at(index / 200.0) for index in range(201)]
    if any(
        following.Z <= preceding.Z
        for preceding, following in zip(samples, samples[1:])
    ):
        raise ValueError("Upper drift does not rise monotonically")
    if any(
        following.X > preceding.X + 1e-6
        for preceding, following in zip(samples, samples[1:])
    ):
        raise ValueError("Upper drift reverses its leftward direction")
    return path


def _lower_sweep_path() -> Any:
    """Exact clockwise circular-plan sweep from the inlet to the R70 rise."""
    horizontal_plane = Plane(
        origin=(0.0, 0.0, D.horizontal_z),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, 0.0, 1.0),
    )
    with BuildLine(horizontal_plane) as path_builder:
        CenterArc(
            (D.lower_sweep_center_x, D.lower_sweep_center_y),
            D.lower_sweep_radius,
            start_angle=180.0,
            arc_size=-math.degrees(D.lower_sweep_turn_rad),
        )
    return path_builder.line


def _compound_route_base_lengths() -> tuple[float, float, float, float]:
    lower_sweep = D.lower_sweep_radius * D.lower_sweep_turn_rad
    bend = math.pi * D.bend_centerline_r / 2.0
    upper_drift = _upper_drift_path().length
    if min(lower_sweep, bend, upper_drift) <= 0.0:
        raise ValueError("Compound port centerline segments must all be positive")
    return lower_sweep, bend, upper_drift, lower_sweep + bend + upper_drift


def _compound_route_state(
    t: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Broad floor sweep, rotated R70 elbow, then one-way upper drift."""
    lower_sweep, bend, upper_drift, total = _compound_route_base_lengths()
    s = max(0.0, min(1.0, t)) * total
    end_dx, end_dy = D.lower_sweep_end_direction_xy

    if s <= lower_sweep:
        alpha = s / D.lower_sweep_radius
        x = D.inlet_throat_x + D.lower_sweep_radius * (1.0 - math.cos(alpha))
        y = D.inlet_throat_y + D.lower_sweep_radius * math.sin(alpha)
        z = D.horizontal_z
        tangent = (math.sin(alpha), math.cos(alpha), 0.0)
    elif s <= lower_sweep + bend:
        theta = -math.pi / 2.0 + (s - lower_sweep) / D.bend_centerline_r
        x = D.bend_center_x + D.bend_centerline_r * math.cos(theta) * end_dx
        y = D.bend_center_y + D.bend_centerline_r * math.cos(theta) * end_dy
        z = D.bend_center_z + D.bend_centerline_r * math.sin(theta)
        tangent = (
            -math.sin(theta) * end_dx,
            -math.sin(theta) * end_dy,
            math.cos(theta),
        )
    else:
        path = _upper_drift_path()
        u = (s - lower_sweep - bend) / upper_drift
        point = path.position_at(u)
        path_tangent = path.tangent_at(u).normalized()
        x, y, z = point.X, point.Y, point.Z
        tangent = (path_tangent.X, path_tangent.Y, path_tangent.Z)
    return (x, y, z), tangent


def _compound_route_length() -> float:
    return _compound_route_base_lengths()[3]


def _compound_route_t_for_z(z: float) -> float:
    if not D.bend_center_z <= z <= D.asymmetric_vertical_return_top_z:
        raise ValueError(
            f"Compound-route z={z:.3f} is outside "
            f"{D.bend_center_z:.3f}..{D.asymmetric_vertical_return_top_z:.3f}"
        )
    low = 0.0
    high = 1.0
    for _ in range(64):
        mid = (low + high) / 2.0
        point, _tangent = _compound_route_state(mid)
        if point[2] < z:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _bottom_mount_xy_positions() -> tuple[tuple[float, float], tuple[float, float]]:
    """Two floor ears on opposite sides of the broad lower sweep."""
    lower_sweep = _compound_route_base_lengths()[0]
    total = _compound_route_base_lengths()[3]
    (tube_x, tube_y, _tube_z), tangent = _compound_route_state(
        0.50 * lower_sweep / total
    )
    tangent_x, tangent_y, _tangent_z = tangent
    lateral_x, lateral_y = -tangent_y, tangent_x
    return (
        (
            tube_x + lateral_x * D.bottom_tab_left_offset_from_tube,
            tube_y + lateral_y * D.bottom_tab_left_offset_from_tube,
        ),
        (
            tube_x - lateral_x * D.bottom_tab_right_offset_from_tube,
            tube_y - lateral_y * D.bottom_tab_right_offset_from_tube,
        ),
    )


def _rear_mount_x_positions() -> tuple[float, float]:
    point, _tangent = _compound_route_state(
        _compound_route_t_for_z(D.bend_center_z)
    )
    tube_x = point[0]
    return (
        tube_x - D.rear_tab_inner_left_offset_from_tube,
        tube_x - D.rear_tab_outer_left_offset_from_tube,
    )


def _compound_route_ellipse(*, rx: float, rn: float) -> Part:
    if abs(rx - rn) > 1e-6:
        raise ValueError("Changing-plane route requires a round constant-area bore")
    lower_sweep, bend, _upper_drift, total = _compound_route_base_lengths()
    end_dx, end_dy = D.lower_sweep_end_direction_xy
    start_point, start_tangent = _compound_route_state(0.0)
    bend_start_t = lower_sweep / total
    bend_start_point, _bend_start_tangent = _compound_route_state(bend_start_t)
    bend_plane = Plane(
        origin=(D.bend_center_x, D.bend_center_y, D.bend_center_z),
        x_dir=(end_dx, end_dy, 0.0),
        z_dir=(end_dy, -end_dx, 0.0),
    )
    with BuildLine(bend_plane) as bend_path_builder:
        CenterArc(
            (0.0, 0.0),
            D.bend_centerline_r,
            start_angle=-90.0,
            arc_size=90.0,
        )
    route = Wire(
        [
            *_lower_sweep_path().edges(),
            *bend_path_builder.line.edges(),
            *_upper_drift_path().edges(),
        ]
    )
    start_dx, start_dy = D.inlet_run_direction_xy
    lateral = (-start_dy, start_dx, 0.0)
    section_plane = Plane(
        origin=start_point,
        x_dir=lateral,
        z_dir=start_tangent,
    )
    with BuildSketch(section_plane) as section:
        Circle(rx)
    assert section.sketch.area > 0.0, "Compound-route section must be positive"
    return _require_single_solid(
        sweep(
            section.sketch.faces()[0],
            path=route,
            is_frenet=False,
        ).clean().fix(),
        feature="round broad floor sweep, rotated R70 elbow, and one-way upper drift",
    )


def _swept_ellipse(*, outlet_throat_z: float, rx: float, rn: float) -> Part:
    if outlet_throat_z <= D.height / 2.0:
        raise ValueError("Solved outlet throat must extend above the enclosure")
    if outlet_throat_z <= D.asymmetric_vertical_return_top_z:
        raise ValueError("Outlet throat must clear the internal return-to-center path")
    radial_extra = rx - D.port_rx
    tower_rx = D.tower_rx + radial_extra
    tower_ry = D.tower_ry + radial_extra
    if (
        abs(D.tower_rx - D.port_rx) < 1e-9
        and abs(D.tower_ry - D.port_rz) < 1e-9
    ):
        return _fuse_connected(
            [
                _compound_route_ellipse(rx=rx, rn=rn),
                _tower_ellipse_loft_z(
                    z0=D.asymmetric_vertical_return_top_z,
                    z1=outlet_throat_z,
                    rx=tower_rx,
                    ry=tower_ry,
                ),
            ],
            feature=(
                "broad round floor sweep, rotated R70 elbow, and straight "
                "circular tower"
            ),
        )
    return _fuse_connected(
        [
            _compound_route_ellipse(rx=rx, rn=rn),
            _ellipse_loft_z(
                z0=D.asymmetric_vertical_return_top_z,
                z1=D.tower_transition_end_z,
                y=D.port_y,
                rx0=rx,
                ry0=rn,
                rx1=tower_rx,
                ry1=tower_ry,
            ),
            _tower_ellipse_loft_z(
                z0=D.tower_transition_end_z,
                z1=outlet_throat_z,
                rx=tower_rx,
                ry=tower_ry,
            ),
        ],
        feature=(
            "broad round floor sweep, rotated R70 elbow, and straight circular tower"
        ),
    )


def _fuse_connected(parts: list[Part], *, feature: str) -> Part:
    result = parts[0]
    for part in parts[1:]:
        result = (result + part).clean().fix()
    return _require_single_solid(result, feature=feature)


def _structural_tower_outer_envelope(
    *, outlet_throat_z: float, outer_extra: float
) -> Part:
    """Hidden OD transition and constant round weight-bearing column."""
    base_r = D.port_rx + D.port_wall_t + outer_extra
    structural_r = D.port_rx + D.structural_tower_wall_t + outer_extra
    if D.structural_wall_transition_start_z < D.asymmetric_vertical_return_top_z:
        raise ValueError("Structural wall transition starts before the straight tower")
    if D.structural_wall_transition_end_z > D.height / 2.0 - D.wall_stack_t:
        raise ValueError("Structural wall transition must finish below the inner roof")
    return _fuse_connected(
        [
            _ellipse_loft_z(
                z0=D.structural_wall_transition_start_z,
                z1=D.structural_wall_transition_end_z,
                y=D.port_y,
                rx0=base_r,
                ry0=base_r,
                rx1=structural_r,
                ry1=structural_r,
            ),
            _tower_ellipse_loft_z(
                z0=D.structural_wall_transition_end_z,
                z1=outlet_throat_z,
                rx=structural_r,
                ry=structural_r,
            ),
        ],
        feature="hidden round wall-thickness transition and structural column",
    )


def _path_solids(outlet_z: float, *, outer_extra: float = 0.0) -> tuple[Part, Part]:
    outer_wall = D.port_wall_t + outer_extra
    outlet_throat_z = outlet_z - D.outlet_flare_l
    inner_main = _swept_ellipse(
        outlet_throat_z=outlet_throat_z,
        rx=D.port_rx,
        rn=D.port_rz,
    )
    outer_main = _swept_ellipse(
        outlet_throat_z=outlet_throat_z,
        rx=D.port_rx + outer_wall,
        rn=D.port_rz + outer_wall,
    )
    structural_outer = _structural_tower_outer_envelope(
        outlet_throat_z=outlet_throat_z,
        outer_extra=outer_extra,
    )
    inner = _fuse_connected(
        [
            _ellipse_loft_inlet(
                z0=D.inlet_mouth_center_z,
                z1=D.inlet_flat_center_z,
                rx0=D.inlet_mouth_width / 2.0,
                rz0=D.inlet_mouth_height / 2.0,
                rx1=D.inlet_flat_width / 2.0,
                rz1=D.inlet_flat_height / 2.0,
            ),
            inner_main,
            _ellipse_loft_z(
                z0=outlet_throat_z,
                z1=outlet_z,
                y=D.upper_tower_y,
                rx0=D.tower_rx,
                ry0=D.tower_ry,
                rx1=D.outlet_mouth_width / 2.0,
                ry1=D.outlet_mouth_depth / 2.0,
            ),
        ],
        feature="continuous single circular airway",
    )
    outer = _fuse_connected(
        [
            _ellipse_loft_inlet(
                z0=D.inlet_mouth_center_z,
                z1=D.inlet_flat_center_z,
                rx0=D.inlet_mouth_width / 2.0 + outer_wall,
                rz0=D.inlet_mouth_height / 2.0 + outer_wall,
                rx1=D.inlet_flat_width / 2.0 + outer_wall,
                rz1=D.inlet_flat_height / 2.0 + outer_wall,
            ),
            outer_main,
            structural_outer,
            _ellipse_loft_z(
                z0=outlet_throat_z,
                z1=outlet_z,
                y=D.upper_tower_y,
                rx0=D.tower_rx + D.structural_tower_wall_t + outer_extra,
                ry0=D.tower_ry + D.structural_tower_wall_t + outer_extra,
                rx1=(
                    D.outlet_mouth_width / 2.0
                    + D.structural_tower_wall_t
                    + outer_extra
                ),
                ry1=(
                    D.outlet_mouth_depth / 2.0
                    + D.structural_tower_wall_t
                    + outer_extra
                ),
            ),
        ],
        feature="continuous circular outer envelope with structural riser",
    )
    return inner, outer


def _bridge_posts() -> list[Part]:
    posts: list[Part] = []
    gap_mid_x = D.width / 2.0 - D.outer_skin_t - D.sand_gap_t / 2.0
    gap_mid_y_rear = (
        D.center_y + D.depth / 2.0 - D.outer_skin_t - D.sand_gap_t / 2.0
    )
    gap_mid_z = D.height / 2.0 - D.outer_skin_t - D.sand_gap_t / 2.0
    for y, z in ((-30.0, -50.0), (-30.0, 50.0), (45.0, -50.0), (45.0, 50.0)):
        for x in (-gap_mid_x, gap_mid_x):
            posts.append(_oriented_cylinder(diameter=4.0, depth=3.4, axis="x", center=(x, y, z)))
    # The original variant has a solid floor, so only the roof needs z-directed
    # point bridges through a sand gap.
    for x, y in ((-65.0, -35.0), (65.0, -35.0), (-65.0, 35.0), (65.0, 35.0)):
        posts.append(
            _oriented_cylinder(
                diameter=4.0,
                depth=3.4,
                axis="z",
                center=(x, y, gap_mid_z),
            )
        )
    for x, z in ((-74.0, -74.0), (74.0, -74.0), (-74.0, 74.0), (74.0, 74.0)):
        posts.append(_oriented_cylinder(diameter=4.0, depth=3.4, axis="y", center=(x, gap_mid_y_rear, z)))
    return posts


def _rear_shifted(shape: Any) -> Any:
    """Move square-cabinet rear features onto the 20 mm-deeper rear wall."""
    return Pos(0.0, REAR_EXTENSION_Y, 0.0) * shape


def _sand_fill_blister_shell(fill_x: float) -> Any:
    """Create the supported curved fill transition as a hollow shell first."""
    support = _rear_shifted(
        _fill_port_inner_support(
            P,
            RESTORED_FEATURE_VARIANT,
            x=fill_x,
            z=P.fill_port_z,
        )
    )
    passage = _rear_shifted(
        _variant_sand_fill_port_cutout(
            P,
            RESTORED_FEATURE_VARIANT,
            x=fill_x,
            z=P.fill_port_z,
        )
    )
    return (support - passage).fix()


def _sand_fill_rear_bore(fill_x: float) -> Part:
    # Extend 1.2 mm through the rear inner face so the straight entry overlaps
    # the already-hollow transition without cutting a loft through the full base.
    depth = P.rear_cap_t + 1.2
    rear_face_y = D.center_y + D.depth / 2.0
    return _oriented_cylinder(
        diameter=P.fill_entry_d,
        depth=depth,
        axis="y",
        center=(fill_x, rear_face_y - depth / 2.0, P.fill_port_z),
    )


def _front_brace_blends() -> Compound:
    """Mold four equal-height rail roots into the actual black-hole contour.

    A root that starts only at the flat driver-seat plane leaves an air pocket
    behind the curved outer portion of the black-hole face.  Start a full-depth
    rail ahead of the enclosure, clip it to the rounded outer envelope, and cut
    it with the same visible recess tool as the baffle.  The resulting front
    face therefore follows the real recess exactly and fills the local dual-skin
    void, while its 10 mm inward face remains coplanar with the complete rail.
    """
    enclosure_front_y = D.center_y - D.depth / 2.0
    driver_seat_y = enclosure_front_y + BLACK_HOLE_SEAT_DEPTH
    raw_front_y = enclosure_front_y - 1.0
    tail_y = (
        driver_seat_y
        - D.front_brace_baffle_embed
        + D.front_brace_blend_length
    )
    cavity_half = D.width / 2.0 - D.wall_stack_t
    rail_inner_r = cavity_half - RESTORED_FEATURE_VARIANT.vertical_brace_height
    rail_outer_r = cavity_half + RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed
    actual_ring_embed = SEAT_LAND_OD / 2.0 - rail_inner_r
    if actual_ring_embed < D.front_brace_ring_embed - 0.001:
        raise ValueError(
            "Full-depth front root does not overlap the driver land: "
            f"{actual_ring_embed:.6f} mm"
        )
    raw_top = Pos(
        0.0,
        (raw_front_y + tail_y) / 2.0,
        (rail_inner_r + rail_outer_r) / 2.0,
    ) * Box(
        RESTORED_FEATURE_VARIANT.vertical_brace_width,
        tail_y - raw_front_y,
        rail_outer_r - rail_inner_r,
    )
    top = (
        (raw_top & _outer_envelope()) - _black_hole_visible_tool()
    ).clean().fix()
    return Compound(
        children=[
            *_fresh_solids(top),
            *_fresh_solids(Rot(0.0, 180.0, 0.0) * top),
            *_fresh_solids(Rot(0.0, 90.0, 0.0) * top),
            *_fresh_solids(Rot(0.0, -90.0, 0.0) * top),
        ]
    )


def _longitudinal_wall_rails() -> Compound:
    """Build the top and side rails; the solid floor needs no lower rail."""
    driver_seat_y = D.center_y - D.depth / 2.0 + BLACK_HOLE_SEAT_DEPTH
    buttress_tail_y = (
        driver_seat_y
        - D.front_brace_baffle_embed
        + D.front_brace_blend_length
    )
    overlap = 0.50
    front_y = buttress_tail_y - overlap
    rear_y = REAR_INNER_Y
    y_span = rear_y - front_y
    cavity_half = D.width / 2.0 - D.wall_stack_t
    radial_height = RESTORED_FEATURE_VARIANT.vertical_brace_height
    skin_embed = RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed
    tangential_width = RESTORED_FEATURE_VARIANT.vertical_brace_width
    radial_size = radial_height + skin_embed
    radial_center = cavity_half - radial_height / 2.0 + skin_embed / 2.0
    y_center = (front_y + rear_y) / 2.0
    top = Pos(0.0, y_center, radial_center) * Box(
        tangential_width,
        y_span,
        radial_size,
    )
    return Compound(
        children=[
            *_fresh_solids(top),
            *_fresh_solids(Rot(0.0, 90.0, 0.0) * top),
            *_fresh_solids(Rot(0.0, -90.0, 0.0) * top),
        ]
    )


def _rear_cradle_brace(port_clearance: Part) -> Any:
    """Rear-wall cross brace with a swept cradle for the vertical tube."""
    cavity_half = D.width / 2.0 - D.wall_stack_t
    skin_embed = RESTORED_FEATURE_VARIANT.window_brace_skin_embed
    brace = Pos(
        0.0,
        D.rear_cradle_front_y + D.rear_cradle_depth / 2.0,
        0.0,
    ) * Box(
        2.0 * (cavity_half + skin_embed),
        D.rear_cradle_depth,
        D.rear_cradle_height,
    )
    return (brace - port_clearance).clean().fix()


def _floor_free_window_brace() -> Any:
    """Retain the top and side frame while deleting its redundant floor rail."""
    raw = _window_brace(P, RESTORED_FEATURE_VARIANT)
    floor_top_z = -D.height / 2.0 + D.wall_stack_t
    rail_inner_z = (
        D.width / 2.0
        - D.wall_stack_t
        - RESTORED_FEATURE_VARIANT.window_brace_height
    )
    cutter_top_z = -rail_inner_z + 0.05
    cutter = Pos(
        0.0,
        RESTORED_FEATURE_VARIANT.window_brace_center_y,
        (floor_top_z - 20.0 + cutter_top_z) / 2.0,
    ) * Box(
        D.width + 20.0,
        RESTORED_FEATURE_VARIANT.window_brace_width + 4.0,
        cutter_top_z - (floor_top_z - 20.0),
    )
    return (raw - cutter).clean().fix()


def _tube_mount_insert_pockets() -> list[Part]:
    """Blind heat-set-insert pockets in the two structural cradles."""
    pockets: list[Part] = []
    for x, y in _bottom_mount_xy_positions():
        pockets.append(
            _oriented_cylinder(
                diameter=D.tube_mount_insert_d,
                depth=D.bottom_tube_mount_insert_depth,
                axis="z",
                center=(
                    x,
                    y,
                    D.bottom_tab_bottom_z
                    - D.bottom_tube_mount_insert_depth / 2.0,
                ),
            )
        )
    for x in _rear_mount_x_positions():
        pockets.append(
            _oriented_cylinder(
                diameter=D.tube_mount_insert_d,
                depth=D.tube_mount_insert_depth,
                axis="y",
                center=(
                    x,
                    D.rear_cradle_front_y + D.tube_mount_insert_depth / 2.0,
                    D.bend_center_z,
                ),
            )
        )
    return pockets


def _internal_tower_mount_saddle(*, clearance: float = 0.0) -> Part:
    """L-shaped tower plate bearing on the inner roof and rear wall."""
    roof_inner_z = D.height / 2.0 - D.wall_stack_t
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    roof = Pos(
        0.0,
        D.internal_mount_roof_front_y + D.internal_mount_roof_depth / 2.0,
        roof_inner_z - D.internal_mount_plate_t / 2.0,
    ) * Box(
        D.internal_mount_plate_w + 2.0 * clearance,
        D.internal_mount_roof_depth + 2.0 * clearance,
        D.internal_mount_plate_t + 2.0 * clearance,
    )
    rear = Pos(
        0.0,
        rear_inner_y - D.internal_mount_plate_t / 2.0,
        (D.internal_mount_rear_bottom_z + roof_inner_z) / 2.0,
    ) * Box(
        D.internal_mount_plate_w + 2.0 * clearance,
        D.internal_mount_plate_t + 2.0 * clearance,
        roof_inner_z - D.internal_mount_rear_bottom_z + 2.0 * clearance,
    )
    return _require_single_solid(
        (roof + rear).clean().fix(), feature="internal roof-and-rear tower saddle"
    )


def _internal_tower_mount_clearance_holes() -> list[Part]:
    roof_inner_z = D.height / 2.0 - D.wall_stack_t
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    holes: list[Part] = []
    for x in (-D.internal_mount_roof_x, D.internal_mount_roof_x):
        holes.append(
            _oriented_cylinder(
                diameter=D.internal_mount_clearance_d,
                depth=D.internal_mount_plate_t + 2.0,
                axis="z",
                center=(
                    x,
                    D.internal_mount_roof_y,
                    roof_inner_z - D.internal_mount_plate_t / 2.0,
                ),
            )
        )
    for x in (-D.internal_mount_rear_x, D.internal_mount_rear_x):
        holes.append(
            _oriented_cylinder(
                diameter=D.internal_mount_clearance_d,
                depth=D.internal_mount_plate_t + 2.0,
                axis="y",
                center=(
                    x,
                    rear_inner_y - D.internal_mount_plate_t / 2.0,
                    D.internal_mount_rear_z,
                ),
            )
        )
    return holes


def _internal_tower_mount_platforms() -> Compound:
    """Point-like solid lands bridging the 2-3-2 roof and rear wall."""
    roof_inner_z = D.height / 2.0 - D.wall_stack_t
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    platforms: list[Part] = []
    for x in (-D.internal_mount_roof_x, D.internal_mount_roof_x):
        platforms.append(
            _oriented_cylinder(
                diameter=D.internal_mount_platform_d,
                depth=D.wall_stack_t,
                axis="z",
                center=(
                    x,
                    D.internal_mount_roof_y,
                    roof_inner_z + D.wall_stack_t / 2.0,
                ),
            )
        )
    for x in (-D.internal_mount_rear_x, D.internal_mount_rear_x):
        platforms.append(
            _oriented_cylinder(
                diameter=D.internal_mount_platform_d,
                depth=D.wall_stack_t,
                axis="y",
                center=(
                    x,
                    rear_inner_y + D.wall_stack_t / 2.0,
                    D.internal_mount_rear_z,
                ),
            )
        )
    return Compound(children=platforms)


def _internal_tower_mount_insert_pockets() -> list[Part]:
    roof_inner_z = D.height / 2.0 - D.wall_stack_t
    rear_inner_y = D.center_y + D.depth / 2.0 - D.wall_stack_t
    pockets: list[Part] = []
    for x in (-D.internal_mount_roof_x, D.internal_mount_roof_x):
        pockets.append(
            _oriented_cylinder(
                diameter=D.internal_mount_insert_d,
                depth=D.internal_mount_insert_depth,
                axis="z",
                center=(
                    x,
                    D.internal_mount_roof_y,
                    roof_inner_z + D.internal_mount_insert_depth / 2.0,
                ),
            )
        )
    for x in (-D.internal_mount_rear_x, D.internal_mount_rear_x):
        pockets.append(
            _oriented_cylinder(
                diameter=D.internal_mount_insert_d,
                depth=D.internal_mount_insert_depth,
                axis="y",
                center=(
                    x,
                    rear_inner_y + D.internal_mount_insert_depth / 2.0,
                    D.internal_mount_rear_z,
                ),
            )
        )
    return pockets


def _internal_tower_mount_displacement(port_outer: Part) -> Part:
    """Filled in-box envelope of the upper tube and internal L saddle."""
    roof_outer_z = D.height / 2.0
    clip = Pos(
        0.0,
        D.center_y,
        (D.internal_tower_bottom_z + roof_outer_z) / 2.0,
    ) * Box(
        300.0,
        300.0,
        roof_outer_z - D.internal_tower_bottom_z,
    )
    upper_tube = _primary_shape(port_outer & clip)
    result: Any = upper_tube.fuse(_internal_tower_mount_saddle()).clean().fix()
    for hole in _internal_tower_mount_clearance_holes():
        result -= hole
    return _require_single_solid(
        result.clean().fix(), feature="upper tower in-box displacement"
    )


def _bottom_tab_brace_clearance() -> Compound:
    """Keep the redundant lower brace rail away from the floor-mounted ears."""
    clearance = 0.50
    parts: list[Part] = []
    for x, y in _bottom_mount_xy_positions():
        parts.append(
            Pos(
                x,
                y,
                D.bottom_tab_bottom_z
                + D.tube_tab_seating_clearance
                + D.tube_tab_t / 2.0,
            )
            * Box(
                D.bottom_tab_width + 2.0 * clearance,
                D.bottom_tab_depth + 2.0 * clearance,
                D.tube_tab_t + 2.0 * clearance,
            )
        )
    return Compound(children=parts)


def _rear_tab_brace_clearance() -> Compound:
    """Notch only the longitudinal rail where the rear tube ears pass."""
    clearance = 0.25
    parts: list[Part] = []
    for x in _rear_mount_x_positions():
        parts.append(
            Pos(
                x,
                D.rear_cradle_front_y
                - D.tube_tab_seating_clearance
                - D.tube_tab_t / 2.0,
                D.bend_center_z,
            )
            * Box(
                D.rear_tab_width + 2.0 * clearance,
                D.tube_tab_t + 2.0 * clearance,
                D.rear_tab_height + 2.0 * clearance,
            )
        )
    return Compound(children=parts)


def _restored_internal_braces(port_clearance: Part) -> Compound:
    """Restore the brace network, leaving the solid floor open around the tube.

    The lower rail of the transverse window brace is not kept continuous.  The
    swept install envelope cuts straight through it, so only open side pads
    remain to cradle and fasten the removable duct; no redundant bridge spans
    the already-solid floor beneath the airway.
    """
    enclosure_clip = _outer_envelope()
    raw_braces = [
        *_fresh_solids(_floor_free_window_brace()),
        *_fresh_solids(_longitudinal_wall_rails()),
    ]
    saddle_clearance = _internal_tower_mount_saddle(
        clearance=D.tube_install_clearance
    )
    bottom_tab_clearance = _bottom_tab_brace_clearance()
    rear_tab_clearance = _rear_tab_brace_clearance()
    trimmed_solids: list[Any] = []
    for brace in raw_braces:
        current = _fresh_solids(brace & enclosure_clip)
        for cutter in (
            port_clearance,
            saddle_clearance,
            bottom_tab_clearance,
            rear_tab_clearance,
        ):
            next_solids: list[Any] = []
            for solid in current:
                next_solids.extend(
                    cut_solid.clean().fix()
                    for cut_solid in _fresh_solids(solid - cutter)
                )
            current = next_solids
        trimmed_solids.extend(current)
    trimmed_solids.extend(_fresh_solids(_front_brace_blends()))
    trimmed_solids.extend(_fresh_solids(_rear_cradle_brace(port_clearance)))
    if not trimmed_solids:
        raise ValueError("Port clearance removed the entire internal brace network")
    return Compound(children=trimmed_solids)


def _tube_mounting_tabs() -> Compound:
    """Four ears printed integrally with the removable internal tube."""
    tabs: list[Part] = []
    for x, y in _bottom_mount_xy_positions():
        tabs.append(
            Pos(
                x,
                y,
                D.bottom_tab_bottom_z
                + D.tube_tab_seating_clearance
                + D.tube_tab_t / 2.0,
            )
            * Box(D.bottom_tab_width, D.bottom_tab_depth, D.tube_tab_t)
        )

    for x in _rear_mount_x_positions():
        tabs.append(
            Pos(
                x,
                D.rear_cradle_front_y
                - D.tube_tab_seating_clearance
                - D.tube_tab_t / 2.0,
                D.bend_center_z,
            )
            * Box(D.rear_tab_width, D.tube_tab_t, D.rear_tab_height)
        )
    return Compound(children=tabs)


def _tube_mount_clearance_holes() -> list[Part]:
    holes: list[Part] = []
    for x, y in _bottom_mount_xy_positions():
        holes.append(
            _oriented_cylinder(
                diameter=D.tube_mount_clearance_d,
                depth=D.tube_tab_t + 2.0,
                axis="z",
                center=(
                    x,
                    y,
                    D.bottom_tab_bottom_z
                    + D.tube_tab_seating_clearance
                    + D.tube_tab_t / 2.0,
                ),
            )
        )
    for x in _rear_mount_x_positions():
        holes.append(
            _oriented_cylinder(
                diameter=D.tube_mount_clearance_d,
                depth=D.tube_tab_t + 2.0,
                axis="y",
                center=(
                    x,
                    D.rear_cradle_front_y
                    - D.tube_tab_seating_clearance
                    - D.tube_tab_t / 2.0,
                    D.bend_center_z,
                ),
            )
        )
    return holes


def build_internal_tube(port_airway: Part, port_outer: Part) -> tuple[Part, Part]:
    """Build the removable in-box port and its full displacement envelope."""
    lower_z = -D.height / 2.0
    lower_clip = Pos(
        0.0,
        D.center_y,
        (lower_z + D.internal_tower_bottom_z) / 2.0,
    ) * Box(
        300.0,
        300.0,
        D.internal_tower_bottom_z - lower_z,
    )
    enclosure_clip = _outer_envelope() & lower_clip
    in_box_outer = _primary_shape(port_outer & enclosure_clip)
    in_box_airway = _primary_shape(port_airway & enclosure_clip)
    tabs = _tube_mounting_tabs()
    tab_airway_clearance = _compound_route_ellipse(
        rx=D.port_rx + 0.25,
        rn=D.port_rz + 0.25,
    )

    tube: Any = (in_box_outer - in_box_airway).clean().fix()
    displacement: Any = in_box_outer
    for raw_tab in tabs.solids():
        tab = (raw_tab - tab_airway_clearance).clean().fix()
        tube = tube.fuse(tab).clean().fix()
        displacement = displacement.fuse(tab).clean().fix()
    # The upper tower's rear plate locally becomes the tube wall.  Relieve the
    # removable lower duct around that plate so the two printable parts can be
    # assembled without occupying the same material.
    saddle_clearance = _internal_tower_mount_saddle(
        clearance=D.tube_install_clearance
    )
    tube = _require_single_solid(
        tube - saddle_clearance,
        feature="lower tube after upper-saddle clearance",
    )
    displacement = _require_single_solid(
        displacement - saddle_clearance,
        feature="lower displacement after upper-saddle clearance",
    )
    for index, hole in enumerate(_tube_mount_clearance_holes()):
        tube = _require_single_solid(
            tube - hole,
            feature=f"lower tube after mounting hole {index + 1}",
        )
        displacement = _require_single_solid(
            displacement - hole,
            feature=f"lower displacement after mounting hole {index + 1}",
        )
    return (
        _require_single_solid(
            tube.clean().fix(), feature="removable internal round port with four tabs"
        ),
        _require_single_solid(
            displacement.clean().fix(),
            feature="internal port and mounting-tab displacement envelope",
        ),
    )


def build_base(
    port_clearance: Part,
    port_install_clearance: Part,
    *,
    include_gx16: bool = True,
    include_fill_ports: bool = True,
) -> Part:
    separated_skins = _outer_envelope() - _rectangular_cavity() - _sand_void()
    base: Any = Compound(children=[copy.copy(solid) for solid in separated_skins.solids()])
    for post in _bridge_posts():
        base = base.fuse(post)
    base = _require_single_solid(
        base.clean().fix(),
        feature="rounded 2-3-2 walls with a point-bridged roof and solid floor",
    )

    if include_gx16:
        base = base.fuse(_rear_shifted(_gx16_connector_island(P))).clean().fix()
    if include_fill_ports:
        for fill_x in (-P.fill_port_x, P.fill_port_x):
            base = base.fuse(_sand_fill_blister_shell(fill_x)).clean().fix()
    base = _require_single_solid(
        base, feature="shell with GX16 island and sand-fill blisters"
    )

    for platform in _internal_tower_mount_platforms().solids():
        base = base.fuse(platform).clean().fix()
    base = _require_single_solid(
        base, feature="shell with four internal upper-tower mounting platforms"
    )

    # Finish the black-hole recess before adding the four structural roots.
    # Cutting the recess after brace fusion was reopening a visible slot at
    # every collar intersection.  The canonical buttresses are now the final
    # material at those four joints.
    base -= _black_hole_visible_tool()
    base -= _black_hole_inner_relief()
    base = _require_single_solid(
        base.clean().fix(), feature="shell with finished black-hole recess"
    )

    braces = _restored_internal_braces(port_clearance)
    for brace_solid in braces.solids():
        base = base.fuse(brace_solid).clean().fix()
    base = _require_single_solid(
        base, feature="port-relieved internal brace and cradle network"
    )

    # The in-box duct is a separate print, but the lower round tube now bears
    # directly on the untouched solid floor. Clip the assembly clearance above
    # the floor tangent so it still opens the roof/socket and clears braces
    # without carving any port-shaped channel into the 7 mm floor.
    floor_top_z = -D.height / 2.0 + D.wall_stack_t
    clearance_clip = Pos(
        0.0,
        D.center_y,
        (floor_top_z + 0.01 + D.height / 2.0) / 2.0,
    ) * Box(
        D.width + 2.0,
        D.depth + 2.0,
        D.height / 2.0 - floor_top_z - 0.01,
    )
    in_box_install_clearance = _primary_shape(
        port_install_clearance & _outer_envelope() & clearance_clip
    )
    base -= in_box_install_clearance
    base = _require_single_solid(
        base.clean().fix(), feature="base with floor-tangent removable tube"
    )

    front_y = D.center_y - D.depth / 2.0
    driver_seat_y = front_y + BLACK_HOLE_SEAT_DEPTH
    for index in range(P.driver_screw_count):
        angle = math.tau * index / P.driver_screw_count + math.pi / 4.0
        base -= _oriented_cylinder(
            diameter=P.insert_bore_d,
            depth=P.driver_insert_bore_depth,
            axis="y",
            center=(
                P.driver_bolt_circle_r * math.cos(angle),
                driver_seat_y - P.driver_insert_bore_depth / 2.0,
                P.driver_bolt_circle_r * math.sin(angle) + BLACK_HOLE_CENTER_Z,
            ),
        )
    for index, pocket in enumerate(_tube_mount_insert_pockets()):
        base = _cut_single_solid(
            base,
            pocket,
            feature=f"base after tube insert pocket {index + 1}",
        )
    for index, pocket in enumerate(_internal_tower_mount_insert_pockets()):
        base = _cut_single_solid(
            base,
            pocket,
            feature=f"base after upper-tower insert pocket {index + 1}",
        )

    if include_gx16:
        base = _cut_single_solid(
            base,
            _rear_shifted(_gx16_rear_cutout_corner(P)),
            feature="GX16-cut base",
        )
    if include_fill_ports:
        for fill_x in (-P.fill_port_x, P.fill_port_x):
            base = _cut_single_solid(
                base,
                _sand_fill_rear_bore(fill_x),
                feature=f"sand-fill passage at x={fill_x}",
            )
    return _require_single_solid(
        base.clean().fix(), feature="finished 190 x 210 monocoque base"
    )


def _printed_non_port_cavity_intrusions(
    port_clearance: Part,
    port_install_clearance: Part,
) -> Compound:
    """Return only printed features that occupy acoustic volume.

    Keeping the dual-skin shell out of this cutter makes exact volume accounting
    fast and auditable even after the detailed brace network is restored.
    """
    parts: list[Any] = []
    parts.extend(_fresh_solids(_restored_internal_braces(port_clearance)))

    platforms = _internal_tower_mount_platforms()
    for pocket in _internal_tower_mount_insert_pockets():
        platforms -= pocket
    parts.extend(_fresh_solids(platforms))

    gx_island = _rear_shifted(_gx16_connector_island(P))
    gx_island -= _rear_shifted(_gx16_rear_cutout_corner(P))
    parts.extend(_fresh_solids(gx_island))

    for fill_x in (-P.fill_port_x, P.fill_port_x):
        parts.extend(_fresh_solids(_sand_fill_blister_shell(fill_x)))

    if not parts:
        raise ValueError("Printed cavity-intrusion set is unexpectedly empty")
    return Compound(children=parts)


def _side_driver_spoke(sign: float) -> Part:
    """Round side rail leaving the plate radially and blending into the tube."""
    if sign not in (-1.0, 1.0):
        raise ValueError("Driver spoke side must be -1 or +1")
    spoke_r = D.horn_spoke_d / 2.0
    # Keep the root's rear tangent exactly on the DE250 mounting plane.  The
    # rail first moves radially outside the driver while it is still in front
    # of that plane, then turns aft with a true 2 mm radial surface gap.
    face_center_y = D.horn_mount_face_y - spoke_r
    center_r = D.de250_envelope_r + D.horn_spoke_gap + spoke_r
    turn_r = center_r + D.horn_spoke_turn_extra_r
    driver_rear_y = D.horn_mount_face_y + D.de250_rear_depth
    tube_side_x = D.tower_outer_rx

    path_plane = Plane(
        origin=(0.0, 0.0, D.horn_center_z),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, 0.0, 1.0),
    )
    with BuildLine(path_plane) as path:
        Line(
            (sign * D.horn_spoke_root_r, face_center_y),
            (sign * center_r, face_center_y),
        )
        Bezier(
            (sign * center_r, face_center_y),
            (sign * (center_r + 3.0), face_center_y),
            (sign * turn_r, face_center_y + 2.0),
            (sign * turn_r, face_center_y + 5.0),
        )
        Bezier(
            (sign * turn_r, face_center_y + 5.0),
            (sign * turn_r, face_center_y + 18.0),
            (sign * center_r, face_center_y + 20.0),
            (sign * center_r, face_center_y + 32.0),
        )
        Line(
            (sign * center_r, face_center_y + 32.0),
            (sign * center_r, driver_rear_y),
        )
        Bezier(
            (sign * center_r, driver_rear_y),
            (sign * center_r, driver_rear_y + 9.0),
            (sign * tube_side_x, D.upper_tower_y - 9.0),
            (sign * tube_side_x, D.upper_tower_y),
        )

    section_plane = Plane(
        origin=(
            sign * D.horn_spoke_root_r,
            face_center_y,
            D.horn_center_z,
        ),
        x_dir=(0.0, 1.0, 0.0),
        z_dir=(1.0, 0.0, 0.0),
    )
    with BuildSketch(section_plane) as section:
        Circle(spoke_r)
    assert section.sketch.area > 0.0, "Side-spoke section area must be positive"
    raw_spoke = sweep(section.sketch, path.line, is_frenet=True).clean().fix()
    plate_front_y = D.horn_mount_face_y - D.horn_face_t
    rear_keep = Pos(0.0, plate_front_y + 200.0, D.horn_center_z) * Box(
        400.0, 400.0, 400.0
    )
    return _require_single_solid(
        (raw_spoke & rear_keep).clean().fix(),
        feature="smooth side driver spoke",
    )


def _bottom_driver_spoke() -> Part:
    """Bottom rail leaving the plate downward and merging into the tube front."""
    spoke_r = D.horn_spoke_d / 2.0
    face_center_y = D.horn_mount_face_y - spoke_r
    center_r = D.de250_envelope_r + D.horn_spoke_gap + spoke_r
    turn_r = center_r + D.horn_spoke_turn_extra_r
    bottom_z = D.horn_center_z - center_r
    tube_front_y = D.upper_tower_y - D.tower_outer_ry
    tube_wall_center_y = (
        tube_front_y + D.structural_tower_wall_t / 2.0
    )

    path_plane = Plane(
        origin=(0.0, 0.0, 0.0),
        x_dir=(0.0, 1.0, 0.0),
        z_dir=(1.0, 0.0, 0.0),
    )
    with BuildLine(path_plane) as path:
        Line(
            (face_center_y, D.horn_center_z - D.horn_spoke_root_r),
            (face_center_y, bottom_z),
        )
        Bezier(
            (face_center_y, bottom_z),
            (face_center_y, D.horn_center_z - center_r - 3.0),
            (face_center_y + 2.0, D.horn_center_z - turn_r),
            (face_center_y + 5.0, D.horn_center_z - turn_r),
        )
        Bezier(
            (face_center_y + 5.0, D.horn_center_z - turn_r),
            (face_center_y + 18.0, D.horn_center_z - turn_r),
            (face_center_y + 20.0, bottom_z),
            (face_center_y + 32.0, bottom_z),
        )
        Line(
            (face_center_y + 32.0, bottom_z),
            (tube_wall_center_y, bottom_z),
        )

    section_plane = Plane(
        origin=(
            D.horn_center_x,
            face_center_y,
            D.horn_center_z - D.horn_spoke_root_r,
        ),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, 0.0, 1.0),
    )
    with BuildSketch(section_plane) as section:
        Circle(spoke_r)
    assert section.sketch.area > 0.0, "Bottom-spoke section area must be positive"
    raw_spoke = sweep(section.sketch, path.line, is_frenet=True).clean().fix()
    plate_front_y = D.horn_mount_face_y - D.horn_face_t
    rear_keep = Pos(0.0, plate_front_y + 200.0, D.horn_center_z) * Box(
        400.0, 400.0, 400.0
    )
    return _require_single_solid(
        (raw_spoke & rear_keep).clean().fix(),
        feature="smooth bottom driver spoke",
    )


def _driver_mount_plate_and_spokes() -> Part:
    """Two-hole DE250 plate with three separate structural tube connections."""
    face_center_y = D.horn_mount_face_y - D.horn_face_t / 2.0
    plate = _oriented_cylinder(
        diameter=2.0 * D.horn_mount_ring_r,
        depth=D.horn_face_t,
        axis="y",
        center=(D.horn_center_x, face_center_y, D.horn_center_z),
    )
    return _fuse_connected(
        [
            plate,
            _side_driver_spoke(-1.0),
            _side_driver_spoke(1.0),
            _bottom_driver_spoke(),
        ],
        feature="two-hole driver plate and three-spoke support",
    )


def _driver_mount_plate_cutouts() -> Part:
    """Acoustic opening and only the horizontal DE250 two-hole pattern."""
    center_y = D.horn_mount_face_y - D.horn_face_t / 2.0
    with BuildPart() as cutouts:
        add(
            _oriented_cylinder(
                diameter=D.horn_acoustic_hole_d,
                depth=D.horn_face_t + 4.0,
                axis="y",
                center=(D.horn_center_x, center_y, D.horn_center_z),
            )
        )
        for x in (-P.horn_bolt_2_bcd / 2.0, P.horn_bolt_2_bcd / 2.0):
            add(
                _oriented_cylinder(
                    diameter=P.horn_bolt_clearance_d,
                    depth=D.horn_face_t + 4.0,
                    axis="y",
                    center=(D.horn_center_x + x, center_y, D.horn_center_z),
                )
            )
    return cutouts.part


def build_tower(outlet_z: float) -> tuple[Part, Part, Part]:
    airway, outer = _path_solids(outlet_z)
    tower_clip_h = outlet_z - D.internal_tower_bottom_z + 30.0
    tower_clip = Pos(
        0.0,
        D.center_y,
        D.internal_tower_bottom_z + tower_clip_h / 2.0,
    ) * Box(
        300.0,
        300.0,
        tower_clip_h,
    )
    tower_outer = _primary_shape(outer & tower_clip)
    driver_support = _driver_mount_plate_and_spokes()
    tower = _fuse_connected(
        [tower_outer, _internal_tower_mount_saddle(), driver_support],
        feature="weight-bearing circular tower and three-spoke DE250 support",
    )
    tower -= airway
    tower -= _driver_mount_plate_cutouts()
    for hole in _internal_tower_mount_clearance_holes():
        tower -= hole
    return (
        _require_single_solid(
            tower.clean().fix(), feature="finished weight-bearing circular tower"
        ),
        airway,
        outer,
    )


def _flare_equivalent_length(
    *, area0: float, rx0: float, ry0: float, rx1: float, ry1: float, length: float
) -> float:
    total = 0.0
    steps = 4000
    for index in range(steps):
        t = (index + 0.5) / steps
        blend = t * t * (3.0 - 2.0 * t)
        rx = rx0 + (rx1 - rx0) * blend
        ry = ry0 + (ry1 - ry0) * blend
        total += area0 / (math.pi * rx * ry)
    return length * total / steps


def _upper_tower_shift_extra_length() -> float:
    """Extra centerline length in the optional external tower offset."""
    span = D.upper_tower_shift_end_z - D.upper_tower_shift_start_z
    offset = D.upper_tower_y - D.port_y
    if span <= 0.0 or offset < 0.0:
        raise ValueError("External tower shift dimensions are invalid")
    if offset < 1e-9:
        return 0.0
    total = 0.0
    steps = 4000
    previous_y = D.port_y
    previous_z = D.upper_tower_shift_start_z
    for index in range(1, steps + 1):
        t = index / steps
        one_minus = 1.0 - t
        # Cubic Bezier with vertical tangents at both ends. The 0.32 control
        # spacing matches the actual path constructed in _swept_ellipse().
        y = (
            one_minus**3 * D.port_y
            + 3.0 * one_minus**2 * t * D.port_y
            + 3.0 * one_minus * t**2 * D.upper_tower_y
            + t**3 * D.upper_tower_y
        )
        z = (
            one_minus**3 * D.upper_tower_shift_start_z
            + 3.0
            * one_minus**2
            * t
            * (D.upper_tower_shift_start_z + span * 0.32)
            + 3.0
            * one_minus
            * t**2
            * (D.upper_tower_shift_end_z - span * 0.32)
            + t**3 * D.upper_tower_shift_end_z
        )
        total += math.hypot(y - previous_y, z - previous_z)
        previous_y = y
        previous_z = z
    return total - span


def _port_length_solution(net_box_l: float) -> dict[str, float]:
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    required_effective = 1000.0 * (
        D.speed_of_sound_m_s**2
        * area_m2
        / ((2.0 * math.pi * D.target_tuning_hz) ** 2 * volume_m3)
    )
    inlet_equiv = _flare_equivalent_length(
        area0=D.port_area_mm2,
        rx0=D.inlet_mouth_width / 2.0,
        ry0=D.inlet_mouth_height / 2.0,
        rx1=D.inlet_flat_width / 2.0,
        ry1=D.inlet_flat_height / 2.0,
        length=D.inlet_flare_l,
    )
    compound_physical = _compound_route_length()
    outlet_equiv = _flare_equivalent_length(
        area0=D.port_area_mm2,
        rx0=D.port_rx,
        ry0=D.port_rz,
        rx1=D.outlet_mouth_width / 2.0,
        ry1=D.outlet_mouth_depth / 2.0,
        length=D.outlet_flare_l,
    )
    inlet_end = D.inlet_end_correction_factor * math.sqrt(
        (D.inlet_mouth_width / 2.0) * (D.inlet_mouth_height / 2.0)
    )
    outlet_end = D.outlet_end_correction_factor * math.sqrt(
        (D.outlet_mouth_width / 2.0) * (D.outlet_mouth_depth / 2.0)
    )
    outlet_z = D.fixed_outlet_top_z
    outlet_throat_z = outlet_z - D.outlet_flare_l
    central_vertical = outlet_throat_z - D.asymmetric_vertical_return_top_z
    central_tower_path = _tower_centerline_length(
        D.asymmetric_vertical_return_top_z,
        outlet_throat_z,
    )
    if outlet_throat_z <= D.height / 2.0 + 10.0:
        raise ValueError("Fixed low outlet does not leave a usable external tower")
    physical = (
        D.inlet_flare_l
        + compound_physical
        + central_tower_path
        + D.outlet_flare_l
    )
    area_corrected = (
        inlet_equiv
        + compound_physical
        + central_tower_path
        + outlet_equiv
    )
    effective_check = area_corrected + inlet_end + outlet_end
    tuning_check = D.speed_of_sound_m_s / (2.0 * math.pi) * math.sqrt(
        area_m2 / (volume_m3 * effective_check / 1000.0)
    )
    return {
        "required_effective_length_mm": required_effective,
        "effective_length_shortfall_vs_exact_39_hz_mm": (
            required_effective - effective_check
        ),
        "physical_centerline_length_mm": physical,
        "inlet_flare_physical_length_mm": D.inlet_flare_l,
        "inlet_flare_area_equivalent_length_mm": inlet_equiv,
        "compound_route_physical_length_mm": compound_physical,
        "compound_route_lower_sweep_length_mm": (
            _compound_route_base_lengths()[0]
        ),
        "compound_route_lower_sweep_radius_mm": D.lower_sweep_radius,
        "compound_route_lower_sweep_turn_deg": math.degrees(
            D.lower_sweep_turn_rad
        ),
        "compound_route_bend_base_length_mm": (
            _compound_route_base_lengths()[1]
        ),
        "compound_route_upper_drift_length_mm": (
            _compound_route_base_lengths()[2]
        ),
        "upper_drift_control_fraction": list(D.upper_drift_control_fraction),
        "upper_drift_end_z_mm": D.asymmetric_vertical_return_top_z,
        "central_vertical_length_mm": central_vertical,
        "central_tower_path_length_mm": central_tower_path,
        "vertical_constant_area_length_mm": central_tower_path,
        "vertical_rise_mm": outlet_throat_z - D.bend_center_z,
        "outlet_flare_physical_length_mm": D.outlet_flare_l,
        "outlet_flare_area_equivalent_length_mm": outlet_equiv,
        "inlet_end_correction_mm": inlet_end,
        "outlet_end_correction_mm": outlet_end,
        "area_corrected_physical_length_mm": area_corrected,
        "effective_length_mm": effective_check,
        "outlet_throat_z_mm": outlet_throat_z,
        "outlet_z_mm": outlet_z,
        "calculated_tuning_hz": tuning_check,
    }


def _volume_accounting(
    printed_intrusions: Any,
    port_outer: Part,
    woofer: Any,
    gx16: Any,
) -> dict[str, float | str]:
    domain = _acoustic_domain()
    rectangular_domain = _rectangular_cavity()
    items: list[tuple[str, Any]] = []
    for category, shape in (
        ("printed", printed_intrusions),
        ("woofer", woofer),
        ("port", port_outer),
    ):
        for solid in shape.solids():
            if not _bounding_boxes_overlap(solid, domain):
                continue
            clipped = solid & domain
            if clipped is not None:
                items.extend((category, part) for part in clipped.solids())

    raw_by_category = {
        category: sum(solid.volume for item_category, solid in items if item_category == category)
        for category in ("printed", "woofer", "port")
    }
    pair_overlaps: list[tuple[int, int, float]] = []
    pair_edges: set[tuple[int, int]] = set()
    for left_index in range(len(items)):
        for right_index in range(left_index + 1, len(items)):
            # Woofer-to-port and woofer-to-brace clearances are enforced by the
            # dedicated geometry checks below. Avoid repeating expensive
            # booleans against the detailed supplied woofer STEP here.
            if "woofer" in (items[left_index][0], items[right_index][0]):
                continue
            if not _bounding_boxes_overlap(
                items[left_index][1],
                items[right_index][1],
            ):
                continue
            overlap = _intersection_volume(
                items[left_index][1],
                items[right_index][1],
            )
            if overlap > 0.001:
                pair_overlaps.append((left_index, right_index, overlap))
                pair_edges.add((left_index, right_index))

    # Pairwise inclusion-exclusion is exact for this layout. Guard that
    # assumption so a future feature cannot silently create a triple overlap.
    for first in range(len(items)):
        for second in range(first + 1, len(items)):
            if (first, second) not in pair_edges:
                continue
            for third in range(second + 1, len(items)):
                if (first, third) in pair_edges and (second, third) in pair_edges:
                    triple = _intersection_volume(
                        items[first][1] & items[second][1],
                        items[third][1],
                    )
                    if triple > 0.001:
                        raise ValueError(
                            "Volume accounting found an unsupported triple overlap "
                            f"of {triple:.6f} mm3"
                        )

    unique_by_category = dict(raw_by_category)
    cross_category_overlap = 0.0
    for left_index, right_index, overlap in pair_overlaps:
        left_category = items[left_index][0]
        right_category = items[right_index][0]
        if left_category == right_category:
            unique_by_category[left_category] -= overlap
        else:
            cross_category_overlap += overlap

    gx_bb = gx16.bounding_box()
    rectangular_bb = rectangular_domain.bounding_box()
    gx_dx = max(0.0, min(gx_bb.max.X, rectangular_bb.max.X) - max(gx_bb.min.X, rectangular_bb.min.X))
    gx_dy = max(0.0, min(gx_bb.max.Y, rectangular_bb.max.Y) - max(gx_bb.min.Y, rectangular_bb.min.Y))
    gx_dz = max(0.0, min(gx_bb.max.Z, rectangular_bb.max.Z) - max(gx_bb.min.Z, rectangular_bb.min.Z))
    gx_conservative_displacement = gx_dx * gx_dy * gx_dz

    total_raw = sum(raw_by_category.values()) + gx_conservative_displacement
    total_pair_overlap = sum(overlap for _, _, overlap in pair_overlaps)
    final_air_volume = domain.volume - (total_raw - total_pair_overlap)
    return {
        "method": (
            "Exact OpenCascade intersection of the printed cavity features, supplied "
            "woofer solids, and complete in-box port envelope with the acoustic domain, "
            "followed by guarded pairwise inclusion-exclusion. The detailed GX16 STEP "
            "uses its conservative in-cavity bounding-box intersection because its "
            "surface model makes an exact boolean disproportionately slow. Binding posts "
            "and amplifier electronics are deferred."
        ),
        "gross_modeled_cavity_with_black_hole_relief_l": domain.volume / 1_000_000.0,
        "printed_non_port_intrusions_braces_blisters_and_platforms_l": (
            unique_by_category["printed"] / 1_000_000.0
        ),
        "e150he_44_step_displacement_l": unique_by_category["woofer"] / 1_000_000.0,
        "gx16_conservative_bbox_displacement_upper_bound_l": (
            gx_conservative_displacement / 1_000_000.0
        ),
        "internal_port_envelope_including_air_l": unique_by_category["port"]
        / 1_000_000.0,
        "cross_category_overlap_correction_l": cross_category_overlap / 1_000_000.0,
        "pair_overlap_count": len(pair_overlaps),
        "triple_overlap_count": 0,
        "final_modeled_net_box_volume_l": final_air_volume / 1_000_000.0,
    }


def _modeled_state(
    *, net_box_l: float, effective_length_mm: float, frequency_hz: float, power_w: float
) -> dict[str, float]:
    """Evaluate the same lumped model as the shared response helper at 39 Hz."""
    e150 = common.E150
    rho = D.air_density_kg_m3
    c = D.speed_of_sound_m_s
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    acoustic_mass = rho * (effective_length_mm / 1000.0) / area_m2
    calculated_tuning_hz = c / (2.0 * math.pi) * math.sqrt(
        area_m2 / (volume_m3 * effective_length_mm / 1000.0)
    )
    port_resistance = (
        2.0 * math.pi * calculated_tuning_hz * acoustic_mass / 10.0
    )
    rms = 1.0 / (
        2.0
        * math.pi
        * e150["fs_hz"]
        * e150["cms_m_n"]
        * e150["qms"]
    )
    omega = 2.0 * math.pi * frequency_hz
    z_port = port_resistance + 1j * omega * acoustic_mass
    box_compliance = volume_m3 / (rho * c * c)
    z_box = 1.0 / (1j * omega * box_compliance + 1.0 / z_port)
    z_mechanical = (
        rms
        + 1j * omega * e150["mms_kg"]
        + 1.0 / (1j * omega * e150["cms_m_n"])
        + e150["sd_m2"] ** 2 * z_box
    )
    z_electrical = e150["re_ohm"] + 1j * omega * e150["le_h"]
    voltage = math.sqrt(power_w * e150["re_ohm"])
    current = voltage / (z_electrical + e150["bl_tm"] ** 2 / z_mechanical)
    cone_velocity = e150["bl_tm"] * current / z_mechanical
    box_pressure = z_box * e150["sd_m2"] * cone_velocity
    port_volume_velocity = box_pressure / z_port
    port_velocity = abs(port_volume_velocity / area_m2)
    excursion = abs(cone_velocity / omega) * 1000.0
    radiated_volume_velocity = port_volume_velocity - e150["sd_m2"] * cone_velocity
    far_pressure = abs(
        1j * omega * rho * radiated_volume_velocity / (2.0 * math.pi)
    )
    spl = 20.0 * math.log10(max(far_pressure, 1e-12) / 20e-6)
    return {
        "ideal_half_space_spl_db_1m": spl,
        "port_velocity_m_s": port_velocity,
        "cone_excursion_mm": excursion,
    }


def _vented_response(
    *, net_box_l: float, effective_length_mm: float
) -> dict[str, Any]:
    powers: dict[str, Any] = {}
    for power in (25.0, 50.0, 100.0, 200.0):
        sweep_rows = [
            {
                "frequency_hz": 15.0 + index * 0.1,
                **_modeled_state(
                    net_box_l=net_box_l,
                    effective_length_mm=effective_length_mm,
                    frequency_hz=15.0 + index * 0.1,
                    power_w=power,
                ),
            }
            for index in range(1051)
        ]
        peak_port = max(sweep_rows, key=lambda row: row["port_velocity_m_s"])
        peak_excursion = max(sweep_rows, key=lambda row: row["cone_excursion_mm"])
        samples = [
            {
                "frequency_hz": frequency,
                **_modeled_state(
                    net_box_l=net_box_l,
                    effective_length_mm=effective_length_mm,
                    frequency_hz=frequency,
                    power_w=power,
                ),
            }
            for frequency in (20, 30, 35, 39, 40, 43, 50, 60, 80)
        ]
        powers[f"{int(power)}_w"] = {
            "input_voltage_v_rms_series_coils": math.sqrt(
                power * common.E150["re_ohm"]
            ),
            "peak_port_velocity": peak_port,
            "peak_cone_excursion_15_to_120_hz": peak_excursion,
            "samples": samples,
        }

    reference = [
        {
            "frequency_hz": 15.0 + index * 0.1,
            **_modeled_state(
                net_box_l=net_box_l,
                effective_length_mm=effective_length_mm,
                frequency_hz=15.0 + index * 0.1,
                power_w=1.0,
            ),
        }
        for index in range(1051)
    ]
    passband_rows = [row for row in reference if 70.0 <= row["frequency_hz"] <= 100.0]
    passband_db = sum(
        row["ideal_half_space_spl_db_1m"] for row in passband_rows
    ) / len(passband_rows)
    threshold = passband_db - 3.0
    f3 = next(
        row["frequency_hz"]
        for row in reference
        if row["ideal_half_space_spl_db_1m"] >= threshold
    )
    return {
        "model": (
            "Small-signal electro-mechano-acoustic lumped model using Dayton's "
            "series-coil T/S parameters, the locally modeled net volume and airway "
            "area, and port loss Q=10."
        ),
        "port_loss_q_assumption": 10.0,
        "predicted_f3_hz": f3,
        "passband_reference_70_100_hz_db": passband_db,
        "power_cases": powers,
        "recommended_protection": (
            "Use a 4th-order high-pass at 28-30 Hz and dynamic bass limiting."
        ),
    }


def _dsp_summary(
    response: dict[str, Any], *, net_box_l: float, effective_length_mm: float
) -> dict[str, Any]:
    samples = response["power_cases"]["25_w"]["samples"]
    spl = {row["frequency_hz"]: row["ideal_half_space_spl_db_1m"] for row in samples}
    passband = sum(spl[f] for f in (60, 80)) / 2.0
    state_39_25 = _modeled_state(
        net_box_l=net_box_l,
        effective_length_mm=effective_length_mm,
        frequency_hz=39.0,
        power_w=25.0,
    )
    attenuation_39 = passband - state_39_25["ideal_half_space_spl_db_1m"]
    boost = max(0.0, attenuation_39)
    boosted_power_factor = 10.0 ** (boost / 10.0)
    boosted_amplitude_factor = 10.0 ** (boost / 20.0)
    boosted_cases: dict[str, Any] = {}
    for power in (25, 50):
        row_39 = _modeled_state(
            net_box_l=net_box_l,
            effective_length_mm=effective_length_mm,
            frequency_hz=39.0,
            power_w=float(power),
        )
        boosted_velocity = row_39["port_velocity_m_s"] * boosted_amplitude_factor
        boosted_cases[f"{power}_w_broadband_reference"] = {
            "effective_amplifier_power_at_39_hz_w": power * boosted_power_factor,
            "flattened_39_hz_spl_db_1m_ideal_half_space": row_39[
                "ideal_half_space_spl_db_1m"
            ]
            + boost,
            "port_velocity_at_39_hz_m_s": boosted_velocity,
            "port_mach_at_39_hz": boosted_velocity / D.speed_of_sound_m_s,
            "cone_excursion_at_39_hz_mm": row_39["cone_excursion_mm"]
            * boosted_amplitude_factor,
        }
    return {
        "design_goal": "No audible 39-40 Hz attenuation at moderate playback with DSP",
        "natural_39_hz_attenuation_vs_60_80_hz_db": attenuation_39,
        "nominal_low_shelf_or_peak_boost_db": round(boost, 2),
        "nominal_center_frequency_hz": 39.0,
        "suggested_q": 0.7,
        "power_multiplier_at_full_boost": boosted_power_factor,
        "dsp_applied_cases": boosted_cases,
        "moderate_volume_definition": (
            "Use the bass limiter so boosted low-frequency demand remains near the "
            "25-50 W acoustic cases; do not treat the TPA3255 voltage capability as "
            "permission to run 200 W of continuous boosted bass."
        ),
        "required_protection": "4th-order high-pass at 28-30 Hz plus dynamic bass limiting",
        "qualification": (
            "The DSP case is evaluated at 39 Hz below the natural vent tuning. Final "
            "audibility depends on room gain, placement, leakage, and the measured unit."
        ),
    }


def _cutaway(
    base: Part,
    internal_tube: Part,
    tower: Part,
    woofer: Any,
    gx16: Any,
    horn: Any,
    de250: Any,
) -> Compound:
    # Size the half-space from every physical component.  Only the enclosure,
    # woofer, and horn are sectioned.  The complete asymmetric duct, tower,
    # GX16, and DE250 stay visible; cutting every component at x=0 previously
    # discarded most of the new right-side route and made the viewer misleading.
    physical_parts = (base, internal_tube, tower, woofer, gx16, horn, de250)
    boxes = [part.bounding_box() for part in physical_parts]
    margin = 10.0
    clip_min_x = min(bb.min.X for bb in boxes) - margin
    clip_max_x = 0.0
    clip_min_y = min(bb.min.Y for bb in boxes) - margin
    clip_max_y = max(bb.max.Y for bb in boxes) + margin
    clip_min_z = min(bb.min.Z for bb in boxes) - margin
    clip_max_z = max(bb.max.Z for bb in boxes) + margin
    clip = Pos(
        (clip_min_x + clip_max_x) / 2.0,
        (clip_min_y + clip_max_y) / 2.0,
        (clip_min_z + clip_max_z) / 2.0,
    ) * Box(
        clip_max_x - clip_min_x,
        clip_max_y - clip_min_y,
        clip_max_z - clip_min_z,
    )
    return Compound(
        children=[
            *_fresh_solids(base & clip),
            *_fresh_solids(internal_tube),
            *_fresh_solids(tower),
            *_fresh_solids(woofer & clip),
            *_fresh_solids(gx16),
            *_fresh_solids(horn & clip),
            *_fresh_solids(de250),
        ]
    )


def generate_authoritative_base_input(
    output_directory: Path,
) -> dict[str, Any]:
    """Publish only the full-detail enclosure input consumed by Variant R.

    This is the authoritative producer boundary for downstream enclosure
    variants.  It intentionally skips the single-oval-port assembly previews
    and component exports, none of which contribute material to this base.
    """

    output_directory.mkdir(parents=True, exist_ok=True)
    _, provisional_brace_clearance = _path_solids(
        185.0,
        outer_extra=D.brace_port_clearance,
    )
    _, provisional_install_clearance = _path_solids(
        185.0,
        outer_extra=D.tube_install_clearance,
    )
    base = build_base(
        provisional_brace_clearance,
        provisional_install_clearance,
    )
    path = output_directory / "sand_cube_190x210_single_oval_port_base.step"
    export_step(base, path, unit=Unit.MM, write_pcurves=True)
    imported = import_step(path)
    result = {
        "path": str(path),
        "source_solid_count": len(base.solids()),
        "imported_solid_count": len(imported.solids()),
        "all_source_solids_valid": all(
            solid.is_valid for solid in base.solids()
        ),
        "all_imported_solids_valid": all(
            solid.is_valid for solid in imported.solids()
        ),
    }
    if result != {
        "path": str(path),
        "source_solid_count": 1,
        "imported_solid_count": 1,
        "all_source_solids_valid": True,
        "all_imported_solids_valid": True,
    }:
        raise ValueError(
            f"Authoritative Variant R base STEP round trip failed: {result}"
        )
    return result


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    provisional_airway, provisional_outer = _path_solids(185.0)
    _, provisional_brace_clearance = _path_solids(
        185.0,
        outer_extra=D.brace_port_clearance,
    )
    _, provisional_install_clearance = _path_solids(
        185.0,
        outer_extra=D.tube_install_clearance,
    )
    rear_wall_install_clearance = REAR_INNER_Y - (
        D.port_y + D.outer_rz + D.tube_install_clearance
    )
    if rear_wall_install_clearance < 0.25:
        raise ValueError(
            "Internal port installation envelope enters the rear 2-3-2 wall: "
            f"{rear_wall_install_clearance:.6f} mm clearance"
        )
    structural_tower_rear_clearance = REAR_INNER_Y - (
        D.upper_tower_y + D.tower_outer_ry
    )
    structural_tower_install_clearance = (
        structural_tower_rear_clearance - D.tube_install_clearance
    )
    if structural_tower_install_clearance < 0.25:
        raise ValueError(
            "Weight-bearing tower installation envelope enters the rear 2-3-2 "
            f"wall: {structural_tower_install_clearance:.6f} mm clearance"
        )
    if abs(D.upper_tower_y - D.port_y) > 0.001:
        raise ValueError(
            "External tower must be a straight continuation of the internal port: "
            f"{D.upper_tower_y - D.port_y:.6f} mm center offset"
        )
    front_buttresses = list(_front_brace_blends().solids())
    front_buttress_volumes = [solid.volume for solid in front_buttresses]
    front_buttress_y_depths = [solid.bounding_box().size.Y for solid in front_buttresses]
    if len(front_buttresses) != 4:
        raise ValueError("Woofer collar must have exactly four structural buttresses")
    if max(front_buttress_volumes) - min(front_buttress_volumes) > 0.001:
        raise ValueError("Woofer-collar buttresses are not equal volume")
    if max(front_buttress_y_depths) - min(front_buttress_y_depths) > 0.001:
        raise ValueError("Woofer-collar buttresses are not equal axial depth")
    nominal_sand_void = _sand_void()
    protected_outer_skin = (
        _outer_envelope() - _inset_outer_envelope(D.outer_skin_t)
    ).clean().fix()
    floor_bottom_z = -D.height / 2.0
    floor_top_z = floor_bottom_z + D.wall_stack_t
    below_floor = Pos(
        0.0,
        D.center_y,
        (floor_bottom_z + floor_top_z) / 2.0,
    ) * Box(
        D.width + 2.0,
        D.depth + 2.0,
        floor_top_z - floor_bottom_z,
    )
    sand_void_outer_skin_overlap = _bounded_intersection_volume(
        nominal_sand_void,
        protected_outer_skin,
    )
    sand_void_floor_overlap = _bounded_intersection_volume(
        nominal_sand_void,
        below_floor,
    )
    unclipped_install_clearance_floor_penetration = max(
        0.0,
        floor_top_z - provisional_install_clearance.bounding_box().min.Z,
    )
    outer_tube_floor_tangency_error = (
        provisional_outer.bounding_box().min.Z - floor_top_z
    )
    actual_port_channel_depth = 0.0
    tube_channel_remaining_floor = D.wall_stack_t - actual_port_channel_depth
    bottom_insert_remaining_floor = (
        D.wall_stack_t - D.bottom_tube_mount_insert_depth
    )
    if sand_void_outer_skin_overlap > 0.001:
        raise ValueError(
            "Rounded sand void breaks through the protected outer skin by "
            f"{sand_void_outer_skin_overlap:.6f} mm3"
        )
    if sand_void_floor_overlap > 0.001:
        raise ValueError(
            "Solid floor contains unintended sand void volume: "
            f"{sand_void_floor_overlap:.6f} mm3"
        )
    if abs(outer_tube_floor_tangency_error) > 0.001:
        raise ValueError(
            "Port shell is not tangent to the solid inner floor: "
            f"{outer_tube_floor_tangency_error:.6f} mm error"
        )
    if tube_channel_remaining_floor < 2.0:
        raise ValueError(
            "Port interface leaves less than 2 mm of solid floor: "
            f"{tube_channel_remaining_floor:.6f} mm"
        )
    if bottom_insert_remaining_floor < 2.0:
        raise ValueError(
            "Bottom insert pockets leave less than 2 mm of exterior floor: "
            f"{bottom_insert_remaining_floor:.6f} mm"
        )
    wall_stack_checks = {
        "method": (
            "concentric all-edge filleted envelopes clipped above the solid floor"
        ),
        "outer_edge_radius_mm": D.edge_fillet_r,
        "inside_outer_skin_radius_mm": D.edge_fillet_r - D.outer_skin_t,
        "inside_sand_gap_radius_mm": (
            D.edge_fillet_r - D.outer_skin_t - D.sand_gap_t
        ),
        "acoustic_face_radius_mm": D.edge_fillet_r - D.wall_stack_t,
        "nominal_outer_sand_inner_mm": [
            D.outer_skin_t,
            D.sand_gap_t,
            D.inner_skin_t,
        ],
        "solid_floor_nominal_thickness_mm": D.wall_stack_t,
        "bottom_sand_void_present": False,
        "sand_void_min_z_mm": nominal_sand_void.bounding_box().min.Z,
        "sand_void_overlap_with_protected_outer_skin_mm3": (
            sand_void_outer_skin_overlap
        ),
        "sand_void_overlap_below_floor_top_mm3": sand_void_floor_overlap,
        "port_channel_cut_into_floor": False,
        "actual_port_channel_depth_mm": actual_port_channel_depth,
        "unclipped_installation_envelope_penetration_below_floor_top_mm": (
            unclipped_install_clearance_floor_penetration
        ),
        "outer_tube_floor_tangency_error_mm": outer_tube_floor_tangency_error,
        "remaining_solid_floor_under_port_mm": tube_channel_remaining_floor,
        "bottom_insert_pocket_depth_mm": D.bottom_tube_mount_insert_depth,
        "remaining_floor_under_bottom_insert_pocket_mm": (
            bottom_insert_remaining_floor
        ),
    }
    base = build_base(
        provisional_brace_clearance,
        provisional_install_clearance,
    )
    _, provisional_tube_displacement = build_internal_tube(
        provisional_airway,
        provisional_outer,
    )
    provisional_upper_displacement = _internal_tower_mount_displacement(
        provisional_outer
    )
    provisional_port_displacement = Compound(
        children=[
            *_fresh_solids(provisional_tube_displacement),
            *_fresh_solids(provisional_upper_displacement),
        ]
    )
    # The driver and restored black-hole feature are truly centered. The low,
    # wide inlet provides the required motor clearance instead of shifting them.
    woofer = Pos(0.0, 0.0, BLACK_HOLE_CENTER_Z) * _confirmed_woofer(P)
    gx16_raw, gx16_data = _placed_gx16(P)
    gx16 = _rear_shifted(gx16_raw)
    gx16_data["hex_pocket_center_y_mm"] += REAR_EXTENSION_Y
    gx16_data["body_y_offset_mm"] += REAR_EXTENSION_Y
    gx16_data["rear_face_y_mm"] += REAR_EXTENSION_Y
    gx16_data["placed_bbox_min_mm"][1] += REAR_EXTENSION_Y
    gx16_data["placed_bbox_max_mm"][1] += REAR_EXTENSION_Y
    gx16_data["rear_extension_shift_mm"] = REAR_EXTENSION_Y
    woofer_bb = woofer.bounding_box()
    woofer_outer_radius = max(
        abs(woofer_bb.min.X),
        abs(woofer_bb.max.X),
        abs(woofer_bb.min.Z),
        abs(woofer_bb.max.Z),
    )
    cavity_half = D.width / 2.0 - D.wall_stack_t
    rib_heights = (
        RESTORED_FEATURE_VARIANT.window_brace_height,
        RESTORED_FEATURE_VARIANT.vertical_brace_height,
        RESTORED_FEATURE_VARIANT.horizontal_brace_height,
    )
    if max(rib_heights) - min(rib_heights) > 0.001:
        raise ValueError(
            "Window and longitudinal rib inward faces are not flush: "
            f"{rib_heights} mm"
        )
    window_opening_half = cavity_half - RESTORED_FEATURE_VARIANT.window_brace_height
    longitudinal_inner_radius = (
        cavity_half - RESTORED_FEATURE_VARIANT.vertical_brace_height
    )
    brace_to_woofer_clearance = min(
        window_opening_half - woofer_outer_radius,
        longitudinal_inner_radius - woofer_outer_radius,
    )
    if brace_to_woofer_clearance <= 0.0:
        raise ValueError(
            "Restored internal bracing does not clear the supplied woofer envelope"
        )
    printed_intrusions = _printed_non_port_cavity_intrusions(
        provisional_brace_clearance,
        provisional_install_clearance,
    )
    volume = _volume_accounting(
        printed_intrusions,
        provisional_port_displacement,
        woofer,
        gx16,
    )
    lengths = _port_length_solution(float(volume["final_modeled_net_box_volume_l"]))
    tower, airway, port_outer = build_tower(lengths["outlet_z_mm"])
    internal_tube, tube_displacement = build_internal_tube(airway, port_outer)
    upper_displacement = _internal_tower_mount_displacement(port_outer)
    port_displacement = Compound(
        children=[
            *_fresh_solids(tube_displacement),
            *_fresh_solids(upper_displacement),
        ]
    )
    horn, de250, horn_data = _placed_face_matched_horn_and_de250()
    enclosure_front_y = D.center_y - D.depth / 2.0
    enclosure_roof_z = D.height / 2.0
    driver_seat_y = enclosure_front_y + BLACK_HOLE_SEAT_DEPTH
    equivalent_port_d = 2.0 * math.sqrt(D.port_area_mm2 / math.pi)
    inlet_clearance_from_driver_seat = D.inlet_mouth_y - driver_seat_y
    run_dx, run_dy = D.inlet_run_direction_xy
    left_acoustic_wall_x = -D.width / 2.0 + D.wall_stack_t
    inlet_lateral_wall_clearance = (
        D.inlet_x
        - (D.inlet_mouth_width / 2.0 + D.port_wall_t + D.tube_install_clearance)
        - left_acoustic_wall_x
    )
    inlet_axial_front_clearance = (
        D.inlet_mouth_y - driver_seat_y
    ) / run_dy
    inlet_minimum_axial_clearance = inlet_axial_front_clearance
    if inlet_lateral_wall_clearance < 0.50:
        raise ValueError(
            "Front-facing port flare leaves less than 0.5 mm lateral install "
            f"clearance: {inlet_lateral_wall_clearance:.3f} mm"
        )
    if inlet_clearance_from_driver_seat < equivalent_port_d:
        raise ValueError(
            "Port inlet needs at least one equivalent diameter behind the driver "
            f"seat: {inlet_clearance_from_driver_seat:.3f} mm available versus "
            f"{equivalent_port_d:.3f} mm required"
        )
    if inlet_minimum_axial_clearance < equivalent_port_d:
        raise ValueError(
            "Front-facing port inlet needs one equivalent diameter along its outward "
            f"normal: {inlet_minimum_axial_clearance:.3f} mm available versus "
            f"{equivalent_port_d:.3f} mm required"
        )
    horn_bbox = horn.bounding_box()
    horn_forward_projection = enclosure_front_y - horn_bbox.min.Y
    horn_forward_position_error = (
        horn_forward_projection - D.horn_forward_projection_mm
    )
    horn_bottom_gap = horn_bbox.min.Z - enclosure_roof_z
    if abs(horn_forward_position_error) > 0.01:
        raise ValueError(
            "Horn forward projection missed the provisional structural clearance: "
            f"{horn_forward_position_error:.6f} mm error"
        )
    if abs(horn_bottom_gap - 5.0) > 0.01:
        raise ValueError(
            "Horn bottom is not 5 mm above the enclosure roof: "
            f"{horn_bottom_gap:.6f} mm actual gap"
        )
    acoustic_mouth_plane_y = (
        D.horn_mount_face_y
        - float(horn_data["profile"]["axial_length_mm_exact"])
    )
    horn_data["alignment_to_enclosure"] = {
        "enclosure_front_y_mm": enclosure_front_y,
        "horn_forwardmost_rolled_surface_y_mm": horn_bbox.min.Y,
        "horn_forward_projection_mm": horn_forward_projection,
        "target_forward_projection_mm": D.horn_forward_projection_mm,
        "forward_position_error_mm": horn_forward_position_error,
        "front_flush_constraint_released": True,
        "acoustic_mouth_plane_y_mm": acoustic_mouth_plane_y,
        "acoustic_mouth_plane_setback_from_front_mm": (
            acoustic_mouth_plane_y - enclosure_front_y
        ),
        "enclosure_roof_z_mm": enclosure_roof_z,
        "horn_bottom_z_mm": horn_bbox.min.Z,
        "horn_bottom_gap_mm": horn_bottom_gap,
        "target_bottom_gap_mm": 5.0,
        "cabinet_face_width_mm": D.width,
        "physical_rolled_envelope_d_mm": max(horn_bbox.size.X, horn_bbox.size.Z),
        "envelope_to_face_width_error_mm": (
            max(horn_bbox.size.X, horn_bbox.size.Z) - D.width
        ),
    }
    de250_bbox = de250.bounding_box()
    upper_spine_front_y = D.upper_tower_y - D.tower_outer_ry
    de250_to_spine_clearance = upper_spine_front_y - de250_bbox.max.Y
    if de250_to_spine_clearance < 0.30:
        raise ValueError(
            "DE250 does not have 0.30 mm assembly clearance to the upper spine: "
            f"{de250_to_spine_clearance:.6f} mm"
        )
    horn_data["driver_support"]["tube_front_y_mm"] = upper_spine_front_y
    horn_data["driver_support"]["upper_spine_center_y_mm"] = D.upper_tower_y
    horn_data["driver_support"]["de250_to_spine_clearance_mm"] = (
        de250_to_spine_clearance
    )
    horn_data["driver_support"]["external_spine_offset_mm"] = (
        D.upper_tower_y - D.port_y
    )
    horn_data["driver_support"]["external_spine_is_straight"] = True

    final_volume = _volume_accounting(
        printed_intrusions,
        port_displacement,
        woofer,
        gx16,
    )
    final_lengths = _port_length_solution(float(final_volume["final_modeled_net_box_volume_l"]))
    if abs(final_lengths["outlet_z_mm"] - lengths["outlet_z_mm"]) > 0.01:
        raise ValueError("In-box port volume changed after solving the external length")
    volume = final_volume
    lengths = final_lengths

    target_outlet_z = D.baseline_outlet_top_z - D.target_outlet_drop
    actual_outlet_drop = D.baseline_outlet_top_z - lengths["outlet_z_mm"]
    outlet_drop_error = actual_outlet_drop - D.target_outlet_drop
    if abs(outlet_drop_error) > 0.15:
        raise ValueError(
            "Asymmetric route missed the requested outlet-height reduction: "
            f"{actual_outlet_drop:.6f} mm actual"
        )

    response = _vented_response(
        net_box_l=float(volume["final_modeled_net_box_volume_l"]),
        effective_length_mm=lengths["effective_length_mm"],
    )
    dsp = _dsp_summary(
        response,
        net_box_l=float(volume["final_modeled_net_box_volume_l"]),
        effective_length_mm=lengths["effective_length_mm"],
    )

    interference = {
        "base_to_tower_mm3": _bounded_intersection_volume(base, tower),
        "base_to_internal_tube_mm3": _bounded_intersection_volume(base, internal_tube),
        "base_to_airway_mm3": _bounded_intersection_volume(base, airway),
        "internal_tube_to_airway_mm3": _bounded_intersection_volume(
            internal_tube, airway
        ),
        "internal_tube_to_tower_mm3": _bounded_intersection_volume(
            internal_tube, tower
        ),
        "internal_tube_to_woofer_mm3": _bounded_intersection_volume(
            internal_tube, woofer
        ),
        "internal_tube_to_gx16_mm3": _bounded_intersection_volume(
            internal_tube, gx16
        ),
        "tower_to_airway_mm3": _bounded_intersection_volume(tower, airway),
        "airway_to_woofer_mm3": _bounded_intersection_volume(airway, woofer),
        "port_outer_to_woofer_mm3": _bounded_intersection_volume(port_outer, woofer),
        "airway_to_gx16_mm3": _bounded_intersection_volume(airway, gx16),
        "port_outer_to_gx16_mm3": _bounded_intersection_volume(port_outer, gx16),
        "tower_to_woofer_mm3": _bounded_intersection_volume(tower, woofer),
        "tower_to_horn_mm3": _bounded_intersection_volume(tower, horn),
        "tower_to_de250_mm3": _bounded_intersection_volume(tower, de250),
        "airway_to_de250_mm3": _bounded_intersection_volume(airway, de250),
    }
    for key in (
        "base_to_tower_mm3",
        "base_to_internal_tube_mm3",
        "base_to_airway_mm3",
        "internal_tube_to_airway_mm3",
        "internal_tube_to_tower_mm3",
        "internal_tube_to_woofer_mm3",
        "internal_tube_to_gx16_mm3",
        "tower_to_airway_mm3",
        "airway_to_woofer_mm3",
        "port_outer_to_woofer_mm3",
        "airway_to_gx16_mm3",
        "port_outer_to_gx16_mm3",
        "tower_to_horn_mm3",
        "tower_to_de250_mm3",
        "airway_to_de250_mm3",
    ):
        if interference[key] > 0.001:
            raise ValueError(f"{key} obstructs the airway by {interference[key]:.6f} mm3")

    assembly = Compound(
        children=[
            *_fresh_solids(base),
            *_fresh_solids(internal_tube),
            *_fresh_solids(tower),
            *_fresh_solids(gx16),
        ]
    )
    hardware = Compound(
        children=[
            *_fresh_solids(base),
            *_fresh_solids(internal_tube),
            *_fresh_solids(tower),
            *_fresh_solids(woofer),
            *_fresh_solids(gx16),
            *_fresh_solids(horn),
            *_fresh_solids(de250),
        ]
    )
    cutaway = _cutaway(
        base,
        internal_tube,
        tower,
        woofer,
        gx16,
        horn,
        de250,
    )
    exports = {
        "sand_cube_190x210_single_oval_port_base.step": base,
        "sand_cube_190x210_single_oval_port_internal_tube.step": internal_tube,
        "sand_cube_190x210_single_oval_port_tower.step": tower,
        "sand_cube_190x210_single_oval_port_airway.step": airway,
        "sand_cube_190x210_single_oval_port_gx16.step": gx16,
        "sand_cube_190x210_single_oval_port_horn.step": horn,
        "sand_cube_190x210_single_oval_port_assembly.step": assembly,
        "sand_cube_190x210_single_oval_port_hardware_check.step": hardware,
        "sand_cube_190x210_single_oval_port_cutaway.step": cutaway,
    }
    for filename, shape in exports.items():
        export_step(shape, OUT / filename, unit=Unit.MM, write_pcurves=True)
    step_roundtrip: dict[str, Any] = {}
    for filename, source_shape in exports.items():
        imported = import_step(OUT / filename)
        imported_solids = imported.solids()
        source_solid_count = len(source_shape.solids())
        valid_solids = [solid.is_valid for solid in imported_solids]
        count_matches = len(imported_solids) == source_solid_count
        step_roundtrip[filename] = {
            "source_solid_count": source_solid_count,
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": count_matches,
            "all_imported_solids_valid": all(valid_solids),
        }
        if not count_matches or not all(valid_solids):
            raise ValueError(
                f"STEP round-trip failed for {filename}: "
                f"source={source_solid_count}, imported={len(imported_solids)}, "
                f"valid={valid_solids}"
            )
    cavity_floor = -D.height / 2.0 + D.wall_stack_t
    in_box_airway = _primary_shape(airway & _outer_envelope())
    in_box_port_outer = _primary_shape(port_outer & _outer_envelope())
    port_bb = in_box_port_outer.bounding_box()
    airway_bb = in_box_airway.bounding_box()
    diagnostics: dict[str, Any] = {
        "name": D.name,
        "status": (
            "separately printable round front-facing route with one broad plan "
            f"sweep, one rotated R70 rise, and {lengths['calculated_tuning_hz']:.2f} Hz "
            "natural tuning"
        ),
        "isolation": {
            "experiment_dir": "experiments/sand_cube_190x210_single_oval_port",
            "output_dir": "build/sand_cube_190x210_single_oval_port",
            "three_prior_variants_modified": False,
        },
        "design_inputs": asdict(D),
        "enclosure": {
            "outer_dimensions_mm": [D.width, D.depth, D.height],
            "front_face_mm": [D.width, D.height],
            "extra_depth_vs_190_cube_mm": D.depth - D.width,
            "non_front_wall_stack_outer_sand_inner_mm": [
                D.outer_skin_t,
                D.sand_gap_t,
                D.inner_skin_t,
            ],
            "wall_stack_geometry": wall_stack_checks,
            "construction": (
                "The sides, roof, and rear use a concentric rounded 2-3-2 stack; "
                "the floor is a solid 7 mm plate and the restored front uses the "
                "larger design's solid 7 mm contoured black-hole wall. A separately "
                "printable circular port sits tangent on top of the untouched solid "
                "floor and passes through a hidden roof saddle while remaining fully "
                "ahead of the rear 2-3-2 wall. The redundant floor rail is deleted; two "
                "mounting ears fasten directly into the solid floor, while a rear "
                "cross-brace provides the second cradle. "
                "The visible tower is a constant circular column with a 5 mm wall and "
                "no external mounting flange; its hidden integral L saddle bears on "
                "the inner roof and rear wall."
            ),
            "scaled_black_hole": {
                "center_offset_up_mm": BLACK_HOLE_CENTER_Z,
                "larger_200_mm_design_outer_diameter_mm": 183.0,
                "scaled_outer_diameter_mm": BLACK_HOLE_OUTER_D,
                "driver_opening_diameter_mm": P.driver_cutout_dia,
                "seat_land_outer_diameter_mm": SEAT_LAND_OD,
                "recess_depth_preserved_from_larger_design_mm": (
                    BLACK_HOLE_VARIANT.recess_depth
                ),
                "driver_seat_depth_mm": BLACK_HOLE_SEAT_DEPTH,
                "larger_design_radial_blend_span_mm": (183.0 - P.driver_cutout_dia)
                / 2.0,
                "scaled_radial_blend_span_mm": (
                    BLACK_HOLE_OUTER_D - P.driver_cutout_dia
                )
                / 2.0,
                "top_clearance_after_edge_fillet_mm": (
                    D.height / 2.0
                    - BLACK_HOLE_CENTER_Z
                    - BLACK_HOLE_OUTER_D / 2.0
                    - D.edge_fillet_r
                ),
                "design_intent": (
                    "The woofer remains dead-centered and the contour extends "
                    "exactly to the cabinet edge-radius tangent on all four sides. "
                    "Its 21.75 mm radial blend is substantially gentler than the "
                    "previous 161 mm-diameter draft while preserving the larger "
                    "design's exact axial depth."
                ),
            },
            "restored_original_features": {
                "gx16": {
                    "center_xz_mm": [P.gx16_x, P.gx16_z],
                    "rear_face_y_mm": D.center_y + D.depth / 2.0,
                    "solid_connector_island": True,
                    "captive_inner_hex_pocket": True,
                    "placed_hardware": gx16_data,
                },
                "sand_fill_ports": {
                    "count": 2,
                    "rear_entry_centers_xz_mm": [
                        [-P.fill_port_x, P.fill_port_z],
                        [P.fill_port_x, P.fill_port_z],
                    ],
                    "entry_diameter_mm": P.fill_entry_d,
                    "transition_length_mm": (
                        RESTORED_FEATURE_VARIANT.fill_port_transition_length
                    ),
                    "internal_support_wall_mm": (
                        RESTORED_FEATURE_VARIANT.fill_port_transition_support_wall
                    ),
                    "curved_internal_blisters": True,
                },
                "internal_bracing": {
                    "transverse_window_brace": True,
                    "transverse_window_brace_is_top_and_side_u_frame": True,
                    "transverse_window_bottom_rail_retained": False,
                    "window_brace_center_y_mm": (
                        RESTORED_FEATURE_VARIANT.window_brace_center_y
                    ),
                    "window_brace_depth_mm": (
                        RESTORED_FEATURE_VARIANT.window_brace_height
                    ),
                    "top_longitudinal_brace": True,
                    "bottom_longitudinal_brace": False,
                    "left_right_longitudinal_braces": True,
                    "longitudinal_brace_depth_mm": (
                        RESTORED_FEATURE_VARIANT.vertical_brace_height
                    ),
                    "all_rib_inward_heights_mm": list(rib_heights),
                    "window_and_longitudinal_inward_faces_flush": True,
                    "port_relief_clearance_mm": D.brace_port_clearance,
                    "front_seamless_blend_count": 4,
                    "front_roots_follow_visible_black_hole_contour": True,
                    "front_roots_fill_local_relief_void": True,
                    "front_root_tail_offset_from_driver_seat_mm": (
                        D.front_brace_blend_length
                        - D.front_brace_baffle_embed
                    ),
                    "front_blend_seat_diameter_mm": SEAT_LAND_OD,
                    "front_root_inner_diameter_mm": 2.0 * longitudinal_inner_radius,
                    "front_mounting_land_radial_embed_mm": D.front_brace_ring_embed,
                    "canonical_buttress_volume_mm3": front_buttress_volumes[0],
                    "canonical_buttress_axial_depth_mm": front_buttress_y_depths[0],
                    "all_four_buttresses_equal_volume": True,
                    "all_four_buttresses_equal_axial_depth": True,
                    "legacy_front_tabs_removed_before_buttress_fusion": True,
                    "black_hole_tools_run_before_final_buttress_fusion": True,
                    "rear_horizontal_cradle": {
                        "front_y_mm": D.rear_cradle_front_y,
                        "depth_mm": D.rear_cradle_depth,
                        "height_mm": D.rear_cradle_height,
                        "tube_seat_clearance_mm": D.brace_port_clearance,
                    },
                    "continuous_floor_rail_retained": False,
                    "floor_support_is_solid_floor_insert_pockets": True,
                    "minimum_analytic_clearance_to_woofer_mm": (
                        brace_to_woofer_clearance
                    ),
                    "design_intent": (
                        "The original brace network is retained around the complete "
                        "port. Four identical constant-height roots follow the exact "
                        "black-hole contour and fill the local relief behind the face, "
                        "then meet the retained 10 mm top and side rails without a step. The "
                        "recess is finished first, so no later subtraction reopens a slot "
                        "at any of the four structural joints. The already-solid floor carries no "
                        "closed rail across the duct; the entire redundant bottom rail "
                        "is removed, and the tube ears fasten into the solid "
                        "floor. The rear cross-rail remains a full "
                        "cradle around the rising return."
                    ),
                },
            },
        },
        "alignment": {
            "type": (
                "single-port bass reflex with a front-facing low inlet, one "
                "broad circular-plan sweep, one rotated R70 rise, and one "
                "monotonic upper drift"
            ),
            "dsp_playback_goal_hz": D.target_tuning_hz,
            "calculated_tuning_hz": lengths["calculated_tuning_hz"],
            "predicted_natural_small_signal_f3_hz": response["predicted_f3_hz"],
            "dsp_assisted_goal": dsp,
        },
        "volume_accounting": volume,
        "port": {
            "airway_ellipse_mm": [D.port_width, D.port_depth],
            "constant_area_airway_is_round": True,
            "constant_area_airway_diameter_mm": D.port_width,
            "area_mm2": D.port_area_mm2,
            "equivalent_round_diameter_mm": equivalent_port_d,
            "ellipse_aspect_ratio": D.port_width / D.port_depth,
            "lower_internal_wall_thickness_mm": D.port_wall_t,
            "visible_weight_bearing_tower_wall_thickness_mm": (
                D.structural_tower_wall_t
            ),
            "wall_thickness_transition_hidden_below_roof": True,
            "wall_thickness_transition_z_mm": [
                D.structural_wall_transition_start_z,
                D.structural_wall_transition_end_z,
            ],
            "separate_printed_internal_tube": {
                "enabled": True,
                "installation_clearance_mm": D.tube_install_clearance,
                "integrated_mounting_tabs": 4,
                "bottom_tab_pairs": 1,
                "rear_tab_pairs": 1,
                "tab_thickness_mm": D.tube_tab_t,
                "clearance_hole_diameter_mm": D.tube_mount_clearance_d,
                "brace_insert_pocket_diameter_mm": D.tube_mount_insert_d,
                "bottom_floor_insert_pocket_depth_mm": (
                    D.bottom_tube_mount_insert_depth
                ),
                "rear_brace_insert_pocket_depth_mm": D.tube_mount_insert_depth,
                "remaining_floor_below_bottom_pocket_mm": (
                    D.wall_stack_t - D.bottom_tube_mount_insert_depth
                ),
                "bottom_tab_to_floor_nominal_gap_mm": D.tube_tab_seating_clearance,
                "rear_tab_to_brace_nominal_gap_mm": D.tube_tab_seating_clearance,
                "fasteners_intrude_into_airway": False,
            },
            "internally_mounted_upper_tower": {
                "external_top_flange_removed": True,
                "sole_visible_cabinet_to_horn_support": True,
                "visible_airway_profile": "constant circle",
                "visible_outer_profile": "constant circle",
                "visible_wall_thickness_mm": D.structural_tower_wall_t,
                "rear_clearance_to_acoustic_face_mm": (
                    structural_tower_rear_clearance
                ),
                "installation_clearance_to_rear_acoustic_face_mm": (
                    structural_tower_install_clearance
                ),
                "tower_starts_inside_enclosure_z_mm": D.internal_tower_bottom_z,
                "horizontal_plate": {
                    "width_mm": D.internal_mount_plate_w,
                    "depth_mm": D.internal_mount_roof_depth,
                    "thickness_mm": D.internal_mount_plate_t,
                    "bearing_surface": "underside of inner roof",
                },
                "vertical_plate": {
                    "width_mm": D.internal_mount_plate_w,
                    "height_mm": (
                        D.height / 2.0
                        - D.wall_stack_t
                        - D.internal_mount_rear_bottom_z
                    ),
                    "thickness_mm": D.internal_mount_plate_t,
                    "bearing_surface": "inside of rear wall",
                },
                "right_angle_is_one_tower_solid": True,
                "clearance_hole_count": 4,
                "clearance_hole_diameter_mm": D.internal_mount_clearance_d,
                "platform_count": 4,
                "platform_diameter_mm": D.internal_mount_platform_d,
                "insert_pocket_diameter_mm": D.internal_mount_insert_d,
                "insert_pocket_depth_mm": D.internal_mount_insert_depth,
                "fasteners_intrude_into_airway": False,
            },
            "inlet_mouth_ellipse_mm": [D.inlet_mouth_width, D.inlet_mouth_height],
            "inlet_mouth_center_xyz_mm": [
                D.inlet_x,
                D.inlet_mouth_y,
                D.inlet_mouth_center_z,
            ],
            "inlet_clearance_from_driver_seat_plane_mm": (
                inlet_clearance_from_driver_seat
            ),
            "inlet_clearance_in_equivalent_diameters": (
                inlet_clearance_from_driver_seat / equivalent_port_d
            ),
            "inlet_lateral_install_clearance_to_left_wall_mm": (
                inlet_lateral_wall_clearance
            ),
            "inlet_axial_clearance_to_front_seat_plane_mm": (
                inlet_axial_front_clearance
            ),
            "inlet_minimum_axial_clearance_mm": inlet_minimum_axial_clearance,
            "inlet_minimum_axial_clearance_in_equivalent_diameters": (
                inlet_minimum_axial_clearance / equivalent_port_d
            ),
            "main_airway_at_throat_mm": [D.inlet_flat_width, D.inlet_flat_height],
            "main_airway_center_z_mm": D.inlet_flat_center_z,
            "asymmetric_route": {
                "lower_right_vertical_center_xy_mm": [
                    D.lower_elbow_vertical_x,
                    D.lower_elbow_vertical_y,
                ],
                "front_facing_inlet_direction_xy": list(
                    D.inlet_run_direction_xy
                ),
                "lower_sweep_center_xy_mm": [
                    D.lower_sweep_center_x,
                    D.lower_sweep_center_y,
                ],
                "lower_sweep_centerline_radius_mm": D.lower_sweep_radius,
                "lower_sweep_turn_deg": math.degrees(D.lower_sweep_turn_rad),
                "lower_sweep_end_direction_xy": list(
                    D.lower_sweep_end_direction_xy
                ),
                "rotated_elbow_center_xyz_mm": [
                    D.bend_center_x,
                    D.bend_center_y,
                    D.bend_center_z,
                ],
                "rotated_elbow_centerline_radius_mm": D.bend_centerline_r,
                "return_to_center_end_z_mm": D.asymmetric_vertical_return_top_z,
                "return_law": (
                    "degree-eight planar Bezier with monotonic Z and no "
                    "lateral reversal"
                ),
                "return_control_fraction": list(D.upper_drift_control_fraction),
                "return_is_single_vertical_plane": True,
                "return_has_vertical_end_tangents": True,
                "constant_area_section_is_round": True,
                "old_center_to_side_floor_s_removed": True,
                "second_discrete_elbow_added": False,
            },
            "outlet_mouth_ellipse_mm": [D.outlet_mouth_width, D.outlet_mouth_depth],
            "outlet_mouth_is_round": True,
            "bend_centerline_radius_mm": D.bend_centerline_r,
            "bend_inside_air_radius_mm": D.bend_centerline_r - D.port_rz,
            "broad_plan_sweep_count": 1,
            "discrete_vertical_elbow_count": 1,
            "bend_count": 2,
            "lengths": lengths,
            "outlet_height_target": {
                "baseline_top_z_mm": D.baseline_outlet_top_z,
                "requested_drop_mm": D.target_outlet_drop,
                "target_top_z_mm": target_outlet_z,
                "actual_top_z_mm": lengths["outlet_z_mm"],
                "actual_drop_mm": actual_outlet_drop,
                "drop_error_mm": outlet_drop_error,
                "outlet_below_de250_body_top_mm": (
                    de250_bbox.max.Z - lengths["outlet_z_mm"]
                ),
            },
            "visible_outlet_height_above_box_mm": lengths["outlet_z_mm"] - D.height / 2.0,
            "physical_interface": {
                "airway_clearance_above_floor_mm": airway_bb.min.Z - cavity_floor,
                "outer_tube_floor_tangency_error_mm": port_bb.min.Z - cavity_floor,
                "floor_channel_cut_depth_mm": actual_port_channel_depth,
                "clearance_to_floor_outer_skin_mm": port_bb.min.Z - (-D.height / 2.0 + D.outer_skin_t),
                "internal_vertical_center_y_mm": D.port_y,
                "rear_wall_acoustic_face_y_mm": REAR_INNER_Y,
                "tube_outer_rear_y_below_external_shift_mm": (
                    D.port_y + D.outer_rz
                ),
                "tube_outer_clearance_to_rear_acoustic_face_mm": (
                    REAR_INNER_Y - (D.port_y + D.outer_rz)
                ),
                "installation_envelope_clearance_to_rear_acoustic_face_mm": (
                    rear_wall_install_clearance
                ),
                "structural_tower_outer_rear_y_mm": (
                    D.upper_tower_y + D.tower_outer_ry
                ),
                "structural_tower_clearance_to_rear_acoustic_face_mm": (
                    structural_tower_rear_clearance
                ),
                "structural_tower_installation_clearance_to_rear_acoustic_face_mm": (
                    structural_tower_install_clearance
                ),
                "rear_2_3_2_wall_encroached": False,
                "external_tower_center_offset_mm": D.upper_tower_y - D.port_y,
                "external_tower_is_straight": True,
            },
        },
        "response_and_velocity": response,
        "geometry": {
            "base_bbox": _bbox(base),
            "internal_tube_bbox": _bbox(internal_tube),
            "tower_bbox": _bbox(tower),
            "airway_bbox": _bbox(airway),
            "assembly_bbox": _bbox(assembly),
            "solid_counts": {
                "base": len(base.solids()),
                "internal_tube": len(internal_tube.solids()),
                "tower": len(tower.solids()),
                "airway": len(airway.solids()),
                "gx16": len(gx16.solids()),
            },
            "validity": {
                "base": _is_valid(base),
                "internal_tube": _is_valid(internal_tube),
                "tower": _is_valid(tower),
                "airway": _is_valid(airway),
                "gx16_all_solids": all(_is_valid(solid) for solid in gx16.solids()),
            },
            "step_roundtrip": step_roundtrip,
            "interference_mm3": interference,
            "gx16_interface": {
                "source_cutout_and_hardware_contract_reused": True,
                "center_alignment_error_mm": 0.0,
                "rear_extension_shift_mm": REAR_EXTENSION_Y,
            },
            "single_external_rising_support": True,
            "cutaway_includes_base_tube_tower_woofer_gx16_horn_and_de250": True,
            "cutaway_opaque_airway_debug_solid_removed": True,
            "horn_and_de250": horn_data,
        },
        "moderate_volume_limits": [
            (
                f"The {D.port_area_mm2:.0f} mm2 port is the packaging trade: it provides a "
                f"modeled {lengths['calculated_tuning_hz']:.2f} Hz natural alignment, but "
                "port velocity—not the E150HE-44 thermal rating—sets "
                "the bass-output ceiling."
            ),
            (
                "DSP can flatten the natural rolloff only by spending voltage, excursion, "
                "and port-velocity headroom. A 28-30 Hz fourth-order high-pass and a "
                "level-dependent bass limiter are part of the alignment."
            ),
            (
                "The lumped model is a design target. Final EQ and the final port trim "
                "must come from an impedance sweep and near-field measurements of a print."
            ),
            (
                "Amplifier electronics, any additional wire-retention features, and final "
                "print splits are deferred; their lost volume must be included before "
                "production tuning. The restored GX16 and sand-fill blisters are included."
            ),
        ],
        "files": {
            **{name: str(OUT / name) for name in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
