"""Generate the removable bucket-style Helmholtz absorber collar experiment.

The print-ready inner core has a continuous unchanged bore, an integral lower
chamber floor, four self-supporting vertical neck rails, and tiny diamond pilot
passages.  The outer sleeve and upper chamber closure are one inverted-print
"bucket" that slides over the core after the pilots are drilled round.  Two
identical separately printed socket adapters connect the module to 40 mm-ID
tube while keeping every print support-free.

This remains an isolated experiment.  It does not modify the production port.
All CAD dimensions are millimetres; acoustic calculations use SI units.
"""

from __future__ import annotations

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

from experiments.sand_cube_190x210_port_absorber_collar import (
    generate_port_absorber_collar as prior,
)


OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_bucket"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_190x210_port_absorber_bucket_v1"

    # Nominal round tube is now exactly 40 mm ID.  The production port remains
    # untouched until this isolated module and its interfaces are validated.
    main_bore_d: float = 40.0
    host_tube_wall_t: float = prior.D.existing_tube_wall_t
    main_port_area_mm2: float = 1256.6370614359173
    main_port_physical_length_mm: float = prior.D.main_port_physical_length_mm
    reported_lf_effective_length_mm: float = prior.D.reported_lf_effective_length_mm
    net_box_volume_l: float = prior.D.net_box_volume_l
    bass_reflex_tuning_hz: float = prior.D.bass_reflex_tuning_hz

    # Long, relatively slim bucket geometry.
    overall_length: float = 120.0
    maximum_outer_d: float = 68.0
    bucket_wall_t: float = 3.0
    bottom_floor_t: float = 3.0
    bucket_top_t: float = 3.0
    core_wall_t: float = 5.0
    slip_clearance_radial: float = 0.20

    # The lower lip locates the open bucket rim.  The upper skirt is integral
    # with the bucket cap and prints upward when the bucket is inverted.
    lower_lip_height: float = 6.0
    lower_lip_radial_t: float = 1.0
    lower_lip_clearance: float = 0.20
    upper_skirt_height: float = 6.0
    upper_skirt_radial_t: float = 2.5

    # Four vertical rails are grown from the integral floor.  Six drillable
    # passages in each rail give 24 holes total after reaming.
    rail_count: int = 4
    rail_angle_offset_deg: float = 30.0
    rail_tangential_width: float = 6.0
    rail_core_overlap: float = 0.80
    neck_physical_length: float = 8.0
    holes_per_rail: int = 6
    hole_row_pitch: float = 10.0
    pilot_diamond_span: float = 0.90
    nominal_ream_diameter_override: float | None = None

    # Two identical support-free end adapters may be printed for either the
    # 3 mm-wall internal tube (46 mm OD) or 5 mm-wall tower tube (50 mm OD).
    adapter_plate_t: float = 3.0
    adapter_socket_depth: float = 10.0
    adapter_socket_wall_t: float = 3.0
    adapter_socket_clearance_diametral: float = 0.40
    adapter_tube_wall_variants: tuple[float, ...] = (3.0, 5.0)

    target_absorber_frequency_hz: float = 345.0
    assumed_absorber_q_for_tmm: float = 1.0
    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204
    dynamic_viscosity_pa_s: float = 1.81e-5

    # Two-sided flush-aperture end correction: 0.85r + 0.85r = 0.85d.
    end_correction_beta: float = 0.85
    end_correction_beta_low: float = 0.70
    end_correction_beta_high: float = 1.00

    # Lumped placement retained from the accessible external-tower study.  The
    # 50 mm hole band is represented as one shunt at this coordinate.
    coupling_path_mm: float = prior.D.collar_center_path_mm

    @property
    def bore_r(self) -> float:
        return self.main_bore_d / 2.0

    @property
    def core_outer_r(self) -> float:
        return self.bore_r + self.core_wall_t

    @property
    def outer_r(self) -> float:
        return self.maximum_outer_d / 2.0

    @property
    def bucket_inner_r(self) -> float:
        return self.outer_r - self.bucket_wall_t

    @property
    def rail_outer_r(self) -> float:
        return self.bore_r + self.neck_physical_length

    @property
    def rail_radial_depth(self) -> float:
        return self.rail_outer_r - self.core_outer_r + self.rail_core_overlap

    @property
    def top_cap_bottom_z(self) -> float:
        return self.overall_length - self.bucket_top_t

    @property
    def top_hole_r(self) -> float:
        return self.core_outer_r + self.slip_clearance_radial

    @property
    def upper_skirt_outer_r(self) -> float:
        return self.top_hole_r + self.upper_skirt_radial_t

    @property
    def lower_lip_outer_r(self) -> float:
        return self.bucket_inner_r - self.lower_lip_clearance

    @property
    def lower_lip_inner_r(self) -> float:
        return self.lower_lip_outer_r - self.lower_lip_radial_t

    @property
    def total_holes(self) -> int:
        return self.rail_count * self.holes_per_rail

    @property
    def hole_band_length(self) -> float:
        return (self.holes_per_rail - 1) * self.hole_row_pitch

    @property
    def hole_z_positions(self) -> tuple[float, ...]:
        center = self.overall_length / 2.0
        start = center - self.hole_band_length / 2.0
        return tuple(
            start + i * self.hole_row_pitch for i in range(self.holes_per_rail)
        )

    @property
    def adapter_total_length(self) -> float:
        return self.adapter_plate_t + self.adapter_socket_depth

    def mating_tube_outer_d(self, tube_wall_t: float) -> float:
        return self.main_bore_d + 2.0 * tube_wall_t

    def adapter_socket_inner_r(self, tube_wall_t: float) -> float:
        return (
            self.mating_tube_outer_d(tube_wall_t)
            + self.adapter_socket_clearance_diametral
        ) / 2.0

    def adapter_socket_outer_r(self, tube_wall_t: float) -> float:
        return self.adapter_socket_inner_r(tube_wall_t) + self.adapter_socket_wall_t


