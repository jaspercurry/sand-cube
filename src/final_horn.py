"""Public API for the current B&C DE250 JMLC horn."""

from __future__ import annotations

from build123d import Location, Part, Rot

from params import p
from src.features.horn import build_jmlc_horn


def build() -> Part:
    """Build the current printable B&C DE250 Le Cleac'h/JMLC horn."""
    return build_jmlc_horn(
        throat_d=p.horn_throat_d,
        mouth_outer_d=p.horn_mouth_outer_d,
        wall_t=p.horn_wall_t,
        exit_angle_deg=p.horn_exit_angle_deg,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=p.horn_profile_step,
        lip_r=p.horn_lip_r,
        flange_d=p.horn_flange_d,
        flange_t=p.horn_flange_t,
        bolt_clearance_d=p.horn_bolt_clearance_d,
        bolt_3_bcd=p.horn_bolt_3_bcd,
        bolt_2_bcd=p.horn_bolt_2_bcd,
        rear_spigot_l=p.horn_bracket_t,
        rear_spigot_od=p.horn_spigot_od,
    )


def place_above_enclosure(
    enclosure: Part,
    horn: Part,
    *,
    clearance: float = 10.0,
) -> Part:
    """Rotate and place a horn above the enclosure with the mouth front-flush."""
    horn = Rot(90, 0, 0) * horn
    enclosure_bb = enclosure.bounding_box()
    horn_bb = horn.bounding_box()
    horn_center_x = (horn_bb.min.X + horn_bb.max.X) / 2
    return (
        Location(
            (
                -horn_center_x,
                enclosure_bb.min.Y - horn_bb.min.Y,
                enclosure_bb.max.Z + clearance - horn_bb.min.Z,
            )
        )
        * horn
    )
