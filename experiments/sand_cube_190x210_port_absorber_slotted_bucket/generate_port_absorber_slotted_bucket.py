"""Generate the cylindrical, post-finished slotted port-absorber prototype.

This experiment keeps the support-free bucket architecture of the drilled-hole
prototype, but replaces the 24 radial holes with four axial racetrack slots.
The print-ready slots are deliberately narrower and shorter than the acoustic
target.  With the bucket removed, every slot is accessible from the chamber
side for controlled widening and endpoint extension.

All CAD dimensions are millimetres; acoustic calculations use SI units.
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

import argparse
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

from experiments.sand_cube_190x210_port_absorber_bucket import (
    generate_port_absorber_bucket as bucket_base,
)
from experiments.sand_cube_190x210_port_absorber_collar import (
    generate_port_absorber_collar as acoustic_base,
)


OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_slotted_bucket"


@dataclass(frozen=True)
class Design(bucket_base.Design):
    name: str = "sand_cube_190x210_port_absorber_slotted_bucket_v2"

    # Current 40 mm-bore folded port supplied for this design pass.
    main_bore_d: float = 40.0
    host_tube_wall_t: float = 3.0
    main_port_area_mm2: float = math.pi * 20.0**2
    main_port_physical_length_mm: float = 513.6
    reported_lf_effective_length_mm: float = 541.0
    net_box_volume_l: float = 4.524
    bass_reflex_tuning_hz: float = 39.12

    # Distributed model inputs.  The body remains a straight cylindrical
    # calibration module even though the final installation will need a bend.
    inlet_flare_length_mm: float = 18.0
    inlet_mouth_d: float = 44.5
    throat_d: float = 40.0
    outlet_flare_length_mm: float = 25.0
    outlet_mouth_d: float = 58.6
    outlet_radiation_end_factor: float = 0.6133
    coupling_path_mm: float = 258.0

    # Preserve the proven support-free 68 x 120 mm body and removable bucket.
    overall_length: float = 120.0
    maximum_outer_d: float = 68.0
    core_wall_t: float = 5.0
    neck_physical_length: float = 8.0
    rail_count: int = 4
    rail_angle_offset_deg: float = 30.0
    rail_tangential_width: float = 6.0

    # Print below the intended tune.  Width is established first with a gauge,
    # abrasive shim, guided side cutter, or end mill; length is then extended.
    pilot_slot_width: float = 0.50
    pilot_slot_length: float = 11.0
    nominal_finished_slot_width: float = 0.60
    target_absorber_frequency_hz: float = 334.7

    # Flush-opening end correction uses 0.85 times the exact racetrack
    # hydraulic diameter.  This is a design estimate, not a fitted measurement.
    slot_end_correction_hydraulic_factor: float = 0.85
    dynamic_viscosity_pa_s: float = 1.81e-5

    # Blind witness notches on the chamber face identify calculated endpoint
    # positions for 0.6, 0.7, and 0.8 mm finished widths.
    witness_slot_widths: tuple[float, ...] = (0.60, 0.70, 0.80)
    witness_notch_radial_depth: float = 0.35
    witness_notch_tangential_width: float = 2.4
    witness_notch_axial_height: float = 0.20

    # A short exact-section print coupon contains four different slot gaps.
    coupon_height: float = 32.0
    coupon_floor_t: float = 3.0
    coupon_slot_widths: tuple[float, ...] = (0.40, 0.50, 0.60, 0.70)


D = Design()


def _validate_design(design: Design) -> None:
    bucket_base._validate_design(design)
    if design.rail_count != 4:
        raise ValueError("This tuning and coupon layout assumes four slots")
    if design.pilot_slot_width <= 0.0:
        raise ValueError("Pilot slot width must be positive")
    if design.pilot_slot_length <= design.pilot_slot_width:
        raise ValueError("Pilot slot must be longer than it is wide")
    if design.nominal_finished_slot_width < design.pilot_slot_width:
        raise ValueError("Finished slot cannot be narrower than the pilot")
    if design.rail_tangential_width < design.nominal_finished_slot_width + 2.0:
        raise ValueError("Insufficient rail wall around the finished slot")
    if len(design.coupon_slot_widths) != design.rail_count:
        raise ValueError("Coupon needs one test width per rail")
    if design.witness_notch_radial_depth >= design.neck_physical_length / 2.0:
        raise ValueError("Witness notches must remain shallow and blind")


def _racetrack_area_mm2(width_mm: float, overall_length_mm: float) -> float:
    if overall_length_mm <= width_mm:
        raise ValueError("Racetrack overall length must exceed its width")
    return (
        width_mm * (overall_length_mm - width_mm)
        + math.pi * width_mm**2 / 4.0
    )


def _racetrack_perimeter_mm(width_mm: float, overall_length_mm: float) -> float:
    if overall_length_mm <= width_mm:
        raise ValueError("Racetrack overall length must exceed its width")
    return 2.0 * (overall_length_mm - width_mm) + math.pi * width_mm


def _hydraulic_diameter_mm(width_mm: float, overall_length_mm: float) -> float:
    return (
        4.0
        * _racetrack_area_mm2(width_mm, overall_length_mm)
        / _racetrack_perimeter_mm(width_mm, overall_length_mm)
    )


def _effective_slot_length_mm(
    width_mm: float, overall_length_mm: float, design: Design
) -> float:
    return design.neck_physical_length + (
        design.slot_end_correction_hydraulic_factor
        * _hydraulic_diameter_mm(width_mm, overall_length_mm)
    )


def _slot_frequency_hz(
    *, width_mm: float, overall_length_mm: float, volume_cm3: float,
    design: Design,
) -> float:
    total_area_m2 = (
        design.rail_count
        * _racetrack_area_mm2(width_mm, overall_length_mm)
        / 1_000_000.0
    )
    effective_length_m = (
        _effective_slot_length_mm(width_mm, overall_length_mm, design) / 1000.0
    )
    volume_m3 = volume_cm3 / 1_000_000.0
    return design.speed_of_sound_m_s / (2.0 * math.pi) * math.sqrt(
        total_area_m2 / (volume_m3 * effective_length_m)
    )


def _solve_slot_length_mm(
    *, width_mm: float, volume_cm3: float, target_hz: float, design: Design
) -> float:
    low = width_mm * 1.01
    high = 60.0
    if _slot_frequency_hz(
        width_mm=width_mm,
        overall_length_mm=low,
        volume_cm3=volume_cm3,
        design=design,
    ) > target_hz:
        raise ValueError("Slot width alone already exceeds the target frequency")
    if _slot_frequency_hz(
        width_mm=width_mm,
        overall_length_mm=high,
        volume_cm3=volume_cm3,
        design=design,
    ) < target_hz:
        raise ValueError("Slot length solver upper bound is too short")
    for _ in range(90):
        middle = (low + high) / 2.0
        frequency = _slot_frequency_hz(
            width_mm=width_mm,
            overall_length_mm=middle,
            volume_cm3=volume_cm3,
            design=design,
        )
        if frequency < target_hz:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _radial_racetrack_tool(
    *, angle_deg: float, z: float, width: float, overall_length: float,
    design: Design,
) -> Any:
    """A radial extrusion of an axial racetrack opening."""
    if overall_length <= width:
        raise ValueError("Racetrack length must exceed width")
    overlap = 0.15
    radial_start = design.bore_r - overlap
    radial_length = design.neck_physical_length + 2.0 * overlap
    center_distance = overall_length - width
    center_box = Box(
        radial_length,
        width,
        center_distance,
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    )
    center_box = (
        Rot(0, 0, angle_deg)
        * Pos(radial_start, 0, z)
        * center_box
    )
    lower = acoustic_base._radial_cylinder(
        angle_deg=angle_deg,
        radial_start=radial_start,
        length=radial_length,
        radius=width / 2.0,
        z=z - center_distance / 2.0,
    )
    upper = acoustic_base._radial_cylinder(
        angle_deg=angle_deg,
        radial_start=radial_start,
        length=radial_length,
        radius=width / 2.0,
        z=z + center_distance / 2.0,
    )
    return (center_box + lower + upper).clean().fix()


def _slot_tools(
    *, width: float, overall_length: float, design: Design,
    z: float | None = None,
) -> list[Any]:
    slot_center_z = design.overall_length / 2.0 if z is None else z
    return [
        _radial_racetrack_tool(
            angle_deg=(
                design.rail_angle_offset_deg
                + 360.0 * index / design.rail_count
            ),
            z=slot_center_z,
            width=width,
            overall_length=overall_length,
            design=design,
        )
        for index in range(design.rail_count)
    ]


def _witness_tools(
    *, target_lengths: dict[float, float], design: Design
) -> list[Any]:
    tools: list[Any] = []
    center_z = design.overall_length / 2.0
    for rail_index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * rail_index / design.rail_count
        )
        for slot_width in design.witness_slot_widths:
            target_length = target_lengths[slot_width]
            for direction in (-1.0, 1.0):
                notch = Box(
                    design.witness_notch_radial_depth + 0.05,
                    design.witness_notch_tangential_width,
                    design.witness_notch_axial_height,
                    align=(Align.MIN, Align.CENTER, Align.CENTER),
                )
                notch = (
                    Rot(0, 0, angle)
                    * Pos(
                        design.rail_outer_r
                        - design.witness_notch_radial_depth,
                        0,
                        center_z + direction * target_length / 2.0,
                    )
                    * notch
                )
                tools.append(notch)
    return tools


def _subtract_tools(blank: Any, tools: list[Any]) -> Any:
    result = blank
    for tool in tools:
        result = (result - tool).clean().fix()
    return result


def _slot_properties(
    *, width_mm: float, overall_length_mm: float, volume_cm3: float,
    design: Design,
) -> dict[str, float]:
    area_each_mm2 = _racetrack_area_mm2(width_mm, overall_length_mm)
    perimeter_each_mm = _racetrack_perimeter_mm(width_mm, overall_length_mm)
    total_area_m2 = design.rail_count * area_each_mm2 / 1_000_000.0
    area_each_m2 = area_each_mm2 / 1_000_000.0
    perimeter_each_m = perimeter_each_mm / 1000.0
    effective_length_m = (
        _effective_slot_length_mm(width_mm, overall_length_mm, design) / 1000.0
    )
    omega = 2.0 * math.pi * _slot_frequency_hz(
        width_mm=width_mm,
        overall_length_mm=overall_length_mm,
        volume_cm3=volume_cm3,
        design=design,
    )
    acoustic_mass = design.air_density_kg_m3 * effective_length_m / total_area_m2
    boundary_resistance = (
        (design.neck_physical_length / 1000.0)
        * perimeter_each_m
        / (design.rail_count * area_each_m2**2)
        * math.sqrt(
            omega
            * design.air_density_kg_m3
            * design.dynamic_viscosity_pa_s
            / 2.0
        )
    )
    boundary_layer_m = math.sqrt(
        2.0
        * design.dynamic_viscosity_pa_s
        / (design.air_density_kg_m3 * omega)
    )
    return {
        "width_mm": width_mm,
        "overall_length_mm": overall_length_mm,
        "straight_center_length_mm": overall_length_mm - width_mm,
        "area_each_mm2": area_each_mm2,
        "total_area_mm2": total_area_m2 * 1_000_000.0,
        "perimeter_each_mm": perimeter_each_mm,
        "hydraulic_diameter_mm": _hydraulic_diameter_mm(
            width_mm, overall_length_mm
        ),
        "physical_passage_length_mm": design.neck_physical_length,
        "effective_passage_length_mm": effective_length_m * 1000.0,
        "calculated_frequency_hz": omega / (2.0 * math.pi),
        "viscous_boundary_layer_mm": boundary_layer_m * 1000.0,
        "acoustic_mass_pa_s2_per_m3": acoustic_mass,
        "high_frequency_boundary_resistance_estimate_pa_s_per_m3": (
            boundary_resistance
        ),
        "q_from_smooth_wall_boundary_estimate_before_edge_losses": (
            omega * acoustic_mass / boundary_resistance
        ),
    }


def _calibration_coupon(design: Design) -> Any:
    height = design.coupon_height
    floor = bucket_base._shell(
        design.outer_r,
        design.bore_r,
        design.coupon_floor_t,
    )
    core = bucket_base._shell(
        design.core_outer_r,
        design.bore_r,
        height,
    )
    coupon = (floor + core).clean().fix()
    rail_height = height - 2.0 * design.coupon_floor_t
    for index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * index / design.rail_count
        )
        rail = Box(
            design.rail_radial_depth,
            design.rail_tangential_width,
            rail_height,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        rail = (
            Rot(0, 0, angle)
            * Pos(
                design.core_outer_r - design.rail_core_overlap,
                0,
                design.coupon_floor_t,
            )
            * rail
        )
        coupon = (coupon + rail).clean().fix()
        test_tool = _radial_racetrack_tool(
            angle_deg=angle,
            z=height / 2.0,
            width=design.coupon_slot_widths[index],
            overall_length=design.pilot_slot_length,
            design=design,
        )
        coupon = (coupon - test_tool).clean().fix()
    return coupon


def _equivalent_tmm_inputs(
    *, properties: dict[str, float], volume_cm3: float, assumed_q: float,
    design: Design,
) -> tuple[acoustic_base.Design, dict[str, Any]]:
    equivalent_diameter = math.sqrt(
        4.0 * properties["total_area_mm2"] / math.pi
    )
    equivalent_physical_length = (
        properties["effective_passage_length_mm"]
        - 0.85 * equivalent_diameter
    )
    if equivalent_physical_length <= 0.0:
        raise ValueError("Equivalent TMM physical length became non-positive")
    tmm_design = replace(
        acoustic_base.D,
        name=design.name,
        main_bore_d=design.main_bore_d,
        existing_tube_wall_t=design.host_tube_wall_t,
        main_port_area_mm2=design.main_port_area_mm2,
        main_port_physical_length_mm=design.main_port_physical_length_mm,
        reported_lf_effective_length_mm=design.reported_lf_effective_length_mm,
        net_box_volume_l=design.net_box_volume_l,
        bass_reflex_tuning_hz=design.bass_reflex_tuning_hz,
        inlet_flare_length_mm=design.inlet_flare_length_mm,
        inlet_mouth_d=design.inlet_mouth_d,
        throat_d=design.throat_d,
        outlet_flare_length_mm=design.outlet_flare_length_mm,
        outlet_mouth_d=design.outlet_mouth_d,
        outlet_radiation_end_factor=design.outlet_radiation_end_factor,
        collar_center_path_mm=design.coupling_path_mm,
        chamber_count=1,
        target_absorber_frequency_hz=design.target_absorber_frequency_hz,
        target_frequency_multipliers=(1.0,),
        neck_physical_length=equivalent_physical_length,
        absorber_q=assumed_q,
        speed_of_sound_m_s=design.speed_of_sound_m_s,
        air_density_kg_m3=design.air_density_kg_m3,
    )
    geometry = {
        "neck_diameters_mm": [equivalent_diameter],
        "acoustic_volumes_cm3": [volume_cm3],
    }
    return tmm_design, geometry


def _build_geometry(design: Design) -> dict[str, Any]:
    blank = bucket_base._core_blank(design)
    bucket = bucket_base._bucket(design)
    cavity_bulk = (
        bucket_base._potential_chamber_envelope(design) - blank - bucket
    ).clean().fix()
    cavity_solids = list(cavity_bulk.solids())
    if len(cavity_solids) != 1:
        raise ValueError(
            f"Expected one common annular cavity, got {len(cavity_solids)}"
        )
    cavity_volume_cm3 = cavity_solids[0].volume / 1000.0

    target_lengths = {
        width: _solve_slot_length_mm(
            width_mm=width,
            volume_cm3=cavity_volume_cm3,
            target_hz=design.target_absorber_frequency_hz,
            design=design,
        )
        for width in design.witness_slot_widths
    }
    nominal_slot_length = _solve_slot_length_mm(
        width_mm=design.nominal_finished_slot_width,
        volume_cm3=cavity_volume_cm3,
        target_hz=design.target_absorber_frequency_hz,
        design=design,
    )
    pilot_tools = _slot_tools(
        width=design.pilot_slot_width,
        overall_length=design.pilot_slot_length,
        design=design,
    )
    nominal_tools = _slot_tools(
        width=design.nominal_finished_slot_width,
        overall_length=nominal_slot_length,
        design=design,
    )
    witness_tools = _witness_tools(
        target_lengths=target_lengths,
        design=design,
    )
    marked_blank = _subtract_tools(blank, witness_tools)
    core_pilot = _subtract_tools(marked_blank, pilot_tools)
    core_nominal = _subtract_tools(marked_blank, nominal_tools)
    if not core_pilot.is_valid or not core_nominal.is_valid or not bucket.is_valid:
        raise ValueError("Pilot core, finished core, or bucket is invalid")

    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    airway = Cylinder(design.bore_r, design.overall_length, align=alignment)
    pilot_air_domain = (airway + cavity_bulk).clean().fix()
    nominal_air_domain = (airway + cavity_bulk).clean().fix()
    for tool in pilot_tools:
        pilot_air_domain = (pilot_air_domain + tool).clean().fix()
    for tool in nominal_tools:
        nominal_air_domain = (nominal_air_domain + tool).clean().fix()

    adapters: dict[str, Any] = {}
    installed_adapters: dict[str, tuple[Any, Any]] = {}
    connected_assemblies: dict[str, Any] = {}
    for tube_wall_t in design.adapter_tube_wall_variants:
        key = f"{tube_wall_t:g}mm_wall"
        adapter = bucket_base._tube_socket_adapter(tube_wall_t, design)
        bottom_adapter = Rot(180, 0, 0) * adapter
        top_adapter = Pos(0, 0, design.overall_length) * adapter
        adapters[key] = adapter
        installed_adapters[key] = (bottom_adapter, top_adapter)
        connected_assemblies[key] = Compound(
            children=[core_nominal, bucket, bottom_adapter, top_adapter]
        )

    default_key = f"{design.adapter_tube_wall_variants[0]:g}mm_wall"
    bottom_adapter, top_adapter = installed_adapters[default_key]
    assembly_pilot = Compound(children=[core_pilot, bucket])
    assembly_nominal = Compound(children=[core_nominal, bucket])
    connected_nominal = connected_assemblies[default_key]
    connected_fused = (
        core_nominal + bucket + bottom_adapter + top_adapter
    ).clean().fix()

    keep = Rot(0, 0, 35) * Box(
        2.2 * design.outer_r,
        1.1 * design.outer_r,
        design.overall_length + 2.0 * design.adapter_total_length,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    keep = Pos(0, 0, -design.adapter_total_length) * keep
    cutaway = (connected_fused & keep).clean().fix()
    exploded = Compound(
        children=[
            Pos(-45, 0, 0) * core_pilot,
            Pos(45, 0, 0) * bucket,
            Pos(-45, 0, -25) * bottom_adapter,
            Pos(45, 0, 135) * top_adapter,
        ]
    )

    coupon = _calibration_coupon(design)
    inverted_bucket = Rot(180, 0, 0) * bucket
    bucket_min_z = inverted_bucket.bounding_box().min.Z
    print_layout = Compound(
        children=[
            Pos(-90, 0, 0) * core_pilot,
            Pos(-10, 0, -bucket_min_z) * inverted_bucket,
            Pos(70, -42, 0) * adapters[default_key],
            Pos(70, 42, 0) * adapters[default_key],
            Pos(145, 0, 0) * coupon,
        ]
    )

    extended_airway = Pos(0, 0, -design.adapter_total_length) * Cylinder(
        design.bore_r,
        design.overall_length + 2.0 * design.adapter_total_length,
        align=alignment,
    )
    return {
        "blank": blank,
        "core_pilot": core_pilot,
        "core_nominal": core_nominal,
        "bucket": bucket,
        "cavity_bulk": cavity_bulk,
        "cavity_volume_cm3": cavity_volume_cm3,
        "airway": airway,
        "extended_airway": extended_airway,
        "pilot_tools": pilot_tools,
        "nominal_tools": nominal_tools,
        "pilot_air_domain": pilot_air_domain,
        "nominal_air_domain": nominal_air_domain,
        "nominal_slot_length_mm": nominal_slot_length,
        "target_lengths_by_width_mm": target_lengths,
        "adapters": adapters,
        "default_adapter_key": default_key,
        "assembly_pilot": assembly_pilot,
        "assembly_nominal": assembly_nominal,
        "connected_assemblies": connected_assemblies,
        "connected_fused": connected_fused,
        "cutaway": cutaway,
        "exploded": exploded,
        "print_layout": print_layout,
        "coupon": coupon,
    }


def _intersection_volume(first: Any, second: Any) -> float:
    return sum(solid.volume for solid in (first & second).solids())


def _geometry_diagnostics(geometry: dict[str, Any], design: Design) -> dict[str, Any]:
    material = Compound(children=[geometry["core_nominal"], geometry["bucket"]])
    material_in_bore = _intersection_volume(material, geometry["airway"])
    connected_in_bore = _intersection_volume(
        geometry["connected_assemblies"][geometry["default_adapter_key"]],
        geometry["extended_airway"],
    )
    if material_in_bore > 0.001 or connected_in_bore > 0.001:
        raise ValueError("Absorber material intrudes into the 40 mm airway")
    if len(geometry["pilot_air_domain"].solids()) != 1:
        raise ValueError("Pilot slots do not connect bore to chamber")
    if len(geometry["nominal_air_domain"].solids()) != 1:
        raise ValueError("Finished slots do not connect bore to chamber")

    slot_connections: list[dict[str, float]] = []
    for index, tool in enumerate(geometry["nominal_tools"], start=1):
        bore_overlap = _intersection_volume(tool, geometry["airway"])
        cavity_overlap = _intersection_volume(tool, geometry["cavity_bulk"])
        if bore_overlap <= 0.0 or cavity_overlap <= 0.0:
            raise ValueError(f"Finished slot {index} misses bore or chamber")
        slot_connections.append(
            {
                "slot": index,
                "bore_overlap_mm3": bore_overlap,
                "cavity_overlap_mm3": cavity_overlap,
            }
        )
    return {
        "main_airway": {
            "nominal_diameter_mm": design.main_bore_d,
            "material_intrusion_mm3": material_in_bore,
            "connected_assembly_intrusion_mm3": connected_in_bore,
            "continuous_circular_bore": True,
        },
        "common_cavity": {
            "solid_count": len(geometry["cavity_bulk"].solids()),
            "gross_volume_cm3": geometry["cavity_volume_cm3"],
        },
        "slot_connections": slot_connections,
        "surface_seam": {
            "physical_joint": False,
            "slot_angle_offset_deg": design.rail_angle_offset_deg,
            "slicer_instruction": (
                "Paint the FDM Z seam between rails; the STEP cylinder seam is "
                "not a physical feature."
            ),
        },
        "printability": {
            "supports_required": False,
            "core": "axis vertical, integral annular floor on build plate",
            "bucket": "inverted, integral annular cap on build plate",
            "slots": (
                "vertical open notches repeated in XY; no long horizontal roof; "
                f"physical radial passage {design.neck_physical_length:.3f} mm"
            ),
            "coupon": (
                "same core wall, radial passage, rail width, and vertical "
                "orientation as the full core"
            ),
        },
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


def _length_tuning_rows(
    *, width_mm: float, volume_cm3: float, design: Design
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    length = design.pilot_slot_length
    while length <= 17.0001:
        rows.append(
            {
                "finished_width_mm": width_mm,
                "overall_slot_length_each_mm": round(length, 3),
                "predicted_frequency_hz": _slot_frequency_hz(
                    width_mm=width_mm,
                    overall_length_mm=length,
                    volume_cm3=volume_cm3,
                    design=design,
                ),
            }
        )
        length += 0.5
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-frequency", type=float)
    parser.add_argument("--pilot-width", type=float)
    parser.add_argument("--pilot-length", type=float)
    parser.add_argument("--finished-width", type=float)
    parser.add_argument("--neck-length", type=float)
    parser.add_argument("--length", type=float)
    parser.add_argument("--outer-diameter", type=float)
    return parser.parse_args()


def _design_from_args(args: argparse.Namespace) -> Design:
    mapping = {
        "target_frequency": "target_absorber_frequency_hz",
        "pilot_width": "pilot_slot_width",
        "pilot_length": "pilot_slot_length",
        "finished_width": "nominal_finished_slot_width",
        "neck_length": "neck_physical_length",
        "length": "overall_length",
        "outer_diameter": "maximum_outer_d",
    }
    values = {
        field: getattr(args, argument)
        for argument, field in mapping.items()
        if getattr(args, argument) is not None
    }
    return replace(D, **values) if values else D


def main() -> None:
    design = _design_from_args(_parse_args())
    _validate_design(design)
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_geometry(design)
    volume_cm3 = geometry["cavity_volume_cm3"]
    nominal_length = geometry["nominal_slot_length_mm"]
    nominal_properties = _slot_properties(
        width_mm=design.nominal_finished_slot_width,
        overall_length_mm=nominal_length,
        volume_cm3=volume_cm3,
        design=design,
    )
    pilot_properties = _slot_properties(
        width_mm=design.pilot_slot_width,
        overall_length_mm=design.pilot_slot_length,
        volume_cm3=volume_cm3,
        design=design,
    )

    ideal_tmm_design, tmm_geometry = _equivalent_tmm_inputs(
        properties=nominal_properties,
        volume_cm3=volume_cm3,
        assumed_q=1.0,
        design=design,
    )
    ideal_model, ideal_rows = acoustic_base._run_acoustic_model(
        tmm_geometry, ideal_tmm_design
    )
    geometric_q = nominal_properties[
        "q_from_smooth_wall_boundary_estimate_before_edge_losses"
    ]
    geometric_tmm_design = replace(ideal_tmm_design, absorber_q=geometric_q)
    geometric_model, geometric_rows = acoustic_base._run_acoustic_model(
        tmm_geometry, geometric_tmm_design
    )

    geometry_checks = _geometry_diagnostics(geometry, design)
    nominal_token = (
        f"{design.nominal_finished_slot_width:.2f}".replace(".", "p")
    )
    exports = {
        "port_absorber_slotted_inner_core_pilot.step": geometry["core_pilot"],
        f"port_absorber_slotted_inner_core_{nominal_token}_finished_reference.step": (
            geometry["core_nominal"]
        ),
        "port_absorber_slotted_outer_bucket.step": geometry["bucket"],
        "port_absorber_slotted_socket_adapter_40id_46od.step": geometry[
            "adapters"
        ]["3mm_wall"],
        "port_absorber_slotted_socket_adapter_40id_50od.step": geometry[
            "adapters"
        ]["5mm_wall"],
        "port_absorber_slotted_assembly_pilot.step": geometry["assembly_pilot"],
        "port_absorber_slotted_assembly_finished_reference.step": geometry[
            "assembly_nominal"
        ],
        "port_absorber_slotted_connected_46od_tubes.step": geometry[
            "connected_assemblies"
        ]["3mm_wall"],
        "port_absorber_slotted_connected_50od_tubes.step": geometry[
            "connected_assemblies"
        ]["5mm_wall"],
        "port_absorber_slotted_cutaway.step": geometry["cutaway"],
        "port_absorber_slotted_exploded.step": geometry["exploded"],
        "port_absorber_slotted_print_layout.step": geometry["print_layout"],
        "port_absorber_slotted_air_domain_finished.step": geometry[
            "nominal_air_domain"
        ],
        "port_absorber_slotted_calibration_coupon.step": geometry["coupon"],
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

    finish_width_rows: list[dict[str, float]] = []
    comparison_widths = sorted(
        set(
            (0.40, 0.50, 0.60, 0.70, 0.80)
            + design.witness_slot_widths
            + (design.nominal_finished_slot_width,)
        )
    )
    for width in comparison_widths:
        solved_length = _solve_slot_length_mm(
            width_mm=width,
            volume_cm3=volume_cm3,
            target_hz=design.target_absorber_frequency_hz,
            design=design,
        )
        props = _slot_properties(
            width_mm=width,
            overall_length_mm=solved_length,
            volume_cm3=volume_cm3,
            design=design,
        )
        finish_width_rows.append(
            {
                "finished_width_mm": width,
                "required_overall_length_each_mm": solved_length,
                "total_open_area_mm2": props["total_area_mm2"],
                "hydraulic_diameter_mm": props["hydraulic_diameter_mm"],
                "smooth_wall_q_estimate_before_edge_losses": props[
                    "q_from_smooth_wall_boundary_estimate_before_edge_losses"
                ],
            }
        )

    diagnostics = {
        "name": design.name,
        "status": (
            "straight cylindrical calibration version; final folded-port "
            "integration remains a later geometry pass"
        ),
        "design_inputs": asdict(design),
        "architecture": {
            "inner_core": (
                "40 mm continuous bore, integral lower floor, four vertical "
                "tool-access rails, blind endpoint witness notches"
            ),
            "outer_bucket": (
                "removable sleeve with integral upper annular closure; printed "
                "inverted and lowered over the core after slot finishing"
            ),
            "tube_interfaces": (
                "two separately printed support-free female socket adapters; "
                "46.4 mm ID for 46 mm OD tube and 50.4 mm ID for 50 mm OD tube"
            ),
            "mesh_or_fill": "none",
        },
        "acoustic_target": {
            "target_frequency_hz": design.target_absorber_frequency_hz,
            "physical_port_length_mm": design.main_port_physical_length_mm,
            "lf_effective_length_not_used_for_pipe_mode_mm": (
                design.reported_lf_effective_length_mm
            ),
            "provisional_pressure_antinode_mm_from_inlet": design.coupling_path_mm,
            "cavity_volume_from_cad_cm3": volume_cm3,
        },
        "print_ready_pilot": pilot_properties,
        "nominal_finished_slot": nominal_properties,
        "finish_width_options_at_same_target": finish_width_rows,
        "nominal_width_length_tuning": _length_tuning_rows(
            width_mm=design.nominal_finished_slot_width,
            volume_cm3=volume_cm3,
            design=design,
        ),
        "tuning_order": {
            "1": (
                "Print and measure the calibration coupon; confirm that the "
                f"{design.pilot_slot_width:.2f} mm pilot can be established "
                "continuously with the intended print and tooling process."
            ),
            "2": (
                "Finish all four slot widths equally to "
                f"{design.nominal_finished_slot_width:.2f} mm. Width is the "
                "primary damping/Q choice and should be established first."
            ),
            "3": (
                "Assemble with removable airtight seals and measure at the port "
                "mouth. Extend total slot length in small equal increments to "
                "raise the absorber center frequency."
            ),
            "4": (
                "Near target, extend one slot endpoint at a time for fine steps; "
                "deburr without chamfering the bore-side edges."
            ),
        },
        "witness_marks": {
            "blind_not_through": True,
            "target_overall_lengths_by_finished_width_mm": {
                str(width): length
                for width, length in geometry[
                    "target_lengths_by_width_mm"
                ].items()
            },
            "reading": (
                "The explicit width-to-tip-length mapping above is authoritative; "
                "marks closer to the slot center correspond to shorter target "
                "lengths."
            ),
        },
        "calibration_coupon": {
            "angles_and_widths_mm": [
                {
                    "angle_deg": (
                        design.rail_angle_offset_deg
                        + 360.0 * index / design.rail_count
                    ),
                    "nominal_width_mm": width,
                }
                for index, width in enumerate(design.coupon_slot_widths)
            ],
            "slot_length_mm": design.pilot_slot_length,
        },
        "geometry_validation": geometry_checks,
        "acoustic_models": {
            "ideal_q1": ideal_model,
            "smooth_wall_boundary_q": geometric_model,
            "qualification": (
                "The Q=1 case is a low-Q response illustration. The smooth-wall "
                "boundary estimate excludes entrance contraction, FDM texture, "
                "tool marks, leakage, and nonlinear loss; actual Q must be measured."
            ),
        },
        "step_roundtrip": roundtrip,
    }
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=False) + "\n"
    )

    for source, viewer_name in (
        ("port_absorber_slotted_connected_46od_tubes.step", "viewer"),
        ("port_absorber_slotted_cutaway.step", "cutaway_viewer"),
        ("port_absorber_slotted_exploded.step", "exploded_viewer"),
        ("port_absorber_slotted_print_layout.step", "print_layout_viewer"),
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

    print(f"Pilot core: {OUT / 'port_absorber_slotted_inner_core_pilot.step'}")
    print(f"Outer bucket: {OUT / 'port_absorber_slotted_outer_bucket.step'}")
    print(f"Assembly: {OUT / 'port_absorber_slotted_connected_46od_tubes.step'}")
    print(f"Cutaway: {OUT / 'port_absorber_slotted_cutaway.step'}")
    print(f"Coupon: {OUT / 'port_absorber_slotted_calibration_coupon.step'}")
    print(f"Diagnostics: {OUT / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
