"""Hash-bound producer and accepted-input provenance for Variant R.

This module deliberately has no native CAD imports.  The producer calls it
after geometry generation, when the complete runtime dependency closure is
already present in ``sys.modules``.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from types import ModuleType
from typing import Any, Final

from .inputs import (
    AUTHORITATIVE_BASE_FILENAME,
    PRODUCER_ATTESTATION_FILENAME,
    PRODUCER_ENTRYPOINT,
)


ATTESTATION_SCHEMA_VERSION: Final = 1


def sha256_file(path: Path) -> str:
    """Hash a file without loading a large CAD artifact into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _repo_python_source(path: Path, repo_root: Path) -> Path | None:
    try:
        resolved = path.resolve()
    except OSError:
        return None
    if resolved.suffix in {".pyc", ".pyo"}:
        py_source = resolved.with_suffix(".py")
        if py_source.is_file():
            resolved = py_source
    if resolved.suffix != ".py" or not resolved.is_file():
        return None
    try:
        relative = resolved.relative_to(repo_root)
    except ValueError:
        return None
    if not relative.parts or relative.parts[0] in {".venv", "build"}:
        return None
    return resolved


def _source_role(relative: Path) -> str:
    if relative == PRODUCER_ENTRYPOINT:
        return "producer_entrypoint"
    if relative.parts and relative.parts[0] in {"experiments", "src"}:
        return "geometry_or_parameter_dependency"
    if relative == Path("params.py"):
        return "geometry_or_parameter_dependency"
    if relative.parts and relative.parts[0] == "cad_runner":
        return "coordinated_runtime_dependency"
    return "repo_runtime_dependency"


def collect_loaded_repo_sources(
    repo_root: Path,
    *,
    modules: Iterable[ModuleType] | None = None,
    explicit_sources: Iterable[Path] = (),
) -> tuple[dict[str, Any], ...]:
    """Hash every repo Python source loaded by the successful producer run."""

    root = repo_root.resolve()
    sources: set[Path] = set()
    for module in modules if modules is not None else tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        source = _repo_python_source(Path(module_file), root)
        if source is not None:
            sources.add(source)
    for path in explicit_sources:
        candidate = path if path.is_absolute() else root / path
        source = _repo_python_source(candidate, root)
        if source is None:
            raise FileNotFoundError(candidate)
        sources.add(source)

    records = []
    for source in sorted(sources):
        relative = source.relative_to(root)
        records.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(source),
                "bytes": source.stat().st_size,
                "role": _source_role(relative),
            }
        )
    return tuple(records)


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not-installed"


def _git_identity(repo_root: Path) -> dict[str, Any]:
    def git(*arguments: str) -> str:
        result = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    return {
        "head": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "tracked_source_dirty": bool(
            git("status", "--porcelain", "--untracked-files=no")
        ),
    }


def write_producer_attestation(
    *,
    repo_root: Path,
    output_directory: Path,
    producer_entrypoint: Path,
) -> dict[str, Any]:
    """Write the exact source/tool/base identity of a completed producer run."""

    root = repo_root.resolve()
    output = output_directory.resolve()
    base_step = output / AUTHORITATIVE_BASE_FILENAME
    if not base_step.is_file():
        raise FileNotFoundError(
            "The authoritative Variant R producer did not emit its base input: "
            f"{base_step}"
        )
    sources = collect_loaded_repo_sources(
        root,
        explicit_sources=(producer_entrypoint, PRODUCER_ENTRYPOINT),
    )
    geometry_sources = tuple(
        record
        for record in sources
        if record["role"] == "geometry_or_parameter_dependency"
    )
    experiment_stages = tuple(
        record
        for record in geometry_sources
        if record["path"].startswith("experiments/")
        and Path(record["path"]).name.startswith("generate")
    )
    if len(experiment_stages) < 19:
        raise RuntimeError(
            "Variant R producer loaded fewer than the documented 19 "
            f"generator stages: {len(experiment_stages)}"
        )

    stage_value = os.environ.get("CAD_JOB_STAGE_ROOT")
    try:
        if stage_value is None:
            raise ValueError
        stage_root = Path(stage_value).resolve()
        base_relative = base_step.relative_to(stage_root).as_posix()
    except ValueError:
        base_relative = base_step.relative_to(root).as_posix()

    payload = {
        "schema_version": ATTESTATION_SCHEMA_VERSION,
        "attestation_kind": "variant_r_authoritative_producer",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "cad_job_id": os.environ.get("CAD_JOB_ID"),
        "producer_entrypoint": PRODUCER_ENTRYPOINT.as_posix(),
        "producer_mode": (
            "base-only capture of the accepted front-fill/solid-rear "
            "compatibility foundation with the coherent brace dependency "
            "bound explicitly; downstream assembly previews and unrelated "
            "component exports are excluded"
        ),
        "git": _git_identity(root),
        "toolchain": {
            "python": platform.python_version(),
            "build123d": _package_version("build123d"),
            "ocp": _package_version("cadquery-ocp-novtk"),
        },
        "authoritative_base_input": {
            "path": base_relative,
            "filename": base_step.name,
            "sha256": sha256_file(base_step),
            "bytes": base_step.stat().st_size,
            "publication": "cad_runner_atomic_job_output",
        },
        "runtime_dependency_closure": {
            "method": (
                "all repository Python sources present in sys.modules after "
                "the successful producer completed, plus the explicit entrypoint"
            ),
            "complete_loaded_repo_source_count": len(sources),
            "geometry_or_parameter_source_count": len(geometry_sources),
            "loaded_generator_stage_count": len(experiment_stages),
            "sources": sources,
        },
    }
    attestation = output / PRODUCER_ATTESTATION_FILENAME
    attestation.parent.mkdir(parents=True, exist_ok=True)
    attestation.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def verify_producer_attestation(
    *,
    repo_root: Path,
    base_step: Path,
    attestation_path: Path,
) -> dict[str, Any]:
    """Reject an absent, stale, foreign, or self-asserted generated base."""

    if not base_step.is_file():
        raise FileNotFoundError(base_step)
    if not attestation_path.is_file():
        raise FileNotFoundError(
            "Authoritative Variant R base requires its producer attestation: "
            f"{attestation_path}"
        )
    payload = json.loads(attestation_path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != ATTESTATION_SCHEMA_VERSION
        or payload.get("attestation_kind")
        != "variant_r_authoritative_producer"
        or payload.get("producer_entrypoint")
        != PRODUCER_ENTRYPOINT.as_posix()
    ):
        raise ValueError(f"Unrecognized Variant R producer attestation: {attestation_path}")
    identity = payload.get("authoritative_base_input", {})
    actual_hash = sha256_file(base_step)
    if (
        identity.get("filename") != AUTHORITATIVE_BASE_FILENAME
        or identity.get("sha256") != actual_hash
        or identity.get("bytes") != base_step.stat().st_size
    ):
        raise ValueError(
            "Variant R base does not match its producer attestation: "
            f"expected={identity}, actual_sha256={actual_hash}"
        )
    closure = payload.get("runtime_dependency_closure", {})
    sources = closure.get("sources")
    if (
        not isinstance(sources, list)
        or closure.get("loaded_generator_stage_count", 0) < 19
        or not sources
    ):
        raise ValueError(
            "Variant R producer attestation lacks the complete runtime "
            f"dependency closure: {attestation_path}"
        )
    if payload.get("git", {}).get("tracked_source_dirty") is not False:
        raise ValueError(
            "Variant R authoritative input was not produced from a clean "
            f"tracked source state: {attestation_path}"
        )
    return payload
