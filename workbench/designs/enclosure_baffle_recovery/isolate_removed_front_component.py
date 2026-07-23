"""Isolate and measure the front geometry lost between two review artifacts.

This is a disposable provenance diagnostic.  It does not select transient STEP
face indices and it does not modify production geometry.  The older artifact
contains both the wanted sculpted seating seam and the unwanted corner
intrusions; the newer artifact omitted that mixed front component.  Their
Boolean difference is therefore the exact object that needs to be understood
before source is changed again.
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

from build123d import (
    Align,
    Box,
    Compound,
    Face,
    Pos,
    Shape,
    Solid,
    Unit,
    Vector,
    export_step,
    import_step,
)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common


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


OLD_STEP = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step"
)
NEW_STEP = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "front_component_removed_restored_bulkhead_candidate_viewer/"
    "front_component_removed_bucket.step"
)
OUT_DIR = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "isolated_removed_front_component"
)
REMOVED_STEP = OUT_DIR / "isolated_removed_front_component.step"
REPORT = OUT_DIR / "isolation_diagnostics.json"


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


def _bounds(shape: Any) -> dict[str, list[float]]:
    bounds = shape.bounding_box()
    return {
        "min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size_mm": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def _solid_record(solid: Solid) -> dict[str, Any]:
    return {
        "volume_mm3": solid.volume,
        "valid": solid.is_valid,
        "face_count": len(solid.faces()),
        "edge_count": len(solid.edges()),
        "bounds": _bounds(solid),
    }


def _planar_y_faces(shape: Any) -> list[dict[str, Any]]:
    records = []
    for face in shape.faces():
        bounds = face.bounding_box()
        if bounds.size.Y > 0.002:
            continue
        records.append(
            {
                "area_mm2": face.area,
                "center_mm": [face.center().X, face.center().Y, face.center().Z],
                "wire_count": len(face.wires()),
                "bounds": _bounds(face),
            }
        )
    return sorted(records, key=lambda item: item["area_mm2"], reverse=True)


def _opening_volume(offset_mm: float, y0_mm: float, y1_mm: float) -> Solid:
    wire = model._hybrid_perimeter_wire(offset_mm=offset_mm, y_mm=y0_mm)
    return Solid.extrude(Face(wire), Vector(0.0, y1_mm - y0_mm, 0.0)).clean().fix()


def main() -> None:
    _install_legacy_intersect_adapter()
    for path in (OLD_STEP, NEW_STEP):
        if not path.is_file():
            raise FileNotFoundError(path)

    old = import_step(OLD_STEP)
    new = import_step(NEW_STEP)
    old_solids = old.solids()
    new_solids = new.solids()
    if len(old_solids) != 1 or len(new_solids) != 1:
        raise ValueError(
            f"Expected one old/new solid, found {len(old_solids)}/{len(new_solids)}"
        )

    # The new artifact's minimum Y is more than 12 mm behind the old one.  A
    # whole-model old-minus-new Boolean is ambiguous because the two shells
    # have hundreds of coincident faces; on this kernel it returned only two
    # tiny tabs.  Spatially clip the old artifact to the complete forward
    # extent absent from the new artifact instead.  This is the exact deleted
    # front object and does not depend on transient topology.
    old_bounds = old_solids[0].bounding_box()
    new_bounds = new_solids[0].bounding_box()
    front_limit_y = new_bounds.min.Y - 0.01
    front_start_y = old_bounds.min.Y - 0.10
    front_clip = Pos(
        0.0,
        (front_start_y + front_limit_y) / 2.0,
        0.0,
    ) * Box(
        240.0,
        front_limit_y - front_start_y,
        240.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    common_builder = BRepAlgoAPI_Common(
        old_solids[0].wrapped,
        front_clip.wrapped,
    )
    common_builder.SetRunParallel(False)
    common_builder.Build()
    if not common_builder.IsDone():
        raise ValueError("OpenCascade could not clip the deleted front extent")
    removed_raw = Compound.cast(common_builder.Shape())
    removed_solids = sorted(
        [solid for solid in removed_raw.solids() if solid.volume > 1e-6],
        key=lambda solid: solid.volume,
        reverse=True,
    )
    if not removed_solids or not all(solid.is_valid for solid in removed_solids):
        raise ValueError("The isolated removed geometry is empty or invalid")
    removed = Compound(children=removed_solids)

    removed_path = job_output_path(REMOVED_STEP)
    removed_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(removed, removed_path, unit=Unit.MM, write_pcurves=True)
    round_trip = import_step(removed_path)

    removed_bounds = removed.bounding_box()
    y0 = removed_bounds.min.Y - 0.10
    y1 = removed_bounds.max.Y + 0.10
    semantic_openings = {}
    for label, offset in (
        ("seam_centerline", 0.0),
        ("gasket_land_inner_edge", -model.SEAL_LAND_WIDTH_MM / 2.0),
        ("gasket_footprint_inner_edge", -model.GASKET_WIDTH_MM / 2.0),
        ("gasket_land_outer_edge", model.SEAL_LAND_WIDTH_MM / 2.0),
    ):
        opening = _opening_volume(offset, y0, y1)
        overlap = _volume(removed.intersect(opening))
        semantic_openings[label] = {
            "offset_mm": offset,
            "opening_bounds": _bounds(opening),
            "removed_material_inside_opening_mm3": overlap,
            "removed_material_inside_opening_ratio": overlap / _volume(removed),
        }

    selected_regions = {
        "upper_left": (-90.5, -80.5, 80.5, 90.5),
        "upper_right": (80.5, 90.5, 80.5, 90.5),
        "lower_left": (-92.0, -72.5, -92.5, -81.0),
        "lower_right": (72.5, 92.0, -92.5, -81.0),
    }
    selected_overlaps = {}
    for label, (xmin, xmax, zmin, zmax) in selected_regions.items():
        region = Pos(
            (xmin + xmax) / 2.0,
            (y0 + y1) / 2.0,
            (zmin + zmax) / 2.0,
        ) * Box(
            xmax - xmin,
            y1 - y0,
            zmax - zmin,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        selected_overlaps[label] = _volume(removed.intersect(region))

    result = {
        "purpose": (
            "old artifact clipped to the complete forward extent absent from "
            "the new artifact; diagnostic only; no face-index selection"
        ),
        "old_artifact": str(OLD_STEP),
        "new_artifact": str(NEW_STEP),
        "isolated_artifact": str(REMOVED_STEP),
        "forward_extent_clip": {
            "old_min_y_mm": old_bounds.min.Y,
            "new_min_y_mm": new_bounds.min.Y,
            "clip_max_y_mm": front_limit_y,
        },
        "old": _solid_record(old_solids[0]),
        "new": _solid_record(new_solids[0]),
        "isolated_removed_total_volume_mm3": _volume(removed),
        "isolated_removed_bounds": _bounds(removed),
        "isolated_component_count": len(removed_solids),
        "isolated_components": [_solid_record(solid) for solid in removed_solids],
        "round_trip": {
            "solid_count": len(round_trip.solids()),
            "all_valid": all(solid.is_valid for solid in round_trip.solids()),
            "volume_mm3": _volume(round_trip),
        },
        "largest_planar_y_faces": _planar_y_faces(removed)[:40],
        "semantic_inner_boundary_tests": semantic_openings,
        "viewer_selected_semantic_corner_region_overlap_mm3": selected_overlaps,
    }

    report_path = job_output_path(REPORT)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
