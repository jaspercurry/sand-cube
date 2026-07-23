"""Export the compact 6 in sand-filled speaker CAD."""

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

from build123d import Compound, Unit  # noqa: E402

from src.cad_io import export_step  # noqa: E402
from src.compact_6in.enclosure import build as build_enclosure  # noqa: E402
from src.compact_6in.horn import build as build_horn  # noqa: E402
from src.compact_6in.horn import build_f110m_envelope  # noqa: E402
from src.compact_6in.horn import place_above_enclosure  # noqa: E402


OUT = ROOT / "build" / "compact_6in"


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    enclosure, enclosure_data = build_enclosure()
    horn, horn_data = build_horn()
    f110m, f110m_data = build_f110m_envelope()
    horn_fit_stack = Compound(children=[horn, f110m])
    placed_horn = place_above_enclosure(enclosure, horn)
    placed_fit_stack = place_above_enclosure(enclosure, horn_fit_stack)
    system_preview = Compound(children=[enclosure, placed_fit_stack])

    files = {
        "enclosure": OUT / "compact_6in_one_piece_enclosure.step",
        "horn": OUT / "compact_6in_f110m_jmlc_horn.step",
        "f110m_fit_envelope": OUT / "compact_6in_f110m_fit_envelope.step",
        "horn_placed": OUT / "compact_6in_f110m_jmlc_horn_placed.step",
        "horn_f110m_fit_stack": OUT / "compact_6in_horn_f110m_fit_stack.step",
        "system_preview": OUT / "compact_6in_system_preview.step",
    }
    export_step(enclosure, files["enclosure"], unit=Unit.MM)
    export_step(horn, files["horn"], unit=Unit.MM, write_pcurves=False)
    export_step(f110m, files["f110m_fit_envelope"], unit=Unit.MM)
    export_step(placed_horn, files["horn_placed"], unit=Unit.MM, write_pcurves=False)
    export_step(
        placed_fit_stack,
        files["horn_f110m_fit_stack"],
        unit=Unit.MM,
        write_pcurves=False,
    )
    export_step(
        system_preview,
        files["system_preview"],
        unit=Unit.MM,
        write_pcurves=False,
    )

    notes = {
        "purpose": "Compact 6 in one-piece sand-filled cube plus separate F110M-targeted 6 in JMLC horn.",
        "files": {key: str(path) for key, path in files.items()},
        "enclosure": enclosure_data,
        "horn": horn_data,
        "f110m_fit_envelope": f110m_data,
        "bounding_boxes": {
            "enclosure": _bbox(enclosure),
            "horn": _bbox(horn),
            "f110m_fit_envelope": _bbox(f110m),
            "horn_placed": _bbox(placed_horn),
            "horn_f110m_fit_stack": _bbox(placed_fit_stack),
            "system_preview": _bbox(system_preview),
        },
        "checks": {
            "enclosure_valid": enclosure_data["is_valid"],
            "horn_valid": horn_data["is_valid"],
            "f110m_fit_envelope_valid": f110m_data["is_valid"],
            "enclosure_single_solid": enclosure_data["checks"]["single_solid"],
            "horn_single_solid": horn_data["checks"]["single_solid"],
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(notes, indent=2))
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
