"""Single source of truth for sourced Sand Cube dimensions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    # Enclosure envelope
    cube_outer: float = 203.0
    outer_skin_t: float = 3.0
    void_t: float = 12.0
    inner_skin_t: float = 3.0
    edge_fillet_r: float = 3.0

    # Dayton Audio Epique E150HE-44, Parts Express 295-102.
    driver_cutout_dia: float = 122.0
    driver_overall_dia: float = 152.0
    driver_bolt_circle_r: float = 70.0
    # Parts Express lists 4.125 in. Treat as conservative clearance until
    # checked against the mechanical drawing and the actual rear-mount plan.
    driver_depth: float = 104.8
    driver_screw_count: int = 4

    # Dayton Audio Epique E180HE-PR, Parts Express 295-114.
    # Dayton mechanical drawing: flange OD 181.5, basket/cutout 151-151.5,
    # 6 mm flange thickness, 6 holes on a 169.5 mm bolt circle.
    pr_cutout_dia: float = 151.5
    # Rear opening must pass the E150HE-44 during assembly, then be covered by
    # the externally mounted PR flange. Verify against the physical PR gasket.
    pr_service_cutout_dia: float = 156.0
    pr_overall_dia: float = 181.5
    pr_recess_dia: float = 183.0
    pr_recess_depth: float = 6.0
    pr_bolt_circle_r: float = 84.75
    pr_depth: float = 54.0
    pr_screw_count: int = 6

    # Recessed front baffle.
    baffle_blend_r: float = 23.0
    baffle_blend_depth: float = 18.0
    baffle_tangent_in: float = 0.3
    baffle_tangent_out: float = 0.33

    # Bracing and inserts.
    bracing_grid_pitch: float = 60.0
    bracing_post_d: float = 8.0
    corner_gusset_leg: float = 15.0
    ring_width: float = 10.0
    ring_t: float = 5.0
    insert_bore_d: float = 5.6
    insert_bore_depth: float = 6.0
    boss_od: float = 8.0
    driver_mount_collar_od: float = 162.0

    # Connectors and fill port.
    gx16_hole_d: float = 16.2
    gx16_flat_chord: float = 1.5
    gx16_flat_radius: float = 12.5
    gx16_x: float = -74.0
    gx16_z: float = -70.0
    gx16_panel_land_t: float = 3.0
    gx16_flange_recess_d: float = 19.0
    gx16_flange_recess_depth: float = 1.2
    gx16_nut_across_flats: float = 20.6
    gx16_island_xy: float = 34.0
    heyco_hole_d: float = 15.9
    heyco_flat_chord: float = 1.4
    fill_thread_major_d: float = 14.0
    fill_thread_pitch: float = 2.0
    fill_thread_core_d: float = 11.8
    fill_thread_length: float = 10.0
    fill_passage_d: float = 10.0
    fill_port_x: float = 72.0
    fill_port_z: float = 92.5
    fill_cap_seat_d: float = 16.0
    fill_cap_seat_depth: float = 1.5
    fill_boss_od: float = 17.0


p = Params()
