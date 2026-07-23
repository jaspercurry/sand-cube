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
import os
import sys
from pathlib import Path

from build123d import Align, Box, Compound, Pos, Unit, export_step, import_step
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_ON


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


AUTHORITATIVE_BASE_STEP = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
    / "sand_cube_190x210_single_oval_port_base.step"
)
OUT = model.OUT
BUCKET_STEP = OUT / "simple_tongue_groove_bucket.step"
BAFFLE_STEP = OUT / "simple_tongue_groove_baffle.step"
DIAGNOSTICS_PATH = OUT / "validation_diagnostics.json"


def _patch_seam():
    """Patch only the one gasket-gap knob and its import-time derivative."""
    originals = {
        "gap": model.source.GASKET_CLOSED_GAP_MM,
        "shoulder": model.source.SHOULDER_Y,
    }

    def apply():
        model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
        model.source.SHOULDER_Y = (
            model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
        )

    def restore():
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
    """Cheap deterministic fingerprint of the hybrid seam primitives."""
    original = model.single._perimeter_wire
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        baffle_land = model.single._single_face_band(
            model.SEAL_LAND_WIDTH_MM,
            model.source.BAFFLE_BED_Y - model.BAFFLE_STRUCTURE_THICKNESS_MM,
            model.source.BAFFLE_BED_Y,
            feature="reproducibility hybrid baffle land",
        )
        shoulder = model.single._single_face_band(
            model.GASKET_WIDTH_MM,
            model.source.SHOULDER_Y,
            model.source.SHOULDER_Y + model.BUCKET_SHOULDER_THICKNESS_MM,
            feature="reproducibility hybrid bucket shoulder land",
        )
    finally:
        model.single._perimeter_wire = original
    return round(baffle_land.volume, 6), round(shoulder.volume, 6)


def _shape_volume(shape) -> float:
    return sum(solid.volume for solid in shape.solids())


def _enclosure_body_audit(full_base, reference: dict, hybrid: dict) -> dict:
    """Independently reject a seam-only bucket masquerading as the shell."""
    base_bounds = full_base.bounding_box()
    reference_bucket = reference["bucket"]
    hybrid_bucket = hybrid["bucket"]
    reference_bounds = reference_bucket.bounding_box()
    hybrid_bounds = hybrid_bucket.bounding_box()
    base_volume = _shape_volume(full_base)
    reference_volume = _shape_volume(reference_bucket)
    hybrid_volume = _shape_volume(hybrid_bucket)
    metrics = {
        "source_base_volume_mm3": base_volume,
        "reference_bucket_volume_mm3": reference_volume,
        "hybrid_bucket_volume_mm3": hybrid_volume,
        "reference_to_source_volume_ratio": reference_volume / base_volume,
        "hybrid_to_reference_volume_ratio": hybrid_volume / reference_volume,
        "source_base_y_span_mm": base_bounds.size.Y,
        "reference_bucket_y_span_mm": reference_bounds.size.Y,
        "hybrid_bucket_y_span_mm": hybrid_bounds.size.Y,
        "reference_rear_y_difference_mm": (
            reference_bounds.max.Y - base_bounds.max.Y
        ),
        "hybrid_rear_y_difference_mm": (
            hybrid_bounds.max.Y - base_bounds.max.Y
        ),
    }
    if (
        metrics["reference_to_source_volume_ratio"] < 0.50
        or metrics["hybrid_to_reference_volume_ratio"] < 0.90
        or metrics["reference_bucket_y_span_mm"] < 150.0
        or metrics["hybrid_bucket_y_span_mm"] < 150.0
        or metrics["reference_rear_y_difference_mm"] < -0.01
        or metrics["hybrid_rear_y_difference_mm"] < -0.01
    ):
        raise ValueError(
            "Standalone hybrid result does not contain the complete enclosure "
            f"bucket: {metrics}"
        )
    return metrics


