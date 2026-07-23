"""Generate explicit fine-mesh review sidecars for the splice comparison."""

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
from cad_runner.outputs import STAGE_ROOT_ENV, job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys


ROOT = _CAD_SAFETY_ROOT
REVIEW_ROOT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/review"
)
TEXT_TO_CAD_ROOT = Path(os.environ["TEXT_TO_CAD_ROOT"]).resolve()
CADPY_SRC = TEXT_TO_CAD_ROOT / "packages/cadpy/src"
if str(CADPY_SRC) not in sys.path:
    sys.path.insert(0, str(CADPY_SRC))

from cadpy.step_artifact import main as step_artifact_main


LINEAR_DEFLECTION_MM = 0.01
ANGULAR_DEFLECTION_RAD = 0.03
INPUTS = {
    "earlier_flat_bottom_baffle": (
        REVIEW_ROOT / "earlier_flat_bottom_baffle.step",
        "part",
    ),
    "current_spliced_baffle": (
        REVIEW_ROOT / "current_spliced_baffle.step",
        "part",
    ),
    "candidate_trimmed_unspliced_baffle": (
        REVIEW_ROOT / "candidate_trimmed_unspliced_baffle.step",
        "part",
    ),
    "candidate_trimmed_unspliced_gasket": (
        REVIEW_ROOT / "candidate_trimmed_unspliced_gasket.step",
        "part",
    ),
    "candidate_trimmed_unspliced_assembly": (
        REVIEW_ROOT / "candidate_trimmed_unspliced_assembly.step",
        "assembly",
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [str(path) for path, _kind in INPUTS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing sidecar inputs: {missing}")

    stage_root = Path(os.environ[STAGE_ROOT_ENV]).resolve()
    records = {}
    for name, (source_step, kind) in INPUTS.items():
        staged_step = job_output_path(source_step)
        staged_step.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_step, staged_step)
        exit_code = int(
            step_artifact_main(
                [
                    "--repo-root",
                    str(stage_root),
                    "--step",
                    str(staged_step),
                    "--kind",
                    kind,
                    "--mesh-tolerance",
                    str(LINEAR_DEFLECTION_MM),
                    "--mesh-angular-tolerance",
                    str(ANGULAR_DEFLECTION_RAD),
                    "--force",
                    "--verbose",
                ]
            )
        )
        if exit_code != 0:
            raise RuntimeError(f"Sidecar generation failed for {name}: {exit_code}")
        generated = staged_step.with_name(f".{staged_step.name}.glb")
        if not generated.is_file():
            raise FileNotFoundError(generated)
        output = source_step.with_name(f".{source_step.name}.glb")
        staged = job_output_path(output)
        staged.parent.mkdir(parents=True, exist_ok=True)
        if generated != staged:
            shutil.copy2(generated, staged)
        records[name] = {
            "step_path": str(source_step.relative_to(ROOT)),
            "step_sha256": _sha256(source_step),
            "sidecar_path": str(output.relative_to(ROOT)),
            "sidecar_sha256": _sha256(generated),
            "sidecar_size_bytes": generated.stat().st_size,
            "kind": kind,
        }

    manifest = {
        "schema_version": 1,
        "mesh": {
            "linear_deflection_mm": LINEAR_DEFLECTION_MM,
            "chordal_tolerance_mm": LINEAR_DEFLECTION_MM,
            "angular_deflection_rad": ANGULAR_DEFLECTION_RAD,
            "angular_deflection_deg": math.degrees(ANGULAR_DEFLECTION_RAD),
            "relative": False,
        },
        "artifacts": records,
    }
    manifest_path = job_output_path(REVIEW_ROOT / "fine_sidecar_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
