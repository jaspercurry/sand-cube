from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import json
import unittest

from cad_verification import (
    ActualValue,
    ArtifactObservation,
    ArtifactReference,
    ArtifactRole,
    EvidenceChannel,
    EvidenceScope,
    ResultStatus,
    SerializationError,
    Unit,
    VisualEvidenceReference,
    review_packet_from_json,
    review_packet_to_dict,
    review_packet_to_json,
    review_packet_status,
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

    def matching_observations(self) -> dict[str, ArtifactObservation]:
        return {
            artifact.path: ArtifactObservation(
                exists=True,
                sha256=artifact.sha256,
                size_bytes=artifact.size_bytes,
            )
            for artifact in self.packet.artifacts
        }

    def test_synthetic_release_packet_is_valid_and_passes(self) -> None:
        self.assertEqual(validate_review_packet(self.packet, self.contract), ())
        self.assertEqual(
            review_packet_status(self.contract, self.packet),
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

    def test_missing_result_is_rejected_and_never_passes(self) -> None:
        packet = replace(self.packet, results=self.packet.results[:-1])

        self.assertIn("result.missing", self.issue_codes(packet))
        self.assertEqual(
            review_packet_status(self.contract, packet),
            ResultStatus.FAIL,
        )

    def test_explicit_unverified_result_is_valid_but_never_passes(self) -> None:
        results = list(self.packet.results)
        results[-1] = unverified("CAD-VIS-001", "human review not yet supplied")
        packet = replace(self.packet, results=tuple(results))

        self.assertEqual(validate_review_packet(packet, self.contract), ())
        self.assertEqual(
            review_packet_status(self.contract, packet),
            ResultStatus.UNVERIFIED,
        )

    def test_programmatic_measurements_cannot_pass_from_snapshot_pixels(self) -> None:
        results = list(self.packet.results)
        results[0] = replace(
            results[0],
            evidence_channel=EvidenceChannel.SNAPSHOT,
            evidence_refs=(VisualEvidenceReference("snapshot.joint-section"),),
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

    def test_evidence_is_bound_to_exact_artifact_hash(self) -> None:
        regenerated_step = replace(
            self.packet.artifacts[0],
            sha256="a" * 64,
        )
        packet = replace(
            self.packet,
            artifacts=(regenerated_step, *self.packet.artifacts[1:]),
        )

        self.assertIn(
            "evidence.artifact_hash_mismatch",
            self.issue_codes(packet),
        )
        self.assertEqual(
            review_packet_status(self.contract, packet),
            ResultStatus.FAIL,
        )

    def test_derived_artifacts_bind_to_the_exact_step_hash(self) -> None:
        sidecar = self.packet.artifacts[1]
        stale_step_reference = replace(
            sidecar.source_artifact_refs[0],
            sha256="0" * 64,
        )
        stale_sidecar = replace(
            sidecar,
            source_artifact_refs=(stale_step_reference,),
        )
        packet = replace(
            self.packet,
            artifacts=(
                self.packet.artifacts[0],
                stale_sidecar,
                self.packet.artifacts[2],
            ),
        )

        self.assertIn(
            "evidence.artifact_hash_mismatch",
            self.issue_codes(packet),
        )

    def test_derived_artifacts_require_their_step_source(self) -> None:
        sidecar = replace(
            self.packet.artifacts[1],
            source_artifact_refs=(),
        )
        packet = replace(
            self.packet,
            artifacts=(
                self.packet.artifacts[0],
                sidecar,
                self.packet.artifacts[2],
            ),
        )

        self.assertIn("artifact.source_role_missing", self.issue_codes(packet))

    def test_artifact_role_rejects_wrong_media_type(self) -> None:
        png_step = replace(self.packet.artifacts[0], media_type="image/png")
        packet = replace(
            self.packet,
            artifacts=(png_step, *self.packet.artifacts[1:]),
        )

        self.assertIn("artifact.media_type_mismatch", self.issue_codes(packet))

    def test_visual_channels_require_their_artifact_roles(self) -> None:
        viewer, snapshot = self.packet.visual_evidence
        viewer_without_sidecar = replace(
            viewer,
            artifact_refs=tuple(
                reference
                for reference in viewer.artifact_refs
                if reference.role is not ArtifactRole.TOPOLOGY_SIDECAR
            ),
        )
        packet = replace(
            self.packet,
            visual_evidence=(viewer_without_sidecar, snapshot),
        )

        self.assertIn("visual.artifact_role_missing", self.issue_codes(packet))

    def test_release_requires_viewer_and_agent_render_channels(self) -> None:
        viewer, snapshot = self.packet.visual_evidence
        cases = {
            "viewer": replace(self.packet, visual_evidence=(snapshot,)),
            "agent_render": replace(self.packet, visual_evidence=(viewer,)),
        }
        for label, packet in cases.items():
            with self.subTest(missing=label):
                self.assertIn(
                    "profile.evidence_channel_missing",
                    self.issue_codes(packet),
                )
                self.assertEqual(
                    review_packet_status(self.contract, packet),
                    ResultStatus.FAIL,
                )

    def test_existing_hash_valid_artifacts_may_predate_review_job(self) -> None:
        old_artifacts = tuple(
            replace(
                artifact,
                created_at=self.packet.job_metrics.started_at - timedelta(days=1),
            )
            for artifact in self.packet.artifacts
        )
        packet = replace(self.packet, artifacts=old_artifacts)

        self.assertEqual(validate_review_packet(packet, self.contract), ())
        self.assertEqual(
            review_packet_status(self.contract, packet),
            ResultStatus.PASS,
        )

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
                observations = self.matching_observations()
                observations[artifact.path] = observation
                probe = FakeArtifactProbe(observations)
                self.assertIn(expected_code, self.issue_codes(self.packet, probe=probe))
                self.assertEqual(
                    review_packet_status(
                        self.contract,
                        self.packet,
                        artifact_probe=probe,
                    ),
                    ResultStatus.FAIL,
                )

    def test_matching_artifact_probe_is_accepted(self) -> None:
        probe = FakeArtifactProbe(self.matching_observations())

        self.assertEqual(
            validate_review_packet(
                self.packet,
                self.contract,
                artifact_probe=probe,
            ),
            (),
        )
        self.assertEqual(
            review_packet_status(
                self.contract,
                self.packet,
                artifact_probe=probe,
            ),
            ResultStatus.PASS,
        )

    def test_status_and_evidence_references_must_match_claims(self) -> None:
        results = list(self.packet.results)
        results[0] = replace(results[0], status=ResultStatus.FAIL)
        results[2] = replace(
            results[2],
            evidence_refs=(
                ArtifactReference(
                    "artifact.unknown",
                    ArtifactRole.STEP,
                    "0" * 64,
                ),
            ),
        )
        packet = replace(self.packet, results=tuple(results))

        codes = self.issue_codes(packet)
        self.assertIn("result.status_mismatch", codes)
        self.assertIn("evidence.artifact_unknown", codes)
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

    def test_failed_or_unclean_job_cannot_pass_release(self) -> None:
        metrics = replace(
            self.packet.job_metrics,
            exit_code=1,
            cleanup_completed=False,
            orphan_processes=3,
        )
        packet = replace(self.packet, job_metrics=metrics)

        codes = self.issue_codes(packet)
        self.assertIn("job.failed", codes)
        self.assertIn("job.cleanup_incomplete", codes)
        self.assertIn("job.orphans_present", codes)
        self.assertEqual(
            review_packet_status(self.contract, packet),
            ResultStatus.FAIL,
        )


if __name__ == "__main__":
    unittest.main()
