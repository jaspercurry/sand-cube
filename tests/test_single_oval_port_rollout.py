from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from cad_verification import (
    VerificationProfile,
    requirements_for_profile,
    validate_contract,
)
from experiments.sand_cube_190x210_single_oval_port.verification import (
    STEP_OUTPUTS,
    bind_candidate,
    design_contract,
    validate_visual_acceptance,
)
from scripts.check_cad_entrypoints import (
    _module_requires_cad,
    production_review_violations,
    source_requires_cad_guard,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = (
    ROOT
    / "experiments/sand_cube_190x210_single_oval_port/"
    "generate_sand_cube_190x210_single_oval_port.py"
)


def test_production_generate_path_has_no_review_work_or_subprocesses() -> None:
    source = GENERATOR.read_text(encoding="utf-8")

    assert production_review_violations(
        GENERATOR.relative_to(ROOT),
        source,
    ) == []


def test_production_review_policy_detects_atomic_worker_coupling() -> None:
    source = """
def generate():
    subprocess.run(["python", "generate_static_ocp_viewer.py"], check=True)
"""

    violations = production_review_violations(Path("model.py"), source)

    assert any("launches subprocess" in item for item in violations)
    assert any("review target" in item for item in violations)


def test_native_entrypoint_policy_classifies_only_geometry_checks_native() -> None:
    assert not _module_requires_cad("cad_geometry_checks")
    assert _module_requires_cad("cad_geometry_checks.native")
    assert _module_requires_cad("cad_geometry_checks.native.measurements")
    assert source_requires_cad_guard(
        "from cad_geometry_checks.native import measure_intersection\n"
    )
    assert not source_requires_cad_guard(
        "from cad_geometry_checks import BooleanOutcome\n"
    )


def test_rollout_contract_is_native_free_and_uses_composed_profiles() -> None:
    program = (
        "from experiments.sand_cube_190x210_single_oval_port.verification "
        "import design_contract; import sys; design_contract(); "
        "forbidden=('build123d','OCP','cad_runner'); "
        "loaded=[name for name in sys.modules if name.split('.')[0] in forbidden]; "
        "assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    contract = design_contract()
    assert validate_contract(contract) == ()
    assert len(requirements_for_profile(contract, VerificationProfile.FAST)) == 2
    assert len(requirements_for_profile(contract, VerificationProfile.FIT)) == 8
    assert len(requirements_for_profile(contract, VerificationProfile.RELEASE)) == 11


def test_candidate_binding_rejects_missing_or_failed_roundtrip(
    tmp_path: Path,
) -> None:
    generator = tmp_path / "experiments/model.py"
    generator.parent.mkdir(parents=True)
    generator.write_text("SOURCE = 'test'\n", encoding="utf-8")
    output = tmp_path / "build/sand_cube_190x210_single_oval_port"
    output.mkdir(parents=True)
    roundtrip = {}
    for index, name in enumerate(STEP_OUTPUTS):
        (output / name).write_bytes(f"STEP-{index}".encode())
        roundtrip[name] = {
            "source_solid_count": 1,
            "imported_solid_count": 1,
            "solid_count_matches": True,
            "all_imported_solids_valid": True,
        }
    diagnostics = {"geometry": {"step_roundtrip": roundtrip}}
    (output / "diagnostics.json").write_text(
        json.dumps(diagnostics),
        encoding="utf-8",
    )

    candidate = bind_candidate(
        repo_root=tmp_path,
        artifact_dir=output,
        generator=generator,
    )

    assert candidate["candidate_id"]
    assert [item["name"] for item in candidate["outputs"]] == list(STEP_OUTPUTS)
    roundtrip[STEP_OUTPUTS[-1]]["all_imported_solids_valid"] = False
    (output / "diagnostics.json").write_text(
        json.dumps(diagnostics),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="round-trip is not passing"):
        bind_candidate(
            repo_root=tmp_path,
            artifact_dir=output,
            generator=generator,
        )


def test_cutaway_remains_a_required_lineage_output() -> None:
    cutaway = "sand_cube_190x210_single_oval_port_cutaway.step"
    consumers = (
        "experiments/"
        "sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_conformal_full_system/"
        "generate_sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_conformal_full_system.py",
        "experiments/"
        "sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_printable_bucket/"
        "generate_sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_printable_bucket.py",
    )

    assert cutaway in STEP_OUTPUTS
    for relative in consumers:
        assert cutaway in (ROOT / relative).read_text(encoding="utf-8")


def test_visual_acceptance_is_bound_to_candidate_and_review_lineage(
    tmp_path: Path,
) -> None:
    step_path = "build/model_hardware_check.step"
    sidecar_path = "build/.model_hardware_check.step.glb"
    snapshot_path = "build/review.png"
    snapshot_provenance_path = "build/snapshot-provenance.json"
    static_review_path = "build/review-provenance.json"
    acceptance_path = "build/visual-acceptance.json"
    step = tmp_path / step_path
    sidecar = tmp_path / sidecar_path
    snapshot = tmp_path / snapshot_path
    step.parent.mkdir(parents=True)
    step.write_bytes(b"STEP")
    sidecar.write_bytes(b"GLB")
    snapshot.write_bytes(b"PNG")

    def digest(path: Path) -> str:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest()

    static_review = {
        "step": {"path": step_path, "sha256": digest(step)},
        "sidecar": {"path": sidecar_path, "sha256": digest(sidecar)},
    }
    static_review_file = tmp_path / static_review_path
    static_review_file.write_text(json.dumps(static_review), encoding="utf-8")
    snapshot_provenance = {
        "sources": [
            {"kind": "step", "path": step_path, "sha256": digest(step)},
            {"kind": "sidecar", "path": sidecar_path, "sha256": digest(sidecar)},
        ]
    }
    snapshot_provenance_file = tmp_path / snapshot_provenance_path
    snapshot_provenance_file.write_text(
        json.dumps(snapshot_provenance),
        encoding="utf-8",
    )
    acceptance = {
        "accepted": True,
        "candidate_id": "candidate-a",
        "measurable_claims_from_pixels": [],
        "snapshot": {"path": snapshot_path, "sha256": digest(snapshot)},
        "snapshot_provenance": {
            "path": snapshot_provenance_path,
            "sha256": digest(snapshot_provenance_file),
        },
        "static_review_provenance": {
            "path": static_review_path,
            "sha256": digest(static_review_file),
        },
    }
    acceptance_file = tmp_path / acceptance_path
    acceptance_file.write_text(json.dumps(acceptance), encoding="utf-8")
    evidence = tuple(
        (path, digest(tmp_path / path))
        for path in (
            snapshot_path,
            snapshot_provenance_path,
            static_review_path,
            acceptance_path,
        )
    )
    candidate = {
        "candidate_id": "candidate-a",
        "outputs": [
            {
                "name": "model_hardware_check.step",
                "path": step_path,
                "sha256": digest(step),
            }
        ],
    }

    assert validate_visual_acceptance(
        candidate,
        evidence,
        repo_root=tmp_path,
    ) == (
        acceptance_path,
        snapshot_path,
        snapshot_provenance_path,
        static_review_path,
    )
    candidate["candidate_id"] = "candidate-b"
    with pytest.raises(ValueError, match="different candidate"):
        validate_visual_acceptance(candidate, evidence, repo_root=tmp_path)
