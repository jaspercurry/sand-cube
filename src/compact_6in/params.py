"""Parameters for the compact 6 in sand-filled speaker."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompactParams:
    # Enclosure envelope.
    cube_outer: float = 6.0 * 25.4
    enclosure_depth_y: float = 6.75 * 25.4
    outer_skin_t: float = 3.0
    void_t: float = 6.0
    inner_skin_t: float = 3.0
    rear_cap_t: float = 12.0
    edge_fillet_r: float = 8.0
    internal_fillet_r: float = 2.0
    sand_void_fillet_r: float = 1.0

    # Dayton Audio ND105-8.
    driver_cutout_dia: float = 93.0
    driver_overall_dia: float = 105.0
    driver_baffle_blend_r: float = 19.5
    driver_baffle_blend_depth: float = 18.0
    driver_baffle_tangent_in: float = 0.6
    driver_baffle_tangent_out: float = 0.45
    driver_baffle_wall_t: float = 10.0
    driver_seat_land_od: float = 112.0
    driver_bolt_circle_dia: float = 100.0
    driver_insert_bore_d: float = 4.2
    driver_insert_bore_depth: float = 6.0
    driver_screw_count: int = 4
    driver_displacement_l: float = 0.20

    # Dayton Audio DSA135-PR.
    pr_cutout_dia: float = 111.76
    pr_overall_dia: float = 134.87
    pr_recess_dia: float = 136.0
    pr_recess_depth: float = 2.0
    pr_bolt_circle_dia: float = 125.0
    pr_screw_clearance_d: float = 3.4
    pr_screw_count: int = 4
    pr_intrusion_l: float = 0.15

    # Sand-wall bridges and sealed cutout collars.
    bracing_post_d: float = 5.0
    cutout_collar_extra_d: float = 8.0
    gx16_collar_od: float = 30.0
    fill_port_d: float = 5.0
    fill_entry_d: float = 8.0
    fill_entry_depth: float = 1.0
    fill_port_x: float = 45.0
    fill_port_z: float = 68.0

    # GX16 rear connector. The PR consumes the middle of the rear face, so the
    # connector lives in the lower-left rear corner.
    gx16_hole_d: float = 16.2
    gx16_flange_recess_d: float = 19.0
    gx16_flange_recess_depth: float = 1.2
    gx16_x: float = -57.0
    gx16_z: float = -57.0

    # Eminence F110M-8 screw-on compression driver target.
    horn_throat_d: float = 25.4
    # Calibrated so the exported physical mouth bbox lands at ~6.0 in.
    horn_mouth_target_d: float = 6.0 * 25.4
    horn_mouth_outer_d: float = 154.7
    horn_wall_t: float = 3.0
    horn_wavefront_t: float = 0.8
    horn_throat_angle_deg: float = 8.0
    horn_exit_angle_deg: float = 140.0
    horn_profile_step: float = 0.5
    horn_lip_r: float = 1.4
    f110_thread_major_d: float = 1.375 * 25.4
    f110_thread_pitch: float = 25.4 / 18.0
    f110_socket_depth: float = 12.0
    f110_thread_core_d: float = 33.35
    f110_thread_interference: float = 0.35
    f110_adapter_od: float = 58.0
    f110_adapter_overlap: float = 6.0
    f110_body_d: float = 85.0
    f110_depth: float = 72.0

    @property
    def sandwich_t(self) -> float:
        return self.outer_skin_t + self.void_t + self.inner_skin_t

    @property
    def cavity_side(self) -> float:
        return self.cube_outer - 2 * self.sandwich_t

    @property
    def cavity_y(self) -> float:
        return self.cavity_side

    @property
    def front_cap_t(self) -> float:
        return self.enclosure_depth_y - self.rear_cap_t - self.cavity_y


p = CompactParams()
