"""Measure geometric equivalence of retained authoritative L/R/T seam edges."""

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

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Pnt


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


OUTPUT = (
    ROOT
    / "build/workbench/variant_r_no_splice_production/"
    "perimeter-edge-equivalence.json"
)


def _point_distance(edge: Any, point: Any) -> float:
    vertex = BRepBuilderAPI_MakeVertex(
        gp_Pnt(point.X, point.Y, point.Z)
    ).Vertex()
    tool = BRepExtrema_DistShapeShape(edge.wrapped, vertex)
    tool.Perform()
    if not tool.IsDone():
        raise ValueError("edge-to-point distance failed")
    return tool.Value()


def _edge_deviation(source: Any, target: Any) -> float:
    return max(
        _point_distance(target, source.position_at(value))
        for value in (0.0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0)
    )


def _retained_edges(wire: Any, *, offset_mm: float) -> tuple[list[Any], list[Any]]:
    tangency = model.VARIANT_R_PARAMETERS.path_bottom_corner_tangency_mm
    half_size = model.VARIANT_R_PARAMETERS.path_half_size_mm + offset_mm
    retained = []
    removed = []
    for edge in wire.edges():
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
    return retained, removed


def main() -> None:
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
        retained, removed = _retained_edges(
            authoritative,
            offset_mm=offset_mm,
        )
        candidates = list(hybrid.edges())
        matches = []
        for index, edge in enumerate(retained):
            ranked = [
                (
                    max(
                        _edge_deviation(edge, candidate),
                        _edge_deviation(candidate, edge),
                    ),
                    candidate,
                )
                for candidate in candidates
            ]
            deviation, match = min(ranked, key=lambda item: item[0])
            matches.append(
                {
                    "authoritative_edge_index": index,
                    "authoritative_length_mm": edge.length,
                    "hybrid_length_mm": match.length,
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
        if maximum_deviation > 1e-9 or maximum_length_difference > 1e-9:
            raise ValueError(
                "retained perimeter edge geometry changed: "
                f"offset={offset_mm}, matches={matches}"
            )
        records[f"offset_{offset_mm:+g}_mm"] = {
            "authoritative_edge_count": len(authoritative.edges()),
            "removed_bottom_edge_count": len(removed),
            "retained_lrt_edge_count": len(retained),
            "hybrid_edge_count": len(candidates),
            "matched_lrt_edge_count": len(matches),
            "maximum_bidirectional_sampled_deviation_mm": maximum_deviation,
            "maximum_length_difference_mm": maximum_length_difference,
            "matches": matches,
        }
    result = {
        "scope": "retained Variant R L/R/T perimeter-edge geometry",
        "result": "pass",
        "records": records,
        "topology_note": (
            "Wire.combine creates new edge wrappers, so geometric equality is "
            "measured bidirectionally instead of asserting handle identity."
        ),
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
