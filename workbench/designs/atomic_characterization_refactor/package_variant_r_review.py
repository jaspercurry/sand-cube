"""Package an exact attested Variant R release for visual review.

This evidence adapter does not generate or transform product geometry.  It
verifies the bucket and baffle against a coordinated release attestation,
places both already-exported parts in one STEP compound in their existing
design coordinates, and publishes a second attestation for Viewer/Snapshot
provenance.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

# This guard must remain before all native CAD/threaded-library imports.
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import (  # noqa: E402
    ensure_coordinated as _ensure_cad_coordinated,
)

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from build123d import Compound, import_step  # noqa: E402

from cad_runner.outputs import job_output_path  # noqa: E402
from src.enclosure_family.variant_r.artifacts import (  # noqa: E402
    VARIANT_R_ARTIFACTS_BY_ID,
)
from src.enclosure_family.variant_r.export import (  # noqa: E402
    publish_step_round_trip,
)
from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    sha256_file,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--release-attestation", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--attestation-out", type=Path, required=True)
    return parser.parse_args()


def _release_artifacts(attestation: dict[str, Any]) -> dict[str, Any]:
    if attestation.get("attestation_kind") != "variant_r_coordinated_release":
        raise ValueError("visual review requires a Variant R release attestation")
    records = attestation.get("release_artifacts")
    if not isinstance(records, list):
        raise ValueError("release attestation has no artifact records")
    return {record["filename"]: record for record in records}


def main() -> None:
    args = _arguments()
    release_dir = args.release_dir.resolve()
    release_attestation_path = args.release_attestation.resolve()
    release_attestation = json.loads(release_attestation_path.read_text())
    release_artifacts = _release_artifacts(release_attestation)

    input_records = []
    shapes = []
    for artifact_id in ("bucket", "baffle"):
        filename = VARIANT_R_ARTIFACTS_BY_ID[artifact_id].filename
        path = release_dir / filename
        record = release_artifacts.get(filename)
        if record is None:
            raise ValueError(
                f"release attestation does not bind visual input {filename}"
            )
        actual_sha256 = sha256_file(path)
        if actual_sha256 != record.get("sha256"):
            raise ValueError(
                f"visual input hash mismatch for {filename}: "
                f"{actual_sha256} != {record.get('sha256')}"
            )
        shape = import_step(path)
        solids = tuple(shape.solids())
        if len(solids) != 1 or not solids[0].is_valid:
            raise ValueError(
                f"visual input is not one valid solid: {filename}"
            )
        shapes.append(shape)
        input_records.append(
            {
                "artifact_id": artifact_id,
                "filename": filename,
                "path": str(path),
                "sha256": actual_sha256,
                "transform": "identity; retained release design coordinates",
            }
        )

    assembly = Compound(children=shapes)
    output = args.out.resolve()
    round_trip = publish_step_round_trip(
        output,
        assembly,
        require_single_solid=False,
    )
    staged_output = job_output_path(output)
    if round_trip["source_solid_count"] != 2:
        raise ValueError(f"visual assembly source contract failed: {round_trip}")
    if round_trip["imported_solid_count"] != 2:
        raise ValueError(f"visual assembly round trip failed: {round_trip}")

    adapter_path = Path(__file__).resolve()
    payload = {
        "schema_version": 1,
        "attestation_kind": "variant_r_visual_review_assembly",
        "cad_job_id": os.environ.get("CAD_JOB_ID"),
        "adapter": {
            "path": adapter_path.relative_to(_CAD_SAFETY_ROOT).as_posix(),
            "sha256": sha256_file(adapter_path),
        },
        "release": {
            "attestation_path": str(release_attestation_path),
            "attestation_sha256": sha256_file(release_attestation_path),
            "cad_job_id": release_attestation.get("cad_job_id"),
            "git": release_attestation.get("git"),
        },
        "inputs": input_records,
        "composition": {
            "operation": "two-child STEP compound only",
            "transforms": "identity",
            "round_trip": round_trip,
        },
        "output": {
            "path": str(output),
            "sha256": sha256_file(staged_output),
            "bytes": staged_output.stat().st_size,
        },
        "claims": {
            "geometry_generation": False,
            "product_geometry_change": False,
            "visual_measurements_authoritative": False,
        },
    }
    attestation_output = job_output_path(args.attestation_out.resolve())
    attestation_output.parent.mkdir(parents=True, exist_ok=True)
    attestation_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "review_assembly": payload["output"],
                "attestation": str(attestation_output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
