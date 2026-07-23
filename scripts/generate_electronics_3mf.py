"""Export focused electronics enclosure printable 3MF files."""

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

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import Location, Mesher, Shape, Unit

from src.features.electronics import (
    DEFAULT_CONFIG,
    PrintedConfig,
    active_layout_variants,
    build_thin_plate_printed_parts,
)


OUT = ROOT / "build" / "electronics_enclosure"

PLA_PRINT_PROFILE = {
    "material": "PLA",
    "nozzle_d_mm": 0.4,
    "layer_height_mm": 0.2,
    "walls": 4,
    "top_layers": 5,
    "bottom_layers": 5,
    "infill_percent": 20,
    "infill_pattern": "gyroid",
    "supports": "none expected",
    "brim": "optional for lid corners if adhesion is marginal",
    "notes": [
        "Print parts in the orientation exported: large flat faces on the bed.",
        "Use normal PLA temperatures for the chosen filament.",
        (
            "Settings are embedded as generic 3MF metadata; slicers may not "
            "auto-apply them."
        ),
    ],
}

FAST_FIT_CONFIG = PrintedConfig(
    wall_t=1.6,
    floor_t=1.6,
    roof_t=1.6,
    front_wall_t=1.6,
    vent_d=5.0,
    vent_pitch=22.0,
    vent_edge_margin=18.0,
)

FAST_FIT_PRINT_PROFILE = {
    "material": "PLA",
    "nozzle_d_mm": 0.4,
    "layer_height_mm": 0.28,
    "walls": 2,
    "top_layers": 3,
    "bottom_layers": 3,
    "infill_percent": 8,
    "infill_pattern": "gyroid",
    "supports": "none expected",
    "brim": "optional if the thin shell corners lift",
    "notes": [
        "Fast fit-check profile for a standard 0.4 mm nozzle.",
        "Use this to validate component placement, not final durability.",
        "Settings are embedded as generic 3MF metadata; slicers may not auto-apply them.",
    ],
}


def _drop_to_bed(shape: Shape) -> Shape:
    bb = shape.bounding_box()
    return Location((0, 0, -bb.min.Z)) * shape


