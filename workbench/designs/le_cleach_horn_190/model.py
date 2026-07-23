"""Standalone 190 mm exact-spreadsheet Le Cléac'h horn model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Part

from src.features.horn import (
    build_jmlc_horn,
    jmlc_profile_metadata,
    le_cleach_2007_profile_for_axial_length,
)
from workbench.designs.le_cleach_horn_190.params import (
    Horn190Parameters,
)


@dataclass(frozen=True)
class SolvedHorn190:
    horn: Part
    wavefront_t: float
    profile_points: tuple[tuple[float, float], ...]
    profile_metadata: dict[str, Any]


def build_horn(
    params: Horn190Parameters,
) -> SolvedHorn190:
    """Solve the named axial target and build the resulting printable horn."""
    points, cutoff_hz, row_step, wavefront_t = (
        le_cleach_2007_profile_for_axial_length(
            throat_d=params.throat_d,
            mouth_inner_r=params.mouth_inner_r,
            target_axial_length_mm=params.target_axial_length,
            exit_angle_deg=params.exit_angle_deg,
            throat_angle_deg=params.throat_angle_deg,
            wavefront_t_bounds=(
                params.wavefront_t_min,
                params.wavefront_t_max,
            ),
            axial_tolerance_mm=params.axial_solve_tolerance,
        )
    )
    horn = build_jmlc_horn(
        throat_d=params.throat_d,
        mouth_outer_d=params.profile_mouth_outer_d_input,
        wall_t=params.wall_t,
        exit_angle_deg=params.exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=params.throat_angle_deg,
        step=params.legacy_profile_step,
        lip_r=params.lip_r,
        flange_d=params.flange_d,
        flange_t=params.flange_t,
        bolt_clearance_d=params.bolt_clearance_d,
        bolt_3_bcd=params.bolt_3_bcd,
        bolt_2_bcd=params.bolt_2_bcd,
        rear_spigot_l=params.rear_spigot_l,
        rear_spigot_od=params.rear_spigot_od,
        profile_method=params.profile_method,
        include_three_bolt_pattern=params.include_three_bolt_pattern,
        include_two_bolt_pattern=params.include_two_bolt_pattern,
    )
    metadata = jmlc_profile_metadata(
        throat_d=params.throat_d,
        mouth_outer_d=params.profile_mouth_outer_d_input,
        wall_t=params.wall_t,
        exit_angle_deg=params.exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=params.throat_angle_deg,
        step=params.legacy_profile_step,
        profile_method=params.profile_method,
    )
    # Keep the directly solved values in the result as an independent check
    # against the metadata path, which recomputes the profile from solved T.
    metadata["direct_solved_cutoff_hz"] = cutoff_hz
    metadata["direct_spreadsheet_row_step_mm"] = row_step
    metadata["direct_axial_length_mm"] = points[-1][1]
    return SolvedHorn190(
        horn=horn,
        wavefront_t=wavefront_t,
        profile_points=tuple(points),
        profile_metadata=metadata,
    )
