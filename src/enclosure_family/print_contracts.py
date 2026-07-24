"""Geometry-neutral print orientation and bed-contact contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Direction = tuple[int, int, int]
PrintContractStatus = Literal["accepted", "future"]


@dataclass(frozen=True, slots=True)
class PrintContract:
    """One part's design-coordinate printing policy.

    The contract is metadata only.  It does not rotate geometry, create
    supports, or claim that an unprinted part has passed a physical print.
    """

    owner_id: str
    part_id: str
    status: PrintContractStatus
    bed_contact: str
    build_direction: Direction
    brim_assumed: bool
    physical_print_verified: bool = False

    def __post_init__(self) -> None:
        if not self.owner_id or not self.part_id:
            raise ValueError("print-contract owner and part IDs must be non-empty")
        if sum(abs(component) for component in self.build_direction) != 1:
            raise ValueError("build direction must be one signed cardinal axis")
