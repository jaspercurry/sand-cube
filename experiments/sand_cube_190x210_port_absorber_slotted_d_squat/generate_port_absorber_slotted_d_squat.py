"""Generate the shortest practical D-shaped slotted port-absorber study.

The circular 40 mm airway is offset toward a flat wall-facing side.  The sealed
common cavity expands away from that wall in a D-shaped plan, allowing the body
to be much shorter while retaining the compact cylindrical variant's chamber
volume.  The core and removable bucket still print vertically without support.

All CAD dimensions are millimetres; acoustic calculations use SI units.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Pos,
    Rot,
    Unit,
    export_step,
    import_step,
)

from experiments.sand_cube_190x210_port_absorber_slotted_bucket import (
    generate_port_absorber_slotted_bucket as acoustic,
)


OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_slotted_d_squat"


@dataclass(frozen=True)
class Design(acoustic.Design):
    name: str = "sand_cube_190x210_port_absorber_slotted_d_squat_v1"

    # The useful acoustic and tooling geometry is retained from the compact
    # cylindrical study.
    overall_length: float = 30.0
    core_wall_t: float = 3.0
    neck_physical_length: float = 5.0
    rail_count: int = 4
    rail_angle_offset_deg: float = 30.0
    pilot_slot_width: float = 0.30
    pilot_slot_length: float = 4.0
    nominal_finished_slot_width: float = 0.40
    witness_slot_widths: tuple[float, ...] = (0.40, 0.50, 0.60)
    coupon_slot_widths: tuple[float, ...] = (0.30, 0.40, 0.50, 0.60)
    target_absorber_frequency_hz: float = 334.7

    # The target is the actual CAD volume of the 65 x 80 mm compact cylinder.
    # The arc radius is solved at build time so the D-shaped body retains it.
    target_cavity_volume_cm3: float = 53.32981472028645

    # D plan: a circle offset in +X and clipped by a flat wall-facing chord.
    # The flat face and the 50 mm-OD tube/socket envelope are nearly tangent.
    d_arc_center_x: float = 8.0
    d_outer_arc_radius: float = 40.0
    d_outer_flat_x: float = -28.5
    bucket_wall_t: float = 3.0
    bottom_floor_t: float = 3.0
    bucket_top_t: float = 3.0
    core_top_clearance_radial: float = 0.20
    upper_skirt_height: float = 0.0
    slot_boss_top_clearance: float = 6.0
    bucket_seat_depth: float = 0.50
    bucket_seat_vertical_clearance: float = 0.10
    bucket_seat_inward_clearance: float = 0.20

    # Separate round adapters remain inside the same wall-facing tangent plane.
    adapter_plate_t: float = 3.0
    adapter_socket_depth: float = 10.0
    adapter_socket_wall_t: float = 3.0
    adapter_socket_clearance_diametral: float = 0.40
    adapter_plate_r: float = 28.5
    adapter_tube_wall_variants: tuple[float, ...] = (3.0, 5.0)

    @property
    def d_inner_arc_radius(self) -> float:
        return self.d_outer_arc_radius - self.bucket_wall_t

    @property
    def d_inner_flat_x(self) -> float:
        return self.d_outer_flat_x + self.bucket_wall_t

    @property
    def cavity_z_min(self) -> float:
        return self.bottom_floor_t

    @property
    def cavity_z_max(self) -> float:
        return self.overall_length - self.bucket_top_t

    @property
    def top_hole_r(self) -> float:
        return self.core_outer_r + self.core_top_clearance_radial

    @property
    def slot_boss_z_min(self) -> float:
        return self.bottom_floor_t

    @property
    def slot_boss_z_max(self) -> float:
        return self.cavity_z_max - self.slot_boss_top_clearance


D = Design()


def _d_prism(
    *, radius: float, flat_x: float, height: float, z: float, design: Design
) -> Any:
    """Extrude an offset circle clipped by its wall-facing flat chord."""
    if radius <= 0.0 or height <= 0.0:
        raise ValueError("D-prism radius and height must be positive")
    circle = Pos(design.d_arc_center_x, 0, z) * Cylinder(
        radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = Pos(flat_x, 0, z) * Box(
        4.0 * radius,
        4.0 * radius,
        height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    result = (circle & clip).clean().fix()
    if not result.is_valid:
        raise ValueError("D-prism construction is invalid")
    return result


def _outer_prism(*, height: float, z: float, design: Design) -> Any:
    return _d_prism(
        radius=design.d_outer_arc_radius,
        flat_x=design.d_outer_flat_x,
        height=height,
        z=z,
        design=design,
    )


def _inner_prism(*, height: float, z: float, design: Design) -> Any:
    return _d_prism(
        radius=design.d_inner_arc_radius,
        flat_x=design.d_inner_flat_x,
        height=height,
        z=z,
        design=design,
    )


def _slot_bosses(design: Design) -> Any:
    boss_height = design.slot_boss_z_max - design.slot_boss_z_min
    boss_radial_depth = (
        design.rail_outer_r
        - design.core_outer_r
        + design.rail_core_overlap
    )
    bosses: Any | None = None
    for index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * index / design.rail_count
        )
        boss = Box(
            boss_radial_depth,
            design.rail_tangential_width,
            boss_height,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        boss = (
            Rot(0, 0, angle)
            * Pos(
                design.core_outer_r - design.rail_core_overlap,
                0,
                design.slot_boss_z_min,
            )
            * boss
        )
        bosses = boss if bosses is None else (bosses + boss).clean().fix()
    if bosses is None:
        raise ValueError("At least one local slot boss is required")
    return bosses


def _core_blank(design: Design) -> Any:
    floor = (
        _outer_prism(height=design.bottom_floor_t, z=0.0, design=design)
        - Cylinder(
            design.bore_r,
            design.bottom_floor_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    ).clean().fix()
    seat_z = design.bottom_floor_t - design.bucket_seat_depth
    seat_outer = _outer_prism(
        height=design.bucket_seat_depth,
        z=seat_z,
        design=design,
    )
    seat_inner = _d_prism(
        radius=(
            design.d_inner_arc_radius
            - design.bucket_seat_inward_clearance
        ),
        flat_x=(
            design.d_inner_flat_x
            + design.bucket_seat_inward_clearance
        ),
        height=design.bucket_seat_depth,
        z=seat_z,
        design=design,
    )
    seat_rebate = (seat_outer - seat_inner).clean().fix()
    floor = (floor - seat_rebate).clean().fix()
    core = (
        Cylinder(
            design.core_outer_r,
            design.overall_length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            design.bore_r,
            design.overall_length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    ).clean().fix()
    return (floor + core + _slot_bosses(design)).clean().fix()


def _bucket(design: Design) -> Any:
    shell_z = (
        design.bottom_floor_t
        - design.bucket_seat_depth
        + design.bucket_seat_vertical_clearance
    )
    shell_height = design.overall_length - shell_z
    shell = (
        _outer_prism(
            height=shell_height,
            z=shell_z,
            design=design,
        )
        - _inner_prism(
            height=shell_height,
            z=shell_z,
            design=design,
        )
    ).clean().fix()
    top = (
        _outer_prism(
            height=design.bucket_top_t,
            z=design.cavity_z_max,
            design=design,
        )
        - Pos(0, 0, design.cavity_z_max)
        * Cylinder(
            design.top_hole_r,
            design.bucket_top_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    ).clean().fix()
    bucket = (shell + top).clean().fix()
    if not bucket.is_valid:
        raise ValueError("D-shaped bucket is invalid")
    return bucket


def _cavity_bulk(design: Design) -> Any:
    height = design.cavity_z_max - design.cavity_z_min
    cavity = _inner_prism(
        height=height,
        z=design.cavity_z_min,
        design=design,
    )
    core_exclusion = Cylinder(
        design.core_outer_r,
        design.overall_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    core_exclusion = (
        core_exclusion + _slot_bosses(design)
    ).clean().fix()
    cavity = (cavity - core_exclusion).clean().fix()
    return cavity


def _cavity_volume_cm3(design: Design) -> float:
    return sum(solid.volume for solid in _cavity_bulk(design).solids()) / 1000.0


def _solve_arc_radius(design: Design) -> Design:
    low = design.d_arc_center_x + design.core_outer_r + design.bucket_wall_t
    high = 55.0
    low_design = replace(design, d_outer_arc_radius=low)
    high_design = replace(design, d_outer_arc_radius=high)
    if _cavity_volume_cm3(low_design) > design.target_cavity_volume_cm3:
        raise ValueError("Minimum D arc already exceeds the cavity target")
    if _cavity_volume_cm3(high_design) < design.target_cavity_volume_cm3:
        raise ValueError("D arc solver upper bound is too small")
    for _ in range(40):
        middle = (low + high) / 2.0
        trial = replace(design, d_outer_arc_radius=middle)
        if _cavity_volume_cm3(trial) < design.target_cavity_volume_cm3:
            low = middle
        else:
            high = middle
    return replace(design, d_outer_arc_radius=(low + high) / 2.0)


def _ray_cavity_backing_mm(angle_deg: float, design: Design) -> float:
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    circle_limit = design.d_arc_center_x * cosine + math.sqrt(
        design.d_inner_arc_radius**2
        - design.d_arc_center_x**2 * sine**2
    )
    limits = [circle_limit]
    if cosine < 0.0:
        limits.append(design.d_inner_flat_x / cosine)
    return min(limits) - design.rail_outer_r


def _tube_socket_adapter(tube_wall_t: float, design: Design) -> Any:
    tube_outer_d = design.main_bore_d + 2.0 * tube_wall_t
    socket_inner_r = (
        tube_outer_d + design.adapter_socket_clearance_diametral
    ) / 2.0
    socket_outer_r = socket_inner_r + design.adapter_socket_wall_t
    if socket_outer_r > design.adapter_plate_r:
        raise ValueError("Socket exceeds the wall-facing adapter plate")
    plate = (
        Cylinder(
            design.adapter_plate_r,
            design.adapter_plate_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            design.bore_r,
            design.adapter_plate_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    ).clean().fix()
    socket = Pos(0, 0, design.adapter_plate_t) * (
        Cylinder(
            socket_outer_r,
            design.adapter_socket_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            socket_inner_r,
            design.adapter_socket_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    return (plate + socket).clean().fix()


def _validate_design(design: Design) -> None:
    if design.neck_physical_length <= design.core_wall_t:
        raise ValueError("Local slot bosses must project beyond the base core")
    if design.overall_length <= (
        design.bottom_floor_t
        + design.bucket_top_t
        + design.slot_boss_top_clearance
        + design.pilot_slot_length
    ):
        raise ValueError("Body is too short for closures, boss land, and pilot slot")
    if design.upper_skirt_height != 0.0:
        raise ValueError("The corrected D variant must not use an internal skirt")
    if not 0.0 < design.bucket_seat_depth < design.bottom_floor_t:
        raise ValueError("D-shaped bucket seat depth is invalid")
    if not 0.0 < design.bucket_seat_vertical_clearance < design.bucket_seat_depth:
        raise ValueError("Bucket seat needs small positive vertical clearance")
    if design.d_inner_flat_x > -design.core_outer_r:
        raise ValueError("Flat inner wall intersects the 50 mm core")
    if (
        design.d_arc_center_x + design.rail_outer_r
        >= design.d_inner_arc_radius
    ):
        raise ValueError("Curved inner wall does not enclose the core")
    if design.adapter_plate_r > -design.d_outer_flat_x + 0.001:
        raise ValueError("Adapter protrudes through the speaker-wall plane")
    for index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * index / design.rail_count
        )
        if _ray_cavity_backing_mm(angle, design) < 1.0:
            raise ValueError(f"Slot at {angle:g} degrees lacks cavity backing")


def _build_geometry(design: Design) -> dict[str, Any]:
    blank = _core_blank(design)
    bucket = _bucket(design)
    cavity = _cavity_bulk(design)
    cavity_solids = list(cavity.solids())
    if len(cavity_solids) != 1:
        raise ValueError(f"Expected one common D cavity, got {len(cavity_solids)}")
    volume_cm3 = cavity_solids[0].volume / 1000.0

    target_lengths = {
        width: acoustic._solve_slot_length_mm(
            width_mm=width,
            volume_cm3=volume_cm3,
            target_hz=design.target_absorber_frequency_hz,
            design=design,
        )
        for width in design.witness_slot_widths
    }
    nominal_length = target_lengths[design.nominal_finished_slot_width]
    available_low = design.cavity_z_min
    available_high = design.slot_boss_z_max
    slot_low = design.overall_length / 2.0 - nominal_length / 2.0
    slot_high = design.overall_length / 2.0 + nominal_length / 2.0
    if slot_low - available_low < 2.0 or available_high - slot_high < 2.0:
        raise ValueError("Nominal slot lacks a 2 mm axial land to seals/skirt")

    pilot_tools = acoustic._slot_tools(
        width=design.pilot_slot_width,
        overall_length=design.pilot_slot_length,
        design=design,
    )
    nominal_tools = acoustic._slot_tools(
        width=design.nominal_finished_slot_width,
        overall_length=nominal_length,
        design=design,
    )
    witness_tools = acoustic._witness_tools(
        target_lengths=target_lengths,
        design=design,
    )
    marked_blank = acoustic._subtract_tools(blank, witness_tools)
    core_pilot = acoustic._subtract_tools(marked_blank, pilot_tools)
    core_nominal = acoustic._subtract_tools(marked_blank, nominal_tools)
    if not core_pilot.is_valid or not core_nominal.is_valid:
        raise ValueError("D core pilot or nominal core is invalid")

    airway = Cylinder(
        design.bore_r,
        design.overall_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pilot_air_domain = (airway + cavity).clean().fix()
    nominal_air_domain = (airway + cavity).clean().fix()
    for tool in pilot_tools:
        pilot_air_domain = (pilot_air_domain + tool).clean().fix()
    for tool in nominal_tools:
        nominal_air_domain = (nominal_air_domain + tool).clean().fix()

    adapters: dict[str, Any] = {}
    connected: dict[str, Any] = {}
    installed: dict[str, tuple[Any, Any]] = {}
    for tube_wall_t in design.adapter_tube_wall_variants:
        key = f"{tube_wall_t:g}mm_wall"
        adapter = _tube_socket_adapter(tube_wall_t, design)
        bottom = Rot(180, 0, 0) * adapter
        top = Pos(0, 0, design.overall_length) * adapter
        adapters[key] = adapter
        installed[key] = (bottom, top)
        connected[key] = Compound(
            children=[core_nominal, bucket, bottom, top]
        )

    default_key = "3mm_wall"
    bottom_adapter, top_adapter = installed[default_key]
    connected_parts = [core_nominal, bucket, bottom_adapter, top_adapter]
    connected_fused = Compound(children=connected_parts)
    total_z_min = -(design.adapter_plate_t + design.adapter_socket_depth)
    total_height = (
        design.overall_length
        + 2.0 * (design.adapter_plate_t + design.adapter_socket_depth)
    )
    keep = Pos(0, 0, total_z_min) * Box(
        2.5 * design.d_outer_arc_radius,
        1.25 * design.d_outer_arc_radius,
        total_height,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    cutaway_solids: list[Any] = []
    for part in connected_parts:
        cutaway_solids.extend(list((part & keep).solids()))
    cutaway = Compound(children=cutaway_solids)

    exploded = Compound(
        children=[
            Pos(-60, 0, 0) * core_pilot,
            Pos(60, 0, 0) * bucket,
            Pos(-60, 0, -22) * adapters[default_key],
            Pos(60, 0, 43) * adapters[default_key],
        ]
    )
    coupon = acoustic._calibration_coupon(design)
    inverted_bucket = Rot(180, 0, 0) * bucket
    bucket_min_z = inverted_bucket.bounding_box().min.Z
    print_layout = Compound(
        children=[
            Pos(-105, 0, 0) * core_pilot,
            Pos(-10, 0, -bucket_min_z) * inverted_bucket,
            Pos(80, -38, 0) * adapters[default_key],
            Pos(80, 38, 0) * adapters[default_key],
            Pos(145, 0, 0) * coupon,
        ]
    )

    extended_airway = Pos(0, 0, total_z_min) * Cylinder(
        design.bore_r,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return {
        "blank": blank,
        "core_pilot": core_pilot,
        "core_nominal": core_nominal,
        "bucket": bucket,
        "cavity_bulk": cavity,
        "cavity_volume_cm3": volume_cm3,
        "airway": airway,
        "extended_airway": extended_airway,
        "pilot_tools": pilot_tools,
        "nominal_tools": nominal_tools,
        "pilot_air_domain": pilot_air_domain,
        "nominal_air_domain": nominal_air_domain,
        "nominal_slot_length_mm": nominal_length,
        "target_lengths_by_width_mm": target_lengths,
        "adapters": adapters,
        "connected": connected,
        "default_adapter_key": default_key,
        "assembly_pilot": Compound(children=[core_pilot, bucket]),
        "assembly_nominal": Compound(children=[core_nominal, bucket]),
        "connected_fused": connected_fused,
        "cutaway": cutaway,
        "exploded": exploded,
        "coupon": coupon,
        "print_layout": print_layout,
    }


def _intersection_volume(first: Any, second: Any) -> float:
    intersection = first & second
    if intersection is None:
        return 0.0
    return sum(solid.volume for solid in intersection.solids())


def _diagnostics(
    geometry: dict[str, Any], design: Design,
    nominal_properties: dict[str, float],
    pilot_properties: dict[str, float],
    ideal_model: dict[str, Any],
    geometric_model: dict[str, Any],
    roundtrip: dict[str, Any],
) -> dict[str, Any]:
    material = Compound(
        children=[geometry["core_nominal"], geometry["bucket"]]
    )
    core_bucket_intersection = _intersection_volume(
        geometry["core_nominal"], geometry["bucket"]
    )
    material_in_bore = _intersection_volume(material, geometry["airway"])
    connected_in_bore = _intersection_volume(
        geometry["connected"][geometry["default_adapter_key"]],
        geometry["extended_airway"],
    )
    if material_in_bore > 0.001 or connected_in_bore > 0.001:
        raise ValueError("D absorber material intrudes into the 40 mm airway")
    if core_bucket_intersection > 0.001:
        raise ValueError("Core and removable D bucket have material interference")
    if len(geometry["pilot_air_domain"].solids()) != 1:
        raise ValueError("Pilot slots do not connect the D cavity to the bore")
    if len(geometry["nominal_air_domain"].solids()) != 1:
        raise ValueError("Finished slots do not connect the D cavity to the bore")

    slot_connections: list[dict[str, float]] = []
    slot_backing: list[dict[str, float]] = []
    for index, tool in enumerate(geometry["nominal_tools"]):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * index / design.rail_count
        )
        bore_overlap = _intersection_volume(tool, geometry["airway"])
        cavity_overlap = _intersection_volume(tool, geometry["cavity_bulk"])
        if bore_overlap <= 0.0 or cavity_overlap <= 0.0:
            raise ValueError(f"Finished D slot {index + 1} misses its air space")
        slot_connections.append(
            {
                "slot": index + 1,
                "angle_deg": angle,
                "bore_overlap_mm3": bore_overlap,
                "cavity_overlap_mm3": cavity_overlap,
            }
        )
        slot_backing.append(
            {
                "angle_deg": angle,
                "radial_cavity_backing_mm": _ray_cavity_backing_mm(
                    angle, design
                ),
            }
        )

    bbox = geometry["connected_fused"].bounding_box()
    body_bbox = Compound(
        children=[geometry["core_nominal"], geometry["bucket"]]
    ).bounding_box()
    return {
        "name": design.name,
        "status": "separate shortest-practical D-shaped packaging study",
        "design_inputs": asdict(design),
        "packaging": {
            "body_x_mm": body_bbox.size.X,
            "body_y_mm": body_bbox.size.Y,
            "body_z_mm": body_bbox.size.Z,
            "connected_x_mm": bbox.size.X,
            "connected_y_mm": bbox.size.Y,
            "connected_z_mm": bbox.size.Z,
            "bore_center_from_flat_speaker_wall_mm": -design.d_outer_flat_x,
            "bore_edge_from_flat_speaker_wall_mm": (
                -design.d_outer_flat_x - design.bore_r
            ),
            "50mm_tube_from_flat_speaker_wall_mm": (
                -design.d_outer_flat_x - 25.0
            ),
            "base_core_to_inner_flat_cavity_mm": (
                -design.d_inner_flat_x - design.core_outer_r
            ),
            "flat_face_x_mm": design.d_outer_flat_x,
            "solved_outer_arc_radius_mm": design.d_outer_arc_radius,
        },
        "acoustic_target": {
            "target_frequency_hz": design.target_absorber_frequency_hz,
            "target_cavity_volume_cm3": design.target_cavity_volume_cm3,
            "cad_cavity_volume_cm3": geometry["cavity_volume_cm3"],
            "provisional_pressure_antinode_mm_from_inlet": (
                design.coupling_path_mm
            ),
        },
        "print_ready_pilot": pilot_properties,
        "nominal_finished_slot": nominal_properties,
        "witness_target_lengths_by_finished_width_mm": {
            str(width): length
            for width, length in geometry[
                "target_lengths_by_width_mm"
            ].items()
        },
        "geometry_validation": {
            "continuous_40mm_bore": True,
            "body_material_intrusion_mm3": material_in_bore,
            "connected_assembly_intrusion_mm3": connected_in_bore,
            "core_bucket_material_intersection_mm3": core_bucket_intersection,
            "common_cavity_solid_count": len(
                geometry["cavity_bulk"].solids()
            ),
            "slot_connections": slot_connections,
            "slot_cavity_backing": slot_backing,
            "flat_side_has_no_slot": all(
                abs((row["angle_deg"] % 360.0) - 180.0) > 1e-6
                for row in slot_backing
            ),
        },
        "printability": {
            "supports_required": False,
            "core": (
                "D floor on build plate, 3 mm tube wall and four 5 mm local "
                "slot bosses grown upward from the floor"
            ),
            "bucket": "invert with D top cap on build plate",
            "adapters": "round plates on build plate, sockets upward",
            "flat_wall_face": "vertical throughout; no overhang",
            "assembly_seal": (
                "removable gasket in lower D locating rebate plus external "
                "face gasket beneath the top socket-adapter plate; no internal skirt"
            ),
            "internal_alignment_skirt": False,
            "lower_d_seat_depth_mm": design.bucket_seat_depth,
            "lower_d_seat_inward_clearance_mm": (
                design.bucket_seat_inward_clearance
            ),
        },
        "acoustic_models": {
            "ideal_q1": ideal_model,
            "smooth_wall_boundary_q": geometric_model,
            "qualification": (
                "Comparative linear TMM only; attenuation and Q require the "
                "same-level microphone test used for the cylindrical variants."
            ),
        },
        "step_roundtrip": roundtrip,
    }


def _step_roundtrip(exports: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        source_solids = list(shape.solids())
        imported_solids = list(imported.solids())
        row = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(source_solids) == len(imported_solids),
            "all_imported_solids_valid": all(
                solid.is_valid for solid in imported_solids
            ),
        }
        results[filename] = row
        if not row["solid_count_matches"] or not row["all_imported_solids_valid"]:
            raise ValueError(f"STEP round-trip failed for {filename}")
    return results


def main() -> None:
    design = _solve_arc_radius(D)
    _validate_design(design)
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_geometry(design)
    volume_cm3 = geometry["cavity_volume_cm3"]
    nominal_properties = acoustic._slot_properties(
        width_mm=design.nominal_finished_slot_width,
        overall_length_mm=geometry["nominal_slot_length_mm"],
        volume_cm3=volume_cm3,
        design=design,
    )
    pilot_properties = acoustic._slot_properties(
        width_mm=design.pilot_slot_width,
        overall_length_mm=design.pilot_slot_length,
        volume_cm3=volume_cm3,
        design=design,
    )

    ideal_tmm_design, tmm_geometry = acoustic._equivalent_tmm_inputs(
        properties=nominal_properties,
        volume_cm3=volume_cm3,
        assumed_q=1.0,
        design=design,
    )
    ideal_model, ideal_rows = acoustic.acoustic_base._run_acoustic_model(
        tmm_geometry, ideal_tmm_design
    )
    geometric_q = nominal_properties[
        "q_from_smooth_wall_boundary_estimate_before_edge_losses"
    ]
    geometric_tmm_design = replace(
        ideal_tmm_design,
        absorber_q=geometric_q,
    )
    geometric_model, geometric_rows = acoustic.acoustic_base._run_acoustic_model(
        tmm_geometry, geometric_tmm_design
    )

    nominal_token = f"{design.nominal_finished_slot_width:.2f}".replace(".", "p")
    exports = {
        "port_absorber_d_squat_inner_core_pilot.step": geometry["core_pilot"],
        f"port_absorber_d_squat_inner_core_{nominal_token}_finished_reference.step": (
            geometry["core_nominal"]
        ),
        "port_absorber_d_squat_outer_bucket.step": geometry["bucket"],
        "port_absorber_d_squat_socket_adapter_40id_46od.step": geometry[
            "adapters"
        ]["3mm_wall"],
        "port_absorber_d_squat_socket_adapter_40id_50od.step": geometry[
            "adapters"
        ]["5mm_wall"],
        "port_absorber_d_squat_assembly_finished_reference.step": geometry[
            "assembly_nominal"
        ],
        "port_absorber_d_squat_connected_46od_tubes.step": geometry[
            "connected"
        ]["3mm_wall"],
        "port_absorber_d_squat_connected_50od_tubes.step": geometry[
            "connected"
        ]["5mm_wall"],
        "port_absorber_d_squat_cutaway.step": geometry["cutaway"],
        "port_absorber_d_squat_exploded.step": geometry["exploded"],
        "port_absorber_d_squat_print_layout.step": geometry["print_layout"],
        "port_absorber_d_squat_air_domain_finished.step": geometry[
            "nominal_air_domain"
        ],
        "port_absorber_d_squat_calibration_coupon.step": geometry["coupon"],
    }
    roundtrip = _step_roundtrip(exports)

    for filename, rows in (
        ("modeled_response_q1.csv", ideal_rows),
        ("modeled_response_smooth_wall_q.csv", geometric_rows),
    ):
        with (OUT / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    diagnostics = _diagnostics(
        geometry,
        design,
        nominal_properties,
        pilot_properties,
        ideal_model,
        geometric_model,
        roundtrip,
    )
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=False) + "\n"
    )

    for source, viewer_name in (
        ("port_absorber_d_squat_connected_46od_tubes.step", "viewer"),
        ("port_absorber_d_squat_cutaway.step", "cutaway_viewer"),
        ("port_absorber_d_squat_exploded.step", "exploded_viewer"),
        ("port_absorber_d_squat_print_layout.step", "print_layout_viewer"),
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

    print(f"D-squat body: {OUT / 'port_absorber_d_squat_assembly_finished_reference.step'}")
    print(f"Cutaway: {OUT / 'port_absorber_d_squat_cutaway.step'}")
    print(f"Diagnostics: {OUT / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