D = Design()


def _validate_design(design: Design) -> None:
    if design.rail_count < 1 or design.holes_per_rail < 1:
        raise ValueError("At least one rail and one hole per rail are required")
    if design.rail_radial_depth <= 0.0:
        raise ValueError("Neck length must exceed the host core-wall thickness")
    if design.rail_core_overlap <= 0.0:
        raise ValueError("Drill rails need positive overlap into the core wall")
    if design.rail_outer_r >= design.bucket_inner_r:
        raise ValueError("Neck rails collide with the bucket inner wall")
    if design.upper_skirt_outer_r >= design.bucket_inner_r:
        raise ValueError("Upper sealing skirt consumes the chamber radial depth")
    if design.bottom_floor_t + design.lower_lip_height >= min(design.hole_z_positions):
        raise ValueError("The first pilot hole collides with the lower locating lip")
    if (
        design.top_cap_bottom_z - design.upper_skirt_height
        <= max(design.hole_z_positions)
    ):
        raise ValueError("The last pilot hole collides with the upper sealing skirt")
    if design.pilot_diamond_span <= 0.0:
        raise ValueError("Pilot size must be positive")
    if design.target_absorber_frequency_hz <= 0.0:
        raise ValueError("Target frequency must be positive")
    if not design.adapter_tube_wall_variants:
        raise ValueError("At least one tube-wall adapter variant is required")
    for wall_t in design.adapter_tube_wall_variants:
        if wall_t <= 0.0:
            raise ValueError("Mating tube wall thickness must be positive")
        if design.adapter_socket_outer_r(wall_t) >= design.outer_r:
            raise ValueError("Tube socket does not fit inside the adapter flange")


def _shell(outer_r: float, inner_r: float, height: float, z: float = 0.0) -> Any:
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    outer = Pos(0, 0, z) * Cylinder(outer_r, height, align=alignment)
    inner = Pos(0, 0, z - 0.01) * Cylinder(
        inner_r,
        height + 0.02,
        align=alignment,
    )
    return (outer - inner).clean().fix()


def _rail(angle_deg: float, design: Design) -> Any:
    rail = Box(
        design.rail_radial_depth,
        design.rail_tangential_width,
        design.top_cap_bottom_z - design.bottom_floor_t,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    return (
        Rot(0, 0, angle_deg)
        * Pos(
            design.core_outer_r - design.rail_core_overlap,
            0,
            design.bottom_floor_t,
        )
        * rail
    )


def _radial_diamond_tool(
    *, angle_deg: float, z: float, span: float, design: Design
) -> Any:
    # A square rotated 45 degrees around the radial axis gives a self-supporting
    # diamond tunnel.  `span` is its corner-to-corner Y/Z envelope.
    side = span / math.sqrt(2.0)
    overlap = 0.15
    tool = Box(
        design.neck_physical_length + 2.0 * overlap,
        side,
        side,
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    )
    return (
        Rot(0, 0, angle_deg)
        * Pos(design.bore_r - overlap, 0, z)
        * Rot(45, 0, 0)
        * tool
    )


def _radial_round_tool(
    *, angle_deg: float, z: float, diameter: float, design: Design
) -> Any:
    overlap = 0.15
    return prior._radial_cylinder(
        angle_deg=angle_deg,
        radial_start=design.bore_r - overlap,
        length=design.neck_physical_length + 2.0 * overlap,
        radius=diameter / 2.0,
        z=z,
    )


def _all_neck_tools(
    design: Design, *, round_diameter: float | None
) -> list[Any]:
    tools: list[Any] = []
    for rail_index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * rail_index / design.rail_count
        )
        for z in design.hole_z_positions:
            if round_diameter is None:
                tool = _radial_diamond_tool(
                    angle_deg=angle,
                    z=z,
                    span=design.pilot_diamond_span,
                    design=design,
                )
            else:
                tool = _radial_round_tool(
                    angle_deg=angle,
                    z=z,
                    diameter=round_diameter,
                    design=design,
                )
            tools.append(tool)
    return tools


def _core_blank(design: Design) -> Any:
    core: Any = _shell(
        design.core_outer_r,
        design.bore_r,
        design.overall_length,
    )
    floor = _shell(
        design.outer_r,
        design.bore_r,
        design.bottom_floor_t,
    )
    core = (core + floor).clean().fix()

    locating_lip = _shell(
        design.lower_lip_outer_r,
        design.lower_lip_inner_r,
        design.lower_lip_height,
        design.bottom_floor_t,
    )
    core = (core + locating_lip).clean().fix()
    for rail_index in range(design.rail_count):
        angle = (
            design.rail_angle_offset_deg
            + 360.0 * rail_index / design.rail_count
        )
        core = (
            core + _rail(angle, design)
        ).clean().fix()
    return core


