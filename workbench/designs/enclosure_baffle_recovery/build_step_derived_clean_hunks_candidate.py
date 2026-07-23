"""Build a review-only candidate from the exact pre-mistake production STEP.

The production source already contains the same corrected interface-reset X/Z
profile, but its full rebuild stalled in a native Boolean.  This disposable
candidate applies that proven profile only across the 1.0 mm unwanted hunk
depth on the exact baseline STEP.  It is visual/geometry evidence, not a
substitute for later source promotion validation.
"""

from __future__ import annotations


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

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from build123d import Compound, Shape, Solid, Unit, export_step, import_step


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


PRODUCTION_DIR = (
    ROOT
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
BASELINE_BUCKET = PRODUCTION_DIR / "simple_tongue_groove_bucket.step"
BASELINE_BAFFLE = PRODUCTION_DIR / "simple_tongue_groove_baffle.step"
TARGET_STEP = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/corner_hunk_provenance/"
    "selected_corner_hunk_targets.step"
)
OUT = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "clean_corner_hunks_candidate_viewer"
)
BUCKET_STEP = OUT / "clean_corner_hunks_bucket.step"
BAFFLE_STEP = OUT / "clean_corner_hunks_baffle.step"
DIAGNOSTICS = OUT / "candidate_diagnostics.json"


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


