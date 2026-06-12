"""Compact 6 in Le Cleac'h / JMLC horn for the Eminence F110M-8."""

from __future__ import annotations

import math

from build123d import Align, Cylinder, Location, Mode, Part, Rot
from bd_warehouse.thread import IsoThread

from src.features.horn import (
    _primary_shape,
    _revolved_acoustic_void,
    _revolved_meridian_body,
    _to_nurbs_solid,
    horn_dimensions,
    jmlc_profile_metadata,
    jmlc_profile_points,
)

from .params import CompactParams, p


def _cylinder_z(
    *,
    diameter: float,
    depth: float,
    center: tuple[float, float, float],
) -> Part:
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    return Location(center) * cyl


def build(params: CompactParams = p) -> tuple[Part, dict[str, object]]:
    """Build a standalone 6 in JMLC horn with an F110M screw-on socket."""
    mouth_outer_r = params.horn_mouth_outer_d / 2
    mouth_inner_r = mouth_outer_r - params.horn_wall_t
    profile, cutoff_hz = jmlc_profile_points(
        throat_d=params.horn_throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=params.horn_exit_angle_deg,
        wavefront_t=params.horn_wavefront_t,
        throat_angle_deg=params.horn_throat_angle_deg,
        step=params.horn_profile_step,
    )

    horn_body = _revolved_meridian_body(
        profile,
        wall_t=params.horn_wall_t,
        throat_overlap=0.0,
        mouth_round_r=params.horn_lip_r,
    )
    horn_body = _to_nurbs_solid(horn_body)

    adapter_l = params.f110_socket_depth
    adapter_overlap = params.f110_adapter_overlap
    adapter_h = adapter_l + adapter_overlap
    adapter_center_z = (-adapter_l + adapter_overlap) / 2
    f110_thread = IsoThread(
        major_diameter=params.f110_thread_major_d,
        pitch=params.f110_thread_pitch,
        length=adapter_l,
        external=False,
        end_finishes=("square", "fade"),
        interference=params.f110_thread_interference,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    adapter = _cylinder_z(
        diameter=params.f110_adapter_od,
        depth=adapter_h,
        center=(0, 0, adapter_center_z),
    )
    adapter = _primary_shape(adapter - _revolved_acoustic_void(profile))
    adapter = _primary_shape(
        adapter
        - _cylinder_z(
            diameter=params.f110_thread_core_d,
            depth=adapter_l + 0.8,
            center=(0, 0, -adapter_l / 2),
        )
    )
    adapter = _primary_shape(
        adapter
        - (Location((0, 0, -adapter_l / 2)) * f110_thread)
    )
    adapter = _primary_shape(adapter.clean().fix())

    horn = _primary_shape(horn_body.fuse(adapter))
    horn = _primary_shape(horn.clean().fix())

    data = horn_dimensions(horn)
    data.update(
        jmlc_profile_metadata(
            throat_d=params.horn_throat_d,
            mouth_outer_d=params.horn_mouth_outer_d,
            wall_t=params.horn_wall_t,
            exit_angle_deg=params.horn_exit_angle_deg,
            wavefront_t=params.horn_wavefront_t,
            throat_angle_deg=params.horn_throat_angle_deg,
            step=params.horn_profile_step,
        )
    )
    data.update(
        {
            "name": "compact_6in_f110m_jmlc_horn",
            "target_driver": "Eminence F110M-8",
            "mouth_outer_dia_input_mm": params.horn_mouth_outer_d,
            "mouth_outer_dia_target_mm": params.horn_mouth_target_d,
            "mouth_outer_dia_target_in": params.horn_mouth_target_d / 25.4,
            "empirical_fc_from_outer_radius_hz": round(
                96216 / (params.horn_mouth_target_d / 2),
                1,
            ),
            "solved_cutoff_hz": round(cutoff_hz, 1),
            "f110_socket": {
                "thread_mode": "modeled_female_thread",
                "nominal_thread": "1-3/8 in 18 TPI external driver thread",
                "thread_major_dia_mm": round(params.f110_thread_major_d, 3),
                "thread_pitch_mm": round(params.f110_thread_pitch, 3),
                "thread_core_dia_mm": params.f110_thread_core_d,
                "thread_interference_mm": params.f110_thread_interference,
                "socket_depth_mm": params.f110_socket_depth,
                "adapter_od_mm": params.f110_adapter_od,
            },
            "checks": {
                "valid": horn.is_valid,
                "single_solid": len(horn.solids()) == 1,
                "mouth_outer_dia_ok": math.isclose(
                    data["bounding_box_mm"][0],
                    params.horn_mouth_target_d,
                    abs_tol=0.35,
                ),
            },
        }
    )
    return horn, data


def build_f110m_envelope(params: CompactParams = p) -> tuple[Part, dict[str, object]]:
    """Build a simplified F110M-8 envelope for fit checks.

    No public STEP file was found during the first search pass, so this uses
    the official Eminence mounting envelope dimensions: 85 mm overall diameter,
    72 mm depth, and 1-3/8 in 18 TPI external screw thread.
    """
    thread_l = params.f110_socket_depth
    body_l = params.f110_depth - thread_l
    threaded_snout = _cylinder_z(
        diameter=params.f110_thread_major_d,
        depth=thread_l,
        center=(0, 0, -thread_l / 2),
    )
    body = _cylinder_z(
        diameter=params.f110_body_d,
        depth=body_l,
        center=(0, 0, -thread_l - body_l / 2),
    )
    throat = _cylinder_z(
        diameter=params.horn_throat_d,
        depth=params.f110_depth + 2.0,
        center=(0, 0, -params.f110_depth / 2),
    )
    envelope = _primary_shape((threaded_snout + body - throat).clean().fix())
    data = {
        "name": "f110m_8_simplified_fit_envelope",
        "source": "Eminence F110M-8 official spec sheet; no public CAD found in first search pass",
        "overall_dia_mm": params.f110_body_d,
        "depth_mm": params.f110_depth,
        "thread": "1-3/8 in 18 TPI external",
        "is_valid": envelope.is_valid,
        "n_solids": len(envelope.solids()),
    }
    return envelope, data


def place_above_enclosure(
    enclosure: Part,
    horn: Part,
    *,
    clearance: float = 6.0,
) -> Part:
    """Rotate and place the horn above the cube with its mouth front-flush."""
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
