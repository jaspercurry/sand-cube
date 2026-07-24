"""Native-CAD-free identity and ownership map for the accepted Variant R."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


@dataclass(frozen=True, slots=True)
class VariantRModel:
    """Stable model identity without importing geometry or experiment code."""

    model_id: Literal["development-190x210-tongue-groove"] = (
        "development-190x210-tongue-groove"
    )
    variant_id: Literal["variant_r"] = "variant_r"
    status: Literal["accepted_no_splice_production"] = (
        "accepted_no_splice_production"
    )
    assembly_owner: str = "src.enclosure_family.variant_r.assembly"
    seam_owner: str = "src.enclosure_family.variant_r.seam"
    bottom_material_owner: str = (
        "src.enclosure_family.variant_r.bottom_ownership"
    )
    parameter_owner: str = "src.enclosure_family.variant_r.parameters"
    artifact_owner: str = "src.enclosure_family.variant_r.artifacts"
    input_owner: str = "src.enclosure_family.variant_r.inputs"
    provenance_owner: str = "src.enclosure_family.variant_r.provenance"
    measurement_owner: str = "src.enclosure_family.variant_r.measurements"
    verification_owner: str = "src.enclosure_family.variant_r.verification"
    export_owner: str = "src.enclosure_family.variant_r.export"
    retention_geometry: Literal["absent"] = "absent"
    known_geometry_boundary: str = (
        "continuous exact-edge donor owns the bucket, gasket and visible "
        "baffle apron; only the baffle sub-sole band is discarded at the "
        "parameter-owned planar sole"
    )
    generated_input_policy: str = (
        "the cataloged producer must emit the base STEP and a matching complete "
        "loaded-source attestation before validation"
    )


VARIANT_R_MODEL: Final = VariantRModel()
