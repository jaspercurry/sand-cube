"""Trace the Viewer-selected corner hunks to the interface-reset radius.

The exact artifact-local face references are translated here into geometric
face signatures on one immutable STEP.  Those faces seed thin semantic target
volumes; no face index is used by production source.  The targets are then
tested against the restored construction stages and against reset envelopes
that differ only in corner radius.
"""

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

import json
import sys
from pathlib import Path
from typing import Any

from build123d import Align, Box, Compound, Face, Pos, Shape, Solid, Unit, Vector, export_step, import_step


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
ARTIFACT = (
    ROOT
    / "build/workbench/enclosure_baffle_recovery/"
    "deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step"
)
OUT_DIR = ROOT / "build/workbench/enclosure_baffle_recovery/corner_hunk_provenance"
TARGET_STEP = OUT_DIR / "selected_corner_hunk_targets.step"
REPORT = OUT_DIR / "corner_hunk_reset_radius_provenance.json"


FACE_SIGNATURES = {
    "upper_left": {
        "artifact_ref": "#f207",
        "center_xz_mm": (-87.328406, 87.328406),
        "area_mm2": 23.352861,
    },
    "upper_right": {
        "artifact_ref": "#f188",
        "center_xz_mm": (87.328406, 87.328406),
        "area_mm2": 23.352861,
    },
    "lower_left": {
        "artifact_ref": "#f32",
        "center_xz_mm": (-85.573715, -89.085026),
        "area_mm2": 47.486082,
    },
    "lower_right": {
        "artifact_ref": "#f190",
        "center_xz_mm": (85.609753, -89.063285),
        "area_mm2": 47.131790,
    },
}


def _volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


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


def _one_solid(shape: Any, *, feature: str) -> Solid:
    solids = [solid for solid in shape.solids() if solid.volume > 1e-6]
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{feature} is not one valid solid: {len(solids)}")
    return solids[0]


def _face_record(face: Face, index: int) -> dict[str, Any]:
    bounds = face.bounding_box()
    return {
        "build123d_face_position_1_based": index + 1,
        "area_mm2": face.area,
        "center_mm": [face.center().X, face.center().Y, face.center().Z],
        "bounds_min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "bounds_max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
    }


def _find_signature_face(artifact: Solid, signature: dict[str, Any]) -> tuple[int, Face]:
    target_x, target_z = signature["center_xz_mm"]
    target_area = signature["area_mm2"]
    candidates: list[tuple[float, int, Face]] = []
    for index, face in enumerate(artifact.faces()):
        bounds = face.bounding_box()
        if bounds.size.Y > 0.002:
            continue
        score = (
            abs(face.center().Y - model.source.BAFFLE_BED_Y) * 1000.0
            + abs(face.center().X - target_x)
            + abs(face.center().Z - target_z)
            + abs(face.area - target_area)
        )
        candidates.append((score, index, face))
    if not candidates:
        raise ValueError(f"No planar face candidates for {signature}")
    score, index, face = min(candidates, key=lambda item: item[0])
    # STEP healing can move the reported area of these small faces by roughly
    # 0.35 mm2 while retaining the same plane, center, bounds, and artifact
    # face position.  Keep the tolerance far below the separation to any
    # neighboring planar face, but do not require byte-identical area.
    if score > 1.0:
        raise ValueError(
            f"Artifact face signature did not resolve tightly: score={score:.6f}, "
            f"signature={signature}, resolved={_face_record(face, index)}"
        )
    return index, face


def _target_from_face(artifact: Solid, face: Face, *, label: str) -> Solid:
    # The selected planar faces are on the baffle-bed plane.  Extrude only
    # rearward exactly to the shoulder plane (the 1.00 mm gasket gap), then
    # intersect with the immutable artifact.  Material behind that plane is
    # the restored flat gasket-support face plate, not the unwanted hunk.
    prism = Solid.extrude(face, Vector(0.0, 1.00, 0.0)).clean().fix()
    return _one_solid(
        artifact.intersect(prism).clean().fix(),
        feature=f"{label} selected-face semantic target",
    )


def _reset(radius_mm: float, width_mm: float = 184.2) -> Solid:
    y0 = (
        model.source.BAFFLE_BED_Y
        - model.previous.BAFFLE_STRUCTURE_THICKNESS_MM
        - 0.15
    )
    y1 = model.source.SHOULDER_Y + 0.20
    outer = model.source._rounded_rectangle_prism(width_mm, radius_mm, y0, y1)
    inner = model.source._rounded_rectangle_prism(
        153.5,
        3.5,
        y0 - 0.10,
        y1 + 0.10,
    )
    return _one_solid(
        outer.cut(inner).clean().fix(),
        feature=(
            f"{width_mm:g} mm interface reset with r{radius_mm:g} corners"
        ),
    )


def _presence(target: Any, shape: Any) -> dict[str, float]:
    target_volume = _volume(target)
    overlap = _volume(target.intersect(shape))
    return {
        "target_volume_mm3": target_volume,
        "overlap_mm3": overlap,
        "coverage_ratio": overlap / target_volume if target_volume else 0.0,
    }


