"""Independent Variant R seam and lower-material composition owner."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .bottom_ownership import (
    SingleSolid,
    splice_flat_bottom_band,
    transfer_baffle_below_print_plane,
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
    """Compose the accepted Variant R joint from explicit dependencies."""

    reference = dict(
        reference_joint
        if reference_joint is not None
        else foundation.build_authoritative_joint(full_base)
    )

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
    for part_name in ("bucket", "baffle", "gasket"):
        common[part_name] = splice_flat_bottom_band(
            reference[part_name],
            donor[part_name],
            feature=f"{part_name} with synthesized flat-bottom ownership",
            single_solid=single_solid,
            parameters=parameters,
        )
    common["bucket"], common["baffle"], print_edge_audit = (
        transfer_baffle_below_print_plane(
            common["bucket"],
            common["baffle"],
            single_solid=single_solid,
            parameters=parameters,
        )
    )
    common["bottom_synthesis"] = {
        "authoritative_joint_reused_above_z_mm": (
            parameters.bottom_synthesis_max_z_mm
        ),
        "flat_bottom_donor_reused_below_z_mm": (
            parameters.bottom_synthesis_max_z_mm
        ),
        "splice_overlap_mm": parameters.bottom_synthesis_overlap_mm,
        "parts": ["bucket", "baffle", "gasket"],
        "print_edge": print_edge_audit,
    }
    return common
