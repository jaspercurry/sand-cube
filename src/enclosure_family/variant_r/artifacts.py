"""Authoritative artifact identities for the accepted Variant R evidence set."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


ArtifactKind = Literal[
    "part",
    "protected_section",
    "diagnostics",
    "provenance",
]


@dataclass(frozen=True, slots=True)
class VariantRArtifact:
    """One required output with a stable semantic identity."""

    artifact_id: str
    filename: str
    kind: ArtifactKind
    role: str


VARIANT_R_ARTIFACTS: Final = (
    VariantRArtifact(
        "bucket",
        "simple_tongue_groove_bucket.step",
        "part",
        "accepted receiving enclosure bucket",
    ),
    VariantRArtifact(
        "baffle",
        "simple_tongue_groove_baffle.step",
        "part",
        "accepted removable front baffle",
    ),
    VariantRArtifact(
        "authoritative_side_seam",
        "authoritative_side_seam_section.step",
        "protected_section",
        "reference side seam",
    ),
    VariantRArtifact(
        "authoritative_top_seam",
        "authoritative_top_seam_section.step",
        "protected_section",
        "reference top seam",
    ),
    VariantRArtifact(
        "hybrid_bottom_corner_transition",
        "hybrid_bottom_corner_transition_section.step",
        "protected_section",
        "accepted bottom-corner transition",
    ),
    VariantRArtifact(
        "hybrid_flat_bottom",
        "hybrid_flat_bottom_section.step",
        "protected_section",
        "accepted imperfect flat-bottom relationship",
    ),
    VariantRArtifact(
        "hybrid_side_seam",
        "hybrid_side_seam_section.step",
        "protected_section",
        "accepted side seam",
    ),
    VariantRArtifact(
        "hybrid_top_seam",
        "hybrid_top_seam_section.step",
        "protected_section",
        "accepted top seam",
    ),
    VariantRArtifact(
        "validation_diagnostics",
        "validation_diagnostics.json",
        "diagnostics",
        "deterministic validation and STEP round-trip evidence",
    ),
    VariantRArtifact(
        "producer_attestation",
        "variant_r_producer_attestation.json",
        "provenance",
        "complete loaded source/tool/base identity from the coordinated producer",
    ),
)

VARIANT_R_ARTIFACTS_BY_ID: Final = {
    artifact.artifact_id: artifact for artifact in VARIANT_R_ARTIFACTS
}
VARIANT_R_PART_ARTIFACTS: Final = tuple(
    artifact for artifact in VARIANT_R_ARTIFACTS if artifact.kind == "part"
)
VARIANT_R_PROTECTED_SECTION_ARTIFACTS: Final = tuple(
    artifact
    for artifact in VARIANT_R_ARTIFACTS
    if artifact.kind == "protected_section"
)
