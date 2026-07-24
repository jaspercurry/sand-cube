"""Variant R hybrid left/right/top plus flat-bottom perimeter builder."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from build123d import Edge, Vector, Wire

from .parameters import VARIANT_R_PARAMETERS, VariantRParameters


def build_hybrid_perimeter_wire(
    authoritative_builder: Callable[..., Any],
    *,
    offset_mm: float,
    y_mm: float,
    parameters: VariantRParameters = VARIANT_R_PARAMETERS,
) -> Wire:
    """Reuse exact authoritative L/R/T edges and replace only the bottom run."""

    authoritative = authoritative_builder(offset_mm=offset_mm, y_mm=y_mm)
    half_size = parameters.path_half_size_mm + offset_mm
    tangency = parameters.path_bottom_corner_tangency_mm
    tolerance = 1e-6

    retained_edges: list[Edge] = []
    removed_bottom_edges: list[Edge] = []
    for edge in authoritative.edges():
        bounds = edge.bounding_box()
        is_bottom_center_detour = (
            bounds.min.X >= -tangency - tolerance
            and bounds.max.X <= tangency + tolerance
            and bounds.min.Z >= -half_size - tolerance
            and bounds.max.Z
            <= -half_size + parameters.screw_bypass_depth_mm + tolerance
        )
        if is_bottom_center_detour:
            removed_bottom_edges.append(edge)
        else:
            retained_edges.append(edge)

    if len(removed_bottom_edges) != 4 or len(retained_edges) != 10:
        raise ValueError(
            "Authoritative bottom-center detour selection changed: "
            f"removed={len(removed_bottom_edges)}, "
            f"retained={len(retained_edges)}"
        )

    flat_bottom = Edge.make_line(
        Vector(tangency, y_mm, -half_size),
        Vector(-tangency, y_mm, -half_size),
    )
    wires = Wire.combine([*retained_edges, flat_bottom])
    if len(wires) != 1 or not wires[0].is_closed:
        raise ValueError("Hybrid L/R/T nested + flat-bottom perimeter did not close")
    return wires[0]
