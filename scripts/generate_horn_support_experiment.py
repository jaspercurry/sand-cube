"""Export the experimental print-assist JMLC horn and support cage."""

from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import Compound, Location, Unit, export_step, export_stl

from params import p
from src.features.horn_support_experiment import (
    _primary_shape,
    build_contoured_lip_cradle,
    build_corrugated_inner_lip_support,
    build_jmlc_horn,
    build_lightweight_flared_lip_cradle,
    build_rear_flange_petg_interface_ring,
    build_rear_flange_support_ring,
    horn_dimensions,
    jmlc_profile_metadata,
    jmlc_profile_points,
)


OUT = ROOT / "build" / "experiments" / "jmlc_horn_support_experiment"
VERSION = "v20"
TARGET_PRINTED_OUTER_D = 220.0
# The rolled-back outer edge finishes inside the nominal construction mouth
# diameter. This value is calibrated by diagnostics; it keeps the exported
# physical mouth close to 220 mm without scaling the JMLC surface.
EXPERIMENTAL_MOUTH_OUTER_D = 221.74
EXPERIMENTAL_EXIT_ANGLE_DEG = 150.0
CONTACT_START_BEFORE_APEX_MM = 14.0
CONTACT_MAX_EXTRA_T = 0.0
CONTACT_MAX_OUTER_CLEARANCE = 0.0
SUPPORT_RADIAL_WIDTH = 10.0
SUPPORT_WALL_THICKNESS = 0.84
SUPPORT_EDGE_MARGIN = 0.35
SUPPORT_WAVE_AMPLITUDE = (
    SUPPORT_RADIAL_WIDTH / 2 - SUPPORT_WALL_THICKNESS / 2 - SUPPORT_EDGE_MARGIN
)
SUPPORT_WAVE_COUNT = 20
SUPPORT_SAMPLES_PER_WAVE = 8
# Keep the bed footprint narrow, then carry the hidden upper support inward
# with ribs so the rolled-back lip has a broader shaped surface to print onto.
SUPPORT_RADIAL_INSET = 0.60 + 1.25 - SUPPORT_RADIAL_WIDTH
TOP_SUPPORT_INNER_EXTRA_R = 16.0
# Carry the extra support inward from the innermost corrugation trough instead
# of spanning the full outer support band. This keeps the flare hidden from the
# outside and removes the V18 pass-through look where ribs crossed the wall.
SUPPORT_TROUGH_INNER_INSET = (
    SUPPORT_RADIAL_INSET
    + SUPPORT_RADIAL_WIDTH / 2
    - SUPPORT_WAVE_AMPLITUDE
    - SUPPORT_WALL_THICKNESS / 2
)
CRADLE_RADIAL_INSET = SUPPORT_TROUGH_INNER_INSET - TOP_SUPPORT_INNER_EXTRA_R
CRADLE_RADIAL_WIDTH = TOP_SUPPORT_INNER_EXTRA_R
OUTER_LANDING_RADIAL_INSET = SUPPORT_TROUGH_INNER_INSET
OUTER_LANDING_RADIAL_WIDTH = (
    SUPPORT_RADIAL_INSET + SUPPORT_RADIAL_WIDTH - SUPPORT_TROUGH_INNER_INSET
)
OUTER_LANDING_BASE_OVERLAP_H = 0.08
INTERFACE_H = 0.40
CRADLE_CAP_H = 1.40
CRADLE_RIB_COUNT = SUPPORT_WAVE_COUNT * 2
CRADLE_RIB_TANGENTIAL_WIDTH = 1.20
CRADLE_RIB_RISE_H = 42.0
CRADLE_RIB_BASE_RADIAL_WIDTH = 1.60
CRADLE_RIB_TROUGH_OVERLAP = 0.20
STL_LINEAR_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.04
CONTACT_PROFILE_SAMPLES = 64
CRADLE_RADIAL_BANDS = 32