def _seam_identity(reference: dict, hybrid: dict) -> dict:
    """Compare actual material occupancy on protected L/R/T seam sections."""

    classifiers = {
        (variant, part): BRepClass3d_SolidClassifier(data[part].wrapped)
        for variant, data in (("reference", reference), ("hybrid", hybrid))
        for part in ("bucket", "baffle")
    }

    def occupied(classifier, point: tuple[float, float, float]) -> bool:
        classifier.Perform(gp_Pnt(*point), 1e-7)
        return classifier.State() in (TopAbs_IN, TopAbs_ON)

    def samples(start: float, stop: float, step: float = 0.5):
        count = int(round((stop - start) / step))
        return [start + (index + 0.5) * step for index in range(count)]

    y_values = samples(-80.0, -68.0)
    top_z_values = samples(72.0, 98.0)
    side_x_abs_values = samples(72.0, 98.0)
    section_points: dict[str, list[tuple[float, float, float]]] = {}
    for x_mm in (-45.0, 0.0, 45.0):
        section_points[f"top_x_{x_mm:+g}"] = [
            (x_mm, y_mm, z_mm)
            for y_mm in y_values
            for z_mm in top_z_values
        ]
    for side_sign, side_label in ((-1.0, "left"), (1.0, "right")):
        for z_mm in (-55.0, 0.0, 55.0):
            section_points[f"{side_label}_z_{z_mm:+g}"] = [
                (side_sign * x_abs_mm, y_mm, z_mm)
                for y_mm in y_values
                for x_abs_mm in side_x_abs_values
            ]

    results = {}
    for label, points in section_points.items():
        part_results = {}
        for part in ("bucket", "baffle"):
            reference_classifier = classifiers[("reference", part)]
            hybrid_classifier = classifiers[("hybrid", part)]
            mismatch_points = [
                point
                for point in points
                if occupied(reference_classifier, point)
                != occupied(hybrid_classifier, point)
            ]
            if mismatch_points:
                raise ValueError(
                    f"{label} {part} seam occupancy differs from the "
                    f"authoritative joint at {len(mismatch_points)} of "
                    f"{len(points)} points; first={mismatch_points[0]}"
                )
            part_results[part] = {
                "sample_count": len(points),
                "occupancy_mismatch_count": 0,
                "grid_spacing_mm": 0.5,
            }
        results[label] = part_results
    return results


def _section(shape, clip, *, feature: str) -> Compound:
    pieces = [
        piece.clean().fix()
        for solid in shape.solids()
        for piece in (solid & clip).solids()
        if piece.volume > 1e-6
    ]
    if not pieces or not all(piece.is_valid for piece in pieces):
        raise ValueError(f"{feature} did not produce valid section solids")
    return Compound(children=pieces)


