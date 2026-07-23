"""Generate the third 38 Hz Sand Cube port concept.

Two equal internal inlet branches merge into one central vertical spine.  Only
that central spine exits the enclosure and supports the B&C DE250 cradle.  The
existing straight 43 Hz and single-U 38 Hz experiments remain untouched.
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
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Locations,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Unit,
    export_step,
    loft,
)


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.sand_cube_200_hybrid_port import (  # noqa: E402
    generate_sand_cube_200_hybrid_port as folded,
)
from experiments.sand_cube_8_5_black_hole.generate_contoured_inner_variants import (  # noqa: E402
    FINAL_200_VARIANT,
    _confirmed_passive_radiator,
    _confirmed_woofer,
    _final_params,
    _intersection_volume,
    _oriented_cylinder,
    _placed_gx16,
    _primary_shape,
    _require_single_solid,
)
from experiments.sand_cube_8_5_black_hole import (  # noqa: E402
    generate_contoured_inner_variants as enclosure_variants,
)


common = folded.common
OUT = ROOT / "build" / "sand_cube_200_twin_inlet_port"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_200_twin_inlet_port_38hz"
    target_tuning_hz: float = 38.0
    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204

    # One central 1,200 mm2 spine. Each internal branch is 600 mm2, so the
    # parallel branch pair preserves the common-spine area and mean velocity.
    common_width: float = 40.0
    common_depth: float = 30.0
    branch_width: float = 20.0
    branch_depth: float = 30.0
    port_wall_t: float = 3.2
    throat_corner_r: float = 2.0
    branch_x: float = 58.0
    duct_y: float = 67.8
    flange_y: float = 72.5

    # Mirrored lower J bends. Each branch joins one half of the common spine.
    # The airway is tangent to the -93 mm cavity floor. Its 3.2 mm bend wall
    # replaces the local 2 mm inner floor skin and extends 1.2 mm into the
    # 3 mm sand gap, while retaining 1.8 mm to the outer skin.
    bottom_bend_center_z: float = -59.0
    bottom_bend_centerline_r: float = 24.0

    # Each inlet turns forward in an expanded upper elbow. The first draft uses
    # a 180-degree forward-facing mouth rather than an obstructed upward mouth.
    # Keep the complete outer flare below the 83.5 mm acoustic-cavity ceiling.
    # The mouth centre lands at z=58 mm and leaves 2.3 mm of roof clearance.
    inlet_elbow_center_z: float = 33.0
    inlet_elbow_centerline_r: float = 25.0
    inlet_mouth_y: float = 26.0
    inlet_mouth_width: float = 34.0
    inlet_mouth_height: float = 40.0
    inlet_mouth_corner_r: float = 6.0
    inlet_end_correction_factor: float = 0.85

    outlet_flare_l: float = 25.0
    outlet_mouth_width: float = 110.0
    outlet_mouth_depth: float = 44.0
    outlet_mouth_corner_r: float = 12.0
    outlet_end_correction_factor: float = 0.613

    receiver_w: float = 116.0
    receiver_d: float = 55.0
    receiver_corner_r: float = 8.0
    receiver_bottom_z: float = 82.0
    spigot_clearance: float = 0.30
    flange_w: float = 116.0
    flange_d: float = 55.0
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
        return self.common_width * self.common_depth

    @property
    def branch_area_mm2(self) -> float:
        return self.branch_width * self.branch_depth

    # Compatibility names used by the shared base, gasket, response, and
    # centered DE250 half-cup helpers.
    @property
    def port_width(self) -> float:
        return self.common_width

    @property
    def port_depth(self) -> float:
        return self.common_depth

    @property
    def outer_width(self) -> float:
        return self.common_width + 2.0 * self.port_wall_t

    @property
    def outer_depth(self) -> float:
        return self.common_depth + 2.0 * self.port_wall_t

    @property
    def rear_lane_y(self) -> float:
        return self.flange_y

    @property
    def port_y(self) -> float:
        return self.duct_y

    @property
    def port_outer_r(self) -> float:
        return self.outer_depth / 2.0

    @property
    def horn_cup_rear_y(self) -> float:
        return self.duct_y - self.outer_depth / 2.0 + self.horn_cup_tube_overlap

    @property
    def inlet_elbow_center_y(self) -> float:
        return self.duct_y - self.inlet_elbow_centerline_r

    @property
    def inlet_horizontal_center_z(self) -> float:
        return self.inlet_elbow_center_z + self.inlet_elbow_centerline_r


D = Design(duct_y=78.0)

# The core 200 mm enclosure keeps a legacy 14 mm rear cap and a solid 7 mm
# floor. This experiment needs the same 2-3-2 construction as its other four
# walls. The rear-cap override is applied only while this base is built;
# importing this generator cannot alter either preserved variant.
TWIN_WALL_STACK_T = 7.0
TWIN_BASE_VARIANT = replace(
    FINAL_200_VARIANT,
    solid_bottom=False,
    skin_bridge_posts=False,
)
P = replace(
    _final_params(TWIN_BASE_VARIANT),
    rear_cap_t=TWIN_WALL_STACK_T,
)

# The shared helpers are parameterized through module-level immutable design
# objects. Redirect them only inside this isolated generator process.
folded.D = D
folded.P = P
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


def _half_annulus_xz(
    *, center_x: float, depth_y: float, inner_r: float, outer_r: float
) -> Part:
    outer = _oriented_cylinder(
        diameter=2.0 * outer_r,
        depth=depth_y,
        axis="y",
        center=(center_x, D.duct_y, D.bottom_bend_center_z),
    )
    inner = _oriented_cylinder(
        diameter=2.0 * inner_r,
        depth=depth_y + 2.0,
        axis="y",
        center=(center_x, D.duct_y, D.bottom_bend_center_z),
    )
    clip = Pos(
        center_x,
        D.duct_y,
        D.bottom_bend_center_z - outer_r / 2.0,
    ) * Box(2.0 * outer_r + 2.0, depth_y + 2.0, outer_r + 0.02)
    return _require_single_solid(
        _primary_shape((outer - inner) & clip).clean().fix(),
        feature="twin-inlet lower half-annulus",
    )


def _quarter_annulus_yz(
    *, branch_x: float, depth_x: float, inner_r: float, outer_r: float
) -> Part:
    center = (
        branch_x,
        D.inlet_elbow_center_y,
        D.inlet_elbow_center_z,
    )
    outer = _oriented_cylinder(
        diameter=2.0 * outer_r,
        depth=depth_x,
        axis="x",
        center=center,
    )
    inner = _oriented_cylinder(
        diameter=2.0 * inner_r,
        depth=depth_x + 2.0,
        axis="x",
        center=center,
    )
    clip = Pos(
        branch_x,
        D.inlet_elbow_center_y + outer_r / 2.0,
        D.inlet_elbow_center_z + outer_r / 2.0,
    ) * Box(depth_x + 2.0, outer_r + 0.02, outer_r + 0.02)
    return _require_single_solid(
        _primary_shape((outer - inner) & clip).clean().fix(),
        feature="twin-inlet forward quarter-annulus",
    )


def _rounded_loft_y(
    *,
    branch_x: float,
    y0: float,
    y1: float,
    center_z: float,
    width0: float,
    height0: float,
    corner0: float,
    width1: float,
    height1: float,
    corner1: float,
) -> Part:
    with BuildPart() as result:
        for index in range(7):
            t = index / 6.0
            blend = t * t * (3.0 - 2.0 * t)
            y = y0 + (y1 - y0) * t
            width = width0 + (width1 - width0) * blend
            height = height0 + (height1 - height0) * blend
            corner = corner0 + (corner1 - corner0) * blend
            section_plane = Plane(
                origin=(branch_x, y, center_z),
                x_dir=(1.0, 0.0, 0.0),
                z_dir=(0.0, -1.0, 0.0),
            )
            with BuildSketch(section_plane) as section:
                with Locations((0.0, 0.0)):
                    RectangleRounded(width, height, corner)
            assert section.sketch.area > 0, "Twin-inlet loft area must be positive"
        loft()
    return _require_single_solid(
        result.part.clean().fix(), feature="forward-facing inlet flare"
    )


def _fuse_connected(parts: list[Part], *, feature: str) -> Part:
    result = parts[0]
    for part in parts[1:]:
        result = (result + part).clean().fix()
    return _require_single_solid(result, feature=feature)


def _path_solids(outlet_z: float) -> tuple[Part, Part]:
    outlet_throat_z = outlet_z - D.outlet_flare_l
    if outlet_throat_z <= D.inlet_horizontal_center_z:
        raise ValueError("Central outlet throat is too low for the twin-inlet manifold")

    branch_half_w = D.branch_width / 2.0
    branch_half_d = D.branch_depth / 2.0
    bottom_air_inner = D.bottom_bend_centerline_r - branch_half_w
    bottom_air_outer = D.bottom_bend_centerline_r + branch_half_w
    bottom_shell_inner = bottom_air_inner - D.port_wall_t
    bottom_shell_outer = bottom_air_outer + D.port_wall_t
    elbow_air_inner = D.inlet_elbow_centerline_r - branch_half_d
    elbow_air_outer = D.inlet_elbow_centerline_r + branch_half_d
    elbow_shell_inner = elbow_air_inner - D.port_wall_t
    elbow_shell_outer = elbow_air_outer + D.port_wall_t

    common_inner = folded._rounded_prism(
        width=D.common_width,
        depth=D.common_depth,
        height=outlet_throat_z - D.bottom_bend_center_z,
        y=D.duct_y,
        z0=D.bottom_bend_center_z,
        corner_r=D.throat_corner_r,
    )
    common_outer = folded._rounded_prism(
        width=D.outer_width,
        depth=D.outer_depth,
        height=outlet_throat_z - D.bottom_bend_center_z,
        y=D.duct_y,
        z0=D.bottom_bend_center_z,
        corner_r=D.throat_corner_r + D.port_wall_t,
    )

    inner_parts: list[Part] = [common_inner]
    outer_parts: list[Part] = [common_outer]
    for sign in (-1.0, 1.0):
        branch_x = sign * D.branch_x
        common_half_x = sign * D.common_width / 4.0
        bend_center_x = (branch_x + common_half_x) / 2.0
        solved_radius = abs(branch_x - common_half_x) / 2.0
        if abs(solved_radius - D.bottom_bend_centerline_r) > 0.001:
            raise ValueError("Branch spacing no longer matches the specified J-bend radius")

        inner_parts.extend(
            [
                _half_annulus_xz(
                    center_x=bend_center_x,
                    depth_y=D.branch_depth,
                    inner_r=bottom_air_inner,
                    outer_r=bottom_air_outer,
                ),
                folded._rounded_prism(
                    width=D.branch_width,
                    depth=D.branch_depth,
                    height=D.inlet_elbow_center_z - D.bottom_bend_center_z,
                    y=D.duct_y,
                    z0=D.bottom_bend_center_z,
                    corner_r=D.throat_corner_r,
                ).moved(Pos(branch_x, 0.0, 0.0)),
                _quarter_annulus_yz(
                    branch_x=branch_x,
                    depth_x=D.branch_width,
                    inner_r=elbow_air_inner,
                    outer_r=elbow_air_outer,
                ),
                _rounded_loft_y(
                    branch_x=branch_x,
                    y0=D.inlet_mouth_y,
                    y1=D.inlet_elbow_center_y,
                    center_z=D.inlet_horizontal_center_z,
                    width0=D.inlet_mouth_width,
                    height0=D.inlet_mouth_height,
                    corner0=D.inlet_mouth_corner_r,
                    width1=D.branch_width,
                    height1=D.branch_depth,
                    corner1=D.throat_corner_r,
                ),
            ]
        )
        outer_parts.extend(
            [
                _half_annulus_xz(
                    center_x=bend_center_x,
                    depth_y=D.branch_depth + 2.0 * D.port_wall_t,
                    inner_r=bottom_shell_inner,
                    outer_r=bottom_shell_outer,
                ),
                folded._rounded_prism(
                    width=D.branch_width + 2.0 * D.port_wall_t,
                    depth=D.branch_depth + 2.0 * D.port_wall_t,
                    height=D.inlet_elbow_center_z - D.bottom_bend_center_z,
                    y=D.duct_y,
                    z0=D.bottom_bend_center_z,
                    corner_r=D.throat_corner_r + D.port_wall_t,
                ).moved(Pos(branch_x, 0.0, 0.0)),
                _quarter_annulus_yz(
                    branch_x=branch_x,
                    depth_x=D.branch_width + 2.0 * D.port_wall_t,
                    inner_r=elbow_shell_inner,
                    outer_r=elbow_shell_outer,
                ),
                _rounded_loft_y(
                    branch_x=branch_x,
                    y0=D.inlet_mouth_y,
                    y1=D.inlet_elbow_center_y,
                    center_z=D.inlet_horizontal_center_z,
                    width0=D.inlet_mouth_width + 2.0 * D.port_wall_t,
                    height0=D.inlet_mouth_height + 2.0 * D.port_wall_t,
                    corner0=D.inlet_mouth_corner_r + D.port_wall_t,
                    width1=D.branch_width + 2.0 * D.port_wall_t,
                    height1=D.branch_depth + 2.0 * D.port_wall_t,
                    corner1=D.throat_corner_r + D.port_wall_t,
                ),
            ]
        )

    inner_outlet = folded._rounded_loft(
        z0=outlet_throat_z,
        z1=outlet_z,
        y=D.duct_y,
        width0=D.common_width,
        depth0=D.common_depth,
        corner0=D.throat_corner_r,
        width1=D.outlet_mouth_width,
        depth1=D.outlet_mouth_depth,
        corner1=D.outlet_mouth_corner_r,
    )
    outer_outlet = folded._rounded_loft(
        z0=outlet_throat_z,
        z1=outlet_z,
        y=D.duct_y,
        width0=D.outer_width,
        depth0=D.outer_depth,
        corner0=D.throat_corner_r + D.port_wall_t,
        width1=D.outlet_mouth_width + 2.0 * D.port_wall_t,
        depth1=D.outlet_mouth_depth + 2.0 * D.port_wall_t,
        corner1=D.outlet_mouth_corner_r + D.port_wall_t,
    )
    inner_parts.append(inner_outlet)
    outer_parts.append(outer_outlet)

    return (
        _fuse_connected(inner_parts, feature="continuous twin-inlet airway"),
        _fuse_connected(outer_parts, feature="continuous twin-inlet outer envelope"),
    )


def _flare_equivalent_length_mm(
    *, area0: float, width0: float, depth0: float, width1: float, depth1: float, length: float
) -> float:
    steps = 4000
    total = 0.0
    for index in range(steps):
        t = (index + 0.5) / steps
        blend = t * t * (3.0 - 2.0 * t)
        width = width0 + (width1 - width0) * blend
        depth = depth0 + (depth1 - depth0) * blend
        total += area0 / (width * depth)
    return length * total / steps


def _port_length_solution(net_box_l: float) -> dict[str, float]:
    area_m2 = D.port_area_mm2 / 1_000_000.0
    volume_m3 = net_box_l / 1000.0
    required_effective_mm = 1000.0 * (
        D.speed_of_sound_m_s**2
        * area_m2
        / ((2.0 * math.pi * D.target_tuning_hz) ** 2 * volume_m3)
    )

    inlet_flare_l = D.inlet_elbow_center_y - D.inlet_mouth_y
    inlet_flare_equiv = _flare_equivalent_length_mm(
        area0=D.branch_area_mm2,
        width0=D.branch_width,
        depth0=D.branch_depth,
        width1=D.inlet_mouth_width,
        depth1=D.inlet_mouth_height,
        length=inlet_flare_l,
    )
    inlet_elbow_l = math.pi * D.inlet_elbow_centerline_r / 2.0
    branch_vertical_l = D.inlet_elbow_center_z - D.bottom_bend_center_z
    bottom_bend_l = math.pi * D.bottom_bend_centerline_r
    inlet_equiv_r = math.sqrt(
        D.inlet_mouth_width * D.inlet_mouth_height / math.pi
    )
    inlet_end = D.inlet_end_correction_factor * inlet_equiv_r

    # With two equal 600 mm2 branches in parallel feeding one 1,200 mm2
    # common spine, the branch acoustic length refers directly to the common
    # area: Ac/(2*Ab) = 1.
    branch_parallel_area_factor = D.port_area_mm2 / (2.0 * D.branch_area_mm2)
    branch_area_corrected = branch_parallel_area_factor * (
        inlet_flare_equiv + inlet_elbow_l + branch_vertical_l + bottom_bend_l
    )
    branch_end_corrected = branch_parallel_area_factor * inlet_end

    outlet_flare_equiv = _flare_equivalent_length_mm(
        area0=D.port_area_mm2,
        width0=D.common_width,
        depth0=D.common_depth,
        width1=D.outlet_mouth_width,
        depth1=D.outlet_mouth_depth,
        length=D.outlet_flare_l,
    )
    outlet_equiv_r = math.sqrt(
        D.outlet_mouth_width * D.outlet_mouth_depth / math.pi
    )
    outlet_end = D.outlet_end_correction_factor * outlet_equiv_r
    common_straight_l = (
        required_effective_mm
        - branch_area_corrected
        - branch_end_corrected
        - outlet_flare_equiv
        - outlet_end
    )
    if common_straight_l <= 0.0:
        raise ValueError("Solved common-spine length is not positive")

    outlet_throat_z = D.bottom_bend_center_z + common_straight_l
    outlet_z = outlet_throat_z + D.outlet_flare_l
    branch_physical_l = (
        inlet_flare_l + inlet_elbow_l + branch_vertical_l + bottom_bend_l
    )
    physical_path_l = branch_physical_l + common_straight_l + D.outlet_flare_l
    area_corrected_physical = (
        branch_area_corrected + common_straight_l + outlet_flare_equiv
    )
    effective_check = area_corrected_physical + branch_end_corrected + outlet_end
    tuning_check = D.speed_of_sound_m_s / (2.0 * math.pi) * math.sqrt(
        area_m2 / (volume_m3 * effective_check / 1000.0)
    )
    return {
        "outlet_z_mm": outlet_z,
        "outlet_throat_z_mm": outlet_throat_z,
        "physical_path_from_either_inlet_mm": physical_path_l,
        "branch_physical_length_mm": branch_physical_l,
        "common_straight_length_mm": common_straight_l,
        "inlet_flare_area_equivalent_length_mm": inlet_flare_equiv,
        "inlet_elbow_centerline_length_mm": inlet_elbow_l,
        "branch_vertical_length_mm": branch_vertical_l,
        "bottom_j_bend_centerline_length_mm": bottom_bend_l,
        "parallel_branch_area_factor": branch_parallel_area_factor,
        "parallel_branch_area_corrected_length_mm": branch_area_corrected,
        "parallel_branch_inlet_end_correction_mm": branch_end_corrected,
        "outlet_flare_area_equivalent_length_mm": outlet_flare_equiv,
        "outlet_end_correction_mm": outlet_end,
        "area_corrected_physical_length_mm": area_corrected_physical,
        "effective_length_mm": effective_check,
        "calculated_tuning_hz": tuning_check,
    }


def _volume_accounting(
    *,
    base: Part,
    baseline: Part,
    baseline_diagnostics: dict[str, Any],
    port_outer_envelope: Part,
    woofer: Any,
    gx16: Any,
) -> dict[str, Any]:
    domain = common._acoustic_domain()
    gross_l = domain.volume / 1_000_000.0
    air = _primary_shape(domain - base)
    base_displacement_mm3 = domain.volume - air.volume
    air, woofer_displacement = common._subtract_and_measure(air, woofer)
    air, port_displacement = common._subtract_and_measure(
        air,
        port_outer_envelope,
    )

    # The unchanged top binding-post placement was measured exactly in the
    # preserved variant. The imported seven-solid GX16 STEP triggers a very
    # slow OpenCascade intersection after the rear cavity moves aft, so count
    # its complete solid volume as a conservative upper bound. The resulting
    # net-volume bias is less than 0.0023 L / 0.05 percent.
    binding_post_displacement_mm3 = 1361.2459290241823
    gx16_conservative_displacement_mm3 = gx16.volume
    final_net_mm3 = (
        air.volume
        - binding_post_displacement_mm3
        - gx16_conservative_displacement_mm3
    )
    brace_l = baseline_diagnostics["total_internal_brace_cavity_displacement_l"]
    other_base_l = max(0.0, base_displacement_mm3 / 1_000_000.0 - brace_l)
    return {
        "method": (
            "Exact OpenCascade cavity subtraction for the finished base, woofer, "
            "and complete in-box port envelope. The unchanged binding-post value "
            "is reused from its exact prior placement; the complete GX16 solid "
            "volume is conservatively counted because its imported compound "
            "causes a pathological rear-cavity boolean."
        ),
        "gross_cavity_plus_front_relief_l": gross_l,
        "existing_braces_l": brace_l,
        "other_base_intrusions_including_receiver_and_port_wall_l": other_base_l,
        "base_structure_total_l": base_displacement_mm3 / 1_000_000.0,
        "e150he_44_step_displacement_l": woofer_displacement / 1_000_000.0,
        "gx16_conservative_upper_bound_displacement_l": (
            gx16_conservative_displacement_mm3 / 1_000_000.0
        ),
        "binding_posts_reused_exact_displacement_l": (
            binding_post_displacement_mm3 / 1_000_000.0
        ),
        "internal_port_envelope_displacement_l": port_displacement / 1_000_000.0,
        "final_net_box_volume_l": final_net_mm3 / 1_000_000.0,
        "gx16_net_volume_uncertainty_l": gx16_conservative_displacement_mm3
        / 1_000_000.0,
        "current_passive_radiator_arrangement": (
            "Not recomputed: this variant replaces the passive-radiator rear wall "
            "with a structurally different 2-3-2 wall."
        ),
    }


def build_base_enclosure(
    port_airway: Part,
    port_outer_envelope: Part,
) -> tuple[Part, Part, dict[str, Any]]:
    original_base_p = enclosure_variants.base_p
    try:
        enclosure_variants.base_p = replace(
            original_base_p,
            rear_cap_t=TWIN_WALL_STACK_T,
        )
        baseline, baseline_diagnostics = enclosure_variants.build_variant(
            TWIN_BASE_VARIANT
        )
    finally:
        enclosure_variants.base_p = original_base_p

    half = P.cube_outer / 2.0
    shell_span = P.cube_outer - 2.0 * P.outer_skin_t

    # Restore the deleted passive-radiator field, then cut one continuous 3 mm
    # rear sand gap through both the legacy cap and that closure. This produces
    # a genuine 2-3-2 wall across the complete rear face rather than only inside
    # the former circular opening.
    rear_closure = _oriented_cylinder(
        diameter=P.pr_recess_dia,
        depth=TWIN_WALL_STACK_T,
        axis="y",
        center=(0.0, half - TWIN_WALL_STACK_T / 2.0, 0.0),
    )
    base = baseline.fuse(rear_closure, glue=True, tol=0.01).clean().fix()
    rear_void_y = half - P.outer_skin_t - P.void_t / 2.0
    rear_void = Pos(0.0, rear_void_y, 0.0) * enclosure_variants._filleted_box(
        shell_span,
        P.void_t,
        shell_span,
        radius=1.0,
    )
    base -= rear_void

    # Point-like bridges support the new rear and floor gaps without producing
    # closed ribs. Rear posts sit outside the projected twin-duct footprint.
    rear_post_depth = P.void_t + 0.4
    for x, z in ((-85.0, 0.0), (85.0, 0.0), (-30.0, -60.0), (30.0, -60.0)):
        base += _oriented_cylinder(
            diameter=4.0,
            depth=rear_post_depth,
            axis="y",
            center=(x, rear_void_y, z),
        )
    bottom_post_z = -half + P.outer_skin_t + P.void_t / 2.0
    bottom_post_depth = P.void_t + 0.4
    for x, y in ((-55.0, -45.0), (55.0, -45.0), (-25.0, 15.0), (25.0, 15.0)):
        base += _oriented_cylinder(
            diameter=4.0,
            depth=bottom_post_depth,
            axis="z",
            center=(x, y, bottom_post_z),
        )

    binding_island, binding_pilots = common._binding_post_island_and_pilots()
    base = base.fuse(binding_island, glue=True, tol=0.01).clean().fix()
    for x in (-P.binding_post_spacing / 2.0, P.binding_post_spacing / 2.0):
        base += _oriented_cylinder(
            diameter=12.0,
            depth=18.0,
            axis="z",
            center=(x, P.binding_post_y, half - 9.0),
        )
    base = base.clean().fix()

    # The base owns the complete in-box duct. Its 3.2 mm wall overlaps and
    # replaces the local 2 mm inner rear/floor skin, enters 1.2 mm of each sand
    # gap, and remains 1.8 mm clear of each outer skin. The removable tower owns
    # only the above-box spine and B&C cradle.
    enclosure_clip = folded._outer_envelope()
    in_box_port_outer = _primary_shape(port_outer_envelope & enclosure_clip)
    in_box_airway = _primary_shape(port_airway & enclosure_clip)
    base = base.fuse(in_box_port_outer, glue=True, tol=0.01).clean().fix()

    receiver = folded._rounded_prism(
        width=D.receiver_w,
        depth=D.receiver_d,
        height=half - D.receiver_bottom_z,
        y=D.flange_y,
        z0=D.receiver_bottom_z,
        corner_r=D.receiver_corner_r,
    )
    receiver = _primary_shape(receiver & folded._outer_envelope())
    base = base.fuse(receiver, glue=True, tol=0.01).clean().fix()
    base -= in_box_airway
    for x, y in folded._attachment_positions():
        base -= _oriented_cylinder(
            diameter=D.base_insert_pocket_d,
            depth=D.base_insert_pocket_depth,
            axis="z",
            center=(x, y, half - D.base_insert_pocket_depth / 2.0),
        )
    base -= binding_pilots
    base = _require_single_solid(
        base.clean().fix(), feature="finished monocoque 2-3-2 twin-inlet base"
    )
    return base, baseline, baseline_diagnostics


def build_tower(outlet_z: float) -> tuple[Part, Part, Part, dict[str, float]]:
    airway, outer_envelope = _path_solids(outlet_z)
    flange_bottom = P.cube_outer / 2.0 + D.gasket_t
    outer_bb = outer_envelope.bounding_box()
    external_height = outer_bb.max.Z - flange_bottom + 2.0
    external_clip = Pos(
        0.0,
        0.0,
        flange_bottom + external_height / 2.0,
    ) * Box(400.0, 400.0, external_height)
    external_outer = _primary_shape(outer_envelope & external_clip)
    flange = folded._rounded_prism(
        width=D.flange_w,
        depth=D.flange_d,
        height=D.flange_t,
        y=D.flange_y,
        z0=flange_bottom,
        corner_r=D.flange_corner_r,
    )
    cup = common._horn_cup()
    tower = _fuse_connected(
        [external_outer, flange, cup],
        feature="uncut twin-inlet tower and single DE250 cradle",
    )
    tower -= airway
    tower -= common._horn_cup_cutouts()
    for x, y in folded._attachment_positions():
        tower -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.flange_t + 2.0,
            axis="z",
            center=(x, y, flange_bottom + D.flange_t / 2.0),
        )
    tower = _require_single_solid(tower.clean().fix(), feature="finished twin-inlet tower")
    if _intersection_volume(tower, airway) > 0.001:
        raise ValueError("Twin-inlet tower obstructs its airway")
    return tower, airway, outer_envelope, {
        "flange_bottom_z_mm": flange_bottom,
        "flange_top_z_mm": flange_bottom + D.flange_t,
        "outlet_z_mm": outlet_z,
        "single_rising_support": True,
        "base_owns_complete_in_box_port": True,
        "internal_inlet_count": 2,
        "inlet_facing": "forward, approximately 180-degree approach",
    }


def build_gasket() -> Part:
    gasket = folded._rounded_prism(
        width=D.flange_w - 1.0,
        depth=D.flange_d - 1.0,
        height=D.gasket_t,
        y=D.flange_y,
        z0=P.cube_outer / 2.0,
        corner_r=D.flange_corner_r - 0.5,
    )
    gasket -= folded._rounded_prism(
        width=D.outer_width + 2.0 * D.spigot_clearance,
        depth=D.outer_depth + 2.0 * D.spigot_clearance,
        height=D.gasket_t + 2.0,
        y=D.duct_y,
        z0=P.cube_outer / 2.0 - 1.0,
        corner_r=D.throat_corner_r + D.port_wall_t + D.spigot_clearance,
    )
    for x, y in folded._attachment_positions():
        gasket -= _oriented_cylinder(
            diameter=D.tower_bolt_clearance_d,
            depth=D.gasket_t + 2.0,
            axis="z",
            center=(x, y, P.cube_outer / 2.0 + D.gasket_t / 2.0),
        )
    return _require_single_solid(
        gasket.clean().fix(), feature="twin-inlet tower gasket"
    )


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    provisional_airway, provisional_outer = _path_solids(250.0)
    base, baseline, baseline_diagnostics = build_base_enclosure(
        provisional_airway,
        provisional_outer,
    )
    woofer = _confirmed_woofer(P)
    gx16, gx16_data = _placed_gx16(P)
    binding_posts = folded._relocated_binding_posts()

    volume_data = _volume_accounting(
        base=base,
        baseline=baseline,
        baseline_diagnostics=baseline_diagnostics,
        port_outer_envelope=provisional_outer,
        woofer=woofer,
        gx16=gx16,
    )
    length_data = _port_length_solution(volume_data["final_net_box_volume_l"])
    tower, airway, port_outer, tower_data = build_tower(length_data["outlet_z_mm"])
    gasket = build_gasket()
    horn, de250, horn_data = common._placed_horn_and_de250()

    volume_data = _volume_accounting(
        base=base,
        baseline=baseline,
        baseline_diagnostics=baseline_diagnostics,
        port_outer_envelope=port_outer,
        woofer=woofer,
        gx16=gx16,
    )
    final_length_data = _port_length_solution(volume_data["final_net_box_volume_l"])
    if abs(final_length_data["outlet_z_mm"] - length_data["outlet_z_mm"]) > 0.01:
        raise ValueError("Final volume unexpectedly changed the twin-inlet length")
    length_data = final_length_data

    gx_bb = gx16.bounding_box()
    gx_bbox_solid = Pos(
        (gx_bb.min.X + gx_bb.max.X) / 2.0,
        (gx_bb.min.Y + gx_bb.max.Y) / 2.0,
        (gx_bb.min.Z + gx_bb.max.Z) / 2.0,
    ) * Box(gx_bb.size.X, gx_bb.size.Y, gx_bb.size.Z)
    interference = {
        "base_to_tower_mm3": _intersection_volume(base, tower),
        "airway_to_base_mm3": _intersection_volume(airway, base),
        "airway_to_tower_mm3": _intersection_volume(airway, tower),
        "tower_to_woofer_mm3": _intersection_volume(tower, woofer),
        "airway_to_woofer_mm3": _intersection_volume(airway, woofer),
        "tower_to_gx16_mm3": _intersection_volume(tower, gx16),
        "in_box_port_to_gx16_bbox_upper_bound_mm3": _intersection_volume(
            port_outer,
            gx_bbox_solid,
        ),
        "airway_to_gx16_bbox_upper_bound_mm3": _intersection_volume(
            airway,
            gx_bbox_solid,
        ),
        "tower_to_binding_posts_mm3": sum(
            _intersection_volume(tower, post) for post in binding_posts
        ),
        "tower_to_horn_mm3": _intersection_volume(tower, horn),
        "tower_to_de250_mm3": _intersection_volume(tower, de250),
    }
    if interference["base_to_tower_mm3"] > 0.001:
        raise ValueError("Base overlaps the twin-inlet tower")
    if interference["airway_to_base_mm3"] > 0.001:
        raise ValueError("Base obstructs the twin-inlet airway")
    if interference["airway_to_tower_mm3"] > 0.001:
        raise ValueError("Tower obstructs the twin-inlet airway")

    response = common._vented_response(
        volume_data["final_net_box_volume_l"], length_data["effective_length_mm"]
    )
    sand_seal = folded._sand_void_seal_check(airway)
    enclosure_clip = folded._outer_envelope()
    in_box_airway = _primary_shape(airway & enclosure_clip)
    airway_bb = in_box_airway.bounding_box()
    in_box_port_outer = _primary_shape(port_outer & enclosure_clip)
    port_outer_bb = in_box_port_outer.bounding_box()
    cavity_rear_y = P.cube_outer / 2.0 - TWIN_WALL_STACK_T
    cavity_floor_z = -P.cube_outer / 2.0 + TWIN_WALL_STACK_T
    rear_outer_skin_inner_y = P.cube_outer / 2.0 - P.outer_skin_t
    floor_outer_skin_inner_z = -P.cube_outer / 2.0 + P.outer_skin_t
    sand_seal.update(
        {
            "rear_wall_stack_mm": [P.outer_skin_t, P.void_t, P.inner_skin_t],
            "floor_stack_mm": [P.outer_skin_t, P.void_t, P.inner_skin_t],
            "airway_rear_tangent_to_cavity_mm": airway_bb.max.Y
            - cavity_rear_y,
            "airway_floor_tangent_to_cavity_mm": airway_bb.min.Z
            - cavity_floor_z,
            "duct_clearance_to_rear_outer_skin_mm": rear_outer_skin_inner_y
            - port_outer_bb.max.Y,
            "duct_clearance_to_floor_outer_skin_mm": port_outer_bb.min.Z
            - floor_outer_skin_inner_z,
            "shared_wall_strategy": (
                "The 3.2 mm duct wall replaces the local 2 mm inner rear/floor "
                "skin and enters 1.2 mm of the 3 mm sand gap."
            ),
        }
    )

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
    cutaway = folded._cutaway_compound(base, tower, gasket, airway)

    exports = {
        "sand_cube_200_twin_inlet_port_base.step": base,
        "sand_cube_200_twin_inlet_port_tower.step": tower,
        "sand_cube_200_twin_inlet_port_airway.step": airway,
        "sand_cube_200_twin_inlet_port_gasket.step": gasket,
        "sand_cube_200_twin_inlet_port_assembly.step": assembly,
        "sand_cube_200_twin_inlet_port_hardware_check.step": hardware_check,
        "sand_cube_200_twin_inlet_port_cutaway.step": cutaway,
    }
    for filename, shape in exports.items():
        export_step(shape, OUT / filename, unit=Unit.MM, write_pcurves=False)

    for source, viewer_name in (
        ("sand_cube_200_twin_inlet_port_assembly.step", "viewer"),
        ("sand_cube_200_twin_inlet_port_cutaway.step", "cutaway_viewer"),
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

    diagnostics: dict[str, Any] = {
        "name": D.name,
        "status": "third isolated topology draft",
        "isolation": {
            "experiment_dir": "experiments/sand_cube_200_twin_inlet_port",
            "output_dir": "build/sand_cube_200_twin_inlet_port",
            "straight_43_hz_variant_modified": False,
            "single_u_38_hz_variant_modified": False,
        },
        "design_inputs": asdict(D),
        "network": {
            "topology": "two equal internal inlet branches in parallel, merging into one central outlet spine",
            "common_spine_area_mm2": D.port_area_mm2,
            "each_branch_area_mm2": D.branch_area_mm2,
            "combined_branch_area_mm2": 2.0 * D.branch_area_mm2,
            "area_ratio_combined_branches_to_spine": 2.0
            * D.branch_area_mm2
            / D.port_area_mm2,
            "single_external_rising_support": True,
            "internal_inlet_count": 2,
            "inlet_approach": (
                "Two equal forward-facing flared mouths. Each uses a swept 90-degree "
                "upper elbow rather than facing upward into the top wall."
            ),
            "bend_centerline_radii_mm": {
                "lower_180_degree_return": D.bottom_bend_centerline_r,
                "upper_90_degree_elbow": D.inlet_elbow_centerline_r,
            },
            "airway_inside_radii_mm": {
                "lower_180_degree_return": D.bottom_bend_centerline_r
                - D.branch_width / 2.0,
                "upper_90_degree_elbow": D.inlet_elbow_centerline_r
                - D.branch_depth / 2.0,
            },
        },
        "alignment": {
            "type": "38 Hz bass reflex with two parallel internal inlets and one common outlet",
            "target_tuning_hz": D.target_tuning_hz,
            "calculated_tuning_hz": length_data["calculated_tuning_hz"],
            "predicted_small_signal_f3_hz": response["predicted_f3_hz"],
        },
        "volume_accounting": volume_data,
        "port": {
            "common_cross_section_mm": [D.common_width, D.common_depth],
            "branch_cross_section_mm": [D.branch_width, D.branch_depth],
            "outlet_mouth_cross_section_mm": [
                D.outlet_mouth_width,
                D.outlet_mouth_depth,
            ],
            "inlet_mouth_cross_section_mm_each": [
                D.inlet_mouth_width,
                D.inlet_mouth_height,
            ],
            "lengths": length_data,
            "flare_length_contribution": {
                "each_inlet_physical_mm": D.inlet_elbow_center_y
                - D.inlet_mouth_y,
                "each_inlet_area_equivalent_mm": length_data[
                    "inlet_flare_area_equivalent_length_mm"
                ],
                "outlet_physical_mm": D.outlet_flare_l,
                "outlet_area_equivalent_mm": length_data[
                    "outlet_flare_area_equivalent_length_mm"
                ],
                "note": (
                    "Flares count toward acoustic length through the integral of "
                    "reference area divided by local area, so an expanding flare "
                    "contributes less than its physical centreline length."
                ),
            },
            "visible_height_above_enclosure_mm": length_data["outlet_z_mm"]
            - P.cube_outer / 2.0,
            "visible_height_above_enclosure_in": (
                length_data["outlet_z_mm"] - P.cube_outer / 2.0
            )
            / 25.4,
        },
        "response_and_velocity": response,
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
        "draft_limits": [
            (
                "The rear and floor now use the requested 2-3-2 construction. The duct "
                "replaces the local inner skin at both interfaces; production work still "
                "needs a print-or-assembly decision for those shared seams."
            ),
            (
                "The two equal branches are represented by a lumped parallel acoustic-mass "
                "network. Junction loss and differential branch modes require CFD or a "
                "physical impedance sweep before production tuning."
            ),
            (
                "Forward inlet clearance to the main woofer is reported rather than moving "
                "the woofer in this draft."
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
