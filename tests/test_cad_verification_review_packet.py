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
            "job_metrics",
            "visual_evidence",
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
            "snapshot_inspection": (
                replace(snapshot, inspected_by_agent=False),
                "visual.not_inspected",
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
        artifact = self.packet.artifacts[0]
        probe = FakeArtifactProbe(
            {
                artifact.path: ArtifactObservation(
                    exists=True,
                    sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes,
                )
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
            self.packet.job_metrics,
            elapsed_seconds=-1.0,
            orphan_processes=-1,
        )
        packet = replace(self.packet, job_metrics=metrics)

        codes = self.issue_codes(packet)
        self.assertIn("job.elapsed_invalid", codes)
        self.assertIn("job.orphans_invalid", codes)


if __name__ == "__main__":
    unittest.main()
