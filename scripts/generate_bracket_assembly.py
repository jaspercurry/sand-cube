"""Generate legacy 203 mm horn bracket assembly previews.

The current full-system export uses ``scripts/generate_final_system_assembly.py``
so it can start from the validated 8.5 in enclosure with inserts, PR, GX16, and
woofer hardware. This script is retained as a historical bracket preview for
the archived 203 mm enclosure.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import Compound, Location, Rot, Unit, export_step, import_step

from params import p
from src.enclosure import build, build_horn, place_horn_above_enclosure
from src.features.bracket import build_binding_post_grommet, build_horn_bracket


OUT = ROOT / "build" / "bracket"
MATERIAL_T = p.horn_bracket_t
HARDWARE_CLEARANCE = 0.05
GROMMET_WASHER_T = 2.0


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _confirmed_woofer():
    half = p.cube_outer / 2
    front_mount_y = -half + p.front_cap_t
    raw_mount_face_y = 110.5
    return (
        Location((0, (front_mount_y + HARDWARE_CLEARANCE) - (-raw_mount_face_y), 0))
        * (Rot(0, 45, 0) * Rot(180, 0, 0) * import_step(ROOT / "objects" / "E150HE-44.step"))
    )


def _confirmed_passive_radiator():
    half = p.cube_outer / 2
    raw_outer_flange_y = 115.7
    return (
        Location((0, (half + HARDWARE_CLEARANCE) - raw_outer_flange_y, 0))
        * (Rot(0, -30, 0) * import_step(ROOT / "objects" / "E180HE-PR.step"))
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    enclosure = build()
    horn = Rot(0, 0, -60) * build_horn()
    placed_horn = place_horn_above_enclosure(enclosure, horn, clearance=10.0)
    horn_bb = placed_horn.bounding_box()
    enclosure_bb = enclosure.bounding_box()
    horn_center_x = (horn_bb.min.X + horn_bb.max.X) / 2
    horn_center_z = (horn_bb.min.Z + horn_bb.max.Z) / 2
    horn_driver_face_y = horn_bb.max.Y
    bracket_front_y = horn_driver_face_y - MATERIAL_T

    bracket = build_horn_bracket(
        enclosure_top_z=enclosure_bb.max.Z,
        horn_rear_y=bracket_front_y,
        horn_center_z=horn_center_z,
        material_t=MATERIAL_T,
        top_bolt_spacing=p.bracket_hole_spacing,
        top_bolt_y=p.bracket_hole_y,
        binding_post_spacing=p.binding_post_spacing,
        binding_post_y=p.binding_post_y,
        acoustic_hole_d=p.horn_bracket_throat_clearance_d,
        horn_bolt_d=p.horn_bolt_clearance_d,
        horn_bolt_3_bcd=p.horn_bolt_3_bcd,
        horn_bolt_2_bcd=p.horn_bolt_2_bcd,
    )
    grommet = build_binding_post_grommet(
        washer_t=GROMMET_WASHER_T,
        sleeve_l=p.outer_skin_t + p.void_t + p.inner_skin_t + MATERIAL_T,
    )
    bracket_top_z = enclosure_bb.max.Z + MATERIAL_T
    grommets = [
        Location((x, p.binding_post_y, bracket_top_z)) * grommet
        for x in (-p.binding_post_spacing / 2, p.binding_post_spacing / 2)
    ]

    comp_raw = import_step(ROOT / "objects" / "Compression DriverDE250.step")
    compression_driver = (
        Location((horn_center_x, horn_driver_face_y, horn_center_z))
        * (Rot(90, 0, 0) * comp_raw)
    )

    woofer = _confirmed_woofer()
    passive_radiator = _confirmed_passive_radiator()

    bracket_path = OUT / "horn_bracket_4mm_folded.step"
    grommet_path = OUT / "binding_post_tpu_grommet.step"
    bracket_preview_path = OUT / "sand_cube_horn_bracket_preview.step"
    full_preview_path = OUT / "sand_cube_horn_bracket_all_hardware.step"

    export_step(bracket, bracket_path, unit=Unit.MM, write_pcurves=False)
    export_step(grommet, grommet_path, unit=Unit.MM, write_pcurves=False)
    export_step(
        Compound(
            children=[
                enclosure,
                placed_horn,
                bracket,
                *grommets,
                *compression_driver.solids(),
            ]
        ),
        bracket_preview_path,
        unit=Unit.MM,
        write_pcurves=False,
    )
    export_step(
        Compound(
            children=[
                enclosure,
                placed_horn,
                bracket,
                *grommets,
                *compression_driver.solids(),
                *woofer.solids(),
                *passive_radiator.solids(),
            ]
        ),
        full_preview_path,
        unit=Unit.MM,
        write_pcurves=False,
    )

    notes = {
        "material_t_mm": MATERIAL_T,
        "material_recommendation": "Prototype in 4 mm 5052 aluminum; move to stainless only after fit is confirmed.",
        "files": {
            "bracket_only": str(bracket_path),
            "binding_post_grommet": str(grommet_path),
            "bracket_preview": str(bracket_preview_path),
            "full_preview": str(full_preview_path),
        },
        "interfaces": {
            "top_mount_holes": {
                "dedicated_screws": 2,
                "binding_posts_as_rear_clamps": 2,
                "front_screw_x_spacing_mm": p.bracket_hole_spacing,
                "front_screw_y_mm": p.bracket_hole_y - p.bracket_hole_spacing / 2,
                "binding_post_spacing_mm": p.binding_post_spacing,
                "binding_post_y_mm": p.binding_post_y,
                "hole_d_mm": 5.5,
            },
            "binding_post_grommet": {
                "material": "TPU",
                "washer_t_mm": GROMMET_WASHER_T,
                "washer_d_mm": 13.0,
                "sleeve_od_mm": 6.2,
                "bore_d_mm": 4.3,
                "sleeve_l_mm": p.outer_skin_t + p.void_t + p.inner_skin_t + MATERIAL_T,
            },
            "horn_mount": {
                "active_pattern": "B&C DE250 3-bolt pattern",
                "bolt_3_bcd_mm": p.horn_bolt_3_bcd,
                "bolt_2_bcd_mm": p.horn_bolt_2_bcd,
                "hole_d_mm": p.horn_bolt_clearance_d,
                "angles_deg": [30, 150, 270, -60, 120],
                "acoustic_hole_d_mm": p.horn_bracket_throat_clearance_d,
                "printed_spigot_od_mm": p.horn_spigot_od,
                "printed_spigot_l_mm": p.horn_bracket_t,
                "bracket_front_y_mm": round(bracket_front_y, 3),
                "compression_driver_face_y_mm": round(horn_driver_face_y, 3),
            },
            "horn_front_flush_y_mm": round(placed_horn.bounding_box().min.Y, 3),
            "enclosure_front_y_mm": round(enclosure_bb.min.Y, 3),
            "horn_clearance_above_top_mm": round(horn_bb.min.Z - enclosure_bb.max.Z, 3),
        },
        "bounding_boxes": {
            "bracket": _bbox(bracket),
            "grommet": _bbox(grommet),
            "preview": _bbox(
                Compound(
                    children=[
                        enclosure,
                        placed_horn,
                        bracket,
                        *grommets,
                        *compression_driver.solids(),
                    ]
                )
            ),
            "full_preview": _bbox(
                Compound(
                    children=[
                        enclosure,
                        placed_horn,
                        bracket,
                        *grommets,
                        *compression_driver.solids(),
                        *woofer.solids(),
                        *passive_radiator.solids(),
                    ]
                )
            ),
        },
    }
    (OUT / "horn_bracket_notes.json").write_text(json.dumps(notes, indent=2))
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
