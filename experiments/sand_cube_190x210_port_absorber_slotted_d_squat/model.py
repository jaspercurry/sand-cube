"""Auditable linear slit/side-branch model for the D-squat absorber.

The neck model uses the exact complex dynamic density for oscillatory flow
between infinite parallel plates.  The finite racetrack slot is represented by
its exact open area; the parallel-plate approximation is appropriate when the
slot length is much larger than its narrow gap.  The model is *viscous*, not a
complete thermal/compressible waveguide solution.  Thermal boundary effects,
3-D entrance flow, leakage, wall compliance and nonlinear separation are not
hidden inside fitted constants.

All public inputs are SI unless a name explicitly ends in ``_mm`` or ``_cm3``.
Acoustic impedance is pressure divided by volume velocity (Pa s / m^3).
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class Air:
    density_kg_m3: float = 1.204
    speed_m_s: float = 343.0
    dynamic_viscosity_pa_s: float = 1.81e-5

    @property
    def kinematic_viscosity_m2_s(self) -> float:
        return self.dynamic_viscosity_pa_s / self.density_kg_m3


@dataclass(frozen=True)
class SlitBranch:
    slot_count: int = 4
    width_mm: float = 0.400
    overall_length_mm: float = 7.166387965983018
    physical_depth_mm: float = 5.000
    cavity_volume_cm3: float = 53.32981472032441
    # Total inertial correction across both ends.  0.651 mm reproduces the old
    # 0.85*Dh assumption.  It is deliberately an exposed uncertain input.
    inertial_end_total_mm: float = 0.651110645089239
    # Linear sharp-edge resistance expressed as an equivalent distributed
    # length per side divided by gap width.  Set to zero to omit it.
    resistive_end_per_side_width_factor: float = 0.425

    @property
    def total_area_m2(self) -> float:
        return self.slot_count * racetrack_area_mm2(
            self.width_mm, self.overall_length_mm
        ) * 1e-6


def racetrack_area_mm2(width_mm: float, overall_length_mm: float) -> float:
    if width_mm <= 0 or overall_length_mm <= width_mm:
        raise ValueError("Racetrack length must exceed a positive width")
    return width_mm * (overall_length_mm - width_mm) + math.pi * width_mm**2 / 4


def racetrack_perimeter_mm(width_mm: float, overall_length_mm: float) -> float:
    if width_mm <= 0 or overall_length_mm <= width_mm:
        raise ValueError("Racetrack length must exceed a positive width")
    return 2 * (overall_length_mm - width_mm) + math.pi * width_mm


def hydraulic_diameter_mm(width_mm: float, overall_length_mm: float) -> float:
    return 4 * racetrack_area_mm2(width_mm, overall_length_mm) / racetrack_perimeter_mm(
        width_mm, overall_length_mm
    )


def viscous_boundary_layer_m(frequency_hz: float, air: Air = Air()) -> float:
    omega = 2 * math.pi * frequency_hz
    return math.sqrt(2 * air.kinematic_viscosity_m2_s / omega)


def parallel_plate_dynamic_density(
    frequency_hz: float, gap_m: float, air: Air = Air()
) -> complex:
    """Return complex viscous dynamic density for two infinite parallel plates.

    Sign convention is exp(+j*omega*t).  The returned density has a negative
    imaginary part, so ``j*omega*rho_eff`` has a positive real resistance.
    """
    if frequency_hz <= 0 or gap_m <= 0:
        raise ValueError("Frequency and plate gap must be positive")
    omega = 2 * math.pi * frequency_hz
    beta = (gap_m / 2) * cmath.sqrt(
        1j * omega / air.kinematic_viscosity_m2_s
    )
    denominator = 1 - cmath.tanh(beta) / beta
    return air.density_kg_m3 / denominator


def distributed_neck_impedance(
    frequency_hz: float, branch: SlitBranch, air: Air = Air()
) -> complex:
    rho_eff = parallel_plate_dynamic_density(
        frequency_hz, branch.width_mm * 1e-3, air
    )
    omega = 2 * math.pi * frequency_hz
    depth_m = branch.physical_depth_mm * 1e-3
    return 1j * omega * rho_eff * depth_m / branch.total_area_m2


def neck_impedance(
    frequency_hz: float, branch: SlitBranch, air: Air = Air()
) -> complex:
    """Distributed slit impedance plus explicit inertial/resistive ends."""
    omega = 2 * math.pi * frequency_hz
    distributed = distributed_neck_impedance(frequency_hz, branch, air)
    inertial = (
        1j
        * omega
        * air.density_kg_m3
        * branch.inertial_end_total_mm
        * 1e-3
        / branch.total_area_m2
    )
    equivalent_resistive_length_m = (
        2
        * branch.resistive_end_per_side_width_factor
        * branch.width_mm
        * 1e-3
    )
    resistive = distributed.real * (
        equivalent_resistive_length_m / (branch.physical_depth_mm * 1e-3)
    )
    return complex(distributed.real + resistive, distributed.imag) + inertial


def cavity_compliance(branch: SlitBranch, air: Air = Air()) -> float:
    return (branch.cavity_volume_cm3 * 1e-6) / (
        air.density_kg_m3 * air.speed_m_s**2
    )


def branch_impedance(
    frequency_hz: float, branch: SlitBranch, air: Air = Air()
) -> complex:
    omega = 2 * math.pi * frequency_hz
    compliance = cavity_compliance(branch, air)
    return neck_impedance(frequency_hz, branch, air) + 1 / (1j * omega * compliance)


def _bisect_root(
    function: Callable[[float], float], low: float, high: float, iterations: int = 100
) -> float:
    f_low = function(low)
    f_high = function(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        raise ValueError(f"Root is not bracketed in {low:g}..{high:g} Hz")
    for _ in range(iterations):
        middle = (low + high) / 2
        f_middle = function(middle)
        if f_low * f_middle <= 0:
            high = middle
            f_high = f_middle
        else:
            low = middle
            f_low = f_middle
    return (low + high) / 2


def resonance_frequency_hz(
    branch: SlitBranch,
    air: Air = Air(),
    low_hz: float = 10,
    high_hz: float = 2000,
) -> float:
    return _bisect_root(
        lambda frequency: branch_impedance(frequency, branch, air).imag,
        low_hz,
        high_hz,
    )


def resonance_q(branch: SlitBranch, air: Air = Air()) -> float:
    """General series-resonance Q from the local reactance slope."""
    frequency = resonance_frequency_hz(branch, air)
    omega = 2 * math.pi * frequency
    step = max(omega * 1e-5, 1e-3)

    def reactance_at_omega(value: float) -> float:
        return branch_impedance(value / (2 * math.pi), branch, air).imag

    slope = (reactance_at_omega(omega + step) - reactance_at_omega(omega - step)) / (
        2 * step
    )
    resistance = branch_impedance(frequency, branch, air).real
    return omega * slope / (2 * resistance)


def duct_characteristic_impedance(
    bore_diameter_mm: float = 40.0, air: Air = Air()
) -> float:
    area = math.pi * (bore_diameter_mm * 1e-3 / 2) ** 2
    return air.density_kg_m3 * air.speed_m_s / area


def solve_slot_length_mm(
    target_frequency_hz: float,
    branch: SlitBranch,
    air: Air = Air(),
    low_mm: float | None = None,
    high_mm: float = 30,
) -> float:
    low = low_mm or branch.width_mm * 1.01

    def error(length_mm: float) -> float:
        trial = SlitBranch(**{**asdict(branch), "overall_length_mm": length_mm})
        return resonance_frequency_hz(trial, air) - target_frequency_hz

    return _bisect_root(error, low, high_mm)


def solve_cavity_volume_cm3(
    target_frequency_hz: float,
    branch: SlitBranch,
    air: Air = Air(),
    low_cm3: float = 5,
    high_cm3: float = 200,
) -> float:
    def error(volume_cm3: float) -> float:
        trial = SlitBranch(**{**asdict(branch), "cavity_volume_cm3": volume_cm3})
        return resonance_frequency_hz(trial, air) - target_frequency_hz

    # Frequency decreases as volume increases, so reverse the generic bracket.
    f_low = error(low_cm3)
    f_high = error(high_cm3)
    if f_low * f_high > 0:
        raise ValueError("Volume root is not bracketed")
    low, high = low_cm3, high_cm3
    for _ in range(100):
        middle = (low + high) / 2
        value = error(middle)
        if value > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def evaluate(
    branch: SlitBranch = SlitBranch(),
    air: Air = Air(),
    reference_hz: float = 334.7,
) -> dict[str, Any]:
    resonance_hz = resonance_frequency_hz(branch, air)
    rho_eff = parallel_plate_dynamic_density(
        reference_hz, branch.width_mm * 1e-3, air
    )
    neck_at_reference = neck_impedance(reference_hz, branch, air)
    neck_at_resonance = neck_impedance(resonance_hz, branch, air)
    z0 = duct_characteristic_impedance(40.0, air)
    return {
        "air": asdict(air),
        "branch": asdict(branch),
        "geometry": {
            "area_each_mm2": racetrack_area_mm2(
                branch.width_mm, branch.overall_length_mm
            ),
            "total_area_mm2": branch.total_area_m2 * 1e6,
            "hydraulic_diameter_mm": hydraulic_diameter_mm(
                branch.width_mm, branch.overall_length_mm
            ),
        },
        "reference_frequency_hz": reference_hz,
        "viscous_boundary_layer_mm": viscous_boundary_layer_m(reference_hz, air)
        * 1e3,
        "width_over_boundary_layer": (branch.width_mm * 1e-3)
        / viscous_boundary_layer_m(reference_hz, air),
        "dynamic_density_ratio_at_reference": {
            "real": rho_eff.real / air.density_kg_m3,
            "imag": rho_eff.imag / air.density_kg_m3,
        },
        "neck_impedance_at_reference_pa_s_m3": {
            "real": neck_at_reference.real,
            "imag": neck_at_reference.imag,
        },
        "resonance_frequency_hz": resonance_hz,
        "resonance_q_from_reactance_slope": resonance_q(branch, air),
        "neck_resistance_at_resonance_pa_s_m3": neck_at_resonance.real,
        "duct_characteristic_impedance_pa_s_m3": z0,
        "resistance_over_duct_impedance": neck_at_resonance.real / z0,
        "qualification": [
            "Linear viscous parallel-plate neck model; no thermal bulk-modulus correction.",
            "Inertial and resistive end corrections are explicit uncertain inputs.",
            "No leakage, wall compliance, three-dimensional entrance flow, or nonlinear jetting.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width-mm", type=float, default=0.4)
    parser.add_argument("--length-mm", type=float, default=7.166387965983018)
    parser.add_argument("--depth-mm", type=float, default=5.0)
    parser.add_argument("--volume-cm3", type=float, default=53.32981472032441)
    parser.add_argument("--end-total-mm", type=float, default=0.651110645089239)
    parser.add_argument("--resistive-end-factor", type=float, default=0.425)
    parser.add_argument("--reference-hz", type=float, default=334.7)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    branch = SlitBranch(
        width_mm=args.width_mm,
        overall_length_mm=args.length_mm,
        physical_depth_mm=args.depth_mm,
        cavity_volume_cm3=args.volume_cm3,
        inertial_end_total_mm=args.end_total_mm,
        resistive_end_per_side_width_factor=args.resistive_end_factor,
    )
    result = evaluate(branch, reference_hz=args.reference_hz)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
