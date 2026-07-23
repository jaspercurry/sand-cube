"""Shared parameter schema for the 190 mm Le Cléac'h horn family."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Horn190Parameters:
    profile_method: str = "le_cleach_2007"

    physical_mouth_target_d: float = 190.0
    # Calibrated profile input from the exact-profile bass-reflex study. The
    # 140-degree rolled-back wall reaches its maximum physical radius before
    # the acoustic terminal point, so this is intentionally not the same as
    # the final physical bounding diameter.
    profile_mouth_outer_d_input: float = 192.5299283
    target_axial_length: float = 82.38213681735276

    throat_d: float = 25.4
    wall_t: float = 3.2
    wavefront_t_min: float = 0.05
    wavefront_t_max: float = 4.0
    axial_solve_tolerance: float = 1e-7
    throat_angle_deg: float = 8.0
    exit_angle_deg: float = 140.0
    legacy_profile_step: float = 0.5

    lip_r: float = 1.6
    flange_d: float = 96.0
    flange_t: float = 8.0
    bolt_clearance_d: float = 6.6
    bolt_3_bcd: float = 57.0
    bolt_2_bcd: float = 76.0
    include_three_bolt_pattern: bool = False
    include_two_bolt_pattern: bool = True
    rear_spigot_l: float = 4.0
    rear_spigot_od: float = 38.0

    official_de250_exit_d: float = 25.0

    @property
    def mouth_inner_r(self) -> float:
        return self.profile_mouth_outer_d_input / 2.0 - self.wall_t
