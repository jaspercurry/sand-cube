"""Test exact, localized restoration of authoritative Variant R bucket material."""

from __future__ import annotations


# This guard must remain before all native CAD/threaded-library imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
import sys
from pathlib import Path
from typing import Any

from build123d import Align, Box, Compound, Pos, import_step

from src.enclosure_family.legacy_runtime import (
    LegacyAttributeBinding,
    bind_legacy_attributes,
)
from src.enclosure_family.variant_r.export import publish_step_round_trip
from src.enclosure_family.variant_r.inputs import authoritative_base_step


ROOT = _CAD_SAFETY_ROOT
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))
WORKBENCH = Path(__file__).resolve().parent
if str(WORKBENCH) not in sys.path:
    sys.path.insert(0, str(WORKBENCH))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
import validate_simple_tongue_groove_baffle as validator  # noqa: E402
import audit_production_candidate_fit as fit_audit  # noqa: E402


CANDIDATE = ROOT / "build/workbench/variant_r_no_splice_production/candidate"
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_no_splice_production/"
    "bucket-material-restoration-feasibility.json"
)
RESTORED = (
    ROOT
    / "build/workbench/variant_r_no_splice_production/restoration"
)
BOTTOM_TANGENCY_Z_MM = -model.VARIANT_R_PARAMETERS.path_bottom_corner_tangency_mm
SELECTION_TOLERANCE_MM = 1e-6


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _bounds(shape: Any) -> dict[str, list[float]]:
    bounds = shape.bounding_box()
    return {
        "min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size_mm": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def _component_record(index: int, solid: Any) -> dict[str, Any]:
    return {
        "index": index,
        "volume_mm3": solid.volume,
        "bounds": _bounds(solid),
        "valid": solid.is_valid,
        "face_count": len(solid.faces()),
        "edge_count": len(solid.edges()),
    }


def _overlap(left: Any, right: Any) -> float:
    return _shape_volume(left & right)


def _audit_restoration(
    restored_shape: Any,
    *,
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    restored_solids = list(restored_shape.solids())
    record: dict[str, Any] = {
        "solid_count": len(restored_solids),
        "validity": [solid.is_valid for solid in restored_solids],
    }
    if len(restored_solids) != 1 or not restored_solids[0].is_valid:
        record["conflict"] = (
            "Restoration Boolean did not yield one valid bucket solid."
        )
        return record, False

    restored = restored_solids[0]
    strict_error = None
    try:
        seam_identity = validator._seam_identity(
            reference,
            {
                "bucket": restored,
                "baffle": candidate["baffle"],
            },
        )
    except ValueError as error:
        seam_identity = None
        strict_error = str(error)
    topology_error = None
    try:
        topology = validator._no_splice_topology_audit(
            restored,
            part_name="bucket",
        )
    except ValueError as error:
        topology = None
        topology_error = str(error)
    candidate_to_restored = fit_audit._protected_surface_deviation(
        candidate["bucket"],
        restored,
    )
    restored_to_candidate = fit_audit._protected_surface_deviation(
        restored,
        candidate["bucket"],
    )
    overlap = {
        "bucket_baffle_mm3": _overlap(restored, candidate["baffle"]),
        "bucket_gasket_mm3": _overlap(restored, candidate["gasket"]),
    }
    candidate_removed = _shape_volume(candidate["bucket"] - restored)
    candidate_topology = {
        "face_count": len(candidate["bucket"].faces()),
        "edge_count": len(candidate["bucket"].edges()),
        "vertex_count": len(candidate["bucket"].vertices()),
    }
    restored_topology = {
        "face_count": len(restored.faces()),
        "edge_count": len(restored.edges()),
        "vertex_count": len(restored.vertices()),
    }
    topology_unchanged = restored_topology == candidate_topology
    record.update(
        {
            "strict_seam_material_identity": seam_identity,
            "strict_seam_material_error": strict_error,
            "no_splice_topology": topology,
            "no_splice_topology_error": topology_error,
            "protected_candidate_surface_deviation": {
                "candidate_to_restored": candidate_to_restored,
                "restored_to_candidate": restored_to_candidate,
            },
            "overlap": overlap,
            "candidate_material_removed_mm3": candidate_removed,
            "candidate_topology": candidate_topology,
            "restored_topology": restored_topology,
            "topology_unchanged": topology_unchanged,
        }
    )
    maximum_visible_deviation = max(
        candidate_to_restored["maximum_point_deviation_mm"],
        restored_to_candidate["maximum_point_deviation_mm"],
    )
    feasible = (
        strict_error is None
        and topology_error is None
        and topology is not None
        and topology["old_splice_height_edge_count"] == 0
        and topology["unrelated_full_width_lower_apron_edge_count"] == 0
        and max(overlap.values()) <= 1e-6
        and candidate_removed <= 1e-6
        and maximum_visible_deviation <= 1e-6
        and topology_unchanged
    )
    if not feasible:
        record["conflict"] = (
            "Restoration failed at least one strict material, topology, "
            "overlap or protected-surface invariant."
        )
    return record, feasible


def _reference_ownership_patches(reference_bucket: Any) -> list[Any]:
    """Return overlap-bridged patches wholly behind the active joint front."""

    y_min_mm = -76.0
    y_max_mm = -66.5
    patch_specs = (
        (-90.5, 90.5, -5.5, 90.5),
        (-90.5, -74.0, -70.0, -4.5),
        (74.0, 90.5, -70.0, -4.5),
    )
    patches = []
    for min_x_mm, max_x_mm, min_z_mm, max_z_mm in patch_specs:
        clip = Pos(
            (min_x_mm + max_x_mm) / 2.0,
            (y_min_mm + y_max_mm) / 2.0,
            (min_z_mm + max_z_mm) / 2.0,
        ) * Box(
            max_x_mm - min_x_mm,
            y_max_mm - y_min_mm,
            max_z_mm - min_z_mm,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        patches.extend(
            solid
            for solid in (reference_bucket & clip).solids()
            if solid.volume > 1e-9
        )
    return patches


def main() -> None:
    full_base = model._single_solid(
        import_step(authoritative_base_step(ROOT)),
        feature="attested production Variant R base",
    )
    candidate = {
        part: import_step(CANDIDATE / f"production_candidate_{part}.step")
        for part in ("bucket", "baffle", "gasket")
    }
    bindings = (
        LegacyAttributeBinding(
            model.source,
            "GASKET_CLOSED_GAP_MM",
            model.GASKET_CLOSED_GAP_MM,
        ),
        LegacyAttributeBinding(
            model.source,
            "SHOULDER_Y",
            model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM,
        ),
    )
    with bind_legacy_attributes(bindings):
        reference = model._authoritative_reference_joint(full_base)

    reference_only = reference["bucket"] - candidate["bucket"]
    components = list(reference_only.solids())
    component_records = [
        _component_record(index, solid)
        for index, solid in enumerate(components)
    ]
    selected = [
        solid
        for solid in components
        if (
            solid.bounding_box().min.Z
            >= BOTTOM_TANGENCY_Z_MM - SELECTION_TOLERANCE_MM
            and solid.volume > 1e-9
        )
    ]
    result: dict[str, Any] = {
        "scope": (
            "focused feasibility check; exact natural reference-only Boolean "
            "components, no clipping, no cleaning, no healing, no splitter "
            "removal and no tolerance widening"
        ),
        "selection": {
            "criterion": (
                "natural reference-only component has min Z at or above the "
                "existing bottom tangency"
            ),
            "bottom_tangency_z_mm": BOTTOM_TANGENCY_Z_MM,
            "selection_tolerance_mm": SELECTION_TOLERANCE_MM,
            "component_count": len(components),
            "selected_component_count": len(selected),
            "reference_only_volume_mm3": _shape_volume(reference_only),
            "selected_volume_mm3": sum(solid.volume for solid in selected),
            "components": component_records,
        },
        "feasible": False,
    }
    if not selected:
        result["conflict"] = (
            "No exact reference-only material component is separable above "
            "the bottom tangency without introducing an artificial clip "
            "boundary."
        )
    else:
        fused = candidate["bucket"].fuse(*selected)
        natural_record, natural_feasible = _audit_restoration(
            fused,
            reference=reference,
            candidate=candidate,
        )
        result["restoration_boolean"] = {
            "operation": (
                "candidate bucket fused with exact natural reference-only "
                "components"
            ),
            "clean_applied": False,
            "fix_applied": False,
            "splitter_removal_applied": False,
            "healing_applied": False,
            "tolerance_widening_applied": False,
            **natural_record,
        }
        result["feasible"] = natural_feasible
        if not natural_feasible:
            result["conflict"] = (
                "The exact natural-component union did not yield one valid "
                "bucket satisfying every unchanged invariant."
            )

    if not result["feasible"]:
        ownership_patches = _reference_ownership_patches(reference["bucket"])
        patch_fused = candidate["bucket"].fuse(*ownership_patches)
        patch_record, patch_feasible = _audit_restoration(
            patch_fused,
            reference=reference,
            candidate=candidate,
        )
        result["overlap_bridged_reference_patch"] = {
            "operation": (
                "candidate bucket fused with three localized reference-owned "
                "L/R/T seam patches; overlap is existing shared material"
            ),
            "patch_count": len(ownership_patches),
            "patch_volume_mm3": sum(
                patch.volume for patch in ownership_patches
            ),
            "patch_bounds": [_bounds(patch) for patch in ownership_patches],
            "front_y_limit_mm": -76.0,
            "bottom_z_limit_mm": -70.0,
            "clean_applied": False,
            "fix_applied": False,
            "splitter_removal_applied": False,
            "healing_applied": False,
            "tolerance_widening_applied": False,
            **patch_record,
        }
        result["feasible"] = patch_feasible
        if patch_feasible:
            restored = patch_fused.solids()[0]
            RESTORED.mkdir(parents=True, exist_ok=True)
            result["round_trip"] = {
                "bucket": publish_step_round_trip(
                    RESTORED / "restored_bucket.step",
                    restored,
                    require_single_solid=True,
                ),
                "assembly": publish_step_round_trip(
                    RESTORED / "restored_review_assembly.step",
                    Compound(
                        children=[
                            restored,
                            candidate["baffle"],
                            candidate["gasket"],
                        ]
                    ),
                    require_single_solid=False,
                ),
            }
            result.pop("conflict", None)
        else:
            result["conflict"] = (
                "Neither exact natural components nor overlap-bridged "
                "localized reference ownership patches preserve every "
                "unchanged invariant."
            )

    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
