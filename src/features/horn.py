"""JMLC-inspired horn geometry for the B&C DE250."""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    Location,
    Mode,
    Part,
    Plane,
    Polyline,
    Spline,
    Torus,
    add,
    make_face,
    revolve,
)


def _cylinder_z(
    *,
    diameter: float,
    depth: float,
    center: tuple[float, float, float],
) -> Part:
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    return Location(center) * cyl


def _jmlc_inspired_radius(
    *,
    throat_r: float,
    mouth_inner_r: float,
    length: float,
    z: float,
    profile_power: float,
) -> float:
    """Smooth spherical-horn-inspired flare with slow throat growth."""
    t = max(0.0, min(1.0, z / length))
    eased = (1 - math.cos(math.pi * t)) / 2
    shaped = eased**profile_power
    return throat_r + (mouth_inner_r - throat_r) * shaped


def build_jmlc_horn(
    *,
    throat_d: float,
    mouth_outer_d: float,
    length: float,
    wall_t: float,
    profile_power: float,
    lip_r: float,
    flange_d: float,
    flange_t: float,
    bolt_clearance_d: float,
    bolt_3_bcd: float,
    bolt_2_bcd: float,
) -> Part:
    """Build a printable JMLC-inspired 1 in horn with DE250 bolt patterns.

    The acoustic profile is intentionally parameterized as a smooth JMLC-like
    flare rather than a closed-form Le Cleac'h calculator. It gives us a
    practical first printable horn that can later be swapped for sampled JMLC
    coordinates from Hornresp/AxialHorn without changing the mounting stack.
    """
    throat_r = throat_d / 2
    mouth_outer_r = mouth_outer_d / 2
    mouth_inner_r = mouth_outer_r - wall_t
    n = 72
    inner = [
        (
            _jmlc_inspired_radius(
                throat_r=throat_r,
                mouth_inner_r=mouth_inner_r,
                length=length,
                z=length * i / n,
                profile_power=profile_power,
            ),
            length * i / n,
        )
        for i in range(n + 1)
    ]
    outer = [(r + wall_t, z) for r, z in inner]

    with BuildPart() as horn_body:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Spline(*inner)
                Polyline(inner[-1], outer[-1])
                Spline(*reversed(outer))
                Polyline(outer[0], inner[0])
            make_face()
        revolve(axis=Axis.Z)

    flange = Cylinder(
        radius=flange_d / 2,
        height=flange_t,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    flange = Location((0, 0, -flange_t / 2)) * flange
    lip = Torus(
        major_radius=mouth_outer_r - lip_r,
        minor_radius=lip_r,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    lip = Location((0, 0, length)) * lip

    horn = horn_body.part + flange + lip
    horn -= _cylinder_z(
        diameter=throat_d,
        depth=flange_t + wall_t + 1.0,
        center=(0, 0, -flange_t / 2 + (flange_t + wall_t + 1.0) / 2 - 0.5),
    )

    for index in range(3):
        angle = math.tau * index / 3 + math.pi / 2
        radius = bolt_3_bcd / 2
        horn -= _cylinder_z(
            diameter=bolt_clearance_d,
            depth=flange_t + 2.0,
            center=(
                radius * math.cos(angle),
                radius * math.sin(angle),
                -flange_t / 2,
            ),
        )

    for angle in (0.0, math.pi):
        radius = bolt_2_bcd / 2
        horn -= _cylinder_z(
            diameter=bolt_clearance_d,
            depth=flange_t + 2.0,
            center=(
                radius * math.cos(angle),
                radius * math.sin(angle),
                -flange_t / 2,
            ),
        )

    return horn


def horn_dimensions(part: Part) -> dict[str, object]:
    bb = part.bounding_box()
    return {
        "bounding_box_mm": (
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ),
        "volume_cm3": round(part.volume / 1000, 1),
        "is_valid": part.is_valid,
        "n_solids": len(part.solids()),
        "n_faces": len(part.faces()),
        "n_edges": len(part.edges()),
    }
