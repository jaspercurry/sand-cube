"""Native-free Variant R equivalence predicates.

Measurement modules produce facts.  This module applies the one accepted
Variant R numerical policy to those facts.  Evidence adapters decide how to
serialize and publish the resulting checkpoint.
"""

from __future__ import annotations

from math import isclose
from typing import Any

from .verification import VARIANT_R_VERIFICATION


def numbers_equal(left: Any, right: Any) -> bool:
    """Compare nested deterministic diagnostics with the owned tolerance."""

    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return isclose(
            float(left),
            float(right),
            rel_tol=0.0,
            abs_tol=VARIANT_R_VERIFICATION.tolerances.diagnostic_number,
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            numbers_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            numbers_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def shape_records_equal(
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> bool:
    """Apply the complete deterministic shape-measurement contract."""

    tolerances = VARIANT_R_VERIFICATION.tolerances
    topology_fields = (
        "shape_count",
        "solid_count",
        "shell_count",
        "face_count",
        "edge_count",
        "vertex_count",
        "boundary_edge_count",
        "manifold_edge_count",
        "non_manifold_edge_count",
    )
    return (
        reference["valid"]
        and candidate["valid"]
        and reference["positive_solid_count"]
        == candidate["positive_solid_count"]
        and all(
            reference["topology"][key] == candidate["topology"][key]
            for key in topology_fields
        )
        and all(
            isclose(a, b, rel_tol=0.0, abs_tol=tolerances.length_mm)
            for group in ("min", "max", "size")
            for a, b in zip(
                reference["bounds_mm"][group],
                candidate["bounds_mm"][group],
                strict=True,
            )
        )
        and isclose(
            reference["volume_mm3"],
            candidate["volume_mm3"],
            rel_tol=0.0,
            abs_tol=tolerances.volume_mm3,
        )
        and isclose(
            reference["surface_area_mm2"],
            candidate["surface_area_mm2"],
            rel_tol=0.0,
            abs_tol=tolerances.area_mm2,
        )
        and all(
            isclose(
                a,
                b,
                rel_tol=0.0,
                abs_tol=tolerances.center_of_mass_mm,
            )
            for a, b in zip(
                reference["center_of_mass_mm"],
                candidate["center_of_mass_mm"],
                strict=True,
            )
        )
    )


def material_comparison_passes(record: dict[str, Any]) -> bool:
    """Reject unusable or non-zero bidirectional material comparisons."""

    tolerance = VARIANT_R_VERIFICATION.tolerances.volume_mm3
    return (
        record["diagnostic"]["usable"]
        and record["removed_volume_mm3"] is not None
        and record["added_volume_mm3"] is not None
        and record["removed_volume_mm3"] <= tolerance
        and record["added_volume_mm3"] <= tolerance
    )
