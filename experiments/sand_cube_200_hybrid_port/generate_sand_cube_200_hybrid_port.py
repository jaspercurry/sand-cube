"""Generate a first-pass 38 Hz folded-reflex Sand Cube concept.

This is deliberately isolated from the validated 43 Hz straight-tower study.
The acoustic path is a wide rounded-rectangular duct with one 180 degree return
inside the enclosure and an upward outlet behind the compression driver.
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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Unit,
    add,
    export_step,
    extrude,
    fillet,
    loft,
)


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.sand_cube_200_port_tower import (  # noqa: E402
    generate_sand_cube_200_port_tower as common,
)
from experiments.sand_cube_8_5_black_hole.generate_contoured_inner_variants import (  # noqa: E402
    FINAL_200_VARIANT,
    _confirmed_binding_posts,
    _confirmed_passive_radiator,
    _confirmed_woofer,
    _final_params,
    _intersection_volume,
    _oriented_cylinder,
    _primary_shape,
    _require_single_solid,
    _placed_gx16,
    build_variant,
)


OUT = ROOT / "build" / "sand_cube_200_hybrid_port"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_200_hybrid_port_38hz"
    target_tuning_hz: float = 38.0
    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204

    # The 80 x 15 mm throat is intentionally broad and shallow.  Its 1,200
    # mm2 area is slightly larger than the straight 43 Hz study while its
    # 86.4 mm outside width remains well inside the DE250 cradle width.
    port_width: float = 80.0
    port_depth: float = 15.0
    port_wall_t: float = 3.2
    throat_corner_r: float = 4.0
    front_lane_y: float = 45.0
    rear_lane_y: float = 75.0
    bend_center_y: float = 60.0
    bend_center_z: float = -56.0
    bend_centerline_r: float = 15.0

    inlet_mouth_z: float = 82.0
    inlet_flare_l: float = 14.0
    inlet_mouth_width: float = 100.0
    inlet_mouth_depth: float = 34.0
    inlet_mouth_corner_r: float = 10.0
    outlet_flare_l: float = 25.0
    outlet_mouth_width: float = 110.0
    outlet_mouth_depth: float = 44.0
    outlet_mouth_corner_r: float = 12.0
    inlet_end_correction_factor: float = 0.85
    outlet_end_correction_factor: float = 0.613

    # The top joint is intentionally simple for the concept.  The complete U
    # cannot yet be installed through this opening; the eventual print split is
    # left visible as an assembly decision rather than hidden in this pass.
    receiver_w: float = 114.0
    receiver_d: float = 52.0
    receiver_corner_r: float = 8.0
    receiver_bottom_z: float = 82.0
    spigot_clearance: float = 0.30
    flange_w: float = 116.0
    flange_d: float = 52.0
    flange_corner_r: float = 8.0
    flange_t: float = 5.0
    gasket_t: float = 0.8
    tower_bolt_clearance_d: float = 4.5
    base_insert_pocket_d: float = 4.8
    base_insert_pocket_depth: float = 6.5

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

    binding_post_y: float = 5.0
    binding_island_d: float = 26.0
    binding_island_corner_r: float = 5.0

    @property
    def port_area_mm2(self) -> float:
        return self.port_width * self.port_depth

    @property
    def outer_width(self) -> float:
        return self.port_width + 2.0 * self.port_wall_t

    @property
    def outer_depth(self) -> float:
        return self.port_depth + 2.0 * self.port_wall_t

    # Compatibility names used by the shared DE250 cradle diagnostics.
    @property
    def port_y(self) -> float:
        return self.rear_lane_y

    @property
    def port_outer_r(self) -> float:
        return self.outer_depth / 2.0

    @property
    def horn_cup_rear_y(self) -> float:
        return (
            self.rear_lane_y
            - self.outer_depth / 2.0
            + self.horn_cup_tube_overlap
        )


D = Design()
P = _final_params(FINAL_200_VARIANT)

# Reuse the already-audited hardware placement, volume, response, and DE250
# cup helpers against this experiment's immutable dimensions.
common.D = D
common.P = P


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
    return [
        (-48.0, D.rear_lane_y - 17.0),
        (48.0, D.rear_lane_y - 17.0),
        (-48.0, D.rear_lane_y + 17.0),
        (48.0, D.rear_lane_y + 17.0),
    ]


def _rounded_prism(
    *, width: float, depth: float, height: float, y: float, z0: float, corner_r: float
) -> Part:
    with BuildPart() as result:
        with BuildSketch(Plane.XY.offset(z0)) as sketch:
            with Locations((0.0, y)):
                RectangleRounded(width, depth, corner_r)
        assert sketch.sketch.area > 0, "Rounded prism sketch area must be positive"
        extrude(amount=height)
    return _require_single_solid(result.part.clean().fix(), feature="rounded prism")


def _rounded_loft(
    *,
    z0: float,
    z1: float,
    y: float,
    width0: float,
    depth0: float,
    corner0: float,
    width1: float,
    depth1: float,
    corner1: float,
) -> Part:
    with BuildPart() as result:
        for index in range(7):
            t = index / 6.0
            blend = t * t * (3.0 - 2.0 * t)
            z = z0 + (z1 - z0) * t
            width = width0 + (width1 - width0) * blend
            depth = depth0 + (depth1 - depth0) * blend
            corner = corner0 + (corner1 - corner0) * blend
            with BuildSketch(Plane.XY.offset(z)) as section:
                with Locations((0.0, y)):
                    RectangleRounded(width, depth, corner)
            assert section.sketch.area > 0, "Port loft section area must be positive"
        loft()
    return _require_single_solid(result.part.clean().fix(), feature="rounded flare loft")


def _half_annulus(*, width: float, inner_r: float, outer_r: float) -> Part:
    outer = _oriented_cylinder(
        diameter=2.0 * outer_r,
        depth=width,
        axis="x",
        center=(0.0, D.bend_center_y, D.bend_center_z),
    )
    inner = _oriented_cylinder(
        diameter=2.0 * inner_r,
        depth=width + 2.0,
        axis="x",
        center=(0.0, D.bend_center_y, D.bend_center_z),
    )
    clip = Pos(
        0.0,
        D.bend_center_y,
        D.bend_center_z - outer_r / 2.0,
    ) * Box(width + 2.0, 2.0 * outer_r + 2.0, outer_r + 0.02)
    return _require_single_solid(
        _primary_shape((outer - inner) & clip).clean().fix(),
        feature="folded-port half-annulus",
    )


def _fuse_connected(parts: list[Part], *, feature: str) -> Part:
    result = parts[0]
    for part in parts[1:]:
        # Boolean addition is more reliable than BRepAlgoAPI glue for the
        # broad face-overlap between the rectangular outlet leg and flange.
        result = (result + part).clean().fix()
    return _require_single_solid(result, feature=feature)


def _path_solids(outlet_z: float) -> tuple[Part, Part]:
    inlet_throat_z = D.inlet_mouth_z - D.inlet_flare_l
    outlet_throat_z = outlet_z - D.outlet_flare_l
    if outlet_throat_z <= D.inlet_mouth_z:
        raise ValueError("Outlet throat must remain above the enclosure")

    air_half_depth = D.port_depth / 2.0
    air_inner_r = D.bend_centerline_r - air_half_depth
    air_outer_r = D.bend_centerline_r + air_half_depth
    shell_inner_r = air_inner_r - D.port_wall_t
    shell_outer_r = air_outer_r + D.port_wall_t

    inner_front = _rounded_prism(
        width=D.port_width,
        depth=D.port_depth,
        height=inlet_throat_z - D.bend_center_z,
        y=D.front_lane_y,
        z0=D.bend_center_z,
        corner_r=D.throat_corner_r,
    )
    inner_rear = _rounded_prism(
        width=D.port_width,
        depth=D.port_depth,
        height=outlet_throat_z - D.bend_center_z,
        y=D.rear_lane_y,
        z0=D.bend_center_z,
        corner_r=D.throat_corner_r,
    )
    inner_bend = _half_annulus(
        width=D.port_width, inner_r=air_inner_r, outer_r=air_outer_r
    )
    inner_inlet = _rounded_loft(
        z0=inlet_throat_z,
        z1=D.inlet_mouth_z,
        y=D.front_lane_y,
        width0=D.port_width,
        depth0=D.port_depth,
        corner0=D.throat_corner_r,
        width1=D.inlet_mouth_width,
        depth1=D.inlet_mouth_depth,
        corner1=D.inlet_mouth_corner_r,
    )
    inner_outlet = _rounded_loft(
        z0=outlet_throat_z,
        z1=outlet_z,
        y=D.rear_lane_y,
        width0=D.port_width,
        depth0=D.port_depth,
        corner0=D.throat_corner_r,
        width1=D.outlet_mouth_width,
        depth1=D.outlet_mouth_depth,
        corner1=D.outlet_mouth_corner_r,
    )
    airway = _fuse_connected(
        [inner_front, inner_bend, inner_rear, inner_inlet, inner_outlet],
        feature="continuous folded airway",
    )

    outer_front = _rounded_prism(
        width=D.outer_width,
        depth=D.outer_depth,
        height=inlet_throat_z - D.bend_center_z,
        y=D.front_lane_y,
        z0=D.bend_center_z,
        corner_r=D.throat_corner_r + D.port_wall_t,
    )
    outer_rear = _rounded_prism(
        width=D.outer_width,
        depth=D.outer_depth,
        height=outlet_throat_z - D.bend_center_z,
        y=D.rear_lane_y,
        z0=D.bend_center_z,
        corner_r=D.throat_corner_r + D.port_wall_t,
    )
    outer_bend = _half_annulus(
        width=D.outer_width, inner_r=shell_inner_r, outer_r=shell_outer_r
    )
    outer_inlet = _rounded_loft(
        z0=inlet_throat_z,
        z1=D.inlet_mouth_z,
        y=D.front_lane_y,
        width0=D.outer_width,
        depth0=D.outer_depth,
        corner0=D.throat_corner_r + D.port_wall_t,
        width1=D.inlet_mouth_width + 2.0 * D.port_wall_t,
        depth1=D.inlet_mouth_depth + 2.0 * D.port_wall_t,
        corner1=D.inlet_mouth_corner_r + D.port_wall_t,
    )
    outer_outlet = _rounded_loft(
        z0=outlet_throat_z,
        z1=outlet_z,
        y=D.rear_lane_y,
        width0=D.outer_width,
        depth0=D.outer_depth,
        corner0=D.throat_corner_r + D.port_wall_t,
        width1=D.outlet_mouth_width + 2.0 * D.port_wall_t,
        depth1=D.outlet_mouth_depth + 2.0 * D.port_wall_t,
        corner1=D.outlet_mouth_corner_r + D.port_wall_t,
    )
    outer_envelope = _fuse_connected(
        [outer_front, outer_bend, outer_rear, outer_inlet, outer_outlet],
        feature="continuous folded duct outer envelope",
    )
    return airway, outer_envelope


def _flare_equivalent_length_mm(
    *, width0: float, depth0: float, width1: float, depth1: float, length: float
) -> float:
    steps = 4000
    throat_area = width0 * depth0
    total = 0.0
    for index in range(steps):
        t = (index + 0.5) / steps
        blend = t * t * (3.0 - 2.0 * t)
        width = width0 + (width1 - width0) * blend
        depth = depth0 + (depth1 - depth0) * blend
        total += throat_area / (width * depth)
    return length * total / steps


def _port_length_solution(net_box_l: float) -> dict[str, float]:
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    required_effective_mm = 1000.0 * (
        D.speed_of_sound_m_s**2
        * area_m2
        / ((2.0 * math.pi * D.target_tuning_hz) ** 2 * volume_m3)
    )
    inlet_equiv = _flare_equivalent_length_mm(
        width0=D.port_width,
        depth0=D.port_depth,
        width1=D.inlet_mouth_width,
        depth1=D.inlet_mouth_depth,
        length=D.inlet_flare_l,
    )
    outlet_equiv = _flare_equivalent_length_mm(
        width0=D.port_width,
        depth0=D.port_depth,
        width1=D.outlet_mouth_width,
        depth1=D.outlet_mouth_depth,
        length=D.outlet_flare_l,
    )
    inlet_equiv_r = math.sqrt(D.inlet_mouth_width * D.inlet_mouth_depth / math.pi)
    outlet_equiv_r = math.sqrt(
        D.outlet_mouth_width * D.outlet_mouth_depth / math.pi
    )
    inlet_end = D.inlet_end_correction_factor * inlet_equiv_r
    outlet_end = D.outlet_end_correction_factor * outlet_equiv_r
    front_straight = (
        D.inlet_mouth_z - D.inlet_flare_l - D.bend_center_z
    )
    bend_length = math.pi * D.bend_centerline_r
    rear_straight = (
        required_effective_mm
        - inlet_end
        - outlet_end
        - inlet_equiv
        - outlet_equiv
        - front_straight
        - bend_length
    )
    if rear_straight <= 0.0:
        raise ValueError("Solved rear folded-port leg is not positive")
    outlet_throat_z = D.bend_center_z + rear_straight
    outlet_z = outlet_throat_z + D.outlet_flare_l
    physical_length = (
        D.inlet_flare_l
        + front_straight
        + bend_length
        + rear_straight
        + D.outlet_flare_l
    )
    area_corrected = (
        inlet_equiv + front_straight + bend_length + rear_straight + outlet_equiv
    )
    effective_check = area_corrected + inlet_end + outlet_end
    tuning_check = D.speed_of_sound_m_s / (2.0 * math.pi) * math.sqrt(
        area_m2 / (volume_m3 * effective_check / 1000.0)
    )
    return {
        "outlet_z_mm": outlet_z,
        "outlet_throat_z_mm": outlet_throat_z,
        "physical_centerline_length_mm": physical_length,
        "front_constant_area_length_mm": front_straight,
        "bend_centerline_length_mm": bend_length,
        "rear_constant_area_length_mm": rear_straight,
        "inlet_flare_area_equivalent_length_mm": inlet_equiv,
        "outlet_flare_area_equivalent_length_mm": outlet_equiv,
        "area_corrected_physical_length_mm": area_corrected,
        "inlet_end_correction_mm": inlet_end,
        "outlet_end_correction_mm": outlet_end,
        "effective_length_mm": effective_check,
        "calculated_tuning_hz": tuning_check,
    }


def _relocated_binding_posts() -> list[Any]:
    dy = D.binding_post_y - P.binding_post_y
    from build123d import Location

    return [Location((0.0, dy, 0.0)) * post for post in _confirmed_binding_posts(P)]


def build_base_enclosure(port_outer_envelope: Part) -> tuple[Part, Part, dict[str, Any]]:
    baseline, baseline_diagnostics = build_variant(FINAL_200_VARIANT)
    half = P.cube_outer / 2.0

    rear_closure = _oriented_cylinder(
        diameter=P.pr_recess_dia,
        depth=P.rear_cap_t,
        axis="y",
        center=(0.0, half - P.rear_cap_t / 2.0, 0.0),
    )
    base = baseline.fuse(rear_closure, glue=True, tol=0.01).clean().fix()
    base = _require_single_solid(base, feature="rear-closed hybrid-port base")

    binding_island, binding_pilots = common._binding_post_island_and_pilots()
    base = base.fuse(binding_island, glue=True, tol=0.01).clean().fix()
    for x in (-P.binding_post_spacing / 2.0, P.binding_post_spacing / 2.0):
        base += _oriented_cylinder(
            diameter=12.0,
            depth=18.0,
            axis="z",
            center=(x, P.binding_post_y, half - 9.0),
        )
    base = _require_single_solid(base.clean().fix(), feature="hybrid binding island")

    # Only the exact duct sweep is removed from the internal brace network.
    # The U is open through the acoustic cavity and does not create any closed
    # ribs in the sand void.
    brace_clearance = _primary_shape(port_outer_envelope & common._acoustic_domain())
    base -= brace_clearance
    base = _require_single_solid(base.clean().fix(), feature="hybrid brace clearance")

    receiver = _rounded_prism(
        width=D.receiver_w,
        depth=D.receiver_d,
        height=half - D.receiver_bottom_z,
        y=D.rear_lane_y,
        z0=D.receiver_bottom_z,
        corner_r=D.receiver_corner_r,
    )
    receiver = _primary_shape(receiver & _outer_envelope())
    base = base.fuse(receiver, glue=True, tol=0.01).clean().fix()

    receiver_bore = _rounded_prism(
        width=D.outer_width + 2.0 * D.spigot_clearance,
        depth=D.outer_depth + 2.0 * D.spigot_clearance,
        height=half - D.receiver_bottom_z + 4.0,
        y=D.rear_lane_y,
        z0=D.receiver_bottom_z - 2.0,
        corner_r=D.throat_corner_r + D.port_wall_t + D.spigot_clearance,
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
    base = _require_single_solid(base.clean().fix(), feature="finished hybrid-port base")
    return base, baseline, baseline_diagnostics


def build_tower(outlet_z: float) -> tuple[Part, Part, Part, dict[str, float]]:
    airway, outer_envelope = _path_solids(outlet_z)
    flange_bottom = P.cube_outer / 2.0 + D.gasket_t
    flange = _rounded_prism(
        width=D.flange_w,
        depth=D.flange_d,
        height=D.flange_t,
        y=D.rear_lane_y,
        z0=flange_bottom,
        corner_r=D.flange_corner_r,
    )
    cup = common._horn_cup()
    tower = _fuse_connected(
        [outer_envelope, flange, cup], feature="uncut hybrid tower and DE250 cradle"
    )
    tower -= airway
    tower -= common._horn_cup_cutouts()
    for x, y in _attachment_positions():
        tower -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.flange_t + 2.0,
            axis="z",
            center=(x, y, flange_bottom + D.flange_t / 2.0),
        )
    tower = _require_single_solid(tower.clean().fix(), feature="finished hybrid tower")
    if _intersection_volume(tower, airway) > 0.001:
        raise ValueError("Hybrid tower obstructs its acoustic airway")
    return tower, airway, outer_envelope, {
        "flange_bottom_z_mm": flange_bottom,
        "flange_top_z_mm": flange_bottom + D.flange_t,
        "outlet_z_mm": outlet_z,
        "horn_mount_center_z_mm": D.horn_center_z,
        "horn_cup_rear_y_mm": D.horn_cup_rear_y,
    }


def build_gasket() -> Part:
    gasket = _rounded_prism(
        width=D.flange_w - 1.0,
        depth=D.flange_d - 1.0,
        height=D.gasket_t,
        y=D.rear_lane_y,
        z0=P.cube_outer / 2.0,
        corner_r=D.flange_corner_r - 0.5,
    )
    gasket -= _rounded_prism(
        width=D.outer_width + 2.0 * D.spigot_clearance,
        depth=D.outer_depth + 2.0 * D.spigot_clearance,
        height=D.gasket_t + 2.0,
        y=D.rear_lane_y,
        z0=P.cube_outer / 2.0 - 1.0,
        corner_r=D.throat_corner_r + D.port_wall_t + D.spigot_clearance,
    )
    for x, y in _attachment_positions():
        gasket -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.gasket_t + 2.0,
            axis="z",
            center=(x, y, P.cube_outer / 2.0 + D.gasket_t / 2.0),
        )
    return _require_single_solid(gasket.clean().fix(), feature="hybrid tower gasket")


def _sand_void_seal_check(airway: Part) -> dict[str, Any]:
    half = P.cube_outer / 2.0
    shell_span = P.cube_outer - 2.0 * P.outer_skin_t
    front_inner_y = -half + P.front_cap_t
    rear_inner_y = half - P.rear_cap_t
    nominal_top_void = Pos(
        0.0,
        (front_inner_y + rear_inner_y) / 2.0,
        half - P.outer_skin_t - P.void_t / 2.0,
    ) * Box(shell_span, rear_inner_y - front_inner_y, P.void_t)
    receiver_exclusion = _rounded_prism(
        width=D.receiver_w,
        depth=D.receiver_d,
        height=half - D.receiver_bottom_z,
        y=D.rear_lane_y,
        z0=D.receiver_bottom_z,
        corner_r=D.receiver_corner_r,
    )
    residual_void = _primary_shape(nominal_top_void - receiver_exclusion)
    overlap = _intersection_volume(airway, residual_void)
    if overlap > 0.001:
        raise ValueError(f"Airway enters residual top sand void by {overlap:.6f} mm3")
    return {
        "airway_overlap_with_residual_top_sand_void_mm3": overlap,
        "receiver_size_mm": [D.receiver_w, D.receiver_d],
        "receiver_bottom_z_mm": D.receiver_bottom_z,
        "gasket_thickness_mm": D.gasket_t,
    }


def _cutaway_compound(base: Part, tower: Part, gasket: Part, airway: Part) -> Compound:
    bb = tower.bounding_box()
    clip = Pos(-50.0, 0.0, (bb.min.Z + bb.max.Z) / 2.0) * Box(
        100.0, 360.0, bb.size.Z + 20.0
    )
    base_half = base & clip
    tower_half = tower & clip
    gasket_half = gasket & clip
    return Compound(
        children=[
            *_fresh_solids(base_half),
            *_fresh_solids(tower_half),
            *_fresh_solids(gasket_half),
            *_fresh_solids(airway),
        ]
    )


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    provisional_airway, provisional_outer = _path_solids(280.0)
    base, baseline, baseline_diagnostics = build_base_enclosure(provisional_outer)
    woofer = _confirmed_woofer(P)
    gx16, gx16_data = _placed_gx16(P)
    binding_posts = _relocated_binding_posts()
    passive_radiator = _confirmed_passive_radiator(P)

    volume_data = common._volume_accounting(
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
    horn, de250, horn_data = common._placed_horn_and_de250()

    volume_data = common._volume_accounting(
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
        raise ValueError("Final net volume changed the solved folded-port length")
    length_data = final_length_data

    base_tower_overlap = _intersection_volume(base, tower)
    airway_base_obstruction = _intersection_volume(base, airway)
    airway_tower_obstruction = _intersection_volume(tower, airway)
    if base_tower_overlap > 0.001:
        raise ValueError(f"Base and tower overlap by {base_tower_overlap:.6f} mm3")
    if airway_base_obstruction > 0.001:
        raise ValueError(f"Base obstructs airway by {airway_base_obstruction:.6f} mm3")

    interference = {
        "base_to_tower_mm3": base_tower_overlap,
        "airway_to_base_mm3": airway_base_obstruction,
        "airway_to_tower_mm3": airway_tower_obstruction,
        "tower_to_woofer_mm3": _intersection_volume(tower, woofer),
        "tower_to_gx16_mm3": _intersection_volume(tower, gx16),
        "tower_to_binding_posts_mm3": sum(
            _intersection_volume(tower, post) for post in binding_posts
        ),
        "tower_to_horn_mm3": _intersection_volume(tower, horn),
        "tower_to_de250_mm3": _intersection_volume(tower, de250),
    }
    response = common._vented_response(
        volume_data["final_net_box_volume_l"], length_data["effective_length_mm"]
    )
    pr_comparison = common._passive_radiator_comparison(
        volume_data["current_passive_radiator_arrangement"]["net_box_volume_l"]
    )
    sand_seal = _sand_void_seal_check(airway)

    assembly = Compound(
        children=[*_fresh_solids(base), *_fresh_solids(tower), *_fresh_solids(gasket)]
    )
    hardware_check = Compound(
        children=[
            *_fresh_solids(base),
            *_fresh_solids(tower),
            *_fresh_solids(gasket),
            *_fresh_solids(woofer),
            *_fresh_solids(gx16),
            *[solid for post in binding_posts for solid in _fresh_solids(post)],
            *_fresh_solids(horn),
            *_fresh_solids(de250),
        ]
    )
    cutaway = _cutaway_compound(base, tower, gasket, airway)

    exports = {
        "sand_cube_200_hybrid_port_base.step": base,
        "sand_cube_200_hybrid_port_tower.step": tower,
        "sand_cube_200_hybrid_port_airway.step": airway,
        "sand_cube_200_hybrid_port_gasket.step": gasket,
        "sand_cube_200_hybrid_port_assembly.step": assembly,
        "sand_cube_200_hybrid_port_hardware_check.step": hardware_check,
        "sand_cube_200_hybrid_port_cutaway.step": cutaway,
    }
    for filename, shape in exports.items():
        export_step(shape, OUT / filename, unit=Unit.MM, write_pcurves=False)

    for source, viewer_name in (
        ("sand_cube_200_hybrid_port_assembly.step", "viewer"),
        ("sand_cube_200_hybrid_port_cutaway.step", "cutaway_viewer"),
    ):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source),
                "--out",
                str(OUT / viewer_name),
            ],
            check=True,
        )

    physical_length_m = length_data["physical_centerline_length_mm"] / 1000.0
    diagnostics: dict[str, Any] = {
        "name": D.name,
        "status": "first-pass packaging concept, not a production print split",
        "isolation": {
            "experiment_dir": "experiments/sand_cube_200_hybrid_port",
            "output_dir": "build/sand_cube_200_hybrid_port",
            "existing_43_hz_experiment_modified": False,
        },
        "design_inputs": asdict(D),
        "alignment": {
            "type": "38 Hz conventional bass reflex with one internal 180-degree fold",
            "target_tuning_hz": D.target_tuning_hz,
            "calculated_tuning_hz": length_data["calculated_tuning_hz"],
            "predicted_small_signal_f3_hz": response["predicted_f3_hz"],
            "not_a_transmission_line": True,
        },
        "volume_accounting": volume_data,
        "port": {
            "throat_cross_section_mm": [D.port_width, D.port_depth],
            "throat_area_mm2": D.port_area_mm2,
            "outer_cross_section_mm": [D.outer_width, D.outer_depth],
            "outlet_mouth_cross_section_mm": [
                D.outlet_mouth_width,
                D.outlet_mouth_depth,
            ],
            "outlet_is_narrower_than_136_mm_de250_cradle": (
                D.outlet_mouth_width + 2.0 * D.port_wall_t < 136.0
            ),
            "fold_count": 1,
            "bend_centerline_radius_mm": D.bend_centerline_r,
            "lengths": length_data,
            "visible_height_above_enclosure_mm": length_data["outlet_z_mm"]
            - P.cube_outer / 2.0,
            "visible_height_above_enclosure_in": (
                length_data["outlet_z_mm"] - P.cube_outer / 2.0
            )
            / 25.4,
            "first_quarter_wave_line_mode_hz": D.speed_of_sound_m_s
            / (4.0 * physical_length_m),
            "first_half_wave_line_mode_hz": D.speed_of_sound_m_s
            / (2.0 * physical_length_m),
        },
        "response_and_velocity": response,
        "passive_radiator_comparison": pr_comparison,
        "geometry": {
            "base_bbox": _bbox(base),
            "tower_bbox": _bbox(tower),
            "airway_bbox": _bbox(airway),
            "assembly_bbox": _bbox(assembly),
            "solid_counts": {
                "base": len(base.solids()),
                "tower": len(tower.solids()),
                "airway": len(airway.solids()),
                "gasket": len(gasket.solids()),
            },
            "validity": {
                "base": _is_valid(base),
                "tower": _is_valid(tower),
                "airway": _is_valid(airway),
                "gasket": _is_valid(gasket),
            },
            "interference_mm3": interference,
            "sand_void_seal": sand_seal,
            "tower": tower_data,
            "horn_and_de250": horn_data,
            "gx16": gx16_data,
        },
        "packaging_decisions_still_open": [
            (
                "The complete internal U cannot be inserted through the top receiver as one "
                "piece. A rear service panel, split duct, or enclosure-integrated lower U "
                "must be chosen before production CAD."
            ),
            (
                "Any nonzero tower-to-woofer interference is intentionally reported rather "
                "than forcing the main-driver location in this concept pass."
            ),
            (
                "The 38 Hz length is a Helmholtz/inertance estimate. Bend loss, wall texture, "
                "and end correction require an impedance sweep of the first printed duct."
            ),
            (
                "The broad 15 mm-deep slot needs generous surface finish and both flares; it "
                "is less forgiving of print ridges than a round passage."
            ),
        ],
        "files": {
            **{name: str(OUT / name) for name in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "viewer" / "index.html"),
            "cutaway_viewer": str(
                OUT / "cutaway_viewer" / "viewer" / "index.html"
            ),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
