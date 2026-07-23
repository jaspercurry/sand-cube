"""Route the 40 mm port through both lower rear cabinet corners.

This isolated derivative preserves the serviceable exterior tower and the
separately printable squat absorber. The floor path is deliberately simple:
a short rearward straight, a 90-degree R75 left-rear sweep, a 0.5 mm tangent
connector, and a 90-degree R50 right-rear rise. The upper header then uses four
rotated R35.7 elbows around the exact 56 mm absorber service straight.

The absorber D-flat has exact nominal contact with the rear acoustic face. No
mounting tab or enclosure node is added in this pass.
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
from dataclasses import replace
from pathlib import Path
from typing import Any

from build123d import Edge, Vector, Wire


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = (
    ROOT / "experiments" / "sand_cube_190x210_internal_squat_absorber_flush"
)
sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_flush as flush  # noqa: E402


prior = flush.prior
serviceable = flush.serviceable
header = flush.header
base = flush.base
OUT = ROOT / "build" / "sand_cube_190x210_internal_squat_absorber_rear_corners"
prior.OUT = OUT
serviceable.OUT = OUT
header.OUT = OUT
base.OUT = OUT


REAR_ACOUSTIC_FACE_Y = 108.0
ABSORBER_CENTER_TO_D_FLAT = 28.5
ABSORBER_AXIS_Y = REAR_ACOUSTIC_FACE_Y - ABSORBER_CENTER_TO_D_FLAT
LOWER_RISE_X = 64.0
LOWER_RISE_Y = 84.0
FLOOR_PLAN_RADIUS_MM = 75.0
FLOOR_PLAN_ANGLE_DEG = 90.0
FLOOR_REAR_STRAIGHT_MM = 19.25
FLOOR_BACK_TANGENT_MM = 0.5
RISE_RADIUS_MM = 50.0

UPPER_RADIUS_MM = 35.7
PRE_HEADER_VERTICAL_MM = 0.5
FINAL_HEADER_VERTICAL_MM = 2.0
ABSORBER_CONNECTED_LENGTH = prior.ABSORBER_CONNECTED_LENGTH

# Solved spatial header directions. The pre-absorber tangent points gently
# forward, the absorber itself runs at constant y, and the post-absorber
# tangent points rearward into the unchanged y=82 mm tower.
ABSORBER_POLAR_DEG = 45.0761128536401
PRE_TANGENT_POLAR_DEG = 31.65431420155988
PRE_TANGENT_YAW_DEG = -29.824441468094285
POST_TANGENT_POLAR_DEG = 28.99797713036616
POST_TANGENT_YAW_DEG = 19.5041271846978


header.H = replace(
    header.H,
    plan_elbow_radius_mm=FLOOR_PLAN_RADIUS_MM,
    plan_elbow_angle_deg=FLOOR_PLAN_ANGLE_DEG,
    inter_elbow_straight_mm=(
        FLOOR_REAR_STRAIGHT_MM + FLOOR_BACK_TANGENT_MM
    ),
    rise_elbow_radius_mm=RISE_RADIUS_MM,
    offset_elbow_radius_mm=UPPER_RADIUS_MM,
    offset_elbow_angle_deg=ABSORBER_POLAR_DEG,
)
base.D = replace(
    base.D,
    name="sand_cube_190x210_rear_corner_sweeps_d_squat_absorber",
    lower_elbow_vertical_x=LOWER_RISE_X,
    lower_elbow_vertical_y=LOWER_RISE_Y,
)


def _angle_between(a: Vector, b: Vector) -> float:
    return math.acos(max(-1.0, min(1.0, a.normalized().dot(b.normalized()))))


def _direction(*, polar_deg: float, yaw_deg: float) -> Vector:
    polar = math.radians(polar_deg)
    yaw = math.radians(yaw_deg)
    return Vector(
        -math.cos(yaw) * math.sin(polar),
        math.sin(yaw) * math.sin(polar),
        math.cos(polar),
    ).normalized()


def _rear_corner_route_geometry() -> tuple[Wire, dict[str, Any]]:
    d = base.D
    p0 = Vector(d.inlet_throat_x, d.inlet_throat_y, d.horizontal_z)
    direction = Vector(0.0, 1.0, 0.0)
    vertical = Vector(0.0, 0.0, 1.0)
    edges: list[Edge] = []

    # Approach the left-rear R75 sweep on a straight tangent.
    point = p0 + direction * FLOOR_REAR_STRAIGHT_MM
    edges.append(Edge.make_line(p0, point))

    plan_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        Vector(0.0, 0.0, -1.0),
        FLOOR_PLAN_RADIUS_MM,
        math.radians(FLOOR_PLAN_ANGLE_DEG),
    )
    edges.append(plan_arc)

    next_point = point + direction * FLOOR_BACK_TANGENT_MM
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    # The R50 rise occupies the lower-right rear corner and ends vertical.
    rise_normal = direction.cross(vertical).normalized()
    rise_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        rise_normal,
        RISE_RADIUS_MM,
        math.pi / 2.0,
    )
    edges.append(rise_arc)
    rise_exit = Vector(point.X, point.Y, point.Z)
    expected_rise = Vector(LOWER_RISE_X, LOWER_RISE_Y, -15.0)
    if (rise_exit - expected_rise).length > 0.001:
        raise ValueError(
            "Rear-corner rise missed its target by "
            f"{(rise_exit - expected_rise).length:.6f} mm"
        )

    next_point = point + vertical * PRE_HEADER_VERTICAL_MM
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    absorber_direction = _direction(
        polar_deg=ABSORBER_POLAR_DEG,
        yaw_deg=0.0,
    )
    pre_direction = _direction(
        polar_deg=PRE_TANGENT_POLAR_DEG,
        yaw_deg=PRE_TANGENT_YAW_DEG,
    )
    post_direction = _direction(
        polar_deg=POST_TANGENT_POLAR_DEG,
        yaw_deg=POST_TANGENT_YAW_DEG,
    )

    pre_main_angle = _angle_between(direction, pre_direction)
    pre_main, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        direction.cross(pre_direction).normalized(),
        UPPER_RADIUS_MM,
        pre_main_angle,
    )
    edges.append(pre_main)

    pre_twist_angle = _angle_between(direction, absorber_direction)
    pre_twist, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        direction.cross(absorber_direction).normalized(),
        UPPER_RADIUS_MM,
        pre_twist_angle,
    )
    edges.append(pre_twist)
    absorber_start = Vector(point.X, point.Y, point.Z)
    if abs(absorber_start.Y - ABSORBER_AXIS_Y) > 0.001:
        raise ValueError(
            "Absorber straight missed the rear-wall datum: "
            f"axis y={absorber_start.Y:.6f} mm"
        )

    next_point = point + absorber_direction * ABSORBER_CONNECTED_LENGTH
    edges.append(Edge.make_line(point, next_point))
    point = next_point
    direction = absorber_direction

    post_twist_angle = _angle_between(direction, post_direction)
    post_twist, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        direction.cross(post_direction).normalized(),
        UPPER_RADIUS_MM,
        post_twist_angle,
    )
    edges.append(post_twist)

    return_angle = _angle_between(direction, vertical)
    return_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        direction.cross(vertical).normalized(),
        UPPER_RADIUS_MM,
        return_angle,
    )
    edges.append(return_arc)

    endpoint = Vector(
        header.H.target_tower_x_mm,
        header.H.target_tower_y_mm,
        header.H.target_tower_z_mm,
    )
    next_point = point + vertical * FINAL_HEADER_VERTICAL_MM
    edges.append(Edge.make_line(point, next_point))
    wire = Wire(edges)
    endpoint_error = (next_point - endpoint).length
    if endpoint_error > 0.002:
        raise ValueError(
            f"Rear-corner route endpoint error is {endpoint_error:.6f} mm"
        )
    tangent_error = (wire.tangent_at(1.0).normalized() - vertical).length
    if tangent_error > 0.001:
        raise ValueError(
            f"Rear-corner route tangent error is {tangent_error:.6f}"
        )

    upper_angles_deg = [
        math.degrees(pre_main_angle),
        math.degrees(pre_twist_angle),
        math.degrees(post_twist_angle),
        math.degrees(return_angle),
    ]
    inner_wall_x = d.width / 2.0 - d.wall_stack_t
    rear_wall_y = d.center_y + d.depth / 2.0 - d.wall_stack_t
    tube_outer_radius = d.port_rx + d.port_wall_t
    metadata = {
        "module_order": [
            f"{FLOOR_REAR_STRAIGHT_MM:.3f} mm rearward floor straight",
            "90 degree R75 lower-left rear sweep",
            f"{FLOOR_BACK_TANGENT_MM:.3f} mm rear-wall tangent",
            "90 degree R50 lower-right rear rise",
            f"{PRE_HEADER_VERTICAL_MM:.3f} mm vertical collar straight",
            f"{upper_angles_deg[0]:.3f} degree R{UPPER_RADIUS_MM:g} pre-absorber elbow",
            f"{upper_angles_deg[1]:.3f} degree R{UPPER_RADIUS_MM:g} pre-absorber steering elbow",
            f"{ABSORBER_CONNECTED_LENGTH:.3f} mm rear-flush absorber straight",
            f"{upper_angles_deg[2]:.3f} degree R{UPPER_RADIUS_MM:g} post-absorber steering elbow",
            f"{upper_angles_deg[3]:.3f} degree R{UPPER_RADIUS_MM:g} tower return elbow",
            f"{FINAL_HEADER_VERTICAL_MM:.3f} mm final vertical straight",
        ],
        "elbow_angles_deg": [
            FLOOR_PLAN_ANGLE_DEG,
            90.0,
            *upper_angles_deg,
        ],
        "elbow_centerline_radii_mm": [
            FLOOR_PLAN_RADIUS_MM,
            RISE_RADIUS_MM,
            *([UPPER_RADIUS_MM] * 4),
        ],
        "total_direction_change_deg": (
            FLOOR_PLAN_ANGLE_DEG + 90.0 + sum(upper_angles_deg)
        ),
        "inter_elbow_straight_mm": (
            FLOOR_REAR_STRAIGHT_MM + FLOOR_BACK_TANGENT_MM
        ),
        "offset_diagonal_straight_mm": ABSORBER_CONNECTED_LENGTH,
        "short_vertical_straights_mm": [
            PRE_HEADER_VERTICAL_MM,
            FINAL_HEADER_VERTICAL_MM,
        ],
        "lateral_offset_mm": math.hypot(
            LOWER_RISE_X - header.H.target_tower_x_mm,
            LOWER_RISE_Y - header.H.target_tower_y_mm,
        ),
        "lateral_offset_direction_xy": [
            -LOWER_RISE_X
            / math.hypot(LOWER_RISE_X, LOWER_RISE_Y - header.H.target_tower_y_mm),
            (header.H.target_tower_y_mm - LOWER_RISE_Y)
            / math.hypot(LOWER_RISE_X, LOWER_RISE_Y - header.H.target_tower_y_mm),
        ],
        "rise_elbow_exit_xyz_mm": [rise_exit.X, rise_exit.Y, rise_exit.Z],
        "route_start_xyz_mm": [p0.X, p0.Y, p0.Z],
        "route_end_xyz_mm": [endpoint.X, endpoint.Y, endpoint.Z],
        "physical_length_mm": wire.length,
        "minimum_centerline_radius_to_bore_ratio": (
            min(FLOOR_PLAN_RADIUS_MM, RISE_RADIUS_MM, UPPER_RADIUS_MM)
            / d.port_width
        ),
        "all_sections_constant_circle": True,
        "all_curves_constant_radius": True,
        "bespoke_spline_sections": 0,
        "absorber_axis_parallel_to_rear_wall": True,
        "absorber_axis_y_mm": ABSORBER_AXIS_Y,
        "absorber_d_flat_nominal_rear_clearance_mm": 0.0,
        "lower_left_nominal_side_clearance_mm": (
            d.inlet_throat_x - tube_outer_radius - (-inner_wall_x)
        ),
        "lower_rear_nominal_clearance_mm": (
            rear_wall_y - (LOWER_RISE_Y + tube_outer_radius)
        ),
        "lower_right_nominal_side_clearance_mm": (
            inner_wall_x - (LOWER_RISE_X + tube_outer_radius)
        ),
        "pre_absorber_rearward_shift_mm": LOWER_RISE_Y - ABSORBER_AXIS_Y,
        "post_absorber_rearward_shift_mm": (
            header.H.target_tower_y_mm - ABSORBER_AXIS_Y
        ),
        "upper_elbow_angles_deg": upper_angles_deg,
    }
    return wire, metadata


header._header_route_geometry = _rear_corner_route_geometry


def _absorber_straight() -> tuple[Any, Vector, Vector]:
    route = header._header_route_wire()
    edges = route.edges()
    if len(edges) != 11:
        raise ValueError(f"Expected eleven route modules, got {len(edges)}")
    straight = edges[7]
    if abs(straight.length - ABSORBER_CONNECTED_LENGTH) > 0.01:
        raise ValueError(
            "Absorber service straight missed its connected length: "
            f"{straight.length:.6f} mm"
        )
    center = straight.position_at(0.5)
    tangent = straight.tangent_at(0.5).normalized()
    if abs(tangent.Y) > 1e-8:
        raise ValueError(
            f"Rear-flush absorber axis has y slope {tangent.Y:.9f}"
        )
    return straight, center, tangent


prior._absorber_straight = _absorber_straight


def _absorber_checks() -> dict[str, Any]:
    material = prior._place_local(prior._local_absorber_material())
    gross = prior._place_local(prior._local_absorber_gross_envelope())
    airway, _outer = base._path_solids(base.D.baseline_outlet_top_z)
    woofer = prior.Pos(
        0.0,
        0.0,
        base.BLACK_HOLE_CENTER_Z,
    ) * base._confirmed_woofer(base.P)
    rear_inner_y = base.D.center_y + base.D.depth / 2.0 - base.D.wall_stack_t
    body_bbox = gross.bounding_box()
    material_in_airway = base._bounded_intersection_volume(material, airway)
    gross_to_woofer = base._bounded_intersection_volume(gross, woofer)
    if material_in_airway > 0.001:
        raise ValueError(
            f"Absorber blocks the 40 mm airway by {material_in_airway:.6f} mm3"
        )
    if gross_to_woofer > 0.001:
        raise ValueError(
            f"Absorber envelope intersects the woofer by {gross_to_woofer:.6f} mm3"
        )
    straight, center, tangent = _absorber_straight()
    route = header._header_route_wire()
    path_before_straight = base.D.inlet_flare_l + sum(
        edge.length for edge in route.edges()[:7]
    )
    absorber_center_path = path_before_straight + straight.length / 2.0
    total_physical = (
        base.D.inlet_flare_l
        + route.length
        + (
            base.D.baseline_outlet_top_z
            - base.D.outlet_flare_l
            - header.H.target_tower_z_mm
        )
        + base.D.outlet_flare_l
    )
    coupling = math.sin(math.pi * absorber_center_path / total_physical) ** 2
    return {
        "straight_center_xyz_mm": [center.X, center.Y, center.Z],
        "straight_tangent_xyz": [tangent.X, tangent.Y, tangent.Z],
        "absorber_center_path_mm_from_inlet": absorber_center_path,
        "provisional_physical_path_mm_at_baseline_top": total_physical,
        "first_mode_pressure_squared_coupling_fraction": coupling,
        "rear_acoustic_face_y_mm": rear_inner_y,
        "installed_envelope_bbox_min_mm": [
            body_bbox.min.X,
            body_bbox.min.Y,
            body_bbox.min.Z,
        ],
        "installed_envelope_bbox_max_mm": [
            body_bbox.max.X,
            body_bbox.max.Y,
            body_bbox.max.Z,
        ],
        "minimum_rear_wall_clearance_mm": rear_inner_y - body_bbox.max.Y,
        "material_intrusion_into_airway_mm3": material_in_airway,
        "gross_envelope_to_woofer_mm3": gross_to_woofer,
    }


prior._absorber_checks = _absorber_checks


def generate() -> dict[str, Any]:
    diagnostics = prior.generate()
    route_metadata = header._header_route_metadata()
    placement = diagnostics["internal_squat_absorber"]["placement"]
    if abs(placement["minimum_rear_wall_clearance_mm"]) > 0.002:
        raise ValueError(
            "Absorber D-flat missed exact nominal rear-wall contact: "
            f"{placement['minimum_rear_wall_clearance_mm']:.6f} mm"
        )

    diagnostics["name"] = base.D.name
    diagnostics["status"] = (
        "40 mm rear-corner floor sweeps with exact rear-flush squat absorber "
        "and unchanged serviceable exterior tower"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/sand_cube_190x210_internal_squat_absorber_rear_corners"
        ),
        "output_dir": (
            "build/sand_cube_190x210_internal_squat_absorber_rear_corners"
        ),
        "prior_flush_absorber_variant_modified": False,
        "standalone_absorber_source_modified": False,
    }
    diagnostics["alignment"]["type"] = (
        "single 40 mm circular port with an R75 lower-left rear sweep, R50 "
        "lower-right rear rise, exact rear-flush 56 mm absorber straight, "
        "four rotated R35.7 upper elbows, and unchanged exterior tower"
    )
    diagnostics["internal_squat_absorber"]["route_changes"] = {
        "lower_rise_center_xy_mm": [LOWER_RISE_X, LOWER_RISE_Y],
        "floor_rear_straight_mm": FLOOR_REAR_STRAIGHT_MM,
        "lower_left_sweep_angle_deg": FLOOR_PLAN_ANGLE_DEG,
        "lower_left_sweep_radius_mm": FLOOR_PLAN_RADIUS_MM,
        "rear_wall_tangent_mm": FLOOR_BACK_TANGENT_MM,
        "lower_right_rise_angle_deg": 90.0,
        "lower_right_rise_radius_mm": RISE_RADIUS_MM,
        "upper_elbow_count": 4,
        "upper_elbow_angles_deg": route_metadata["upper_elbow_angles_deg"],
        "upper_elbow_radius_mm": UPPER_RADIUS_MM,
        "upper_radius_to_bore_ratio": UPPER_RADIUS_MM / base.D.port_width,
        "absorber_service_straight_mm": ABSORBER_CONNECTED_LENGTH,
        "absorber_axis_y_mm": ABSORBER_AXIS_Y,
        "absorber_nominal_rear_clearance_mm": 0.0,
    }
    diagnostics["internal_squat_absorber"]["manufacturing"].update(
        {
            "entire_d_flat_exact_nominal_rear_contact": True,
            "modeled_printing_relief_mm": 0.0,
            "future_mounting_tab_included": False,
            "rear_wall_mounting_node_included": False,
        }
    )
    diagnostics["alignment"]["packaging_tuning_tradeoff"].update(
        {
            "both_lower_rear_corners_used": True,
            "exterior_tower_xy_and_height_preserved": True,
            "current_natural_tuning_hz": diagnostics["alignment"][
                "calculated_tuning_hz"
            ],
            "exact_39p1_hz_recovery_deferred": False,
            "remaining_offset_above_39p1_hz": diagnostics["alignment"][
                "calculated_tuning_hz"
            ]
            - 39.1,
            "approximate_additional_internal_effective_length_needed_mm": 3.0,
        }
    )
    diagnostics["moderate_volume_limits"][1] = (
        "The floor route uses broad R75 and R50 corner sweeps. The four "
        "upper steering elbows use R35.7 centerlines (0.893D), retain the "
        "40 mm circular bore, and avoid spline or flattened sections."
    )
    diagnostics["files"]["diagnostics"] = str(OUT / "diagnostics.json")
    diagnostics["files"]["exterior_viewer"] = str(OUT / "viewer" / "index.html")
    diagnostics["files"]["cutaway_viewer"] = str(
        OUT / "cutaway_viewer" / "index.html"
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