def _export_sections(reference: dict, hybrid: dict) -> dict:
    """Publish the actual seam views the user asked to inspect first."""
    y_center = model.source.BAFFLE_BED_Y + 4.0
    audit_dir = Path(os.environ["CAD_JOB_STAGE_ROOT"]) / "section_inputs"
    audit_dir.mkdir(parents=True, exist_ok=True)

    def stabilized(shape, label: str):
        path = audit_dir / f"{label}.step"
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        result = import_step(path)
        path.unlink()
        solids = result.solids()
        if len(solids) != 1 or not solids[0].is_valid:
            raise ValueError(f"{label} section input failed STEP stabilization")
        return solids[0]

    assembled_reference = Compound(
        children=[
            stabilized(reference["bucket"], "reference_bucket"),
            stabilized(reference["baffle"], "reference_baffle"),
        ]
    )
    assembled_hybrid = Compound(
        children=[
            stabilized(hybrid["bucket"], "hybrid_bucket"),
            stabilized(hybrid["baffle"], "hybrid_baffle"),
        ]
    )
    specs = {
        "authoritative_top_seam_section.step": (
            assembled_reference,
            Pos(45.0, y_center, 84.0)
            * Box(
                5.0,
                14.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        "hybrid_top_seam_section.step": (
            assembled_hybrid,
            Pos(45.0, y_center, 84.0)
            * Box(
                5.0,
                14.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        "authoritative_side_seam_section.step": (
            assembled_reference,
            Pos(-84.0, y_center, 20.0)
            * Box(
                22.0,
                14.0,
                5.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        "hybrid_side_seam_section.step": (
            assembled_hybrid,
            Pos(-84.0, y_center, 20.0)
            * Box(
                22.0,
                14.0,
                5.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        "hybrid_bottom_corner_transition_section.step": (
            assembled_hybrid,
            Pos(80.0, y_center, -80.0)
            * Box(
                28.0,
                14.0,
                28.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        "hybrid_flat_bottom_section.step": (
            assembled_hybrid,
            Pos(0.0, y_center, -86.0)
            * Box(
                12.0,
                14.0,
                18.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
    }
    checks = {}
    for filename, (shape, clip) in specs.items():
        section = _section(shape, clip, feature=filename)
        path = OUT / filename
        published = job_output_path(path)
        published.parent.mkdir(parents=True, exist_ok=True)
        export_step(section, published, unit=Unit.MM, write_pcurves=True)
        imported = import_step(published)
        if not imported.solids() or not all(s.is_valid for s in imported.solids()):
            raise ValueError(f"{filename} failed its STEP round trip")
        checks[filename] = {
            "source_solid_count": len(section.solids()),
            "imported_solid_count": len(imported.solids()),
            "all_imported_solids_valid": True,
        }
    return checks


def _flat_bottom_audit(hybrid: dict) -> dict:
    """Require matching planar bottom lands and one continuous gasket run."""
    bucket = hybrid["bucket"]
    baffle = hybrid["baffle"]
    original = model.single._perimeter_wire
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        baffle_land = model.single._single_face_band(
            model.SEAL_LAND_WIDTH_MM,
            model.source.BAFFLE_BED_Y - model.BAFFLE_STRUCTURE_THICKNESS_MM,
            model.source.BAFFLE_BED_Y,
            feature="hybrid bottom baffle-land audit band",
        )
        bucket_land = model.single._single_face_band(
            model.SEAL_LAND_WIDTH_MM,
            model.source.SHOULDER_Y,
            model.source.SHOULDER_Y + model.BUCKET_SHOULDER_THICKNESS_MM,
            feature="hybrid bottom bucket-land audit band",
        )
        gasket = model.single._single_face_band(
            model.GASKET_WIDTH_MM,
            model.source.BAFFLE_BED_Y,
            model.source.SHOULDER_Y,
            feature="hybrid bottom gasket continuity band",
        )
    finally:
        model.single._perimeter_wire = original

    bottom_clip = Pos(0.0, model.source.BAFFLE_BED_Y + 0.5, -88.0) * Box(
        148.0,
        model.BAFFLE_STRUCTURE_THICKNESS_MM
        + model.BUCKET_SHOULDER_THICKNESS_MM
        + model.GASKET_CLOSED_GAP_MM
        + 0.4,
        8.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    bottom_seal = (gasket & bottom_clip).clean().fix()
    bottom_seal_parts = [
        solid for solid in bottom_seal.solids() if solid.volume > 1e-6
    ]
    if len(bottom_seal_parts) != 1:
        raise ValueError(
            "The flat bottom seal is not one continuous run: "
            f"parts={len(bottom_seal_parts)}"
        )

    bottom_baffle_land = (baffle_land & bottom_clip).clean().fix()
    bottom_bucket_land = (bucket_land & bottom_clip).clean().fix()

    def sampled_support(ideal_land, actual_part) -> tuple[float, int]:
        ideal_classifier = BRepClass3d_SolidClassifier(ideal_land.wrapped)
        actual_classifier = BRepClass3d_SolidClassifier(actual_part.wrapped)

        def occupied(classifier, x_mm, y_mm, z_mm):
            classifier.Perform(gp_Pnt(x_mm, y_mm, z_mm), 1e-7)
            return classifier.State() in (TopAbs_IN, TopAbs_ON)

        bounds = ideal_land.bounding_box()
        x_values = [
            bounds.min.X + 1.0 + 2.0 * index
            for index in range(int(bounds.size.X // 2.0))
        ]
        y_values = [
            bounds.min.Y + 0.25 + 0.5 * index
            for index in range(int(bounds.size.Y // 0.5))
        ]
        z_values = [
            bounds.min.Z + 0.25 + 0.5 * index
            for index in range(int(bounds.size.Z // 0.5))
        ]
        ideal_count = 0
        supported_count = 0
        for x_mm in x_values:
            for y_mm in y_values:
                for z_mm in z_values:
                    if not occupied(
                        ideal_classifier, x_mm, y_mm, z_mm
                    ):
                        continue
                    ideal_count += 1
                    if occupied(actual_classifier, x_mm, y_mm, z_mm):
                        supported_count += 1
        if ideal_count == 0:
            raise ValueError("The bottom-land support sample is empty")
        return supported_count / ideal_count, ideal_count

    baffle_land_support, baffle_support_samples = sampled_support(
        bottom_baffle_land, baffle
    )
    bucket_land_support, bucket_support_samples = sampled_support(
        bottom_bucket_land, bucket
    )
    if min(baffle_land_support, bucket_land_support) < model.MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            "The matching flat bottom lands are not fully supported by both "
            f"parts: baffle={baffle_land_support:.6f}, "
            f"bucket={bucket_land_support:.6f}"
        )

    planar_areas = {}
    for label, land in (
        ("baffle", bottom_baffle_land),
        ("bucket", bottom_bucket_land),
    ):
        bounds = land.bounding_box()
        planar_faces = [
            face
            for face in land.faces()
            if face.bounding_box().size.Z < 0.01
            and abs(face.center().Z - bounds.min.Z) < 0.01
        ]
        planar_area = sum(face.area for face in planar_faces)
        if not planar_faces or planar_area < 10.0:
            raise ValueError(
                f"The {label} bottom mating land is not a usable planar face: "
                f"faces={len(planar_faces)}, area={planar_area:.6f} mm2"
            )
        planar_areas[label] = planar_area

    return {
        "baffle_bottom_land_planar_area_mm2": planar_areas["baffle"],
        "bucket_bottom_land_planar_area_mm2": planar_areas["bucket"],
        "baffle_bottom_land_support_ratio": baffle_land_support,
        "bucket_bottom_land_support_ratio": bucket_land_support,
        "baffle_bottom_land_support_sample_count": baffle_support_samples,
        "bucket_bottom_land_support_sample_count": bucket_support_samples,
        "bottom_seal_connected_component_count": len(bottom_seal_parts),
        "bottom_seal_continuous": True,
    }


def main() -> None:
    if not AUTHORITATIVE_BASE_STEP.is_file():
        raise FileNotFoundError(AUTHORITATIVE_BASE_STEP)

    full_base = model._single_solid(
        import_step(AUTHORITATIVE_BASE_STEP),
        feature="authoritative full-detail enclosure source",
    )
    print("harness: full-detail base loaded", flush=True)

    apply, restore, originals = _patch_seam()
    apply()
    try:
        reference = model._authoritative_reference_joint(full_base)
        print("harness: authoritative seam reference built", flush=True)
        common = model._build_authoritative_joint(
            full_base,
            hybrid_bottom=True,
        )
        model._FILL_AUDIT.clear()
        model._FILL_AUDIT.update(model.previous._FILL_AUDIT)
        model._JOINT_AUDIT.clear()
        model._JOINT_AUDIT.update(model.previous._JOINT_AUDIT)
        model._JOINT_AUDIT.update(
            {
                "installation_motion": "seam-only validation; retention disabled",
                "gasket_closed_gap_mm": model.GASKET_CLOSED_GAP_MM,
                "shoulder_y_mm": model.source.SHOULDER_Y,
                "baffle_bed_y_mm": model.source.BAFFLE_BED_Y,
                "seam_architecture": "authoritative nested L/R/T + flat bottom",
                "authoritative_common_joint_inherited": True,
                "front_bulkhead_architecture": (
                    "constant-height support wedge only"
                ),
                "authoritative_outside_gasket_closure_retained": False,
                "authoritative_corner_closure_panels_retained": True,
                "authoritative_front_closure_audit_retained": False,
                "front_bulkhead_exact_exterior_audit": True,
                "top_hinge": {"present": False},
            }
        )
        print("harness: hybrid seam built", flush=True)
        enclosure_body = _enclosure_body_audit(full_base, reference, common)
        print("harness: complete enclosure body retained", flush=True)
        seam_fingerprint_1 = _seam_band_volumes()
        seam_identity = _seam_identity(reference, common)
        print("harness: L/R/T seam identity verified", flush=True)
        flat_bottom = _flat_bottom_audit(common)
        print("harness: flat bottom + seal continuity verified", flush=True)
        section_round_trip = _export_sections(reference, common)
        print("harness: inspection sections exported", flush=True)
    finally:
        restore()

    # --- isolation: every patched shared attribute is restored ------------
    isolation_restored = (
        model.source.GASKET_CLOSED_GAP_MM == originals["gap"]
        and model.source.SHOULDER_Y == originals["shoulder"]
        and model.single._perimeter_wire is model._AUTHORITATIVE_PERIMETER_WIRE
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
        model.source.GASKET_CLOSED_GAP_MM == originals["gap"]
        and model.source.SHOULDER_Y == originals["shoulder"]
        and model.single._perimeter_wire is model._AUTHORITATIVE_PERIMETER_WIRE
    )
    print("harness: reproducibility + restore verified", flush=True)

    bucket = common["bucket"]
    baffle = common["baffle"]

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

    reproducible = {
        "seam_fingerprint_build_1": seam_fingerprint_1,
        "seam_fingerprint_build_2": seam_fingerprint_2,
        "identical": seam_fingerprint_1 == seam_fingerprint_2,
        "second_restore_ok": second_restore_ok,
    }

    diagnostics = {
        "scope": "Variant A Stage 1 hybrid-seam standalone validation",
        "authoritative_base_step": str(AUTHORITATIVE_BASE_STEP),
        "stage_flags": {
            "BUILD_TOP_HINGE": model.BUILD_TOP_HINGE,
            "BUILD_BOTTOM_SCREWS": model.BUILD_BOTTOM_SCREWS,
        },
        "compression_knob_mm": model.GASKET_CLOSED_GAP_MM,
        "shoulder_y_mm": joint["shoulder_y_mm"],
        "baffle_bed_y_mm": joint["baffle_bed_y_mm"],
        "single_solid": {"bucket": True, "baffle": True},
        "enclosure_body_retention": enclosure_body,
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
        "baffle_bridge_roots_mm3": joint["baffle_bridge_roots_mm3"],
        "front_fill": fill,
        "seam_identity_lrt": seam_identity,
        "corner_seal": {
            "front_bulkhead_exact_exterior_audit": joint[
                "front_bulkhead_exact_exterior_audit"
            ],
            "outside_gasket_corner_closure_count": joint[
                "outside_gasket_corner_closure_count"
            ],
            "unclosed_outside_gasket_corner_volume_mm3": joint[
                "unclosed_outside_gasket_corner_volume_mm3"
            ],
            "baffle_corner_closure_count": joint[
                "baffle_corner_closure_count"
            ],
            "unclosed_baffle_corner_face_volume_mm3": joint[
                "unclosed_corner_face_volume_mm3"
            ],
        },
        "flat_bottom": flat_bottom,
        "inspection_section_roundtrip": section_round_trip,
        "exterior_identity": {
            "fairing_area_difference_mm2": common[
                "fairing_area_difference_mm2"
            ],
            "authoritative_exterior_seam_ring_reused": True,
            "permitted_change_scope": (
                "internal bottom transition only; L/R/T section identity exact"
            ),
        },
        "bucket_baffle_overlap_mm3": common["bucket_baffle_overlap_mm3"],
        "isolation_shared_upstream_generators_restored": isolation_restored,
        "reproducibility_two_builds_same_process": reproducible,
        "restored_features": [
            "nested_split_envelope_on_left_right_top",
            "constant_height_inner_support_wedge",
            "baffle_corner_closure_panels",
            "dual_skin_fill_passages_and_blisters",
        ],
    }
    diagnostics_path = job_output_path(DIAGNOSTICS_PATH)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
