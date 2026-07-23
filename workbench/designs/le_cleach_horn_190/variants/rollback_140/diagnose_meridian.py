"""Check center-plane connectivity in the exported 140-degree horn STEP."""

from __future__ import annotations

# ruff: noqa: E402


# This guard must remain before all native CAD imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json

from build123d import Plane, import_step, section

from cad_runner.outputs import job_output_path


ROOT = _CAD_SAFETY_ROOT
STEP_PATH = (
    ROOT
    / "build/workbench/le_cleach_horn_190/variants/rollback_140/"
    "le_cleach_horn_190_rollback_140.step"
)
OUTPUT_PATH = (
    ROOT
    / "build/workbench/le_cleach_horn_190/variants/rollback_140/"
    "meridian_diagnostics.json"
)


def main() -> None:
    horn = import_step(STEP_PATH)
    meridian = section(horn, section_by=Plane.YZ)
    faces = list(meridian.faces())
    wires = list(meridian.wires())
    diagnostics = {
        "step": (
            "build/workbench/le_cleach_horn_190/variants/rollback_140/"
            "le_cleach_horn_190_rollback_140.step"
        ),
        "plane": "YZ at X=0",
        "face_count": len(faces),
        "wire_count": len(wires),
        "all_faces_valid": all(bool(face.is_valid) for face in faces),
        "all_faces_positive_area": all(face.area > 0.0 for face in faces),
        "face_areas_mm2": [face.area for face in faces],
        "all_wires_closed": all(wire.is_closed for wire in wires),
        "wire_lengths_mm": [wire.length for wire in wires],
    }
    diagnostics["passed"] = (
        diagnostics["face_count"] == 2
        and diagnostics["wire_count"] == 2
        and diagnostics["all_faces_valid"]
        and diagnostics["all_faces_positive_area"]
        and diagnostics["all_wires_closed"]
    )
    output = job_output_path(OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    if not diagnostics["passed"]:
        raise SystemExit("Horn meridian connectivity check failed")


if __name__ == "__main__":
    main()
