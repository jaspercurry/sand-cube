"""Trace the Viewer-selected front-corner residue through bucket construction.

The selected ``#f...`` tokens are deliberately not used as topology selectors.
Their measured bounds define four semantic corner regions on the exact
candidate STEP.  Each region is intersected with the existing construction
stages to identify the operation that creates or fails to remove the material.
"""

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

from build123d import Align, Box, Compound, Pos, Shape, import_step


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


BASE_STEP = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
    / "sand_cube_190x210_single_oval_port_base.step"
)
CANDIDATE_STEP = (
    ROOT
    / "build"
    / "workbench"
    / "enclosure_baffle_recovery"
    / "deleted_face_plate_candidate_viewer"
    / "deleted_face_plate_bucket.step"
)
REPORT = (
    ROOT
    / "build"
    / "workbench"
    / "enclosure_baffle_recovery"
    / "selected_corner_residue_provenance.json"
)


def _install_legacy_intersect_adapter() -> None:
    original_intersect = Shape.intersect

    def legacy_intersect(self, *others, **kwargs):
        result = original_intersect(self, *others, **kwargs)
        if result is None:
            return None
        if isinstance(result, list):
            if len(result) == 1:
                return result[0]
            return Compound(children=list(result))
        return result

    Shape.intersect = legacy_intersect


def _volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _one_solid(shape: Any, *, feature: str):
    solids = [solid for solid in shape.solids() if solid.volume > 1e-6]
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{feature} is not one valid solid: {len(solids)}")
    return solids[0]


