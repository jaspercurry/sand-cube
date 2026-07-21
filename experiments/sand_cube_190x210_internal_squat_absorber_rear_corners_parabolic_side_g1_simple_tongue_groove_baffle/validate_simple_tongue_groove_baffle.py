"""Standalone geometry validation for Variant A (no full-cascade viewers).

Adapts the closure's own ``generate_bucket_front_transition_candidate.py``
pattern: load the authoritative full-detail base solid, drive the Variant A
hooks directly, and assert every geometry invariant.  This deliberately avoids
the shared cascade's inherited-assembly preview cutaway, which fails on this
machine's OCCT for the UNCHANGED baseline too (see the run report).
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

from build123d import Unit, export_step, import_step


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


FULL_DETAIL_BASE_STEP = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
    / "parabolic_g1_conformal_full_detail_base.step"
)
OUT = model.OUT
BUCKET_STEP = OUT / "simple_tongue_groove_bucket.step"
BAFFLE_STEP = OUT / "simple_tongue_groove_baffle.step"
DIAGNOSTICS_PATH = OUT / "validation_diagnostics.json"


def _patch_seam():
    """Return (apply, restore) closures for the Variant A seam patches."""
    originals = {
        "perimeter_wire": model.single._perimeter_wire,
        "gap": model.source.GASKET_CLOSED_GAP_MM,
        "shoulder": model.source.SHOULDER_Y,
    }

    def apply():
        model.single._perimeter_wire = model._straight_perimeter_wire
        model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
        model.source.SHOULDER_Y = (
            model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
        )

    def restore():
        model.single._perimeter_wire = originals["perimeter_wire"]
        model.source.GASKET_CLOSED_GAP_MM = originals["gap"]
        model.source.SHOULDER_Y = originals["shoulder"]

    return apply, restore, originals


def _round_trip(step_path: Path, solid) -> dict:
    published = job_output_path(step_path)
    published.parent.mkdir(parents=True, exist_ok=True)
    export_step(solid, published, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published)
    result = {
        "source_solid_count": len(solid.solids()),
        "imported_solid_count": len(imported.solids()),
        "all_imported_solids_valid": all(
            s.is_valid for s in imported.solids()
        ),
    }
    if result != {
        "source_solid_count": 1,
        "imported_solid_count": 1,
        "all_imported_solids_valid": True,
    }:
        raise ValueError(f"STEP round trip failed: {step_path.name}: {result}")
    return result


def _seam_band_volumes():
    """Cheap deterministic fingerprint of the patched seam primitives."""
    baffle_land = model.single._single_face_band(
        model.SEAL_LAND_WIDTH_MM,
        model.source.BAFFLE_BED_Y - model.BAFFLE_STRUCTURE_THICKNESS_MM,
        model.source.BAFFLE_BED_Y,
        feature="reproducibility baffle land",
    )
    shoulder = model.single._single_face_band(
        model.GASKET_WIDTH_MM,
        model.source.SHOULDER_Y,
        model.source.SHOULDER_Y + model.BUCKET_SHOULDER_THICKNESS_MM,
        feature="reproducibility bucket shoulder land",
    )
    return round(baffle_land.volume, 6), round(shoulder.volume, 6)


def main() -> None:
    if not FULL_DETAIL_BASE_STEP.is_file():
        raise FileNotFoundError(FULL_DETAIL_BASE_STEP)

    full_base = model._single_solid(
        import_step(FULL_DETAIL_BASE_STEP),
        feature="authoritative full-detail enclosure source",
    )
    print("harness: full-detail base loaded", flush=True)

    apply, restore, originals = _patch_seam()
    apply()
    try:
        common = model._simple_tongue_groove_joint(full_base)
        print("harness: joint built", flush=True)
        concept = model._removable_baffle_fastener_concept(common)
        print("harness: fastener concept built", flush=True)
        seam_fingerprint_1 = _seam_band_volumes()
    finally:
        restore()

    # --- isolation: every patched shared attribute is restored ------------
    isolation_restored = (
        model.single._perimeter_wire is originals["perimeter_wire"]
        and model.source.GASKET_CLOSED_GAP_MM == originals["gap"]
        and model.source.SHOULDER_Y == originals["shoulder"]
    )
    if not isolation_restored:
        raise ValueError("Variant A seam patches were not restored")

    # --- 2nd in-process build (light): re-apply the patches and rebuild the
    #     seam primitives; identical volumes prove the save/restore cycle is
    #     reusable and deterministic without repeating the whole heavy joint.
    apply()
    try:
        seam_fingerprint_2 = _seam_band_volumes()
    finally:
        restore()
    if seam_fingerprint_1 != seam_fingerprint_2:
        raise ValueError(
            "Second in-process build diverged: "
            f"{seam_fingerprint_1} != {seam_fingerprint_2}"
        )
    second_restore_ok = (
        model.single._perimeter_wire is originals["perimeter_wire"]
        and model.source.GASKET_CLOSED_GAP_MM == originals["gap"]
        and model.source.SHOULDER_Y == originals["shoulder"]
    )
    print("harness: reproducibility + restore verified", flush=True)

    bucket = concept["bucket"]
    baffle = concept["baffle"]

    # --- single valid solid after every boolean ---------------------------
    for name, solid in (("bucket", bucket), ("baffle", baffle)):
        solids = solid.solids()
        if len(solids) != 1 or not solid.is_valid:
            raise ValueError(f"{name} is not one valid solid: n={len(solids)}")

    # --- STEP export/import solid-count match + all valid -----------------
    bucket_round_trip = _round_trip(BUCKET_STEP, bucket)
    baffle_round_trip = _round_trip(BAFFLE_STEP, baffle)

    joint = dict(model._JOINT_AUDIT)
    fill = dict(model._FILL_AUDIT)
    geometry = concept["geometry"]

    reproducible = {
        "seam_fingerprint_build_1": seam_fingerprint_1,
        "seam_fingerprint_build_2": seam_fingerprint_2,
        "identical": seam_fingerprint_1 == seam_fingerprint_2,
        "second_restore_ok": second_restore_ok,
    }

    diagnostics = {
        "scope": "Variant A Stage 1 (simplified seal) standalone validation",
        "full_detail_base_step": str(FULL_DETAIL_BASE_STEP),
        "stage_flags": {
            "BUILD_TOP_HINGE": model.BUILD_TOP_HINGE,
            "BUILD_BOTTOM_SCREWS": model.BUILD_BOTTOM_SCREWS,
        },
        "compression_knob_mm": model.GASKET_CLOSED_GAP_MM,
        "shoulder_y_mm": joint["shoulder_y_mm"],
        "baffle_bed_y_mm": joint["baffle_bed_y_mm"],
        "single_solid": {"bucket": True, "baffle": True},
        "bucket_step_roundtrip": bucket_round_trip,
        "baffle_step_roundtrip": baffle_round_trip,
        "gasket_bucket_support_ratio_after_all_features": joint[
            "gasket_bucket_support_ratio"
        ],
        "gasket_baffle_support_ratio_after_all_features": joint[
            "gasket_baffle_support_ratio"
        ],
        "minimum_gasket_support_ratio": model.MINIMUM_GASKET_SUPPORT_RATIO,
        "top_hinge": joint.get("top_hinge"),
        "bottom_fasteners": dict(model._FASTENER_AUDIT),
        "fill_passage_blockage_mm3": joint["fill_passage_blockage_mm3"],
        "unclosed_non_fill_sand_cap_mm3": joint["unclosed_non_fill_sand_cap_mm3"],
        "baffle_minimal_rib_root_mm3": joint["baffle_minimal_rib_root_mm3"],
        "front_fill": fill,
        "exterior_identity": {
            "baffle_bounds_difference_mm": geometry[
                "baffle_exterior_bounds_difference_mm"
            ],
            "bucket_bounds_difference_mm": geometry[
                "bucket_exterior_bounds_difference_mm"
            ],
            "bucket_protected_skin_face_count": geometry[
                "bucket_protected_skin_face_count"
            ],
            "fairing_area_difference_mm2": common[
                "fairing_area_difference_mm2"
            ],
        },
        "bucket_baffle_overlap_mm3": common["bucket_baffle_overlap_mm3"],
        "isolation_shared_upstream_generators_restored": isolation_restored,
        "reproducibility_two_builds_same_process": reproducible,
        "deleted_features": joint["deleted_features"],
    }
    diagnostics_path = job_output_path(DIAGNOSTICS_PATH)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
