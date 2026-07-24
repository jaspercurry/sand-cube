"""Prove the current produced Variant R base matches its historical input."""

from __future__ import annotations

import argparse
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
from cad_runner.outputs import job_output_path  # noqa: E402

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from build123d import import_step  # noqa: E402
from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    sha256_file,
    verify_producer_attestation,
)
from workbench.designs.atomic_characterization_refactor.compare_geometry_checkpoint import (  # noqa: E402
    VOLUME_TOLERANCE_MM3,
    _comparison_passes,
    _material_comparison,
    _shape_stats,
    _stats_equal,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--producer-attestation", type=Path, required=True)
    parser.add_argument("--producer-job-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    reference_path = args.reference.resolve()
    candidate_path = args.candidate.resolve()
    attestation_path = args.producer_attestation.resolve()
    for path in (reference_path, candidate_path, attestation_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    attestation = verify_producer_attestation(
        repo_root=_CAD_SAFETY_ROOT,
        base_step=candidate_path,
        attestation_path=attestation_path,
    )
    if attestation["cad_job_id"] != args.producer_job_id:
        raise ValueError(
            "Producer job does not match the base attestation: "
            f"{args.producer_job_id} != {attestation['cad_job_id']}"
        )

    reference = import_step(reference_path)
    candidate = import_step(candidate_path)
    reference_stats = _shape_stats(reference)
    candidate_stats = _shape_stats(candidate)
    material = _material_comparison(reference, candidate)
    passed = (
        _stats_equal(reference_stats, candidate_stats)
        and _comparison_passes(material)
    )
    report = {
        "schema_version": 1,
        "passed": passed,
        "comparison": (
            "historical accepted full-detail base versus current "
            "cataloged-producer base"
        ),
        "reference": {
            "path": str(reference_path),
            "sha256": sha256_file(reference_path),
            "measurements": reference_stats,
            "provenance": (
                "historical accepted Stage 1 input; immutable hash retained "
                "for audit, but the ignored file is not required in a clean checkout"
            ),
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": sha256_file(candidate_path),
            "measurements": candidate_stats,
            "producer_job_id": args.producer_job_id,
            "producer_attestation_sha256": sha256_file(attestation_path),
            "producer_git": attestation["git"],
            "toolchain": attestation["toolchain"],
        },
        "bidirectional_material": material,
        "tolerance_mm3": VOLUME_TOLERANCE_MM3,
        "adapter_sha256": sha256_file(Path(__file__)),
    }
    published = job_output_path(args.out.resolve())
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    if not passed:
        raise ValueError(
            f"authoritative base equivalence failed; inspect {published}"
        )
    print(json.dumps({"passed": True, "report": str(published)}, indent=2))


if __name__ == "__main__":
    main()
