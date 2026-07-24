"""Deterministic equivalence contract for Variant R verification adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .artifacts import VARIANT_R_PROTECTED_SECTION_ARTIFACTS


@dataclass(frozen=True, slots=True)
class VariantREquivalenceTolerances:
    """Numerical policy for detecting geometry drift, in CAD millimetres."""

    length_mm: float = 1e-6
    volume_mm3: float = 1e-5
    area_mm2: float = 1e-5
    center_of_mass_mm: float = 1e-7
    diagnostic_number: float = 1e-9


@dataclass(frozen=True, slots=True)
class VariantRVerificationContract:
    """Required evidence dimensions for every geometry-bearing checkpoint."""

    required_shape_measurements: tuple[str, ...] = (
        "validity",
        "positive solid count",
        "topology",
        "bounds",
        "volume",
        "surface area",
        "center of mass",
    )
    required_pair_measurements: tuple[str, ...] = (
        "bidirectional removed/added material",
        "bucket/baffle intersection",
        "mating gap/overlap/clearance",
        "transforms",
    )
    require_step_round_trip: bool = True
    require_normalized_diagnostics_identity: bool = True
    protected_section_ids: tuple[str, ...] = tuple(
        artifact.artifact_id
        for artifact in VARIANT_R_PROTECTED_SECTION_ARTIFACTS
    )
    tolerances: VariantREquivalenceTolerances = (
        VariantREquivalenceTolerances()
    )


VARIANT_R_VERIFICATION: Final = VariantRVerificationContract()
