"""Authoritative verification vocabulary and composition policy.

This module is the single source of truth for enums, profile composition, check
costs, and evidence-channel meanings.  Other modules consume these catalogs;
they do not restate the policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class StringEnum(str, Enum):
    """A JSON-friendly enum with stable string values."""


class ResultStatus(StringEnum):
    PASS = "pass"
    FAIL = "fail"
    UNVERIFIED = "unverified"


class VerificationProfile(StringEnum):
    FAST = "fast"
    FIT = "fit"
    RELEASE = "release"


class Unit(StringEnum):
    NONE = "none"
    BOOLEAN = "boolean"
    COUNT = "count"
    MILLIMETER = "mm"
    SQUARE_MILLIMETER = "mm2"
    CUBIC_MILLIMETER = "mm3"
    DEGREE = "deg"
    RATIO = "ratio"
    PERCENT = "percent"


class ExpectationKind(StringEnum):
    EXACT = "exact"
    RANGE = "range"


class CheckKind(StringEnum):
    STRUCTURAL = "structural"
    DIMENSION = "dimension"
    FIT = "fit"
    CLEARANCE = "clearance"
    INTERFERENCE = "interference"
    WALL_THICKNESS = "wall_thickness"
    SECTION = "section"
    ROUND_TRIP = "round_trip"
    ARTIFACT_INTEGRITY = "artifact_integrity"
    VISUAL_REVIEW = "visual_review"


class EvidenceTier(StringEnum):
    NONE = "none"
    AUTHORITATIVE = "authoritative"
    HUMAN_INTERACTIVE = "human_interactive"
    AGENT_REVIEW = "agent_review"
    SCRATCH_ONLY = "scratch_only"
    EXCEPTIONAL = "exceptional"


class EvidenceChannel(StringEnum):
    NONE = "none"
    PROGRAMMATIC_GEOMETRY = "programmatic_geometry"
    VIEWER = "viewer"
    SNAPSHOT = "snapshot"
    MCP_RENDER_VIEW = "mcp_render_view"
    FOCUSED_RENDERER = "focused_renderer"
    BROWSER_AUTOMATION = "browser_automation"


class EvidenceScope(StringEnum):
    NONE = "none"
    SCRATCH = "scratch"
    EXPORTED_ARTIFACT = "exported_artifact"


class ArtifactRole(StringEnum):
    STEP = "step"
    TOPOLOGY_SIDECAR = "topology_sidecar"
    RENDER_IMAGE = "render_image"
    DIAGNOSTICS = "diagnostics"
    OTHER = "other"


@dataclass(frozen=True)
class ProfilePolicy:
    description: str
    includes: tuple[VerificationProfile, ...]
    required_check_kinds: tuple[CheckKind, ...] = ()
    required_evidence_groups: tuple[tuple[EvidenceChannel, ...], ...] = ()


@dataclass(frozen=True)
class EvidencePolicy:
    tier: EvidenceTier
    meaning: str
    allowed_scopes: tuple[EvidenceScope, ...]
    measurable_authority: bool = False
    required_artifact_roles: tuple[ArtifactRole, ...] = ()
    requires_reason: bool = False
    requires_agent_inspection: bool = False
    requires_read_only: bool = False


@dataclass(frozen=True)
class CheckPolicy:
    description: str
    minimum_profile: VerificationProfile
    allowed_channels: tuple[EvidenceChannel, ...]
    requires_artifact_reference: bool = False


@dataclass(frozen=True)
class ArtifactPolicy:
    description: str
    allowed_media_types: tuple[str, ...]
    required_source_roles: tuple[ArtifactRole, ...] = ()


PROFILE_ORDER: tuple[VerificationProfile, ...] = (
    VerificationProfile.FAST,
    VerificationProfile.FIT,
    VerificationProfile.RELEASE,
)


PROFILE_POLICIES: Mapping[VerificationProfile, ProfilePolicy] = MappingProxyType(
    {
        VerificationProfile.FAST: ProfilePolicy(
            "Cheap structural and programmatic geometry feedback.",
            (VerificationProfile.FAST,),
        ),
        VerificationProfile.FIT: ProfilePolicy(
            "Fast checks plus mating, clearance, interference, wall, and "
            "section feedback.",
            (VerificationProfile.FAST, VerificationProfile.FIT),
        ),
        VerificationProfile.RELEASE: ProfilePolicy(
            "Fit checks plus full regression, round-trip, and review evidence.",
            (
                VerificationProfile.FAST,
                VerificationProfile.FIT,
                VerificationProfile.RELEASE,
            ),
            required_check_kinds=(
                CheckKind.ROUND_TRIP,
                CheckKind.VISUAL_REVIEW,
            ),
            required_evidence_groups=(
                (EvidenceChannel.VIEWER,),
                (
                    EvidenceChannel.SNAPSHOT,
                    EvidenceChannel.FOCUSED_RENDERER,
                ),
            ),
        ),
    }
)


EVIDENCE_POLICIES: Mapping[EvidenceChannel, EvidencePolicy] = MappingProxyType(
    {
        EvidenceChannel.NONE: EvidencePolicy(
            EvidenceTier.NONE,
            "No evidence has verified the requirement.",
            (EvidenceScope.NONE,),
        ),
        EvidenceChannel.PROGRAMMATIC_GEOMETRY: EvidencePolicy(
            EvidenceTier.AUTHORITATIVE,
            "Kernel or deterministic geometry data; authoritative for "
            "measurable claims.",
            (EvidenceScope.SCRATCH, EvidenceScope.EXPORTED_ARTIFACT),
            measurable_authority=True,
        ),
        EvidenceChannel.VIEWER: EvidencePolicy(
            EvidenceTier.HUMAN_INTERACTIVE,
            "Read-only Text-to-CAD Viewer for interactive human review.",
            (EvidenceScope.EXPORTED_ARTIFACT,),
            required_artifact_roles=(
                ArtifactRole.STEP,
                ArtifactRole.TOPOLOGY_SIDECAR,
            ),
            requires_read_only=True,
        ),
        EvidenceChannel.SNAPSHOT: EvidencePolicy(
            EvidenceTier.AGENT_REVIEW,
            "Text-to-CAD Snapshot of the exact exported STEP for agent review.",
            (EvidenceScope.EXPORTED_ARTIFACT,),
            required_artifact_roles=(
                ArtifactRole.STEP,
                ArtifactRole.TOPOLOGY_SIDECAR,
                ArtifactRole.RENDER_IMAGE,
            ),
            requires_agent_inspection=True,
        ),
        EvidenceChannel.MCP_RENDER_VIEW: EvidencePolicy(
            EvidenceTier.SCRATCH_ONLY,
            "Build123d-MCP render_view of disposable in-memory scratch geometry only.",
            (EvidenceScope.SCRATCH,),
            requires_agent_inspection=True,
        ),
        EvidenceChannel.FOCUSED_RENDERER: EvidencePolicy(
            EvidenceTier.AGENT_REVIEW,
            "Coordinated production fallback when Snapshot cannot answer the "
            "visual question.",
            (EvidenceScope.EXPORTED_ARTIFACT,),
            required_artifact_roles=(
                ArtifactRole.STEP,
                ArtifactRole.RENDER_IMAGE,
            ),
            requires_reason=True,
            requires_agent_inspection=True,
        ),
        EvidenceChannel.BROWSER_AUTOMATION: EvidencePolicy(
            EvidenceTier.EXCEPTIONAL,
            "Exceptional Viewer-behavior test when artifact-native channels "
            "are insufficient.",
            (EvidenceScope.EXPORTED_ARTIFACT,),
            required_artifact_roles=(
                ArtifactRole.STEP,
                ArtifactRole.TOPOLOGY_SIDECAR,
                ArtifactRole.RENDER_IMAGE,
            ),
            requires_reason=True,
            requires_agent_inspection=True,
        ),
    }
)


ARTIFACT_POLICIES: Mapping[ArtifactRole, ArtifactPolicy] = MappingProxyType(
    {
        ArtifactRole.STEP: ArtifactPolicy(
            "Exported STEP/STP geometry.",
            ("model/step", "application/step", "model/vnd.step"),
        ),
        ArtifactRole.TOPOLOGY_SIDECAR: ArtifactPolicy(
            "Topology sidecar for the exact exported STEP.",
            ("application/json",),
            required_source_roles=(ArtifactRole.STEP,),
        ),
        ArtifactRole.RENDER_IMAGE: ArtifactPolicy(
            "Snapshot, focused render, or exceptional browser image.",
            ("image/png", "image/jpeg"),
            required_source_roles=(ArtifactRole.STEP,),
        ),
        ArtifactRole.DIAGNOSTICS: ArtifactPolicy(
            "Machine-readable diagnostic output.",
            ("application/json",),
        ),
        ArtifactRole.OTHER: ArtifactPolicy(
            "Explicitly classified artifact without a constrained media type.",
            (),
        ),
    }
)


_MEASURABLE_CHANNELS = (EvidenceChannel.PROGRAMMATIC_GEOMETRY,)
_VISUAL_CHANNELS = (
    EvidenceChannel.VIEWER,
    EvidenceChannel.SNAPSHOT,
    EvidenceChannel.MCP_RENDER_VIEW,
    EvidenceChannel.FOCUSED_RENDERER,
    EvidenceChannel.BROWSER_AUTOMATION,
)


CHECK_POLICIES: Mapping[CheckKind, CheckPolicy] = MappingProxyType(
    {
        CheckKind.STRUCTURAL: CheckPolicy(
            "Validity, topology, or other cheap structural invariant.",
            VerificationProfile.FAST,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.DIMENSION: CheckPolicy(
            "Deterministic dimension or extent measurement.",
            VerificationProfile.FAST,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.FIT: CheckPolicy(
            "Mating or assembly-fit measurement.",
            VerificationProfile.FIT,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.CLEARANCE: CheckPolicy(
            "Minimum or nominal clearance measurement.",
            VerificationProfile.FIT,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.INTERFERENCE: CheckPolicy(
            "Positive-volume or contact interference measurement.",
            VerificationProfile.FIT,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.WALL_THICKNESS: CheckPolicy(
            "Wall-thickness measurement at contract-relevant locations.",
            VerificationProfile.FIT,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.SECTION: CheckPolicy(
            "Programmatic section measurement or section-presence check.",
            VerificationProfile.FIT,
            _MEASURABLE_CHANNELS,
        ),
        CheckKind.ROUND_TRIP: CheckPolicy(
            "Export/import regression bound to a generated artifact.",
            VerificationProfile.RELEASE,
            _MEASURABLE_CHANNELS,
            requires_artifact_reference=True,
        ),
        CheckKind.ARTIFACT_INTEGRITY: CheckPolicy(
            "Hash, topology-sidecar, or artifact-integrity regression.",
            VerificationProfile.RELEASE,
            _MEASURABLE_CHANNELS,
            requires_artifact_reference=True,
        ),
        CheckKind.VISUAL_REVIEW: CheckPolicy(
            "Explicit human or agent visual question.",
            VerificationProfile.RELEASE,
            _VISUAL_CHANNELS,
            requires_artifact_reference=True,
        ),
    }
)


def profile_rank(profile: VerificationProfile) -> int:
    return PROFILE_ORDER.index(profile)


def included_costs(
    profile: VerificationProfile,
) -> tuple[VerificationProfile, ...]:
    return PROFILE_POLICIES[profile].includes


def evidence_tier(channel: EvidenceChannel) -> EvidenceTier:
    return EVIDENCE_POLICIES[channel].tier


def _assert_catalogs_complete() -> None:
    if set(PROFILE_POLICIES) != set(VerificationProfile):
        raise RuntimeError("PROFILE_POLICIES must cover every profile")
    if set(EVIDENCE_POLICIES) != set(EvidenceChannel):
        raise RuntimeError("EVIDENCE_POLICIES must cover every evidence channel")
    if set(CHECK_POLICIES) != set(CheckKind):
        raise RuntimeError("CHECK_POLICIES must cover every check kind")
    if set(ARTIFACT_POLICIES) != set(ArtifactRole):
        raise RuntimeError("ARTIFACT_POLICIES must cover every artifact role")


_assert_catalogs_complete()