def _corrugation_peak_trough_rib_specs(
    mouth_inner_r: float,
) -> list[tuple[float, float, float]]:
    """Return alternating peak/trough rib anchors for the hidden inner cradle."""
    support_center_inset = SUPPORT_RADIAL_INSET + SUPPORT_RADIAL_WIDTH / 2
    trough_inner_r = (
        mouth_inner_r
        + support_center_inset
        - SUPPORT_WAVE_AMPLITUDE
        - SUPPORT_WALL_THICKNESS / 2
    )
    peak_inner_r = (
        mouth_inner_r
        + support_center_inset
        + SUPPORT_WAVE_AMPLITUDE
        - SUPPORT_WALL_THICKNESS / 2
    )

    specs = []
    for index in range(SUPPORT_WAVE_COUNT):
        peak_theta = (0.5 * math.pi + math.tau * index) / SUPPORT_WAVE_COUNT
        trough_theta = (1.5 * math.pi + math.tau * index) / SUPPORT_WAVE_COUNT
        specs.extend(
            [
                (
                    peak_theta,
                    peak_inner_r - CRADLE_RIB_BASE_RADIAL_WIDTH,
                    peak_inner_r + CRADLE_RIB_TROUGH_OVERLAP,
                ),
                (
                    trough_theta,
                    trough_inner_r - CRADLE_RIB_BASE_RADIAL_WIDTH,
                    trough_inner_r + CRADLE_RIB_TROUGH_OVERLAP,
                ),
            ]
        )
    return sorted(specs)


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _z_shifted(shape, z_shift: float):
    return Location((0, 0, z_shift)) * shape


def _stl_lower_envelope_profile(
    path: Path,
    *,
    radial_min: float,
    radial_max: float,
    sample_count: int,
    search_window: float = 0.15,
) -> list[tuple[float, float]]:
    """Sample the lowest horn mesh vertex around each radius."""
    if sample_count < 8:
        raise ValueError("Contact profile needs at least eight samples")
    if radial_max <= radial_min:
        raise ValueError("Contact profile radial bounds are invalid")

    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + triangle_count * 50
    if expected != len(data):
        raise ValueError(f"{path} does not look like a binary STL")

    radial_pad = max(search_window * 2.5, 0.25)
    vertices: list[tuple[float, float]] = []
    offset = 84
    for _triangle in range(triangle_count):
        offset += 12
        for _vertex in range(3):
            x, y, z = struct.unpack_from("<fff", data, offset)
            offset += 12
            radius = math.hypot(x, y)
            if radial_min - radial_pad <= radius <= radial_max + radial_pad:
                vertices.append((radius, z))
        offset += 2
    if not vertices:
        raise ValueError("No STL vertices found in support contact band")

    profile: list[tuple[float, float]] = []
    for index in range(sample_count):
        t = index / (sample_count - 1)
        radius = radial_min + (radial_max - radial_min) * t
        window = search_window
        nearby: list[float] = []
        while not nearby and window <= 0.6:
            nearby = [z for point_r, z in vertices if abs(point_r - radius) <= window]
            window *= 1.6
        if not nearby:
            raise ValueError(f"No STL lower-envelope samples at radius {radius:.3f}")
        profile.append((radius, min(nearby)))
    return profile


