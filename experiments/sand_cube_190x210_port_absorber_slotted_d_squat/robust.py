"""Robustness sweeps for the verified slit and 1-D duct models.

The script separates cheap branch-physics sweeps from a smaller set of costly
duct sweeps.  Absolute dB results remain conditional on the chosen 1-D loss,
source and radiation load; trends are saved with those inputs in JSON/CSV.
"""

from __future__ import annotations

import argparse
import csv
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


BASELINE_PORT_LENGTH_MM = 513.589
BASELINE_TARGET_HZ = 334.5
BASELINE_BRANCH_PATH_MM = 258.0
INSTALLED_PORT_LENGTH_MM = 508.0815787648397
INSTALLED_TARGET_HZ = 338.25
INSTALLED_BODY_CENTER_PATH_MM = 276.8815502462105
REV_D_SLOT_CENTER_OFFSET_MM = -3.0
REV_D_BRANCH_PATH_MM = (
    INSTALLED_BODY_CENTER_PATH_MM + REV_D_SLOT_CENTER_OFFSET_MM
)
TARGET_HZ = INSTALLED_TARGET_HZ
CURRENT_LENGTH_MM = 7.166387965983018
VOLUME_CM3 = 53.32981472032441
MID_END_FACTOR_WIDTHS = 2.75  # 1.1 mm total at the 0.4 mm nominal gap.


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _branch(width: float, length: float, volume: float, end: float) -> model.SlitBranch:
    return model.SlitBranch(
        width_mm=width,
        overall_length_mm=length,
        cavity_volume_cm3=volume,
        inertial_end_total_mm=end,
    )


def _frequency(width: float, length: float, volume: float, end: float) -> float:
    return model.resonance_frequency_hz(_branch(width, length, volume, end))


