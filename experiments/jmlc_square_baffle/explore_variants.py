"""Explore square-cropped JMLC baffle profile variants.

The production horn is an axisymmetric Le Cleac'h/JMLC horn. This experiment
keeps that math but asks a different question: if a 203 mm square cube face is
cropped out of a much larger horn, how deep is the driver/collar seat?
"""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from params import p


OUT = ROOT / "build" / "jmlc_square_baffle"

SOUND_SPEED_MM_S = 344_000.0
STEP_MM = 0.5


@dataclass(frozen=True)
class Variant:
    name: str
    mouth_inner_d: float
    exit_angle_deg: float


def _target_area(
    *,
    s0: float,
    cutoff_hz: float,
    path_l: float,
    wavefront_t: float,
) -> float:
    m = 4 * math.pi * cutoff_hz / SOUND_SPEED_MM_S
    u = m * path_l / 2
    return s0 * (math.cosh(u) + wavefront_t * math.sinh(u)) ** 2


def _jmlc_points_for_cutoff(
    *,
    throat_d: float,
    mouth_inner_r: float,
    cutoff_hz: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
) -> tuple[list[tuple[float, float]], float]:
    """Fast form of the recurrence in src.features.horn.

    The original recurrence is O(n^2), which is fine for production profiles
    but clumsy for broad sweeps. These prefix sums preserve the same recurrence
    while making exploratory scans quick.
    """
    throat_r = throat_d / 2
    phi0 = math.radians(throat_angle_deg)
    r0 = throat_r / math.sin(phi0)
    s0 = 2 * math.pi * r0**2 * (1 - math.cos(phi0))

    l_samples = [0.0]
    phi = [phi0]
    xp = [r0 * (1 - math.cos(phi0))]
    yp = [throat_r]

    sum_da_sin = 0.0
    sum_da_l_sin = 0.0
    sum_da_l2_sin = 0.0
    sum_da_y = 0.0
    sum_da_l_y = 0.0

    while yp[-1] < mouth_inner_r and len(l_samples) < 40_000:
        i = len(l_samples)
        li = i * step

        projected = 2 * math.pi * (r0 + li) ** 2 * (1 - math.cos(phi0))
        projected += 2 * math.pi * (
            li**2 * sum_da_sin
            - 2 * li * sum_da_l_sin
            + sum_da_l2_sin
            + li * sum_da_y
            - sum_da_l_y
        )
        target = _target_area(
            s0=s0,
            cutoff_hz=cutoff_hz,
            path_l=li,
            wavefront_t=wavefront_t,
        )

        local_r = step * math.sin(phi[-1]) + yp[-1]
        delta_alpha = (target - projected) / (2 * math.pi * local_r * step)
        next_phi = phi[-1] + delta_alpha
        next_x = xp[-1] + step * math.cos(next_phi)
        next_y = yp[-1] + step * math.sin(next_phi)

        if (
            not all(
                math.isfinite(v)
                for v in (delta_alpha, next_phi, next_x, next_y)
            )
            or next_y <= yp[-1]
        ):
            raise ValueError("JMLC recurrence diverged")

        lj = l_samples[-1]
        sin_phi_j = math.sin(phi[-1])
        yj = yp[-1]
        sum_da_sin += delta_alpha * sin_phi_j
        sum_da_l_sin += delta_alpha * lj * sin_phi_j
        sum_da_l2_sin += delta_alpha * lj**2 * sin_phi_j
        sum_da_y += delta_alpha * yj
        sum_da_l_y += delta_alpha * lj * yj

        l_samples.append(li)
        phi.append(next_phi)
        xp.append(next_x)
        yp.append(next_y)

    if yp[-1] < mouth_inner_r:
        raise ValueError("JMLC recurrence did not reach mouth radius")

    terminal_phi = phi[-1]
    if yp[-1] > mouth_inner_r:
        t = (mouth_inner_r - yp[-2]) / (yp[-1] - yp[-2])
        xp[-1] = xp[-2] + t * (xp[-1] - xp[-2])
        yp[-1] = mouth_inner_r
        terminal_phi = phi[-2] + t * (phi[-1] - phi[-2])

    z0 = xp[0]
    return [(r, z - z0) for r, z in zip(yp, xp)], math.degrees(terminal_phi)


def _terminal_angle_or_none(
    *,
    cutoff_hz: float,
    mouth_inner_r: float,
) -> float | None:
    try:
        _points, angle = _jmlc_points_for_cutoff(
            throat_d=p.horn_throat_d,
            mouth_inner_r=mouth_inner_r,
            cutoff_hz=cutoff_hz,
            wavefront_t=p.horn_wavefront_t,
            throat_angle_deg=p.horn_throat_angle_deg,
            step=STEP_MM,
        )
    except ValueError:
        return None
    return angle


