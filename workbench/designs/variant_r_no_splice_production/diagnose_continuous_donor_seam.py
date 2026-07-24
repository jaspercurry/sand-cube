"""Diagnose L/R/T seam differences between reference and continuous donor."""

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

from build123d import import_step
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN, TopAbs_ON
from OCP.gp import gp_Pnt

from src.enclosure_family.legacy_runtime import (
    LegacyAttributeBinding,
    bind_legacy_attributes,
)
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

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
import validate_simple_tongue_groove_baffle as validator  # noqa: E402


CANDIDATE = ROOT / "build/workbench/variant_r_no_splice_production/candidate"
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_no_splice_production/"
    "continuous-donor-seam-diagnostic.json"
)


def _samples(start: float, stop: float, step: float = 0.5) -> list[float]:
    count = int(round((stop - start) / step))
    return [start + (index + 0.5) * step for index in range(count)]


def _seam_material_records(
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    classifiers = {
        (variant, part): BRepClass3d_SolidClassifier(data[part].wrapped)
        for variant, data in (("reference", reference), ("candidate", candidate))
        for part in ("bucket", "baffle")
    }

    def occupied(classifier, point: tuple[float, float, float]) -> bool:
        classifier.Perform(gp_Pnt(*point), 1e-7)
        return classifier.State() in (TopAbs_IN, TopAbs_ON)

    y_values = _samples(-80.0, -68.0)
    top_z_values = _samples(72.0, 98.0)
    side_x_abs_values = _samples(72.0, 98.0)
    sections: dict[str, list[tuple[float, float, float]]] = {}
    for x_mm in (-45.0, 0.0, 45.0):
        sections[f"top_x_{x_mm:+g}"] = [
            (x_mm, y_mm, z_mm)
            for y_mm in y_values
            for z_mm in top_z_values
        ]
    for sign, label in ((-1.0, "left"), (1.0, "right")):
        for z_mm in (-55.0, 0.0, 55.0):
            sections[f"{label}_z_{z_mm:+g}"] = [
                (sign * x_abs_mm, y_mm, z_mm)
                for y_mm in y_values
                for x_abs_mm in side_x_abs_values
            ]

    results = {}
    for label, points in sections.items():
        results[label] = {}
        for part in ("bucket", "baffle"):
            mismatches = []
            for point in points:
                if occupied(classifiers[("reference", part)], point) == occupied(
                    classifiers[("candidate", part)],
                    point,
                ):
                    continue
                difference = validator._local_material_difference(
                    reference[part],
                    candidate[part],
                    point,
                    cube_size_mm=1.0,
                )
                if max(
                    difference["reference_only_mm3"],
                    difference["hybrid_only_mm3"],
                ) > 0.001:
                    mismatches.append(difference)
            results[label][part] = {
                "sample_count": len(points),
                "material_mismatch_count": len(mismatches),
                "material_mismatches": mismatches,
            }
    return results


def _retained_edge_identity() -> dict[str, Any]:
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
        identity_count = sum(
            1
            for edge in retained
            if any(
                edge.wrapped.IsSame(candidate.wrapped)
                for candidate in hybrid.edges()
            )
        )
        records[f"offset_{offset_mm:+g}_mm"] = {
            "authoritative_edge_count": len(authoritative.edges()),
            "removed_bottom_edge_count": len(removed),
            "retained_lrt_edge_count": len(retained),
            "retained_lrt_edges_same_topology_identity_count": identity_count,
            "hybrid_edge_count": len(hybrid.edges()),
        }
    return records


def main() -> None:
    full_base = model._single_solid(
        import_step(authoritative_base_step(ROOT)),
        feature="attested production Variant R base",
    )
    candidate = {
        "bucket": import_step(
            CANDIDATE / "production_candidate_bucket.step"
        ),
        "baffle": import_step(
            CANDIDATE / "production_candidate_baffle.step"
        ),
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
        edge_identity = _retained_edge_identity()
    result = {
        "scope": (
            "focused authoritative-reference versus exported continuous-donor "
            "L/R/T seam diagnostic"
        ),
        "retained_perimeter_edge_identity": edge_identity,
        "seam_material_samples": _seam_material_records(
            reference,
            candidate,
        ),
        "candidate_support_ratios": {
            "bucket": 1.0,
            "baffle": 1.0,
        },
        "acceptance_boundary": (
            "Do not widen tolerances. Determine whether any nonzero local "
            "material records are limited to a source-explained donor boundary "
            "while all ten retained L/R/T perimeter edges remain identical."
        ),
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
