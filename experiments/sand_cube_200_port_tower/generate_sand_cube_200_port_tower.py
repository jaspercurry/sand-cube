"""Generate the isolated 200 mm Sand Cube resonant-port tower derivative.

The validated FINAL_200_VARIANT is used as a read-only geometric baseline.  The
rear passive-radiator service opening is restored, a sealed top receiver is
added, and a separately printable straight flared duct/tower is fitted through
that receiver.  All dimensions are millimetres unless stated otherwise.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Axis,
    Bezier,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Location,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    Rot,
    Unit,
    add,
    export_step,
    fillet,
    import_step,
    make_face,
    revolve,
)


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.sand_cube_8_5_black_hole.generate_contoured_inner_variants import (  # noqa: E402
    FINAL_200_VARIANT,
    _confirmed_binding_posts,
    _confirmed_passive_radiator,
    _confirmed_woofer,
    _final_params,
    _front_tool_global_oriented,
    _inner_relief_tool,
    _intersection_volume,
    _oriented_cylinder,
    _placed_gx16,
    _primary_shape,
    _require_single_solid,
    build_variant,
)
from src.final_horn import build as build_final_horn  # noqa: E402


OUT = ROOT / "build" / "sand_cube_200_port_tower"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_200_port_tower"
    target_tuning_hz: float = 43.0
    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204

    # Straight circular Helmholtz neck.  Area was selected to keep the ideal
    # 100 W peak near Mach 0.09 while retaining a six-inch-class visible tower.
    port_area_mm2: float = 1100.0
    port_wall_t: float = 3.2
    # Keep the tower on the enclosure's visual centerline.  It remains aft in
    # Y so the in-box duct clears the E150HE-44 motor.
    port_x: float = 0.0
    port_y: float = 55.5
    inlet_z: float = -80.0
    inlet_flare_l: float = 16.0
    inlet_mouth_r: float = 26.0
    outlet_flare_l: float = 25.0
    outlet_mouth_r: float = 29.0
    inlet_end_correction_factor: float = 0.85
    outlet_end_correction_factor: float = 0.613

    # Sealed top receiver and separate-tower joint.
    receiver_r: float = 32.0
    receiver_bottom_z: float = 82.0
    spigot_radial_clearance: float = 0.30
    flange_r: float = 32.0
    flange_t: float = 5.0
    gasket_t: float = 0.8
    attachment_bcd_r: float = 27.0
    attachment_count: int = 3
    tower_bolt_clearance_d: float = 4.5
    base_insert_pocket_d: float = 4.8
    base_insert_pocket_depth: float = 6.5

    # The DE250 is centered ahead of the tube.  A full front clamp ring carries
    # both B&C bolt patterns while a rear, open-top U cradle supports the body
    # from below and blends directly into the tube.
    horn_center_x: float = 0.0
    horn_center_z: float = 210.0
    horn_mount_face_y: float = -31.5
    horn_face_t: float = 4.0
    horn_acoustic_hole_d: float = 42.0
    horn_mount_ring_r: float = 50.0
    horn_cup_inner_r: float = 62.0
    horn_cup_outer_r: float = 68.0
    horn_cup_open_above_center: float = 8.0
    horn_cup_front_overlap: float = 0.6
    horn_cup_tube_overlap: float = 5.0

    # Move the two binding posts ahead of the now-centered receiver.  The new
    # island overlaps the existing top island, preserving one connected solid.
    binding_post_y: float = 5.0
    binding_island_d: float = 26.0
    binding_island_corner_r: float = 5.0

    waist_brace_clearance_extra_d: float = 1.0

    @property
    def port_r(self) -> float:
        return math.sqrt(self.port_area_mm2 / math.pi)

    @property
    def port_d(self) -> float:
        return 2.0 * self.port_r

    @property
    def port_outer_r(self) -> float:
        return self.port_r + self.port_wall_t

    @property
    def receiver_bore_r(self) -> float:
        return self.port_outer_r + self.spigot_radial_clearance

    @property
    def horn_cup_rear_y(self) -> float:
        return self.port_y - self.port_outer_r + self.horn_cup_tube_overlap


D = Design()
P = _final_params(FINAL_200_VARIANT)


E150_SOURCE_URL = (
    "https://www.parts-express.com/pedocs/specs/"
    "295-102--epique-e150he-44-spec-sheet.pdf"
)
E150_PRODUCT_URL = (
    "https://www.daytonaudio.com/product/1911/"
    "e150he-44-5-1-2-dvc-mmag-extended-range-subwoofer-4-ohms-per-coil"
)
E180_PR_SOURCE_URL = (
    "https://www.parts-express.com/pedocs/specs/"
    "295-114--epique-e180he-pr-spec-sheet.pdf"
)


E150 = {
    "voice_coils": "series, as used for Dayton's published graphs and data",
    "re_ohm": 6.6,
    "le_h": 1.6e-3,
    "fs_hz": 40.0,
    "qms": 2.94,
    "qes": 0.45,
    "qts": 0.39,
    "mms_kg": 26.6e-3,
    "cms_m_n": 0.60e-3,
    "sd_m2": 95.03e-4,
    "vas_l": 0.27 * 28.316846592,
    "bl_tm": 9.8,
    "xmax_mm": 14.7,
    "vd_cm3": 139.7,
    "rms_power_w": 200.0,
    "manufacturer_recommended_vented_volume_l": 0.22 * 28.316846592,
    "manufacturer_recommended_vented_f3_hz": 43.0,
}


E180_PR = {
    "sd_m2": 136.1e-4,
    "cmpr_m_n": 0.48e-3,
    "rmpr_kg_s": 4.34,
    "xmech_mm": 19.0,
    "vd_cm3": 258.59,
    "mass_cases_g": [110.0, 143.5, 172.0, 200.7],
    "added_disks": [0, 1, 2, 3],
}


def _is_valid(shape: Any) -> bool:
    valid = getattr(shape, "is_valid")
    return valid() if callable(valid) else bool(valid)


def _fresh_solids(shape: Any) -> list[Any]:
    return [copy.copy(solid) for solid in shape.solids()]


def _bbox(shape: Any) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min_mm": [round(bb.min.X, 4), round(bb.min.Y, 4), round(bb.min.Z, 4)],
        "max_mm": [round(bb.max.X, 4), round(bb.max.Y, 4), round(bb.max.Z, 4)],
        "size_mm": [round(bb.size.X, 4), round(bb.size.Y, 4), round(bb.size.Z, 4)],
    }


def _outer_envelope() -> Part:
    outer = Box(P.cube_outer, P.cube_outer, P.cube_outer)
    outer = fillet(outer.edges(), radius=P.edge_fillet_r)
    return _primary_shape(outer)


def _attachment_positions() -> list[tuple[float, float]]:
    # One fastener is aft and two are forward, keeping all three away from the
    # two existing binding-post pilots.
    return [
        (
            D.port_x + D.attachment_bcd_r * math.cos(math.radians(angle)),
            D.port_y + D.attachment_bcd_r * math.sin(math.radians(angle)),
        )
        for angle in (90.0, 210.0, 330.0)
    ]


def _radius_profile_solid(
    *,
    tube_r: float,
    inlet_mouth_r: float,
    outlet_mouth_r: float,
    outlet_z: float,
) -> Part:
    """Revolve a tangent-controlled, positive-area port profile on Plane.XZ."""
    inlet_throat_z = D.inlet_z + D.inlet_flare_l
    outlet_throat_z = outlet_z - D.outlet_flare_l
    if outlet_throat_z <= inlet_throat_z:
        raise ValueError("Port straight section must have positive length")

    with BuildPart() as profile:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Polyline((0.0, D.inlet_z), (inlet_mouth_r, D.inlet_z))
                Bezier(
                    (inlet_mouth_r, D.inlet_z),
                    (inlet_mouth_r, D.inlet_z + 0.45 * D.inlet_flare_l),
                    (tube_r, inlet_throat_z - 0.45 * D.inlet_flare_l),
                    (tube_r, inlet_throat_z),
                )
                Polyline((tube_r, inlet_throat_z), (tube_r, outlet_throat_z))
                Bezier(
                    (tube_r, outlet_throat_z),
                    (tube_r, outlet_throat_z + 0.45 * D.outlet_flare_l),
                    (outlet_mouth_r, outlet_z - 0.45 * D.outlet_flare_l),
                    (outlet_mouth_r, outlet_z),
                )
                Polyline(
                    (outlet_mouth_r, outlet_z),
                    (0.0, outlet_z),
                    (0.0, D.inlet_z),
                )
            make_face()
        assert sketch.sketch.area > 0, "Port revolve profile must have positive area"
        revolve(axis=Axis.Z)
    return _require_single_solid(profile.part, feature="revolved port profile")


def _bezier_radius(
    start_r: float,
    end_r: float,
    t: float,
) -> float:
    # The geometric profiles use controls at 45% of the axial flare length.
    p0 = start_r
    p1 = start_r
    p2 = end_r
    p3 = end_r
    u = 1.0 - t
    return u**3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t**3 * p3


def _flare_equivalent_length_mm(start_r: float, end_r: float, length: float) -> float:
    """Return inertance-equivalent length referred to the constant throat area."""
    steps = 4000
    total = 0.0
    for index in range(steps):
        t = (index + 0.5) / steps
        radius = _bezier_radius(start_r, end_r, t)
        total += (D.port_r / radius) ** 2
    return length * total / steps


def _port_length_solution(net_box_l: float) -> dict[str, float]:
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    required_effective_m = (
        D.speed_of_sound_m_s**2
        * area_m2
        / ((2.0 * math.pi * D.target_tuning_hz) ** 2 * volume_m3)
    )
    inlet_end_mm = D.inlet_end_correction_factor * D.inlet_mouth_r
    outlet_end_mm = D.outlet_end_correction_factor * D.outlet_mouth_r
    inlet_flare_equiv_mm = _flare_equivalent_length_mm(
        D.inlet_mouth_r,
        D.port_r,
        D.inlet_flare_l,
    )
    outlet_flare_equiv_mm = _flare_equivalent_length_mm(
        D.port_r,
        D.outlet_mouth_r,
        D.outlet_flare_l,
    )
    straight_equiv_needed_mm = (
        required_effective_m * 1000.0
        - inlet_end_mm
        - outlet_end_mm
        - inlet_flare_equiv_mm
        - outlet_flare_equiv_mm
    )
    outlet_z = (
        D.inlet_z
        + D.inlet_flare_l
        + straight_equiv_needed_mm
        + D.outlet_flare_l
    )
    physical_length_mm = outlet_z - D.inlet_z
    area_corrected_physical_mm = (
        inlet_flare_equiv_mm
        + straight_equiv_needed_mm
        + outlet_flare_equiv_mm
    )
    effective_check_mm = area_corrected_physical_mm + inlet_end_mm + outlet_end_mm
    tuning_check = D.speed_of_sound_m_s / (2.0 * math.pi) * math.sqrt(
        area_m2 / (volume_m3 * (effective_check_mm / 1000.0))
    )
    return {
        "outlet_z_mm": outlet_z,
        "physical_centerline_length_mm": physical_length_mm,
        "straight_constant_area_length_mm": straight_equiv_needed_mm,
        "inlet_flare_area_equivalent_length_mm": inlet_flare_equiv_mm,
        "outlet_flare_area_equivalent_length_mm": outlet_flare_equiv_mm,
        "area_corrected_physical_length_mm": area_corrected_physical_mm,
        "inlet_end_correction_mm": inlet_end_mm,
        "outlet_end_correction_mm": outlet_end_mm,
        "effective_length_mm": effective_check_mm,
        "calculated_tuning_hz": tuning_check,
    }


def _horn_cup() -> Part:
    """Open-top DE250 cradle with a full front mounting ring."""
    shell_front_y = D.horn_mount_face_y - D.horn_cup_front_overlap
    shell_rear_y = D.horn_cup_rear_y
    shell_depth = shell_rear_y - shell_front_y
    shell_center_y = (shell_front_y + shell_rear_y) / 2.0

    outer = _oriented_cylinder(
        diameter=2.0 * D.horn_cup_outer_r,
        depth=shell_depth,
        axis="y",
        center=(D.horn_center_x, shell_center_y, D.horn_center_z),
    )
    inner = _oriented_cylinder(
        diameter=2.0 * D.horn_cup_inner_r,
        depth=shell_depth + 2.0,
        axis="y",
        center=(D.horn_center_x, shell_center_y, D.horn_center_z),
    )
    shell = _primary_shape(outer - inner)
    shell_bottom_z = D.horn_center_z - D.horn_cup_outer_r
    shell_top_z = D.horn_center_z + D.horn_cup_open_above_center
    keep = Pos(
        D.horn_center_x,
        shell_center_y,
        (shell_bottom_z + shell_top_z) / 2.0,
    ) * Box(
        2.0 * D.horn_cup_outer_r + 4.0,
        shell_depth + 4.0,
        shell_top_z - shell_bottom_z,
    )
    shell = _primary_shape(shell & keep)

    face_center_y = D.horn_mount_face_y - D.horn_face_t / 2.0
    ring = _oriented_cylinder(
        diameter=2.0 * D.horn_mount_ring_r,
        depth=D.horn_face_t,
        axis="y",
        center=(
            D.horn_center_x,
            face_center_y,
            D.horn_center_z,
        ),
    )
    lip_outer = _oriented_cylinder(
        diameter=2.0 * D.horn_cup_outer_r,
        depth=D.horn_face_t,
        axis="y",
        center=(D.horn_center_x, face_center_y, D.horn_center_z),
    )
    lip_inner = _oriented_cylinder(
        diameter=2.0 * (D.horn_mount_ring_r - 1.0),
        depth=D.horn_face_t + 2.0,
        axis="y",
        center=(D.horn_center_x, face_center_y, D.horn_center_z),
    )
    front_keep = Pos(
        D.horn_center_x,
        face_center_y,
        (shell_bottom_z + shell_top_z) / 2.0,
    ) * Box(
        2.0 * D.horn_cup_outer_r + 4.0,
        D.horn_face_t + 2.0,
        shell_top_z - shell_bottom_z,
    )
    front_lip = _primary_shape((lip_outer - lip_inner) & front_keep)
    cup = (ring + front_lip + shell).clean().fix()
    rim_edges = []
    for edge in cup.edges():
        bb = edge.bounding_box()
        if (
            abs(bb.min.Z - shell_top_z) < 0.01
            and bb.size.Y > 60.0
            and bb.size.X < 0.01
            and bb.size.Z < 0.01
        ):
            rim_edges.append(edge)
    if len(rim_edges) != 4:
        raise ValueError(f"Expected four DE250 cup rim edges, found {len(rim_edges)}")
    cup = fillet(rim_edges, radius=2.5).clean().fix()
    return _require_single_solid(cup, feature="integrated DE250 half-cup")


def _horn_cup_cutouts() -> Part:
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
        for angle_deg in (30.0, 150.0, 270.0):
            angle = math.radians(angle_deg)
            add(
                _oriented_cylinder(
                    diameter=P.horn_bolt_clearance_d,
                    depth=D.horn_face_t + 4.0,
                    axis="y",
                    center=(
                        D.horn_center_x
                        + P.horn_bolt_3_bcd / 2.0 * math.cos(angle),
                        center_y,
                        D.horn_center_z
                        + P.horn_bolt_3_bcd / 2.0 * math.sin(angle),
                    ),
                )
            )
        for angle_deg in (-60.0, 120.0):
            angle = math.radians(angle_deg)
            add(
                _oriented_cylinder(
                    diameter=P.horn_bolt_clearance_d,
                    depth=D.horn_face_t + 4.0,
                    axis="y",
                    center=(
                        D.horn_center_x
                        + P.horn_bolt_2_bcd / 2.0 * math.cos(angle),
                        center_y,
                        D.horn_center_z
                        + P.horn_bolt_2_bcd / 2.0 * math.sin(angle),
                    ),
                )
            )
    return cutouts.part


def _relocated_binding_posts() -> list[Any]:
    dy = D.binding_post_y - P.binding_post_y
    return [Location((0.0, dy, 0.0)) * post for post in _confirmed_binding_posts(P)]


def _binding_post_island_and_pilots() -> tuple[Part, Part]:
    half = P.cube_outer / 2.0
    top_stack_t = P.outer_skin_t + P.void_t + P.inner_skin_t
    island = Box(P.top_island_w, D.binding_island_d, top_stack_t)
    vertical_edges = [
        edge
        for edge in island.edges()
        if abs(edge.bounding_box().size.Z - top_stack_t) < 0.01
        and edge.bounding_box().size.X < 0.01
        and edge.bounding_box().size.Y < 0.01
    ]
    island = fillet(vertical_edges, radius=D.binding_island_corner_r)
    island = Pos(0.0, D.binding_post_y, half - top_stack_t / 2.0) * island

    pilot_side = FINAL_200_VARIANT.binding_post_diamond_pilot_diagonal / math.sqrt(2)
    with BuildPart() as pilots:
        for x in (-P.binding_post_spacing / 2.0, P.binding_post_spacing / 2.0):
            add(
                Location((x, D.binding_post_y, half - top_stack_t / 2.0))
                * (
                    Rot(0.0, 0.0, 45.0)
                    * Box(pilot_side, pilot_side, top_stack_t + 2.0)
                )
            )
    return _primary_shape(island), pilots.part


def build_base_enclosure() -> tuple[Part, Part, dict[str, Any]]:
    baseline, baseline_diagnostics = build_variant(FINAL_200_VARIANT)
    half = P.cube_outer / 2.0

    # Restore the complete 14 mm rear cap through the service opening, shallow
    # PR recess, and all six insert bores.  The disk stops at the original rear
    # cavity plane, so the acoustic cavity length is unchanged.
    rear_closure = _oriented_cylinder(
        diameter=P.pr_recess_dia,
        depth=P.rear_cap_t,
        axis="y",
        center=(0.0, half - P.rear_cap_t / 2.0, 0.0),
    )
    base = baseline.fuse(rear_closure, glue=True, tol=0.01).clean().fix()
    base = _require_single_solid(base, feature="rear-closed base enclosure")

    # Move the binding-post pilots ahead of the centered receiver.  The added
    # island overlaps the existing reinforcement, and the original pilots are
    # restored before the two new self-supporting diamond pilots are cut.
    binding_island, binding_pilots = _binding_post_island_and_pilots()
    base = base.fuse(binding_island, glue=True, tol=0.01).clean().fix()
    for x in (-P.binding_post_spacing / 2.0, P.binding_post_spacing / 2.0):
        base = base + (
            _oriented_cylinder(
                diameter=12.0,
                depth=18.0,
                axis="z",
                center=(x, P.binding_post_y, half - 9.0),
            )
        )
    base = _require_single_solid(base.clean().fix(), feature="relocated binding island")

    # The centered in-box route crosses the aft center rail and the horizontal
    # waist rail.  Clear only the swept port envelope; each rail retains its two
    # original wall contacts and no closed sand-void rib is introduced.
    clearance_extra_r = D.waist_brace_clearance_extra_d / 2.0
    clearance_local = _radius_profile_solid(
        tube_r=D.port_outer_r + clearance_extra_r,
        inlet_mouth_r=D.inlet_mouth_r + D.port_wall_t + clearance_extra_r,
        outlet_mouth_r=D.port_outer_r + clearance_extra_r,
        outlet_z=D.receiver_bottom_z + D.outlet_flare_l,
    )
    clearance_clip = Pos(
        D.port_x,
        D.port_y,
        (D.inlet_z + D.receiver_bottom_z) / 2.0,
    ) * Box(
        2.0 * (D.inlet_mouth_r + D.port_wall_t + clearance_extra_r) + 2.0,
        2.0 * (D.inlet_mouth_r + D.port_wall_t + clearance_extra_r) + 2.0,
        D.receiver_bottom_z - D.inlet_z,
    )
    brace_clearance = _primary_shape(
        (Location((D.port_x, D.port_y, 0.0)) * clearance_local) & clearance_clip
    )
    base -= brace_clearance
    base = _require_single_solid(base.clean().fix(), feature="brace-cleared base")

    receiver = _oriented_cylinder(
        diameter=2.0 * D.receiver_r,
        depth=half - D.receiver_bottom_z,
        axis="z",
        center=(
            D.port_x,
            D.port_y,
            (half + D.receiver_bottom_z) / 2.0,
        ),
    )
    receiver = _primary_shape(receiver & _outer_envelope())
    base = base.fuse(receiver, glue=True, tol=0.01).clean().fix()
    base = _require_single_solid(base, feature="base with sealed top receiver")

    receiver_bore = _oriented_cylinder(
        diameter=2.0 * D.receiver_bore_r,
        depth=half - D.receiver_bottom_z + 4.0,
        axis="z",
        center=(D.port_x, D.port_y, (half + D.receiver_bottom_z) / 2.0),
    )
    base -= receiver_bore
    for x, y in _attachment_positions():
        base -= _oriented_cylinder(
            diameter=D.base_insert_pocket_d,
            depth=D.base_insert_pocket_depth,
            axis="z",
            center=(x, y, half - D.base_insert_pocket_depth / 2.0),
        )
    base -= binding_pilots
    base = _require_single_solid(base.clean().fix(), feature="finished base")

    bb = base.bounding_box()
    for actual, expected, axis_name in (
        (bb.size.X, P.cube_outer, "X"),
        (bb.size.Y, P.cube_outer, "Y"),
        (bb.size.Z, P.cube_outer, "Z"),
    ):
        if abs(actual - expected) > 0.001:
            raise ValueError(
                f"Base enclosure {axis_name} bbox is {actual:.6f}, expected {expected}"
            )

    return base, baseline, baseline_diagnostics


def build_tower(
    outlet_z: float,
) -> tuple[Part, Part, Part, dict[str, Any]]:
    inner_local = _radius_profile_solid(
        tube_r=D.port_r,
        inlet_mouth_r=D.inlet_mouth_r,
        outlet_mouth_r=D.outlet_mouth_r,
        outlet_z=outlet_z,
    )
    outer_local = _radius_profile_solid(
        tube_r=D.port_outer_r,
        inlet_mouth_r=D.inlet_mouth_r + D.port_wall_t,
        outlet_mouth_r=D.outlet_mouth_r + D.port_wall_t,
        outlet_z=outlet_z,
    )
    airway = Location((D.port_x, D.port_y, 0.0)) * inner_local
    outer_envelope = Location((D.port_x, D.port_y, 0.0)) * outer_local

    flange_bottom = P.cube_outer / 2.0 + D.gasket_t
    flange = Pos(D.port_x, D.port_y, flange_bottom) * Cylinder(
        radius=D.flange_r,
        height=D.flange_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    cup = _horn_cup()
    tower = outer_envelope + flange
    tower = tower + cup
    tower = tower.clean().fix()
    tower = _require_single_solid(tower, feature="uncut port tower")

    # Cut the final airway after all structural additions so the throat remains
    # circular and unobstructed where the cradle blends into the tube.
    tower -= airway
    tower -= _horn_cup_cutouts()
    for x, y in _attachment_positions():
        tower -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.flange_t + 2.0,
            axis="z",
            center=(x, y, flange_bottom + D.flange_t / 2.0),
        )
    tower = _require_single_solid(tower.clean().fix(), feature="finished port tower")

    obstruction = _intersection_volume(tower, airway)
    if obstruction > 0.001:
        raise ValueError(f"Tower obstructs airway by {obstruction:.6f} mm^3")

    return tower, airway, outer_envelope, {
        "flange_bottom_z_mm": flange_bottom,
        "flange_top_z_mm": flange_bottom + D.flange_t,
        "horn_mount_face_front_y_mm": D.horn_mount_face_y - D.horn_face_t,
        "horn_mount_face_rear_y_mm": D.horn_mount_face_y,
        "horn_cup_rear_y_mm": D.horn_cup_rear_y,
        "horn_cup_opening_z_mm": (
            D.horn_center_z + D.horn_cup_open_above_center
        ),
        "outlet_z_mm": outlet_z,
    }


def build_gasket() -> Part:
    half = P.cube_outer / 2.0
    gasket = Pos(D.port_x, D.port_y, half) * Cylinder(
        radius=D.flange_r - 0.5,
        height=D.gasket_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    gasket -= _oriented_cylinder(
        diameter=2.0 * D.receiver_bore_r,
        depth=D.gasket_t + 2.0,
        axis="z",
        center=(D.port_x, D.port_y, half + D.gasket_t / 2.0),
    )
    for x, y in _attachment_positions():
        gasket -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.gasket_t + 2.0,
            axis="z",
            center=(x, y, half + D.gasket_t / 2.0),
        )
    return _require_single_solid(gasket.clean().fix(), feature="tower flange gasket")


def _acoustic_domain() -> Part:
    half = P.cube_outer / 2.0
    wall_stack = P.outer_skin_t + P.void_t + P.inner_skin_t
    cavity_side = P.cube_outer - 2.0 * wall_stack
    front_inner_y = -half + P.front_cap_t
    rear_inner_y = half - P.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    cavity = Pos(0.0, (front_inner_y + rear_inner_y) / 2.0, 0.0) * Box(
        cavity_side,
        cavity_y,
        cavity_side,
    )
    relief = _front_tool_global_oriented(
        _inner_relief_tool(P, FINAL_200_VARIANT),
        P,
        FINAL_200_VARIANT,
    )
    relief_clip = Pos(0.0, -half + P.front_cap_t / 2.0, 0.0) * Box(
        cavity_side,
        P.front_cap_t + 0.5,
        cavity_side,
    )
    return _primary_shape(cavity + _primary_shape(relief & relief_clip))


def _subtract_and_measure(volume: Part, shape: Any) -> tuple[Part, float]:
    before = volume.volume
    result = _primary_shape(volume - shape)
    return result, max(0.0, before - result.volume)


def _placed_horn_and_de250() -> tuple[Part, Any, dict[str, Any]]:
    horn = Rot(90.0, 0.0, 0.0) * (Rot(0.0, 0.0, -60.0) * build_final_horn())
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

    de250_raw = import_step(ROOT / "objects" / "Compression DriverDE250.step")
    de250 = Location(
        (D.horn_center_x, D.horn_mount_face_y, D.horn_center_z)
    ) * (Rot(90.0, 0.0, 0.0) * de250_raw)
    return placed_horn, de250, {
        "requested_wording_checked": (
            "No BMC component exists; the supplied and fitted component is B&C DE250."
        ),
        "compression_driver_source": "objects/Compression DriverDE250.step",
        "horn_source": "src.final_horn.build / current JMLC profile",
        "centered_open_top_half_cup_replaces_folded_bracket": True,
        "clamp_stack_mm": {
            "ring_front_y": D.horn_mount_face_y - D.horn_face_t,
            "ring_rear_y": D.horn_mount_face_y,
            "horn_spigot_rear_y": round(placed_horn.bounding_box().max.Y, 4),
            "de250_mount_face_y": D.horn_mount_face_y,
            "ring_thickness": D.horn_face_t,
        },
        "cradle": {
            "front_mount_ring_diameter_mm": 2.0 * D.horn_mount_ring_r,
            "inner_diameter_mm": 2.0 * D.horn_cup_inner_r,
            "outer_diameter_mm": 2.0 * D.horn_cup_outer_r,
            "open_top_z_mm": D.horn_center_z + D.horn_cup_open_above_center,
            "rear_y_mm": D.horn_cup_rear_y,
            "tube_front_y_mm": D.port_y - D.port_outer_r,
            "tube_overlap_mm": D.horn_cup_tube_overlap,
        },
    }


def _volume_accounting(
    *,
    base: Part,
    baseline: Part,
    baseline_diagnostics: dict[str, Any],
    port_outer_envelope: Part,
    woofer: Any,
    gx16: Any,
    binding_posts: list[Any],
    passive_radiator: Any,
) -> dict[str, Any]:
    domain = _acoustic_domain()
    gross_l = domain.volume / 1_000_000.0

    air = _primary_shape(domain - base)
    base_displacement_mm3 = domain.volume - air.volume
    stages: dict[str, float] = {}
    air, stages["e150he_44"] = _subtract_and_measure(air, woofer)
    air, stages["gx16"] = _subtract_and_measure(air, gx16)
    for binding_post in binding_posts:
        air, displacement = _subtract_and_measure(air, binding_post)
        stages["binding_posts"] = stages.get("binding_posts", 0.0) + displacement
    air, stages["internal_port_outer_envelope_including_port_air"] = (
        _subtract_and_measure(air, port_outer_envelope)
    )
    final_net_l = air.volume / 1_000_000.0

    current = _primary_shape(domain - baseline)
    current, _ = _subtract_and_measure(current, woofer)
    current, _ = _subtract_and_measure(current, gx16)
    for binding_post in binding_posts:
        current, _ = _subtract_and_measure(current, binding_post)
    current_before_pr = current.volume
    current, pr_displacement = _subtract_and_measure(current, passive_radiator)
    current_net_l = current.volume / 1_000_000.0

    brace_l = baseline_diagnostics["total_internal_brace_cavity_displacement_l"]
    other_base_l = max(0.0, base_displacement_mm3 / 1_000_000.0 - brace_l)
    return {
        "method": (
            "Exact OpenCascade boolean volume of the modeled cavity plus front relief, "
            "sequentially subtracting the finished base, supplied STEP hardware, and the "
            "complete in-box outer envelope of the port (including its acoustic air slug)."
        ),
        "gross_cavity_plus_front_relief_l": gross_l,
        "existing_braces_l": brace_l,
        "other_base_intrusions_including_receiver_l": other_base_l,
        "base_structure_total_l": base_displacement_mm3 / 1_000_000.0,
        "e150he_44_step_displacement_l": stages["e150he_44"] / 1_000_000.0,
        "gx16_step_displacement_l": stages["gx16"] / 1_000_000.0,
        "binding_posts_step_displacement_l": stages.get("binding_posts", 0.0)
        / 1_000_000.0,
        "internal_port_envelope_displacement_l": stages[
            "internal_port_outer_envelope_including_port_air"
        ]
        / 1_000_000.0,
        "final_net_box_volume_l": final_net_l,
        "current_passive_radiator_arrangement": {
            "air_volume_before_pr_displacement_l": current_before_pr / 1_000_000.0,
            "pr_step_displacement_l": pr_displacement / 1_000_000.0,
            "net_box_volume_l": current_net_l,
        },
    }


def _vented_response(net_box_l: float, effective_length_mm: float) -> dict[str, Any]:
    rho = D.air_density_kg_m3
    c = D.speed_of_sound_m_s
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    acoustic_mass = rho * (effective_length_mm / 1000.0) / area_m2
    port_loss_q = 10.0
    port_resistance = (
        2.0 * math.pi * D.target_tuning_hz * acoustic_mass / port_loss_q
    )
    rms = 1.0 / (
        2.0
        * math.pi
        * E150["fs_hz"]
        * E150["cms_m_n"]
        * E150["qms"]
    )

    def state(frequency_hz: float, power_w: float) -> dict[str, float]:
        omega = 2.0 * math.pi * frequency_hz
        z_port = port_resistance + 1j * omega * acoustic_mass
        box_compliance = volume_m3 / (rho * c * c)
        z_box = 1.0 / (1j * omega * box_compliance + 1.0 / z_port)
        z_mechanical = (
            rms
            + 1j * omega * E150["mms_kg"]
            + 1.0 / (1j * omega * E150["cms_m_n"])
            + E150["sd_m2"] ** 2 * z_box
        )
        z_electrical = E150["re_ohm"] + 1j * omega * E150["le_h"]
        voltage = math.sqrt(power_w * E150["re_ohm"])
        current = voltage / (
            z_electrical + E150["bl_tm"] ** 2 / z_mechanical
        )
        cone_velocity = E150["bl_tm"] * current / z_mechanical
        box_pressure = z_box * E150["sd_m2"] * cone_velocity
        port_volume_velocity = box_pressure / z_port
        port_velocity = abs(port_volume_velocity / area_m2)
        excursion_mm = abs(cone_velocity / omega) * 1000.0
        # v is positive into the box, so the forward cone source is -Sd*v.
        radiated_volume_velocity = port_volume_velocity - E150["sd_m2"] * cone_velocity
        far_pressure = abs(1j * omega * rho * radiated_volume_velocity / (2.0 * math.pi))
        spl_db_1m = 20.0 * math.log10(max(far_pressure, 1e-12) / 20e-6)
        return {
            "frequency_hz": frequency_hz,
            "cone_excursion_mm": excursion_mm,
            "port_velocity_m_s": port_velocity,
            "port_mach": port_velocity / c,
            "ideal_half_space_spl_db_1m": spl_db_1m,
        }

    powers: dict[str, Any] = {}
    for power in (25.0, 50.0, 100.0, 200.0):
        sweep = [state(15.0 + index * 0.1, power) for index in range(1051)]
        peak_port = max(sweep, key=lambda row: row["port_velocity_m_s"])
        peak_excursion = max(sweep, key=lambda row: row["cone_excursion_mm"])
        samples = [state(frequency, power) for frequency in (20, 30, 35, 40, 43, 50, 60, 80)]
        powers[f"{int(power)}_w"] = {
            "input_voltage_v_rms_series_coils": math.sqrt(power * E150["re_ohm"]),
            "peak_port_velocity": peak_port,
            "peak_cone_excursion_15_to_120_hz": peak_excursion,
            "samples": samples,
        }

    reference_sweep = [state(15.0 + index * 0.1, 1.0) for index in range(1051)]
    passband_rows = [
        row
        for row in reference_sweep
        if 70.0 <= row["frequency_hz"] <= 100.0
    ]
    passband_db = sum(row["ideal_half_space_spl_db_1m"] for row in passband_rows) / len(
        passband_rows
    )
    threshold = passband_db - 3.0
    f3 = next(
        row["frequency_hz"]
        for row in reference_sweep
        if row["ideal_half_space_spl_db_1m"] >= threshold
    )
    return {
        "model": (
            "Small-signal electro-mechano-acoustic lumped model using Dayton's series-coil "
            "T/S parameters, a rigid final net volume, and port loss Q=10. No room gain, "
            "thermal compression, nonlinear suspension, or crossover response is included."
        ),
        "port_loss_q_assumption": port_loss_q,
        "predicted_f3_hz": f3,
        "passband_reference_70_100_hz_db": passband_db,
        "power_cases": powers,
        "recommended_protection": (
            "Use a 4th-order high-pass at 28-30 Hz. The 100 W model exceeds 14.7 mm "
            "Xmax near 20 Hz without that protection; 200 W is thermal capability, not a "
            "safe unfiltered low-frequency operating point for this ported enclosure."
        ),
    }


def _passive_radiator_comparison(current_net_l: float) -> dict[str, Any]:
    volume_m3 = current_net_l / 1000.0
    box_stiffness_n_m = (
        D.air_density_kg_m3
        * D.speed_of_sound_m_s**2
        * E180_PR["sd_m2"] ** 2
        / volume_m3
    )
    suspension_stiffness_n_m = 1.0 / E180_PR["cmpr_m_n"]
    cases = []
    for disks, mass_g in zip(E180_PR["added_disks"], E180_PR["mass_cases_g"]):
        system_hz = math.sqrt(
            (box_stiffness_n_m + suspension_stiffness_n_m) / (mass_g / 1000.0)
        ) / (2.0 * math.pi)
        cases.append(
            {
                "added_disks": disks,
                "moving_mass_g": mass_g,
                "estimated_box_loaded_resonance_hz": system_hz,
            }
        )
    return {
        "method": (
            "Linear PR moving-mass/suspension resonance with the measured current net box "
            "air stiffness. It does not infer which of the three supplied mass disks is "
            "installed in the existing design."
        ),
        "current_net_volume_l": current_net_l,
        "cases": cases,
        "manufacturer_vd_cm3": E180_PR["vd_cm3"],
        "active_driver_vd_cm3": E150["vd_cm3"],
        "pr_to_driver_vd_ratio": E180_PR["vd_cm3"] / E150["vd_cm3"],
        "comparison": (
            "The PR eliminates chuffing, pipe resonance, and the long duct displacement, "
            "and its 258.59 cm3 displacement is 1.85x the woofer's published Vd. The port "
            "has fixed repeatable tuning and an upward outlet, but becomes velocity-limited "
            "before the E150HE-44 reaches its 200 W thermal rating."
        ),
    }


def _sand_void_seal_check(base: Part, airway: Part) -> dict[str, Any]:
    half = P.cube_outer / 2.0
    shell_span = P.cube_outer - 2.0 * P.outer_skin_t
    front_inner_y = -half + P.front_cap_t
    rear_inner_y = half - P.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    nominal_top_void = Pos(
        0.0,
        (front_inner_y + rear_inner_y) / 2.0,
        half - P.outer_skin_t - P.void_t / 2.0,
    ) * Box(shell_span, cavity_y, P.void_t)
    receiver_exclusion = _oriented_cylinder(
        diameter=2.0 * D.receiver_r,
        depth=half - D.receiver_bottom_z,
        axis="z",
        center=(D.port_x, D.port_y, (half + D.receiver_bottom_z) / 2.0),
    )
    residual_sand_void = _primary_shape(nominal_top_void - receiver_exclusion)
    airway_to_sand_overlap = _intersection_volume(airway, residual_sand_void)
    if airway_to_sand_overlap > 0.001:
        raise ValueError(
            "Port airway overlaps residual top sand void by "
            f"{airway_to_sand_overlap:.6f} mm^3"
        )
    return {
        "sealed_receiver_outer_radius_mm": D.receiver_r,
        "receiver_bore_radius_mm": D.receiver_bore_r,
        "minimum_radial_seal_wall_mm": D.receiver_r - D.receiver_bore_r,
        "airway_overlap_with_residual_sand_void_mm3": airway_to_sand_overlap,
        "gasket_land": "0.8 mm flat annular gasket between z=100.0 and tower flange",
        "attachment_pockets": (
            "Three 4.8 mm blind heat-set pockets stop at z=93.5, above the cavity and "
            "inside the locally solid receiver island."
        ),
        "base_valid_during_check": _is_valid(base),
    }


def _export_shapes(
    *,
    base: Part,
    tower: Part,
    gasket: Part,
    woofer: Any,
    gx16: Any,
    binding_posts: list[Any],
    horn: Any,
    de250: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    enclosure_port = Compound(
        children=[
            *_fresh_solids(base),
            *_fresh_solids(tower),
            *_fresh_solids(gasket),
        ]
    )
    hardware_check = Compound(
        children=[
            *_fresh_solids(base),
            *_fresh_solids(tower),
            *_fresh_solids(gasket),
            *_fresh_solids(woofer),
            *_fresh_solids(gx16),
            *[
                solid
                for binding_post in binding_posts
                for solid in _fresh_solids(binding_post)
            ],
            *_fresh_solids(horn),
            *_fresh_solids(de250),
        ]
    )
    shapes = {
        "sand_cube_200_port_tower_base.step": base,
        "sand_cube_200_port_tower.step": tower,
        "sand_cube_200_port_tower_gasket.step": gasket,
        "sand_cube_200_port_tower_assembly.step": enclosure_port,
        "sand_cube_200_port_tower_hardware_check.step": hardware_check,
    }
    return shapes, {
        "enclosure_port": enclosure_port,
        "hardware_check": hardware_check,
    }


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    base, baseline, baseline_diagnostics = build_base_enclosure()
    woofer = _confirmed_woofer(P)
    gx16, gx16_data = _placed_gx16(P)
    binding_posts = _relocated_binding_posts()
    passive_radiator = _confirmed_passive_radiator(P)

    # Net volume is independent of tower length above the cavity, so a generous
    # provisional outlet can be used for the exact in-box displacement pass.
    _provisional_tower, _provisional_airway, provisional_outer, _ = build_tower(
        300.0
    )
    volume_data = _volume_accounting(
        base=base,
        baseline=baseline,
        baseline_diagnostics=baseline_diagnostics,
        port_outer_envelope=provisional_outer,
        woofer=woofer,
        gx16=gx16,
        binding_posts=binding_posts,
        passive_radiator=passive_radiator,
    )
    length_data = _port_length_solution(volume_data["final_net_box_volume_l"])
    tower, airway, port_outer, tower_data = build_tower(length_data["outlet_z_mm"])
    gasket = build_gasket()
    horn, de250, horn_data = _placed_horn_and_de250()

    # Recompute the final volume against the actual final outer-envelope solid.
    volume_data = _volume_accounting(
        base=base,
        baseline=baseline,
        baseline_diagnostics=baseline_diagnostics,
        port_outer_envelope=port_outer,
        woofer=woofer,
        gx16=gx16,
        binding_posts=binding_posts,
        passive_radiator=passive_radiator,
    )
    final_length_data = _port_length_solution(volume_data["final_net_box_volume_l"])
    if abs(final_length_data["outlet_z_mm"] - length_data["outlet_z_mm"]) > 0.01:
        raise ValueError("Final net volume changed the solved port length unexpectedly")
    length_data = final_length_data

    base_tower_overlap = _intersection_volume(base, tower)
    airway_base_obstruction = _intersection_volume(base, airway)
    if base_tower_overlap > 0.001:
        raise ValueError(f"Base and tower overlap by {base_tower_overlap:.6f} mm^3")
    if airway_base_obstruction > 0.001:
        raise ValueError(
            f"Base obstructs the port airway by {airway_base_obstruction:.6f} mm^3"
        )

    # Front geometry is protected explicitly; all derivative modifications must
    # remain out of the woofer seat and mounting annulus zone.
    seat_protector = Pos(0.0, -90.0, 0.0) * Box(190.0, 20.0, 190.0)
    changed_front = _intersection_volume(_primary_shape(base - baseline), seat_protector)
    changed_front += _intersection_volume(_primary_shape(baseline - base), seat_protector)
    if changed_front > 0.001:
        raise ValueError(
            f"Derivative changes reached the woofer/front zone by {changed_front:.6f} mm^3"
        )

    interference = {
        "base_to_tower_mm3": base_tower_overlap,
        "airway_to_base_obstruction_mm3": airway_base_obstruction,
        "airway_to_tower_obstruction_mm3": _intersection_volume(airway, tower),
        "tower_to_woofer_mm3": _intersection_volume(tower, woofer),
        "tower_to_gx16_mm3": _intersection_volume(tower, gx16),
        "tower_to_binding_posts_mm3": sum(
            _intersection_volume(tower, post) for post in binding_posts
        ),
        "tower_to_horn_mm3": _intersection_volume(tower, horn),
        "tower_to_de250_mm3": _intersection_volume(tower, de250),
        "base_to_horn_mm3": _intersection_volume(base, horn),
        "front_woofer_zone_changed_mm3": changed_front,
    }
    unresolved = {
        key: value
        for key, value in interference.items()
        if value > 0.001
        and key
        not in {
            # The horn spigot and DE250 are intended to touch the two faces of
            # the 4 mm clamp pad, but volume overlap is still not permitted.
        }
    }
    if unresolved:
        raise ValueError(f"Unresolved hardware/port interference: {unresolved}")

    sand_seal = _sand_void_seal_check(base, airway)
    response = _vented_response(
        volume_data["final_net_box_volume_l"],
        length_data["effective_length_mm"],
    )
    pr_comparison = _passive_radiator_comparison(
        volume_data["current_passive_radiator_arrangement"]["net_box_volume_l"]
    )

    physical_length_m = length_data["physical_centerline_length_mm"] / 1000.0
    quarter_wave_hz = D.speed_of_sound_m_s / (4.0 * physical_length_m)
    half_wave_hz = D.speed_of_sound_m_s / (2.0 * physical_length_m)
    shape_exports, assemblies = _export_shapes(
        base=base,
        tower=tower,
        gasket=gasket,
        woofer=woofer,
        gx16=gx16,
        binding_posts=binding_posts,
        horn=horn,
        de250=de250,
    )
    for filename, shape in shape_exports.items():
        export_step(shape, OUT / filename, unit=Unit.MM, write_pcurves=False)

    viewer_out = OUT / "viewer"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
            str(OUT / "sand_cube_200_port_tower_assembly.step"),
            "--out",
            str(viewer_out),
        ],
        check=True,
    )

    diagnostics: dict[str, Any] = {
        "name": D.name,
        "isolation": {
            "experiment_dir": "experiments/sand_cube_200_port_tower",
            "output_dir": "build/sand_cube_200_port_tower",
            "baseline": (
                "FINAL_200_VARIANT imported read-only from experiments/"
                "sand_cube_8_5_black_hole/generate_contoured_inner_variants.py"
            ),
            "existing_final_files_modified": False,
        },
        "manufacturer_sources": {
            "e150he_44_specification_sheet": E150_SOURCE_URL,
            "e150he_44_product_page": E150_PRODUCT_URL,
            "e180he_pr_specification_sheet": E180_PR_SOURCE_URL,
            "e150he_44_parameters": E150,
            "e180he_pr_parameters": E180_PR,
        },
        "alignment": {
            "selected_type": "conventional bass-reflex Helmholtz resonator",
            "target_tuning_hz": D.target_tuning_hz,
            "calculated_tuning_hz": length_data["calculated_tuning_hz"],
            "why_not_quarter_wave": (
                "A 43 Hz quarter-wave line is "
                f"{D.speed_of_sound_m_s / (4 * D.target_tuning_hz):.3f} m, "
                "far longer than this enclosure/tower. The final duct is the acoustic mass "
                "working against box compliance; its line-mode frequencies are parasitic."
            ),
            "predicted_f3_hz": response["predicted_f3_hz"],
        },
        "volume_accounting": volume_data,
        "port": {
            "cross_section_area_mm2": D.port_area_mm2,
            "equivalent_diameter_mm": D.port_d,
            "wall_thickness_mm": D.port_wall_t,
            "center_xy_mm": [D.port_x, D.port_y],
            "inlet_z_mm": D.inlet_z,
            "outlet_z_mm": length_data["outlet_z_mm"],
            "visible_height_above_enclosure_mm": length_data["outlet_z_mm"]
            - P.cube_outer / 2.0,
            "visible_height_above_enclosure_in": (
                length_data["outlet_z_mm"] - P.cube_outer / 2.0
            )
            / 25.4,
            "inlet_flare_mouth_d_mm": 2.0 * D.inlet_mouth_r,
            "outlet_flare_mouth_d_mm": 2.0 * D.outlet_mouth_r,
            "lengths": length_data,
            "bends": {
                "count": 0,
                "bend_centerline_radius_mm": None,
                "bend_area_correction": 0.0,
                "reason": (
                    "The laterally centered, aft straight route clears the woofer, GX16, "
                    "relocated binding posts, sand fills, and bottom tripod area. Its swept "
                    "envelope locally clears the crossed center/waist rails while retaining "
                    "their wall contacts. Avoiding bends also avoids separation and unknown "
                    "inertance corrections."
                ),
            },
            "first_quarter_wave_line_mode_hz": quarter_wave_hz,
            "first_half_wave_line_mode_hz": half_wave_hz,
            "midrange_leakage_risk": (
                "Material: the first duct mode falls in the upper-bass/lower-midrange region. "
                "The inlet is aft of the cone motor and not in direct line with the cone, but absorptive "
                "lining on the opposing cavity walls and an appropriate woofer-to-horn low-pass "
                "remain necessary. Do not put damping material inside the duct."
            ),
        },
        "response_and_velocity": response,
        "passive_radiator_comparison": pr_comparison,
        "geometry": {
            "base_bbox": _bbox(base),
            "tower_bbox": _bbox(tower),
            "gasket_bbox": _bbox(gasket),
            "enclosure_port_bbox": _bbox(assemblies["enclosure_port"]),
            "hardware_check_bbox": _bbox(assemblies["hardware_check"]),
            "assembled_enclosure_port_height_mm": assemblies[
                "enclosure_port"
            ].bounding_box().size.Z,
            "complete_hardware_check_height_mm": assemblies[
                "hardware_check"
            ].bounding_box().size.Z,
            "solid_counts": {
                "base": len(base.solids()),
                "tower": len(tower.solids()),
                "gasket": len(gasket.solids()),
                "enclosure_port_assembly": len(assemblies["enclosure_port"].solids()),
                "hardware_check_assembly": len(assemblies["hardware_check"].solids()),
                "airway": len(airway.solids()),
            },
            "validity": {
                "base": _is_valid(base),
                "tower": _is_valid(tower),
                "gasket": _is_valid(gasket),
                "airway": _is_valid(airway),
            },
            "interference_mm3": interference,
            "port_continuity": {
                "airway_solid_count": len(airway.solids()),
                "airway_valid": _is_valid(airway),
                "airway_obstruction_mm3": _intersection_volume(
                    Compound(children=[*_fresh_solids(base), *_fresh_solids(tower)]),
                    airway,
                ),
            },
            "sand_void_seal": sand_seal,
            "brace_changes": {
                "transverse_window_frame": "unchanged",
                "vertical_center_rails": (
                    f"Aft rail locally cleared by the centered {2 * D.port_outer_r + D.waist_brace_clearance_extra_d:.3f} mm "
                    "swept envelope; both original wall contacts retained."
                ),
                "horizontal_waist_rails": (
                    f"Local {2 * D.port_outer_r + D.waist_brace_clearance_extra_d:.3f} mm "
                    f"diameter clearance at x={D.port_x}, y={D.port_y}; "
                    "both wall contacts retained."
                ),
            },
            "rear_wall": {
                "passive_radiator_cutout_removed": True,
                "passive_radiator_recess_removed": True,
                "passive_radiator_insert_bores_removed": True,
                "rear_cap_thickness_mm": P.rear_cap_t,
            },
            "horn_and_de250": horn_data,
            "binding_posts": {
                "relocated_positions_xy_mm": [
                    [-P.binding_post_spacing / 2.0, D.binding_post_y],
                    [P.binding_post_spacing / 2.0, D.binding_post_y],
                ],
                "original_pilots_restored": True,
                "new_connected_island_depth_mm": D.binding_island_d,
            },
            "gx16": gx16_data,
        },
        "manufacturing": {
            "base_print_orientation": "rear face down, unchanged from the baseline intent",
            "integral_tower_rejected": (
                "A 300+ mm integral duct would be a long horizontal internal bridge when the "
                "base is printed rear-face-down and would also make service access impractical."
            ),
            "tower_print_orientation": (
                "Print upright from the broad inlet flare with a brim. The bore remains vertical; "
                "the open-top horn cup needs localized removable support beneath its front ring, "
                "while the cup and both flares use continuous curved profiles."
            ),
            "joint": (
                "Deep 0.30 mm radial-clearance spigot through a solid receiver, 0.8 mm flat "
                "gasket, 64 mm flange, and three M4 clearance holes into blind 4.8 mm "
                "heat-set-insert pockets."
            ),
            "remaining_risks": [
                "The tall, narrow tower needs a brim and conservative acceleration while printing.",
                (
                    "The integrated plastic half-cup preserves the 4 mm clamp stack and exact "
                    "DE250 fit, but still needs a physical proof-load before service."
                ),
                (
                    "At 100 W the port is near the conventional Mach 0.10 "
                    "compression/chuffing boundary; 200 W is not a low-noise "
                    "operating point."
                ),
                (
                    "The long straight duct has an audible-frequency pipe mode and "
                    "must be managed with crossover and cavity lining."
                ),
            ],
        },
        "files": {
            **{key: str(OUT / key) for key in shape_exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "static_viewer": str(viewer_out / "viewer" / "index.html"),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
