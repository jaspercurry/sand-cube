"""Prove the current produced Variant R base matches its historical input."""

from __future__ import annotations

import argparse
import hashlib
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
from src.enclosure_family.variant_r.equivalence import (  # noqa: E402
    material_comparison_passes,
    shape_records_equal,
)
from src.enclosure_family.variant_r.measurements import (  # noqa: E402
    material_comparison_record,
    shape_record,
)
from workbench.designs.atomic_characterization_refactor.compare_geometry_checkpoint import (  # noqa: E402
    VOLUME_TOLERANCE_MM3,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--producer-attestation", type=Path)
    parser.add_argument("--producer-commit")
    parser.add_argument("--capture-overlay-sha256")
    parser.add_argument("--producer-job-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _step_data_section_sha256(path: Path) -> str:
    """Hash the complete ISO-10303 DATA entity payload, excluding its header."""

    data = path.read_bytes()
    marker = b"DATA;"
    offset = data.find(marker)
    if offset < 0:
        raise ValueError(f"STEP DATA section is missing: {path}")
    return hashlib.sha256(data[offset:]).hexdigest()


def main() -> None:
    args = _arguments()
    reference_path = args.reference.resolve()
    candidate_path = args.candidate.resolve()
    attestation_path = (
        None
        if args.producer_attestation is None
        else args.producer_attestation.resolve()
    )
    required_paths = [reference_path, candidate_path]
    if attestation_path is not None:
        required_paths.append(attestation_path)
    for path in required_paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    if attestation_path is not None:
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
        candidate_provenance = {
            "producer_attestation_sha256": sha256_file(attestation_path),
            "producer_git": attestation["git"],
            "toolchain": attestation["toolchain"],
        }
    else:
        if not args.producer_commit or not args.capture_overlay_sha256:
            raise ValueError(
                "Historical capture requires --producer-commit and "
                "--capture-overlay-sha256"
            )
        candidate_provenance = {
            "producer_commit": args.producer_commit,
            "capture_overlay_sha256": args.capture_overlay_sha256,
            "producer_attestation_sha256": None,
        }

    reference = import_step(reference_path)
    candidate = import_step(candidate_path)
    reference_stats = shape_record(reference)
    candidate_stats = shape_record(candidate)
    material = material_comparison_record(reference, candidate)
    reference_data_sha256 = _step_data_section_sha256(reference_path)
    candidate_data_sha256 = _step_data_section_sha256(candidate_path)
    data_section_identical = (
        reference_data_sha256 == candidate_data_sha256
    )
    material_proof = (
        {
            "method": "byte-identical complete ISO-10303 DATA entity payload",
            "removed_volume_mm3": 0.0,
            "added_volume_mm3": 0.0,
            "boolean_cross_check": material,
            "boolean_cross_check_usable": False,
            "boolean_cross_check_note": (
                "OCCT symmetric difference was unstable for separately "
                "imported coincident copies; exact DATA payload identity plus "
                "independent topology and mass properties is authoritative"
            ),
        }
        if data_section_identical
        else {
            "method": "bidirectional OCCT protected-material comparison",
            "removed_volume_mm3": material["removed_volume_mm3"],
            "added_volume_mm3": material["added_volume_mm3"],
            "boolean_cross_check": material,
            "boolean_cross_check_usable": material["diagnostic"]["usable"],
        }
    )
    passed = (
        shape_records_equal(reference_stats, candidate_stats)
        and (
            data_section_identical
            or material_comparison_passes(material)
        )
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
            "step_data_section_sha256": reference_data_sha256,
            "measurements": reference_stats,
            "provenance": (
                "historical accepted Stage 1 input; immutable hash retained "
                "for audit, but the ignored file is not required in a clean checkout"
            ),
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": sha256_file(candidate_path),
            "step_data_section_sha256": candidate_data_sha256,
            "measurements": candidate_stats,
            "producer_job_id": args.producer_job_id,
            **candidate_provenance,
        },
        "step_data_section_identical": data_section_identical,
        "bidirectional_material": material_proof,
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
