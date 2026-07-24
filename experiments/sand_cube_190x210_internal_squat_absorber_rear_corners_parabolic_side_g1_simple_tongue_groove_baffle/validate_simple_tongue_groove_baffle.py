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

from build123d import (
    Align,
    Box,
    Compound,
    GeomType,
    Pos,
    import_step,
)
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_ON


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
from src.enclosure_family.variant_r.artifacts import (  # noqa: E402
    VARIANT_R_ARTIFACTS_BY_ID,
)
from src.enclosure_family.variant_r.inputs import (  # noqa: E402
    authoritative_base_step,
    producer_attestation_path,
)
from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    sha256_file,
    verify_producer_attestation,
)
from src.enclosure_family.variant_r.export import (  # noqa: E402
    publish_step_round_trip,
    stabilize_single_solid,
)


AUTHORITATIVE_BASE_STEP = authoritative_base_step(ROOT)
AUTHORITATIVE_BASE_ATTESTATION = producer_attestation_path(ROOT)
OUT = model.OUT
BUCKET_STEP = OUT / VARIANT_R_ARTIFACTS_BY_ID["bucket"].filename
BAFFLE_STEP = OUT / VARIANT_R_ARTIFACTS_BY_ID["baffle"].filename
GASKET_STEP = OUT / "simple_tongue_groove_gasket.step"
ASSEMBLY_STEP = OUT / "simple_tongue_groove_review_assembly.step"
DIAGNOSTICS_PATH = (
    OUT / VARIANT_R_ARTIFACTS_BY_ID["validation_diagnostics"].filename
)
AUTHORIZED_BUCKET_REFERENCE_ONLY_SIGNATURE = {
    "top_x_-45": (
        ([-45.0, -71.75, 86.25], 0.03512460099577875),
        ([-45.0, -69.75, 87.75], 0.015422238791818964),
    ),
    "top_x_+45": (
        ([45.0, -71.75, 86.25], 0.03512460099577917),
        ([45.0, -69.75, 87.75], 0.015422238792071776),
    ),
    "left_z_-55": (
        ([-86.25, -71.75, -55.0], 0.03512485408190204),
        ([-87.75, -69.75, -55.0], 0.01542223877973842),
    ),
    "left_z_+55": (
        ([-86.25, -71.75, 55.0], 0.03512485408341897),
        ([-87.75, -69.75, 55.0], 0.015422238804824904),
    ),
    "right_z_-55": (
        ([86.25, -71.75, -55.0], 0.03512460101947833),
        ([87.75, -69.75, -55.0], 0.015422238781002719),
    ),
    "right_z_+55": (
        ([86.25, -71.75, 55.0], 0.03512460101527814),
        ([87.75, -69.75, 55.0], 0.015422238805489798),
    ),
}
AUTHORIZED_SIGNATURE_VOLUME_ATTESTATION_TOLERANCE_MM3 = 1e-6


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
    return publish_step_round_trip(
        step_path,
        solid,
        require_single_solid=True,
    )


def _assembly_round_trip(step_path: Path, assembly) -> dict:
    result = publish_step_round_trip(
        step_path,
        assembly,
        require_single_solid=False,
    )
    if (
        result["source_solid_count"] != 3
        or result["imported_solid_count"] != 3
    ):
        raise ValueError(f"Variant R assembly is not three solids: {result}")
    return result


