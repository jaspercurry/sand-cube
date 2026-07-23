"""Generate an isolated Helmholtz-absorber collar for the long round port.

The collar is a short straight coupon matching the external 5 mm-wall tower.
Four sealed annular-sector chambers open into the unchanged circular airway
through flush radial necks.  The experiment deliberately remains separate
from the current enclosure and port generators.

All CAD dimensions are millimetres.  Acoustic calculations use SI units.
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

from build123d import (
    Align,
    Box,
    CenterOf,
    Compound,
    Cylinder,
    Part,
    Pos,
    Rot,
    Unit,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_collar"


@dataclass(frozen=True)
class Design:
    name: str = "sand_cube_190x210_external_port_absorber_collar_v1"

    # Host port and enclosure values copied from the isolated round-port study.
    main_bore_d: float = 39.242833740697165
    existing_tube_wall_t: float = 5.0
    main_port_area_mm2: float = 1209.5131716320702
    main_port_physical_length_mm: float = 491.36883778918025
    reported_lf_effective_length_mm: float = 518.5403834157696
    net_box_volume_l: float = 4.570116862348586
    bass_reflex_tuning_hz: float = 39.0

    # Physical flare model used by the distributed calculation.
    inlet_flare_length_mm: float = 15.0
    inlet_mouth_d: float = 44.474711915874174
    throat_d: float = 39.242833740697165
    outlet_flare_length_mm: float = 25.0
    outlet_mouth_d: float = 58.58327406350724
    outlet_radiation_end_factor: float = 0.6133

    # The collar occupies z=95..125 mm on the external straight tower.  The
    # corresponding physical path coordinate is measured from the inlet mouth.
    collar_center_path_mm: float = 358.2556340705263
    collar_center_global_z_mm: float = 110.0

    # Printable collar geometry.  The 8 mm local liner thickens outward only;
    # the 39.243 mm airway remains unchanged.
    chamber_count: int = 4
    collar_axial_length: float = 30.0
    maximum_outer_d: float = 100.0
    outer_wall_t: float = 3.0
    bottom_wall_t: float = 3.0
    lid_t: float = 3.0
    divider_t: float = 2.4
    neck_physical_length: float = 8.0
    damping_allowance_cm3_per_chamber: float = 0.25
    print_clearance: float = 0.20

    # Each chamber is independently tunable.  Equal defaults maximize the
    # first-mode attenuation; CLI multipliers support later measured staggering.
    target_absorber_frequency_hz: float = 345.0
    target_frequency_multipliers: tuple[float, ...] = (1.0, 1.0, 1.0, 1.0)
    neck_diameter_override_mm: float | None = None
    absorber_q: float = 1.0

    # Nominal small circular flush-aperture correction:
    # Leff = t + 0.85r + 0.85r = t + 0.85d.
    duct_side_end_correction_r: float = 0.85
    cavity_side_end_correction_r: float = 0.85
    end_correction_beta_low: float = 0.70
    end_correction_beta_high: float = 1.00

    speed_of_sound_m_s: float = 343.0
    air_density_kg_m3: float = 1.204
    tmm_segments: int = 220

    @property
    def bore_r(self) -> float:
        return self.main_bore_d / 2.0

    @property
    def collar_outer_r(self) -> float:
        return self.maximum_outer_d / 2.0

    @property
    def cavity_inner_r(self) -> float:
        return self.bore_r + self.neck_physical_length

    @property
    def cavity_outer_r(self) -> float:
        return self.collar_outer_r - self.outer_wall_t

    @property
    def body_height(self) -> float:
        return self.collar_axial_length - self.lid_t

    @property
    def cavity_height(self) -> float:
        return self.body_height - self.bottom_wall_t

    @property
    def target_frequencies_hz(self) -> tuple[float, ...]:
        if len(self.target_frequency_multipliers) != self.chamber_count:
            raise ValueError(
                "target_frequency_multipliers must match chamber_count"
            )
        return tuple(
            self.target_absorber_frequency_hz * multiplier
            for multiplier in self.target_frequency_multipliers
        )


D = Design()


def _validate_design(design: Design) -> None:
    if design.chamber_count < 2:
        raise ValueError("At least two chambers are required")
    if design.neck_physical_length < design.existing_tube_wall_t:
        raise ValueError(
            "The local neck/liner may thicken outward but cannot be thinner than "
            "the existing host tube wall in this support-free coupon"
        )
    if design.cavity_inner_r >= design.cavity_outer_r:
        raise ValueError("No radial cavity depth remains")
    if design.cavity_height <= 0.0:
        raise ValueError("No axial cavity height remains")
    if design.absorber_q <= 0.0:
        raise ValueError("Absorber Q must be positive")
    if design.print_clearance < 0.0:
        raise ValueError("Print clearance cannot be negative")
    _ = design.target_frequencies_hz


def _shell(outer_r: float, inner_r: float, height: float, z: float = 0.0) -> Any:
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    outer = Pos(0, 0, z) * Cylinder(outer_r, height, align=alignment)
    inner = Pos(0, 0, z - 0.01) * Cylinder(
        inner_r,
        height + 0.02,
        align=alignment,
    )
    return (outer - inner).clean().fix()


def _radial_divider(angle_deg: float, design: Design) -> Any:
    radial_length = design.cavity_outer_r - design.cavity_inner_r + 2.0
    divider = Box(
        radial_length,
        design.divider_t,
        design.cavity_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    return (
        Rot(0, 0, angle_deg)
        * Pos(design.cavity_inner_r - 1.0, 0, design.bottom_wall_t)
        * divider
    )


def _cavity_voids(design: Design) -> tuple[Any, list[Any]]:
    cavity_ring: Any = _shell(
        design.cavity_outer_r,
        design.cavity_inner_r,
        design.cavity_height,
        design.bottom_wall_t,
    )
    for index in range(design.chamber_count):
        cavity_ring = (
            cavity_ring - _radial_divider(360.0 * index / design.chamber_count, design)
        ).clean().fix()

    solids = list(cavity_ring.solids())
    solids.sort(
        key=lambda solid: (
            math.atan2(
                solid.center(CenterOf.MASS).Y,
                solid.center(CenterOf.MASS).X,
            )
            % (2.0 * math.pi)
        )
    )
    if len(solids) != design.chamber_count:
        raise ValueError(
            f"Expected {design.chamber_count} isolated cavities, got {len(solids)}"
        )
    return cavity_ring, solids


def _effective_neck_length_mm(diameter_mm: float, design: Design) -> float:
    radius = diameter_mm / 2.0
    return design.neck_physical_length + radius * (
        design.duct_side_end_correction_r
        + design.cavity_side_end_correction_r
    )


def _helmholtz_frequency_hz(
    *,
    diameter_mm: float,
    volume_cm3: float,
    design: Design,
    beta: float | None = None,
    speed_of_sound_m_s: float | None = None,
) -> float:
    area_m2 = math.pi * (diameter_mm / 1000.0) ** 2 / 4.0
    if beta is None:
        length_mm = _effective_neck_length_mm(diameter_mm, design)
    else:
        length_mm = design.neck_physical_length + beta * diameter_mm
    c = speed_of_sound_m_s or design.speed_of_sound_m_s
    return c / (2.0 * math.pi) * math.sqrt(
        area_m2 / ((volume_cm3 / 1_000_000.0) * (length_mm / 1000.0))
    )


def _solve_neck_diameter_mm(
    target_hz: float, volume_cm3: float, design: Design
) -> float:
    low = 0.5
    high = min(15.0, design.main_bore_d / 2.5)
    if _helmholtz_frequency_hz(
        diameter_mm=low, volume_cm3=volume_cm3, design=design
    ) > target_hz:
        raise ValueError("Target is below the available neck-diameter search range")
    if _helmholtz_frequency_hz(
        diameter_mm=high, volume_cm3=volume_cm3, design=design
    ) < target_hz:
        raise ValueError("Target is above the available neck-diameter search range")
    for _ in range(80):
        middle = (low + high) / 2.0
        result = _helmholtz_frequency_hz(
            diameter_mm=middle,
            volume_cm3=volume_cm3,
            design=design,
        )
        if result < target_hz:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _radial_cylinder(
    *,
    angle_deg: float,
    radial_start: float,
    length: float,
    radius: float,
    z: float,
) -> Any:
    tool = Cylinder(
        radius,
        length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return (
        Rot(0, 0, angle_deg)
        * Pos(radial_start, 0, z)
        * Rot(0, 90, 0)
        * tool
    )


def _neck_tools(neck_diameters_mm: list[float], design: Design) -> list[Any]:
    tools: list[Any] = []
    radial_overlap = 0.15
    for index, diameter in enumerate(neck_diameters_mm):
        angle = 360.0 * (index + 0.5) / design.chamber_count
        tools.append(
            _radial_cylinder(
                angle_deg=angle,
                radial_start=design.bore_r - radial_overlap,
                length=design.neck_physical_length + 2.0 * radial_overlap,
                radius=diameter / 2.0,
                z=design.collar_axial_length / 2.0,
            )
        )
    return tools


def _build_geometry(design: Design) -> dict[str, Any]:
    cavity_voids, cavity_solids = _cavity_voids(design)
    gross_volumes_cm3 = [solid.volume / 1000.0 for solid in cavity_solids]
    acoustic_volumes_cm3 = [
        volume - design.damping_allowance_cm3_per_chamber
        for volume in gross_volumes_cm3
    ]
    if min(acoustic_volumes_cm3) <= 0.0:
        raise ValueError("Damping allowance consumes the cavity volume")

    if design.neck_diameter_override_mm is None:
        diameters = [
            _solve_neck_diameter_mm(target, volume, design)
            for target, volume in zip(
                design.target_frequencies_hz,
                acoustic_volumes_cm3,
                strict=True,
            )
        ]
    else:
        diameters = [design.neck_diameter_override_mm] * design.chamber_count

    necks = _neck_tools(diameters, design)
    axial_alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    body: Any = Cylinder(
        design.collar_outer_r,
        design.body_height,
        align=axial_alignment,
    )
    bore_cut = Pos(0, 0, -0.05) * Cylinder(
        design.bore_r,
        design.collar_axial_length + 0.1,
        align=axial_alignment,
    )
    body = (body - bore_cut - cavity_voids).clean().fix()
    for neck in necks:
        body = (body - neck).clean().fix()

    lid = Pos(0, 0, design.body_height) * _shell(
        design.collar_outer_r,
        design.bore_r,
        design.lid_t,
    )
    body = Part(body)
    lid = Part(lid)
    if not body.is_valid or not lid.is_valid:
        raise ValueError("Body or lid is invalid")

    airway = Cylinder(
        design.bore_r,
        design.collar_axial_length,
        align=axial_alignment,
    )
    air_domain: Any = airway
    for cavity in cavity_solids:
        air_domain = (air_domain + cavity).clean().fix()
    for neck in necks:
        air_domain = (air_domain + neck).clean().fix()

    assembly = Compound(children=[body, lid])
    fused_housing = (body + lid).clean().fix()
    cutaway_keep = Rot(0, 0, 45) * Box(
        2.2 * design.collar_outer_r,
        1.1 * design.collar_outer_r,
        design.collar_axial_length,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    cutaway = (fused_housing & cutaway_keep).clean().fix()

    return {
        "body": body,
        "lid": lid,
        "assembly": assembly,
        "fused_housing": fused_housing,
        "cutaway": cutaway,
        "airway": airway,
        "air_domain": air_domain,
        "cavity_voids": cavity_voids,
        "cavity_solids": cavity_solids,
        "neck_tools": necks,
        "gross_volumes_cm3": gross_volumes_cm3,
        "acoustic_volumes_cm3": acoustic_volumes_cm3,
        "neck_diameters_mm": diameters,
    }


Matrix = tuple[tuple[complex, complex], tuple[complex, complex]]


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _port_radius_m(x_m: float, design: Design) -> float:
    inlet_length = design.inlet_flare_length_mm / 1000.0
    outlet_length = design.outlet_flare_length_mm / 1000.0
    total_length = design.main_port_physical_length_mm / 1000.0
    inlet_r = design.inlet_mouth_d / 2000.0
    throat_r = design.throat_d / 2000.0
    outlet_r = design.outlet_mouth_d / 2000.0
    outlet_start = total_length - outlet_length
    if x_m < inlet_length:
        return inlet_r + (throat_r - inlet_r) * x_m / inlet_length
    if x_m <= outlet_start:
        return throat_r
    return throat_r + (outlet_r - throat_r) * (
        (x_m - outlet_start) / outlet_length
    )


def _duct_matrix(
    frequency_hz: float,
    start_m: float,
    end_m: float,
    design: Design,
) -> Matrix:
    if end_m <= start_m:
        return ((1.0 + 0j, 0j), (0j, 1.0 + 0j))
    total_length = design.main_port_physical_length_mm / 1000.0
    segments = max(
        8,
        round(design.tmm_segments * (end_m - start_m) / total_length),
    )
    dx = (end_m - start_m) / segments
    k = 2.0 * math.pi * frequency_hz / design.speed_of_sound_m_s
    matrix: Matrix = ((1.0 + 0j, 0j), (0j, 1.0 + 0j))
    for index in range(segments):
        x = start_m + (index + 0.5) * dx
        area = math.pi * _port_radius_m(x, design) ** 2
        characteristic_impedance = (
            design.air_density_kg_m3 * design.speed_of_sound_m_s / area
        )
        phase = k * dx
        segment: Matrix = (
            (
                complex(math.cos(phase)),
                1j * characteristic_impedance * math.sin(phase),
            ),
            (
                1j * math.sin(phase) / characteristic_impedance,
                complex(math.cos(phase)),
            ),
        )
        matrix = _matrix_multiply(matrix, segment)
    return matrix


def _outlet_radiation_impedance(frequency_hz: float, design: Design) -> complex:
    radius = design.outlet_mouth_d / 2000.0
    area = math.pi * radius**2
    characteristic_impedance = (
        design.air_density_kg_m3 * design.speed_of_sound_m_s / area
    )
    ka = 2.0 * math.pi * frequency_hz * radius / design.speed_of_sound_m_s
    return characteristic_impedance * (
        0.5 * ka**2 + 1j * design.outlet_radiation_end_factor * ka
    )


def _absorber_properties(
    *,
    diameter_mm: float,
    volume_cm3: float,
    target_frequency_hz: float,
    design: Design,
) -> dict[str, float]:
    area_m2 = math.pi * (diameter_mm / 1000.0) ** 2 / 4.0
    effective_length_m = _effective_neck_length_mm(diameter_mm, design) / 1000.0
    acoustic_mass = design.air_density_kg_m3 * effective_length_m / area_m2
    acoustic_compliance = (volume_cm3 / 1_000_000.0) / (
        design.air_density_kg_m3 * design.speed_of_sound_m_s**2
    )
    resistance = (
        2.0
        * math.pi
        * target_frequency_hz
        * acoustic_mass
        / design.absorber_q
    )
    return {
        "neck_area_mm2": area_m2 * 1_000_000.0,
        "effective_neck_length_mm": effective_length_m * 1000.0,
        "acoustic_mass_pa_s2_per_m3": acoustic_mass,
        "acoustic_compliance_m5_per_n": acoustic_compliance,
        "required_resistance_pa_s_per_m3": resistance,
    }


def _absorber_admittance(
    frequency_hz: float,
    geometry: dict[str, Any],
    design: Design,
) -> complex:
    omega = 2.0 * math.pi * frequency_hz
    total = 0j
    for diameter, volume, target in zip(
        geometry["neck_diameters_mm"],
        geometry["acoustic_volumes_cm3"],
        design.target_frequencies_hz,
        strict=True,
    ):
        properties = _absorber_properties(
            diameter_mm=diameter,
            volume_cm3=volume,
            target_frequency_hz=target,
            design=design,
        )
        mass = properties["acoustic_mass_pa_s2_per_m3"]
        compliance = properties["acoustic_compliance_m5_per_n"]
        resistance = properties["required_resistance_pa_s_per_m3"]
        impedance = resistance + 1j * (
            omega * mass - 1.0 / (omega * compliance)
        )
        total += 1.0 / impedance
    return total


def _port_matrix(
    frequency_hz: float,
    geometry: dict[str, Any],
    design: Design,
    *,
    with_absorber: bool,
) -> Matrix:
    total_length = design.main_port_physical_length_mm / 1000.0
    collar_x = design.collar_center_path_mm / 1000.0
    before = _duct_matrix(frequency_hz, 0.0, collar_x, design)
    after = _duct_matrix(frequency_hz, collar_x, total_length, design)
    if not with_absorber:
        return _matrix_multiply(before, after)
    shunt: Matrix = (
        (1.0 + 0j, 0j),
        (_absorber_admittance(frequency_hz, geometry, design), 1.0 + 0j),
    )
    return _matrix_multiply(_matrix_multiply(before, shunt), after)


def _pressure_driven_outlet_transfer(
    frequency_hz: float,
    geometry: dict[str, Any],
    design: Design,
    *,
    with_absorber: bool,
) -> float:
    matrix = _port_matrix(
        frequency_hz,
        geometry,
        design,
        with_absorber=with_absorber,
    )
    radiation = _outlet_radiation_impedance(frequency_hz, design)
    denominator = matrix[0][0] * radiation + matrix[0][1]
    return abs(1.0 / denominator)


def _box_driven_outlet_transfer(
    frequency_hz: float,
    geometry: dict[str, Any],
    design: Design,
    *,
    with_absorber: bool,
) -> float:
    matrix = _port_matrix(
        frequency_hz,
        geometry,
        design,
        with_absorber=with_absorber,
    )
    radiation = _outlet_radiation_impedance(frequency_hz, design)
    a, b = matrix[0]
    c, d = matrix[1]
    input_impedance = (a * radiation + b) / (c * radiation + d)
    box_compliance = (design.net_box_volume_l / 1000.0) / (
        design.air_density_kg_m3 * design.speed_of_sound_m_s**2
    )
    box_impedance = 1.0 / (1j * 2.0 * math.pi * frequency_hz * box_compliance)
    inlet_pressure = 1.0 / (1.0 / input_impedance + 1.0 / box_impedance)
    return abs(inlet_pressure / (a * radiation + b))


def _local_maxima(rows: list[dict[str, float]], key: str) -> list[dict[str, float]]:
    return [
        rows[index]
        for index in range(1, len(rows) - 1)
        if rows[index][key] > rows[index - 1][key]
        and rows[index][key] > rows[index + 1][key]
    ]


def _modal_pressure_coupling(
    mode_frequency_hz: float,
    geometry: dict[str, Any],
    design: Design,
) -> dict[str, float]:
    total_length = design.main_port_physical_length_mm / 1000.0
    radiation = _outlet_radiation_impedance(mode_frequency_hz, design)
    complete = _port_matrix(
        mode_frequency_hz,
        geometry,
        design,
        with_absorber=False,
    )
    outlet_velocity = 1.0 / (complete[0][0] * radiation + complete[0][1])
    samples: list[tuple[float, float]] = []
    for index in range(201):
        x = total_length * index / 200.0
        downstream = _duct_matrix(mode_frequency_hz, x, total_length, design)
        pressure = abs(
            (downstream[0][0] * radiation + downstream[0][1])
            * outlet_velocity
        )
        samples.append((x, pressure))
    maximum = max(value for _, value in samples)
    collar_x = design.collar_center_path_mm / 1000.0
    nearest = min(samples, key=lambda row: abs(row[0] - collar_x))
    maximum_row = max(samples, key=lambda row: row[1])
    return {
        "collar_path_fraction": collar_x / total_length,
        "normalized_pressure_at_collar": nearest[1] / maximum,
        "pressure_antinode_path_mm": maximum_row[0] * 1000.0,
    }


def _run_acoustic_model(
    geometry: dict[str, Any], design: Design
) -> tuple[dict[str, Any], list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    frequency = 200.0
    while frequency <= 1500.0001:
        bare = _pressure_driven_outlet_transfer(
            frequency, geometry, design, with_absorber=False
        )
        treated = _pressure_driven_outlet_transfer(
            frequency, geometry, design, with_absorber=True
        )
        rows.append(
            {
                "frequency_hz": frequency,
                "bare_outlet_transfer": bare,
                "treated_outlet_transfer": treated,
                "treated_minus_bare_db": 20.0 * math.log10(treated / bare),
            }
        )
        frequency += 0.5

    bare_peaks = _local_maxima(rows, "bare_outlet_transfer")[:4]
    treated_peaks = _local_maxima(rows, "treated_outlet_transfer")[:4]
    peak_summary: list[dict[str, Any]] = []
    for mode_index, peak in enumerate(bare_peaks, start=1):
        frequency_hz = peak["frequency_hz"]
        treated = _pressure_driven_outlet_transfer(
            frequency_hz, geometry, design, with_absorber=True
        )
        peak_summary.append(
            {
                "mode": mode_index,
                "bare_peak_frequency_hz": frequency_hz,
                "ideal_treated_minus_bare_db_at_bare_peak": 20.0
                * math.log10(treated / peak["bare_outlet_transfer"]),
                "placement": _modal_pressure_coupling(
                    frequency_hz, geometry, design
                ),
            }
        )

    low_rows: list[dict[str, float]] = []
    frequency = 32.0
    while frequency <= 48.0001:
        low_rows.append(
            {
                "frequency_hz": frequency,
                "bare": _box_driven_outlet_transfer(
                    frequency, geometry, design, with_absorber=False
                ),
                "treated": _box_driven_outlet_transfer(
                    frequency, geometry, design, with_absorber=True
                ),
            }
        )
        frequency += 0.01
    bare_lf_peak = max(low_rows, key=lambda row: row["bare"])
    treated_lf_peak = max(low_rows, key=lambda row: row["treated"])

    model = {
        "assumptions": [
            "lossless plane-wave cylindrical slices with linear-radius flares",
            "low-ka outlet radiation load; bends represented by centerline length only",
            "ideal internal pressure drive for midrange port leakage",
            "enclosure compliance included only in the low-frequency comparison",
            "driver electro-mechanics, thermoviscous duct loss, bend scattering, and "
            "cabinet radiation are excluded",
        ],
        "bare_mode_peaks_hz": [row["frequency_hz"] for row in bare_peaks],
        "treated_mode_peaks_hz": [row["frequency_hz"] for row in treated_peaks],
        "mode_summary": peak_summary,
        "bass_reflex_comparison": {
            "bare_peak_hz": bare_lf_peak["frequency_hz"],
            "treated_peak_hz": treated_lf_peak["frequency_hz"],
            "modeled_shift_hz": (
                treated_lf_peak["frequency_hz"] - bare_lf_peak["frequency_hz"]
            ),
            "qualification": (
                "Relative TMM result only; verify tuning and 39 Hz output on the "
                "printed system. External placement displaces no cabinet air."
            ),
        },
    }
    return model, rows


def _sensitivity_rows(
    diameter_mm: float,
    volume_cm3: float,
    design: Design,
) -> list[dict[str, Any]]:
    cases = [
        ("neck_diameter_mm", -0.15, {"diameter_mm": diameter_mm - 0.15}),
        ("neck_diameter_mm", 0.15, {"diameter_mm": diameter_mm + 0.15}),
        ("physical_neck_length_mm", -0.20, {"neck_delta": -0.20}),
        ("physical_neck_length_mm", 0.20, {"neck_delta": 0.20}),
        ("cavity_volume_percent", -5.0, {"volume_cm3": volume_cm3 * 0.95}),
        ("cavity_volume_percent", 5.0, {"volume_cm3": volume_cm3 * 1.05}),
        ("speed_of_sound_m_s", 340.3, {"speed": 340.3}),
        ("speed_of_sound_m_s", 349.0, {"speed": 349.0}),
        (
            "end_correction_beta",
            design.end_correction_beta_low,
            {"beta": design.end_correction_beta_low},
        ),
        (
            "end_correction_beta",
            design.end_correction_beta_high,
            {"beta": design.end_correction_beta_high},
        ),
    ]
    rows: list[dict[str, Any]] = []
    for parameter, variation, values in cases:
        local_design = design
        if "neck_delta" in values:
            local_design = replace(
                design,
                neck_physical_length=(
                    design.neck_physical_length + values["neck_delta"]
                ),
            )
        frequency = _helmholtz_frequency_hz(
            diameter_mm=values.get("diameter_mm", diameter_mm),
            volume_cm3=values.get("volume_cm3", volume_cm3),
            design=local_design,
            beta=values.get("beta"),
            speed_of_sound_m_s=values.get("speed"),
        )
        rows.append(
            {
                "parameter": parameter,
                "variation": variation,
                "predicted_frequency_hz": frequency,
            }
        )
    return rows


def _intersection_volume(first: Any, second: Any) -> float:
    result = first & second
    return sum(solid.volume for solid in result.solids())


def _geometry_diagnostics(
    geometry: dict[str, Any], design: Design
) -> dict[str, Any]:
    cavity_solids = geometry["cavity_solids"]
    necks = geometry["neck_tools"]
    airway = geometry["airway"]
    housing = geometry["fused_housing"]

    intended_connections: list[dict[str, Any]] = []
    for index, neck in enumerate(necks):
        cavity_intersections = [
            _intersection_volume(neck, cavity) for cavity in cavity_solids
        ]
        intended_connections.append(
            {
                "chamber": index + 1,
                "neck_to_bore_overlap_mm3": _intersection_volume(neck, airway),
                "neck_to_own_cavity_overlap_mm3": cavity_intersections[index],
                "neck_to_other_cavities_overlap_mm3": sum(cavity_intersections)
                - cavity_intersections[index],
            }
        )

    material_in_bore = _intersection_volume(housing, airway)
    air_domain_solid_count = len(geometry["air_domain"].solids())
    if material_in_bore > 0.001:
        raise ValueError(f"Housing intrudes into bore by {material_in_bore:.6f} mm3")
    if air_domain_solid_count != 1:
        raise ValueError(
            f"Expected one connected intended air domain, got {air_domain_solid_count}"
        )
    for connection in intended_connections:
        if connection["neck_to_bore_overlap_mm3"] <= 0.0:
            raise ValueError("A neck does not reach the bore")
        if connection["neck_to_own_cavity_overlap_mm3"] <= 0.0:
            raise ValueError("A neck does not reach its chamber")
        if connection["neck_to_other_cavities_overlap_mm3"] > 0.001:
            raise ValueError("A neck crosses into a neighboring chamber")

    return {
        "main_airway": {
            "nominal_diameter_mm": design.main_bore_d,
            "minimum_diameter_mm": design.main_bore_d,
            "material_intrusion_mm3": material_in_bore,
            "continuous_circular_bore": True,
        },
        "cavities": {
            "isolated_before_intended_necks": len(cavity_solids)
            == design.chamber_count,
            "intended_air_domain_connected_solid_count": air_domain_solid_count,
            "gross_volumes_cm3": geometry["gross_volumes_cm3"],
            "acoustic_volumes_after_damping_allowance_cm3": geometry[
                "acoustic_volumes_cm3"
            ],
            "nominal_outer_wall_mm": design.outer_wall_t,
            "nominal_bottom_wall_mm": design.bottom_wall_t,
            "nominal_lid_wall_mm": design.lid_t,
            "nominal_divider_wall_mm": design.divider_t,
            "assembly_seal": (
                "Bond the complete outer, inner, and divider contact lines of the "
                "lid; pressure-decay test each chamber before use."
            ),
        },
        "neck_connections": intended_connections,
        "print_orientation": {
            "body": (
                "axis vertical, integral chamber floor on build plate, "
                "cavities open upward"
            ),
            "lid": "flat",
            "supports_required": False,
            "qualification": (
                "The radial round apertures are short horizontal bridges; calibrate "
                "or ream them to measured diameter."
            ),
        },
    }


def _step_roundtrip(exports: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for filename, shape in exports.items():
        export_step(shape, OUT / filename, unit=Unit.MM, write_pcurves=True)
        imported = import_step(OUT / filename)
        source_solids = list(shape.solids())
        imported_solids = list(imported.solids())
        valid = [solid.is_valid for solid in imported_solids]
        counts_match = len(source_solids) == len(imported_solids)
        results[filename] = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": counts_match,
            "all_imported_solids_valid": all(valid),
        }
        if not counts_match or not all(valid):
            raise ValueError(
                f"STEP round-trip failed for {filename}: "
                f"source={len(source_solids)}, imported={len(imported_solids)}, "
                f"valid={valid}"
            )
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-frequency", type=float)
    parser.add_argument("--target-multipliers", type=str)
    parser.add_argument("--neck-diameter", type=float)
    parser.add_argument("--chambers", type=int)
    parser.add_argument("--collar-length", type=float)
    parser.add_argument("--maximum-outer-diameter", type=float)
    parser.add_argument("--neck-length", type=float)
    parser.add_argument("--absorber-q", type=float)
    return parser.parse_args()


def _design_from_args(args: argparse.Namespace) -> Design:
    design = D
    replacements: dict[str, Any] = {}
    if args.target_frequency is not None:
        replacements["target_absorber_frequency_hz"] = args.target_frequency
    if args.neck_diameter is not None:
        replacements["neck_diameter_override_mm"] = args.neck_diameter
    if args.chambers is not None:
        replacements["chamber_count"] = args.chambers
    if args.collar_length is not None:
        replacements["collar_axial_length"] = args.collar_length
    if args.maximum_outer_diameter is not None:
        replacements["maximum_outer_d"] = args.maximum_outer_diameter
    if args.neck_length is not None:
        replacements["neck_physical_length"] = args.neck_length
    if args.absorber_q is not None:
        replacements["absorber_q"] = args.absorber_q
    if args.target_multipliers is not None:
        replacements["target_frequency_multipliers"] = tuple(
            float(value.strip())
            for value in args.target_multipliers.split(",")
            if value.strip()
        )
    elif args.chambers is not None:
        replacements["target_frequency_multipliers"] = (1.0,) * args.chambers
    if replacements:
        design = replace(design, **replacements)
    return design


def main() -> None:
    design = _design_from_args(_parse_args())
    _validate_design(design)
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_geometry(design)
    acoustic_model, response_rows = _run_acoustic_model(geometry, design)
    geometry_checks = _geometry_diagnostics(geometry, design)

    exports = {
        "port_absorber_collar_body.step": geometry["body"],
        "port_absorber_collar_lid.step": geometry["lid"],
        "port_absorber_collar_assembly.step": geometry["assembly"],
        "port_absorber_collar_cutaway.step": geometry["cutaway"],
        "port_absorber_collar_air_domain.step": geometry["air_domain"],
    }
    roundtrip = _step_roundtrip(exports)

    with (OUT / "modeled_response.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(response_rows[0]))
        writer.writeheader()
        writer.writerows(response_rows)

    chamber_rows: list[dict[str, Any]] = []
    for index, (diameter, gross_volume, volume, target) in enumerate(
        zip(
            geometry["neck_diameters_mm"],
            geometry["gross_volumes_cm3"],
            geometry["acoustic_volumes_cm3"],
            design.target_frequencies_hz,
            strict=True,
        ),
        start=1,
    ):
        properties = _absorber_properties(
            diameter_mm=diameter,
            volume_cm3=volume,
            target_frequency_hz=target,
            design=design,
        )
        chamber_rows.append(
            {
                "chamber": index,
                "target_frequency_hz": target,
                "gross_cavity_volume_cm3": gross_volume,
                "damping_allowance_cm3": (
                    design.damping_allowance_cm3_per_chamber
                ),
                "net_acoustic_cavity_volume_cm3": volume,
                "neck_diameter_mm": diameter,
                "physical_neck_length_mm": design.neck_physical_length,
                "duct_side_end_correction_mm": (
                    design.duct_side_end_correction_r * diameter / 2.0
                ),
                "cavity_side_end_correction_mm": (
                    design.cavity_side_end_correction_r * diameter / 2.0
                ),
                "calculated_resonance_hz": _helmholtz_frequency_hz(
                    diameter_mm=diameter,
                    volume_cm3=volume,
                    design=design,
                ),
                "quality_factor_target": design.absorber_q,
                **properties,
            }
        )

    nominal_diameter = geometry["neck_diameters_mm"][0]
    nominal_volume = geometry["acoustic_volumes_cm3"][0]
    leakage_compliance = nominal_volume / 1_000_000.0 / (
        design.air_density_kg_m3 * design.speed_of_sound_m_s**2
    )
    leakage_resistance_5pct = 20.0 / (
        2.0
        * math.pi
        * design.target_absorber_frequency_hz
        * leakage_compliance
    )
    diagnostics = {
        "name": design.name,
        "status": (
            "isolated removable four-sector Helmholtz collar; no production port "
            "geometry modified"
        ),
        "design_inputs": asdict(design),
        "project_port": {
            "physical_half_wave_estimates_hz": [
                mode
                * design.speed_of_sound_m_s
                / (2.0 * design.main_port_physical_length_mm / 1000.0)
                for mode in range(1, 5)
            ],
            "reported_lf_length_half_wave_estimates_hz": [
                mode
                * design.speed_of_sound_m_s
                / (2.0 * design.reported_lf_effective_length_mm / 1000.0)
                for mode in range(1, 5)
            ],
            "warning": (
                "The reported effective length is a 39 Hz inertance quantity, not "
                "a validated midrange phase length."
            ),
        },
        "recommended_architecture": {
            "initial_configuration": (
                "all chambers identical at the measured first mode"
            ),
            "why_not_staggered_yet": (
                "Q 0.75-1 is already broad; blind staggering gives up peak shunt "
                "admittance before the bare-port response is measured."
            ),
            "later_options": [
                "2+2 at approximately 0.97 and 1.03 times measured f1 if needed",
                (
                    "a smaller dedicated f2 chamber only if the measured second "
                    "mode matters"
                ),
            ],
        },
        "chambers": chamber_rows,
        "geometry_validation": geometry_checks,
        "acoustic_model": acoustic_model,
        "sensitivity": {
            "cases": _sensitivity_rows(nominal_diameter, nominal_volume, design),
            "end_correction_qualification": (
                "The nominal two-sided 0.85r correction is not validated for this "
                "curved finite duct and sector cavity; beta=0.70..1.00 brackets it."
            ),
            "leakage": {
                "model": "leak resistance in parallel with cavity compliance",
                "minimum_resistance_for_about_5_percent_effect_pa_s_per_m3": (
                    leakage_resistance_5pct
                ),
                "minimum_pressure_decay_time_ms": (
                    leakage_resistance_5pct * leakage_compliance * 1000.0
                ),
                "recommended_pressure_decay_time_ms": 50.0,
            },
        },
        "placement": {
            "prototype_global_z_span_mm": [95.0, 125.0],
            "center_global_z_mm": design.collar_center_global_z_mm,
            "center_path_mm_from_inlet": design.collar_center_path_mm,
            "path_fraction": (
                design.collar_center_path_mm / design.main_port_physical_length_mm
            ),
            "reason": (
                "Lowest accessible external straight-tower position: strong first-mode "
                "pressure, nearly maximum second-mode pressure, zero box displacement, "
                "and below the DE250 envelope."
            ),
        },
        "enclosure_volume_and_tuning": {
            "external_prototype_displacement_l": 0.0,
            "gross_added_envelope_if_installed_inside_l": (
                math.pi
                * (
                    design.collar_outer_r**2
                    - (design.bore_r + design.existing_tube_wall_t) ** 2
                )
                * design.collar_axial_length
                / 1_000_000.0
            ),
            "naive_inside_install_tuning_before_side_branch_correction_hz": (
                design.bass_reflex_tuning_hz
                * math.sqrt(
                    design.net_box_volume_l
                    / (
                        design.net_box_volume_l
                        - math.pi
                        * (
                            design.collar_outer_r**2
                            - (
                                design.bore_r + design.existing_tube_wall_t
                            )
                            ** 2
                        )
                        * design.collar_axial_length
                        / 1_000_000.0
                    )
                )
            ),
            "qualification": (
                "An inside-cabinet version requires renewed exact box-volume and port "
                "tuning calculations; the external prototype avoids that penalty."
            ),
        },
        "step_roundtrip": roundtrip,
        "research_basis": [
            "Malte Hildebrandt, Daempfung stehender Wellen in Bassreflexrohren, 2024",
            "U. Ingard, On the Theory and Design of Acoustic Resonators, 1953",
            (
                "H. Levine and J. Schwinger, On the Radiation of Sound from an "
                "Unflanged Circular Pipe, 1948"
            ),
            (
                "M. R. Stinson, The Propagation of Plane Sound Waves in Narrow "
                "and Wide Circular Tubes, 1991"
            ),
        ],
    }
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=False) + "\n"
    )

    for source, viewer_name in (
        ("port_absorber_collar_assembly.step", "viewer"),
        ("port_absorber_collar_cutaway.step", "cutaway_viewer"),
        ("port_absorber_collar_air_domain.step", "air_domain_viewer"),
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

    print(f"Collar body: {OUT / 'port_absorber_collar_body.step'}")
    print(f"Collar lid: {OUT / 'port_absorber_collar_lid.step'}")
    print(f"Cutaway viewer: {OUT / 'cutaway_viewer' / 'viewer' / 'index.html'}")
    print(f"Diagnostics: {OUT / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
