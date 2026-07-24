"""Compare one Variant R bucket/baffle checkpoint with an accepted reference.

This is an evidence adapter, not a model generator.  It imports each published
STEP once, measures deterministic topology and mass properties, and performs
bidirectional material comparisons for the complete parts and every protected
section emitted by the active validator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from pathlib import Path as _CadSafetyPath
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
from cad_runner.outputs import job_output_path  # noqa: E402

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from build123d import import_step  # noqa: E402
from src.enclosure_family.variant_r.artifacts import (  # noqa: E402
    VARIANT_R_ARTIFACTS_BY_ID,
    VARIANT_R_PART_ARTIFACTS,
    VARIANT_R_PROTECTED_SECTION_ARTIFACTS,
)
from src.enclosure_family.variant_r.verification import (  # noqa: E402
    VARIANT_R_VERIFICATION,
)
from src.enclosure_family.variant_r.inputs import (  # noqa: E402
    AUTHORITATIVE_BASE_FILENAME,
    HISTORICAL_ACCEPTED_BASE_DATA_SHA256,
    HISTORICAL_ACCEPTED_BASE_SHA256,
)
from src.enclosure_family.variant_r.equivalence import (  # noqa: E402
    material_comparison_passes,
    numbers_equal,
    shape_records_equal,
)
from src.enclosure_family.variant_r.measurements import (  # noqa: E402
    intersection_record,
    material_comparison_record,
    shape_record,
)


PART_FILES = {
    artifact.artifact_id: artifact.filename
    for artifact in VARIANT_R_PART_ARTIFACTS
}
SECTION_FILES = tuple(
    artifact.filename for artifact in VARIANT_R_PROTECTED_SECTION_ARTIFACTS
)
DIAGNOSTICS_FILE = VARIANT_R_ARTIFACTS_BY_ID[
    "validation_diagnostics"
].filename
LENGTH_TOLERANCE_MM = VARIANT_R_VERIFICATION.tolerances.length_mm
VOLUME_TOLERANCE_MM3 = VARIANT_R_VERIFICATION.tolerances.volume_mm3
AREA_TOLERANCE_MM2 = VARIANT_R_VERIFICATION.tolerances.area_mm2
CENTER_TOLERANCE_MM = (
    VARIANT_R_VERIFICATION.tolerances.center_of_mass_mm
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalized_diagnostics(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    record.pop("scope", None)
    record["validation_contract"] = (
        "accepted Variant R deterministic geometry and interface invariants"
    )
    current_input = record.pop("authoritative_base_input", None)
    authoritative = Path(record["authoritative_base_step"])
    if current_input is None:
        base_data_sha256 = HISTORICAL_ACCEPTED_BASE_DATA_SHA256
    else:
        if current_input.get("filename") != AUTHORITATIVE_BASE_FILENAME:
            raise ValueError(
                f"unexpected Variant R base input: {current_input}"
            )
        base_data_sha256 = current_input["step_data_section_sha256"]
    record["authoritative_base_step"] = {
        "filename": authoritative.name,
        "step_data_section_sha256": base_data_sha256,
    }
    return record


def _base_input_provenance(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    current = record.get("authoritative_base_input")
    if current is not None:
        return {
            "status": "current_attested_producer_input",
            **current,
        }
    return {
        "status": "historical_hash_only_input",
        "filename": AUTHORITATIVE_BASE_FILENAME,
        "sha256": HISTORICAL_ACCEPTED_BASE_SHA256,
        "step_data_section_sha256": HISTORICAL_ACCEPTED_BASE_DATA_SHA256,
        "portable_producer_attestation": False,
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--reference-source-sha256", required=True)
    parser.add_argument("--candidate-source-sha256", required=True)
    parser.add_argument("--candidate-job-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    reference_dir = args.reference_dir.resolve()
    candidate_dir = args.candidate_dir.resolve()
    required = (*PART_FILES.values(), *SECTION_FILES, DIAGNOSTICS_FILE)
    for directory in (reference_dir, candidate_dir):
        for name in required:
            if not (directory / name).is_file():
                raise FileNotFoundError(directory / name)

    loaded: dict[str, dict[str, Any]] = {"reference": {}, "candidate": {}}
    for side, directory in (
        ("reference", reference_dir),
        ("candidate", candidate_dir),
    ):
        for name in (*PART_FILES.values(), *SECTION_FILES):
            loaded[side][name] = import_step(directory / name)

    comparisons: dict[str, Any] = {}
    for name in (*PART_FILES.values(), *SECTION_FILES):
        reference = loaded["reference"][name]
        candidate = loaded["candidate"][name]
        reference_stats = shape_record(reference)
        candidate_stats = shape_record(candidate)
        material = material_comparison_record(reference, candidate)
        comparisons[name] = {
            "reference_sha256": _sha256(reference_dir / name),
            "candidate_sha256": _sha256(candidate_dir / name),
            "reference": reference_stats,
            "candidate": candidate_stats,
            "material": material,
            "equivalent": (
                shape_records_equal(reference_stats, candidate_stats)
                and material_comparison_passes(material)
            ),
        }

    reference_diagnostics = _normalized_diagnostics(
        reference_dir / DIAGNOSTICS_FILE
    )
    candidate_diagnostics = _normalized_diagnostics(
        candidate_dir / DIAGNOSTICS_FILE
    )
    fit = intersection_record(
        loaded["candidate"][PART_FILES["bucket"]],
        loaded["candidate"][PART_FILES["baffle"]],
    )
    diagnostics_equal = numbers_equal(
        reference_diagnostics,
        candidate_diagnostics,
    )
    passed = (
        all(record["equivalent"] for record in comparisons.values())
        and diagnostics_equal
        and fit["diagnostic"]["usable"]
        and (
            fit["volume_mm3"] is None
            or fit["volume_mm3"] <= VOLUME_TOLERANCE_MM3
        )
    )
    report = {
        "schema_version": 1,
        "label": args.label,
        "passed": passed,
        "identities": {
            "reference_dir": str(reference_dir),
            "candidate_dir": str(candidate_dir),
            "reference_source_sha256": args.reference_source_sha256,
            "candidate_source_sha256": args.candidate_source_sha256,
            "candidate_job_id": args.candidate_job_id,
            "adapter_sha256": _sha256(Path(__file__)),
        },
        "tolerances": {
            "length_mm": LENGTH_TOLERANCE_MM,
            "volume_mm3": VOLUME_TOLERANCE_MM3,
            "surface_area_mm2": AREA_TOLERANCE_MM2,
            "center_of_mass_mm": CENTER_TOLERANCE_MM,
            "diagnostic_numeric": (
                VARIANT_R_VERIFICATION.tolerances.diagnostic_number
            ),
        },
        "parts_and_protected_sections": comparisons,
        "candidate_bucket_baffle_intersection": fit,
        "normalized_diagnostics_equal": diagnostics_equal,
        "base_input_provenance": {
            "reference": _base_input_provenance(
                reference_dir / DIAGNOSTICS_FILE
            ),
            "candidate": _base_input_provenance(
                candidate_dir / DIAGNOSTICS_FILE
            ),
        },
        "normalized_reference_diagnostics": reference_diagnostics,
        "normalized_candidate_diagnostics": candidate_diagnostics,
    }
    published = job_output_path(args.out.resolve())
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise ValueError(f"geometry checkpoint failed; inspect {published}")
    print(json.dumps({"passed": True, "report": str(published)}, indent=2))


if __name__ == "__main__":
    main()
