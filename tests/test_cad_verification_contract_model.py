from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import unittest

from cad_verification import (
    ARTIFACT_POLICIES,
    CHECK_POLICIES,
    EVIDENCE_POLICIES,
    PROFILE_POLICIES,
    ActualValue,
    ArtifactRole,
    CheckKind,
    CheckSpec,
    EvidenceChannel,
    ResultStatus,
    SerializationError,
    Tolerance,
    Unit,
    VerificationProfile,
    actual_satisfies,
    aggregate_status,
    assess,
    contract_from_json,
    contract_to_dict,
    contract_to_json,
    requirements_for_profile,
    unverified,
    validate_contract,
)
from cad_verification.examples import minimal_contract, minimal_review_packet


class CadVerificationContractModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = minimal_contract()

    def issue_codes(self, contract) -> set[str]:
        return {issue.code for issue in validate_contract(contract)}

    def test_policy_catalogs_are_complete_single_sources(self) -> None:
        self.assertEqual(set(ARTIFACT_POLICIES), set(ArtifactRole))
        self.assertEqual(set(PROFILE_POLICIES), set(VerificationProfile))
        self.assertEqual(set(EVIDENCE_POLICIES), set(EvidenceChannel))
        self.assertEqual(set(CHECK_POLICIES), set(CheckKind))

    def test_synthetic_contract_is_valid(self) -> None:
        self.assertEqual(validate_contract(self.contract), ())

    def test_profiles_compose_cost_layers_without_requirement_duplication(self) -> None:
        fast = requirements_for_profile(self.contract, VerificationProfile.FAST)
        fit = requirements_for_profile(self.contract, VerificationProfile.FIT)
        release = requirements_for_profile(
            self.contract,
            VerificationProfile.RELEASE,
        )

        self.assertEqual([item.requirement_id for item in fast], ["CAD-DIM-001"])
        self.assertEqual(
            [item.requirement_id for item in fit],
            ["CAD-DIM-001", "CAD-FIT-001"],
        )
        self.assertEqual(len(release), 4)
        self.assertEqual(len({item.requirement_id for item in release}), 4)

    def test_duplicate_requirement_ids_are_rejected(self) -> None:
        requirements = list(self.contract.requirements)
        requirements[1] = replace(
            requirements[1],
            requirement_id=requirements[0].requirement_id,
        )
        malformed = replace(self.contract, requirements=tuple(requirements))

        self.assertIn("requirement.duplicate_id", self.issue_codes(malformed))

    def test_invalid_unit_and_tolerance_are_rejected(self) -> None:
        requirements = list(self.contract.requirements)
        requirements[0] = replace(
            requirements[0],
            unit=Unit.BOOLEAN,
            tolerance=Tolerance(-0.1),
        )
        malformed = replace(self.contract, requirements=tuple(requirements))

        codes = self.issue_codes(malformed)
        self.assertIn("unit.mismatch", codes)
        self.assertIn("tolerance.invalid", codes)

    def test_vacuous_fit_profile_is_rejected(self) -> None:
        requirements = list(self.contract.requirements)
        requirements[1] = replace(
            requirements[1],
            check=CheckSpec(CheckKind.DIMENSION, "kernel.another_dimension"),
        )
        malformed = replace(self.contract, requirements=tuple(requirements))

        self.assertIn("profile.vacuous", self.issue_codes(malformed))

    def test_empty_profile_and_incomplete_release_are_rejected(self) -> None:
        requirements = tuple(
            requirement
            for requirement in self.contract.requirements
            if requirement.cost_profile is VerificationProfile.FAST
        )
        malformed = replace(self.contract, requirements=requirements)

        codes = self.issue_codes(malformed)
        self.assertIn("profile.empty", codes)
        self.assertIn("profile.required_check_missing", codes)

    def test_range_and_exact_evaluation_honor_absolute_tolerance(self) -> None:
        fit = self.contract.requirements[1]
        self.assertTrue(
            actual_satisfies(fit, ActualValue(0.19, Unit.MILLIMETER))
        )
        self.assertFalse(
            actual_satisfies(fit, ActualValue(0.18, Unit.MILLIMETER))
        )

        dimension = self.contract.requirements[0]
        self.assertEqual(
            assess(
                dimension,
                ActualValue(80.009, Unit.MILLIMETER),
                evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
                diagnostic="within tolerance",
            ).status,
            ResultStatus.PASS,
        )

    def test_unverified_and_missing_results_never_aggregate_to_pass(self) -> None:
        passing = minimal_review_packet(self.contract).results
        self.assertEqual(aggregate_status(passing), ResultStatus.PASS)
        self.assertEqual(
            aggregate_status((unverified("CAD-DIM-001", "not run"),)),
            ResultStatus.UNVERIFIED,
        )
        self.assertEqual(
            aggregate_status(passing, missing_requirements=True),
            ResultStatus.UNVERIFIED,
        )
        failing = replace(passing[0], status=ResultStatus.FAIL)
        self.assertEqual(
            aggregate_status((unverified("CAD-FIT-001", "not run"), failing)),
            ResultStatus.FAIL,
        )
    def test_contract_serialization_is_deterministic_and_round_trips(self) -> None:
        encoded = contract_to_json(self.contract)
        decoded = contract_from_json(encoded)

        self.assertEqual(encoded, contract_to_json(decoded))
        self.assertEqual(decoded, self.contract)
        self.assertEqual(encoded, contract_to_json(self.contract))

    def test_deserialization_rejects_unknown_enums_and_duplicate_keys(
        self,
    ) -> None:
        data = contract_to_dict(self.contract)
        data["requirements"][0]["unit"] = "furlong"
        with self.assertRaises(SerializationError):
            contract_from_json(json.dumps(data))

        with self.assertRaisesRegex(SerializationError, "duplicate JSON key"):
            contract_from_json('{"schema_version":1,"schema_version":1}')

    def test_core_import_does_not_load_native_cad_modules(self) -> None:
        root = Path(__file__).resolve().parents[1]
        program = (
            "import cad_verification, sys; "
            "forbidden=('build123d','OCP','cad_runner'); "
            "loaded=[name for name in sys.modules if name.split('.')[0] in forbidden]; "
            "assert not loaded, loaded"
        )
        completed = subprocess.run(
            [sys.executable, "-c", program],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
