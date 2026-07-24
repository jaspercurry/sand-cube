"""Accepted design-coordinate print policies for Variant R parts."""

from __future__ import annotations

from typing import Final

from ..print_contracts import PrintContract
from .parameters import VARIANT_R_PARAMETERS


VARIANT_R_BUCKET_PRINT_CONTRACT: Final = PrintContract(
    owner_id="variant_r",
    part_id="bucket",
    status="accepted",
    bed_contact="rear exterior face; design-coordinate Y maximum",
    build_direction=(0, -1, 0),
    brim_assumed=False,
)

VARIANT_R_BAFFLE_PRINT_CONTRACT: Final = PrintContract(
    owner_id="variant_r",
    part_id="baffle",
    status="accepted",
    bed_contact=(
        "flat lower edge at design-coordinate "
        f"Z={VARIANT_R_PARAMETERS.baffle_print_bed_z_mm:g} mm"
    ),
    build_direction=(0, 0, 1),
    brim_assumed=True,
)

VARIANT_R_PRINT_CONTRACTS: Final = (
    VARIANT_R_BUCKET_PRINT_CONTRACT,
    VARIANT_R_BAFFLE_PRINT_CONTRACT,
)
