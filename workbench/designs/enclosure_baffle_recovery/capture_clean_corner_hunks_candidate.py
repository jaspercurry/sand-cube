"""Build and publish the minimal corner-hunk correction for review."""

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

from build123d import Compound, Shape, Unit, export_step, import_step
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_ON


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
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure/"
    "sand_cube_190x210_single_oval_port_base.step"
)
BASELINE_STEP = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step"
)
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _round_trip(shape: Any, destination: Path) -> tuple[Any, dict[str, Any]]:
    staged = job_output_path(destination)
    staged.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, staged, unit=Unit.MM, write_pcurves=True)
    imported = import_step(staged)
    solids = imported.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(
            f"{destination.name} failed STEP round trip: "
            f"solids={len(solids)}, valid={[solid.is_valid for solid in solids]}"
        )
    return solids[0], {
        "path": str(destination),
        "sha256": _sha256(staged),
        "source_solid_count": len(shape.solids()),
        "imported_solid_count": len(solids),
        "all_imported_solids_valid": True,
        "volume_mm3": solids[0].volume,
        "face_count": len(solids[0].faces()),
        "edge_count": len(solids[0].edges()),
    }


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


def _forward_seat_occupancy_identity(baseline: Any, candidate: Any) -> dict[str, Any]:
    baseline_classifier = BRepClass3d_SolidClassifier(baseline.wrapped)
    candidate_classifier = BRepClass3d_SolidClassifier(candidate.wrapped)

    def occupied(classifier: Any, point: tuple[float, float, float]) -> bool:
        classifier.Perform(gp_Pnt(*point), 1e-7)
        return classifier.State() in (TopAbs_IN, TopAbs_ON)

    points = []
    xz_values = [-94.5 + 2.0 * index for index in range(95)]
    for y_mm in (-86.5, -84.5, -82.5, -80.5, -79.25):
        for x_mm in xz_values:
            for z_mm in xz_values:
                if max(abs(x_mm), abs(z_mm)) < 68.0:
                    continue
                points.append((x_mm, y_mm, z_mm))
    mismatches = [
        point
        for point in points
        if occupied(baseline_classifier, point)
        != occupied(candidate_classifier, point)
    ]
    if mismatches:
        raise ValueError(
            "The protected forward curved seat changed at "
            f"{len(mismatches)} of {len(points)} points; first={mismatches[0]}"
        )
    return {
        "sample_count": len(points),
        "grid_spacing_mm": 2.0,
        "y_sections_mm": [-86.5, -84.5, -82.5, -80.5, -79.25],
        "occupancy_mismatch_count": 0,
    }


def main() -> None:
    _install_legacy_intersect_adapter()
    for path in (BASE_STEP, BASELINE_STEP, TARGET_STEP):
        if not path.is_file():
            raise FileNotFoundError(path)

    full_base = model._single_solid(
        import_step(BASE_STEP),
        feature="authoritative full-detail enclosure source",
    )
    print("candidate: authoritative base loaded", flush=True)

    originals = {
        "gap": model.source.GASKET_CLOSED_GAP_MM,
        "shoulder": model.source.SHOULDER_Y,
    }
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    try:
        common = model._build_authoritative_joint(full_base, hybrid_bottom=True)
        joint_audit = dict(model.previous._JOINT_AUDIT)
    finally:
        model.source.GASKET_CLOSED_GAP_MM = originals["gap"]
        model.source.SHOULDER_Y = originals["shoulder"]

    bucket = common["bucket"]
    baffle = common["baffle"]
    if len(bucket.solids()) != 1 or not bucket.is_valid:
        raise ValueError("Candidate bucket is not one valid solid")
    if len(baffle.solids()) != 1 or not baffle.is_valid:
        raise ValueError("Candidate baffle is not one valid solid")

    imported_bucket, bucket_round_trip = _round_trip(bucket, BUCKET_STEP)
    imported_baffle, baffle_round_trip = _round_trip(baffle, BAFFLE_STEP)
    target = import_step(TARGET_STEP)
    selected_target_remaining = _volume(imported_bucket.intersect(target))
    if selected_target_remaining > 0.01:
        raise ValueError(
            "Selected corner-hunk target remains after STEP: "
            f"{selected_target_remaining:.6f} mm3"
        )

    baseline = model._single_solid(
        import_step(BASELINE_STEP),
        feature="immutable pre-mistake bucket baseline",
    )
    forward_seat = _forward_seat_occupancy_identity(baseline, imported_bucket)
    baseline_bounds = _bounds(baseline)
    candidate_bounds = _bounds(imported_bucket)
    bounds_difference = {
        key: candidate_bounds[key] - baseline_bounds[key]
        for key in baseline_bounds
    }
    if max(abs(value) for value in bounds_difference.values()) > 0.001:
        raise ValueError(f"Candidate exterior bounds changed: {bounds_difference}")

    diagnostics = {
        "scope": "minimal existing-interface reset correction",
        "source_change": (
            "existing _broad_interface_reset outer profile changed from "
            "184.2 mm/r20 to 184.3 mm/r7; Y limits unchanged"
        ),
        "artifact_local_source_references": {
            "artifact": str(BASELINE_STEP),
            "faces": [
                "#f207",
                "#f210",
                "#f209",
                "#f211",
                "#f250",
                "#f188",
                "#f32",
                "#f190",
            ],
        },
        "bucket": bucket_round_trip,
        "baffle": baffle_round_trip,
        "geometry_checks": {
            "selected_corner_hunk_target_remaining_mm3": selected_target_remaining,
            "protected_forward_curved_seat": forward_seat,
            "bucket_bounds_difference_from_pre_mistake_artifact_mm": bounds_difference,
            "bucket_baffle_overlap_mm3": common["bucket_baffle_overlap_mm3"],
            "gasket_bucket_overlap_mm3": common["gasket_bucket_overlap_mm3"],
            "gasket_baffle_overlap_mm3": common["gasket_baffle_overlap_mm3"],
            "fill_passage_blockage_mm3": joint_audit["fill_passage_blockage_mm3"],
            "unclosed_non_fill_sand_cap_mm3": joint_audit[
                "unclosed_non_fill_sand_cap_mm3"
            ],
            "gasket_bucket_support_ratio": joint_audit[
                "gasket_bucket_support_ratio"
            ],
            "gasket_baffle_support_ratio": joint_audit[
                "gasket_baffle_support_ratio"
            ],
            "minimum_gasket_support_ratio": model.MINIMUM_GASKET_SUPPORT_RATIO,
        },
    }
    staged = job_output_path(DIAGNOSTICS)
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2), flush=True)


if __name__ == "__main__":
    main()
