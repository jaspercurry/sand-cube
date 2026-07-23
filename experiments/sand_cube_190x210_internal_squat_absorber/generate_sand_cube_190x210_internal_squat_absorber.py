"""Install the ultra-squat slotted absorber inside the serviceable enclosure.

This isolated packaging variant preserves the proven serviceable tower and the
40 mm acoustic bore.  The lower plan route is moved forward enough to give the
D-shaped absorber a real rear-wall installation gap.  The former pair of
67-degree offset elbows is replaced by a symmetric header pair surrounding a
56 mm straight: exactly the connected length of the unmodified squat absorber.

The absorber remains a separately printable four-piece cartridge.  The host
tube is interrupted only between the two adapter shoulders; its 40 mm airway
remains continuous and unobstructed.
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
from dataclasses import replace
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Compound,
    Cylinder,
    Plane,
    Pos,
    Unit,
    Vector,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
SERVICEABLE_EXPERIMENT = ROOT / "experiments" / "sand_cube_190x210_serviceable_tower"
sys.path.insert(0, str(SERVICEABLE_EXPERIMENT))

import generate_sand_cube_190x210_serviceable_tower as serviceable  # noqa: E402

from experiments.sand_cube_190x210_port_absorber_slotted_d_squat import (  # noqa: E402
    generate_port_absorber_slotted_d_squat as squat,
)


header = serviceable.header
base = serviceable.base
OUT = ROOT / "build" / "sand_cube_190x210_internal_squat_absorber"
base.OUT = OUT
header.OUT = OUT
serviceable.OUT = OUT


# The exact connected absorber is 56 mm long.  Moving the rise forward to
# y=72 mm leaves the D-flat approximately 1 mm ahead of the rear acoustic face
# after accounting for the diagonal axis and the complete adapter stack.
ABSORBER_CONNECTED_LENGTH = 56.0
TARGET_RISE_X = 64.0
TARGET_RISE_Y = 72.0
OFFSET_SHORT_VERTICAL = 2.0
ABSORBER_ROLL_DEG = 0.0  # D-flat faces the rear wall; chamber lobe faces forward.
ABSORBER_BRACE_CLEARANCE = 1.0
HOST_BREAK_HALF_LENGTH = 18.0  # 30 mm body plus two 3 mm adapter plates.
HOST_BREAK_RADIUS = 24.0


def _solve_plan_route() -> tuple[float, float]:
    """Solve the R75 plan elbow and straight for the shifted rise location."""
    start_x = base.D.inlet_throat_x
    start_y = base.D.inlet_throat_y
    radius = header.H.plan_elbow_radius_mm
    rise_radius = header.H.rise_elbow_radius_mm
    angle = math.radians(82.5)
    straight = 11.0
    for _ in range(30):
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        x = start_x + radius * (1.0 - cos_a) + (straight + rise_radius) * sin_a
        y = start_y + radius * sin_a + (straight + rise_radius) * cos_a
        fx = x - TARGET_RISE_X
        fy = y - TARGET_RISE_Y
        dx_da = radius * sin_a + (straight + rise_radius) * cos_a
        dx_ds = sin_a
        dy_da = radius * cos_a - (straight + rise_radius) * sin_a
        dy_ds = cos_a
        determinant = dx_da * dy_ds - dx_ds * dy_da
        angle -= (fx * dy_ds - dx_ds * fy) / determinant
        straight -= (dx_da * fy - fx * dy_da) / determinant
    return math.degrees(angle), straight


def _solve_offset_route(lateral_distance: float) -> tuple[float, float]:
    """Solve equal elbows around the exact 56 mm absorber straight."""
    available_vertical = header.H.target_tower_z_mm - (-15.0)
    elbow_vertical = available_vertical - 2.0 * OFFSET_SHORT_VERTICAL
    radius = 39.0
    angle = math.radians(46.5)
    for _ in range(30):
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        f_lateral = (
            2.0 * radius * (1.0 - cos_a)
            + ABSORBER_CONNECTED_LENGTH * sin_a
            - lateral_distance
        )
        f_vertical = (
            2.0 * radius * sin_a
            + ABSORBER_CONNECTED_LENGTH * cos_a
            - elbow_vertical
        )
        dl_dr = 2.0 * (1.0 - cos_a)
        dl_da = 2.0 * radius * sin_a + ABSORBER_CONNECTED_LENGTH * cos_a
        dv_dr = 2.0 * sin_a
        dv_da = 2.0 * radius * cos_a - ABSORBER_CONNECTED_LENGTH * sin_a
        determinant = dl_dr * dv_da - dl_da * dv_dr
        radius -= (f_lateral * dv_da - dl_da * f_vertical) / determinant
        angle -= (dl_dr * f_vertical - f_lateral * dv_dr) / determinant
    return radius, math.degrees(angle)


PLAN_ANGLE_DEG, PLAN_STRAIGHT_MM = _solve_plan_route()
LATERAL_DISTANCE = math.hypot(
    TARGET_RISE_X - header.H.target_tower_x_mm,
    TARGET_RISE_Y - header.H.target_tower_y_mm,
)
OFFSET_RADIUS_MM, OFFSET_ANGLE_DEG = _solve_offset_route(LATERAL_DISTANCE)

header.H = replace(
    header.H,
    plan_elbow_angle_deg=PLAN_ANGLE_DEG,
    inter_elbow_straight_mm=PLAN_STRAIGHT_MM,
    offset_elbow_radius_mm=OFFSET_RADIUS_MM,
    offset_elbow_angle_deg=OFFSET_ANGLE_DEG,
)
base.D = replace(
    base.D,
    name="sand_cube_190x210_internal_d_squat_absorber",
    lower_elbow_vertical_x=TARGET_RISE_X,
    lower_elbow_vertical_y=TARGET_RISE_Y,
    # Preserve the established exterior height rather than allowing the lost
    # box volume to push the outlet above the DE250 body.  This packaging pass
    # therefore lands just below 40 Hz; a later route pass can recover the
    # remaining internal effective length if an exact 39.1 Hz target is kept.
    target_tuning_hz=39.75065,
    target_outlet_drop=28.8954,
)


ABSORBER_DESIGN = squat._solve_arc_radius(squat.D)
squat._validate_design(ABSORBER_DESIGN)
ABSORBER_GEOMETRY = squat._build_geometry(ABSORBER_DESIGN)


def _fresh_solids(shape: Any) -> list[Any]:
    return [copy.copy(solid) for solid in shape.solids()]


def _rotate(vector: Vector, axis: Vector, angle_rad: float) -> Vector:
    axis = axis.normalized()
    return (
        vector * math.cos(angle_rad)
        + axis.cross(vector) * math.sin(angle_rad)
        + axis * axis.dot(vector) * (1.0 - math.cos(angle_rad))
    )


def _absorber_straight() -> tuple[Any, Vector, Vector]:
    route = header._header_route_wire()
    edges = route.edges()
    if len(edges) != 8:
        raise ValueError(f"Expected eight header modules, got {len(edges)}")
    straight = edges[5]
    if abs(straight.length - ABSORBER_CONNECTED_LENGTH) > 0.01:
        raise ValueError(
            "Absorber service straight missed its connected length: "
            f"{straight.length:.6f} mm"
        )
    center = straight.position_at(0.5)
    tangent = straight.tangent_at(0.5).normalized()
    return straight, center, tangent


def _absorber_plane() -> Plane:
    _straight, center, tangent = _absorber_straight()
    rear = Vector(0.0, 1.0, 0.0)
    rear_projected = (rear - tangent * rear.dot(tangent)).normalized()
    # Local -X is the D-flat.  Local +X therefore points away from the rear
    # wall, into the useful open cabinet volume.
    x_direction = rear_projected * -1.0
    x_direction = _rotate(
        x_direction,
        tangent,
        math.radians(ABSORBER_ROLL_DEG),
    ).normalized()
    return Plane(origin=center, x_dir=x_direction, z_dir=tangent)


def _place_local(shape: Any) -> Any:
    # The connected local assembly spans z=-13..43 mm, centered at z=15 mm.
    centered = Pos(0.0, 0.0, -15.0) * shape
    return _absorber_plane().from_local_coords(centered)


def _local_absorber_material() -> Any:
    return Compound(
        children=_fresh_solids(
            ABSORBER_GEOMETRY["connected"]["3mm_wall"]
        )
    )


def _local_absorber_gross_envelope() -> Any:
    body = squat._outer_prism(
        height=ABSORBER_DESIGN.overall_length,
        z=0.0,
        design=ABSORBER_DESIGN,
    )
    socket_inner_r = (
        base.D.port_width
        + 2.0 * base.D.port_wall_t
        + ABSORBER_DESIGN.adapter_socket_clearance_diametral
    ) / 2.0
    socket_outer_r = socket_inner_r + ABSORBER_DESIGN.adapter_socket_wall_t
    lower_socket = Pos(0.0, 0.0, -13.0) * Cylinder(
        socket_outer_r,
        ABSORBER_DESIGN.adapter_socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    lower_plate = Pos(0.0, 0.0, -3.0) * Cylinder(
        ABSORBER_DESIGN.adapter_plate_r,
        ABSORBER_DESIGN.adapter_plate_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    upper_plate = Pos(0.0, 0.0, ABSORBER_DESIGN.overall_length) * Cylinder(
        ABSORBER_DESIGN.adapter_plate_r,
        ABSORBER_DESIGN.adapter_plate_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    upper_socket = Pos(0.0, 0.0, ABSORBER_DESIGN.overall_length + 3.0) * Cylinder(
        socket_outer_r,
        ABSORBER_DESIGN.adapter_socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return Compound(
        children=[body, lower_socket, lower_plate, upper_plate, upper_socket]
    )


def _local_absorber_installation_envelope() -> Any:
    clearance_design = replace(
        ABSORBER_DESIGN,
        d_outer_arc_radius=(
            ABSORBER_DESIGN.d_outer_arc_radius + ABSORBER_BRACE_CLEARANCE
        ),
        d_outer_flat_x=(
            ABSORBER_DESIGN.d_outer_flat_x - ABSORBER_BRACE_CLEARANCE
        ),
    )
    body = squat._outer_prism(
        height=ABSORBER_DESIGN.overall_length + 2.0 * ABSORBER_BRACE_CLEARANCE,
        z=-ABSORBER_BRACE_CLEARANCE,
        design=clearance_design,
    )
    socket_outer_r = (
        (base.D.port_width + 2.0 * base.D.port_wall_t + 0.40) / 2.0
        + ABSORBER_DESIGN.adapter_socket_wall_t
        + ABSORBER_BRACE_CLEARANCE
    )
    lower = Pos(0.0, 0.0, -13.0 - ABSORBER_BRACE_CLEARANCE) * Cylinder(
        socket_outer_r,
        13.0 + ABSORBER_BRACE_CLEARANCE,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    upper = Pos(0.0, 0.0, ABSORBER_DESIGN.overall_length) * Cylinder(
        socket_outer_r,
        13.0 + ABSORBER_BRACE_CLEARANCE,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return Compound(children=[body, lower, upper])


def _host_break_tool() -> Any:
    local = Pos(0.0, 0.0, -HOST_BREAK_HALF_LENGTH) * Cylinder(
        HOST_BREAK_RADIUS,
        2.0 * HOST_BREAK_HALF_LENGTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return _absorber_plane().from_local_coords(local)


ORIGINAL_BUILD_INTERNAL_TUBE = serviceable._internal_tube_with_male_spigot
ORIGINAL_SERVICEABLE_BRACES = base._restored_internal_braces


def _internal_tube_with_absorber(
    port_airway: Any,
    port_outer: Any,
) -> tuple[Any, Any]:
    host_tube, host_displacement = ORIGINAL_BUILD_INTERNAL_TUBE(
        port_airway, port_outer
    )
    host_cut = host_tube - _host_break_tool()
    host_remainder = Compound(
        children=[solid.clean().fix() for solid in host_cut.solids()]
    )
    absorber_material = _place_local(_local_absorber_material())
    absorber_gross = _place_local(_local_absorber_gross_envelope())

    tube = Compound(
        children=[
            *_fresh_solids(host_remainder),
            *_fresh_solids(absorber_material),
        ]
    )
    displacement = Compound(
        children=[
            *_fresh_solids(host_displacement),
            *_fresh_solids(absorber_gross),
        ]
    )
    return tube, displacement


def _braces_with_absorber_clearance(port_clearance: Any) -> Compound:
    braces = ORIGINAL_SERVICEABLE_BRACES(port_clearance)
    clearance = _place_local(_local_absorber_installation_envelope())
    retained: list[Any] = []
    for solid in braces.solids():
        retained.extend((solid - clearance).clean().fix().solids())
    return Compound(children=retained)


base.build_internal_tube = _internal_tube_with_absorber
base._restored_internal_braces = _braces_with_absorber_clearance


def _absorber_checks() -> dict[str, Any]:
    material = _place_local(_local_absorber_material())
    gross = _place_local(_local_absorber_gross_envelope())
    airway, _outer = base._path_solids(base.D.baseline_outlet_top_z)
    woofer = Pos(0.0, 0.0, base.BLACK_HOLE_CENTER_Z) * base._confirmed_woofer(
        base.P
    )
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
        edge.length for edge in route.edges()[:5]
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


def _export_absorber_parts() -> dict[str, Any]:
    installed = _place_local(_local_absorber_material())
    parts = {
        "internal_d_squat_absorber_installed.step": installed,
        "internal_d_squat_absorber_print_reference.step": (
            ABSORBER_GEOMETRY["connected"]["3mm_wall"]
        ),
    }
    checks: dict[str, Any] = {}
    for filename, shape in parts.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        checks[filename] = {
            "source_solid_count": len(shape.solids()),
            "imported_solid_count": len(imported.solids()),
            "all_imported_solids_valid": all(
                solid.is_valid for solid in imported.solids()
            ),
        }
        if (
            checks[filename]["source_solid_count"]
            != checks[filename]["imported_solid_count"]
            or not checks[filename]["all_imported_solids_valid"]
        ):
            raise ValueError(f"STEP round-trip failed for {filename}")
    return checks


def generate() -> dict[str, Any]:
    checks = _absorber_checks()
    diagnostics = serviceable.generate()
    actual_physical_length = diagnostics["port"]["lengths"][
        "physical_centerline_length_mm"
    ]
    checks["actual_physical_path_mm"] = actual_physical_length
    checks["first_mode_pressure_squared_coupling_fraction"] = math.sin(
        math.pi
        * checks["absorber_center_path_mm_from_inlet"]
        / actual_physical_length
    ) ** 2
    diagnostics["name"] = base.D.name
    diagnostics["status"] = (
        "serviceable 40 mm tower with an internally packaged 334.7 Hz "
        "D-shaped squat absorber on a dedicated diagonal service straight"
    )
    diagnostics["isolation"] = {
        "experiment_dir": "experiments/sand_cube_190x210_internal_squat_absorber",
        "output_dir": "build/sand_cube_190x210_internal_squat_absorber",
        "serviceable_tower_variant_modified": False,
        "squat_absorber_variant_modified": False,
    }
    diagnostics["alignment"]["type"] = (
        "single 40 mm circular port with an R75 lower plan sweep, one R50 "
        "rise, and two approximately 46-degree offset elbows surrounding an "
        "internal 56 mm absorber service straight"
    )
    diagnostics["alignment"]["packaging_tuning_tradeoff"] = {
        "exterior_tower_height_preserved": True,
        "current_natural_tuning_hz": diagnostics["alignment"][
            "calculated_tuning_hz"
        ],
        "exact_39p1_hz_recovery_deferred": True,
        "approximate_additional_internal_effective_length_needed_mm": 19.0,
    }
    diagnostics["internal_squat_absorber"] = {
        "source_experiment": (
            "experiments/sand_cube_190x210_port_absorber_slotted_d_squat"
        ),
        "source_geometry_modified": False,
        "continuous_bore_diameter_mm": base.D.port_width,
        "body_height_mm": ABSORBER_DESIGN.overall_length,
        "connected_length_mm": ABSORBER_CONNECTED_LENGTH,
        "body_footprint_mm": [
            74.96720390571545,
            76.9344078114309,
        ],
        "sealed_chamber_volume_cm3": ABSORBER_GEOMETRY["cavity_volume_cm3"],
        "target_absorber_frequency_hz": (
            ABSORBER_DESIGN.target_absorber_frequency_hz
        ),
        "nominal_finished_slot_width_mm": (
            ABSORBER_DESIGN.nominal_finished_slot_width
        ),
        "nominal_finished_slot_length_mm": (
            ABSORBER_GEOMETRY["nominal_slot_length_mm"]
        ),
        "placement": checks,
        "route_changes": {
            "right_rise_center_xy_mm": [TARGET_RISE_X, TARGET_RISE_Y],
            "plan_elbow_angle_deg": PLAN_ANGLE_DEG,
            "plan_straight_mm": PLAN_STRAIGHT_MM,
            "offset_elbow_count": 2,
            "offset_elbow_angle_deg": OFFSET_ANGLE_DEG,
            "offset_elbow_centerline_radius_mm": OFFSET_RADIUS_MM,
            "offset_centerline_radius_to_bore_ratio": (
                OFFSET_RADIUS_MM / base.D.port_width
            ),
            "service_straight_mm": ABSORBER_CONNECTED_LENGTH,
            "total_offset_direction_change_deg": 2.0 * OFFSET_ANGLE_DEG,
        },
        "manufacturing": {
            "absorber_is_separately_printable": True,
            "adapter_socket_depth_mm": ABSORBER_DESIGN.adapter_socket_depth,
            "host_tube_break_between_adapter_shoulders_mm": (
                2.0 * HOST_BREAK_HALF_LENGTH
            ),
            "d_flat_faces_rear_wall": True,
            "chamber_lobe_faces_forward": True,
            "brace_clearance_mm": ABSORBER_BRACE_CLEARANCE,
        },
        "separate_step_roundtrip": _export_absorber_parts(),
    }
    actual_final_straight = header._header_route_metadata()[
        "short_vertical_straights_mm"
    ][-1]
    diagnostics["serviceable_tower"]["modular_interfaces"][
        "final_header_vertical_straight_available_mm"
    ] = actual_final_straight
    diagnostics["serviceable_tower"]["modular_interfaces"][
        "straight_remaining_below_spigot_root_mm"
    ] = (
        serviceable.LOWER_SOCKET_MOUTH_Z
        - serviceable.LOWER_SPIGOT_ROOT_OVERLAP
        - (header.H.target_tower_z_mm - actual_final_straight)
    )
    diagnostics["moderate_volume_limits"][1] = (
        "The absorber service dogleg uses two "
        f"{OFFSET_ANGLE_DEG:.1f}-degree R{OFFSET_RADIUS_MM:.1f} elbows. "
        f"Their minimum centerline radius is {OFFSET_RADIUS_MM / base.D.port_width:.2f}D, "
        "but their combined direction change is substantially lower than the "
        "previous pair of 67-degree elbows."
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
