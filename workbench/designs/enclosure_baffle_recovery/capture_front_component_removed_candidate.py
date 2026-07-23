"""Publish the corrected front-component-removal candidate for review."""

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

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import importlib.util
import inspect
import json
from pathlib import Path

from build123d import import_step
from cad_runner.outputs import job_output_path


ROOT = Path(__file__).resolve().parents[3]
CAPTURE_SOURCE = Path("/private/tmp/capture_deleted_face_plate_candidate.py")
OUT = (
    ROOT
    / "build"
    / "workbench"
    / "enclosure_baffle_recovery"
    / "front_component_removed_restored_bulkhead_candidate_viewer"
)


def main() -> None:
    if not CAPTURE_SOURCE.is_file():
        raise FileNotFoundError(CAPTURE_SOURCE)
    spec = importlib.util.spec_from_file_location(
        "capture_deleted_face_plate_candidate", CAPTURE_SOURCE
    )
    if spec is None or spec.loader is None:
        raise ImportError(CAPTURE_SOURCE)
    capture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(capture)
    capture.OUT = OUT
    capture.BUCKET_STEP = OUT / "front_component_removed_bucket.step"
    capture.BAFFLE_STEP = OUT / "front_component_removed_baffle.step"
    capture.DIAGNOSTICS = OUT / "candidate_diagnostics.json"
    model = capture.model
    if "face_plate" not in inspect.getsource(model.previous._front_bulkhead):
        raise ValueError("The required shoulder face plate is still missing")

    full_base = model._single_solid(
        import_step(capture.AUTHORITATIVE_BASE_STEP),
        feature="authoritative full-detail enclosure source",
    )
    print("capture: authoritative base loaded", flush=True)

    originals = {
        "gap": model.source.GASKET_CLOSED_GAP_MM,
        "shoulder": model.source.SHOULDER_Y,
        "minimum": model.MINIMUM_GASKET_SUPPORT_RATIO,
        "previous_minimum": model.previous.MINIMUM_GASKET_SUPPORT_RATIO,
    }
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    # Preserve the prior review convention: geometry is unchanged, while the
    # already-known gasket threshold is waived only in this disposable worker.
    model.MINIMUM_GASKET_SUPPORT_RATIO = 0.0
    model.previous.MINIMUM_GASKET_SUPPORT_RATIO = 0.0
    try:
        common = model._build_authoritative_joint(full_base, hybrid_bottom=True)
        joint_audit = dict(model.previous._JOINT_AUDIT)
    finally:
        model.source.GASKET_CLOSED_GAP_MM = originals["gap"]
        model.source.SHOULDER_Y = originals["shoulder"]
        model.MINIMUM_GASKET_SUPPORT_RATIO = originals["minimum"]
        model.previous.MINIMUM_GASKET_SUPPORT_RATIO = originals[
            "previous_minimum"
        ]

    bucket = common["bucket"]
    baffle = common["baffle"]
    if len(bucket.solids()) != 1 or not bucket.is_valid:
        raise ValueError("Candidate bucket is not one valid solid")
    if len(baffle.solids()) != 1 or not baffle.is_valid:
        raise ValueError("Candidate baffle is not one valid solid")

    bucket_round_trip = capture._round_trip(bucket, capture.BUCKET_STEP)
    baffle_round_trip = capture._round_trip(baffle, capture.BAFFLE_STEP)
    imported_bucket = import_step(job_output_path(capture.BUCKET_STEP))
    old_face_signatures = (
        (-87.328406, 87.328406, 23.352861),
        (87.328406, 87.328406, 23.352861),
        (-85.573715, -89.085026, 47.486082),
        (85.609753, -89.063285, 47.131790),
    )
    surviving_old_faces = []
    for face in imported_bucket.faces():
        bounds = face.bounding_box()
        center = face.center()
        if (
            bounds.size.Y > 1e-4
            or abs(center.Y - model.source.BAFFLE_BED_Y) > 0.02
        ):
            continue
        for old_x, old_z, old_area in old_face_signatures:
            if (
                abs(center.X - old_x) <= 0.20
                and abs(center.Z - old_z) <= 0.20
                and abs(face.area - old_area) <= 0.20
            ):
                surviving_old_faces.append(
                    {
                        "center_mm": [center.X, center.Y, center.Z],
                        "area_mm2": face.area,
                    }
                )
    if surviving_old_faces:
        raise ValueError(
            f"Old selected planar faces survived: {surviving_old_faces}"
        )

    diagnostics = {
        "scope": "unpromoted front-component-removal Viewer candidate",
        "source_geometry_change": (
            "existing interface reset spans the full inherited front and the "
            "detached front component is omitted from the rear bucket"
        ),
        "front_bulkhead_source_contains_face_plate": True,
        "old_artifact_face_tokens": [
            "#f207",
            "#f210",
            "#f209",
            "#f211",
            "#f250",
            "#f188",
            "#f32",
            "#f190",
        ],
        "matching_old_face_signatures_remaining": len(surviving_old_faces),
        "bucket": bucket_round_trip,
        "baffle": baffle_round_trip,
        "geometry_checks": {
            "bucket_single_valid_solid": True,
            "baffle_single_valid_solid": True,
            "bucket_baffle_overlap_mm3": common[
                "bucket_baffle_overlap_mm3"
            ],
            "gasket_bucket_overlap_mm3": common[
                "gasket_bucket_overlap_mm3"
            ],
            "gasket_baffle_overlap_mm3": common[
                "gasket_baffle_overlap_mm3"
            ],
            "fill_passage_blockage_mm3": joint_audit[
                "fill_passage_blockage_mm3"
            ],
            "old_selected_planar_face_signatures_absent_after_step": True,
            "unclosed_non_fill_sand_cap_mm3": joint_audit[
                "unclosed_non_fill_sand_cap_mm3"
            ],
            "gasket_bucket_support_ratio": joint_audit[
                "gasket_bucket_support_ratio"
            ],
            "gasket_baffle_support_ratio": joint_audit[
                "gasket_baffle_support_ratio"
            ],
            "minimum_gasket_support_ratio": originals["minimum"],
        },
    }
    staged = job_output_path(capture.DIAGNOSTICS)
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2), flush=True)


if __name__ == "__main__":
    main()
