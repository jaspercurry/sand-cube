"""Bracing, inserts, and reinforcement helpers."""

from __future__ import annotations

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    extrude,
    make_face,
)


def bonded_collar(
    *,
    full_h: float,
    collar_od: float = 8.0,
    insert_bore_d: float = 5.6,
    insert_bore_depth: float = 9.0,
    blind: bool = True,
) -> Part:
    """Post that joins both skins with an optional M4 heat-set insert bore."""
    post = Cylinder(
        radius=collar_od / 2,
        height=full_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = Pos(0, 0, full_h - insert_bore_depth) * Cylinder(
        radius=insert_bore_d / 2,
        height=insert_bore_depth + 0.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    result = post - bore
    if blind:
        relief = Pos(0, 0, full_h - insert_bore_depth - 0.5) * Cylinder(
            radius=insert_bore_d / 2 + 0.3,
            height=0.5,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        result -= relief
    return result


def reinforcement_ring(
    *,
    cutout_dia: float,
    ring_width: float = 10.0,
    ring_t: float = 5.0,
) -> Part:
    """Flat inner-skin ring around a driver or passive radiator cutout."""
    with BuildPart() as ring:
        with BuildSketch(Plane.XY):
            Circle(cutout_dia / 2 + ring_width)
            Circle(cutout_dia / 2, mode=Mode.SUBTRACT)
        extrude(amount=ring_t)
    return ring.part


def corner_gusset(*, leg: float = 15.0, thickness: float = 3.0) -> Part:
    """Right-triangle corner gusset."""
    with BuildPart() as gusset:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Polyline((0, 0), (leg, 0), (0, leg), (0, 0))
            make_face()
        extrude(amount=thickness)
    return gusset.part
