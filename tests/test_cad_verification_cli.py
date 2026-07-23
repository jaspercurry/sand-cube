from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from cad_verification import (
    ActualValue,
    Fingerprint,
    ResultStatus,
    Unit,
    contract_to_json,
    fingerprint_collection,
    review_packet_to_json,
    unverified,
)
from cad_verification.examples import minimal_contract, minimal_review_packet
from scripts.cad_review import main


class CadVerificationCliTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        build = root / "build"
        build.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix="verification-cli-",
            dir=build,
        )
        self.root = Path(self.temporary.name)
        self.contract = minimal_contract()
        self.contract_path = self.root / "contract.json"
        self.packet_path = self.root / "packet.json"
        self.artifact_path = self.root / "synthetic_joint.step"
        self.source_path = self.root / "synthetic_joint.py"
        self.input_path = self.root / "parameters.json"
        self.artifact_path.write_bytes(b"synthetic STEP evidence")
        self.source_path.write_bytes(b"synthetic source")
        self.input_path.write_bytes(b'{"length":80}')
        self.contract_path.write_text(contract_to_json(self.contract))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _packet(self):
        packet = minimal_review_packet(self.contract)
        sources = (
            Fingerprint(str(self.source_path), packet.source_fingerprints[0].sha256),
        )
        inputs = (
            Fingerprint(str(self.input_path), packet.input_fingerprints[0].sha256),
        )
        artifact = replace(
            packet.artifacts[0],
            path=str(self.artifact_path),
            source_fingerprint=fingerprint_collection(sources),
            input_fingerprint=fingerprint_collection(inputs),
        )
        return replace(
            packet,
            source_fingerprints=sources,
            input_fingerprints=inputs,
            artifacts=(artifact,),
        )

    def _run(self, *arguments: str) -> int:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return main(list(arguments))

    def _verify_packet(self, packet) -> int:
        self.packet_path.write_text(review_packet_to_json(packet))
        return self._run(
            "verify",
            "packet",
            str(self.contract_path),
            str(self.packet_path),
            "--profile",
            "release",
            "--json",
        )

    def test_valid_contract_and_complete_packet_succeed(self) -> None:
        self.assertEqual(
            self._run(
                "verify",
                "contract",
                str(self.contract_path),
                "--profile",
                "fit",
            ),
            0,
        )
        self.assertEqual(self._verify_packet(self._packet()), 0)

    def test_failed_and_unverified_results_never_succeed(self) -> None:
        packet = self._packet()
        failed = replace(
            packet.results[0],
            status=ResultStatus.FAIL,
            actual=ActualValue(79.0, Unit.MILLIMETER),
        )
        self.assertEqual(
            self._verify_packet(replace(packet, results=(failed, *packet.results[1:]))),
            1,
        )

        results = (*packet.results[:-1], unverified("CAD-VIS-001", "not inspected"))
        self.assertEqual(self._verify_packet(replace(packet, results=results)), 1)

    def test_missing_and_stale_artifacts_never_succeed(self) -> None:
        packet = self._packet()
        self.artifact_path.unlink()
        self.assertEqual(self._verify_packet(packet), 1)

        self.artifact_path.write_bytes(b"changed after packet creation")
        self.assertEqual(self._verify_packet(packet), 1)

    def test_stale_source_fingerprint_never_succeeds(self) -> None:
        packet = self._packet()
        self.source_path.write_bytes(b"changed source")
        self.assertEqual(self._verify_packet(packet), 1)

    def test_missing_result_and_profile_mismatch_never_succeed(self) -> None:
        packet = self._packet()
        self.assertEqual(
            self._verify_packet(replace(packet, results=packet.results[:-1])),
            1,
        )
        self.packet_path.write_text(review_packet_to_json(packet))
        self.assertEqual(
            self._run(
                "verify",
                "packet",
                str(self.contract_path),
                str(self.packet_path),
                "--profile",
                "fit",
            ),
            1,
        )

    def test_malformed_contract_and_packet_return_usage_error(self) -> None:
        self.contract_path.write_text("{not-json")
        self.assertEqual(
            self._run(
                "verify",
                "contract",
                str(self.contract_path),
                "--profile",
                "fast",
            ),
            2,
        )

        self.contract_path.write_text(contract_to_json(self.contract))
        self.packet_path.write_text("[]")
        self.assertEqual(
            self._run(
                "verify",
                "packet",
                str(self.contract_path),
                str(self.packet_path),
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