def _bucket(design: Design) -> Any:
    wall = _shell(
        design.outer_r,
        design.bucket_inner_r,
        design.overall_length - design.bottom_floor_t,
        design.bottom_floor_t,
    )
    cap = _shell(
        design.outer_r,
        design.top_hole_r,
        design.bucket_top_t,
        design.top_cap_bottom_z,
    )
    skirt = _shell(
        design.upper_skirt_outer_r,
        design.top_hole_r,
        design.upper_skirt_height,
        design.top_cap_bottom_z - design.upper_skirt_height,
    )
    return (wall + cap + skirt).clean().fix()


def _tube_socket_adapter(tube_wall_t: float, design: Design) -> Any:
    """One reversible end adapter; print two copies for a symmetric module."""
    plate = _shell(
        design.outer_r,
        design.bore_r,
        design.adapter_plate_t,
    )
    socket = _shell(
        design.adapter_socket_outer_r(tube_wall_t),
        design.adapter_socket_inner_r(tube_wall_t),
        design.adapter_socket_depth,
        design.adapter_plate_t,
    )
    return (plate + socket).clean().fix()


def _cut_necks(blank: Any, tools: list[Any]) -> Any:
    result = blank
    for tool in tools:
        result = (result - tool).clean().fix()
    return result


def _potential_chamber_envelope(design: Design) -> Any:
    return _shell(
        design.bucket_inner_r,
        design.bore_r,
        design.top_cap_bottom_z - design.bottom_floor_t,
        design.bottom_floor_t,
    )


def _helmholtz_frequency_hz(
    *, diameter_mm: float, hole_count: int, volume_cm3: float, design: Design,
    beta: float | None = None, speed_of_sound_m_s: float | None = None,
) -> float:
    beta_value = design.end_correction_beta if beta is None else beta
    d_m = diameter_mm / 1000.0
    total_area_m2 = hole_count * math.pi * d_m**2 / 4.0
    effective_length_m = (
        design.neck_physical_length + beta_value * diameter_mm
    ) / 1000.0
    volume_m3 = volume_cm3 / 1_000_000.0
    c = design.speed_of_sound_m_s if speed_of_sound_m_s is None else speed_of_sound_m_s
    return c / (2.0 * math.pi) * math.sqrt(
        total_area_m2 / (volume_m3 * effective_length_m)
    )


def _solve_ream_diameter_mm(
    *,
    hole_count: int,
    volume_cm3: float,
    target_hz: float,
    design: Design,
    respect_printed_pilot: bool = True,
) -> float:
    low = max(design.pilot_diamond_span * 1.01, 0.5)
    if not respect_printed_pilot:
        low = 0.20
    high = 4.0
    if _helmholtz_frequency_hz(
        diameter_mm=low,
        hole_count=hole_count,
        volume_cm3=volume_cm3,
        design=design,
    ) > target_hz:
        raise ValueError("Pilot is already larger than the solved ream diameter")
    if _helmholtz_frequency_hz(
        diameter_mm=high,
        hole_count=hole_count,
        volume_cm3=volume_cm3,
        design=design,
    ) < target_hz:
        raise ValueError("Target is above the available ream-diameter range")
    for _ in range(80):
        middle = (low + high) / 2.0
        frequency = _helmholtz_frequency_hz(
            diameter_mm=middle,
            hole_count=hole_count,
            volume_cm3=volume_cm3,
            design=design,
        )
        if frequency < target_hz:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _resonator_properties(
    *, diameter_mm: float, volume_cm3: float, design: Design
) -> dict[str, float]:
    d_m = diameter_mm / 1000.0
    area_each_m2 = math.pi * d_m**2 / 4.0
    total_area_m2 = design.total_holes * area_each_m2
    effective_length_m = (
        design.neck_physical_length + design.end_correction_beta * diameter_mm
    ) / 1000.0
    acoustic_mass = (
        design.air_density_kg_m3 * effective_length_m / total_area_m2
    )
    compliance = (volume_cm3 / 1_000_000.0) / (
        design.air_density_kg_m3 * design.speed_of_sound_m_s**2
    )
    omega = 2.0 * math.pi * design.target_absorber_frequency_hz
    resistance_for_assumed_q = (
        omega * acoustic_mass / design.assumed_absorber_q_for_tmm
    )
    boundary_layer_m = math.sqrt(
        2.0
        * design.dynamic_viscosity_pa_s
        / (design.air_density_kg_m3 * omega)
    )
    radius_m = d_m / 2.0
    steady_poiseuille_resistance = (
        8.0
        * design.dynamic_viscosity_pa_s
        * (design.neck_physical_length / 1000.0)
        / (design.total_holes * math.pi * radius_m**4)
    )
    oscillatory_boundary_resistance = (
        16.0
        * (design.neck_physical_length / 1000.0)
        / (design.total_holes * math.pi * d_m**3)
        * math.sqrt(
            omega
            * design.air_density_kg_m3
            * design.dynamic_viscosity_pa_s
            / 2.0
        )
    )
    boundary_estimated_q = (
        omega * acoustic_mass / oscillatory_boundary_resistance
    )
    return {
        "hole_count": design.total_holes,
        "diameter_each_mm": diameter_mm,
        "area_each_mm2": area_each_m2 * 1_000_000.0,
        "total_neck_area_mm2": total_area_m2 * 1_000_000.0,
        "effective_neck_length_each_mm": effective_length_m * 1000.0,
        "acoustic_mass_equivalent_pa_s2_per_m3": acoustic_mass,
        "cavity_compliance_m5_per_n": compliance,
        "required_resistance_for_assumed_q_pa_s_per_m3": resistance_for_assumed_q,
        "viscous_boundary_layer_mm": boundary_layer_m * 1000.0,
        "hole_radius_to_boundary_layer_ratio": radius_m / boundary_layer_m,
        "steady_poiseuille_resistance_comparison_only_pa_s_per_m3": (
            steady_poiseuille_resistance
        ),
        "high_womersley_boundary_resistance_estimate_pa_s_per_m3": (
            oscillatory_boundary_resistance
        ),
        "q_from_boundary_resistance_before_end_losses": boundary_estimated_q,
    }