def _corner_regions(baffle_bed_y: float) -> dict[str, Any]:
    # Bounds are padded from the exact Viewer-selected faces.  The 1.25 mm
    # depth includes all selected side/cylindrical faces beginning at the
    # baffle-bed plane.  The bucket shoulder is exactly 1 mm farther rearward.
    y_center = baffle_bed_y + 0.60
    y_size = 1.20
    return {
        "upper_left": Pos(-85.5, y_center, 85.5)
        * Box(10.0, y_size, 10.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "upper_right": Pos(85.5, y_center, 85.5)
        * Box(10.0, y_size, 10.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "lower_left": Pos(-82.25, y_center, -86.75)
        * Box(19.0, y_size, 11.5, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        "lower_right": Pos(82.25, y_center, -86.75)
        * Box(19.0, y_size, 11.5, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
    }


def _presence(target: Any, shape: Any) -> dict[str, float]:
    target_volume = _volume(target)
    overlap = _volume(target.intersect(shape))
    return {
        "target_volume_mm3": target_volume,
        "overlap_mm3": overlap,
        "presence_ratio": overlap / target_volume if target_volume else 0.0,
    }


def main() -> None:
    _install_legacy_intersect_adapter()
    if not BASE_STEP.is_file():
        raise FileNotFoundError(BASE_STEP)
    if not CANDIDATE_STEP.is_file():
        raise FileNotFoundError(CANDIDATE_STEP)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    original_perimeter = model.single._perimeter_wire
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        full_base = _one_solid(import_step(BASE_STEP), feature="full base")
        final_candidate = _one_solid(
            import_step(CANDIDATE_STEP), feature="candidate bucket"
        )
        clearance = model.closure._nested_split_envelope(
            clearance_mm=model.closure.SOCKET_NORMAL_CLEARANCE_MM
        )
        initial_bucket = _one_solid(
            full_base.cut(clearance).clean().fix(),
            feature="bucket after nested split",
        )
        broad_reset = model.simplified._broad_interface_reset(
            model.source.BAFFLE_BED_Y
            - model.previous.BAFFLE_STRUCTURE_THICKNESS_MM
            - 0.15,
            model.source.SHOULDER_Y + 0.20,
        )
        after_reset_raw = initial_bucket.cut(broad_reset).clean().fix()
        after_reset_solids = [
            solid for solid in after_reset_raw.solids() if solid.volume > 1e-6
        ]
        if not after_reset_solids or not all(
            solid.is_valid for solid in after_reset_solids
        ):
            raise ValueError("bucket after broad interface reset is invalid")
        after_reset = Compound(children=after_reset_solids)
        service_opening = model.previous._projected_service_opening_clearance()
        after_service_raw = after_reset.cut(service_opening).clean().fix()
        after_service_solids = [
            solid for solid in after_service_raw.solids() if solid.volume > 1e-6
        ]
        if not after_service_solids or not all(
            solid.is_valid for solid in after_service_solids
        ):
            raise ValueError("bucket after projected service opening is invalid")
        after_service = Compound(children=after_service_solids)
        face_plate, support_wedge, _bulkhead, _audit = (
            model.previous._front_bulkhead()
        )
        fill_features = [
            model.simplified._front_fill_feature(sign) for sign in (-1.0, 1.0)
        ]
        fill_supports = Compound(
            children=[feature["support"] for feature in fill_features]
        )

        regions = _corner_regions(model.source.BAFFLE_BED_Y)
        stages = {
            "full_base": full_base,
            "nested_split_clearance_envelope": clearance,
            "initial_bucket_after_nested_split": initial_bucket,
            "broad_interface_reset_cutter": broad_reset,
            "bucket_after_broad_interface_reset": after_reset,
            "projected_service_opening_cutter": service_opening,
            "bucket_after_projected_service_opening": after_service,
            "support_wedge_addition": support_wedge,
            "face_plate_addition": face_plate,
            "fill_support_additions": fill_supports,
            "final_candidate_bucket": final_candidate,
        }
        result: dict[str, Any] = {
            "artifact": str(CANDIDATE_STEP),
            "artifact_local_references": [
                "#f207",
                "#f210",
                "#f209",
                "#f211",
                "#f250",
                "#f188",
                "#f32",
                "#f190",
            ],
            "semantic_target": (
                "four shallow outer-corner residues at the bucket shoulder "
                "plane, ahead of the support wedge"
            ),
            "baffle_bed_y_mm": model.source.BAFFLE_BED_Y,
            "shoulder_y_mm": model.source.SHOULDER_Y,
            "support_wedge_min_y_mm": support_wedge.bounding_box().min.Y,
            "after_reset_solid_pieces": [
                {
                    "volume_mm3": solid.volume,
                    "bbox_min_mm": [
                        solid.bounding_box().min.X,
                        solid.bounding_box().min.Y,
                        solid.bounding_box().min.Z,
                    ],
                    "bbox_max_mm": [
                        solid.bounding_box().max.X,
                        solid.bounding_box().max.Y,
                        solid.bounding_box().max.Z,
                    ],
                }
                for solid in sorted(
                    after_reset_solids, key=lambda item: item.volume, reverse=True
                )
            ],
            "regions": {},
        }
        for label, region in regions.items():
            target = final_candidate.intersect(region)
            if _volume(target) <= 1e-6:
                raise ValueError(f"No candidate material in {label} target region")
            result["regions"][label] = {
                name: _presence(target, stage) for name, stage in stages.items()
            }

        target_all = Compound(
            children=[final_candidate.intersect(region) for region in regions.values()]
        )
        result["all_regions"] = {
            name: _presence(target_all, stage) for name, stage in stages.items()
        }
        result["conclusion_inputs"] = {
            "target_predates_all_current_additions": all(
                result["all_regions"][name]["presence_ratio"] < 1e-6
                for name in ("support_wedge_addition", "fill_support_additions")
            ),
            "target_is_inherited_from_full_base": (
                result["all_regions"]["full_base"]["presence_ratio"] > 0.999
            ),
            "nested_split_leaves_target_in_bucket": (
                result["all_regions"]["initial_bucket_after_nested_split"]
                ["presence_ratio"]
                > 0.999
            ),
            "broad_reset_misses_target": (
                result["all_regions"]["broad_interface_reset_cutter"]
                ["presence_ratio"]
                < 0.001
            ),
            "service_opening_misses_target": (
                result["all_regions"]["projected_service_opening_cutter"]
                ["presence_ratio"]
                < 0.001
            ),
        }
    finally:
        model.single._perimeter_wire = original_perimeter
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder

    staged = job_output_path(REPORT)
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
