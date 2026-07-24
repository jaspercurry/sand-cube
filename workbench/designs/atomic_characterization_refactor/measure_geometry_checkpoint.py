"""Measure a proportional Variant R checkpoint without material Booleans.

Use this for source changes proven to be native-CAD-free ownership rewiring.
Geometry/interface extractions still use ``compare_geometry_checkpoint.py``
with bidirectional protected-material comparisons.
"""

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

from cad_geometry_checks.native import measure_intersection  # noqa: E402
from workbench.designs.atomic_characterization_refactor.compare_geometry_checkpoint import (  # noqa: E402
    DIAGNOSTICS_FILE,
    LENGTH_TOLERANCE_MM,
    PART_FILES,
    SECTION_FILES,
    VOLUME_TOLERANCE_MM3,
    _diagnostic,
    _enum_value,
    _normalized_diagnostics,
    _numbers_equal,
    _shape_stats,
    _stats_equal,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--atom-id", required=True)
    parser.add_argument("--before-source-sha256", required=True)
    parser.add_argument("--candidate-source-sha256", required=True)
    parser.add_argument("--candidate-job-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    reference_dir = args.reference_dir.resolve()
    candidate_dir = args.candidate_dir.resolve()
    names = (*PART_FILES.values(), *SECTION_FILES)
    required = (*names, DIAGNOSTICS_FILE)
    for directory in (reference_dir, candidate_dir):
        for name in required:
            if not (directory / name).is_file():
                raise FileNotFoundError(directory / name)

    comparisons: dict[str, object] = {}
    candidate_parts: dict[str, object] = {}
    for name in names:
        reference = import_step(reference_dir / name)
        candidate = import_step(candidate_dir / name)
        reference_stats = _shape_stats(reference)
        candidate_stats = _shape_stats(candidate)
        comparisons[name] = {
            "reference_sha256": _sha256(reference_dir / name),
            "candidate_sha256": _sha256(candidate_dir / name),
            "reference": reference_stats,
            "candidate": candidate_stats,
            "equivalent": _stats_equal(reference_stats, candidate_stats),
        }
        if name in PART_FILES.values():
            candidate_parts[name] = candidate

    fit_result = measure_intersection(
        candidate_parts[PART_FILES["bucket"]],
        candidate_parts[PART_FILES["baffle"]],
        bounding_box_tolerance_mm=LENGTH_TOLERANCE_MM,
        boolean_tolerance_mm=LENGTH_TOLERANCE_MM,
        volume_tolerance_mm3=VOLUME_TOLERANCE_MM3,
    )
    fit = {
        "volume_mm3": fit_result.volume_mm3,
        "outcome": _enum_value(fit_result.outcome),
        "diagnostic": _diagnostic(fit_result.diagnostic),
    }
    diagnostics_equal = _numbers_equal(
        _normalized_diagnostics(reference_dir / DIAGNOSTICS_FILE),
        _normalized_diagnostics(candidate_dir / DIAGNOSTICS_FILE),
    )
    passed = (
        all(record["equivalent"] for record in comparisons.values())  # type: ignore[index,union-attr]
        and diagnostics_equal
        and fit["diagnostic"]["usable"]  # type: ignore[index]
        and (
            fit["volume_mm3"] is None  # type: ignore[index]
            or fit["volume_mm3"] <= VOLUME_TOLERANCE_MM3  # type: ignore[index,operator]
        )
    )
    report = {
        "schema_version": 1,
        "atom_id": args.atom_id,
        "passed": passed,
        "profile": "proportional_native_metrics_no_material_booleans",
        "rationale": (
            "The atom changes native-free parameter/metadata ownership only. "
            "The exact baseline already has a release-grade bidirectional "
            "material proof; geometry/interface atoms require a fresh strict proof."
        ),
        "identities": {
            "before_source_sha256": args.before_source_sha256,
            "candidate_source_sha256": args.candidate_source_sha256,
            "candidate_job_id": args.candidate_job_id,
            "adapter_sha256": _sha256(Path(__file__)),
        },
        "parts_and_protected_sections": comparisons,
        "candidate_bucket_baffle_intersection": fit,
        "normalized_diagnostics_equal": diagnostics_equal,
    }
    published = job_output_path(args.out.resolve())
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise ValueError(f"geometry metrics checkpoint failed; inspect {published}")
    print(json.dumps({"passed": True, "report": str(published)}, indent=2))


if __name__ == "__main__":
    main()
