"""Attest a completed Variant R release without entering its geometry process."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from pathlib import Path as _CadSafetyPath
import subprocess
import sys as _cad_safety_sys
from typing import Any


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_release_job(
    *,
    release_dir: Path,
    release_job_path: Path,
    artifact_filenames: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, Any]]:
    release_job = json.loads(release_job_path.read_text())
    if release_job.get("state") != "completed":
        raise ValueError(f"release job did not complete: {release_job_path}")
    command = release_job.get("command")
    if not isinstance(command, list) or len(command) < 4:
        raise ValueError("release job has no complete worker command")
    if command[1:3] != ["-m", "cad_runner.worker"]:
        raise ValueError(f"release job did not use cad_runner.worker: {command}")
    if Path(command[0]).resolve() != Path(_cad_safety_sys.executable).resolve():
        raise ValueError(f"release job used a different Python runtime: {command[0]}")
    if Path(command[-1]).resolve() != _VALIDATOR:
        raise ValueError(
            f"release job used {command[-1]} instead of {_VALIDATOR}"
        )

    published: dict[str, dict[str, Any]] = {}
    for record in release_job.get("final_outputs", ()):
        filename = Path(record["relative_path"]).name
        if filename in published:
            raise ValueError(f"release job published duplicate {filename}")
        published[filename] = record

    bound_outputs = []
    for filename in artifact_filenames:
        record = published.get(filename)
        path = (release_dir / filename).resolve()
        if record is None or not path.is_file():
            raise FileNotFoundError(f"release job did not publish {filename}")
        if Path(record["path"]).resolve() != path:
            raise ValueError(
                f"release job output path does not bind {path}: {record['path']}"
            )
        actual_sha256 = _sha256(path)
        actual_bytes = path.stat().st_size
        if record.get("sha256") != actual_sha256:
            raise ValueError(
                f"release job hash for {filename} does not match the artifact"
            )
        if record.get("bytes") != actual_bytes:
            raise ValueError(
                f"release job byte count for {filename} does not match"
            )
        bound_outputs.append(
            {
                "filename": filename,
                "sha256": actual_sha256,
                "bytes": actual_bytes,
            }
        )

    identity = {
        "job_id": release_job["job_id"],
        "job_record": {
            "path": release_job_path.relative_to(_CAD_SAFETY_ROOT).as_posix(),
            "sha256": _sha256(release_job_path),
        },
        "worker_module": "cad_runner.worker",
        "release_entrypoint": _VALIDATOR.relative_to(
            _CAD_SAFETY_ROOT
        ).as_posix(),
        "model_final_outputs": bound_outputs,
        "tracked_source_state": (
            "not recorded by the historical release job; exact dependency "
            "bytes are verified separately at the asserted commit"
        ),
    }
    return release_job, identity


def _verify_sources_at_commit(
    *,
    git_head: str,
    runtime_sources: tuple[dict[str, Any], ...],
) -> str:
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{git_head}^{{commit}}"],
        cwd=_CAD_SAFETY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != git_head:
        raise ValueError(f"release commit is not exact: {git_head} != {resolved}")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", resolved, "HEAD"],
        cwd=_CAD_SAFETY_ROOT,
        check=True,
        capture_output=True,
    )
    for record in runtime_sources:
        result = subprocess.run(
            ["git", "show", f"{resolved}:{record['path']}"],
            cwd=_CAD_SAFETY_ROOT,
            check=True,
            capture_output=True,
        )
        if hashlib.sha256(result.stdout).hexdigest() != record["sha256"]:
            raise ValueError(
                f"{record['path']} does not match release commit {resolved}"
            )
        if len(result.stdout) != record["bytes"]:
            raise ValueError(
                f"{record['path']} byte count does not match {resolved}"
            )
    return resolved


def main() -> None:
    args = _arguments()
    release_dir = args.release_dir.resolve()
    release_job_path = args.release_job.resolve()

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
    release_job, release_job_identity = _verify_release_job(
        release_dir=release_dir,
        release_job_path=release_job_path,
        artifact_filenames=artifacts,
    )

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
    release_git_head = _verify_sources_at_commit(
        git_head=args.release_git_head,
        runtime_sources=runtime_sources,
    )
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=_CAD_SAFETY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if current_branch != args.release_git_branch:
        raise ValueError(
            f"evidence branch {current_branch!r} does not match "
            f"{args.release_git_branch!r}"
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
            "head": release_git_head,
            "branch": args.release_git_branch,
            "tracked_source_dirty": None,
            "dependency_source_bytes_match_commit": True,
            "whole_tree_cleanliness_recorded_by_release_job": False,
        },
        release_job_identity=release_job_identity,
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
