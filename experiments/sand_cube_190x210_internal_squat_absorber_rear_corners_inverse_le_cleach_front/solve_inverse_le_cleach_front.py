"""Inverse-solve exact Le Cléac'h 2007 profiles for a sculpted front.

This script creates no CAD. It calls the direct 4,000-row workbook recurrence
in ``src.features.horn`` and varies only authentic workbook inputs. The inner
horn is virtual and will eventually be discarded at the black-hole crest; the
outer rolled-back surface is intended to be cropped by the current R8 cabinet.
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
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners"
)
OUT = job_output_path(
    (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_inverse_le_cleach_front"
    )
)
os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SOURCE_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners as prior  # noqa: E402
from src.features.horn import _le_cleach_2007_points_for_cutoff  # noqa: E402


base = prior.base
DEFAULT_PULLBACKS_MM = (10.0, 12.5, 15.0, 17.5, 20.0)
DEFAULT_VIRTUAL_THROAT_D_MM = base.P.driver_cutout_dia
DEFAULT_THROAT_HALF_ANGLE_DEG = 60.0
CUTOFF_BOUNDS_HZ = (100.0, 1200.0)
WAVEFRONT_T_BOUNDS = (0.05, 20.0)
SOLVE_TOLERANCE_MM = 1e-4


@dataclass(frozen=True)
class FaceTargets:
    width_mm: float
    height_mm: float
    edge_radius_mm: float
    black_hole_radius_mm: float
    edge_midpoint_radius_mm: float
    physical_corner_radius_mm: float
    driver_cutout_diameter_mm: float
    driver_overall_diameter_mm: float


@dataclass(frozen=True)
class ProfileMetrics:
    target_corner_pullback_mm: float
    solved_cutoff_hz: float
    solved_wavefront_t: float
    wavefront_t_family: str
    virtual_throat_diameter_mm: float
    throat_half_angle_deg: float
    crest_radius_mm: float
    crest_radius_error_mm: float
    corner_radius_mm: float
    corner_pullback_mm: float
    corner_pullback_error_mm: float
    edge_midpoint_pullback_mm: float
    corner_terminal_angle_deg: float
    spreadsheet_row_step_mm: float
    recurrence_sample_count: int
    retained_outer_sample_count: int
    unique_crest: bool
    segment_angles_monotonic: bool
    maximum_segment_angle_step_deg: float
    minimum_segment_angle_deg: float
    maximum_segment_angle_deg: float
    driver_cutout_to_black_hole_radial_land_mm: float
    driver_overall_to_black_hole_radial_land_mm: float


@dataclass(frozen=True)
class SolvedProfile:
    metrics: ProfileMetrics
    points: tuple[tuple[float, float], ...]
    crest_axial_mm: float


def _face_targets() -> FaceTargets:
    half_width = base.D.width / 2.0
    half_height = base.D.height / 2.0
    edge_r = base.D.edge_fillet_r
    corner_center_x = half_width - edge_r
    corner_center_z = half_height - edge_r
    physical_corner_r = math.hypot(corner_center_x, corner_center_z) + edge_r
    return FaceTargets(
        width_mm=base.D.width,
        height_mm=base.D.height,
        edge_radius_mm=edge_r,
        black_hole_radius_mm=base.BLACK_HOLE_OUTER_D / 2.0,
        edge_midpoint_radius_mm=min(half_width, half_height),
        physical_corner_radius_mm=physical_corner_r,
        driver_cutout_diameter_mm=base.P.driver_cutout_dia,
        driver_overall_diameter_mm=base.P.driver_overall_dia,
    )


def _interpolated_axial(
    points: list[tuple[float, float]],
    radius_mm: float,
) -> float:
    for (radius0, axial0), (radius1, axial1) in zip(points, points[1:]):
        if radius0 <= radius_mm <= radius1:
            fraction = (radius_mm - radius0) / (radius1 - radius0)
            return axial0 + fraction * (axial1 - axial0)
    raise ValueError(f"Profile does not include radius {radius_mm:.6f} mm")


def _quadratic_crest(
    points: list[tuple[float, float]],
) -> tuple[float, float, int]:
    crest_index = max(range(len(points)), key=lambda index: points[index][1])
    if crest_index == 0 or crest_index == len(points) - 1:
        raise ValueError("Le Cléac'h profile has no interior rolled-back crest")
    local = points[crest_index - 1 : crest_index + 2]
    radii = np.asarray([point[0] for point in local], dtype=float)
    axials = np.asarray([point[1] for point in local], dtype=float)
    quadratic, linear, constant = np.polyfit(radii, axials, 2)
    if quadratic >= 0.0:
        raise ValueError("Le Cléac'h crest interpolation is not concave")
    crest_radius = -linear / (2.0 * quadratic)
    crest_axial = (
        quadratic * crest_radius**2 + linear * crest_radius + constant
    )
    return float(crest_radius), float(crest_axial), crest_index


def _segment_angles_deg(points: list[tuple[float, float]]) -> list[float]:
    return [
        math.degrees(math.atan2(radius1 - radius0, axial1 - axial0))
        for (radius0, axial0), (radius1, axial1) in zip(points, points[1:])
    ]


def _wavefront_family(wavefront_t: float) -> str:
    if math.isclose(wavefront_t, 1.0, abs_tol=1e-6):
        return "exponential"
    return "cosh" if wavefront_t < 1.0 else "sinh"


def _evaluate(
    *,
    cutoff_hz: float,
    wavefront_t: float,
    target_pullback_mm: float,
    targets: FaceTargets,
    virtual_throat_d_mm: float,
    throat_half_angle_deg: float,
) -> SolvedProfile:
    points, terminal_angle_deg, row_step_mm = (
        _le_cleach_2007_points_for_cutoff(
            throat_d=virtual_throat_d_mm,
            mouth_inner_r=targets.physical_corner_radius_mm,
            cutoff_hz=cutoff_hz,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_half_angle_deg,
        )
    )
    crest_radius, crest_axial, crest_index = _quadratic_crest(points)
    ring_axial = _interpolated_axial(points, targets.black_hole_radius_mm)
    edge_axial = _interpolated_axial(points, targets.edge_midpoint_radius_mm)
    corner_axial = _interpolated_axial(
        points,
        targets.physical_corner_radius_mm,
    )
    angles = _segment_angles_deg(points)
    angle_steps = np.diff(np.asarray(angles, dtype=float))
    angles_monotonic = bool(np.all(angle_steps >= -1e-7))
    ninety_crossings = sum(
        1
        for angle0, angle1 in zip(angles, angles[1:])
        if angle0 <= 90.0 < angle1
    )
    unique_crest = (
        ninety_crossings == 1
        and all(points[index][1] <= points[index + 1][1] for index in range(crest_index))
        and all(
            points[index][1] >= points[index + 1][1]
            for index in range(crest_index, len(points) - 1)
        )
    )
    corner_pullback = crest_axial - corner_axial
    retained_points = tuple(
        (radius, crest_axial - axial)
        for radius, axial in points
        if radius >= targets.black_hole_radius_mm
    )
    metrics = ProfileMetrics(
        target_corner_pullback_mm=target_pullback_mm,
        solved_cutoff_hz=cutoff_hz,
        solved_wavefront_t=wavefront_t,
        wavefront_t_family=_wavefront_family(wavefront_t),
        virtual_throat_diameter_mm=virtual_throat_d_mm,
        throat_half_angle_deg=throat_half_angle_deg,
        crest_radius_mm=crest_radius,
        crest_radius_error_mm=crest_radius - targets.black_hole_radius_mm,
        corner_radius_mm=targets.physical_corner_radius_mm,
        corner_pullback_mm=corner_pullback,
        corner_pullback_error_mm=corner_pullback - target_pullback_mm,
        edge_midpoint_pullback_mm=crest_axial - edge_axial,
        corner_terminal_angle_deg=terminal_angle_deg,
        spreadsheet_row_step_mm=row_step_mm,
        recurrence_sample_count=len(points),
        retained_outer_sample_count=len(retained_points),
        unique_crest=unique_crest,
        segment_angles_monotonic=angles_monotonic,
        maximum_segment_angle_step_deg=float(np.max(angle_steps)),
        minimum_segment_angle_deg=min(angles),
        maximum_segment_angle_deg=max(angles),
        driver_cutout_to_black_hole_radial_land_mm=(
            targets.black_hole_radius_mm
            - targets.driver_cutout_diameter_mm / 2.0
        ),
        driver_overall_to_black_hole_radial_land_mm=(
            targets.black_hole_radius_mm
            - targets.driver_overall_diameter_mm / 2.0
        ),
    )
    return SolvedProfile(
        metrics=metrics,
        points=retained_points,
        crest_axial_mm=crest_axial,
    )


def _solve_one(
    *,
    target_pullback_mm: float,
    targets: FaceTargets,
    virtual_throat_d_mm: float,
    throat_half_angle_deg: float,
) -> SolvedProfile:
    def residual(values: np.ndarray) -> np.ndarray:
        try:
            profile = _evaluate(
                cutoff_hz=float(values[0]),
                wavefront_t=float(values[1]),
                target_pullback_mm=target_pullback_mm,
                targets=targets,
                virtual_throat_d_mm=virtual_throat_d_mm,
                throat_half_angle_deg=throat_half_angle_deg,
            )
        except (OverflowError, ValueError):
            return np.asarray([1e5, 1e5])
        return np.asarray(
            [
                profile.metrics.crest_radius_error_mm,
                profile.metrics.corner_pullback_error_mm,
            ]
        )

    # The valid rolled-back region is narrow compared with the full workbook
    # input domain. Seed the local solve from a deterministic coarse scan so an
    # arbitrary requested pullback doesn't begin in a divergent recurrence.
    coarse_candidates: list[tuple[float, np.ndarray]] = []
    cutoff_samples = np.linspace(250.0, 750.0, 21)
    wavefront_samples = np.geomspace(0.5, 8.0, 21)
    for cutoff_hz in cutoff_samples:
        for wavefront_t in wavefront_samples:
            values = np.asarray([cutoff_hz, wavefront_t], dtype=float)
            errors = residual(values)
            score = float(np.dot(errors, errors))
            if score < 1e9:
                coarse_candidates.append((score, values))
    if not coarse_candidates:
        raise ValueError("No valid exact-workbook seed found for inverse solve")

    refined_candidates = []
    for _score, initial in sorted(coarse_candidates, key=lambda item: item[0])[:8]:
        refined = least_squares(
            residual,
            initial,
            bounds=(
                [CUTOFF_BOUNDS_HZ[0], WAVEFRONT_T_BOUNDS[0]],
                [CUTOFF_BOUNDS_HZ[1], WAVEFRONT_T_BOUNDS[1]],
            ),
            max_nfev=1000,
            xtol=1e-13,
            ftol=1e-13,
            gtol=1e-13,
            x_scale="jac",
        )
        errors = residual(refined.x)
        score = float(np.dot(errors, errors))
        if score < 1e9:
            refined_candidates.append((score, refined))
    if not refined_candidates:
        raise ValueError("All exact-workbook local inverse solves diverged")
    _best_score, refined = min(refined_candidates, key=lambda item: item[0])
    profile = _evaluate(
        cutoff_hz=float(refined.x[0]),
        wavefront_t=float(refined.x[1]),
        target_pullback_mm=target_pullback_mm,
        targets=targets,
        virtual_throat_d_mm=virtual_throat_d_mm,
        throat_half_angle_deg=throat_half_angle_deg,
    )
    if (
        abs(profile.metrics.crest_radius_error_mm) > SOLVE_TOLERANCE_MM
        or abs(profile.metrics.corner_pullback_error_mm) > SOLVE_TOLERANCE_MM
    ):
        raise ValueError(
            f"Inverse solve missed {target_pullback_mm:.3f} mm target: "
            f"crest error {profile.metrics.crest_radius_error_mm:.6f} mm, "
            f"corner error {profile.metrics.corner_pullback_error_mm:.6f} mm"
        )
    if not profile.metrics.unique_crest:
        raise ValueError("Solved profile does not have one clean rolled-back crest")
    if not profile.metrics.segment_angles_monotonic:
        raise ValueError("Solved profile wall angle is not monotonic")
    if profile.metrics.maximum_segment_angle_deg >= 180.0:
        raise ValueError("Solved profile turns through 180 degrees before the corner")
    return profile


def _rounded_square_top_half(
    targets: FaceTargets,
    samples_per_section: int = 160,
) -> tuple[np.ndarray, np.ndarray]:
    half_width = targets.width_mm / 2.0
    half_height = targets.height_mm / 2.0
    radius = targets.edge_radius_mm
    center_x = half_width - radius
    center_z = half_height - radius

    coordinates: list[tuple[float, float]] = []
    for angle_deg in np.linspace(135.0, 90.0, samples_per_section, endpoint=False):
        angle = math.radians(float(angle_deg))
        coordinates.append(
            (-center_x + radius * math.cos(angle), center_z + radius * math.sin(angle))
        )
    coordinates.extend(
        (float(x), half_height)
        for x in np.linspace(-center_x, center_x, 2 * samples_per_section, endpoint=False)
    )
    for angle_deg in np.linspace(90.0, 45.0, samples_per_section + 1):
        angle = math.radians(float(angle_deg))
        coordinates.append(
            (center_x + radius * math.cos(angle), center_z + radius * math.sin(angle))
        )

    arc_length = [0.0]
    for (x0, z0), (x1, z1) in zip(coordinates, coordinates[1:]):
        arc_length.append(arc_length[-1] + math.hypot(x1 - x0, z1 - z0))
    radial = [math.hypot(x, z) for x, z in coordinates]
    normalized = np.asarray(arc_length) / arc_length[-1]
    return normalized, np.asarray(radial)


def _profile_depth(profile: SolvedProfile, radius_mm: float) -> float:
    points = list(profile.points)
    return _interpolated_axial(points, radius_mm)


def _write_outputs(
    profiles: list[SolvedProfile],
    targets: FaceTargets,
) -> dict[str, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    solutions_json = OUT / "solutions.json"
    solutions_csv = OUT / "solutions.csv"
    points_csv = OUT / "retained_profile_points.csv"
    profiles_png = OUT / "profiles_by_corner_pullback.png"
    arches_png = OUT / "rounded_square_edge_arches.png"

    payload = {
        "status": "exact Le Cleac'h 2007 spreadsheet recurrence inverse solve",
        "cad_generated": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
        "recurrence": {
            "implementation": "src.features.horn._le_cleach_2007_points_for_cutoff",
            "source_workbook": "pavillon_JMLC.xls, 2007 recurrence",
            "source_cells": "B24:H4028",
            "faster_legacy_or_exploratory_recurrence_used": False,
        },
        "targets": asdict(targets),
        "solutions": [asdict(profile.metrics) for profile in profiles],
    }
    solutions_json.write_text(json.dumps(payload, indent=2))

    rows = [asdict(profile.metrics) for profile in profiles]
    with solutions_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with points_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "target_corner_pullback_mm",
                "radius_mm",
                "setback_from_crest_mm",
            ),
        )
        writer.writeheader()
        for profile in profiles:
            for radius_mm, depth_mm in profile.points:
                writer.writerow(
                    {
                        "target_corner_pullback_mm": (
                            profile.metrics.target_corner_pullback_mm
                        ),
                        "radius_mm": radius_mm,
                        "setback_from_crest_mm": depth_mm,
                    }
                )

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=180)
    for profile in profiles:
        radii = [point[0] for point in profile.points]
        depths = [point[1] for point in profile.points]
        ax.plot(
            radii,
            depths,
            label=f"{profile.metrics.target_corner_pullback_mm:g} mm corner",
        )
    ax.axvline(targets.black_hole_radius_mm, color="0.2", lw=0.8, ls="--")
    ax.axvline(targets.edge_midpoint_radius_mm, color="0.45", lw=0.8, ls=":")
    ax.axvline(targets.physical_corner_radius_mm, color="0.2", lw=0.8, ls="--")
    ax.set_xlabel("Radius from driver axis, mm")
    ax.set_ylabel("Setback behind black-hole crest plane, mm")
    ax.set_title("Exact 2007 Le Cléac'h rollback retained outside the 87 mm crest")
    ax.grid(True, alpha=0.24)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(profiles_png)
    plt.close(fig)

    boundary_position, boundary_radius = _rounded_square_top_half(targets)
    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=180)
    for profile in profiles:
        setback = np.asarray(
            [_profile_depth(profile, float(radius)) for radius in boundary_radius]
        )
        forward_rise = profile.metrics.target_corner_pullback_mm - setback
        ax.plot(
            boundary_position,
            forward_rise,
            label=f"{profile.metrics.target_corner_pullback_mm:g} mm corner",
        )
    ax.set_xlabel("Position along top perimeter, corner to corner")
    ax.set_ylabel("Forward rise above the corner plane, mm")
    ax.set_title("Side silhouette of the R8 square-cropped Le Cléac'h surface")
    ax.grid(True, alpha=0.24)
    ax.legend(loc="lower center", fontsize=8)
    fig.tight_layout()
    fig.savefig(arches_png)
    plt.close(fig)

    return {
        "solutions_json": str(solutions_json),
        "solutions_csv": str(solutions_csv),
        "retained_profile_points_csv": str(points_csv),
        "profiles_plot": str(profiles_png),
        "edge_arches_plot": str(arches_png),
    }


def solve(
    *,
    pullbacks_mm: list[float],
    virtual_throat_d_mm: float,
    throat_half_angle_deg: float,
) -> dict[str, Any]:
    if any(pullback <= 0.0 for pullback in pullbacks_mm):
        raise ValueError("Corner pullbacks must be positive")
    targets = _face_targets()
    if virtual_throat_d_mm >= 2.0 * targets.black_hole_radius_mm:
        raise ValueError("Virtual throat must fit inside the black-hole crest")

    profiles = [
        _solve_one(
            target_pullback_mm=pullback,
            targets=targets,
            virtual_throat_d_mm=virtual_throat_d_mm,
            throat_half_angle_deg=throat_half_angle_deg,
        )
        for pullback in sorted(set(pullbacks_mm))
    ]
    files = _write_outputs(profiles, targets)
    return {
        "status": "solved",
        "cad_generated": False,
        "targets": asdict(targets),
        "solutions": [asdict(profile.metrics) for profile in profiles],
        "files": files,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inverse-solve exact Le Cléac'h 2007 parent-horn profiles for the "
            "rear-corner enclosure front."
        )
    )
    parser.add_argument(
        "--corner-pullbacks",
        nargs="+",
        type=float,
        default=list(DEFAULT_PULLBACKS_MM),
        help="Corner setbacks to solve in millimeters.",
    )
    parser.add_argument(
        "--virtual-throat-d",
        type=float,
        default=DEFAULT_VIRTUAL_THROAT_D_MM,
        help=(
            "Virtual parent throat diameter. Defaults to the current woofer "
            "opening; the inner profile is discarded at the crest."
        ),
    )
    parser.add_argument(
        "--throat-half-angle",
        type=float,
        default=DEFAULT_THROAT_HALF_ANGLE_DEG,
        help="Le Cléac'h workbook throat half-angle in degrees.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = solve(
        pullbacks_mm=args.corner_pullbacks,
        virtual_throat_d_mm=args.virtual_throat_d,
        throat_half_angle_deg=args.throat_half_angle,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