def _equivalent_tmm_inputs(
    *, diameter_mm: float, volume_cm3: float, design: Design
) -> tuple[prior.Design, dict[str, Any]]:
    # The prior TMM accepts one circular neck.  Preserve actual parallel-neck
    # area and mass with an area-equivalent diameter and adjusted physical
    # length.  This is only a lumped network equivalence, not CAD geometry.
    equivalent_diameter = math.sqrt(design.total_holes) * diameter_mm
    actual_effective_length = (
        design.neck_physical_length + design.end_correction_beta * diameter_mm
    )
    equivalent_physical_length = (
        actual_effective_length
        - design.end_correction_beta * equivalent_diameter
    )
    if equivalent_physical_length <= 0.0:
        raise ValueError("Equivalent TMM physical length became non-positive")
    tmm_design = replace(
        prior.D,
        name=design.name,
        main_bore_d=design.main_bore_d,
        main_port_area_mm2=design.main_port_area_mm2,
        throat_d=design.main_bore_d,
        chamber_count=1,
        target_frequency_multipliers=(1.0,),
        target_absorber_frequency_hz=design.target_absorber_frequency_hz,
        absorber_q=design.assumed_absorber_q_for_tmm,
        neck_physical_length=equivalent_physical_length,
        collar_center_path_mm=design.coupling_path_mm,
        speed_of_sound_m_s=design.speed_of_sound_m_s,
        air_density_kg_m3=design.air_density_kg_m3,
    )
    geometry = {
        "neck_diameters_mm": [equivalent_diameter],
        "acoustic_volumes_cm3": [volume_cm3],
    }
    return tmm_design, geometry


