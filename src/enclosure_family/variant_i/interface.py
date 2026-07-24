"""Explicit future Variant I boundary; no Variant I geometry exists yet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from ..print_contracts import PrintContract


@dataclass(frozen=True, slots=True)
class FutureVariantIInterface:
    """Ownership declaration that prevents accidental Variant R composition."""

    owner_id: Literal["variant_i"] = "variant_i"
    implementation_status: Literal["future_geometry_absent"] = (
        "future_geometry_absent"
    )
    composition_boundary: str = (
        "branch from a neutral enclosure body before any removable-front split"
    )
    required_owned_features: tuple[str, ...] = (
        "monolithic front",
        "open bottom",
        "future bottom hatch interface",
    )
    forbidden_variant_r_features: tuple[str, ...] = (
        "service opening",
        "removable baffle",
        "gasket gap",
        "removable seam",
        "hinge",
        "front fasteners",
    )
    print_contract: PrintContract = PrintContract(
        owner_id="variant_i",
        part_id="integral_enclosure",
        status="future",
        bed_contact="future open-bottom perimeter; no geometry fabricated",
        build_direction=(0, 0, 1),
        brim_assumed=False,
    )

    def require_geometry_owner(self) -> None:
        """Fail explicitly until a separately authorized owner is implemented."""

        raise NotImplementedError(
            "Variant I geometry is intentionally absent; implement an "
            "independent assembly owner before requesting geometry"
        )


VARIANT_I_BOUNDARY: Final = FutureVariantIInterface()
