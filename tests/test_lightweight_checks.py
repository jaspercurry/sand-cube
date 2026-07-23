from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

from scripts.check_lightweight import lightweight_checks, run_checks


def test_lightweight_plan_is_complete_and_never_launches_a_cad_target() -> None:
    checks = lightweight_checks("python")

    assert [check.name for check in checks] == [
        "unit tests",
        "model catalog consistency",
        "CAD entrypoint safety",
        "lint",
    ]
    commands = [check.command for check in checks]
    assert commands == [
        ("python", "-m", "pytest", "-q"),
        ("python", "scripts/cad_review.py", "check-catalog"),
        ("python", "scripts/check_cad_entrypoints.py"),
        (
            "python",
            "-m",
            "ruff",
            "check",
            "cad_verification",
            "cad_runner",
            "scripts/cad_review.py",
            "scripts/cad_workflow_cli.py",
            "scripts/cad_verification_io.py",
            "scripts/check_cad_entrypoints.py",
            "scripts/check_lightweight.py",
            "scripts/model_catalog.py",
            "scripts/text_to_cad_artifacts.py",
            "src/enclosure_family",
            "tests/test_cad_job_statistics.py",
            "tests/test_cad_review.py",
            "tests/test_cad_workflow.py",
            "tests/test_cad_verification_cli.py",
            "tests/test_cad_verification_contract_model.py",
            "tests/test_cad_verification_review_packet.py",
            "tests/test_enclosure_family_coordinate_contract.py",
            "tests/test_joint_coupon_verification.py",
            "tests/test_lightweight_checks.py",
            "tests/test_model_catalog.py",
            "tests/test_cad_runner.py",
            "workbench/designs/joint_coupon/packet.py",
            "workbench/designs/joint_coupon/parameters.py",
            "workbench/designs/joint_coupon/verification.py",
        ),
    ]
    assert not any(
        "generate_" in argument for command in commands for argument in command
    )


def test_lightweight_runner_reports_all_failures_in_one_pass() -> None:
    checks = lightweight_checks("python")
    results = [
        SimpleNamespace(returncode=1),
        SimpleNamespace(returncode=0),
        SimpleNamespace(returncode=1),
        SimpleNamespace(returncode=0),
    ]

    with mock.patch("scripts.check_lightweight.subprocess.run", side_effect=results) as run:
        returncode = run_checks(checks)

    assert returncode == 1
    assert run.call_count == len(checks)
