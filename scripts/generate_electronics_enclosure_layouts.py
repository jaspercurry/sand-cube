"""Export first-pass electronics enclosure layout studies."""

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

from build123d import Unit

from src.cad_io import export_step
from src.features.electronics import (
    DEFAULT_CONFIG,
    active_layout_variants,
    archived_layout_variants,
    build_layout_assembly,
    build_printed_enclosure,
    build_thin_plate_printed_parts,
    researched_sources,
)


OUT = ROOT / "build" / "electronics_enclosure"


def main() -> None:
    """Export STEP studies and a machine-readable layout summary."""
    OUT.mkdir(parents=True, exist_ok=True)

    variants = {}
    for variant in active_layout_variants():
        enclosure, enclosure_notes = build_printed_enclosure(variant, DEFAULT_CONFIG)
        assembly, assembly_notes = build_layout_assembly(variant, DEFAULT_CONFIG)

        enclosure_path = OUT / f"{variant.name}_printed_enclosure.step"
        assembly_path = OUT / f"{variant.name}_electronics_assembly.step"
        export_step(
            enclosure,
            enclosure_path,
            unit=Unit.MM,
            write_pcurves=False,
        )
        export_step(
            assembly,
            assembly_path,
            unit=Unit.MM,
            write_pcurves=False,
        )
        files = {
            "printed_enclosure": str(enclosure_path),
            "assembly": str(assembly_path),
        }
        if variant.name == "thin_plate_inline_separate_mic":
            base, lid, _printed, _thin_notes = build_thin_plate_printed_parts(
                variant,
                DEFAULT_CONFIG,
            )
            base_path = OUT / f"{variant.name}_base_with_standoffs.step"
            lid_path = OUT / f"{variant.name}_screw_on_lid.step"
            export_step(
                base,
                base_path,
                unit=Unit.MM,
                write_pcurves=False,
            )
            export_step(
                lid,
                lid_path,
                unit=Unit.MM,
                write_pcurves=False,
            )
            files["base_with_standoffs"] = str(base_path)
            files["screw_on_lid"] = str(lid_path)
        variants[variant.name] = {
            **assembly_notes,
            "files": files,
            "printed_only": enclosure_notes,
        }

    summary = {
        "purpose": (
            "First-pass packaging study for amp, Raspberry Pi 5 with DAC8x-style "
            "HAT clearance, buck converter, and optional separate 100 mm mic puck."
        ),
        "assumptions": {
            "units": "millimeters",
            "rear": (
                "closed rear panel on the active thin plate with Pi, GX14, and "
                "buck wire-entry cutouts"
            ),
            "top": "closed roof with simple staggered round ventilation holes",
            "standoffs": (
                "rough printed bosses/pegs for fit study; not yet screw-ready "
                "production details"
            ),
            "wire_clearances": {
                "amp_signal_exit": 18.0,
                "buck_end_clearance": 18.0,
                "rear_buck_vertical_body": 58.0,
                "rear_buck_bottom_wire_entry": (
                    "Buck wires bend 90 degrees downward and enter through the "
                    "bottom edge of the rear panel."
                ),
            },
            "dac8x": (
                "No independent DAC8x mechanical drawing was found during this pass; "
                "the active model uses a narrower Pi service envelope with the HAT "
                "allowed to overhang above the amp input side, plus the official "
                "Raspberry Pi HAT mounting pattern."
            ),
            "separate_mic": (
                "Thin hidden-plate variants remove the mic from the electronics "
                "enclosure and pair with a separate low-profile horizontal mic puck."
            ),
        },
        "sources": researched_sources(),
        "separate_mic": {
            "status": "deferred",
            "note": (
                "The active print set omits the mic puck. Keep the microphone "
                "external/separate for now and revisit after the plate fit is good."
            ),
        },
        "archived_variants": [
            variant.name for variant in archived_layout_variants()
        ],
        "variants": variants,
        "recommendation": {
            "best_first_print": "thin_plate_inline_separate_mic",
            "why": (
                "It fits inside a 256 mm square bed target with margin, keeps the "
                "thin hidden-plate format, exposes the Pi side near the rear "
                "panel, and moves the buck onto the rear wall instead of over "
                "the amp input area."
            ),
            "risk": (
                "The rear-mounted buck location is a fit concept. Keep the "
                "switching converter wiring short/twisted and validate audio "
                "noise before committing to a final printed routing."
            ),
        },
    }
    notes_path = OUT / "electronics_enclosure_layouts.json"
    notes_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
