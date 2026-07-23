"""Native-free parameter model and analytic expectations for the joint coupon."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import pi
from pathlib import Path
from typing import Any, Mapping


PARAMETERS_PATH = Path(__file__).with_name("params.json")


@dataclass(frozen=True)
class CouponParameters:
    length: float
    depth: float
    lower_thickness: float
    upper_thickness: float
    closed_gap: float
    tongue_length: float
    tongue_width: float
    tongue_height: float
    groove_end_clearance: float
    groove_side_clearance: float
    groove_depth: float
    gasket_length: float
    gasket_width: float
    gasket_land_gap: float
    gasket_free_thickness: float
    fastener_diameter: float
    fastener_x: float
    fastener_y: float

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "CouponParameters":
        return cls(**{name: float(values[name]) for name in cls.__annotations__})

    @property
    def upper_underside_z(self) -> float:
        return self.lower_thickness + self.closed_gap

    @property
    def groove_width(self) -> float:
        return self.tongue_width + 2.0 * self.groove_side_clearance

    @property
    def groove_length(self) -> float:
        return self.tongue_length + 2.0 * self.groove_end_clearance

    @property
    def gasket_closed_thickness(self) -> float:
        return self.closed_gap

    @property
    def gasket_compression(self) -> float:
        return self.gasket_free_thickness - self.gasket_closed_thickness

    @property
    def gasket_center_y(self) -> float:
        return self.groove_width / 2.0 + self.gasket_land_gap + self.gasket_width / 2.0


def load_parameters(
    path: Path = PARAMETERS_PATH,
) -> tuple[dict[str, Any], CouponParameters]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw, CouponParameters.from_mapping(raw)


def expected_volumes(params: CouponParameters) -> dict[str, float]:
    lower_hole_volume = (
        4.0 * pi * (params.fastener_diameter / 2.0) ** 2 * params.lower_thickness
    )
    upper_hole_volume = (
        4.0 * pi * (params.fastener_diameter / 2.0) ** 2 * params.upper_thickness
    )
    lower = (
        params.length * params.depth * params.lower_thickness
        + params.tongue_length * params.tongue_width * params.tongue_height
        - lower_hole_volume
    )
    upper = (
        params.length * params.depth * params.upper_thickness
        - params.groove_length * params.groove_width * params.groove_depth
        - upper_hole_volume
    )
    gasket = params.gasket_length * params.gasket_width * params.gasket_closed_thickness
    return {"lower": lower, "upper": upper, "gasket_each": gasket}
