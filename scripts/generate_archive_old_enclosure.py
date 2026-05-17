"""Regenerate the archived 203 mm Sand Cube enclosure outputs."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import Unit, export_step

from archive import old_enclosure


OUT = ROOT / "build" / "archive" / "old_enclosure"


def main() -> None:
    """Export the archived old enclosure, plug, horn, and preview assembly."""
    OUT.mkdir(parents=True, exist_ok=True)

    enclosure = old_enclosure.build()
    fill_plug = old_enclosure.build_fill_plug()
    horn = old_enclosure.build_horn()
    assembly = old_enclosure.build_enclosure_horn_assembly(enclosure, horn)

    enclosure_data = old_enclosure.diagnostics(enclosure)
    horn_data = old_enclosure.horn_dimensions(horn)
    horn_data.update(
        old_enclosure.jmlc_profile_metadata(
            throat_d=old_enclosure.p.horn_throat_d,
            mouth_outer_d=old_enclosure.p.horn_mouth_outer_d,
            wall_t=old_enclosure.p.horn_wall_t,
            exit_angle_deg=old_enclosure.p.horn_exit_angle_deg,
            wavefront_t=old_enclosure.p.horn_wavefront_t,
            throat_angle_deg=old_enclosure.p.horn_throat_angle_deg,
            step=old_enclosure.p.horn_profile_step,
        )
    )

    export_step(enclosure, OUT / "old_sand_cube_203mm.step", unit=Unit.MM)
    export_step(fill_plug, OUT / "old_sand_fill_plug.step", unit=Unit.MM)
    export_step(
        horn,
        OUT / "old_jmlc_horn.step",
        unit=Unit.MM,
        write_pcurves=False,
    )
    export_step(
        assembly,
        OUT / "old_sand_cube_with_horn.step",
        unit=Unit.MM,
        write_pcurves=False,
    )

    notes = {
        "purpose": "Archived 203 mm enclosure outputs for comparison.",
        "files": {
            "enclosure": str(OUT / "old_sand_cube_203mm.step"),
            "fill_plug": str(OUT / "old_sand_fill_plug.step"),
            "horn": str(OUT / "old_jmlc_horn.step"),
            "assembly": str(OUT / "old_sand_cube_with_horn.step"),
        },
        "enclosure": enclosure_data,
        "horn": horn_data,
    }
    (OUT / "diagnostics.json").write_text(json.dumps(notes, indent=2))
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
