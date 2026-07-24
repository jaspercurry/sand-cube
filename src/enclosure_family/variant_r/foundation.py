"""Explicit dependency boundary between Variant R and legacy foundation CAD."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol


PerimeterWireBuilder = Callable[..., Any]


class VariantRFoundation(Protocol):
    """Minimum foundation behavior required by the Variant R composer."""

    def authoritative_perimeter_wire(
        self,
        *,
        offset_mm: float,
        y_mm: float,
    ) -> Any:
        """Return the accepted pre-flat-bottom perimeter wire."""

    def build_authoritative_joint(self, full_base: Any) -> Mapping[str, Any]:
        """Build the accepted sculpted joint before lower-band replacement."""

    def build_flat_bottom_donor(
        self,
        full_base: Any,
        *,
        perimeter_wire: PerimeterWireBuilder,
    ) -> Mapping[str, Any]:
        """Build the donor joint using the supplied Variant R perimeter."""