def _export_step_and_stl(
    shape,
    stem: str,
    *,
    bed_z_shift: float,
    export_step_file: bool = True,
    export_bed_stl: bool = True,
    stl_tolerance: float = STL_LINEAR_TOLERANCE,
    stl_angular_tolerance: float = STL_ANGULAR_TOLERANCE,
) -> dict[str, str]:
    print(f"exporting {stem}...", flush=True)
    step = OUT / f"{stem}.step"
    bed_stl = OUT / f"{stem}_bed_oriented.stl"
    paths: dict[str, str] = {}
    if export_step_file:
        export_step(shape, step, unit=Unit.MM, write_pcurves=False)
        paths["step"] = str(step.resolve())
    if export_bed_stl:
        export_stl(
            _z_shifted(shape, bed_z_shift),
            bed_stl,
            tolerance=stl_tolerance,
            angular_tolerance=stl_angular_tolerance,
        )
        paths["bed_oriented_stl"] = str(bed_stl.resolve())
    return paths


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("building 220 mm experimental JMLC horn...", flush=True)
    horn_body = build_jmlc_horn(
        throat_d=p.horn_throat_d,
        mouth_outer_d=EXPERIMENTAL_MOUTH_OUTER_D,
        wall_t=p.horn_wall_t,
        exit_angle_deg=EXPERIMENTAL_EXIT_ANGLE_DEG,
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

    print("building experimental assist geometry...", flush=True)
    mouth_outer_r = EXPERIMENTAL_MOUTH_OUTER_D / 2
    mouth_inner_r = mouth_outer_r - p.horn_wall_t
    profile, _cutoff_hz = jmlc_profile_points(
        throat_d=p.horn_throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=EXPERIMENTAL_EXIT_ANGLE_DEG,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=p.horn_profile_step,
    )
    inner = [
        (radius, z - p.horn_flange_t - p.horn_bracket_t)
        for radius, z in profile
    ]
    mouth_z = inner[-1][1]
    horn = _primary_shape(horn_body.clean().fix())

    support_inner_r = mouth_inner_r + SUPPORT_RADIAL_INSET
    support_outer_r = support_inner_r + SUPPORT_RADIAL_WIDTH
    support_trough_inner_r = mouth_inner_r + SUPPORT_TROUGH_INNER_INSET
    cradle_inner_r = mouth_inner_r + CRADLE_RADIAL_INSET
    cradle_outer_r = cradle_inner_r + CRADLE_RADIAL_WIDTH
    del cradle_inner_r, cradle_outer_r
    contoured_contact_profile = None
    support_wall = build_corrugated_inner_lip_support(
        mouth_outer_d=EXPERIMENTAL_MOUTH_OUTER_D,
        wall_t=p.horn_wall_t,
        lip_r=p.horn_lip_r,
        mouth_z=mouth_z,
        bottom_z=-p.horn_flange_t - p.horn_bracket_t,
        interface_h=INTERFACE_H,
        radial_inset=SUPPORT_RADIAL_INSET,
        radial_width=SUPPORT_RADIAL_WIDTH,
        wall_thickness=SUPPORT_WALL_THICKNESS,
        wave_amplitude=SUPPORT_WAVE_AMPLITUDE,
        wave_count=SUPPORT_WAVE_COUNT,
        samples_per_wave=SUPPORT_SAMPLES_PER_WAVE,
        top_landing_h=1.20,
        top_inner_extra_r=0.0,
        hoop_spacing=22.0,
        include_intermediate_hoops=False,
        landing_vertical_drop=0.0,
    )
    print("building lightweight ribbed flared support cradle...", flush=True)
    inner_cradle, inner_interface, cradle_metadata = build_lightweight_flared_lip_cradle(
        profile=inner,
        wall_t=p.horn_wall_t,
        radial_inset=CRADLE_RADIAL_INSET,
        radial_width=CRADLE_RADIAL_WIDTH,
        rib_base_inner_r=support_trough_inner_r - CRADLE_RIB_BASE_RADIAL_WIDTH,
        rib_base_outer_r=support_trough_inner_r + CRADLE_RIB_TROUGH_OVERLAP,
        contact_profile=contoured_contact_profile,
        interface_h=INTERFACE_H,
        cap_h=CRADLE_CAP_H,
        rib_count=CRADLE_RIB_COUNT,
        rib_specs=_corrugation_peak_trough_rib_specs(mouth_inner_r),
        rib_tangential_width=CRADLE_RIB_TANGENTIAL_WIDTH,
        rib_rise_h=CRADLE_RIB_RISE_H,
        fairing_start_before_apex_mm=CONTACT_START_BEFORE_APEX_MM,
        fairing_max_extra_t=CONTACT_MAX_EXTRA_T,
        max_outer_clearance=CONTACT_MAX_OUTER_CLEARANCE,
        sample_count=CONTACT_PROFILE_SAMPLES,
        radial_sample_count=CRADLE_RADIAL_BANDS,
    )
    print("building contoured outer landing over corrugated wall...", flush=True)
    outer_landing, outer_interface, outer_landing_metadata = build_contoured_lip_cradle(
        profile=inner,
        wall_t=p.horn_wall_t,
        radial_inset=OUTER_LANDING_RADIAL_INSET,
        radial_width=OUTER_LANDING_RADIAL_WIDTH,
        contact_profile=contoured_contact_profile,
        interface_h=INTERFACE_H,
        cradle_base_overlap_h=OUTER_LANDING_BASE_OVERLAP_H,
        fairing_start_before_apex_mm=CONTACT_START_BEFORE_APEX_MM,
        fairing_max_extra_t=CONTACT_MAX_EXTRA_T,
        max_outer_clearance=CONTACT_MAX_OUTER_CLEARANCE,
        sample_count=CONTACT_PROFILE_SAMPLES,
        radial_band_count=max(12, CRADLE_RADIAL_BANDS // 2),
        use_smooth_revolve=True,
    )
    pla_cradle = Compound(
        children=[*inner_cradle.solids(), *outer_landing.solids()]
    )
    interface_cap = Compound(
        children=[*inner_interface.solids(), *outer_interface.solids()]
    )
    support = Compound(
        children=[*support_wall.solids(), *pla_cradle.solids()]
    )
    rear_flange_support = build_rear_flange_support_ring(
        flange_d=p.horn_flange_d,
        flange_t=p.horn_flange_t,
        rear_spigot_l=p.horn_bracket_t,
        rear_spigot_od=p.horn_spigot_od,
        outer_inset=1.10,
        interface_h=0.40,
    )
    rear_flange_interface = build_rear_flange_petg_interface_ring(
        flange_d=p.horn_flange_d,
        flange_t=p.horn_flange_t,
        rear_spigot_l=p.horn_bracket_t,
        rear_spigot_od=p.horn_spigot_od,
        outer_inset=1.10,
        interface_h=0.40,
    )
    assembly = Compound(
        children=[
            *horn.solids(),
            *support.solids(),
            *interface_cap.solids(),
            *rear_flange_support.solids(),
            *rear_flange_interface.solids(),
        ]
    )

    print("exporting STEP/STL files...", flush=True)
    bed_z_shift = -assembly.bounding_box().min.Z
    output_paths = {
        "horn": _export_step_and_stl(
            horn,
            f"experimental_jmlc_horn_print_assist_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
        ),
        "accordion_support_wall_pla": _export_step_and_stl(
            support_wall,
            f"experimental_jmlc_horn_accordion_support_wall_pla_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "inner_flare_cradle_pla": _export_step_and_stl(
            inner_cradle,
            f"experimental_jmlc_horn_inner_flare_cradle_pla_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "outer_landing_cradle_pla": _export_step_and_stl(
            outer_landing,
            f"experimental_jmlc_horn_outer_landing_cradle_pla_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "inner_flare_interface_skin": _export_step_and_stl(
            inner_interface,
            f"experimental_jmlc_horn_inner_flare_bambu_support_interface_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "outer_landing_interface_skin": _export_step_and_stl(
            outer_interface,
            f"experimental_jmlc_horn_outer_landing_bambu_support_interface_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "rear_flange_support_pla": _export_step_and_stl(
            rear_flange_support,
            f"experimental_jmlc_horn_rear_flange_support_ring_pla_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "rear_flange_interface_skin": _export_step_and_stl(
            rear_flange_interface,
            f"experimental_jmlc_horn_rear_flange_interface_skin_{VERSION}",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            stl_tolerance=0.02,
            stl_angular_tolerance=0.08,
        ),
        "assembly": _export_step_and_stl(
            assembly,
            f"experimental_jmlc_horn_print_assist_accordion_{VERSION}_assembly",
            bed_z_shift=bed_z_shift,
            export_step_file=False,
            export_bed_stl=False,
        ),
    }
    print("writing diagnostics...", flush=True)
    horn_data = horn_dimensions(horn)
    horn_data.update(
        jmlc_profile_metadata(
            throat_d=p.horn_throat_d,
            mouth_outer_d=EXPERIMENTAL_MOUTH_OUTER_D,
            wall_t=p.horn_wall_t,
            exit_angle_deg=EXPERIMENTAL_EXIT_ANGLE_DEG,
            wavefront_t=p.horn_wavefront_t,
            throat_angle_deg=p.horn_throat_angle_deg,
            step=p.horn_profile_step,
        )
    )
    diagnostics = {
        "design": (
            "Experimental 220 mm target horn generated directly from the "
            "Le Cleac'h / JMLC recurrence with a more dramatic 150 degree "
            "rolled-back exit angle. V20 "
            "keeps the corrugated PLA support footprint narrow at the bed, "
            "then carries a 16 mm inward flare with radial buttress ribs and "
            "a continuous top cap. V20 keeps the coarser 20-wave exterior, "
            "but doubles the hidden inward ribs so they alternate between "
            "corrugation troughs and peaks. That keeps the outer wall visually "
            "coarser while reducing the unsupported cap spans before the "
            "support-material interface prints. A narrow contoured outer landing "
            "sits only above the corrugated wall band so the lip is still "
            "supported without resurrecting the full V18 annular flare. "
            "The rear-flange support washer "
            "continues to use a 0.4 mm support-material interface skin."
        ),
        "recommended_materials": {
            "horn": "Bambu PLA Matte",
            "accordion_support_wall_and_cradle_pla": "Bambu PLA Matte",
            "support_interface_skin": "Bambu Support for PLA/PETG",
            "rear_flange_support_pla": "Bambu PLA Matte",
            "rear_flange_interface_skin": "Bambu Support for PLA/PETG",
        },
        "horn": horn_data,
        "accordion_support_wall": {
            "bbox": _bbox(support_wall),
            "solids": len(support_wall.solids()),
            "is_valid": bool(support_wall.is_valid),
            "volume_mm3": round(support_wall.volume, 3),
            "wave_count": SUPPORT_WAVE_COUNT,
            "radial_width_mm": SUPPORT_RADIAL_WIDTH,
            "wall_thickness_mm": SUPPORT_WALL_THICKNESS,
            "wave_amplitude_mm": round(SUPPORT_WAVE_AMPLITUDE, 3),
            "radial_inset_mm": round(SUPPORT_RADIAL_INSET, 3),
            "trough_inner_radius_mm": round(support_trough_inner_r, 3),
            "outer_landing_radial_width_mm": round(
                OUTER_LANDING_RADIAL_WIDTH, 3
            ),
            "planned_cradle_inner_flare_r_mm": TOP_SUPPORT_INNER_EXTRA_R,
            "planned_cradle_rib_count": CRADLE_RIB_COUNT,
            "cradle_rib_anchor_pattern": "alternating_peak_and_trough",
            "intermediate_hoops": False,
            "closure": "closed_outer_loop_with_inner_hole_no_intentional_gaps",
        },
        "contoured_cradle_pla": {
            "bbox": _bbox(pla_cradle),
            "solids": len(pla_cradle.solids()),
            "is_valid": bool(pla_cradle.is_valid),
            "volume_mm3": round(pla_cradle.volume, 3),
            "contact_profile_source": "analytic_jmlc_rolled_wall_lower_envelope",
            "contact_profile_samples": CONTACT_PROFILE_SAMPLES,
            **{
                key: round(value, 3)
                for key, value in cradle_metadata.items()
            },
            "outer_landing": {
                key: round(value, 3)
                for key, value in outer_landing_metadata.items()
            },
        },
        "stl_export": {
            "horn_linear_tolerance_mm": STL_LINEAR_TOLERANCE,
            "horn_angular_tolerance_rad": STL_ANGULAR_TOLERANCE,
            "sacrificial_support_linear_tolerance_mm": 0.02,
            "sacrificial_support_angular_tolerance_rad": 0.08,
        },
        "support_interface_skin": {
            "bbox": _bbox(interface_cap),
            "solids": len(interface_cap.solids()),
            "is_valid": bool(interface_cap.is_valid),
            "volume_mm3": round(interface_cap.volume, 3),
        },
        "support_contact_model": {
            "kind": "analytic lower envelope of the 150 degree JMLC rolled wall",
            "start_before_apex_mm": CONTACT_START_BEFORE_APEX_MM,
            "max_extra_thickness_mm": CONTACT_MAX_EXTRA_T,
            "max_outer_clearance_mm": CONTACT_MAX_OUTER_CLEARANCE,
        },
        "rear_flange_support": {
            "bbox": _bbox(rear_flange_support),
            "solids": len(rear_flange_support.solids()),
            "is_valid": bool(rear_flange_support.is_valid),
            "volume_mm3": round(rear_flange_support.volume, 3),
        },
        "rear_flange_interface_skin": {
            "bbox": _bbox(rear_flange_interface),
            "solids": len(rear_flange_interface.solids()),
            "is_valid": bool(rear_flange_interface.is_valid),
            "volume_mm3": round(rear_flange_interface.volume, 3),
        },
        "assembly": {
            "bbox": _bbox(assembly),
            "solids": len(assembly.solids()),
            "volume_mm3": round(assembly.volume, 3),
        },
        "targets": {
            "printed_outer_d_mm": TARGET_PRINTED_OUTER_D,
            "construction_mouth_outer_d_mm": EXPERIMENTAL_MOUTH_OUTER_D,
            "exit_angle_deg": EXPERIMENTAL_EXIT_ANGLE_DEG,
        },
        "outputs": output_paths,
    }
    (OUT / f"diagnostics_{VERSION}.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
