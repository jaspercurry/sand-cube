"""Run the complete native-CAD-free development check suite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]


def lightweight_checks(python: str = sys.executable) -> tuple[Check, ...]:
    """Return the authoritative ordered lightweight-check plan."""

    return (
        Check("unit tests", (python, "-m", "pytest", "-q")),
        Check(
            "model catalog consistency",
            (python, "scripts/cad_review.py", "check-catalog"),
        ),
        Check(
            "CAD entrypoint safety",
            (python, "scripts/check_cad_entrypoints.py"),
        ),
        Check(
            "lint",
            (
                python,
                "-m",
                "ruff",
                "check",
                "cad_verification",
                "cad_runner/statistics.py",
                "scripts/cad_review.py",
                "scripts/cad_verification_io.py",
                "scripts/check_cad_entrypoints.py",
                "scripts/check_lightweight.py",
                "scripts/model_catalog.py",
                "tests/test_cad_job_statistics.py",
                "tests/test_cad_review.py",
                "tests/test_cad_verification_cli.py",
                "tests/test_cad_verification_contract_model.py",
                "tests/test_cad_verification_review_packet.py",
                "tests/test_joint_coupon_verification.py",
                "tests/test_lightweight_checks.py",
                "tests/test_model_catalog.py",
                "workbench/designs/joint_coupon/packet.py",
                "workbench/designs/joint_coupon/parameters.py",
                "workbench/designs/joint_coupon/verification.py",
            ),
        ),
    )


def run_checks(checks: Sequence[Check]) -> int:
    failures: list[str] = []
    for check in checks:
        print(f"\n== {check.name} ==", flush=True)
        completed = subprocess.run(check.command, cwd=ROOT, check=False)
        if completed.returncode:
            failures.append(check.name)
    if failures:
        print(f"\nFAILED: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nAll lightweight checks passed.")
    return 0


def main() -> int:
    return run_checks(lightweight_checks())


if __name__ == "__main__":
    raise SystemExit(main())
