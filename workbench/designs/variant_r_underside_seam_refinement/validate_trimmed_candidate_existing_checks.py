"""Apply the existing seal, contact, body, and round-trip checks to the candidate."""

from __future__ import annotations


# This guard must remain before all native CAD/threaded-library imports.
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
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
from pathlib import Path
import sys

from build123d import import_step


ROOT = _CAD_SAFETY_ROOT
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import validate_simple_tongue_groove_baffle as validator


CANDIDATE = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/trimmed_candidate"
)
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/"
    "candidate_existing_checks.json"
)


def _assert_round_trip_records(records: dict) -> None:
    expected = {
        "trimmed_unspliced_bucket.step": 1,
        "trimmed_unspliced_baffle.step": 1,
        "trimmed_unspliced_gasket.step": 1,
        "trimmed_unspliced_assembly.step": 3,
    }
    for filename, solid_count in expected.items():
        record = records.get(filename, {})
        if (
            record.get("source_solid_count") != solid_count
            or record.get("imported_solid_count") != solid_count
            or record.get("all_imported_solids_valid") is not True
        ):
            raise ValueError(
                f"Candidate round-trip record failed for {filename}: {record}"
            )


def main() -> None:
    paths = {
        "bucket": CANDIDATE / "trimmed_unspliced_bucket.step",
        "baffle": CANDIDATE / "trimmed_unspliced_baffle.step",
        "gasket": CANDIDATE / "trimmed_unspliced_gasket.step",
    }
    diagnostics_path = CANDIDATE / "diagnostics.json"
    missing = [
        str(path)
        for path in (*paths.values(), diagnostics_path)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Missing candidate check inputs: {missing}")

    shapes = {name: import_step(path) for name, path in paths.items()}
    for name, shape in shapes.items():
        if len(shape.solids()) != 1 or not shape.is_valid:
            raise ValueError(f"{name} is not one valid imported solid")

    apply, restore, _originals = validator._patch_seam()
    apply()
    try:
        flat_bottom = validator._flat_bottom_audit(shapes)
        print_contact = validator._baffle_print_contact_audit(
            shapes["baffle"]
        )
    finally:
        restore()

    full_base = import_step(validator.AUTHORITATIVE_BASE_STEP)
    body_retention = validator._enclosure_body_audit(
        full_base,
        {"bucket": shapes["bucket"]},
        {"bucket": shapes["bucket"]},
    )
    diagnostics = json.loads(diagnostics_path.read_text())
    _assert_round_trip_records(diagnostics["round_trip"])

    if (
        diagnostics["bucket_baffle_overlap_mm3"] > 1e-6
        or diagnostics["gasket_bucket_overlap_mm3"] > 1e-6
        or diagnostics["gasket_baffle_overlap_mm3"] > 1e-6
    ):
        raise ValueError("Candidate part overlap is nonzero")
    joint = diagnostics["joint_audit"]
    minimum_support = validator.model.MINIMUM_GASKET_SUPPORT_RATIO
    if min(
        joint["gasket_bucket_support_ratio"],
        joint["gasket_baffle_support_ratio"],
    ) < minimum_support:
        raise ValueError("Candidate gasket support is below the existing limit")

    result = {
        "scope": (
            "existing standalone-validator checks applied to exported "
            "trimmed no-splice candidate"
        ),
        "single_valid_solid": {name: True for name in shapes},
        "complete_enclosure_body_retained": body_retention,
        "flat_bottom_and_seal_continuity": flat_bottom,
        "baffle_print_contact": print_contact,
        "gasket_support": {
            "bucket_ratio": joint["gasket_bucket_support_ratio"],
            "baffle_ratio": joint["gasket_baffle_support_ratio"],
            "minimum_ratio": minimum_support,
        },
        "overlap_mm3": {
            "bucket_baffle": diagnostics["bucket_baffle_overlap_mm3"],
            "gasket_bucket": diagnostics["gasket_bucket_overlap_mm3"],
            "gasket_baffle": diagnostics["gasket_baffle_overlap_mm3"],
        },
        "step_round_trip": diagnostics["round_trip"],
        "shared_source_state_restored": diagnostics[
            "ancestor_state_restored"
        ],
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
