"""Small gasketed tongue-and-groove coupon for design-loop experiments."""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Box, Compound, Cylinder, Location, Shape

from workbench.designs.joint_coupon.parameters import (
    CouponParameters,
    expected_volumes,
)


@dataclass(frozen=True)
class CouponModel:
    lower: Shape
    upper: Shape
    gasket_left: Shape
    gasket_right: Shape
    assembly: Compound
    tongue: Shape
    groove: Shape


def _box(
    length: float,
    width: float,
    height: float,
    z: float = 0.0,
    y: float = 0.0,
) -> Shape:
    return Box(
        length,
        width,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).located(Location((0.0, y, z)))


def _fastener_cutters(params: CouponParameters) -> list[Shape]:
    cutters: list[Shape] = []
    height = params.lower_thickness + params.closed_gap + params.upper_thickness + 2.0
    for x in (-params.fastener_x, params.fastener_x):
        for y in (-params.fastener_y, params.fastener_y):
            cutters.append(
                Cylinder(
                    params.fastener_diameter / 2.0,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                ).located(Location((x, y, -1.0)))
            )
    return cutters


def build_coupon(params: CouponParameters) -> CouponModel:
    lower_plate = _box(params.length, params.depth, params.lower_thickness)
    tongue = _box(
        params.tongue_length,
        params.tongue_width,
        params.tongue_height,
        params.lower_thickness,
    )
    lower = lower_plate.fuse(tongue)

    upper = _box(
        params.length,
        params.depth,
        params.upper_thickness,
        params.upper_underside_z,
    )
    groove = _box(
        params.groove_length,
        params.groove_width,
        params.groove_depth,
        params.upper_underside_z,
    )
    upper = upper.cut(groove)

    for cutter in _fastener_cutters(params):
        lower = lower.cut(cutter)
        upper = upper.cut(cutter)

    gasket_left = _box(
        params.gasket_length,
        params.gasket_width,
        params.gasket_closed_thickness,
        params.lower_thickness,
        params.gasket_center_y,
    )
    gasket_right = _box(
        params.gasket_length,
        params.gasket_width,
        params.gasket_closed_thickness,
        params.lower_thickness,
        -params.gasket_center_y,
    )

    assembly = Compound(children=[lower, upper, gasket_left, gasket_right])
    return CouponModel(
        lower,
        upper,
        gasket_left,
        gasket_right,
        assembly,
        tongue,
        groove,
    )
