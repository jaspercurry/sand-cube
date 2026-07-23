"""Place the squat absorber flat against the enclosure rear acoustic face.

This isolated derivative keeps the separately printable absorber, the 40 mm
airway, and the complete serviceable exterior tower from the preceding
internal-absorber study.  Only the in-box route is re-planned:

* the absorber service straight is parallel to the rear wall, so the complete
  D-flat follows the rear inner face with only 0.02 mm nominal assembly relief;
* a shallow three-dimensional elbow after the absorber starts moving the tube
  rearward;
* a final rotated elbow returns to the unchanged tower center and vertical
  tangent.

The future absorber mounting tab/node is intentionally deferred.
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
SOURCE_EXPERIMENT = ROOT / "experiments" / "sand_cube_190x210_internal_squat_absorber"
sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber as prior  # noqa: E402


header = prior.header
base = prior.base
serviceable = prior.serviceable
OUT = ROOT / "build" / "sand_cube_190x210_internal_squat_absorber_flush"
prior.OUT = OUT
serviceable.OUT = OUT
header.OUT = OUT
base.OUT = OUT


# The rear acoustic face is y=108 mm.  The absorber bore center is 28.5 mm
# ahead of its D-flat. A 0.02 mm relief avoids coincident-body ambiguity while
# remaining far below both FDM accuracy and the intended sealant film.
REAR_ACOUSTIC_FACE_Y = 108.0
ABSORBER_CENTER_TO_D_FLAT = 28.5
ABSORBER_REAR_ASSEMBLY_RELIEF = 0.02
TARGET_RISE_X = 64.0
TARGET_RISE_Y = (
    REAR_ACOUSTIC_FACE_Y
    - ABSORBER_CENTER_TO_D_FLAT
    - ABSORBER_REAR_ASSEMBLY_RELIEF
)

# The first upper elbow and the 56 mm absorber straight lie in an XZ plane.
# The 8.38-degree intermediate elbow twists the following return plane toward
# +Y, allowing the final elbow to land at the unchanged y=82 mm tower.
UPPER_RADIUS_MM = 38.0
PRE_ABSORBER_VERTICAL_MM = 0.5
POST_RETURN_VERTICAL_MM = 2.0
FIRST_UPPER_ANGLE_DEG = 44.55541366348005
RETURN_TANGENT_POLAR_DEG = 42.893080121067925
RETURN_TANGENT_YAW_DEG = 12.043281712516583


def _solve_plan_route() -> tuple[float, float]:
    """Solve the existing R75 plan elbow and straight to the new rise."""
    start_x = base.D.inlet_throat_x
    start_y = base.D.inlet_throat_y
    radius = header.H.plan_elbow_radius_mm
    rise_radius = header.H.rise_elbow_radius_mm
    angle = math.radians(76.0)
    straight = 20.5
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


PLAN_ANGLE_DEG, PLAN_STRAIGHT_MM = _solve_plan_route()
header.H = replace(
    header.H,
    plan_elbow_angle_deg=PLAN_ANGLE_DEG,
    inter_elbow_straight_mm=PLAN_STRAIGHT_MM,
    offset_elbow_radius_mm=UPPER_RADIUS_MM,
    offset_elbow_angle_deg=FIRST_UPPER_ANGLE_DEG,
)
base.D = replace(
    base.D,
    name="sand_cube_190x210_internal_d_squat_absorber_flush_rear",
    lower_elbow_vertical_x=TARGET_RISE_X,
    lower_elbow_vertical_y=TARGET_RISE_Y,
)


# The extra G1 junction in the twisted return increases OpenCascade's
# independently integrated cut/intersection disagreement to about 0.17 mm3 on
# a 1.16e6 mm3 shell. Keep the unique volume-verified selection, with a
# 2.5e-7 relative tolerance that is still far below any printable fragment.
_ORIGINAL_CUT_SINGLE_SOLID = base._cut_single_solid


def _cut_single_solid_with_sweep_tolerance(
    base_shape: Any,
    cutter: Any,
    *,
    feature: str,
) -> Any:
    try:
        return _ORIGINAL_CUT_SINGLE_SOLID(
            base_shape,
            cutter,
            feature=feature,
        )
    except ValueError as original_error:
        overlap = base._intersection_volume(base_shape, cutter)
        if overlap <= 0.001:
            raise original_error
        expected_volume = base_shape.volume - overlap
        solids = base._fresh_solids(base_shape.cut(cutter))
        tolerance = max(0.30, abs(expected_volume) * 2.5e-7)
        candidates = [
            solid
            for solid in solids
            if abs(solid.volume - expected_volume) <= tolerance
        ]
        if len(candidates) != 1:
            raise original_error
        return base._require_single_solid(
            candidates[0].clean().fix(),
            feature=feature,
        )


base._cut_single_solid = _cut_single_solid_with_sweep_tolerance


def _angle_between(a: Vector, b: Vector) -> float:
    return math.acos(max(-1.0, min(1.0, a.normalized().dot(b.normalized()))))


def _flush_header_route_geometry() -> tuple[Wire, dict[str, Any]]:
    """Build the wall-parallel absorber run and twisted rearward return."""
    d = base.D
    p0 = Vector(d.inlet_throat_x, d.inlet_throat_y, d.horizontal_z)
    direction = Vector(0.0, 1.0, 0.0)
    vertical = Vector(0.0, 0.0, 1.0)
    edges: list[Edge] = []

    plan_angle = math.radians(PLAN_ANGLE_DEG)
    plan_arc, point, direction = header._arc_from_start_tangent(
        p0,
        direction,
        Vector(0.0, 0.0, -1.0),
        header.H.plan_elbow_radius_mm,
        plan_angle,
    )
    edges.append(plan_arc)

    next_point = point + direction * PLAN_STRAIGHT_MM
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    rise_normal = direction.cross(vertical).normalized()
    rise_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        rise_normal,
        header.H.rise_elbow_radius_mm,
        math.radians(header.H.rise_elbow_angle_deg),
    )
    edges.append(rise_arc)
    rise_exit = Vector(point.X, point.Y, point.Z)
    expected_rise = Vector(TARGET_RISE_X, TARGET_RISE_Y, -15.0)
    if (rise_exit - expected_rise).length > 0.001:
        raise ValueError(
            "Flush-absorber rise missed its target by "
            f"{(rise_exit - expected_rise).length:.6f} mm"
        )

    next_point = point + direction * PRE_ABSORBER_VERTICAL_MM
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    first_angle = math.radians(FIRST_UPPER_ANGLE_DEG)
    first_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        Vector(0.0, -1.0, 0.0),
        UPPER_RADIUS_MM,
        first_angle,
    )
    edges.append(first_arc)

    next_point = point + direction * prior.ABSORBER_CONNECTED_LENGTH
    edges.append(Edge.make_line(point, next_point))
    point = next_point

    polar = math.radians(RETURN_TANGENT_POLAR_DEG)
    yaw = math.radians(RETURN_TANGENT_YAW_DEG)
    return_tangent = Vector(
        -math.cos(yaw) * math.sin(polar),
        math.sin(yaw) * math.sin(polar),
        math.cos(polar),
    ).normalized()

    twist_angle = _angle_between(direction, return_tangent)
    twist_normal = direction.cross(return_tangent).normalized()
    twist_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        twist_normal,
        UPPER_RADIUS_MM,
        twist_angle,
    )
    edges.append(twist_arc)

    return_angle = _angle_between(direction, vertical)
    return_normal = direction.cross(vertical).normalized()
    return_arc, point, direction = header._arc_from_start_tangent(
        point,
        direction,
        return_normal,
        UPPER_RADIUS_MM,
        return_angle,
    )
    edges.append(return_arc)

    endpoint = Vector(
        header.H.target_tower_x_mm,
        header.H.target_tower_y_mm,
        header.H.target_tower_z_mm,
    )
    next_point = point + vertical * POST_RETURN_VERTICAL_MM
    edges.append(Edge.make_line(point, next_point))
    wire = Wire(edges)

    endpoint_error = (next_point - endpoint).length
    if endpoint_error > 0.002:
        raise ValueError(
            f"Flush-absorber header endpoint error is {endpoint_error:.6f} mm"
        )
    tangent_error = (wire.tangent_at(1.0).normalized() - vertical).length
    if tangent_error > 0.001:
        raise ValueError(
            f"Flush-absorber header tangent error is {tangent_error:.6f}"
        )

    twist_angle_deg = math.degrees(twist_angle)
    return_angle_deg = math.degrees(return_angle)
    metadata = {
        "module_order": [
            f"{PLAN_ANGLE_DEG:.3f} degree R75 plan elbow",
            f"{PLAN_STRAIGHT_MM:.3f} mm straight",
            "90 degree R50 rise elbow",
            f"{PRE_ABSORBER_VERTICAL_MM:.3f} mm vertical straight",
            f"{FIRST_UPPER_ANGLE_DEG:.3f} degree R{UPPER_RADIUS_MM:g} elbow",
            f"{prior.ABSORBER_CONNECTED_LENGTH:.3f} mm wall-parallel absorber straight",
            f"{twist_angle_deg:.3f} degree R{UPPER_RADIUS_MM:g} twisted elbow",
            f"{return_angle_deg:.3f} degree R{UPPER_RADIUS_MM:g} return elbow",
            f"{POST_RETURN_VERTICAL_MM:.3f} mm final vertical straight",
        ],
        "elbow_angles_deg": [
            PLAN_ANGLE_DEG,
            header.H.rise_elbow_angle_deg,
            FIRST_UPPER_ANGLE_DEG,
            twist_angle_deg,
            return_angle_deg,
        ],
        "elbow_centerline_radii_mm": [
            header.H.plan_elbow_radius_mm,
            header.H.rise_elbow_radius_mm,
            UPPER_RADIUS_MM,
            UPPER_RADIUS_MM,
            UPPER_RADIUS_MM,
        ],
        "total_direction_change_deg": (
            PLAN_ANGLE_DEG
            + header.H.rise_elbow_angle_deg
            + FIRST_UPPER_ANGLE_DEG
            + twist_angle_deg
            + return_angle_deg
        ),
        "inter_elbow_straight_mm": PLAN_STRAIGHT_MM,
        "offset_diagonal_straight_mm": prior.ABSORBER_CONNECTED_LENGTH,
        "short_vertical_straights_mm": [
            PRE_ABSORBER_VERTICAL_MM,
            POST_RETURN_VERTICAL_MM,
        ],
        "lateral_offset_mm": math.hypot(
            TARGET_RISE_X - header.H.target_tower_x_mm,
            TARGET_RISE_Y - header.H.target_tower_y_mm,
        ),
        "lateral_offset_direction_xy": [
            -TARGET_RISE_X
            / math.hypot(TARGET_RISE_X, TARGET_RISE_Y - header.H.target_tower_y_mm),
            (header.H.target_tower_y_mm - TARGET_RISE_Y)
            / math.hypot(TARGET_RISE_X, TARGET_RISE_Y - header.H.target_tower_y_mm),
        ],
        "rise_elbow_exit_xyz_mm": [rise_exit.X, rise_exit.Y, rise_exit.Z],
        "route_start_xyz_mm": [p0.X, p0.Y, p0.Z],
        "route_end_xyz_mm": [endpoint.X, endpoint.Y, endpoint.Z],
        "physical_length_mm": wire.length,
        "minimum_centerline_radius_to_bore_ratio": (
            min(
                header.H.plan_elbow_radius_mm,
                header.H.rise_elbow_radius_mm,
                UPPER_RADIUS_MM,
            )
            / base.D.port_width
        ),
        "all_sections_constant_circle": True,
        "all_curves_constant_radius": True,
        "bespoke_spline_sections": 0,
        "absorber_axis_parallel_to_rear_wall": True,
        "absorber_axis_y_mm": TARGET_RISE_Y,
        "rearward_return_shift_mm": (
            header.H.target_tower_y_mm - TARGET_RISE_Y
        ),
        "twisted_return_elbow_angle_deg": twist_angle_deg,
        "return_elbow_angle_deg": return_angle_deg,
    }
    return wire, metadata


header._header_route_geometry = _flush_header_route_geometry


def _absorber_straight() -> tuple[Any, Vector, Vector]:
    route = header._header_route_wire()
    edges = route.edges()
    if len(edges) != 9:
        raise ValueError(f"Expected nine header modules, got {len(edges)}")
    straight = edges[5]
    if abs(straight.length - prior.ABSORBER_CONNECTED_LENGTH) > 0.01:
        raise ValueError(
            "Absorber service straight missed its connected length: "
            f"{straight.length:.6f} mm"
        )
    center = straight.position_at(0.5)
    tangent = straight.tangent_at(0.5).normalized()
    if abs(tangent.Y) > 1e-8:
        raise ValueError(
            f"Flush absorber axis has nonzero rear-wall slope {tangent.Y:.9f}"
        )
    return straight, center, tangent


prior._absorber_straight = _absorber_straight


# The source clearance envelope covered the D-body and sockets but not the two
# 3 mm circular adapter shoulders. In the former diagonal placement those
# shoulders missed the rear cradle; the wall-parallel placement exposes the
# omission. Add explicit 1 mm shoulder reliefs while leaving the brace topology
# and the separately printable absorber unchanged.
_ORIGINAL_ABSORBER_INSTALLATION_ENVELOPE = (
    prior._local_absorber_installation_envelope
)


def _local_absorber_installation_envelope_with_shoulders() -> Any:
    clearance = prior.ABSORBER_BRACE_CLEARANCE
    shoulder_radius = prior.ABSORBER_DESIGN.adapter_plate_r + clearance
    body_height = prior.ABSORBER_DESIGN.overall_length
    lower_shoulder = prior.Pos(0.0, 0.0, -3.0 - clearance) * prior.Cylinder(
        shoulder_radius,
        3.0 + 2.0 * clearance,
        align=(prior.Align.CENTER, prior.Align.CENTER, prior.Align.MIN),
    )
    upper_shoulder = prior.Pos(
        0.0,
        0.0,
        body_height - clearance,
    ) * prior.Cylinder(
        shoulder_radius,
        3.0 + 2.0 * clearance,
        align=(prior.Align.CENTER, prior.Align.CENTER, prior.Align.MIN),
    )
    return prior.Compound(
        children=[
            *prior._fresh_solids(_ORIGINAL_ABSORBER_INSTALLATION_ENVELOPE()),
            *prior._fresh_solids(lower_shoulder),
            *prior._fresh_solids(upper_shoulder),
        ]
    )


prior._local_absorber_installation_envelope = (
    _local_absorber_installation_envelope_with_shoulders
)


def generate() -> dict[str, Any]:
    diagnostics = prior.generate()
    route_metadata = header._header_route_metadata()
    placement = diagnostics["internal_squat_absorber"]["placement"]
    rear_clearance = placement["minimum_rear_wall_clearance_mm"]
    if abs(rear_clearance - ABSORBER_REAR_ASSEMBLY_RELIEF) > 0.002:
        raise ValueError(
            "The complete absorber D-flat missed its rear-wall relief: "
            f"clearance={rear_clearance:.6f} mm"
        )

    diagnostics["name"] = base.D.name
    diagnostics["status"] = (
        "serviceable 40 mm tower with the internal squat absorber D-flat "
        "parallel and effectively flush with the rear acoustic face, plus a "
        "twisted rearward return"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/sand_cube_190x210_internal_squat_absorber_flush"
        ),
        "output_dir": "build/sand_cube_190x210_internal_squat_absorber_flush",
        "prior_internal_absorber_variant_modified": False,
        "squat_absorber_source_modified": False,
    }
    diagnostics["alignment"]["type"] = (
        "single 40 mm circular port with an R75 lower plan sweep, R50 rise, "
        "wall-parallel 56 mm absorber straight, shallow twisted return, and "
        "unchanged serviceable exterior tower"
    )
    diagnostics["internal_squat_absorber"]["route_changes"] = {
        "right_rise_center_xy_mm": [TARGET_RISE_X, TARGET_RISE_Y],
        "plan_elbow_angle_deg": PLAN_ANGLE_DEG,
        "plan_straight_mm": PLAN_STRAIGHT_MM,
        "upper_elbow_count": 3,
        "upper_elbow_angles_deg": route_metadata["elbow_angles_deg"][2:],
        "upper_elbow_centerline_radius_mm": UPPER_RADIUS_MM,
        "upper_centerline_radius_to_bore_ratio": (
            UPPER_RADIUS_MM / base.D.port_width
        ),
        "service_straight_mm": prior.ABSORBER_CONNECTED_LENGTH,
        "service_straight_axis_y_mm": TARGET_RISE_Y,
        "rearward_return_shift_mm": route_metadata["rearward_return_shift_mm"],
        "total_upper_direction_change_deg": sum(
            route_metadata["elbow_angles_deg"][2:]
        ),
    }
    diagnostics["internal_squat_absorber"]["manufacturing"].update(
        {
            "entire_d_flat_parallel_to_rear_acoustic_face": True,
            "nominal_rear_assembly_relief_mm": (
                ABSORBER_REAR_ASSEMBLY_RELIEF
            ),
            "future_mounting_tab_included": False,
            "rear_wall_mounting_node_included": False,
        }
    )
    diagnostics["alignment"]["packaging_tuning_tradeoff"].update(
        {
            "rear_wall_flush_absorber": True,
            "twisted_return_preserves_external_tower_xy": True,
            "current_natural_tuning_hz": diagnostics["alignment"][
                "calculated_tuning_hz"
            ],
        }
    )
    diagnostics["moderate_volume_limits"][1] = (
        "The wall-parallel absorber run uses an R38 main elbow, an R38 "
        f"{route_metadata['twisted_return_elbow_angle_deg']:.1f}-degree "
        "three-dimensional steering elbow, and an R38 return elbow. The "
        "shallow steering elbow moves the airway rearward without relocating "
        "the weight-bearing exterior tower."
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
