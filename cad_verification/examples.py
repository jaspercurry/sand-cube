"""Small synthetic examples with no CAD imports or model coupling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256

from .evaluation import assess
from .model import (
    ActualValue,
    ArtifactEvidence,
    CheckSpec,
    DesignContract,
    Expectation,
    Fingerprint,
    JobMetrics,
    ModelIdentity,
    Requirement,
    ReviewPacket,
    Tolerance,
    ToolIdentity,
    ToolchainIdentity,
    VisualEvidence,
)
from .policy import (
    CheckKind,
    EvidenceChannel,
    EvidenceScope,
    Unit,
    VerificationProfile,
)
from .serialization import contract_fingerprint, fingerprint_collection


_STARTED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
_FINISHED = _STARTED + timedelta(seconds=1.25)


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def minimal_contract() -> DesignContract:
    """Return a valid contract spanning every compositional cost layer."""

    model = ModelIdentity(
        model_id="synthetic-joint-coupon",
        name="Synthetic joint coupon",
        variant="framework-example",
        source="examples/synthetic_joint.py",
        entrypoint="examples/build_synthetic_joint.py",
    )
    return DesignContract(
        contract_id="contract.synthetic-joint",
        title="Synthetic joint acceptance",
        model=model,
        requirements=(
            Requirement(
                requirement_id="CAD-DIM-001",
                description="Coupon length is nominal.",
                check=CheckSpec(CheckKind.DIMENSION, "kernel.bounding_box_x"),
                expectation=Expectation.exactly(80.0),
                unit=Unit.MILLIMETER,
                tolerance=Tolerance(0.01),
                cost_profile=VerificationProfile.FAST,
            ),
            Requirement(
                requirement_id="CAD-FIT-001",
                description="Mating clearance remains printable.",
                check=CheckSpec(
                    CheckKind.CLEARANCE,
                    "kernel.minimum_clearance",
                    (("pair", "tongue_to_groove"),),
                ),
                expectation=Expectation.between(0.2, 0.3),
                unit=Unit.MILLIMETER,
                tolerance=Tolerance(0.01),
                cost_profile=VerificationProfile.FIT,
            ),
            Requirement(
                requirement_id="CAD-REL-001",
                description="The exported STEP round-trips as valid geometry.",
                check=CheckSpec(CheckKind.ROUND_TRIP, "artifact.step_round_trip"),
                expectation=Expectation.exactly(True),
                unit=Unit.BOOLEAN,
                tolerance=Tolerance(),
                cost_profile=VerificationProfile.RELEASE,
            ),
            Requirement(
                requirement_id="CAD-VIS-001",
                description="The joint section visibly answers the fit question.",
                check=CheckSpec(CheckKind.VISUAL_REVIEW, "review.joint_section"),
                expectation=Expectation.exactly(True),
                unit=Unit.BOOLEAN,
                tolerance=Tolerance(),
                cost_profile=VerificationProfile.RELEASE,
            ),
        ),
    )


def minimal_review_packet(
    contract: DesignContract | None = None,
) -> ReviewPacket:
    """Return a complete release packet for :func:`minimal_contract`."""

    contract = contract or minimal_contract()
    requirements = {
        requirement.requirement_id: requirement
        for requirement in contract.requirements
    }
    source_fingerprints = (
        Fingerprint("examples/synthetic_joint.py", _digest(b"synthetic source")),
    )
    input_fingerprints = (
        Fingerprint("examples/parameters.json", _digest(b'{"length":80}')),
    )
    step_bytes = b"synthetic STEP evidence"
    artifact = ArtifactEvidence(
        artifact_id="artifact.synthetic-step",
        path="build/examples/synthetic_joint.step",
        media_type="model/step",
        sha256=_digest(step_bytes),
        size_bytes=len(step_bytes),
        created_at=_FINISHED,
        contract_fingerprint=contract_fingerprint(contract),
        source_fingerprint=fingerprint_collection(source_fingerprints),
        input_fingerprint=fingerprint_collection(input_fingerprints),
    )
    viewer = VisualEvidence(
        evidence_id="viewer.synthetic-step",
        channel=EvidenceChannel.VIEWER,
        scope=EvidenceScope.EXPORTED_ARTIFACT,
        locator="http://127.0.0.1:4178/?file=synthetic_joint.step",
        purpose="Interactive inspection of the exact exported STEP.",
        created_at=_FINISHED,
        artifact_id=artifact.artifact_id,
        renderer="Text-to-CAD Viewer",
        read_only=True,
    )
    snapshot = VisualEvidence(
        evidence_id="snapshot.joint-section",
        channel=EvidenceChannel.SNAPSHOT,
        scope=EvidenceScope.EXPORTED_ARTIFACT,
        locator="build/examples/synthetic_joint_section.png",
        purpose="Confirm the joint section answers the visual fit question.",
        created_at=_FINISHED,
        artifact_id=artifact.artifact_id,
        renderer="Text-to-CAD Snapshot",
        inspected_by_agent=True,
    )
    results = (
        assess(
            requirements["CAD-DIM-001"],
            ActualValue(80.0, Unit.MILLIMETER),
            evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            diagnostic="Bounding-box X extent is 80.0 mm.",
        ),
        assess(
            requirements["CAD-FIT-001"],
            ActualValue(0.22, Unit.MILLIMETER),
            evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            diagnostic="Minimum tongue-to-groove clearance is 0.22 mm.",
        ),
        assess(
            requirements["CAD-REL-001"],
            ActualValue(True, Unit.BOOLEAN),
            evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            diagnostic="STEP import preserved valid geometry.",
            evidence_refs=(artifact.artifact_id,),
        ),
        assess(
            requirements["CAD-VIS-001"],
            ActualValue(True, Unit.BOOLEAN),
            evidence_channel=EvidenceChannel.SNAPSHOT,
            diagnostic="Agent inspected the exported-STEP section view.",
            evidence_refs=(snapshot.evidence_id,),
        ),
    )
    return ReviewPacket(
        packet_id="review.synthetic-001",
        contract_id=contract.contract_id,
        contract_fingerprint=contract_fingerprint(contract),
        profile=VerificationProfile.RELEASE,
        model=contract.model,
        source_fingerprints=source_fingerprints,
        input_fingerprints=input_fingerprints,
        toolchain=ToolchainIdentity(
            (
                ToolIdentity("python", "3.12", "cpython-3.12"),
                ToolIdentity("synthetic-kernel", "1", "test-double"),
            )
        ),
        artifacts=(artifact,),
        results=results,
        job_metrics=JobMetrics(
            job_id="job.synthetic-001",
            started_at=_STARTED,
            finished_at=_FINISHED,
            elapsed_seconds=1.25,
            exit_code=0,
            worker_pid=1234,
            peak_rss_bytes=12_345_678,
            cleanup_completed=True,
            orphan_processes=0,
            outputs=(artifact.path,),
        ),
        visual_evidence=(viewer, snapshot),
        confirmed_facts=(
            "Synthetic dimensions, fit, round-trip, and visual checks passed.",
        ),
        remaining_uncertainty=(
            "Synthetic evidence does not establish behavior of a real CAD model.",
        ),
        created_at=_FINISHED,
    )