def solve_minimax_length(target_hz: float = TARGET_HZ) -> float:
    """Balance the 0.65 and 1.50 mm end-correction frequency extremes."""
    low, high = 6.0, 12.0
    for _ in range(90):
        middle = (low + high) / 2
        average = (
            _frequency(0.4, middle, VOLUME_CM3, 0.65)
            + _frequency(0.4, middle, VOLUME_CM3, 1.50)
        ) / 2
        if average < target_hz:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def _duct_metric(
    branch: model.SlitBranch,
    path_mm: float,
    alpha: float,
    port_length_mm: float = INSTALLED_PORT_LENGTH_MM,
    segments: int = 260,
) -> dict[str, float]:
    port = duct.Port(
        length_mm=port_length_mm,
        attenuation_np_per_m=alpha,
        segments=segments,
    )
    rows = duct.response(
        branch,
        branch_path_mm=path_mm,
        port=port,
        start_hz=230,
        stop_hz=450,
        step_hz=0.5,
    )
    bare = max(rows, key=lambda row: row["bare_outlet_velocity_per_pa"])
    treated = max(rows, key=lambda row: row["treated_outlet_velocity_per_pa"])
    at_bare = min(rows, key=lambda row: abs(row["frequency_hz"] - bare["frequency_hz"]))
    return {
        "bare_peak_hz": bare["frequency_hz"],
        "treated_worst_peak_hz": treated["frequency_hz"],
        "worst_peak_vs_bare_db": 20
        * math.log10(
            treated["treated_outlet_velocity_per_pa"]
            / bare["bare_outlet_velocity_per_pa"]
        ),
        "treated_at_bare_peak_db": at_bare["treated_minus_bare_db"],
    }


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    robust_length = solve_minimax_length()
    nominal_length = model.solve_slot_length_mm(
        TARGET_HZ,
        model.SlitBranch(inertial_end_total_mm=1.1),
        low_mm=4,
        high_mm=15,
    )

    width_rows: list[dict] = []
    for width in np.linspace(0.30, 0.55, 26):
        for label, length in (
            ("legacy_geometry_mid_end", CURRENT_LENGTH_MM),
            ("rev_d_end_minimax", robust_length),
        ):
            end = MID_END_FACTOR_WIDTHS * float(width)
            branch = _branch(float(width), length, VOLUME_CM3, end)
            evaluated = model.evaluate(branch)
            width_rows.append(
                {
                    "design": label,
                    "width_mm": float(width),
                    "length_mm": length,
                    "end_total_mm": end,
                    "resonance_hz": evaluated["resonance_frequency_hz"],
                    "q": evaluated["resonance_q_from_reactance_slope"],
                    "resistance_over_z0": evaluated["resistance_over_duct_impedance"],
                }
            )
    _write_csv(output / "width_sweep.csv", width_rows)

    lengths = np.linspace(6.0, 11.0, 51)
    ends = np.linspace(0.65, 1.50, 35)
    length_end_grid = np.empty((len(ends), len(lengths)))
    length_end_rows: list[dict] = []
    for i, end in enumerate(ends):
        for j, length in enumerate(lengths):
            frequency = _frequency(0.4, float(length), VOLUME_CM3, float(end))
            length_end_grid[i, j] = frequency
            length_end_rows.append(
                {"length_mm": float(length), "end_total_mm": float(end), "resonance_hz": frequency}
            )
    _write_csv(output / "length_end_sweep.csv", length_end_rows)

    volumes = np.linspace(40, 60, 41)
    volume_end_grid = np.empty((len(ends), len(volumes)))
    volume_end_rows: list[dict] = []
    for i, end in enumerate(ends):
        for j, volume in enumerate(volumes):
            frequency = _frequency(0.4, robust_length, float(volume), float(end))
            volume_end_grid[i, j] = frequency
            volume_end_rows.append(
                {"volume_cm3": float(volume), "end_total_mm": float(end), "resonance_hz": frequency}
            )
    _write_csv(output / "volume_end_sweep.csv", volume_end_rows)

    legacy_mid_end = _branch(0.4, CURRENT_LENGTH_MM, VOLUME_CM3, 1.1)
    candidate = _branch(0.4, robust_length, VOLUME_CM3, 1.1)
    placement_rows: list[dict] = []
    for path in np.linspace(200, 430, 9):
        for label, branch in (
            ("legacy_geometry_mid_end", legacy_mid_end),
            ("rev_d_end_minimax", candidate),
        ):
            placement_rows.append(
                {
                    "design": label,
                    "path_mm": float(path),
                    **_duct_metric(branch, float(path), 0.1),
                }
            )
    _write_csv(output / "placement_sweep.csv", placement_rows)

    loss_rows: list[dict] = []
    for alpha in (0.0, 0.05, 0.10, 0.15, 0.20):
        for label, branch in (
            ("legacy_geometry_mid_end", legacy_mid_end),
            ("rev_d_end_minimax", candidate),
        ):
            loss_rows.append(
                {
                    "design": label,
                    "attenuation_np_m": alpha,
                    **_duct_metric(branch, REV_D_BRANCH_PATH_MM, alpha),
                }
            )
    _write_csv(output / "duct_loss_sweep.csv", loss_rows)

    end_case_rows: list[dict] = []
    for end in (0.65, 1.1, 1.5):
        for label, length in (
            ("legacy_geometry_mid_end", CURRENT_LENGTH_MM),
            ("rev_d_end_minimax", robust_length),
        ):
            branch = _branch(0.4, length, VOLUME_CM3, end)
            end_case_rows.append(
                {
                    "design": label,
                    "end_total_mm": end,
                    "resonance_hz": model.resonance_frequency_hz(branch),
                    "q": model.resonance_q(branch),
                    "resistance_over_z0": model.evaluate(branch)["resistance_over_duct_impedance"],
                    **_duct_metric(branch, REV_D_BRANCH_PATH_MM, 0.1),
                }
            )
    _write_csv(output / "end_case_duct_sweep.csv", end_case_rows)

    # Linear low-frequency velocity estimate.  It deliberately stops short of
    # claiming the nonlinear jet velocity, which must self-limit through added R.
    bass_rows: list[dict] = []
    bass_frequency = 39.12
    x_m = REV_D_BRANCH_PATH_MM * 1e-3
    for port_velocity in np.linspace(0, 20, 41):
        local_pressure = 2 * math.pi * bass_frequency * model.Air().density_kg_m3 * port_velocity * x_m
        branch_velocity = 0.0 if port_velocity == 0 else (
            local_pressure / abs(model.branch_impedance(bass_frequency, candidate)) / candidate.total_area_m2
        )
        bass_rows.append(
            {
                "port_velocity_m_s": float(port_velocity),
                "estimated_local_pressure_pa": local_pressure,
                "linear_slit_velocity_m_s": branch_velocity,
                "linear_strouhal": math.inf if branch_velocity == 0 else 2 * math.pi * bass_frequency * candidate.width_mm * 1e-3 / branch_velocity,
            }
        )
    _write_csv(output / "bass_velocity_linear.csv", bass_rows)

    # Plots.
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 9.0), sharex=True)
    for label, length in (
        ("legacy_geometry_mid_end", CURRENT_LENGTH_MM),
        ("rev_d_end_minimax", robust_length),
    ):
        subset = [row for row in width_rows if row["design"] == label]
        name = f"{label.replace('_', ' ')} ({length:.3f} mm)"
        axes[0].plot([r["width_mm"] for r in subset], [r["resonance_hz"] for r in subset], label=name)
        axes[1].plot([r["width_mm"] for r in subset], [r["q"] for r in subset], label=name)
        axes[2].plot([r["width_mm"] for r in subset], [r["resistance_over_z0"] for r in subset], label=name)
    axes[0].axhline(TARGET_HZ, color="0.3", linestyle="--")
    axes[0].set_ylabel("Resonance (Hz)")
    axes[1].set_ylabel("Intrinsic Q")
    axes[2].set_ylabel("R / Z₀")
    axes[2].set_xlabel("Finished gap width (mm)")
    axes[0].set_title("Width changes frequency, damping and duct loading together")
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "robust_width.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    image = ax.pcolormesh(lengths, ends, length_end_grid, shading="auto", cmap="viridis")
    contour = ax.contour(lengths, ends, length_end_grid, levels=[TARGET_HZ], colors="white", linewidths=2)
    ax.clabel(contour, fmt={TARGET_HZ: f"{TARGET_HZ:.2f} Hz"})
    ax.axvline(robust_length, color="white", linestyle="--", alpha=0.8)
    fig.colorbar(image, ax=ax, label="Branch resonance (Hz)")
    ax.set(xlabel="Slot length (mm)", ylabel="Total inertial end correction (mm)", title="Slot length versus unresolved end correction")
    fig.tight_layout()
    fig.savefig(output / "robust_length_end.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    image = ax.pcolormesh(volumes, ends, volume_end_grid, shading="auto", cmap="viridis")
    contour = ax.contour(volumes, ends, volume_end_grid, levels=[TARGET_HZ], colors="white", linewidths=2)
    ax.clabel(contour, fmt={TARGET_HZ: f"{TARGET_HZ:.2f} Hz"})
    ax.axvline(VOLUME_CM3, color="white", linestyle="--", alpha=0.8)
    fig.colorbar(image, ax=ax, label="Branch resonance (Hz)")
    ax.set(xlabel="Cavity volume (cm³)", ylabel="Total inertial end correction (mm)", title=f"Volume trim with {robust_length:.3f} mm slots")
    fig.tight_layout()
    fig.savefig(output / "robust_volume_end.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for label in ("legacy_geometry_mid_end", "rev_d_end_minimax"):
        subset = [row for row in placement_rows if row["design"] == label]
        ax.plot([r["path_mm"] for r in subset], [r["worst_peak_vs_bare_db"] for r in subset], marker="o", label=label.replace("_", " "))
    ax.axvline(
        REV_D_BRANCH_PATH_MM,
        color="0.3",
        linestyle="--",
        label="Rev D installed slot center",
    )
    ax.set(xlabel="Branch path from inlet (mm)", ylabel="Worst treated peak / bare peak (dB)", title="Placement remains consequential in the lossy 1-D model")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "robust_placement.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for label in ("legacy_geometry_mid_end", "rev_d_end_minimax"):
        subset = [row for row in loss_rows if row["design"] == label]
        ax.plot([r["attenuation_np_m"] for r in subset], [r["worst_peak_vs_bare_db"] for r in subset], marker="o", label=label.replace("_", " "))
    ax.set(xlabel="Assumed distributed duct attenuation (Np/m)", ylabel="Worst treated peak / bare peak (dB)", title="Absolute attenuation depends strongly on unknown bare-port loss")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "robust_duct_loss.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.plot([r["port_velocity_m_s"] for r in bass_rows], [r["linear_slit_velocity_m_s"] for r in bass_rows])
    ax.set(xlabel="Port velocity at 39.12 Hz (m/s)", ylabel="Linear slit-velocity estimate (m/s)", title="Bass-frequency slit flow: screening estimate before nonlinear self-limiting")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "robust_bass_velocity.png", dpi=180)
    plt.close(fig)

    result = {
        "inputs": {
            "target_hz": TARGET_HZ,
            "baseline_route": {
                "physical_length_mm": BASELINE_PORT_LENGTH_MM,
                "bare_first_mode_hz": BASELINE_TARGET_HZ,
                "branch_path_mm": BASELINE_BRANCH_PATH_MM,
            },
            "integrated_route": {
                "physical_length_mm": INSTALLED_PORT_LENGTH_MM,
                "bare_first_mode_hz": INSTALLED_TARGET_HZ,
                "body_center_path_mm": INSTALLED_BODY_CENTER_PATH_MM,
                "rev_d_slot_center_path_mm": REV_D_BRANCH_PATH_MM,
            },
            "legacy_geometry_length_mm": CURRENT_LENGTH_MM,
            "cavity_volume_cm3": VOLUME_CM3,
            "midpoint_end_total_mm": 1.1,
            "end_uncertainty_mm": [0.65, 1.5],
            "reference_loss_alpha_np_m": 0.1,
            "reference_loss_bare_q_approx": 27,
        },
        "results": {
            "midpoint_target_length_mm": nominal_length,
            "minimax_end_uncertainty_length_mm": robust_length,
            "minimax_end_frequencies_hz": {
                "end_0p65_mm": _frequency(0.4, robust_length, VOLUME_CM3, 0.65),
                "end_1p50_mm": _frequency(0.4, robust_length, VOLUME_CM3, 1.50),
            },
            "candidate_model": model.evaluate(candidate, reference_hz=TARGET_HZ),
            "candidate_reference_duct": _duct_metric(
                candidate, REV_D_BRANCH_PATH_MM, 0.1
            ),
            "legacy_geometry_mid_end_reference_duct": _duct_metric(
                legacy_mid_end, REV_D_BRANCH_PATH_MM, 0.1
            ),
            "baseline_route_candidate_reference_duct": _duct_metric(
                candidate,
                BASELINE_BRANCH_PATH_MM,
                0.1,
                port_length_mm=BASELINE_PORT_LENGTH_MM,
            ),
        },
        "qualification": [
            "End correction is swept, not claimed known.",
            "Alpha=0.1 Np/m is a hypothetical calibration giving bare Q about 27.",
            "Absolute dB values require measured bare response and 3-D validation.",
            "The minimax label covers only the stated inertial end range, not all tolerances.",
            "Bass-frequency slit velocity is only an order-of-magnitude placeholder and will self-limit nonlinearly.",
        ],
    }
    (output / "robustness.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
