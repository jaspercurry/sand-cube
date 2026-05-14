"""Connector and pass-through cutout helpers."""

from __future__ import annotations

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, Part


def gx16_cutout(
    *,
    hole_d: float = 16.2,
    flat_chord: float = 1.5,
    flat_radius: float = 12.5,
    depth: float = 100.0,
) -> Part:
    """GX16 circular cutout with a small anti-rotation flat."""
    with BuildPart() as cut:
        Cylinder(
            radius=hole_d / 2,
            height=depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations((flat_radius - flat_chord / 2, 0, depth / 2)):
            Box(flat_chord, hole_d * 0.8, depth, mode=Mode.SUBTRACT)
    return cut.part


def heyco_cutout(
    *,
    hole_d: float = 15.9,
    flat_chord: float = 1.4,
    depth: float = 100.0,
) -> Part:
    """Heyco SR-6P-4 strain-relief cutout."""
    with BuildPart() as cut:
        Cylinder(
            radius=hole_d / 2,
            height=depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations((hole_d / 2 - flat_chord / 2, 0, depth / 2)):
            Box(flat_chord, hole_d * 0.8, depth, mode=Mode.SUBTRACT)
    return cut.part