def _solve_cutoff_hz(
    *,
    mouth_inner_r: float,
    exit_angle_deg: float,
) -> float:
    last_cutoff = 100.0
    last_angle = _terminal_angle_or_none(
        cutoff_hz=last_cutoff,
        mouth_inner_r=mouth_inner_r,
    )
    if last_angle is None:
        raise ValueError("Unable to evaluate low cutoff")

    for cutoff in (
        150,
        200,
        250,
        300,
        350,
        400,
        450,
        500,
        550,
        600,
        650,
        700,
        750,
        800,
        850,
        900,
        950,
        1000,
        1100,
        1200,
    ):
        angle = _terminal_angle_or_none(
            cutoff_hz=cutoff,
            mouth_inner_r=mouth_inner_r,
        )
        if angle is None:
            angle = 999.0
        if last_angle <= exit_angle_deg <= angle:
            low = last_cutoff
            high = float(cutoff)
            for _ in range(42):
                mid = (low + high) / 2
                mid_angle = _terminal_angle_or_none(
                    cutoff_hz=mid,
                    mouth_inner_r=mouth_inner_r,
                )
                if mid_angle is None or mid_angle >= exit_angle_deg:
                    high = mid
                else:
                    low = mid
            return (low + high) / 2
        last_cutoff = float(cutoff)
        last_angle = angle

    raise ValueError("Unable to bracket requested exit angle")


def _intersections_at_radius(
    points: list[tuple[float, float]],
    radius: float,
) -> list[float]:
    z_values: list[float] = []
    for (r0, z0), (r1, z1) in zip(points, points[1:]):
        if not (min(r0, r1) <= radius <= max(r0, r1)) or r0 == r1:
            continue
        t = (radius - r0) / (r1 - r0)
        if 0 <= t <= 1:
            z_values.append(z0 + t * (z1 - z0))
    return z_values


def _profile_for_variant(variant: Variant) -> dict[str, object]:
    mouth_inner_r = variant.mouth_inner_d / 2
    cutoff_hz = _solve_cutoff_hz(
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=variant.exit_angle_deg,
    )
    points, terminal_angle = _jmlc_points_for_cutoff(
        throat_d=p.horn_throat_d,
        mouth_inner_r=mouth_inner_r,
        cutoff_hz=cutoff_hz,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=STEP_MM,
    )
    z_values = [z for _r, z in points]
    mouth_z = points[-1][1]
    frontmost_z = max(z_values)

    diameters = {
        "driver_cutout": p.driver_cutout_dia,
        "driver_overall": p.driver_overall_dia,
        "driver_mount_collar": p.driver_mount_collar_od,
    }
    seats: dict[str, dict[str, float | int | None]] = {}
    for label, diameter in diameters.items():
        intersections = _intersections_at_radius(points, diameter / 2)
        if not intersections:
            seats[label] = {
                "diameter_mm": diameter,
                "intersections": 0,
                "depth_from_mouth_plane_mm": None,
                "depth_from_frontmost_plane_mm": None,
            }
            continue
        seat_z = intersections[0]
        seats[label] = {
            "diameter_mm": diameter,
            "intersections": len(intersections),
            "depth_from_mouth_plane_mm": round(mouth_z - seat_z, 3),
            "depth_from_frontmost_plane_mm": round(frontmost_z - seat_z, 3),
        }

    return {
        "variant": asdict(variant),
        "solved_cutoff_hz": round(cutoff_hz, 3),
        "terminal_angle_deg": round(terminal_angle, 3),
        "mouth_outer_d_with_wall_mm": round(
            variant.mouth_inner_d + 2 * p.horn_wall_t,
            3,
        ),
        "mouth_z_mm": round(mouth_z, 3),
        "frontmost_z_mm": round(frontmost_z, 3),
        "rollback_mm": round(frontmost_z - mouth_z, 3),
        "sample_count": len(points),
        "seats": seats,
        "points": points,
    }