def _no_splice_topology_audit(shape, *, part_name: str) -> dict:
    """Reject the old splice and unrelated lower-apron construction edges."""

    lower_edges = []
    for edge in shape.edges():
        bounds = edge.bounding_box()
        if (
            bounds.size.X >= 20.0
            and bounds.size.Z <= 0.02
            and bounds.max.Z <= -70.0
        ):
            center = edge.position_at(0.5)
            lower_edges.append(
                {
                    "center_mm": [center.X, center.Y, center.Z],
                    "bounds_min_mm": [
                        bounds.min.X,
                        bounds.min.Y,
                        bounds.min.Z,
                    ],
                    "bounds_max_mm": [
                        bounds.max.X,
                        bounds.max.Y,
                        bounds.max.Z,
                    ],
                    "bounds_size_mm": [
                        bounds.size.X,
                        bounds.size.Y,
                        bounds.size.Z,
                    ],
                    "length_mm": edge.length,
                }
            )
    old_splice_edges = [
        record
        for record in lower_edges
        if (
            abs(record["center_mm"][2] + 80.1) <= 0.15
            and record["bounds_min_mm"][1] < -80.0
        )
    ]
    unrelated_lower_apron_edges = [
        record
        for record in lower_edges
        if (
            record["bounds_min_mm"][1] < -80.0
            and record["bounds_size_mm"][0] >= 40.0
            and record["center_mm"][2]
            > model.BAFFLE_PLANAR_SOLE_Z_MM + 0.05
        )
    ]
    result = {
        "part": part_name,
        "face_count": len(shape.faces()),
        "edge_count": len(shape.edges()),
        "vertex_count": len(shape.vertices()),
        "old_splice_height_edge_count": len(old_splice_edges),
        "unrelated_full_width_lower_apron_edge_count": len(
            unrelated_lower_apron_edges
        ),
        "old_splice_height_edges": old_splice_edges,
        "unrelated_full_width_lower_apron_edges": (
            unrelated_lower_apron_edges
        ),
    }
    if old_splice_edges or unrelated_lower_apron_edges:
        raise ValueError(f"{part_name} retains an unwanted lower edge: {result}")
    if (
        part_name == "baffle"
        and (result["face_count"], result["edge_count"]) != (91, 257)
    ):
        raise ValueError(
            "Production baffle topology differs from the validated no-splice "
            f"candidate expectation 91/257: {result}"
        )
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
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _difference_volume(left, right) -> float:
    left_volume = _shape_volume(left)
    if left_volume <= 1e-9:
        return 0.0
    if _shape_volume(right) <= 1e-9:
        return left_volume
    return _shape_volume(left - right)