def _bbox(shape: Shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _export_3mf(
    shape: Shape,
    path: Path,
    *,
    part_name: str,
    print_profile: dict[str, object],
    metadata: dict[str, object],
) -> None:
    mesher = Mesher(unit=Unit.MM)
    mesher.add_shape(
        shape,
        linear_deflection=0.08,
        angular_deflection=0.12,
        part_number=part_name,
    )
    mesher.add_meta_data(
        name_space="sand-cube-electronics",
        name="material",
        value="PLA",
        metadata_type="str",
        must_preserve=False,
    )
    mesher.add_meta_data(
        name_space="sand-cube-electronics",
        name="print_profile",
        value=json.dumps(print_profile, sort_keys=True),
        metadata_type="str",
        must_preserve=False,
    )
    mesher.add_meta_data(
        name_space="sand-cube-electronics",
        name="part_notes",
        value=json.dumps(metadata, sort_keys=True),
        metadata_type="str",
        must_preserve=False,
    )
    mesher.write(str(path))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    variant = active_layout_variants()[0]
    base, lid, _plate_assembly, plate_notes = build_thin_plate_printed_parts(
        variant,
        DEFAULT_CONFIG,
    )
    fast_base, fast_lid, _fast_assembly, fast_notes = build_thin_plate_printed_parts(
        variant,
        FAST_FIT_CONFIG,
    )

    base_on_bed = _drop_to_bed(base)
    lid_on_bed = _drop_to_bed(lid)
    fast_base_on_bed = _drop_to_bed(fast_base)
    fast_lid_on_bed = _drop_to_bed(fast_lid)

    files = {
        "base_with_standoffs": OUT
        / "thin_plate_inline_separate_mic_base_with_standoffs.3mf",
        "screw_on_lid": OUT / "thin_plate_inline_separate_mic_screw_on_lid.3mf",
        "fast_fit_base": OUT
        / "thin_plate_inline_separate_mic_fast_fit_base.3mf",
        "fast_fit_lid": OUT / "thin_plate_inline_separate_mic_fast_fit_lid.3mf",
    }
    _export_3mf(
        base_on_bed,
        files["base_with_standoffs"],
        part_name="thin-plate-base-with-standoffs",
        print_profile=PLA_PRINT_PROFILE,
        metadata={
            "variant": variant.name,
            "part": "base_with_standoffs",
            "bbox_mm": _bbox(base_on_bed),
            "print_profile": PLA_PRINT_PROFILE,
            "design_notes": plate_notes.get("base", {}),
        },
    )
    _export_3mf(
        lid_on_bed,
        files["screw_on_lid"],
        part_name="thin-plate-screw-on-lid",
        print_profile=PLA_PRINT_PROFILE,
        metadata={
            "variant": variant.name,
            "part": "screw_on_lid",
            "bbox_mm": _bbox(lid_on_bed),
            "print_profile": PLA_PRINT_PROFILE,
            "design_notes": plate_notes.get("lid", {}),
        },
    )
    _export_3mf(
        fast_base_on_bed,
        files["fast_fit_base"],
        part_name="thin-plate-fast-fit-base",
        print_profile=FAST_FIT_PRINT_PROFILE,
        metadata={
            "variant": variant.name,
            "part": "fast_fit_base",
            "bbox_mm": _bbox(fast_base_on_bed),
            "printed_config": {
                "wall_t_mm": FAST_FIT_CONFIG.wall_t,
                "floor_t_mm": FAST_FIT_CONFIG.floor_t,
                "roof_t_mm": FAST_FIT_CONFIG.roof_t,
                "front_wall_t_mm": FAST_FIT_CONFIG.front_wall_t,
            },
            "print_profile": FAST_FIT_PRINT_PROFILE,
            "design_notes": fast_notes.get("base", {}),
        },
    )
    _export_3mf(
        fast_lid_on_bed,
        files["fast_fit_lid"],
        part_name="thin-plate-fast-fit-lid",
        print_profile=FAST_FIT_PRINT_PROFILE,
        metadata={
            "variant": variant.name,
            "part": "fast_fit_lid",
            "bbox_mm": _bbox(fast_lid_on_bed),
            "printed_config": {
                "wall_t_mm": FAST_FIT_CONFIG.wall_t,
                "floor_t_mm": FAST_FIT_CONFIG.floor_t,
                "roof_t_mm": FAST_FIT_CONFIG.roof_t,
                "front_wall_t_mm": FAST_FIT_CONFIG.front_wall_t,
            },
            "print_profile": FAST_FIT_PRINT_PROFILE,
            "design_notes": fast_notes.get("lid", {}),
        },
    )
    notes = {
        "purpose": "Printable 3MF exports for the focused electronics plate.",
        "material": "PLA",
        "print_profile": PLA_PRINT_PROFILE,
        "fast_fit": {
            "purpose": (
                "Thin, quick layout validation geometry with the same critical "
                "component placement and rear-panel fit features."
            ),
            "printed_config": {
                "wall_t_mm": FAST_FIT_CONFIG.wall_t,
                "floor_t_mm": FAST_FIT_CONFIG.floor_t,
                "roof_t_mm": FAST_FIT_CONFIG.roof_t,
                "front_wall_t_mm": FAST_FIT_CONFIG.front_wall_t,
            },
            "print_profile": FAST_FIT_PRINT_PROFILE,
        },
        "files": {key: str(path) for key, path in files.items()},
        "bounding_boxes": {
            "base_with_standoffs": _bbox(base_on_bed),
            "screw_on_lid": _bbox(lid_on_bed),
            "fast_fit_base": _bbox(fast_base_on_bed),
            "fast_fit_lid": _bbox(fast_lid_on_bed),
        },
    }
    notes_path = OUT / "electronics_3mf_notes.json"
    notes_path.write_text(json.dumps(notes, indent=2))
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
