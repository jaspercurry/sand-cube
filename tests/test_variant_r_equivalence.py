from __future__ import annotations

from copy import deepcopy

from src.enclosure_family.variant_r.equivalence import (
    material_comparison_passes,
    numbers_equal,
    shape_records_equal,
)


def _shape_record() -> dict[str, object]:
    return {
        "valid": True,
        "positive_solid_count": 1,
        "topology": {
            "shape_count": 1,
            "solid_count": 1,
            "shell_count": 1,
            "face_count": 6,
            "edge_count": 12,
            "vertex_count": 8,
            "boundary_edge_count": 0,
            "manifold_edge_count": 12,
            "non_manifold_edge_count": 0,
        },
        "bounds_mm": {
            "min": [0.0, 0.0, 0.0],
            "max": [1.0, 2.0, 3.0],
            "size": [1.0, 2.0, 3.0],
        },
        "volume_mm3": 6.0,
        "surface_area_mm2": 22.0,
        "center_of_mass_mm": [0.5, 1.0, 1.5],
    }


def test_variant_r_shape_equivalence_covers_every_owned_measurement() -> None:
    reference = _shape_record()
    candidate = deepcopy(reference)
    assert shape_records_equal(reference, candidate)
    candidate["volume_mm3"] = 6.001
    assert not shape_records_equal(reference, candidate)


def test_variant_r_diagnostic_identity_uses_only_owned_tolerance() -> None:
    assert numbers_equal({"value": [1.0]}, {"value": [1.0 + 5e-10]})
    assert not numbers_equal({"value": [1.0]}, {"value": [1.0 + 2e-9]})


def test_variant_r_material_comparison_fails_closed() -> None:
    passing = {
        "removed_volume_mm3": 0.0,
        "added_volume_mm3": 0.0,
        "diagnostic": {"usable": True},
    }
    assert material_comparison_passes(passing)
    unusable = deepcopy(passing)
    unusable["diagnostic"]["usable"] = False
    assert not material_comparison_passes(unusable)
