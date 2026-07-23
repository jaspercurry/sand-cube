"""Generate an isolated 40 mm modular-header port study.

The proven 39 mm smooth-sweep experiment remains untouched.  This variant
reuses its enclosure, woofer, horn, response model, and export checks, but
replaces the bespoke compound port centerline with circular straight and
constant-radius elbow modules.  Joints, collars, and structural mounts are
intentionally deferred so this pass can compare core packaging and volume.
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

import json
import math
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from build123d import Box, BuildSketch, Circle, Compound, Edge, Plane, Pos, Vector, Wire, sweep


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = ROOT / "experiments" / "sand_cube_190x210_single_oval_port"
sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_single_oval_port as base  # noqa: E402


OUT = ROOT / "build" / "sand_cube_190x210_header_port"
OLD_DIAGNOSTICS = (
    ROOT / "build" / "sand_cube_190x210_single_oval_port" / "diagnostics.json"
)


@dataclass(frozen=True)
class HeaderRoute:
    """Centerline modules, in their physical order from inlet to tower."""

    plan_elbow_radius_mm: float = 75.0
    plan_elbow_angle_deg: float = 72.7
    inter_elbow_straight_mm: float = 26.274878283306606
    rise_elbow_radius_mm: float = 50.0
    rise_elbow_angle_deg: float = 90.0
    offset_elbow_radius_mm: float = 50.0
    offset_elbow_angle_deg: float = 67.0
    target_tower_x_mm: float = 0.0
    target_tower_y_mm: float = 82.0
    target_tower_z_mm: float = 84.0


H = HeaderRoute()


def _configured_design() -> base.Design:
    mouth_d = math.sqrt(46.0 * 43.0)
    return replace(
        base.D,
        name="sand_cube_190x210_modular_header_40mm_39hz",
        port_width=40.0,
        port_depth=40.0,
        tower_width=40.0,
        tower_depth=40.0,
        port_y=H.target_tower_y_mm,
        upper_tower_y=H.target_tower_y_mm,
        horizontal_z=-65.0,
        # The small left shift restores positive woofer-to-port-wall clearance
        # after growing the bore from 39.243 to 40 mm. The R75 plan elbow and
        # short straight land the rise inside both wall-installation limits.
        inlet_x=-61.5,
        # Extend the flare toward the front by 3 mm without moving its 40 mm
        # throat or the rest of the floor route toward the woofer.
        inlet_mouth_y=-28.25,
        inlet_flare_l=18.0,
        inlet_flat_width=40.0,
        inlet_flat_height=40.0,
        inlet_flat_center_z=-65.0,
        inlet_mouth_width=mouth_d,
        inlet_mouth_height=mouth_d,
        inlet_mouth_center_z=-88.0 + mouth_d / 2.0 + 3.0,
        lower_elbow_vertical_x=64.02114821591442,
        lower_elbow_vertical_y=84.03929228750656,
        bend_centerline_r=H.rise_elbow_radius_mm,
        asymmetric_vertical_return_top_z=H.target_tower_z_mm,
        # Exact 39 Hz solve after measuring the finished in-box displacement.
        target_outlet_drop=28.8954,
    )


base.D = _configured_design()
base.OUT = OUT


def _rotate(vector: Vector, axis: Vector, angle_rad: float) -> Vector:
    """Rodrigues rotation for a normalized axis."""
    axis = axis.normalized()
    return (
        vector * math.cos(angle_rad)
        + axis.cross(vector) * math.sin(angle_rad)
        + axis * axis.dot(vector) * (1.0 - math.cos(angle_rad))
    )


def _arc_from_start_tangent(
    start: Vector,
    tangent: Vector,
    normal: Vector,
    radius: float,
    angle_rad: float,
) -> tuple[Edge, Vector, Vector]:
    """Create a circular elbow and return edge, endpoint, and end tangent."""
    tangent = tangent.normalized()
    normal = normal.normalized()
    if abs(tangent.dot(normal)) > 1e-8:
        raise ValueError("Elbow tangent and plane normal are not perpendicular")
    center = start + normal.cross(tangent) * radius
    radial_start = start - center
    radial_mid = _rotate(radial_start, normal, angle_rad / 2.0)
    radial_end = _rotate(radial_start, normal, angle_rad)
    midpoint = center + radial_mid
    endpoint = center + radial_end
    end_tangent = _rotate(tangent, normal, angle_rad).normalized()
    return (
        Edge.make_three_point_arc(start, midpoint, endpoint),
        endpoint,
        end_tangent,
    )


def _header_route_geometry() -> tuple[Wire, dict[str, Any]]:
    d = base.D
    p0 = Vector(d.inlet_throat_x, d.inlet_throat_y, d.horizontal_z)
    direction = Vector(0.0, 1.0, 0.0)
    edges: list[Edge] = []

    plan_angle = math.radians(H.plan_elbow_angle_deg)
    plan_arc, point, direction = _arc_from_start_tangent(
        p0,
        direction,
        Vector(0.0, 0.0, -1.0),
        H.plan_elbow_radius_mm,
        plan_angle,
    )
    edges.append(plan_arc)

    next_point = point + direction * H.inter_elbow_straight_mm
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    rise_normal = direction.cross(Vector(0.0, 0.0, 1.0)).normalized()
    rise_arc, point, direction = _arc_from_start_tangent(
        point,
        direction,
        rise_normal,
        H.rise_elbow_radius_mm,
        math.radians(H.rise_elbow_angle_deg),
    )
    edges.append(rise_arc)
    if direction.dot(Vector(0.0, 0.0, 1.0)) < 1.0 - 1e-8:
        raise ValueError("Rise elbow does not finish vertical")
    rise_exit = Vector(point.X, point.Y, point.Z)

    target_xy = Vector(H.target_tower_x_mm, H.target_tower_y_mm, point.Z)
    lateral = Vector(target_xy.X - point.X, target_xy.Y - point.Y, 0.0)
    lateral_distance = lateral.length
    lateral = lateral.normalized()
    offset_angle = math.radians(H.offset_elbow_angle_deg)
    offset_base = 2.0 * H.offset_elbow_radius_mm * (
        1.0 - math.cos(offset_angle)
    )
    diagonal_length = (lateral_distance - offset_base) / math.sin(offset_angle)
    if diagonal_length <= 0.0:
        raise ValueError("Offset elbows overlap; increase the lateral displacement")
    offset_vertical = (
        2.0 * H.offset_elbow_radius_mm * math.sin(offset_angle)
        + diagonal_length * math.cos(offset_angle)
    )
    available_vertical = H.target_tower_z_mm - point.Z
    remaining_vertical = available_vertical - offset_vertical
    if remaining_vertical <= 0.0:
        raise ValueError("Header offset does not fit below the straight tower")
    short_vertical = remaining_vertical / 2.0

    next_point = point + direction * short_vertical
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    offset_normal = direction.cross(lateral).normalized()
    offset_arc_1, point, direction = _arc_from_start_tangent(
        point,
        direction,
        offset_normal,
        H.offset_elbow_radius_mm,
        offset_angle,
    )
    edges.append(offset_arc_1)

    next_point = point + direction * diagonal_length
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    return_normal = direction.cross(Vector(0.0, 0.0, 1.0)).normalized()
    offset_arc_2, point, direction = _arc_from_start_tangent(
        point,
        direction,
        return_normal,
        H.offset_elbow_radius_mm,
        offset_angle,
    )
    edges.append(offset_arc_2)

    endpoint = Vector(
        H.target_tower_x_mm,
        H.target_tower_y_mm,
        H.target_tower_z_mm,
    )
    edges.append(Edge.make_line(point, endpoint))
    wire = Wire(edges)

    endpoint_error = (wire.position_at(1.0) - endpoint).length
    if endpoint_error > 0.001:
        raise ValueError(f"Header route endpoint error is {endpoint_error:.6f} mm")
    tangent_error = (
        wire.tangent_at(1.0).normalized() - Vector(0.0, 0.0, 1.0)
    ).length
    if tangent_error > 0.001:
        raise ValueError(f"Header route tangent error is {tangent_error:.6f}")

    metadata = {
        "module_order": [
            (
                f"{H.plan_elbow_angle_deg:g} degree "
                f"R{H.plan_elbow_radius_mm:g} plan elbow"
            ),
            f"{H.inter_elbow_straight_mm:g} mm straight",
            (
                f"{H.rise_elbow_angle_deg:g} degree "
                f"R{H.rise_elbow_radius_mm:g} rise elbow"
            ),
            f"{short_vertical:.3f} mm vertical straight",
            (
                f"{H.offset_elbow_angle_deg:g} degree "
                f"R{H.offset_elbow_radius_mm:g} offset elbow"
            ),
            f"{diagonal_length:.3f} mm diagonal straight",
            (
                f"{H.offset_elbow_angle_deg:g} degree "
                f"R{H.offset_elbow_radius_mm:g} return elbow"
            ),
            f"{short_vertical:.3f} mm vertical straight",
        ],
        "elbow_angles_deg": [
            H.plan_elbow_angle_deg,
            H.rise_elbow_angle_deg,
            H.offset_elbow_angle_deg,
            H.offset_elbow_angle_deg,
        ],
        "elbow_centerline_radii_mm": [
            H.plan_elbow_radius_mm,
            H.rise_elbow_radius_mm,
            H.offset_elbow_radius_mm,
            H.offset_elbow_radius_mm,
        ],
        "total_direction_change_deg": (
            H.plan_elbow_angle_deg
            + H.rise_elbow_angle_deg
            + 2.0 * H.offset_elbow_angle_deg
        ),
        "inter_elbow_straight_mm": H.inter_elbow_straight_mm,
        "offset_diagonal_straight_mm": diagonal_length,
        "short_vertical_straights_mm": [short_vertical, short_vertical],
        "lateral_offset_mm": lateral_distance,
        "lateral_offset_direction_xy": [lateral.X, lateral.Y],
        "rise_elbow_exit_xyz_mm": [rise_exit.X, rise_exit.Y, rise_exit.Z],
        "route_start_xyz_mm": [p0.X, p0.Y, p0.Z],
        "route_end_xyz_mm": [endpoint.X, endpoint.Y, endpoint.Z],
        "physical_length_mm": wire.length,
        "minimum_centerline_radius_to_bore_ratio": min(
            H.plan_elbow_radius_mm,
            H.rise_elbow_radius_mm,
            H.offset_elbow_radius_mm,
        )
        / base.D.port_width,
        "all_sections_constant_circle": True,
        "all_curves_constant_radius": True,
        "bespoke_spline_sections": 0,
    }
    return wire, metadata


def _header_route_wire() -> Wire:
    return _header_route_geometry()[0]


def _header_route_metadata() -> dict[str, Any]:
    return _header_route_geometry()[1]


def _compound_route_ellipse(*, rx: float, rn: float) -> Any:
    if abs(rx - rn) > 1e-6:
        raise ValueError("Header route requires a circular cross-section")
    route = _header_route_wire()
    start = route.position_at(0.0)
    tangent = route.tangent_at(0.0).normalized()
    section_plane = Plane(
        origin=start,
        x_dir=(-tangent.Y, tangent.X, 0.0),
        z_dir=tangent,
    )
    with BuildSketch(section_plane) as section:
        Circle(rx)
    if section.sketch.area <= 0.0:
        raise ValueError("Header route section area is not positive")
    return base._require_single_solid(
        sweep(
            section.sketch.faces()[0],
            path=route,
            is_frenet=False,
        ).clean().fix(),
        feature="constant-circle modular header route",
    )


def _compound_route_base_lengths() -> tuple[float, float, float, float]:
    metadata = _header_route_metadata()
    plan_group = (
        H.plan_elbow_radius_mm * math.radians(H.plan_elbow_angle_deg)
        + H.inter_elbow_straight_mm
    )
    rise_group = H.rise_elbow_radius_mm * math.pi / 2.0
    offset_group = metadata["physical_length_mm"] - plan_group - rise_group
    return plan_group, rise_group, offset_group, metadata["physical_length_mm"]


def _compound_route_length() -> float:
    return _header_route_wire().length


def _compound_route_state(
    t: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    route = _header_route_wire()
    point = route.position_at(max(0.0, min(1.0, t)))
    tangent = route.tangent_at(max(0.0, min(1.0, t))).normalized()
    return (point.X, point.Y, point.Z), (tangent.X, tangent.Y, tangent.Z)


def _simple_internal_tube(port_airway: Any, port_outer: Any) -> tuple[Any, Any]:
    lower_z = -base.D.height / 2.0
    lower_clip = Pos(
        0.0,
        base.D.center_y,
        (lower_z + base.D.internal_tower_bottom_z) / 2.0,
    ) * Box(300.0, 300.0, base.D.internal_tower_bottom_z - lower_z)
    enclosure_clip = base._outer_envelope() & lower_clip
    in_box_outer = base._primary_shape(port_outer & enclosure_clip)
    in_box_airway = base._primary_shape(port_airway & enclosure_clip)
    tube = base._require_single_solid(
        (in_box_outer - in_box_airway).clean().fix(),
        feature="mount-free modular-header internal tube",
    )
    return tube, in_box_outer


def _simple_upper_displacement(port_outer: Any) -> Any:
    roof_z = base.D.height / 2.0
    clip = Pos(
        0.0,
        base.D.center_y,
        (base.D.internal_tower_bottom_z + roof_z) / 2.0,
    ) * Box(300.0, 300.0, roof_z - base.D.internal_tower_bottom_z)
    return base._primary_shape(port_outer & base._outer_envelope() & clip)


def _simple_tower(outlet_z: float) -> tuple[Any, Any, Any]:
    airway, outer = base._path_solids(outlet_z)
    clip_height = outlet_z - base.D.internal_tower_bottom_z + 30.0
    clip = Pos(
        0.0,
        base.D.center_y,
        base.D.internal_tower_bottom_z + clip_height / 2.0,
    ) * Box(300.0, 300.0, clip_height)
    tower_outer = base._primary_shape(outer & clip)
    tower = base._require_single_solid(
        (tower_outer - airway).clean().fix(),
        feature="mount-free straight circular tower",
    )
    return tower, airway, outer


def _empty_platforms() -> Compound:
    return Compound(children=[])


base._compound_route_ellipse = _compound_route_ellipse
base._compound_route_base_lengths = _compound_route_base_lengths
base._compound_route_length = _compound_route_length
base._compound_route_state = _compound_route_state
base.build_internal_tube = _simple_internal_tube
base._internal_tower_mount_displacement = _simple_upper_displacement
base.build_tower = _simple_tower
base._tube_mount_insert_pockets = lambda: []
base._internal_tower_mount_insert_pockets = lambda: []
base._internal_tower_mount_clearance_holes = lambda: []
base._internal_tower_mount_platforms = _empty_platforms


def _rewrite_diagnostics(diagnostics: dict[str, Any]) -> dict[str, Any]:
    route = _header_route_metadata()
    diagnostics["name"] = base.D.name
    diagnostics["status"] = (
        "40 mm constant-circle modular-header core with four tangent elbows, "
        f"39 Hz target, and {route['physical_length_mm']:.2f} mm in-box route"
    )
    diagnostics["alignment"]["type"] = (
        "single-port bass reflex with a front-facing circular inlet; a "
        f"{H.plan_elbow_angle_deg:g}-degree R{H.plan_elbow_radius_mm:g} plan "
        "elbow; one R50 rise elbow; and two rotated 67-degree R50 offset "
        "elbows returning to the straight centered tower"
    )
    diagnostics["isolation"] = {
        "experiment_dir": "experiments/sand_cube_190x210_header_port",
        "output_dir": "build/sand_cube_190x210_header_port",
        "smooth_39mm_variant_modified": False,
    }
    diagnostics["header_route_inputs"] = asdict(H)
    diagnostics["enclosure"]["construction"] = (
        "The established 190 x 210 x 190 enclosure, centered black-hole face, "
        "GX16, fill blisters, solid floor, and port-relieved brace network are "
        "retained. This study contains only the 40 mm acoustic tube shells; "
        "join collars, tube tabs, heat-set platforms, and the horn load path "
        "are intentionally deferred."
    )
    brace_data = diagnostics["enclosure"]["restored_original_features"][
        "internal_bracing"
    ]
    brace_data["floor_support_is_solid_floor_insert_pockets"] = False
    brace_data["tube_mounting_features_deferred"] = True
    brace_data["design_intent"] = (
        "The top and side brace network and four conformal black-hole roots "
        "remain for packaging reference. Port clearance is cut from the braces, "
        "but no tube mounts are included in this core-geometry pass."
    )

    port = diagnostics["port"]
    port["airway_ellipse_mm"] = [40.0, 40.0]
    port["constant_area_airway_diameter_mm"] = 40.0
    port["separate_printed_internal_tube"] = {
        "enabled": True,
        "core_shell_only": True,
        "join_collars_deferred": True,
        "mounting_tabs_deferred": True,
        "heat_set_insert_features_deferred": True,
    }
    port["internally_mounted_upper_tower"] = {
        "core_shell_only": True,
        "visible_airway_profile": "constant 40 mm circle",
        "visible_wall_thickness_mm": base.D.structural_tower_wall_t,
        "load_bearing_mount_design_deferred": True,
    }
    port["asymmetric_route"] = route
    rise_x, rise_y, _rise_z = route["rise_elbow_exit_xyz_mm"]
    side_acoustic_face_x = base.D.width / 2.0 - base.D.wall_stack_t
    rear_acoustic_face_y = (
        base.D.center_y + base.D.depth / 2.0 - base.D.wall_stack_t
    )
    route["packaging_clearance_mm"] = {
        "right_side_nominal": side_acoustic_face_x
        - (rise_x + base.D.outer_rx),
        "right_side_installation_envelope": side_acoustic_face_x
        - (rise_x + base.D.outer_rx + base.D.tube_install_clearance),
        "rear_nominal": rear_acoustic_face_y - (rise_y + base.D.outer_rz),
        "rear_installation_envelope": rear_acoustic_face_y
        - (rise_y + base.D.outer_rz + base.D.tube_install_clearance),
    }
    port["bend_count"] = 4
    port["broad_plan_sweep_count"] = 1
    port["discrete_vertical_elbow_count"] = 3
    port["header_manufacturing_analogy"] = (
        "constant-radius elbows and short straight coupons, with elbow planes "
        "rotated in 3D like a fabricated exhaust header"
    )

    horn_data = diagnostics["geometry"]["horn_and_de250"]
    horn_data.pop("three_spoke_driver_support_replaces_half_cup", None)
    horn_data.pop("driver_support", None)
    horn_data["driver_mount_status"] = (
        "reference placement only; tube-to-DE250 structure deferred"
    )
    diagnostics["geometry"]["single_external_rising_support"] = False
    diagnostics["geometry"]["structural_mounts_deferred"] = True

    if OLD_DIAGNOSTICS.exists():
        old = json.loads(OLD_DIAGNOSTICS.read_text())
        diagnostics["comparison_to_smooth_39mm_variant"] = {
            "old_bore_diameter_mm": old["port"][
                "constant_area_airway_diameter_mm"
            ],
            "new_bore_diameter_mm": 40.0,
            "port_area_change_percent": 100.0
            * (
                diagnostics["port"]["area_mm2"]
                / old["port"]["area_mm2"]
                - 1.0
            ),
            "old_net_box_volume_l": old["volume_accounting"][
                "final_modeled_net_box_volume_l"
            ],
            "new_net_box_volume_l": diagnostics["volume_accounting"][
                "final_modeled_net_box_volume_l"
            ],
            "net_volume_change_l": diagnostics["volume_accounting"][
                "final_modeled_net_box_volume_l"
            ]
            - old["volume_accounting"]["final_modeled_net_box_volume_l"],
            "old_in_box_port_envelope_l": old["volume_accounting"][
                "internal_port_envelope_including_air_l"
            ],
            "new_in_box_port_envelope_l": diagnostics["volume_accounting"][
                "internal_port_envelope_including_air_l"
            ],
            "old_compound_route_length_mm": old["port"]["lengths"][
                "compound_route_physical_length_mm"
            ],
            "new_compound_route_length_mm": route["physical_length_mm"],
            "old_outlet_top_z_mm": old["port"]["lengths"]["outlet_z_mm"],
            "new_outlet_top_z_mm": diagnostics["port"]["lengths"][
                "outlet_z_mm"
            ],
            "old_tuning_hz": old["alignment"]["calculated_tuning_hz"],
            "new_tuning_hz": diagnostics["alignment"]["calculated_tuning_hz"],
        }

    diagnostics["moderate_volume_limits"] = [
        (
            "The 40 mm bore has 3.9% more area than the smooth 39.243 mm "
            "variant, lowering velocity for the same volume flow but requiring "
            "more effective length at the same box volume and tuning."
        ),
        (
            "Four elbow modules simplify generation and print orientation, but "
            f"their {route['total_direction_change_deg']:.0f} degree total "
            "direction change and 1.25D minimum radius are an acoustic "
            "compromise versus the broader spline route."
        ),
        (
            "No empirical bend-loss correction is baked into the Helmholtz "
            "length. Final tuning, compression, and noise must be measured on "
            "a printed core before mounts and couplers are frozen."
        ),
    ]
    diagnostics["files"]["diagnostics"] = str(OUT / "diagnostics.json")
    return diagnostics


def generate() -> dict[str, Any]:
    diagnostics = base.generate()
    diagnostics = _rewrite_diagnostics(diagnostics)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
