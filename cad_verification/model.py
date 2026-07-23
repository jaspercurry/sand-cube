"""Dependency-free contract, result, and review-packet models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias

from .policy import (
    CheckKind,
    EvidenceChannel,
    EvidenceScope,
    EvidenceTier,
    ExpectationKind,
    ResultStatus,
    Unit,
    VerificationProfile,
    evidence_tier,
)


SCHEMA_VERSION = 2
Scalar: TypeAlias = bool | int | float | str


@dataclass(frozen=True)
class ModelIdentity:
    model_id: str
    name: str
    variant: str
    source: str
    entrypoint: str


@dataclass(frozen=True)
class Expectation:
    kind: ExpectationKind
    exact: Scalar | None = None
    minimum: float | None = None
    maximum: float | None = None

    @classmethod
    def exactly(cls, value: Scalar) -> "Expectation":
        return cls(kind=ExpectationKind.EXACT, exact=value)

    @classmethod
    def between(cls, minimum: float, maximum: float) -> "Expectation":
        return cls(
            kind=ExpectationKind.RANGE,
            minimum=minimum,
            maximum=maximum,
        )


@dataclass(frozen=True)
class Tolerance:
    absolute: float = 0.0


@dataclass(frozen=True)
class CheckSpec:
    kind: CheckKind
    adapter: str
    parameters: tuple[tuple[str, Scalar], ...] = ()


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    description: str
    check: CheckSpec
    expectation: Expectation
    unit: Unit
    tolerance: Tolerance
    cost_profile: VerificationProfile


@dataclass(frozen=True)
class DesignContract:
    contract_id: str
    title: str
    model: ModelIdentity
    requirements: tuple[Requirement, ...]
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class ActualValue:
    value: Scalar
    unit: Unit


@dataclass(frozen=True)
class RequirementResult:
    requirement_id: str
    status: ResultStatus
    actual: ActualValue | None
    evidence_channel: EvidenceChannel
    diagnostic: str
    evidence_refs: tuple[str, ...] = ()

    @property
    def evidence_tier(self) -> EvidenceTier:
        return evidence_tier(self.evidence_channel)


@dataclass(frozen=True)
class Fingerprint:
    subject: str
    sha256: str


@dataclass(frozen=True)
class ToolIdentity:
    name: str
    version: str
    identity: str


@dataclass(frozen=True)
class ToolchainIdentity:
    tools: tuple[ToolIdentity, ...]


@dataclass(frozen=True)
class ArtifactEvidence:
    artifact_id: str
    path: str
    media_type: str
    sha256: str
    size_bytes: int
    created_at: datetime
    contract_fingerprint: str
    source_fingerprint: str
    input_fingerprint: str


@dataclass(frozen=True)
class ArtifactObservation:
    exists: bool
    sha256: str | None = None
    size_bytes: int | None = None
    modified_at: datetime | None = None


@dataclass(frozen=True)
class VisualEvidence:
    evidence_id: str
    channel: EvidenceChannel
    scope: EvidenceScope
    locator: str
    purpose: str
    created_at: datetime
    renderer: str
    artifact_id: str | None = None
    source_artifact_ids: tuple[str, ...] = ()
    attestation_id: str | None = None
    viewer_record_id: str | None = None
    read_only: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class InspectionAttestation:
    attestation_id: str
    inspector: str
    inspected_at: datetime
    statement: str
    artifact_fingerprints: tuple[Fingerprint, ...]


@dataclass(frozen=True)
class ViewerSessionRecord:
    record_id: str
    url: str
    recorded_at: datetime
    server_app: str
    backend: str
    dynamic_root: bool
    generation_available: bool
    viewer_version: str
    artifact_fingerprints: tuple[Fingerprint, ...]


@dataclass(frozen=True)
class JobOutput:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class JobMetrics:
    role: str
    job_id: str
    name: str
    state: str
    target: str
    profile: VerificationProfile
    command: tuple[str, ...]
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    exit_code: int
    worker_pid: int | None
    peak_rss_bytes: int | None
    cleanup_completed: bool
    orphan_processes: int
    outputs: tuple[JobOutput, ...] = ()


@dataclass(frozen=True)
class ReviewPacket:
    packet_id: str
    contract_id: str
    contract_fingerprint: str
    profile: VerificationProfile
    model: ModelIdentity
    source_fingerprints: tuple[Fingerprint, ...]
    input_fingerprints: tuple[Fingerprint, ...]
    toolchain: ToolchainIdentity
    artifacts: tuple[ArtifactEvidence, ...]
    results: tuple[RequirementResult, ...]
    jobs: tuple[JobMetrics, ...]
    visual_evidence: tuple[VisualEvidence, ...]
    inspection_attestations: tuple[InspectionAttestation, ...]
    viewer_records: tuple[ViewerSessionRecord, ...]
    confirmed_facts: tuple[str, ...]
    remaining_uncertainty: tuple[str, ...]
    created_at: datetime
    schema_version: int = field(default=SCHEMA_VERSION)
