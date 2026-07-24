"""Post-geometry release evidence for Variant R.

A separate coordinated evidence job imports this module only after the release
geometry job has completed. Keeping release-only names and allocations here
makes provenance observational with respect to the serialized legacy geometry
path.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import platform
from typing import Any, Final

from .inputs import MODEL_OUTPUT_DIRECTORY
from .provenance import (
    ATTESTATION_SCHEMA_VERSION,
    _git_identity,
    _package_version,
    collect_loaded_repo_sources,
    sha256_file,
)


RELEASE_ATTESTATION_FILENAME: Final = "variant_r_release_attestation.json"


def write_release_attestation(
    *,
    repo_root: Path,
    output_directory: Path,
    release_entrypoint: Path,
    authoritative_base_input: dict[str, Any],
    artifact_filenames: Iterable[str],
    release_job_id: str | None = None,
    runtime_sources: Iterable[dict[str, Any]] | None = None,
    attestation_output: Path | None = None,
    evidence_entrypoint: Path | None = None,
    release_git_identity: dict[str, Any] | None = None,
    release_job_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind a completed coordinated release to its sources and artifacts."""

    root = repo_root.resolve()
    output = output_directory.resolve()
    evidence_git_identity = _git_identity(root)
    if evidence_git_identity["tracked_source_dirty"]:
        raise RuntimeError(
            "Variant R release attestation requires a clean tracked source state"
        )
    release_git = release_git_identity or evidence_git_identity
    if release_git.get("tracked_source_dirty") is True:
        raise RuntimeError("Variant R release was not produced from clean source")
    if (
        release_git_identity is not None
        and release_git.get("dependency_source_bytes_match_commit") is not True
    ):
        raise RuntimeError(
            "Variant R release dependencies were not verified at the "
            "asserted release commit"
        )
    release_source = release_entrypoint.resolve()
    if runtime_sources is None:
        sources = collect_loaded_repo_sources(
            root,
            explicit_sources=(release_source,),
        )
    else:
        sources = tuple(runtime_sources)
    sources = tuple(
        {**record, "revision": release_git["head"]}
        for record in sources
    )
    geometry_sources = tuple(
        record
        for record in sources
        if record["role"] == "geometry_or_parameter_dependency"
    )
    generator_stages = tuple(
        record
        for record in sources
        if record["path"].startswith("experiments/")
        and Path(record["path"]).name.startswith("generate")
    )
    if len(generator_stages) < 19:
        raise RuntimeError(
            "Variant R release loaded fewer than the documented 19 "
            f"generator stages: {len(generator_stages)}"
        )

    artifacts = []
    for filename in artifact_filenames:
        artifact = output / filename
        if not artifact.is_file():
            raise FileNotFoundError(artifact)
        artifacts.append(
            {
                "path": (MODEL_OUTPUT_DIRECTORY / filename).as_posix(),
                "filename": filename,
                "sha256": sha256_file(artifact),
                "bytes": artifact.stat().st_size,
            }
        )

    writer_path = Path(__file__).resolve()
    writer_record_path = (
        writer_path.relative_to(root).as_posix()
        if writer_path.is_relative_to(root)
        else str(writer_path)
    )
    payload = {
        "schema_version": ATTESTATION_SCHEMA_VERSION,
        "attestation_kind": "variant_r_coordinated_release",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "cad_job_id": release_job_id or os.environ.get("CAD_JOB_ID"),
        "evidence_collection": {
            "cad_job_id": os.environ.get("CAD_JOB_ID"),
            "git": evidence_git_identity,
            "adapter": (
                None
                if evidence_entrypoint is None
                else {
                    "path": evidence_entrypoint.resolve()
                    .relative_to(root)
                    .as_posix(),
                    "sha256": sha256_file(evidence_entrypoint.resolve()),
                }
            ),
            "writer": {
                "path": writer_record_path,
                "sha256": sha256_file(writer_path),
            },
        },
        "release_entrypoint": release_source.relative_to(root).as_posix(),
        "release_mode": (
            "current attested base input plus explicit Variant R composition; "
            "complete parts, protected sections, deterministic diagnostics and "
            "STEP round trips; post-geometry observational evidence collection; "
            "unrelated runtime caches excluded"
        ),
        "git": release_git,
        "release_job": release_job_identity,
        "toolchain": {
            "python": platform.python_version(),
            "build123d": _package_version("build123d"),
            "ocp": _package_version("cadquery-ocp-novtk"),
        },
        "authoritative_base_input": authoritative_base_input,
        "release_artifacts": artifacts,
        "runtime_dependency_closure": {
            "method": (
                (
                    "every repository Python source present in sys.modules "
                    "after the successful coordinated release, plus the "
                    "explicit release entrypoint"
                )
                if runtime_sources is None
                else (
                    "repository source set captured in a separate coordinated "
                    "evidence job by importing the exact release entrypoint "
                    "without calling main; main contains no local repository "
                    "imports; the separately identified evidence adapter is "
                    "excluded from this geometry/runtime closure"
                )
            ),
            "complete_loaded_repo_source_count": len(sources),
            "geometry_or_parameter_source_count": len(geometry_sources),
            "loaded_generator_stage_count": len(generator_stages),
            "sources": sources,
        },
    }
    attestation = (
        output / RELEASE_ATTESTATION_FILENAME
        if attestation_output is None
        else attestation_output.resolve()
    )
    attestation.parent.mkdir(parents=True, exist_ok=True)
    attestation.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
