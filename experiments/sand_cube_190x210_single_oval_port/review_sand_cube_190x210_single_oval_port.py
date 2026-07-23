"""Generate a static review from an already-published, sidecar-bound STEP."""

# ruff: noqa: E402

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

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cad_runner.outputs import job_output_path
from scripts.generate_static_ocp_viewer import model_payload, render_viewer
from scripts.text_to_cad_artifacts import verify_cached_sidecar


ROOT = _CAD_SAFETY_ROOT
OUT = ROOT / "build" / "sand_cube_190x210_single_oval_port"
HARDWARE_STEP = OUT / "sand_cube_190x210_single_oval_port_hardware_check.step"
CUTAWAY_STEP = OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
REVIEWABLE_STEPS = {
    HARDWARE_STEP.name: OUT / "viewer",
    CUTAWAY_STEP.name: OUT / "cutaway_viewer",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_file(value: Path, *, label: str) -> Path:
    candidate = value.expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve(strict=True)
    try:
        candidate.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"{label} escapes repository root: {candidate}") from error
    if not candidate.is_file():
        raise ValueError(f"{label} is not a file: {candidate}")
    return candidate


def _requested_output(step: Path, value: Path | None) -> Path:
    if value is None:
        try:
            return REVIEWABLE_STEPS[step.name]
        except KeyError as error:
            raise ValueError(
                f"no default review output for {step.name}; pass --out"
            ) from error
    requested = value.expanduser()
    if not requested.is_absolute():
        requested = ROOT / requested
    requested = requested.resolve(strict=False)
    try:
        requested.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(
            f"review output escapes repository root: {requested}"
        ) from error
    if requested == step.parent:
        raise ValueError("review output must be a child directory, not the STEP parent")
    return requested


def _output_records(stage_dir: Path, requested_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(item for item in stage_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(stage_dir)
        records.append(
            {
                "path": (requested_dir.relative_to(ROOT) / relative).as_posix(),
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return records


def generate_review(
    *,
    step: Path,
    sidecar: Path,
    kind: str,
    output: Path,
) -> dict[str, Any]:
    step = _repo_file(step, label="STEP")
    sidecar = _repo_file(sidecar, label="sidecar")
    requested_output = _requested_output(step, output)
    verified = verify_cached_sidecar(ROOT, step, sidecar, kind)
    before_hash = _sha256_file(step)
    if before_hash != verified.step_sha256:
        raise RuntimeError("STEP changed after verified-sidecar lookup")

    staged_output = job_output_path(requested_output)
    staged_output.mkdir(parents=True, exist_ok=True)
    payload = model_payload(step)
    render_viewer(payload, staged_output)

    after_hash = _sha256_file(step)
    if after_hash != before_hash:
        raise RuntimeError("published STEP changed during review generation")
    provenance = {
        "schema_version": 1,
        "job_id": os.environ["CAD_JOB_ID"],
        "review_target": Path(__file__).relative_to(ROOT).as_posix(),
        "step": {
            "path": verified.step_path,
            "sha256": verified.step_sha256,
        },
        "sidecar": {
            "path": verified.sidecar_path,
            "sha256": verified.sidecar_sha256,
            "size_bytes": verified.sidecar_size_bytes,
            "kind": verified.kind,
            "verified_cache_key": verified.cache_key,
        },
        "renderer": {
            "name": "repository static OCP viewer",
            "artifact_import_count": 1,
            "tessellation_count": 1,
        },
        "outputs": _output_records(staged_output, requested_output),
    }
    provenance_path = staged_output / "review-provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return provenance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a failure-isolated static review from one published "
            "single-oval-port STEP and its current verified sidecar."
        )
    )
    parser.add_argument("--step", type=Path, default=HARDWARE_STEP)
    parser.add_argument("--sidecar", type=Path)
    parser.add_argument("--kind", choices=("part", "assembly"), default="assembly")
    parser.add_argument("--out", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    step = args.step
    resolved_step = step if step.is_absolute() else ROOT / step
    sidecar = args.sidecar or resolved_step.with_name(f".{resolved_step.name}.glb")
    print(
        json.dumps(
            generate_review(
                step=step,
                sidecar=sidecar,
                kind=args.kind,
                output=_requested_output(
                    resolved_step.resolve(strict=True),
                    args.out,
                ),
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