def main() -> None:
    _install_legacy_intersect_adapter()
    for path in (BASE_STEP, ARTIFACT):
        if not path.is_file():
            raise FileNotFoundError(path)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    original_perimeter = model.single._perimeter_wire
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        full_base = _one_solid(import_step(BASE_STEP), feature="authoritative base")
        artifact = _one_solid(import_step(ARTIFACT), feature="selected-face artifact")

        targets: dict[str, Solid] = {}
        resolved_faces = {}
        for label, signature in FACE_SIGNATURES.items():
            index, face = _find_signature_face(artifact, signature)
            targets[label] = _target_from_face(artifact, face, label=label)
            resolved_faces[label] = {
                "artifact_ref": signature["artifact_ref"],
                "resolved": _face_record(face, index),
            }
        target_all = Compound(children=list(targets.values()))

        clearance = model.closure._nested_split_envelope(
            clearance_mm=model.closure.SOCKET_NORMAL_CLEARANCE_MM
        )
        initial_bucket = _one_solid(
            full_base.cut(clearance).clean().fix(),
            feature="bucket after nested split",
        )

        reset_y0 = (
            model.source.BAFFLE_BED_Y
            - model.previous.BAFFLE_STRUCTURE_THICKNESS_MM
            - 0.15
        )
        initial_bounds = initial_bucket.bounding_box()
        artifact_bounds = artifact.bounding_box()
        protected_seat_max_y = reset_y0 - 0.05
        if artifact_bounds.min.Y >= protected_seat_max_y:
            raise ValueError("The immutable artifact has no forward curved-seat extent")

        face_plate, support_wedge, _bulkhead, _audit = model.previous._front_bulkhead()
        fill_supports = Compound(
            children=[
                model.simplified._front_fill_feature(sign)["support"]
                for sign in (-1.0, 1.0)
            ]
        )
        stages = {
            "full_base": full_base,
            "nested_split_clearance": clearance,
            "initial_bucket_after_nested_split": initial_bucket,
            "face_plate_addition": face_plate,
            "support_wedge_addition": support_wedge,
            "fill_support_additions": fill_supports,
        }

        radii = {}
        for radius_mm in (20.0, 12.0, 10.0, 8.0, 7.0, 6.5, 6.0, 5.0):
            cutter = _reset(radius_mm)
            cut_result = initial_bucket.cut(cutter).clean().fix()
            solids = [solid for solid in cut_result.solids() if solid.volume > 1e-6]
            radii[f"r{radius_mm:g}"] = {
                "cutter_target_coverage": {
                    label: _presence(target, cutter)
                    for label, target in targets.items()
                },
                "result_solid_count": len(solids),
                "all_result_solids_valid": all(solid.is_valid for solid in solids),
                "result_bounds": (
                    {
                        "min_y_mm": min(s.bounding_box().min.Y for s in solids),
                        "max_y_mm": max(s.bounding_box().max.Y for s in solids),
                    }
                    if solids
                    else None
                ),
                "cutter_min_y_mm": cutter.bounding_box().min.Y,
                "protected_forward_seat_max_y_mm": protected_seat_max_y,
                "cutter_to_protected_seat_y_gap_mm": (
                    cutter.bounding_box().min.Y - protected_seat_max_y
                ),
                "remaining_selected_target_mm3": _volume(
                    cut_result.intersect(target_all)
                ),
            }

        widths = {}
        for width_mm in (184.2, 184.3, 184.4, 184.5, 184.6):
            cutter = _reset(7.0, width_mm)
            cut_result = initial_bucket.cut(cutter).clean().fix()
            solids = [solid for solid in cut_result.solids() if solid.volume > 1e-6]
            widths[f"w{width_mm:g}"] = {
                "cutter_target_coverage": {
                    label: _presence(target, cutter)
                    for label, target in targets.items()
                },
                "result_solid_count": len(solids),
                "all_result_solids_valid": all(solid.is_valid for solid in solids),
                "result_min_y_mm": min(
                    solid.bounding_box().min.Y for solid in solids
                ),
                "remaining_selected_target_mm3": _volume(
                    cut_result.intersect(target_all)
                ),
            }

        target_path = job_output_path(TARGET_STEP)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        export_step(target_all, target_path, unit=Unit.MM, write_pcurves=True)

        result = {
            "artifact": str(ARTIFACT),
            "artifact_local_face_references": resolved_faces,
            "semantic_target": (
                "four radiused inherited-shell hunks on the baffle-bed face; "
                "two upper hunks sit directly at the fill mouths"
            ),
            "source_hypothesis": (
                "the 20 mm outer radius of _broad_interface_reset leaves the "
                "four corner sectors outside its reset envelope"
            ),
            "baffle_bed_y_mm": model.source.BAFFLE_BED_Y,
            "shoulder_y_mm": model.source.SHOULDER_Y,
            "reset_front_y_mm": reset_y0,
            "protected_forward_seat_y_extent_mm": [
                artifact_bounds.min.Y,
                protected_seat_max_y,
            ],
            "target_total_volume_mm3": _volume(target_all),
            "stage_presence": {
                label: {
                    name: _presence(target, stage)
                    for name, stage in stages.items()
                }
                for label, target in targets.items()
            },
            "reset_radius_trials": radii,
            "reset_width_trials_at_r7": widths,
        }
    finally:
        model.single._perimeter_wire = original_perimeter
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder

    report_path = job_output_path(REPORT)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
