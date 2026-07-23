from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode
import shutil
import subprocess
import sys
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
        self.repository_root = root
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
        self.sidecar_path = self.root / ".synthetic_joint.step.glb"
        self.snapshot_path = self.root / "synthetic_joint_section.png"
        self.source_path = self.root / "synthetic_joint.py"
        self.input_path = self.root / "parameters.json"
        self.artifact_path.write_bytes(b"synthetic STEP evidence")
        self.sidecar_path.write_bytes(b"synthetic topology sidecar")
        self.snapshot_path.write_bytes(b"synthetic rendered PNG")
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
        paths = (self.artifact_path, self.sidecar_path, self.snapshot_path)
        relative_paths = tuple(
            str(path.relative_to(self.repository_root)) for path in paths
        )
        artifacts = tuple(
            replace(
                artifact,
                path=relative_path,
                source_fingerprint=fingerprint_collection(sources),
                input_fingerprint=fingerprint_collection(inputs),
            )
            for artifact, relative_path in zip(
                packet.artifacts, relative_paths, strict=True
            )
        )
        visual = list(packet.visual_evidence)
        viewer_url = "http://127.0.0.1:4178/?" + urlencode(
            {"dir": str(self.artifact_path.parent), "file": self.artifact_path.name}
        )
        visual[0] = replace(visual[0], locator=viewer_url)
        visual[1] = replace(visual[1], locator=relative_paths[2])
        viewer_record = replace(packet.viewer_records[0], url=viewer_url)
        outputs = tuple(
            replace(output, path=relative_path)
            for output, relative_path in zip(
                packet.jobs[0].outputs, relative_paths, strict=True
            )
        )
        return replace(
            packet,
            source_fingerprints=sources,
            input_fingerprints=inputs,
            artifacts=artifacts,
            visual_evidence=tuple(visual),
            viewer_records=(viewer_record,),
            jobs=(replace(packet.jobs[0], outputs=outputs),),
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

    def test_visual_evidence_requires_valid_locator_render_and_attestation(
        self,
    ) -> None:
        packet = self._packet()
        self.snapshot_path.unlink()
        self.assertEqual(self._verify_packet(packet), 1)

        self.snapshot_path.write_bytes(b"synthetic rendered PNG")
        viewer, snapshot = packet.visual_evidence
        invalid_url = "https://example.invalid/viewer?file=anything.step"
        invalid_viewer = replace(viewer, locator=invalid_url)
        invalid_record = replace(packet.viewer_records[0], url=invalid_url)
        self.assertEqual(
            self._verify_packet(
                replace(
                    packet,
                    visual_evidence=(invalid_viewer, snapshot),
                    viewer_records=(invalid_record,),
                )
            ),
            1,
        )
        self.assertEqual(
            self._verify_packet(replace(packet, inspection_attestations=())),
            1,
        )

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

    def test_verify_is_self_contained_without_runner_or_project_config(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimal-verification-") as directory:
            root = Path(directory)
            shutil.copytree(
                self.repository_root / "cad_verification",
                root / "cad_verification",
            )
            (root / "scripts").mkdir()
            for name in ("cad_review.py", "cad_verification_io.py"):
                shutil.copy2(
                    self.repository_root / "scripts" / name,
                    root / "scripts" / name,
                )
            (root / "examples").mkdir()
            (root / "examples/synthetic_joint.py").write_bytes(b"synthetic source")
            (root / "examples/parameters.json").write_bytes(b'{"length":80}')
            evidence_root = root / "build/examples"
            evidence_root.mkdir(parents=True)
            step = evidence_root / "synthetic_joint.step"
            sidecar = evidence_root / ".synthetic_joint.step.glb"
            snapshot = evidence_root / "synthetic_joint_section.png"
            step.write_bytes(b"synthetic STEP evidence")
            sidecar.write_bytes(b"synthetic topology sidecar")
            snapshot.write_bytes(b"synthetic rendered PNG")

            contract = minimal_contract()
            packet = minimal_review_packet(contract)
            viewer_url = "http://127.0.0.1:4178/?" + urlencode(
                {"dir": str(evidence_root.resolve()), "file": step.name}
            )
            visual = list(packet.visual_evidence)
            visual[0] = replace(visual[0], locator=viewer_url)
            packet = replace(
                packet,
                visual_evidence=tuple(visual),
                viewer_records=(replace(packet.viewer_records[0], url=viewer_url),),
            )
            contract_path = root / "contract.json"
            packet_path = root / "packet.json"
            contract_path.write_text(contract_to_json(contract))

            def run_packet(value) -> int:
                packet_path.write_text(review_packet_to_json(value))
                completed = subprocess.run(
                    [
                        sys.executable,
                        "scripts/cad_review.py",
                        "verify",
                        "packet",
                        str(contract_path),
                        str(packet_path),
                        "--profile",
                        "release",
                        "--json",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.minimal_verify_output = completed.stdout + completed.stderr
                return completed.returncode

            self.assertFalse((root / ".cad-project").exists())
            self.assertFalse((root / "cad_runner").exists())
            self.assertEqual(run_packet(packet), 0, self.minimal_verify_output)
            failed = replace(
                packet.results[0],
                status=ResultStatus.FAIL,
                actual=ActualValue(70.0, Unit.MILLIMETER),
            )
            self.assertEqual(
                run_packet(replace(packet, results=(failed, *packet.results[1:]))),
                1,
            )
            self.assertEqual(
                run_packet(
                    replace(
                        packet,
                        results=(
                            *packet.results[:-1],
                            unverified("CAD-VIS-001", "attestation removed"),
                        ),
                    )
                ),
                1,
            )
            snapshot.unlink()
            self.assertEqual(run_packet(packet), 1)
            snapshot.write_bytes(b"synthetic rendered PNG")
            (root / "examples/synthetic_joint.py").write_bytes(b"stale source")
            self.assertEqual(run_packet(packet), 1)
            packet_path.write_text("{malformed")
            malformed = subprocess.run(
                [
                    sys.executable,
                    "scripts/cad_review.py",
                    "verify",
                    "packet",
                    str(contract_path),
                    str(packet_path),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(malformed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
