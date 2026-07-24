"""Locate boundaries introduced by the localized bucket restoration experiment."""

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

from build123d import Compound, import_step
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Pnt

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
WORKBENCH = Path(__file__).resolve().parent
for module_root in (EXPERIMENT, WORKBENCH):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
import validate_simple_tongue_groove_baffle as validator  # noqa: E402
import check_bucket_material_restoration as feasibility  # noqa: E402


CANDIDATE = ROOT / "build/workbench/variant_r_no_splice_production/candidate"
RESTORED = ROOT / "build/workbench/variant_r_no_splice_production/restoration"
OUTPUT = RESTORED / "boundary-diagnostic.json"
MATCH_TOLERANCE_MM = 1e-7


def _point_to_edge_distance(edge: Any, point: Any) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(edge.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        raise ValueError("Point-to-edge distance failed")
    return tool.Value()


def _distance_to_edge_set(edge: Any, targets: list[Any]) -> float:
    return max(
        min(_point_to_edge_distance(target, edge.position_at(value))
            for target in targets)
        for value in (0.0, 0.25, 0.5, 0.75, 1.0)
    )


def _edge_record(edge: Any, *, candidate_edges: list[Any]) -> dict[str, Any]:
    bounds = edge.bounding_box()
    center = edge.position_at(0.5)
    candidate_deviation = _distance_to_edge_set(edge, candidate_edges)
    return {
        "center_mm": [center.X, center.Y, center.Z],
        "bounds_min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "bounds_max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "bounds_size_mm": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        "length_mm": edge.length,
        "candidate_edge_sampled_deviation_mm": candidate_deviation,
        "matches_candidate_edge_geometry": (
            candidate_deviation <= MATCH_TOLERANCE_MM
        ),
        "at_local_patch_floor_z_minus_70": (
            abs(bounds.min.Z + 70.0) <= 1e-6
            and abs(bounds.max.Z + 70.0) <= 1e-6
        ),
        "at_patch_front_y_minus_76": (
            abs(bounds.min.Y + 76.0) <= 1e-6
            and abs(bounds.max.Y + 76.0) <= 1e-6
        ),
        "reaches_visible_front_apron_y": bounds.min.Y < -80.0,
        "whole_width_x_span": bounds.size.X >= 40.0,
        "whole_height_z_span": bounds.size.Z >= 40.0,
        "outer_side_region": max(abs(center.X), abs(bounds.min.X),
                                 abs(bounds.max.X)) >= 86.0,
    }


def _shape_volume(shape: Any) -> float:
    return sum(solid.volume for solid in shape.solids())


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
    patches = feasibility._reference_ownership_patches(reference["bucket"])
    restored_solids = list(candidate["bucket"].fuse(*patches).solids())
    if len(restored_solids) != 1 or not restored_solids[0].is_valid:
        raise ValueError("Localized patch restoration is not one valid solid")
    restored = restored_solids[0]

    candidate_edges = list(candidate["bucket"].edges())
    edge_records = [
        _edge_record(edge, candidate_edges=candidate_edges)
        for edge in restored.edges()
    ]
    unmatched = [
        record
        for record in edge_records
        if not record["matches_candidate_edge_geometry"]
    ]
    topology = validator._no_splice_topology_audit(
        restored,
        part_name="bucket",
    )
    assembly = Compound(
        children=[
            restored,
            candidate["baffle"],
            candidate["gasket"],
        ]
    )
    result = {
        "scope": (
            "experimental localized ownership union boundary location; not a "
            "production acceptance"
        ),
        "match_tolerance_mm": MATCH_TOLERANCE_MM,
        "topology": topology,
        "candidate_topology": {
            "faces": len(candidate["bucket"].faces()),
            "edges": len(candidate_edges),
            "vertices": len(candidate["bucket"].vertices()),
        },
        "restored_topology": {
            "faces": len(restored.faces()),
            "edges": len(restored.edges()),
            "vertices": len(restored.vertices()),
        },
        "restored_edges_matching_candidate_geometry": (
            len(edge_records) - len(unmatched)
        ),
        "new_boundary_curve_count": len(unmatched),
        "new_boundary_curves": unmatched,
        "new_curve_classification": {
            "reaches_visible_front_apron_count": sum(
                record["reaches_visible_front_apron_y"]
                for record in unmatched
            ),
            "whole_width_count": sum(
                record["whole_width_x_span"] for record in unmatched
            ),
            "whole_height_count": sum(
                record["whole_height_z_span"] for record in unmatched
            ),
            "outer_side_region_count": sum(
                record["outer_side_region"] for record in unmatched
            ),
            "local_patch_floor_count": sum(
                record["at_local_patch_floor_z_minus_70"]
                for record in unmatched
            ),
            "patch_front_count": sum(
                record["at_patch_front_y_minus_76"] for record in unmatched
            ),
        },
        "overlap": {
            "bucket_baffle_mm3": _shape_volume(
                restored & candidate["baffle"]
            ),
            "bucket_gasket_mm3": _shape_volume(
                restored & candidate["gasket"]
            ),
        },
        "round_trip": {
            "bucket": publish_step_round_trip(
                RESTORED / "experimental_restored_bucket.step",
                restored,
                require_single_solid=True,
            ),
            "assembly": publish_step_round_trip(
                RESTORED / "experimental_restored_assembly.step",
                assembly,
                require_single_solid=False,
            ),
        },
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
