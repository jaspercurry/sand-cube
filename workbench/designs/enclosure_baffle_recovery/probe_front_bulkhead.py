"""Trace visible upper-fill material to its source construction.

This is a read-only geometry diagnostic.  It rebuilds the current Stage-1
hybrid joint in memory, compares it with the current bucket STEP, then clips
the upper-left fill region into its source components.  Published artifacts go
under build/workbench and the existing review-viewer root.
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
import subprocess
import sys
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    Compound,
    Pos,
    Shape,
    Unit,
    export_step,
    import_step,
)
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


SOURCE_BUILD = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
AUTHORITATIVE_BASE_STEP = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
    / "sand_cube_190x210_single_oval_port_base.step"
)
CURRENT_BUCKET_STEP = SOURCE_BUILD / "simple_tongue_groove_bucket.step"
OUT = ROOT / "build" / "workbench" / "enclosure_baffle_recovery" / "provenance"
VIEWER_ROOT = SOURCE_BUILD / "review_viewers"


def _install_legacy_intersect_adapter() -> None:
    """Adapt build123d 0.11 ShapeList intersections for legacy project code.

    The current repository source predates build123d 0.11.1 and consistently
    expects ``shape.intersect(other)`` to return one Shape/Compound.  Keep this
    compatibility local to the disposable worker instead of modifying the
    production geometry during a read-only diagnosis.
    """
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


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _one_valid_solid(shape: Any, *, feature: str):
    solids = [solid for solid in shape.solids() if solid.volume > 1e-6]
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{feature} is not one valid solid: count={len(solids)}")
    return solids[0]


def _nonempty_compound(shape: Any, *, feature: str) -> Compound:
    solids = [solid for solid in shape.solids() if solid.volume > 1e-6]
    if not solids or not all(solid.is_valid for solid in solids):
        raise ValueError(f"{feature} did not produce valid solids")
    return Compound(children=solids)


def _bbox(shape: Any) -> dict[str, list[float]]:
    bounds = shape.bounding_box()
    return {
        "min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size_mm": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def _export_viewer(shape: Any, *, stem: str) -> dict[str, Any]:
    published_step = job_output_path(OUT / f"{stem}.step")
    published_step.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, published_step, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published_step)
    imported_solids = imported.solids()
    if not imported_solids or not all(solid.is_valid for solid in imported_solids):
        raise ValueError(f"{stem} failed STEP round trip")

    published_viewer = job_output_path(VIEWER_ROOT / stem)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
            str(published_step),
            "--out",
            str(published_viewer),
        ],
        check=True,
    )
    return {
        "step": str(OUT / f"{stem}.step"),
        "viewer": f"http://127.0.0.1:3939/{stem}/viewer/",
        "solid_count": len(imported_solids),
        "all_solids_valid": True,
    }


def _occupancy_probe(
    bucket: Any,
    face_plate: Any,
    support_wedge: Any,
    fill_supports: Any,
    *,
    y_values: list[float],
) -> dict[str, Any]:
    classifiers = {
        name: [BRepClass3d_SolidClassifier(solid.wrapped) for solid in shape.solids()]
        for name, shape in (
            ("bucket", bucket),
            ("face_plate", face_plate),
            ("support_wedge", support_wedge),
            ("fill_supports", fill_supports),
        )
    }

    def occupied(name: str, x_mm: float, y_mm: float, z_mm: float) -> bool:
        for classifier in classifiers[name]:
            classifier.Perform(gp_Pnt(x_mm, y_mm, z_mm), 1e-7)
            if classifier.State() in (TopAbs_IN, TopAbs_ON):
                return True
        return False

    counts = {
        y_key: {
            "bucket": 0,
            "face_plate": 0,
            "support_wedge": 0,
            "fill_supports": 0,
            "unattributed_bucket": 0,
        }
        for y_key in (f"{value:.3f}" for value in y_values)
    }
    occupied_points: list[dict[str, Any]] = []
    x_values = [-96.0, -92.0, -88.0, -86.0, -84.0, -80.0, -76.0, -72.0]
    z_values = [72.0, 76.0, 80.0, 84.0, 86.0, 88.0, 92.0, 96.0]
    for y_mm in y_values:
        y_key = f"{y_mm:.3f}"
        for x_mm in x_values:
            for z_mm in z_values:
                labels = [
                    name
                    for name in ("face_plate", "support_wedge", "fill_supports")
                    if occupied(name, x_mm, y_mm, z_mm)
                ]
                in_bucket = occupied("bucket", x_mm, y_mm, z_mm)
                if in_bucket:
                    counts[y_key]["bucket"] += 1
                    if not labels:
                        counts[y_key]["unattributed_bucket"] += 1
                    occupied_points.append(
                        {
                            "xyz_mm": [x_mm, y_mm, z_mm],
                            "source_components": labels or ["inherited_bucket"],
                        }
                    )
                for label in labels:
                    counts[y_key][label] += 1
    return {
        "grid": {
            "x_mm": x_values,
            "z_mm": z_values,
            "y_mm": y_values,
            "sample_count": len(x_values) * len(z_values) * len(y_values),
        },
        "occupied_counts_by_y": counts,
        "occupied_bucket_points": occupied_points,
    }


def main() -> None:
    _install_legacy_intersect_adapter()
    if not CURRENT_BUCKET_STEP.is_file():
        raise FileNotFoundError(CURRENT_BUCKET_STEP)

    current_bucket = _one_valid_solid(
        import_step(CURRENT_BUCKET_STEP),
        feature="current bucket STEP",
    )
    print("probe: current bucket STEP loaded", flush=True)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    original_perimeter = model.single._perimeter_wire
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        face_plate, support_wedge, _bulkhead, bulkhead_audit = (
            model.previous._front_bulkhead()
        )
        service_opening = model.previous._projected_service_opening_clearance()
        fill_features = [
            model.simplified._front_fill_feature(x_sign)
            for x_sign in (-1.0, 1.0)
        ]
        fill_supports = Compound(
            children=[feature["support"] for feature in fill_features]
        )
    finally:
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder
        model.single._perimeter_wire = original_perimeter
    print("probe: canonical source components built in memory", flush=True)

    face_y = model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    plate_rear_y = face_y + model.previous.FRONT_BULKHEAD_THICKNESS_MM
    wedge_landing_y = plate_rear_y + model.previous.FRONT_BULKHEAD_SUPPORT_DROP_MM
    wedge_root_y = wedge_landing_y + model.previous.FRONT_BULKHEAD_ROOT_DEPTH_MM

    upper_left_clip = Pos(
        -77.5,
        (face_y - 0.5 + wedge_root_y + 16.0) / 2.0,
        77.5,
    ) * Box(
        45.0,
        wedge_root_y + 16.0 - (face_y - 0.5),
        45.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    fill_axis_clip = Pos(
        -86.0,
        (face_y - 1.0 + wedge_root_y + 18.0) / 2.0,
        84.0,
    ) * Box(
        5.0,
        wedge_root_y + 18.0 - (face_y - 1.0),
        32.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    observed = _nonempty_compound(
        current_bucket.intersect(upper_left_clip),
        feature="observed upper-left bucket region",
    )
    face_piece = _nonempty_compound(
        face_plate.intersect(upper_left_clip),
        feature="upper-left face-plate component",
    )
    wedge_piece = _nonempty_compound(
        support_wedge.intersect(upper_left_clip),
        feature="upper-left support-wedge component",
    )
    fill_piece = _nonempty_compound(
        fill_supports.intersect(upper_left_clip),
        feature="upper-left fill-support component",
    )
    attributed = Compound(children=[face_plate, support_wedge, *fill_supports.solids()])
    residual_piece_raw = current_bucket.intersect(upper_left_clip).cut(attributed)
    service_intrusion = current_bucket.intersect(service_opening)
    service_residual = (
        None if service_intrusion is None else service_intrusion.cut(attributed)
    )

    protected_service_opening = {
        "artifact_intrusion_mm3": _shape_volume(service_intrusion),
        "face_plate_attribution_mm3": _shape_volume(
            None if service_intrusion is None else service_intrusion.intersect(face_plate)
        ),
        "support_wedge_attribution_mm3": _shape_volume(
            None
            if service_intrusion is None
            else service_intrusion.intersect(support_wedge)
        ),
        "fill_support_attribution_mm3": _shape_volume(
            None
            if service_intrusion is None
            else service_intrusion.intersect(fill_supports)
        ),
        "unattributed_inherited_bucket_mm3": _shape_volume(service_residual),
        "probe_bbox": _bbox(service_opening),
    }

    upper_left_components = {
        "observed_bucket_mm3": _shape_volume(observed),
        "face_plate_intersection_mm3": _shape_volume(face_piece),
        "support_wedge_intersection_mm3": _shape_volume(wedge_piece),
        "fill_support_intersection_mm3": _shape_volume(fill_piece),
        "inherited_bucket_remainder_mm3": _shape_volume(residual_piece_raw),
        "face_plate_presence_ratio": (
            _shape_volume(face_piece.intersect(current_bucket))
            / _shape_volume(face_piece)
        ),
        "support_wedge_presence_ratio": (
            _shape_volume(wedge_piece.intersect(current_bucket))
            / _shape_volume(wedge_piece)
        ),
        "fill_support_presence_ratio": (
            _shape_volume(fill_piece.intersect(current_bucket))
            / _shape_volume(fill_piece)
        ),
    }
    occupancy = _occupancy_probe(
        current_bucket,
        face_plate,
        support_wedge,
        fill_supports,
        y_values=[
            face_y + 0.5,
            face_y + 1.5,
            plate_rear_y + 0.5,
            wedge_landing_y - 0.25,
            wedge_root_y - 0.10,
        ],
    )
    print("probe: X/Y/Z provenance grid measured", flush=True)

    diagnostics = {
        "scope": "read-only front-bulkhead and upper-fill provenance",
        "current_bucket_step": str(CURRENT_BUCKET_STEP),
        "source_component_reconstruction": {
            "diagnostic_build123d_0_11_intersect_adapter": True,
            "current_artifact_volume_mm3": current_bucket.volume,
            "method": (
                "Rebuild only the canonical face plate, support wedge, and "
                "two fill supports; intersect each directly with the current "
                "bucket STEP and protected service opening."
            ),
            "bulkhead_audit": bulkhead_audit,
        },
        "front_planes_mm": {
            "bulkhead_face_y": face_y,
            "bulkhead_plate_rear_y": plate_rear_y,
            "support_wedge_landing_y": wedge_landing_y,
            "support_wedge_root_y": wedge_root_y,
        },
        "upper_left_probe_bbox": _bbox(upper_left_clip),
        "upper_left_component_intersections": upper_left_components,
        "protected_service_opening": protected_service_opening,
        "xyz_occupancy": occupancy,
        "source_operations": {
            "face_plate": (
                "_front_bulkhead: exact_outer.intersect(slab).cut(inner_opening), "
                "then cut(fill_keepout)"
            ),
            "support_wedge": (
                "_front_bulkhead: exact_outer.intersect(wedge_slab).cut(" 
                "wedge_opening), then cut(fill_keepout), then fuse(face_plate)"
            ),
            "fill_support": (
                "simplified._front_fill_feature: outer_entry.fuse(" 
                "outer_transition).cut(passage), then _lightweight_common_joint "
                "fuses the hollow support into bucket"
            ),
        },
        "visual_evidence": {
            "interactive_bucket": "http://127.0.0.1:3939/bucket/viewer/",
            "mcp_isometric_png": (
                "build/workbench/enclosure_baffle_recovery/mcp_bucket_iso.png"
            ),
            "mcp_fill_axis_section_png": (
                "build/workbench/enclosure_baffle_recovery/"
                "mcp_upper_fill_section.png"
            ),
        },
    }
    diagnostics_path = job_output_path(OUT / "front_bulkhead_provenance.json")
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2), flush=True)


if __name__ == "__main__":
    main()
