"""Project ignored Variant R attestations into stable committed audit records.

The coordinated producer and release attestations are derived ``build/``
outputs.  This native-free adapter preserves every immutable identity needed
for a clean-checkout audit while omitting only the volatile creation time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-attestation", type=Path, required=True)
    parser.add_argument("--release-attestation", type=Path, required=True)
    parser.add_argument("--producer-out", type=Path, required=True)
    parser.add_argument("--release-out", type=Path, required=True)
    return parser.parse_args()


def _load(path: Path, expected_kind: str) -> dict[str, Any]:
    record = json.loads(path.read_text())
    if record.get("attestation_kind") != expected_kind:
        raise ValueError(
            f"{path} has {record.get('attestation_kind')!r}, "
            f"expected {expected_kind!r}"
        )
    closure = record.get("runtime_dependency_closure")
    if not isinstance(closure, dict):
        raise ValueError(f"{path} has no runtime dependency closure")
    if closure.get("complete_loaded_repo_source_count") != len(
        closure.get("sources", ())
    ):
        raise ValueError(f"{path} source count does not match its source list")
    return record


def _derived_identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": _sha256(path),
    }


def _producer_projection(
    path: Path,
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_kind": "variant_r_producer_source_closure_projection",
        "producer_attestation": _derived_identity(path),
        "cad_job_id": record["cad_job_id"],
        "producer_entrypoint": record["producer_entrypoint"],
        "producer_mode": record["producer_mode"],
        "git": record["git"],
        "historical_geometry_producer": record[
            "historical_geometry_producer"
        ],
        "toolchain": record["toolchain"],
        "authoritative_base_input": record["authoritative_base_input"],
        "closure": record["runtime_dependency_closure"],
    }


def _release_projection(
    path: Path,
    record: dict[str, Any],
) -> dict[str, Any]:
    artifacts = record.get("release_artifacts", ())
    if len(artifacts) != 9:
        raise ValueError(
            f"{path} binds {len(artifacts)} model artifacts instead of 9"
        )
    if record.get("git", {}).get("tracked_source_dirty"):
        raise ValueError(f"{path} was not produced from clean tracked source")
    return {
        "schema_version": 1,
        "record_kind": "variant_r_release_source_closure_projection",
        "release_attestation": _derived_identity(path),
        "cad_job_id": record["cad_job_id"],
        "release_entrypoint": record["release_entrypoint"],
        "release_mode": record["release_mode"],
        "git": record["git"],
        "evidence_collection": record["evidence_collection"],
        "toolchain": record["toolchain"],
        "authoritative_base_input": record["authoritative_base_input"],
        "release_artifacts": artifacts,
        "closure": record["runtime_dependency_closure"],
    }


def _write(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = _arguments()
    producer_path = args.producer_attestation
    release_path = args.release_attestation
    producer = _load(
        producer_path,
        "variant_r_authoritative_producer",
    )
    release = _load(
        release_path,
        "variant_r_coordinated_release",
    )
    if (
        release["authoritative_base_input"].get(
            "producer_attestation_sha256"
        )
        != _sha256(producer_path)
    ):
        raise ValueError(
            "release does not bind the supplied producer attestation"
        )
    _write(
        args.producer_out,
        _producer_projection(producer_path, producer),
    )
    _write(
        args.release_out,
        _release_projection(release_path, release),
    )


if __name__ == "__main__":
    main()
