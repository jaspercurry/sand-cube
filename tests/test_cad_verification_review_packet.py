from __future__ import annotations

from dataclasses import replace
import json
import unittest

from cad_verification import (
    ActualValue,
    ArtifactObservation,
    EvidenceChannel,
    EvidenceScope,
    ResultStatus,
    SerializationError,
    Unit,
    VerificationProfile,
    profile_status,
    review_packet_from_json,
    review_packet_to_dict,
    review_packet_to_json,
    unverified,
    validate_review_packet,
)
from cad_verification.examples import minimal_contract, minimal_review_packet


class FakeArtifactProbe:
    def __init__(self, observations: dict[str, ArtifactObservation]):
        self.observations = observations

    def inspect(self, path: str) -> ArtifactObservation:
        return self.observations.get(path, ArtifactObservation(exists=False))


class CadVerificationReviewPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = minimal_contract()
        self.packet = minimal_review_packet(self.contract)

    def issue_codes(self, packet, *, probe=None) -> set[str]:
        return {
            issue.code
            for issue in validate_review_packet(
                packet,
                self.contract,
                artifact_probe=probe,
            )
        }

    def test_synthetic_release_packet_is_valid_and_passes(self) -> None:
        self.assertEqual(validate_review_packet(self.packet, self.contract), ())
        self.assertEqual(
            profile_status(
                self.contract,
                VerificationProfile.RELEASE,
                self.packet.results,
            ),
            ResultStatus.PASS,
        )

    def test_standard_packet_contains_required_sections_and_derived_tier(self) -> None:
        data = review_packet_to_dict(self.packet)
        required = {
            "source_fingerprints",
            "input_fingerprints",
            "model",
            "toolchain",
            "artifacts",
            "results",
            "jobs",
            "visual_evidence",
            "inspection_attestations",
            "viewer_records",
            "confirmed_facts",
            "remaining_uncertainty",
        }
        self.assertTrue(required.issubset(data))
        tiers = {result["evidence_tier"] for result in data["results"]}
        self.assertIn("authoritative", tiers)
        self.assertIn("agent_review", tiers)

    def test_packet_serialization_is_deterministic_and_round_trips(self) -> None:
        encoded = review_packet_to_json(self.packet)
        decoded = review_packet_from_json(encoded, contract=self.contract)

        self.assertEqual(encoded, review_packet_to_json(decoded))
        self.assertEqual(validate_review_packet(decoded, self.contract), ())

    def test_deserialization_rejects_evidence_tier_drift(self) -> None:
        data = review_packet_to_dict(self.packet)
        data["results"][0]["evidence_tier"] = "human_interactive"

        with self.assertRaisesRegex(SerializationError, "channel policy"):
            review_packet_from_json(json.dumps(data), contract=self.contract)

    def test_missing_result_is_reported_and_profile_remains_unverified(self) -> None:
        packet = replace(self.packet, results=self.packet.results[:-1])

        self.assertIn("result.missing", self.issue_codes(packet))
        self.assertEqual(
            profile_status(
                self.contract,
                VerificationProfile.RELEASE,
                packet.results,
            ),
            ResultStatus.UNVERIFIED,
        )

    def test_explicit_unverified_result_is_valid_but_never_passes(self) -> None:
        results = list(self.packet.results)
        results[-1] = unverified("CAD-VIS-001", "human review not yet supplied")
        packet = replace(self.packet, results=tuple(results))

        self.assertEqual(validate_review_packet(packet, self.contract), ())
        self.assertEqual(
            profile_status(
                self.contract,
                VerificationProfile.RELEASE,
                packet.results,
            ),
            ResultStatus.UNVERIFIED,
        )

    def test_programmatic_measurements_cannot_pass_from_snapshot_pixels(self) -> None:
        results = list(self.packet.results)
        results[0] = replace(
            results[0],
            evidence_channel=EvidenceChannel.SNAPSHOT,
            evidence_refs=("snapshot.joint-section",),
        )
        packet = replace(self.packet, results=tuple(results))

        self.assertIn("result.channel_not_authoritative", self.issue_codes(packet))

    def test_visual_routing_rules_are_enforced(self) -> None:
        viewer, snapshot = self.packet.visual_evidence
        cases = {
            "viewer_read_only": (
                replace(viewer, read_only=False),
                "visual.not_read_only",
            ),
            "snapshot_scope": (
                replace(snapshot, scope=EvidenceScope.SCRATCH),
                "visual.scope_invalid",
            ),
            "snapshot_attestation": (
                replace(snapshot, attestation_id=None),
                "visual.attestation_missing",
            ),
            "mcp_exported": (
                replace(
                    snapshot,
                    channel=EvidenceChannel.MCP_RENDER_VIEW,
                    scope=EvidenceScope.EXPORTED_ARTIFACT,
                ),
                "visual.scope_invalid",
            ),
            "focused_reason": (
                replace(
                    snapshot,
                    channel=EvidenceChannel.FOCUSED_RENDERER,
                    reason=None,
                ),
                "visual.reason_missing",
            ),
            "browser_reason": (
                replace(
                    snapshot,
                    channel=EvidenceChannel.BROWSER_AUTOMATION,
                    reason=None,
                ),
                "visual.reason_missing",
            ),
        }
        for label, (replacement, expected_code) in cases.items():
            with self.subTest(label=label):
                visual = tuple(
                    replacement if item.evidence_id == replacement.evidence_id else item
                    for item in self.packet.visual_evidence
                )
                packet = replace(self.packet, visual_evidence=visual)
                self.assertIn(expected_code, self.issue_codes(packet))

    def test_stale_artifact_provenance_is_rejected(self) -> None:
        artifact = replace(
            self.packet.artifacts[0],
            source_fingerprint="0" * 64,
        )
        packet = replace(self.packet, artifacts=(artifact,))

        self.assertIn("artifact.stale_provenance", self.issue_codes(packet))

    def test_artifact_probe_catches_missing_hash_and_size_evidence(self) -> None:
        artifact = self.packet.artifacts[0]
        cases = {
            "missing": (
                ArtifactObservation(exists=False),
                "artifact.missing",
            ),
            "hash": (
                ArtifactObservation(
                    exists=True,
                    sha256="f" * 64,
                    size_bytes=artifact.size_bytes,
                ),
                "artifact.hash_mismatch",
            ),
            "size": (
                ArtifactObservation(
                    exists=True,
                    sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes + 1,
                ),
                "artifact.size_mismatch",
            ),
        }
        for label, (observation, expected_code) in cases.items():
            with self.subTest(label=label):
                probe = FakeArtifactProbe({artifact.path: observation})
                self.assertIn(expected_code, self.issue_codes(self.packet, probe=probe))

    def test_matching_artifact_probe_is_accepted(self) -> None:
        probe = FakeArtifactProbe(
            {
                artifact.path: ArtifactObservation(
                    exists=True,
                    sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes,
                )
                for artifact in self.packet.artifacts
            }
        )

        self.assertEqual(
            validate_review_packet(
                self.packet,
                self.contract,
                artifact_probe=probe,
            ),
            (),
        )

    def test_status_and_evidence_references_must_match_claims(self) -> None:
        results = list(self.packet.results)
        results[0] = replace(results[0], status=ResultStatus.FAIL)
        results[2] = replace(results[2], evidence_refs=("artifact.unknown",))
        packet = replace(self.packet, results=tuple(results))

        codes = self.issue_codes(packet)
        self.assertIn("result.status_mismatch", codes)
        self.assertIn("result.evidence_unknown", codes)
        self.assertIn("result.artifact_evidence_missing", codes)

    def test_result_units_must_match_the_contract(self) -> None:
        results = list(self.packet.results)
        results[0] = replace(
            results[0],
            actual=ActualValue(80.0, Unit.CUBIC_MILLIMETER),
            status=ResultStatus.FAIL,
        )
        packet = replace(self.packet, results=tuple(results))

        self.assertIn("result.unit_mismatch", self.issue_codes(packet))

    def test_invalid_job_metrics_are_rejected(self) -> None:
        metrics = replace(
            self.packet.jobs[0],
            elapsed_seconds=-1.0,
            orphan_processes=-1,
        )
        packet = replace(self.packet, jobs=(metrics,))

        codes = self.issue_codes(packet)
        self.assertIn("job.elapsed_invalid", codes)
        self.assertIn("job.orphans_invalid", codes)

    def test_every_failed_execution_state_blocks_pass_eligibility(self) -> None:
        metrics = self.packet.jobs[0]
        cases = {
            "state": (replace(metrics, state="failed"), "job.state_failed"),
            "exit": (replace(metrics, exit_code=137), "job.exit_failed"),
            "cleanup": (
                replace(metrics, cleanup_completed=False),
                "job.cleanup_failed",
            ),
            "orphans": (
                replace(metrics, orphan_processes=4),
                "job.orphans_remain",
            ),
        }
        for label, (replacement, expected) in cases.items():
            with self.subTest(label=label):
                packet = replace(self.packet, jobs=(replacement,))
                self.assertIn(expected, self.issue_codes(packet))

    def test_artifacts_are_hash_bound_to_successful_job_outputs(self) -> None:
        metrics = self.packet.jobs[0]
        outputs = list(metrics.outputs)
        outputs[0] = replace(outputs[0], sha256="0" * 64)
        packet = replace(
            self.packet,
            jobs=(replace(metrics, outputs=tuple(outputs)),),
        )

        self.assertIn("artifact.job_output_mismatch", self.issue_codes(packet))

    def test_snapshot_requires_rendered_png_sources_and_attestation(self) -> None:
        viewer, snapshot = self.packet.visual_evidence
        cases = {
            "wrong_render": (
                replace(snapshot, artifact_id=self.packet.artifacts[0].artifact_id),
                "visual.snapshot_media_invalid",
            ),
            "wrong_locator": (
                replace(snapshot, locator="build/examples/removed.png"),
                "visual.snapshot_locator_mismatch",
            ),
            "missing_sources": (
                replace(snapshot, source_artifact_ids=()),
                "visual.snapshot_sources_incomplete",
            ),
            "missing_attestation": (
                replace(snapshot, attestation_id=None),
                "visual.attestation_missing",
            ),
        }
        for label, (replacement, expected) in cases.items():
            with self.subTest(label=label):
                packet = replace(self.packet, visual_evidence=(viewer, replacement))
                self.assertIn(expected, self.issue_codes(packet))

    def test_visual_attestation_rejects_wrong_source_and_render_hashes(self) -> None:
        attestation = self.packet.inspection_attestations[0]
        for index in (0, -1):
            fingerprints = list(attestation.artifact_fingerprints)
            fingerprints[index] = replace(fingerprints[index], sha256="0" * 64)
            packet = replace(
                self.packet,
                inspection_attestations=(
                    replace(attestation, artifact_fingerprints=tuple(fingerprints)),
                ),
            )
            with self.subTest(index=index):
                self.assertIn("attestation.hash_mismatch", self.issue_codes(packet))

    def test_external_executor_id_is_preserved(self) -> None:
        metrics = replace(
            self.packet.jobs[0],
            job_id="20260723T000857-joint-coupon-release-60829aa5fa",
        )
        packet = replace(self.packet, jobs=(metrics,))

        self.assertNotIn("id.invalid", self.issue_codes(packet))


if __name__ == "__main__":
    unittest.main()