def _build_geometry(design: Design) -> dict[str, Any]:
    blank = _core_blank(design)
    bucket = _bucket(design)
    pilot_tools = _all_neck_tools(design, round_diameter=None)
    core_pilot = _cut_necks(blank, pilot_tools)

    cavity_bulk: Any = (
        _potential_chamber_envelope(design) - blank - bucket
    ).clean().fix()
    cavity_solids = list(cavity_bulk.solids())
    if len(cavity_solids) != 1:
        raise ValueError(
            f"Expected one connected common annular cavity, got {len(cavity_solids)}"
        )
    cavity_volume_cm3 = cavity_solids[0].volume / 1000.0

    nominal_diameter = design.nominal_ream_diameter_override
    if nominal_diameter is None:
        nominal_diameter = _solve_ream_diameter_mm(
            hole_count=design.total_holes,
            volume_cm3=cavity_volume_cm3,
            target_hz=design.target_absorber_frequency_hz,
            design=design,
        )
    round_tools = _all_neck_tools(design, round_diameter=nominal_diameter)
    core_reamed = _cut_necks(blank, round_tools)
    if not core_pilot.is_valid or not core_reamed.is_valid or not bucket.is_valid:
        raise ValueError("Core or bucket is invalid")

    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    airway = Cylinder(design.bore_r, design.overall_length, align=alignment)
    pilot_air_domain: Any = (airway + cavity_bulk).clean().fix()
    for tool in pilot_tools:
        pilot_air_domain = (pilot_air_domain + tool).clean().fix()
    nominal_air_domain: Any = (airway + cavity_bulk).clean().fix()
    for tool in round_tools:
        nominal_air_domain = (nominal_air_domain + tool).clean().fix()

    assembly_pilot = Compound(children=[core_pilot, bucket])
    assembly_nominal = Compound(children=[core_reamed, bucket])
    fused_nominal = (core_reamed + bucket).clean().fix()

    adapters: dict[str, Any] = {}
    connected_assemblies: dict[str, Any] = {}
    connected_fused: dict[str, Any] = {}
    installed_adapters: dict[str, tuple[Any, Any]] = {}
    for tube_wall_t in design.adapter_tube_wall_variants:
        key = f"{tube_wall_t:g}mm_wall"
        adapter = _tube_socket_adapter(tube_wall_t, design)
        bottom_adapter = Rot(180, 0, 0) * adapter
        top_adapter = Pos(0, 0, design.overall_length) * adapter
        adapters[key] = adapter
        installed_adapters[key] = (bottom_adapter, top_adapter)
        connected_assemblies[key] = Compound(
            children=[core_reamed, bucket, bottom_adapter, top_adapter]
        )
        connected_fused[key] = (
            fused_nominal + bottom_adapter + top_adapter
        ).clean().fix()

    default_adapter_key = f"{design.adapter_tube_wall_variants[0]:g}mm_wall"
    default_bottom_adapter, default_top_adapter = installed_adapters[
        default_adapter_key
    ]
    default_connected_fused = connected_fused[default_adapter_key]
    cutaway_keep = Rot(0, 0, 35) * Box(
        2.2 * design.outer_r,
        1.1 * design.outer_r,
        design.overall_length + 2.0 * design.adapter_total_length,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    cutaway_keep = Pos(0, 0, -design.adapter_total_length) * cutaway_keep
    cutaway = (default_connected_fused & cutaway_keep).clean().fix()
    exploded = Compound(
        children=[
            core_pilot,
            Pos(0, 0, 35) * bucket,
            Pos(0, 0, -20) * default_bottom_adapter,
            Pos(0, 0, 70) * default_top_adapter,
        ]
    )

    # Print layout: core upright; bucket inverted so its integrated top collar
    # is on the build plate and the open end grows upward.
    inverted_bucket = Rot(180, 0, 0) * bucket
    bucket_min_z = inverted_bucket.bounding_box().min.Z
    print_layout = Compound(
        children=[
            Pos(-70, 0, 0) * core_pilot,
            Pos(10, 0, -bucket_min_z) * inverted_bucket,
            Pos(90, -40, 0) * adapters[default_adapter_key],
            Pos(90, 40, 0) * adapters[default_adapter_key],
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
        "core_reamed": core_reamed,
        "bucket": bucket,
        "assembly_pilot": assembly_pilot,
        "assembly_nominal": assembly_nominal,
        "adapters": adapters,
        "connected_assemblies": connected_assemblies,
        "connected_fused": connected_fused,
        "default_adapter_key": default_adapter_key,
        "fused_nominal": fused_nominal,
        "cutaway": cutaway,
        "exploded": exploded,
        "print_layout": print_layout,
        "airway": airway,
        "extended_airway": extended_airway,
        "cavity_bulk": cavity_bulk,
        "pilot_air_domain": pilot_air_domain,
        "nominal_air_domain": nominal_air_domain,
        "pilot_tools": pilot_tools,
        "round_tools": round_tools,
        "cavity_volume_cm3": cavity_volume_cm3,
        "nominal_ream_diameter_mm": nominal_diameter,
    }


def _intersection_volume(first: Any, second: Any) -> float:
    return sum(solid.volume for solid in (first & second).solids())


def _frequency_ladder(
    *, nominal_diameter: float, volume_cm3: float, design: Design
) -> list[dict[str, float]]:
    start = max(design.pilot_diamond_span + 0.05, nominal_diameter - 0.25)
    end = nominal_diameter + 0.20
    first_step = math.ceil(start / 0.05 - 1e-9) * 0.05
    rows: list[dict[str, float]] = []
    diameter = first_step
    while diameter <= end + 1e-9:
        rows.append(
            {
                "ream_diameter_mm": round(diameter, 3),
                "predicted_frequency_hz": _helmholtz_frequency_hz(
                    diameter_mm=diameter,
                    hole_count=design.total_holes,
                    volume_cm3=volume_cm3,
                    design=design,
                ),
            }
        )
        diameter += 0.05
    return rows


def _hole_family_rows(volume_cm3: float, design: Design) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    omega = 2.0 * math.pi * design.target_absorber_frequency_hz
    for count in (16, 24, 32, 64, 96):
        diameter = _solve_ream_diameter_mm(
            hole_count=count,
            volume_cm3=volume_cm3,
            target_hz=design.target_absorber_frequency_hz,
            design=design,
            respect_printed_pilot=False,
        )
        radius_m = diameter / 2000.0
        diameter_m = diameter / 1000.0
        total_area_m2 = count * math.pi * diameter_m**2 / 4.0
        effective_length_m = (
            design.neck_physical_length
            + design.end_correction_beta * diameter
        ) / 1000.0
        acoustic_mass = (
            design.air_density_kg_m3 * effective_length_m / total_area_m2
        )
        resistance = (
            8.0
            * design.dynamic_viscosity_pa_s
            * (design.neck_physical_length / 1000.0)
            / (count * math.pi * radius_m**4)
        )
        boundary_resistance = (
            16.0
            * (design.neck_physical_length / 1000.0)
            / (count * math.pi * diameter_m**3)
            * math.sqrt(
                omega
                * design.air_density_kg_m3
                * design.dynamic_viscosity_pa_s
                / 2.0
            )
        )
        rows.append(
            {
                "hole_count": count,
                "solved_diameter_mm": diameter,
                "total_area_mm2": count * math.pi * diameter**2 / 4.0,
                "steady_poiseuille_resistance_comparison_only_pa_s_per_m3": resistance,
                "high_womersley_boundary_resistance_estimate_pa_s_per_m3": (
                    boundary_resistance
                ),
                "q_from_boundary_resistance_before_end_losses": (
                    omega * acoustic_mass / boundary_resistance
                ),
            }
        )
    baseline = next(row for row in rows if row["hole_count"] == 24)
    for row in rows:
        row["relative_steady_resistance_vs_24_holes"] = (
            row["steady_poiseuille_resistance_comparison_only_pa_s_per_m3"]
            / baseline["steady_poiseuille_resistance_comparison_only_pa_s_per_m3"]
        )
        row["relative_boundary_resistance_vs_24_holes"] = (
            row["high_womersley_boundary_resistance_estimate_pa_s_per_m3"]
            / baseline["high_womersley_boundary_resistance_estimate_pa_s_per_m3"]
        )
    return rows


def _geometry_diagnostics(geometry: dict[str, Any], design: Design) -> dict[str, Any]:
    airway = geometry["airway"]
    cavity = geometry["cavity_bulk"]
    material = geometry["fused_nominal"]
    material_in_bore = _intersection_volume(material, airway)
    connected_material = geometry["connected_fused"][
        geometry["default_adapter_key"]
    ]
    connected_material_in_bore = _intersection_volume(
        connected_material,
        geometry["extended_airway"],
    )
    nominal_air_solid_count = len(geometry["nominal_air_domain"].solids())
    pilot_air_solid_count = len(geometry["pilot_air_domain"].solids())
    if material_in_bore > 0.001:
        raise ValueError(f"Housing intrudes into bore by {material_in_bore:.6f} mm3")
    if connected_material_in_bore > 0.001:
        raise ValueError(
            "Connected adapter assembly intrudes into the 40 mm bore by "
            f"{connected_material_in_bore:.6f} mm3"
        )
    if nominal_air_solid_count != 1 or pilot_air_solid_count != 1:
        raise ValueError(
            "Pilot or nominal neck array does not connect the bore and chamber"
        )

    core_tube = _shell(
        design.core_outer_r,
        design.bore_r,
        design.overall_length,
    )
    rail_core_overlap_volume = _intersection_volume(
        _rail(design.rail_angle_offset_deg, design),
        core_tube,
    )
    if rail_core_overlap_volume <= 1.0:
        raise ValueError(
            "Drill rail does not have a printable volumetric attachment to core"
        )

    connection_rows: list[dict[str, float]] = []
    for index, tool in enumerate(geometry["round_tools"], start=1):
        bore_overlap = _intersection_volume(tool, airway)
        cavity_overlap = _intersection_volume(tool, cavity)
        if bore_overlap <= 0.0 or cavity_overlap <= 0.0:
            raise ValueError(f"Nominal neck {index} misses the bore or cavity")
        connection_rows.append(
            {
                "hole": index,
                "bore_overlap_mm3": bore_overlap,
                "cavity_overlap_mm3": cavity_overlap,
            }
        )

    adapter_rows: list[dict[str, float]] = []
    for tube_wall_t in design.adapter_tube_wall_variants:
        key = f"{tube_wall_t:g}mm_wall"
        adapter = geometry["adapters"][key]
        if not adapter.is_valid:
            raise ValueError(f"Invalid tube adapter for {tube_wall_t:g} mm wall")
        adapter_rows.append(
            {
                "mating_tube_wall_mm": tube_wall_t,
                "mating_tube_id_mm": design.main_bore_d,
                "mating_tube_od_mm": design.mating_tube_outer_d(tube_wall_t),
                "socket_id_mm": 2.0 * design.adapter_socket_inner_r(tube_wall_t),
                "diametral_clearance_mm": (
                    design.adapter_socket_clearance_diametral
                ),
                "socket_depth_mm": design.adapter_socket_depth,
            }
        )

    return {
        "main_airway": {
            "nominal_diameter_mm": design.main_bore_d,
            "minimum_diameter_mm": design.main_bore_d,
            "material_intrusion_mm3": material_in_bore,
            "connected_adapter_assembly_intrusion_mm3": (
                connected_material_in_bore
            ),
            "continuous_circular_bore": True,
        },
        "common_annular_cavity": {
            "connected_bulk_solid_count": len(cavity.solids()),
            "gross_volume_cm3": geometry["cavity_volume_cm3"],
            "nominal_air_domain_connected_solid_count": nominal_air_solid_count,
            "pilot_air_domain_connected_solid_count": pilot_air_solid_count,
            "qualification": (
                "Equivalent to identical parallel chambers at the lumped target; "
                "independent staggered tuning would require sealed dividers."
            ),
        },
        "rail_attachment": {
            "designed_radial_overlap_mm": design.rail_core_overlap,
            "overlap_volume_each_mm3": rail_core_overlap_volume,
            "volumetric_attachment": True,
        },
        "neck_connections": connection_rows,
        "viewer_seam": {
            "physical_joint": False,
            "explanation": (
                "The vertical line on a cylindrical STEP face is its parametric "
                "surface seam, not a split or gap."
            ),
            "rail_angle_offset_from_cylinder_seam_deg": (
                design.rail_angle_offset_deg
            ),
        },
        "tube_socket_adapters": adapter_rows,
        "assembly_interfaces": {
            "bottom": (
                "Bucket rim seats on the integral floor and is centered by the "
                "printed lower lip; use a thin removable face seal while tuning."
            ),
            "top": (
                "Integral bucket skirt slips over the continuous core; use a "
                "circumferential gasket or removable sealant in the 0.20 mm gap."
            ),
            "pressure_decay_target_ms": 50.0,
        },
        "print_orientation": {
            "inner_core": "integral floor on build plate; axis vertical",
            "outer_bucket": (
                "invert for printing so the integrated annular cap is on the bed "
                "and the open rim grows upward"
            ),
            "tube_socket_adapter": (
                "print two identical copies flat on the annular plate, socket up; "
                "flip one during assembly"
            ),
            "supports_required": False,
            "horizontal_features": (
                "0.90 mm diamond pilot tunnels only; drill round from outside "
                "with the bucket removed"
            ),
            "bore_cleanup": (
                "Remove only proud breakthrough burrs with fine rolled sandpaper; "
                "do not intentionally countersink the airway-side openings."
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
        valid = [solid.is_valid for solid in imported_solids]
        match = len(source_solids) == len(imported_solids)
        results[filename] = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": match,
            "all_imported_solids_valid": all(valid),
        }
        if not match or not all(valid):
            raise ValueError(f"STEP round-trip failed for {filename}")
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-frequency", type=float)
    parser.add_argument("--holes-per-rail", type=int)
    parser.add_argument("--hole-pitch", type=float)
    parser.add_argument("--pilot-span", type=float)
    parser.add_argument("--rail-count", type=int)
    parser.add_argument("--rail-angle-offset", type=float)
    parser.add_argument("--ream-diameter", type=float)
    parser.add_argument("--neck-length", type=float)
    parser.add_argument("--length", type=float)
    parser.add_argument("--outer-diameter", type=float)
    parser.add_argument("--assumed-q", type=float)
    return parser.parse_args()


def _design_from_args(args: argparse.Namespace) -> Design:
    replacements: dict[str, Any] = {}
    mapping = {
        "target_frequency": "target_absorber_frequency_hz",
        "holes_per_rail": "holes_per_rail",
        "hole_pitch": "hole_row_pitch",
        "pilot_span": "pilot_diamond_span",
        "rail_count": "rail_count",
        "rail_angle_offset": "rail_angle_offset_deg",
        "ream_diameter": "nominal_ream_diameter_override",
        "neck_length": "neck_physical_length",
        "length": "overall_length",
        "outer_diameter": "maximum_outer_d",
        "assumed_q": "assumed_absorber_q_for_tmm",
    }
    for argument, field in mapping.items():
        value = getattr(args, argument)
        if value is not None:
            replacements[field] = value
    return replace(D, **replacements) if replacements else D


def main() -> None:
    design = _design_from_args(_parse_args())
    _validate_design(design)
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_geometry(design)
    nominal_diameter = geometry["nominal_ream_diameter_mm"]
    cavity_volume = geometry["cavity_volume_cm3"]
    properties = _resonator_properties(
        diameter_mm=nominal_diameter,
        volume_cm3=cavity_volume,
        design=design,
    )

    tmm_design, tmm_geometry = _equivalent_tmm_inputs(
        diameter_mm=nominal_diameter,
        volume_cm3=cavity_volume,
        design=design,
    )
    acoustic_model, response_rows = prior._run_acoustic_model(
        tmm_geometry,
        tmm_design,
    )
    geometry_checks = _geometry_diagnostics(geometry, design)

    placement_rows: list[dict[str, Any]] = []
    bare_modes = acoustic_model["bare_mode_peaks_hz"][:3]
    for fraction in (1.0 / 3.0, 0.5, 2.0 / 3.0):
        local_design = replace(
            tmm_design,
            collar_center_path_mm=(
                design.main_port_physical_length_mm * fraction
            ),
        )
        pressure_by_mode: dict[str, float] = {}
        for mode_index, mode_frequency in enumerate(bare_modes, start=1):
            coupling = prior._modal_pressure_coupling(
                mode_frequency,
                {},
                local_design,
            )
            pressure_by_mode[f"mode_{mode_index}_normalized_pressure"] = (
                coupling["normalized_pressure_at_collar"]
            )
        placement_rows.append(
            {
                "path_fraction": fraction,
                "path_mm_from_inlet": (
                    design.main_port_physical_length_mm * fraction
                ),
                **pressure_by_mode,
            }
        )
    one_third = placement_rows[0]
    two_thirds = placement_rows[2]
    split_first_mode_relative_coupling = 0.5 * (
        one_third["mode_1_normalized_pressure"] ** 2
        + two_thirds["mode_1_normalized_pressure"] ** 2
    )

    exports = {
        "port_absorber_bucket_inner_core_pilots.step": geometry["core_pilot"],
        "port_absorber_bucket_inner_core_nominal_reamed.step": geometry["core_reamed"],
        "port_absorber_bucket_outer_bucket.step": geometry["bucket"],
        "port_absorber_bucket_socket_adapter_40id_46od.step": geometry[
            "adapters"
        ]["3mm_wall"],
        "port_absorber_bucket_socket_adapter_40id_50od.step": geometry[
            "adapters"
        ]["5mm_wall"],
        "port_absorber_bucket_assembly_pilots.step": geometry["assembly_pilot"],
        "port_absorber_bucket_assembly_nominal_reamed.step": geometry[
            "assembly_nominal"
        ],
        "port_absorber_bucket_cutaway.step": geometry["cutaway"],
        "port_absorber_bucket_exploded.step": geometry["exploded"],
        "port_absorber_bucket_connected_46od_tubes.step": geometry[
            "connected_assemblies"
        ]["3mm_wall"],
        "port_absorber_bucket_connected_50od_tubes.step": geometry[
            "connected_assemblies"
        ]["5mm_wall"],
        "port_absorber_bucket_print_layout.step": geometry["print_layout"],
        "port_absorber_bucket_air_domain_nominal.step": geometry["nominal_air_domain"],
    }
    roundtrip = _step_roundtrip(exports)

    with (OUT / "modeled_response.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(response_rows[0]))
        writer.writeheader()
        writer.writerows(response_rows)

    calculated_frequency = _helmholtz_frequency_hz(
        diameter_mm=nominal_diameter,
        hole_count=design.total_holes,
        volume_cm3=cavity_volume,
        design=design,
    )
    diagnostics = {
        "name": design.name,
        "status": (
            "isolated two-part bucket absorber with two identical end adapters; "
            "production port remains unchanged"
        ),
        "design_inputs": asdict(design),
        "architecture": {
            "inner_core": (
                "continuous bore, host-thickness wall, integral bottom floor, "
                "lower locating lip, four vertical drill rails"
            ),
            "outer_bucket": (
                "outer wall plus integral top collar and inner sealing skirt; "
                "printed inverted with cap on build plate"
            ),
            "tube_interfaces": (
                "two identical separately printed annular socket adapters; one "
                "is flipped at assembly, preserving support-free printing and "
                "the full 40 mm bore"
            ),
            "common_cavity_reason": (
                "avoids unreliable dry seals along removable divider ribs; at one "
                "target it is equivalent to identical parallel chambers"
            ),
            "damping_material": "none; resistance is developed by hole geometry",
        },
        "nominal_absorber": {
            "target_frequency_hz": design.target_absorber_frequency_hz,
            "calculated_frequency_hz": calculated_frequency,
            "gross_common_cavity_volume_cm3": cavity_volume,
            "pilot_diamond_span_mm": design.pilot_diamond_span,
            "solved_nominal_ream_diameter_mm": nominal_diameter,
            "hole_rows": design.rail_count,
            "holes_per_row": design.holes_per_rail,
            "hole_z_positions_mm": design.hole_z_positions,
            "hole_band_length_mm": design.hole_band_length,
            "physical_neck_length_mm": design.neck_physical_length,
            "nominal_end_correction_beta_times_d": design.end_correction_beta,
            "total_open_area_percent_of_main_port": (
                properties["total_neck_area_mm2"]
                / design.main_port_area_mm2
                * 100.0
            ),
            **properties,
        },
        "geometry_validation": geometry_checks,
        "reaming_plan": {
            "direction": (
                "start below target with undersized round holes; enlarge all active "
                "holes in equal calibrated steps to raise resonance"
            ),
            "predicted_frequency_by_bit": _frequency_ladder(
                nominal_diameter=nominal_diameter,
                volume_cm3=cavity_volume,
                design=design,
            ),
            "reversible_reduction": (
                "with the bucket removed, plug selected openings from the chamber "
                "side before reassembly"
            ),
        },
        "geometry_only_resistance_study": {
            "families_at_same_target": _hole_family_rows(cavity_volume, design),
            "qualification": (
                "Steady Poiseuille values compare geometric trends only. Actual "
                "oscillatory resistance and Q depend on edge finish, FDM texture, "
                "level, and end losses and must be measured."
            ),
        },
        "acoustic_model": acoustic_model,
        "acoustic_model_qualification": (
            "The 24-hole array and common cavity are represented by an exact "
            "lumped area/mass equivalent single neck. Q=1 is an assumed response "
            "case, not a claim that the first drilled geometry will measure Q=1."
        ),
        "placement": {
            "lumped_coupling_path_mm_from_inlet": design.coupling_path_mm,
            "hole_band_is_distributed_mm": design.hole_band_length,
            "pressure_coupling_by_path_fraction": placement_rows,
            "two_half_modules_at_one_third_and_two_thirds": {
                "first_mode_relative_pressure_squared_coupling_for_same_total_volume": (
                    split_first_mode_relative_coupling
                ),
                "interpretation": (
                    "Approximately 75 percent of the ideal centered first-mode "
                    "coupling for the same total absorber volume, while both "
                    "locations also have strong second-mode pressure."
                ),
            },
            "qualification": (
                "This long architecture coupon is not yet integrated into the "
                "crowded external tower; final hole-band position follows the "
                "measured port-mode pressure region."
            ),
        },
        "step_roundtrip": roundtrip,
    }
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=False) + "\n"
    )

    for source, viewer_name in (
        ("port_absorber_bucket_connected_46od_tubes.step", "viewer"),
        ("port_absorber_bucket_cutaway.step", "cutaway_viewer"),
        ("port_absorber_bucket_exploded.step", "exploded_viewer"),
        ("port_absorber_bucket_print_layout.step", "print_layout_viewer"),
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

    print(f"Inner core: {OUT / 'port_absorber_bucket_inner_core_pilots.step'}")
    print(f"Outer bucket: {OUT / 'port_absorber_bucket_outer_bucket.step'}")
    print(f"Assembly: {OUT / 'port_absorber_bucket_connected_46od_tubes.step'}")
    print(f"Cutaway: {OUT / 'port_absorber_bucket_cutaway.step'}")
    print(f"Diagnostics: {OUT / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
