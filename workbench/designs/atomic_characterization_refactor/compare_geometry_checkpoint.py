"""Compare one Variant R bucket/baffle checkpoint with an accepted reference.

This is an evidence adapter, not a model generator.  It imports each published
STEP once, measures deterministic topology and mass properties, and performs
bidirectional material comparisons for the complete parts and every protected
section emitted by the active validator.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from math import isclose
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

from build123d import CenterOf, import_step  # noqa: E402
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

from cad_geometry_checks.native import (  # noqa: E402
    compare_protected_material,
    measure_intersection,
    summarize_topology,
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


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _diagnostic(record: Any) -> dict[str, Any]:
    return {
        "status": _enum_value(record.status),
        "message": record.message,
        "failure_reason": (
            None
            if record.failure_reason is None
            else _enum_value(record.failure_reason)
        ),
        "usable": record.usable,
    }


def _topology(shape: Any) -> dict[str, Any]:
    summary = summarize_topology(shape)
    result = asdict(summary)
    result["unit"] = _enum_value(summary.unit)
    result["diagnostic"] = _diagnostic(summary.diagnostic)
    return result


def _shape_stats(shape: Any) -> dict[str, Any]:
    solids = tuple(solid for solid in shape.solids() if solid.volume > 1e-9)
    if not solids:
        raise ValueError("STEP contains no positive-volume solid")
    volume = sum(solid.volume for solid in solids)
    center = tuple(
        sum(
            solid.volume * getattr(solid.center(CenterOf.MASS), axis)
            for solid in solids
        )
        / volume
        for axis in ("X", "Y", "Z")
    )
    bounds = shape.bounding_box()
    return {
        "valid": bool(shape.is_valid)
        and all(bool(solid.is_valid) for solid in solids),
        "positive_solid_count": len(solids),
        "topology": _topology(shape),
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "volume_mm3": volume,
        "surface_area_mm2": sum(face.area for face in shape.faces()),
        "center_of_mass_mm": list(center),
    }


def _material_comparison(reference: Any, candidate: Any) -> dict[str, Any]:
    result = compare_protected_material(
        reference,
        candidate,
        bounding_box_tolerance_mm=LENGTH_TOLERANCE_MM,
        volume_tolerance_mm3=VOLUME_TOLERANCE_MM3,
    )
    return {
        "reference_volume_mm3": result.reference_volume_mm3,
        "candidate_volume_mm3": result.candidate_volume_mm3,
        "removed_volume_mm3": result.removed_volume_mm3,
        "added_volume_mm3": result.added_volume_mm3,
        "diagnostic": _diagnostic(result.diagnostic),
    }


def _intersection(left: Any, right: Any) -> dict[str, Any]:
    result = measure_intersection(
        left,
        right,
        bounding_box_tolerance_mm=LENGTH_TOLERANCE_MM,
        boolean_tolerance_mm=LENGTH_TOLERANCE_MM,
        volume_tolerance_mm3=VOLUME_TOLERANCE_MM3,
    )
    return {
        "volume_mm3": result.volume_mm3,
        "outcome": _enum_value(result.outcome),
        "diagnostic": _diagnostic(result.diagnostic),
    }


def _normalized_diagnostics(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
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


def _numbers_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return isclose(
            float(left),
            float(right),
            rel_tol=0.0,
            abs_tol=VARIANT_R_VERIFICATION.tolerances.diagnostic_number,
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _numbers_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _numbers_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _stats_equal(reference: dict[str, Any], candidate: dict[str, Any]) -> bool:
    topology_fields = (
        "shape_count",
        "solid_count",
        "shell_count",
        "face_count",
        "edge_count",
        "vertex_count",
        "boundary_edge_count",
        "manifold_edge_count",
        "non_manifold_edge_count",
    )
    return (
        reference["valid"]
        and candidate["valid"]
        and reference["positive_solid_count"] == candidate["positive_solid_count"]
        and all(
            reference["topology"][key] == candidate["topology"][key]
            for key in topology_fields
        )
        and all(
            isclose(a, b, rel_tol=0.0, abs_tol=LENGTH_TOLERANCE_MM)
            for group in ("min", "max", "size")
            for a, b in zip(
                reference["bounds_mm"][group],
                candidate["bounds_mm"][group],
                strict=True,
            )
        )
        and isclose(
            reference["volume_mm3"],
            candidate["volume_mm3"],
            rel_tol=0.0,
            abs_tol=VOLUME_TOLERANCE_MM3,
        )
        and isclose(
            reference["surface_area_mm2"],
            candidate["surface_area_mm2"],
            rel_tol=0.0,
            abs_tol=AREA_TOLERANCE_MM2,
        )
        and all(
            isclose(a, b, rel_tol=0.0, abs_tol=CENTER_TOLERANCE_MM)
            for a, b in zip(
                reference["center_of_mass_mm"],
                candidate["center_of_mass_mm"],
                strict=True,
            )
        )
    )


def _comparison_passes(record: dict[str, Any]) -> bool:
    return (
        record["diagnostic"]["usable"]
        and record["removed_volume_mm3"] is not None
        and record["added_volume_mm3"] is not None
        and record["removed_volume_mm3"] <= VOLUME_TOLERANCE_MM3
        and record["added_volume_mm3"] <= VOLUME_TOLERANCE_MM3
    )


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
        reference_stats = _shape_stats(reference)
        candidate_stats = _shape_stats(candidate)
        material = _material_comparison(reference, candidate)
        comparisons[name] = {
            "reference_sha256": _sha256(reference_dir / name),
            "candidate_sha256": _sha256(candidate_dir / name),
            "reference": reference_stats,
            "candidate": candidate_stats,
            "material": material,
            "equivalent": (
                _stats_equal(reference_stats, candidate_stats)
                and _comparison_passes(material)
            ),
        }

    reference_diagnostics = _normalized_diagnostics(
        reference_dir / DIAGNOSTICS_FILE
    )
    candidate_diagnostics = _normalized_diagnostics(
        candidate_dir / DIAGNOSTICS_FILE
    )
    fit = _intersection(
        loaded["candidate"][PART_FILES["bucket"]],
        loaded["candidate"][PART_FILES["baffle"]],
    )
    diagnostics_equal = _numbers_equal(
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
