"""Deterministic native measurements for Variant R evidence adapters.

This is the only Variant R module that translates live CAD objects into the
stable JSON-shaped records used by checkpoint and release evidence.  It owns
no model geometry, parameters, acceptance policy, or artifact publication.
Callers must already be running inside ``cad_runner``.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from build123d import CenterOf

from cad_geometry_checks.native import (
    compare_protected_material,
    measure_intersection,
    summarize_topology,
)

from .verification import VARIANT_R_VERIFICATION


def enum_value(value: Any) -> Any:
    """Return the stable scalar value of an enum-like measurement field."""

    return getattr(value, "value", value)


def diagnostic_record(record: Any) -> dict[str, Any]:
    """Serialize one reusable measurement diagnostic without copying policy."""

    return {
        "status": enum_value(record.status),
        "message": record.message,
        "failure_reason": (
            None
            if record.failure_reason is None
            else enum_value(record.failure_reason)
        ),
        "usable": record.usable,
    }


def topology_record(shape: Any) -> dict[str, Any]:
    """Measure and serialize deterministic topology for one shape."""

    summary = summarize_topology(shape)
    result = asdict(summary)
    result["unit"] = enum_value(summary.unit)
    result["diagnostic"] = diagnostic_record(summary.diagnostic)
    return result


def shape_record(shape: Any) -> dict[str, Any]:
    """Measure validity, topology, bounds, mass properties, and center."""

    solids = tuple(solid for solid in shape.solids() if solid.volume > 1e-9)
    if not solids:
        raise ValueError("STEP contains no positive-volume solid")
    volume = sum(solid.volume for solid in solids)
    center = tuple(
        sum(
            solid.volume * getattr(solid.center(CenterOf.MASS), axis)
            for solid in solids
        )
        / volume
        for axis in ("X", "Y", "Z")
    )
    bounds = shape.bounding_box()
    return {
        "valid": bool(shape.is_valid)
        and all(bool(solid.is_valid) for solid in solids),
        "positive_solid_count": len(solids),
        "topology": topology_record(shape),
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "volume_mm3": volume,
        "surface_area_mm2": sum(face.area for face in shape.faces()),
        "center_of_mass_mm": list(center),
    }


def material_comparison_record(
    reference: Any,
    candidate: Any,
) -> dict[str, Any]:
    """Measure bidirectional material change using the Variant R policy."""

    tolerances = VARIANT_R_VERIFICATION.tolerances
    result = compare_protected_material(
        reference,
        candidate,
        bounding_box_tolerance_mm=tolerances.length_mm,
        volume_tolerance_mm3=tolerances.volume_mm3,
    )
    return {
        "reference_volume_mm3": result.reference_volume_mm3,
        "candidate_volume_mm3": result.candidate_volume_mm3,
        "removed_volume_mm3": result.removed_volume_mm3,
        "added_volume_mm3": result.added_volume_mm3,
        "diagnostic": diagnostic_record(result.diagnostic),
    }


def intersection_record(left: Any, right: Any) -> dict[str, Any]:
    """Measure mating overlap without collapsing contact to a false failure."""

    tolerances = VARIANT_R_VERIFICATION.tolerances
    result = measure_intersection(
        left,
        right,
        bounding_box_tolerance_mm=tolerances.length_mm,
        boolean_tolerance_mm=tolerances.length_mm,
        volume_tolerance_mm3=tolerances.volume_mm3,
    )
    return {
        "volume_mm3": result.volume_mm3,
        "outcome": enum_value(result.outcome),
        "diagnostic": diagnostic_record(result.diagnostic),
    }
