"""Independent checks and limit plots for ``model.py`` and ``duct.py``.

This script intentionally recomputes expected asymptotes and reference values
instead of treating another script's JSON as truth.  A non-zero exit indicates
that a core equation, normalization, or historical comparison changed.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    from . import duct, model
except ImportError:  # Direct script execution.
    import duct
    import model


def _close(actual: float, expected: float, relative: float = 2e-3) -> None:
    if not math.isclose(actual, expected, rel_tol=relative):
        raise AssertionError(f"{actual:.9g} != {expected:.9g}")


def _bare_q(port: duct.Port, air: model.Air = model.Air()) -> float:
    rows = duct.response(
        None, port=port, air=air, start_hz=270, stop_hz=400, step_hz=0.05
    )
    key = "bare_outlet_velocity_per_pa"
    peak_index = max(range(len(rows)), key=lambda index: rows[index][key])
    half_power = rows[peak_index][key] / math.sqrt(2)
    lower = max(
        index for index in range(peak_index) if rows[index][key] <= half_power
    )
    upper = next(
        index
        for index in range(peak_index, len(rows))
        if rows[index][key] <= half_power
    )
    return rows[peak_index]["frequency_hz"] / (
        rows[upper]["frequency_hz"] - rows[lower]["frequency_hz"]
    )


def _series_half_power_q(
    branch: model.SlitBranch,
    air: model.Air = model.Air(),
) -> float:
    """Numerical current half-power Q for the isolated series branch."""
    resonance = model.resonance_frequency_hz(branch, air)
    target = math.sqrt(2) * abs(model.branch_impedance(resonance, branch, air))

    def error(frequency: float) -> float:
        return abs(model.branch_impedance(frequency, branch, air)) - target

    def root(low: float, high: float) -> float:
        f_low = error(low)
        for _ in range(100):
            middle = (low + high) / 2
            f_middle = error(middle)
            if f_low * f_middle <= 0:
                high = middle
            else:
                low = middle
                f_low = f_middle
        return (low + high) / 2

    lower = root(resonance * 0.2, resonance)
    upper = root(resonance, resonance * 3.0)
    return resonance / (upper - lower)


def run_checks() -> dict:
    air = model.Air()
    current = model.SlitBranch()
    result = model.evaluate(current, air)

    _close(result["geometry"]["total_area_mm2"], 11.3288755701, 1e-9)
    _close(result["dynamic_density_ratio_at_reference"]["real"], 1.192593474, 1e-8)
    _close(result["dynamic_density_ratio_at_reference"]["imag"], -0.566126644, 1e-8)
    _close(result["resonance_frequency_hz"], 309.257828, 1e-7)
    _close(result["resonance_q_from_reactance_slope"], 2.028781, 2e-5)
    _close(result["resistance_over_duct_impedance"], 2.0409015, 2e-5)
    half_power_q = _series_half_power_q(current, air)
    _close(half_power_q, result["resonance_q_from_reactance_slope"], 0.02)

    # Passivity and transfer-matrix invariants catch sign/convention mistakes.
    minimum_branch_resistance = min(
        model.branch_impedance(float(frequency), current, air).real
        for frequency in np.geomspace(20, 2000, 200)
    )
    if minimum_branch_resistance <= 0:
        raise AssertionError("Branch model became active")
    area = math.pi * (0.020**2)
    segment = duct.segment_matrix(338.25, 0.01, area, 0.0, air)
    _close(abs(np.linalg.det(segment)), 1.0, 1e-10)
    shunt = np.array(
        [[1 + 0j, 0j], [1 / model.branch_impedance(338.25, current), 1 + 0j]]
    )
    _close(abs(np.linalg.det(shunt)), 1.0, 1e-10)

    # Low-frequency parallel-plate limit: Re(rho_eff)/rho -> 6/5 and
    # R -> 12*mu*t/(S*w^2).
    low_frequency = 0.001
    rho_low = model.parallel_plate_dynamic_density(
        low_frequency, current.width_mm * 1e-3, air
    )
    _close(rho_low.real / air.density_kg_m3, 1.2, 1e-5)
    distributed_low = model.distributed_neck_impedance(low_frequency, current, air)
    poiseuille = (
        12
        * air.dynamic_viscosity_pa_s
        * current.physical_depth_mm
        * 1e-3
        / (current.total_area_m2 * (current.width_mm * 1e-3) ** 2)
    )
    _close(distributed_low.real, poiseuille, 2e-5)

    # High-shear density must approach bulk density.
    rho_high = model.parallel_plate_dynamic_density(1e8, current.width_mm * 1e-3, air)
    _close(rho_high.real / air.density_kg_m3, 1.0, 2e-3)

    end_cases = {}
    for end_mm in (0.0, 0.651110645089239, 1.1, 1.5):
        branch = model.SlitBranch(**{**asdict(current), "inertial_end_total_mm": end_mm})
        end_cases[f"{end_mm:g}"] = {
            "frequency_hz": model.resonance_frequency_hz(branch, air),
            "q": model.resonance_q(branch, air),
            "resistance_over_z0": model.evaluate(branch, air)[
                "resistance_over_duct_impedance"
            ],
        }

    # Reproduce the nominal Hildebrandt dimensions using the same parallel-
    # plate model.  The disagreement with the thesis's ~85 kPa s/m3/Q~3.25 is
    # recorded rather than silently called validation.
    hildebrandt = model.SlitBranch(
        slot_count=4,
        width_mm=0.2,
        overall_length_mm=50.0,
        physical_depth_mm=2.0,
        cavity_volume_cm3=123.0,
        inertial_end_total_mm=0.4,
        resistive_end_per_side_width_factor=0.425,
    )
    h_neck = model.neck_impedance(653.0, hildebrandt, air)
    h_mass = h_neck.imag / (2 * math.pi * 653)
    h_q_at_653 = 2 * math.pi * 653 * h_mass / h_neck.real

    lossless = duct.Port(attenuation_np_per_m=0.0, segments=260)
    q27 = duct.Port(attenuation_np_per_m=0.1, segments=260)
    lossless_summary, _, _ = duct.summarize(current, port=lossless)
    q27_summary, _, _ = duct.summarize(current, port=q27)

    # Check discretization convergence for the actual integrated route.
    installed_length = 508.0815787648397
    convergence = []
    for segments in (80, 260, 840):
        port = duct.Port(length_mm=installed_length, segments=segments)
        rows = duct.response(
            None,
            port=port,
            start_hz=330,
            stop_hz=345,
            step_hz=0.05,
        )
        peak = max(rows, key=lambda row: row["bare_outlet_velocity_per_pa"])
        profile = duct.pressure_profile(peak["frequency_hz"], port=port)
        antinode = max(profile, key=lambda row: row["pressure_magnitude"])
        convergence.append(
            {
                "segments": segments,
                "bare_peak_hz": peak["frequency_hz"],
                "pressure_antinode_path_mm": antinode["path_mm"],
            }
        )
    if (
        max(row["bare_peak_hz"] for row in convergence)
        - min(row["bare_peak_hz"] for row in convergence)
        > 0.1
    ):
        raise AssertionError("Installed duct frequency failed segment convergence")
    if (
        max(row["pressure_antinode_path_mm"] for row in convergence)
        - min(row["pressure_antinode_path_mm"] for row in convergence)
        > 1.0
    ):
        raise AssertionError("Installed duct antinode failed segment convergence")

    return {
        "status": "all assertions passed",
        "current_branch": result,
        "end_correction_cases": end_cases,
        "parallel_plate_limits": {
            "low_frequency_real_density_ratio": rho_low.real / air.density_kg_m3,
            "poiseuille_resistance_pa_s_m3": poiseuille,
            "computed_low_frequency_resistance_pa_s_m3": distributed_low.real,
            "high_frequency_real_density_ratio": rho_high.real / air.density_kg_m3,
        },
        "independent_invariants": {
            "series_q_from_reactance_slope": result[
                "resonance_q_from_reactance_slope"
            ],
            "series_q_from_half_power_bandwidth": half_power_q,
            "minimum_branch_resistance_20_to_2000_hz_pa_s_m3": (
                minimum_branch_resistance
            ),
            "lossless_segment_determinant": {
                "real": np.linalg.det(segment).real,
                "imag": np.linalg.det(segment).imag,
            },
            "shunt_determinant": {
                "real": np.linalg.det(shunt).real,
                "imag": np.linalg.det(shunt).imag,
            },
            "integrated_duct_segment_convergence": convergence,
        },
        "hildebrandt_cross_check": {
            "geometry": asdict(hildebrandt),
            "computed_neck_resistance_at_653_pa_s_m3": h_neck.real,
            "computed_omega_m_over_r_at_653": h_q_at_653,
            "reported_thesis_comparison": {
                "resistance_pa_s_m3_approx": 85000,
                "q_approx": 3.25,
            },
            "qualification": (
                "The factor-of-about-three mismatch must be reconciled before "
                "the thesis is claimed as quantitative validation of this model."
            ),
        },
        "duct_reference_cases": {
            "radiation_loss_only": lossless_summary,
            "alpha_0p1_np_m": q27_summary,
            "bare_q_at_alpha_0p1_np_m": _bare_q(q27),
        },
    }


def make_plots(output: Path, results: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    air = model.Air()
    current = model.SlitBranch()

    shear = np.logspace(-1, 1.5, 260)
    frequencies = (
        shear**2
        * 2
        * air.kinematic_viscosity_m2_s
        / ((current.width_mm * 1e-3) ** 2 * 2 * math.pi)
    )
    density = np.array(
        [
            model.parallel_plate_dynamic_density(float(f), current.width_mm * 1e-3, air)
            / air.density_kg_m3
            for f in frequencies
        ]
    )
    fig, (mass_ax, loss_ax) = plt.subplots(2, 1, figsize=(8.2, 6.5), sharex=True)
    mass_ax.semilogx(shear, density.real, label="Re(dynamic density) / bulk")
    mass_ax.axhline(1.2, color="0.45", linestyle="--", label="6/5 low-frequency mass")
    mass_ax.axvline(3.3453, color="0.25", linestyle=":", label="Current gap at 334.7 Hz")
    mass_ax.set(ylabel="Mass factor", title="Parallel-plate viscous solution and checked limits")
    mass_ax.set_ylim(0.98, 1.22)
    mass_ax.grid(True, which="both", alpha=0.25)
    mass_ax.legend()
    loss_ax.loglog(shear, -density.imag, label="−Im(dynamic density) / bulk")
    loss_ax.axvline(3.3453, color="0.25", linestyle=":")
    loss_ax.set(xlabel="Gap / viscous boundary-layer thickness", ylabel="Viscous loss factor")
    loss_ax.grid(True, which="both", alpha=0.25)
    loss_ax.legend()
    fig.tight_layout()
    fig.savefig(output / "verify_dynamic_density.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    frequency = np.linspace(250, 380, 500)
    for end_mm in (0.0, 0.651110645089239, 1.1, 1.5):
        branch = model.SlitBranch(**{**asdict(current), "inertial_end_total_mm": end_mm})
        reactance = [model.branch_impedance(float(f), branch, air).imag / 1e6 for f in frequency]
        root = model.resonance_frequency_hz(branch, air)
        ax.plot(frequency, reactance, label=f"Total end correction {end_mm:.2f} mm; f₀={root:.1f} Hz")
    ax.axhline(0, color="0.2", linewidth=1)
    ax.axvline(334.5, color="0.35", linestyle="--", label="Mode target 334.5 Hz")
    ax.set(xlabel="Frequency (Hz)", ylabel="Branch reactance (MPa·s/m³)", title="Current 7.166 mm slots: tuning uncertainty is explicit")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "verify_end_correction.png", dpi=180)
    plt.close(fig)

    # Use the explicitly qualified alpha=0.1 Np/m case (bare Q~27) to make
    # model-sensitivity plots finite and comparable to a lossy physical port.
    port = duct.Port(attenuation_np_per_m=0.1, segments=260)
    candidate_length = model.solve_slot_length_mm(
        334.5,
        model.SlitBranch(inertial_end_total_mm=1.1),
        high_mm=15,
    )
    candidate = model.SlitBranch(
        overall_length_mm=candidate_length, inertial_end_total_mm=1.1
    )
    old_rows = duct.response(current, port=port)
    new_rows = duct.response(candidate, port=port)
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 8.0), sharex=True)
    ax = axes[0]
    f = [row["frequency_hz"] for row in old_rows]
    bare = np.array([row["bare_outlet_velocity_per_pa"] for row in old_rows])
    old = np.array([row["treated_outlet_velocity_per_pa"] for row in old_rows])
    new = np.array([row["treated_outlet_velocity_per_pa"] for row in new_rows])
    reference = bare.max()
    ax.plot(f, 20 * np.log10(bare / reference), label="Bare port")
    ax.plot(f, 20 * np.log10(old / reference), label="Legacy 7.166 mm slots")
    ax.plot(
        f,
        20 * np.log10(new / reference),
        label=f"Pre-integration midpoint-targeted {candidate_length:.3f} mm slots",
    )
    ax.set(
        ylabel="Outlet response / bare peak (dB)",
        title="Pre-integration 513.589 mm route (assumed distributed loss)",
    )
    ax.grid(True, alpha=0.25)
    ax.legend()

    installed_target = 338.25
    low, high = 6.0, 12.0
    for _ in range(100):
        middle = (low + high) / 2
        average = sum(
            model.resonance_frequency_hz(
                model.SlitBranch(
                    overall_length_mm=middle,
                    inertial_end_total_mm=end_total,
                )
            )
            for end_total in (0.65, 1.50)
        ) / 2
        if average < installed_target:
            low = middle
        else:
            high = middle
    installed_length = (low + high) / 2
    installed_candidate = model.SlitBranch(
        overall_length_mm=installed_length,
        inertial_end_total_mm=1.1,
    )
    installed_port = duct.Port(
        length_mm=508.0815787648397,
        attenuation_np_per_m=0.1,
        segments=260,
    )
    installed_path = 273.8815502462105
    old_installed_rows = duct.response(
        model.SlitBranch(inertial_end_total_mm=1.1),
        branch_path_mm=installed_path,
        port=installed_port,
    )
    rev_d_rows = duct.response(
        installed_candidate,
        branch_path_mm=installed_path,
        port=installed_port,
    )
    ax = axes[1]
    f = [row["frequency_hz"] for row in rev_d_rows]
    bare = np.array(
        [row["bare_outlet_velocity_per_pa"] for row in rev_d_rows]
    )
    old = np.array(
        [row["treated_outlet_velocity_per_pa"] for row in old_installed_rows]
    )
    new = np.array(
        [row["treated_outlet_velocity_per_pa"] for row in rev_d_rows]
    )
    reference = bare.max()
    ax.plot(f, 20 * np.log10(bare / reference), label="Bare integrated route")
    ax.plot(
        f,
        20 * np.log10(old / reference),
        label="Legacy geometry with 1.10 mm end assumption",
    )
    ax.plot(
        f,
        20 * np.log10(new / reference),
        label=f"Rev D end-minimax {installed_length:.3f} mm slots",
    )
    ax.set(
        xlabel="Frequency (Hz)",
        ylabel="Outlet response / bare peak (dB)",
        title="Integrated 508.082 mm route (same conditional loss model)",
    )
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "verify_duct_response.png", dpi=180)
    plt.close(fig)

    results["candidate_reference"] = {
        "slot_length_mm": candidate_length,
        "branch": model.evaluate(candidate),
        "duct": duct.summarize(candidate, port=port)[0],
        "qualification": "Uses midpoint total inertial end correction 1.1 mm and assumed alpha=0.1 Np/m.",
    }
    results["rev_d_integrated_reference"] = {
        "slot_length_mm": installed_length,
        "slot_center_path_mm": installed_path,
        "branch": model.evaluate(
            installed_candidate,
            reference_hz=installed_target,
        ),
        "duct": duct.summarize(
            installed_candidate,
            branch_path_mm=installed_path,
            port=installed_port,
        )[0],
        "qualification": (
            "End-minimax only over 0.65..1.50 mm total inertial correction; "
            "duct uses hypothetical alpha=0.1 Np/m."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    results = run_checks()
    make_plots(args.output_dir, results)
    payload = json.dumps(results, indent=2) + "\n"
    (args.output_dir / "verification.json").write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
