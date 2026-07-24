"""Attest a completed Variant R release without entering its geometry process."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
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

from cad_runner.entrypoint import (  # noqa: E402
    ensure_coordinated as _ensure_cad_coordinated,
)

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from cad_runner.outputs import job_output_path  # noqa: E402


_VALIDATOR = _CAD_SAFETY_ROOT / (
    "experiments/"
    "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle/"
    "validate_simple_tongue_groove_baffle.py"
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--release-job", type=Path, required=True)
    parser.add_argument("--release-git-head", required=True)
    parser.add_argument("--release-git-branch", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _load_release_entrypoint() -> None:
    spec = importlib.util.spec_from_file_location(
        "variant_r_release_dependency_probe",
        _VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Variant R validator: {_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def main() -> None:
    args = _arguments()
    release_dir = args.release_dir.resolve()
    release_job_path = args.release_job.resolve()
    release_job = json.loads(release_job_path.read_text())
    if release_job.get("state") != "completed":
        raise ValueError(f"release job did not complete: {release_job_path}")

    # Import the exact release entrypoint without calling main. Its module-level
    # imports are the complete repository dependency set used by main; main has
    # no local imports. Capture that set before loading release-only evidence.
    _load_release_entrypoint()

    from src.enclosure_family.variant_r.artifacts import VARIANT_R_ARTIFACTS
    from src.enclosure_family.variant_r.provenance import (
        collect_loaded_repo_sources,
    )

    artifacts = tuple(
        artifact.filename
        for artifact in VARIANT_R_ARTIFACTS
        if artifact.kind in {"part", "protected_section", "diagnostics"}
    )
    if len(artifacts) != 9:
        raise ValueError(f"expected nine Variant R release artifacts: {artifacts}")
    published = {
        Path(record["relative_path"]).name: record
        for record in release_job.get("final_outputs", ())
    }
    for filename in artifacts:
        record = published.get(filename)
        path = release_dir / filename
        if record is None or not path.is_file():
            raise FileNotFoundError(f"release job did not publish {filename}")

    runtime_sources = collect_loaded_repo_sources(
        _CAD_SAFETY_ROOT,
        explicit_sources=(_VALIDATOR,),
    )
    evidence_path = Path(__file__).resolve()
    runtime_sources = tuple(
        record
        for record in runtime_sources
        if record["path"]
        != evidence_path.relative_to(_CAD_SAFETY_ROOT).as_posix()
    )
    diagnostics = json.loads(
        (release_dir / "validation_diagnostics.json").read_text()
    )

    from src.enclosure_family.variant_r.release_provenance import (
        write_release_attestation,
    )

    payload = write_release_attestation(
        repo_root=_CAD_SAFETY_ROOT,
        output_directory=release_dir,
        release_entrypoint=_VALIDATOR,
        authoritative_base_input=diagnostics["authoritative_base_input"],
        artifact_filenames=artifacts,
        release_job_id=release_job["job_id"],
        runtime_sources=runtime_sources,
        attestation_output=job_output_path(args.out.resolve()),
        evidence_entrypoint=evidence_path,
        release_git_identity={
            "head": args.release_git_head,
            "branch": args.release_git_branch,
            "tracked_source_dirty": False,
        },
    )
    print(
        json.dumps(
            {
                "release_job_id": payload["cad_job_id"],
                "evidence_job_id": payload["evidence_collection"]["cad_job_id"],
                "loaded_sources": payload["runtime_dependency_closure"][
                    "complete_loaded_repo_source_count"
                ],
                "release_artifacts": len(payload["release_artifacts"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
