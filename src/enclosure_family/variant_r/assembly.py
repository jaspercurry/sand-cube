"""Independent Variant R seam and lower-material composition owner."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .bottom_ownership import (
    SingleSolid,
    trim_baffle_to_planar_sole,
)
from .foundation import VariantRFoundation
from .parameters import VARIANT_R_PARAMETERS, VariantRParameters
from .seam import build_hybrid_perimeter_wire


def build_variant_r_joint(
    full_base: Any,
    *,
    foundation: VariantRFoundation,
    single_solid: SingleSolid,
    reference_joint: Mapping[str, Any] | None = None,
    parameters: VariantRParameters = VARIANT_R_PARAMETERS,
) -> dict[str, Any]:
    """Compose the no-splice Variant R joint from explicit dependencies."""

    def perimeter_wire(*, offset_mm: float, y_mm: float) -> Any:
        return build_hybrid_perimeter_wire(
            foundation.authoritative_perimeter_wire,
            offset_mm=offset_mm,
            y_mm=y_mm,
            parameters=parameters,
        )

    donor = dict(
        foundation.build_flat_bottom_donor(
            full_base,
            perimeter_wire=perimeter_wire,
        )
    )
    common = dict(donor)
    common["baffle"], sole_trim_audit = trim_baffle_to_planar_sole(
        donor["baffle"],
        single_solid=single_solid,
        parameters=parameters,
    )
    common["bottom_synthesis"] = {
        "construction": (
            "continuous exact-edge flat-bottom donor with baffle-only planar "
            "sole trim"
        ),
        "foundation_output_used_directly": {
            "bucket": True,
            "baffle_above_sole": True,
            "gasket": True,
        },
        "reference_joint_used_in_active_composition": False,
        "reference_joint_supplied_for_validation": reference_joint is not None,
        "whole_part_z_splice_applied": False,
        "lower_material_transfer_to_bucket_applied": False,
        "sub_sole_material_disposition": "discarded",
        "sole_trim": sole_trim_audit,
    }
    return common