def _one_solid(shape: Any, *, feature: str) -> Solid:
    solids = [solid for solid in shape.solids() if solid.volume > 1e-6]
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{feature} is not one valid solid: {len(solids)}")
    return solids[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bounds(shape: Any) -> dict[str, float]:
    bounds = shape.bounding_box()
    return {
        "min_x_mm": bounds.min.X,
        "min_y_mm": bounds.min.Y,
        "min_z_mm": bounds.min.Z,
        "max_x_mm": bounds.max.X,
        "max_y_mm": bounds.max.Y,
        "max_z_mm": bounds.max.Z,
    }


def main() -> None:
    _install_legacy_intersect_adapter()
    for path in (BASELINE_BUCKET, BASELINE_BAFFLE, TARGET_STEP):
        if not path.is_file():
            raise FileNotFoundError(path)

    baseline_bucket = _one_solid(
        import_step(BASELINE_BUCKET), feature="exact pre-mistake production bucket"
    )
    baseline_baffle = _one_solid(
        import_step(BASELINE_BAFFLE), feature="exact pre-mistake production baffle"
    )
    target = import_step(TARGET_STEP)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    try:
        y0 = model.source.BAFFLE_BED_Y - 0.05
        y1 = model.source.SHOULDER_Y
        outer = model.source._rounded_rectangle_prism(184.3, 7.0, y0, y1)
        inner = model.source._rounded_rectangle_prism(
            153.5, 3.5, y0 - 0.10, y1 + 0.10
        )
        interface_partition = _one_solid(
            outer.cut(inner).clean().fix(),
            feature="selected-depth corrected interface partition",
        )
        candidate = _one_solid(
            baseline_bucket.cut(interface_partition).clean().fix(),
            feature="STEP-derived clean-corner-hunk candidate",
        )

        selected_target_remaining = _volume(candidate.intersect(target))
        if selected_target_remaining > 0.01:
            raise ValueError(
                "Selected corner-hunk target remains: "
                f"{selected_target_remaining:.6f} mm3"
            )

        gasket_probe = model.single._single_face_band(
            model.GASKET_WIDTH_MM,
            model.source.SHOULDER_Y,
            model.source.SHOULDER_Y + 0.05,
            feature="restored flat gasket-face support probe",
        )
        baseline_gasket_support = _volume(
            gasket_probe.intersect(baseline_bucket)
        ) / gasket_probe.volume
        candidate_gasket_support = _volume(
            gasket_probe.intersect(candidate)
        ) / gasket_probe.volume

        passages = Compound(
            children=[
                model.simplified._front_fill_feature(sign)["passage"]
                for sign in (-1.0, 1.0)
            ]
        )
        fill_passage_blockage = _volume(passages.intersect(candidate))
        bucket_baffle_overlap = _volume(candidate.intersect(baseline_baffle))
    finally:
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder

    baseline_bounds = _bounds(baseline_bucket)
    candidate_bounds = _bounds(candidate)
    bounds_difference = {
        key: candidate_bounds[key] - baseline_bounds[key]
        for key in baseline_bounds
    }
    if max(abs(value) for value in bounds_difference.values()) > 0.001:
        raise ValueError(f"Candidate exterior bounds changed: {bounds_difference}")
    if abs(candidate_bounds["min_y_mm"] - (-87.0000001)) > 0.001:
        raise ValueError("The elegant forward-seat extent was not retained")
    if candidate_gasket_support < baseline_gasket_support - 0.001:
        raise ValueError(
            "The corrected partition reduced flat gasket-face support: "
            f"{baseline_gasket_support:.6f} -> {candidate_gasket_support:.6f}"
        )
    if fill_passage_blockage > 0.01 or bucket_baffle_overlap > 0.01:
        raise ValueError(
            "Candidate obstruction/interference: "
            f"fill={fill_passage_blockage:.6f}, baffle={bucket_baffle_overlap:.6f}"
        )

    staged_bucket = job_output_path(BUCKET_STEP)
    staged_bucket.parent.mkdir(parents=True, exist_ok=True)
    export_step(candidate, staged_bucket, unit=Unit.MM, write_pcurves=True)
    imported_candidate = _one_solid(
        import_step(staged_bucket), feature="candidate STEP round trip"
    )
    staged_baffle = job_output_path(BAFFLE_STEP)
    staged_baffle.parent.mkdir(parents=True, exist_ok=True)
    export_step(baseline_baffle, staged_baffle, unit=Unit.MM, write_pcurves=True)
    imported_baffle = _one_solid(
        import_step(staged_baffle), feature="unchanged baffle STEP round trip"
    )

    diagnostics = {
        "scope": "unpromoted STEP-derived review candidate",
        "baseline_bucket": {
            "path": str(BASELINE_BUCKET),
            "sha256": _sha256(BASELINE_BUCKET),
        },
        "source_status": (
            "the same 184.3 mm/r7 reset profile is implemented in source; "
            "full source promotion build stalled and is not claimed as passed"
        ),
        "review_candidate": {
            "path": str(BUCKET_STEP),
            "sha256": _sha256(staged_bucket),
            "solid_count": len(imported_candidate.solids()),
            "valid": imported_candidate.is_valid,
            "volume_mm3": imported_candidate.volume,
            "face_count": len(imported_candidate.faces()),
            "edge_count": len(imported_candidate.edges()),
        },
        "unchanged_baffle": {
            "path": str(BAFFLE_STEP),
            "sha256": _sha256(staged_baffle),
            "solid_count": len(imported_baffle.solids()),
            "valid": imported_baffle.is_valid,
        },
        "geometry_checks": {
            "selected_corner_hunk_target_remaining_mm3": selected_target_remaining,
            "baseline_bounds": baseline_bounds,
            "candidate_bounds": candidate_bounds,
            "bounds_difference_mm": bounds_difference,
            "forward_seat_min_y_retained": True,
            "partition_front_y_mm": y0,
            "protected_forward_seat_max_y_mm": -79.01666666666667,
            "partition_to_protected_seat_gap_mm": y0 - (-79.01666666666667),
            "baseline_gasket_support_ratio": baseline_gasket_support,
            "candidate_gasket_support_ratio": candidate_gasket_support,
            "fill_passage_blockage_mm3": fill_passage_blockage,
            "bucket_baffle_overlap_mm3": bucket_baffle_overlap,
        },
    }
    staged_diagnostics = job_output_path(DIAGNOSTICS)
    staged_diagnostics.parent.mkdir(parents=True, exist_ok=True)
    staged_diagnostics.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2), flush=True)


if __name__ == "__main__":
    main()
