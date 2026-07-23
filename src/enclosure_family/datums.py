"""Exact design-coordinate contract for the 190 x 210 enclosure family.

This module is intentionally native-CAD-free.  It owns only units, envelope
dimensions, axis polarity, and derived named planes; geometry builders consume
the contract without importing Build123d or OCP here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


Direction = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class CoordinateContract:
    """Immutable envelope and datum owner in design coordinates."""

    units: Literal["mm"]
    width_mm: float
    depth_mm: float
    height_mm: float
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    center_z_mm: float = 0.0

    def __post_init__(self) -> None:
        if self.units != "mm":
            raise ValueError("enclosure coordinates must use millimetres")
        if min(self.width_mm, self.depth_mm, self.height_mm) <= 0.0:
            raise ValueError("enclosure envelope dimensions must be positive")

    @property
    def width_axis(self) -> Literal["X"]:
        return "X"

    @property
    def depth_axis(self) -> Literal["Y"]:
        return "Y"

    @property
    def height_axis(self) -> Literal["Z"]:
        return "Z"

    @property
    def left_direction(self) -> Direction:
        return (-1, 0, 0)

    @property
    def right_direction(self) -> Direction:
        return (1, 0, 0)

    @property
    def front_direction(self) -> Direction:
        return (0, -1, 0)

    @property
    def rear_direction(self) -> Direction:
        return (0, 1, 0)

    @property
    def bottom_direction(self) -> Direction:
        return (0, 0, -1)

    @property
    def top_direction(self) -> Direction:
        return (0, 0, 1)

    @property
    def left_x_mm(self) -> float:
        return self.center_x_mm - self.width_mm / 2.0

    @property
    def right_x_mm(self) -> float:
        return self.center_x_mm + self.width_mm / 2.0

    @property
    def front_y_mm(self) -> float:
        return self.center_y_mm - self.depth_mm / 2.0

    @property
    def rear_y_mm(self) -> float:
        return self.center_y_mm + self.depth_mm / 2.0

    @property
    def bottom_z_mm(self) -> float:
        return self.center_z_mm - self.height_mm / 2.0

    @property
    def top_z_mm(self) -> float:
        return self.center_z_mm + self.height_mm / 2.0


ENCLOSURE_190X210_COORDINATES: Final = CoordinateContract(
    units="mm",
    width_mm=190.0,
    depth_mm=210.0,
    height_mm=190.0,
    center_y_mm=10.0,
)