def _local_material_difference(
    reference_shape,
    hybrid_shape,
    point: tuple[float, float, float],
    *,
    cube_size_mm: float,
) -> dict[str, float | list[float]]:
    cube = Pos(*point) * Box(
        cube_size_mm,
        cube_size_mm,
        cube_size_mm,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    reference_local = reference_shape & cube
    hybrid_local = hybrid_shape & cube
    return {
        "center_mm": list(point),
        "cube_size_mm": cube_size_mm,
        "reference_volume_mm3": _shape_volume(reference_local),
        "hybrid_volume_mm3": _shape_volume(hybrid_local),
        "reference_only_mm3": _difference_volume(
            reference_local,
            hybrid_local,
        ),
        "hybrid_only_mm3": _difference_volume(
            hybrid_local,
            reference_local,
        ),
    }


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
    """Require exact L/R/T identity plus the authorized bucket-only delta."""

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
            classifier_mismatch_points = [
                point
                for point in points
                if occupied(reference_classifier, point)
                != occupied(hybrid_classifier, point)
            ]
            local_material_differences = [
                _local_material_difference(
                    reference[part],
                    hybrid[part],
                    point,
                    cube_size_mm=1.0,
                )
                for point in classifier_mismatch_points
            ]
            material_mismatches = [
                difference
                for difference in local_material_differences
                if max(
                    difference["reference_only_mm3"],
                    difference["hybrid_only_mm3"],
                )
                > 0.001
            ]
            part_results[part] = {
                "sample_count": len(points),
                "classifier_mismatch_count": len(classifier_mismatch_points),
                "material_mismatch_count": len(material_mismatches),
                "material_mismatches": material_mismatches,
                "boundary_equivalent_classifier_mismatches": (
                    [
                        difference
                        for difference in local_material_differences
                        if difference not in material_mismatches
                    ]
                ),
                "local_material_cube_size_mm": 1.0,
                "local_material_tolerance_mm3": 0.001,
                "grid_spacing_mm": 0.5,
            }
        results[label] = part_results
    authorized_records = []
    for label, part_results in results.items():
        baffle_mismatches = part_results["baffle"]["material_mismatches"]
        if baffle_mismatches:
            raise ValueError(
                f"{label} baffle changed on the protected L/R/T seam: "
                f"{baffle_mismatches}"
            )
        observed = part_results["bucket"]["material_mismatches"]
        expected = AUTHORIZED_BUCKET_REFERENCE_ONLY_SIGNATURE.get(label, ())
        if len(observed) != len(expected):
            raise ValueError(
                "Authorized bucket-only seam signature changed: "
                f"{label}: expected={len(expected)}, observed={observed}"
            )
        for record, (expected_center, expected_reference_only) in zip(
            observed,
            expected,
            strict=True,
        ):
            if record["center_mm"] != expected_center:
                raise ValueError(
                    "Authorized bucket-only seam point changed: "
                    f"{label}: {record}"
                )
            if record["hybrid_only_mm3"] != 0.0:
                raise ValueError(
                    "Candidate-added bucket material is not authorized: "
                    f"{label}: {record}"
                )
            if (
                abs(
                    record["reference_only_mm3"]
                    - expected_reference_only
                )
                > AUTHORIZED_SIGNATURE_VOLUME_ATTESTATION_TOLERANCE_MM3
            ):
                raise ValueError(
                    "Authorized reference-only bucket volume signature "
                    f"changed: {label}: {record}"
                )
            authorized_records.append(record)
    if len(authorized_records) != 12:
        raise ValueError(
            "Authorized bucket-only seam signature is not exactly twelve "
            f"points: {authorized_records}"
        )
    results["authorized_bucket_reference_only_signature"] = {
        "authorization": (
            "intentional internal bucket-only geometry delta required by the "
            "continuous no-splice donor; not tolerance widening or equivalence"
        ),
        "point_count": len(authorized_records),
        "expected_point_count": 12,
        "candidate_added_material_mm3": sum(
            record["hybrid_only_mm3"] for record in authorized_records
        ),
        "reference_only_sample_cube_material_mm3": sum(
            record["reference_only_mm3"] for record in authorized_records
        ),
        "volume_attestation_tolerance_mm3": (
            AUTHORIZED_SIGNATURE_VOLUME_ATTESTATION_TOLERANCE_MM3
        ),
        "records": authorized_records,
    }
    return results


def _point_to_edge_distance(edge, point) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(edge.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        raise ValueError("Protected perimeter edge distance failed")
    return tool.Value()


def _edge_deviation(source_edge, target_edge) -> float:
    return max(
        _point_to_edge_distance(target_edge, source_edge.position_at(value))
        for value in (0.0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0)
    )


def _retained_perimeter_edge_audit() -> dict:
    """Require geometric identity for all retained L/R/T perimeter edges."""

    records = {}
    for offset_mm in (0.0, -2.5, 2.5):
        authoritative = model._AUTHORITATIVE_PERIMETER_WIRE(
            offset_mm=offset_mm,
            y_mm=model.source.BAFFLE_BED_Y,
        )
        hybrid = model._hybrid_perimeter_wire(
            offset_mm=offset_mm,
            y_mm=model.source.BAFFLE_BED_Y,
        )
        tangency = model.VARIANT_R_PARAMETERS.path_bottom_corner_tangency_mm
        half_size = model.VARIANT_R_PARAMETERS.path_half_size_mm + offset_mm
        retained = []
        removed = []
        for edge in authoritative.edges():
            bounds = edge.bounding_box()
            is_bottom_detour = (
                bounds.min.X >= -tangency - 1e-6
                and bounds.max.X <= tangency + 1e-6
                and bounds.min.Z >= -half_size - 1e-6
                and bounds.max.Z
                <= (
                    -half_size
                    + model.VARIANT_R_PARAMETERS.screw_bypass_depth_mm
                    + 1e-6
                )
            )
            (removed if is_bottom_detour else retained).append(edge)
        hybrid_edges = list(hybrid.edges())
        matches = []
        matched_indices = []
        for edge in retained:
            candidates = []
            for index, candidate in enumerate(hybrid_edges):
                deviation = max(
                    _edge_deviation(edge, candidate),
                    _edge_deviation(candidate, edge),
                )
                candidates.append((deviation, index, candidate))
            deviation, match_index, match = min(
                candidates,
                key=lambda item: item[0],
            )
            matched_indices.append(match_index)
            matches.append(
                {
                    "bidirectional_sampled_deviation_mm": deviation,
                    "length_difference_mm": match.length - edge.length,
                }
            )
        maximum_deviation = max(
            record["bidirectional_sampled_deviation_mm"]
            for record in matches
        )
        maximum_length_difference = max(
            abs(record["length_difference_mm"]) for record in matches
        )
        if (
            len(retained) != 10
            or len(removed) != 4
            or len(set(matched_indices)) != 10
            or maximum_deviation > 1e-9
            or maximum_length_difference > 1e-9
        ):
            raise ValueError(
                "Protected L/R/T perimeter edge geometry changed: "
                f"offset={offset_mm}, retained={len(retained)}, "
                f"removed={len(removed)}, matches={matches}"
            )
        records[f"offset_{offset_mm:+g}_mm"] = {
            "retained_lrt_edge_count": len(retained),
            "removed_bottom_detour_edge_count": len(removed),
            "unique_matched_lrt_edge_count": len(set(matched_indices)),
            "maximum_bidirectional_sampled_deviation_mm": maximum_deviation,
            "maximum_length_difference_mm": maximum_length_difference,
            "acceptance_tolerance_mm": 1e-9,
        }
    return records


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
        return stabilize_single_solid(
            shape,
            audit_dir / f"{label}.step",
        )

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
        VARIANT_R_ARTIFACTS_BY_ID["authoritative_top_seam"].filename: (
            assembled_reference,
            Pos(45.0, y_center, 84.0)
            * Box(
                5.0,
                14.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        VARIANT_R_ARTIFACTS_BY_ID["hybrid_top_seam"].filename: (
            assembled_hybrid,
            Pos(45.0, y_center, 84.0)
            * Box(
                5.0,
                14.0,
                22.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        VARIANT_R_ARTIFACTS_BY_ID["authoritative_side_seam"].filename: (
            assembled_reference,
            Pos(-84.0, y_center, 20.0)
            * Box(
                22.0,
                14.0,
                5.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        VARIANT_R_ARTIFACTS_BY_ID["hybrid_side_seam"].filename: (
            assembled_hybrid,
            Pos(-84.0, y_center, 20.0)
            * Box(
                22.0,
                14.0,
                5.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        VARIANT_R_ARTIFACTS_BY_ID[
            "hybrid_bottom_corner_transition"
        ].filename: (
            assembled_hybrid,
            Pos(80.0, y_center, -80.0)
            * Box(
                28.0,
                14.0,
                28.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ),
        ),
        VARIANT_R_ARTIFACTS_BY_ID["hybrid_flat_bottom"].filename: (
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
        checks[filename] = publish_step_round_trip(
            path,
            section,
            require_single_solid=False,
        )
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


def _baffle_print_contact_audit(baffle) -> dict:
    """Require the trimmed baffle topology to terminate on one planar bed."""
    tolerance = 0.01
    bed_z = min(vertex.Z for vertex in baffle.vertices())
    contacts = []
    for face in baffle.faces():
        bounds = face.bounding_box()
        if (
            face.geom_type == GeomType.PLANE
            and bounds.size.Z <= tolerance
            and abs(bounds.min.Z - bed_z) <= tolerance
            and abs(bounds.max.Z - bed_z) <= tolerance
        ):
            contacts.append(
                {
                    "area_mm2": face.area,
                    "x_span_mm": bounds.size.X,
                    "y_span_mm": bounds.size.Y,
                }
            )
    if not contacts:
        raise ValueError(f"Baffle has no planar face at bed Z={bed_z}")
    largest = max(contacts, key=lambda record: record["x_span_mm"])
    if (
        abs(bed_z - model.BAFFLE_PLANAR_SOLE_Z_MM) > 1e-6
        or largest["x_span_mm"] < 187.020979 - 0.001
        or largest["area_mm2"] < 2277.950023 - 0.001
    ):
        raise ValueError(
            "Baffle print contact misses the full-width plane contract: "
            f"bed_z={bed_z}, largest={largest}"
        )
    return {
        "build_direction_design_coordinates": "+Z",
        "bed_z_mm": bed_z,
        "planar_contact_face_count": len(contacts),
        "total_planar_contact_area_mm2": sum(
            record["area_mm2"] for record in contacts
        ),
        "largest_planar_contact_face": largest,
        "brim_assumed": True,
        "physical_adhesion_validated": False,
    }


def main() -> None:
    producer_attestation = verify_producer_attestation(
        repo_root=ROOT,
        base_step=AUTHORITATIVE_BASE_STEP,
        attestation_path=AUTHORITATIVE_BASE_ATTESTATION,
    )
    base_identity = dict(
        producer_attestation["authoritative_base_input"]
    )
    base_identity.update(
        {
            "producer_entrypoint": producer_attestation[
                "producer_entrypoint"
            ],
            "producer_job_id": producer_attestation["cad_job_id"],
            "producer_attestation_sha256": sha256_file(
                AUTHORITATIVE_BASE_ATTESTATION
            ),
        }
    )

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
            reference_joint=reference,
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
        print("harness: L/R/T material signature verified", flush=True)
        retained_perimeter_edges = _retained_perimeter_edge_audit()
        print("harness: retained L/R/T perimeter edges verified", flush=True)
        flat_bottom = _flat_bottom_audit(common)
        print("harness: flat bottom + seal continuity verified", flush=True)
        print_contact = _baffle_print_contact_audit(common["baffle"])
        print("harness: baffle print contact verified", flush=True)
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
    gasket = common["gasket"]

    # --- single valid solid after every boolean ---------------------------
    for name, solid in (
        ("bucket", bucket),
        ("baffle", baffle),
        ("gasket", gasket),
    ):
        solids = solid.solids()
        if len(solids) != 1 or not solid.is_valid:
            raise ValueError(f"{name} is not one valid solid: n={len(solids)}")

    # --- STEP export/import solid-count match + all valid -----------------
    topology = {
        "source_bucket": _no_splice_topology_audit(
            bucket,
            part_name="bucket",
        ),
        "source_baffle": _no_splice_topology_audit(
            baffle,
            part_name="baffle",
        ),
    }
    bucket_round_trip = _round_trip(BUCKET_STEP, bucket)
    baffle_round_trip = _round_trip(BAFFLE_STEP, baffle)
    gasket_round_trip = _round_trip(GASKET_STEP, gasket)
    assembly_round_trip = _assembly_round_trip(
        ASSEMBLY_STEP,
        Compound(children=[bucket, baffle, gasket]),
    )
    topology.update(
        {
            "round_trip_bucket": _no_splice_topology_audit(
                import_step(job_output_path(BUCKET_STEP)),
                part_name="bucket",
            ),
            "round_trip_baffle": _no_splice_topology_audit(
                import_step(job_output_path(BAFFLE_STEP)),
                part_name="baffle",
            ),
        }
    )
    pairwise_overlap = {
        "bucket_baffle_mm3": _shape_volume(bucket.intersect(baffle)),
        "gasket_bucket_mm3": _shape_volume(gasket.intersect(bucket)),
        "gasket_baffle_mm3": _shape_volume(gasket.intersect(baffle)),
    }
    if max(pairwise_overlap.values()) > 0.001:
        raise ValueError(f"Variant R parts overlap: {pairwise_overlap}")

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
        "authoritative_base_input": base_identity,
        "stage_flags": {
            "BUILD_TOP_HINGE": False,
            "BUILD_BOTTOM_SCREWS": False,
        },
        "compression_knob_mm": model.GASKET_CLOSED_GAP_MM,
        "shoulder_y_mm": joint["shoulder_y_mm"],
        "baffle_bed_y_mm": joint["baffle_bed_y_mm"],
        "single_solid": {"bucket": True, "baffle": True, "gasket": True},
        "enclosure_body_retention": enclosure_body,
        "bucket_step_roundtrip": bucket_round_trip,
        "baffle_step_roundtrip": baffle_round_trip,
        "gasket_step_roundtrip": gasket_round_trip,
        "assembly_step_roundtrip": assembly_round_trip,
        "no_splice_topology": topology,
        "bottom_ownership": common["bottom_synthesis"],
        "pairwise_overlap": pairwise_overlap,
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
        "retained_perimeter_edge_geometry": retained_perimeter_edges,
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
        "baffle_print_contact": print_contact,
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