def _flatten_for_csv(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    flat_rows: list[dict[str, object]] = []
    for row in rows:
        variant = row["variant"]
        assert isinstance(variant, dict)
        seats = row["seats"]
        assert isinstance(seats, dict)
        for seat_name, seat_data in seats.items():
            assert isinstance(seat_data, dict)
            flat_rows.append(
                {
                    "name": variant["name"],
                    "mouth_inner_d": variant["mouth_inner_d"],
                    "exit_angle_deg": variant["exit_angle_deg"],
                    "mouth_outer_d_with_wall_mm": row[
                        "mouth_outer_d_with_wall_mm"
                    ],
                    "solved_cutoff_hz": row["solved_cutoff_hz"],
                    "mouth_z_mm": row["mouth_z_mm"],
                    "frontmost_z_mm": row["frontmost_z_mm"],
                    "rollback_mm": row["rollback_mm"],
                    "seat": seat_name,
                    "seat_diameter_mm": seat_data["diameter_mm"],
                    "depth_from_mouth_plane_mm": seat_data[
                        "depth_from_mouth_plane_mm"
                    ],
                    "depth_from_frontmost_plane_mm": seat_data[
                        "depth_from_frontmost_plane_mm"
                    ],
                }
            )
    return flat_rows


def _plot_profiles_by_mouth(rows: list[dict[str, object]], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=180)
    selected = [
        row
        for row in rows
        if row["variant"]["exit_angle_deg"] == 90.0
    ]
    for row in selected:
        variant = row["variant"]
        mouth_z = row["mouth_z_mm"]
        points = row["points"]
        x_depth = [mouth_z - z for _r, z in points]
        y_diameter = [2 * r for r, _z in points]
        ax.plot(
            x_depth,
            y_diameter,
            label=f'{variant["name"]}: {variant["mouth_inner_d"]:.0f} mm mouth',
        )

    ax.axhline(p.driver_cutout_dia, color="0.25", lw=0.8, ls="--")
    ax.axhline(p.driver_overall_dia, color="0.35", lw=0.8, ls=":")
    ax.axhline(p.driver_mount_collar_od, color="0.35", lw=0.8, ls="-.")
    ax.axhline(math.sqrt(2) * p.cube_outer, color="0.6", lw=0.8)
    ax.set_xlabel("Depth behind mouth plane, mm")
    ax.set_ylabel("Horn/profile diameter, mm")
    ax.set_title("Square baffle candidates, 90 deg stop angle")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def _plot_profiles_by_exit_angle(
    rows: list[dict[str, object]],
    output: Path,
    *,
    mouth_inner_d: float,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=180)
    selected = [
        row
        for row in rows
        if math.isclose(row["variant"]["mouth_inner_d"], mouth_inner_d)
    ]
    for row in selected:
        variant = row["variant"]
        mouth_z = row["mouth_z_mm"]
        points = row["points"]
        x_depth = [mouth_z - z for _r, z in points]
        y_diameter = [2 * r for r, _z in points]
        ax.plot(
            x_depth,
            y_diameter,
            label=(
                f'{variant["exit_angle_deg"]:.0f} deg stop, '
                f'rollback {row["rollback_mm"]:.1f} mm'
            ),
        )

    ax.axvline(0, color="0.35", lw=0.8)
    ax.axhline(p.driver_cutout_dia, color="0.25", lw=0.8, ls="--")
    ax.axhline(p.driver_overall_dia, color="0.35", lw=0.8, ls=":")
    ax.axhline(p.driver_mount_collar_od, color="0.35", lw=0.8, ls="-.")
    ax.axhline(math.sqrt(2) * p.cube_outer, color="0.6", lw=0.8)
    ax.set_xlabel("Depth behind mouth plane, mm")
    ax.set_ylabel("Horn/profile diameter, mm")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    square_min_inner_d = math.sqrt(2) * p.cube_outer
    mouth_diameters = [
        square_min_inner_d,
        300.0,
        320.0,
        350.0,
        400.0,
    ]
    exit_angles = [90.0, 105.0, 110.0, 120.0, 140.0]
    variants = [
        Variant(
            name=(
                "min_square"
                if math.isclose(mouth_d, square_min_inner_d)
                else f"mouth_{mouth_d:.0f}"
            ),
            mouth_inner_d=mouth_d,
            exit_angle_deg=exit_angle,
        )
        for exit_angle in exit_angles
        for mouth_d in mouth_diameters
    ]

    rows = [_profile_for_variant(variant) for variant in variants]
    json_rows = [{k: v for k, v in row.items() if k != "points"} for row in rows]
    (OUT / "variants.json").write_text(json.dumps(json_rows, indent=2))

    flat_rows = _flatten_for_csv(rows)
    with (OUT / "variants.csv").open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)

    _plot_profiles_by_mouth(rows, OUT / "profiles_by_mouth.png")
    _plot_profiles_by_exit_angle(
        rows,
        OUT / "profiles_square_mouth_by_exit_angle.png",
        mouth_inner_d=square_min_inner_d,
        title="Effect of stop angle at minimum square mouth",
    )
    _plot_profiles_by_exit_angle(
        rows,
        OUT / "profiles_320_mouth_by_exit_angle.png",
        mouth_inner_d=320.0,
        title="Effect of stop angle at 320 mm inner mouth",
    )

    print(json.dumps(json_rows, indent=2))


if __name__ == "__main__":
    main()
