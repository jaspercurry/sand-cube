"""One-dimensional folded-port/side-branch transfer-matrix model.

The bends are represented by their centerline length.  The 18 mm inlet flare
and 25 mm outlet flare are discretized as locally cylindrical slices; the
middle path has the 40 mm bore.  State convention is [pressure, volume velocity]
and matrices map downstream state to upstream state.

Absolute attenuation remains comparative because the model omits bend
scattering, driver/cabinet radiation and a measured distributed-loss law.  The
script reports its exact source/load convention and both point and worst-peak
comparisons so a narrow split peak cannot be hidden.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

try:
    from . import model
except ImportError:  # Direct script execution.
    import model


Matrix = np.ndarray


@dataclass(frozen=True)
class Port:
    length_mm: float = 513.589
    bore_diameter_mm: float = 40.0
    inlet_flare_length_mm: float = 18.0
    inlet_mouth_diameter_mm: float = 44.5
    outlet_flare_length_mm: float = 25.0
    outlet_mouth_diameter_mm: float = 58.6
    outlet_radiation_end_factor: float = 0.6133
    segments: int = 420
    # Optional amplitude attenuation of a forward wave.  Complex propagation
    # uses k=k0-j*alpha for exp(+jwt).  Zero leaves only outlet radiation loss.
    attenuation_np_per_m: float = 0.0


def radius_m(path_m: float, port: Port) -> float:
    total = port.length_mm * 1e-3
    inlet = port.inlet_flare_length_mm * 1e-3
    outlet = port.outlet_flare_length_mm * 1e-3
    outlet_start = total - outlet
    throat = port.bore_diameter_mm * 0.5e-3
    inlet_radius = port.inlet_mouth_diameter_mm * 0.5e-3
    outlet_radius = port.outlet_mouth_diameter_mm * 0.5e-3
    if path_m < inlet:
        return inlet_radius + (throat - inlet_radius) * path_m / inlet
    if path_m <= outlet_start:
        return throat
    return throat + (outlet_radius - throat) * (path_m - outlet_start) / outlet


def segment_matrix(
    frequency_hz: float,
    length_m: float,
    area_m2: float,
    attenuation_np_per_m: float,
    air: model.Air,
) -> Matrix:
    if length_m <= 0:
        return np.eye(2, dtype=complex)
    k = 2 * math.pi * frequency_hz / air.speed_m_s - 1j * attenuation_np_per_m
    zc = air.density_kg_m3 * air.speed_m_s / area_m2
    phase = k * length_m
    return np.array(
        [
            [np.cos(phase), 1j * zc * np.sin(phase)],
            [1j * np.sin(phase) / zc, np.cos(phase)],
        ],
        dtype=complex,
    )


def duct_matrix(
    frequency_hz: float,
    start_m: float,
    end_m: float,
    port: Port = Port(),
    air: model.Air = model.Air(),
) -> Matrix:
    if end_m <= start_m:
        return np.eye(2, dtype=complex)
    total = port.length_mm * 1e-3
    count = max(4, round(port.segments * (end_m - start_m) / total))
    dx = (end_m - start_m) / count
    result = np.eye(2, dtype=complex)
    for index in range(count):
        x = start_m + (index + 0.5) * dx
        area = math.pi * radius_m(x, port) ** 2
        result = result @ segment_matrix(
            frequency_hz, dx, area, port.attenuation_np_per_m, air
        )
    return result


def radiation_impedance(
    frequency_hz: float, port: Port = Port(), air: model.Air = model.Air()
) -> complex:
    radius = port.outlet_mouth_diameter_mm * 0.5e-3
    area = math.pi * radius**2
    zc = air.density_kg_m3 * air.speed_m_s / area
    ka = 2 * math.pi * frequency_hz * radius / air.speed_m_s
    return zc * (0.5 * ka**2 + 1j * port.outlet_radiation_end_factor * ka)


def complete_matrix(
    frequency_hz: float,
    branch_impedance: complex | None,
    branch_path_mm: float,
    port: Port = Port(),
    air: model.Air = model.Air(),
) -> Matrix:
    total = port.length_mm * 1e-3
    x = branch_path_mm * 1e-3
    if not 0 <= x <= total:
        raise ValueError("Branch path must lie inside the port")
    before = duct_matrix(frequency_hz, 0, x, port, air)
    after = duct_matrix(frequency_hz, x, total, port, air)
    if branch_impedance is None:
        return before @ after
    shunt = np.array(
        [[1 + 0j, 0j], [1 / branch_impedance, 1 + 0j]], dtype=complex
    )
    return before @ shunt @ after


def fixed_inlet_pressure_outlet_velocity(
    frequency_hz: float,
    branch_function: Callable[[float], complex] | None,
    branch_path_mm: float = 258.0,
    port: Port = Port(),
    air: model.Air = model.Air(),
) -> complex:
    impedance = None if branch_function is None else branch_function(frequency_hz)
    matrix = complete_matrix(
        frequency_hz, impedance, branch_path_mm, port, air
    )
    load = radiation_impedance(frequency_hz, port, air)
    # p_in=1 Pa and p_out=Zrad*U_out.
    return 1 / (matrix[0, 0] * load + matrix[0, 1])


def pressure_profile(
    frequency_hz: float,
    samples: int = 401,
    port: Port = Port(),
    air: model.Air = model.Air(),
) -> list[dict[str, float]]:
    total = port.length_mm * 1e-3
    complete = duct_matrix(frequency_hz, 0, total, port, air)
    load = radiation_impedance(frequency_hz, port, air)
    outlet_velocity = 1 / (complete[0, 0] * load + complete[0, 1])
    rows: list[dict[str, float]] = []
    for x in np.linspace(0, total, samples):
        downstream = duct_matrix(frequency_hz, float(x), total, port, air)
        pressure = (
            downstream[0, 0] * load + downstream[0, 1]
        ) * outlet_velocity
        rows.append({"path_mm": float(x * 1e3), "pressure_magnitude": abs(pressure)})
    maximum = max(row["pressure_magnitude"] for row in rows)
    for row in rows:
        row["normalized_pressure"] = row["pressure_magnitude"] / maximum
    return rows


def response(
    branch: model.SlitBranch | None,
    branch_path_mm: float = 258.0,
    port: Port = Port(),
    air: model.Air = model.Air(),
    start_hz: float = 220,
    stop_hz: float = 450,
    step_hz: float = 0.25,
) -> list[dict[str, float]]:
    branch_function = None
    if branch is not None:
        branch_function = lambda frequency: model.branch_impedance(
            frequency, branch, air
        )
    rows = []
    for frequency in np.arange(start_hz, stop_hz + step_hz / 2, step_hz):
        bare = abs(
            fixed_inlet_pressure_outlet_velocity(
                float(frequency), None, branch_path_mm, port, air
            )
        )
        treated = abs(
            fixed_inlet_pressure_outlet_velocity(
                float(frequency), branch_function, branch_path_mm, port, air
            )
        ) if branch is not None else bare
        rows.append(
            {
                "frequency_hz": float(frequency),
                "bare_outlet_velocity_per_pa": bare,
                "treated_outlet_velocity_per_pa": treated,
                "treated_minus_bare_db": 20 * math.log10(treated / bare),
            }
        )
    return rows


def _local_peaks(rows: list[dict[str, float]], key: str) -> list[dict[str, float]]:
    return [
        rows[index]
        for index in range(1, len(rows) - 1)
        if rows[index][key] >= rows[index - 1][key]
        and rows[index][key] > rows[index + 1][key]
    ]


def summarize(
    branch: model.SlitBranch,
    branch_path_mm: float = 258.0,
    port: Port = Port(),
    air: model.Air = model.Air(),
) -> tuple[dict[str, Any], list[dict[str, float]], list[dict[str, float]]]:
    rows = response(branch, branch_path_mm, port, air)
    bare_peak = max(rows, key=lambda row: row["bare_outlet_velocity_per_pa"])
    treated_peak = max(rows, key=lambda row: row["treated_outlet_velocity_per_pa"])
    at_bare = min(rows, key=lambda row: abs(row["frequency_hz"] - bare_peak["frequency_hz"]))
    profile = pressure_profile(bare_peak["frequency_hz"], port=port, air=air)
    profile_max = max(profile, key=lambda row: row["pressure_magnitude"])
    branch_profile = min(profile, key=lambda row: abs(row["path_mm"] - branch_path_mm))
    result = {
        "port": asdict(port),
        "branch_path_mm": branch_path_mm,
        "source_load_definition": (
            "1 Pa fixed pressure at inlet; outlet terminated by low-ka unflanged "
            "radiation impedance; reported response is outlet volume velocity."
        ),
        "branch_model": model.evaluate(
            branch,
            air,
            reference_hz=bare_peak["frequency_hz"],
        ),
        "bare_peak_frequency_hz": bare_peak["frequency_hz"],
        "treated_worst_peak_frequency_hz": treated_peak["frequency_hz"],
        "treated_worst_peak_vs_bare_peak_db": 20
        * math.log10(
            treated_peak["treated_outlet_velocity_per_pa"]
            / bare_peak["bare_outlet_velocity_per_pa"]
        ),
        "treated_at_bare_peak_db": at_bare["treated_minus_bare_db"],
        "bare_pressure_antinode_path_mm": profile_max["path_mm"],
        "normalized_pressure_at_branch": branch_profile["normalized_pressure"],
        "qualification": [
            "Bends represented by centerline length only.",
            "Absolute dB values are comparative and source/load dependent.",
            "Distributed attenuation is a user input, not a fitted physical law.",
        ],
    }
    return result, rows, profile


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width-mm", type=float, default=0.4)
    parser.add_argument("--length-mm", type=float, default=7.166387965983018)
    parser.add_argument("--depth-mm", type=float, default=5.0)
    parser.add_argument("--volume-cm3", type=float, default=53.32981472032441)
    parser.add_argument("--end-total-mm", type=float, default=0.651110645089239)
    parser.add_argument("--branch-path-mm", type=float, default=258.0)
    parser.add_argument("--port-length-mm", type=float, default=513.589)
    parser.add_argument("--attenuation-np-m", type=float, default=0.0)
    parser.add_argument("--output-dir", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    branch = model.SlitBranch(
        width_mm=args.width_mm,
        overall_length_mm=args.length_mm,
        physical_depth_mm=args.depth_mm,
        cavity_volume_cm3=args.volume_cm3,
        inertial_end_total_mm=args.end_total_mm,
    )
    port = Port(
        length_mm=args.port_length_mm,
        attenuation_np_per_m=args.attenuation_np_m,
    )
    summary, rows, profile = summarize(branch, args.branch_path_mm, port)
    payload = json.dumps(summary, indent=2) + "\n"
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "duct_summary.json").write_text(payload)
        _write_csv(args.output_dir / "duct_response.csv", rows)
        _write_csv(args.output_dir / "pressure_profile.csv", profile)
    print(payload, end="")


if __name__ == "__main__":
    main()
