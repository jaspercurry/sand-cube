"""Build the simple gasket chamfer and cylindrical screw-pocket candidate."""

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

from build123d import Align, Box, Compound, Pos, Unit, export_step, import_step


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure as model  # noqa: E402


OUTPUT_ROOT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
REFERENCE_BUCKET_STEP = OUTPUT_ROOT / "centered_captive_nut_bucket.step"
FULL_DETAIL_BASE_STEP = OUTPUT_ROOT / "parabolic_g1_conformal_full_detail_base.step"
FROZEN_BAFFLE_STEP = (
    ROOT
    / "releases"
    / "enclosure_v1"
    / "front_baffle"
    / "artifacts"
    / "front_baffle_v1.step"
)
CANDIDATE_STEP = (
    OUTPUT_ROOT / "bucket_simple_transition_fasteners_candidate.step"
)
DIAGNOSTICS_PATH = (
    OUTPUT_ROOT / "bucket_simple_transition_fasteners_candidate_diagnostics.json"
)
VIEWER_PATH = OUTPUT_ROOT / "bucket_simple_transition_fasteners_candidate_viewer"
GASKET_SECTION_STEP = (
    OUTPUT_ROOT / "bucket_simple_transition_gasket_section.step"
)
GASKET_SECTION_VIEWER_PATH = (
    OUTPUT_ROOT / "bucket_simple_transition_gasket_section_viewer"
)
SCREW_SECTION_STEP = OUTPUT_ROOT / "bucket_simple_screw_recess_section.step"
SCREW_SECTION_VIEWER_PATH = (
    OUTPUT_ROOT / "bucket_simple_screw_recess_section_viewer"
)


def _bbox_deltas(reference, candidate) -> dict[str, float]:
    reference_box = reference.bounding_box()
    candidate_box = candidate.bounding_box()
    return {
        "min_x": candidate_box.min.X - reference_box.min.X,
        "max_x": candidate_box.max.X - reference_box.max.X,
        "min_y": candidate_box.min.Y - reference_box.min.Y,
        "max_y": candidate_box.max.Y - reference_box.max.Y,
        "min_z": candidate_box.min.Z - reference_box.min.Z,
        "max_z": candidate_box.max.Z - reference_box.max.Z,
    }


def _publish_viewer(shape, step_path: Path, viewer_path: Path) -> None:
    published_step = job_output_path(step_path)
    published_step.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, published_step, unit=Unit.MM, write_pcurves=True)
    published_viewer = job_output_path(viewer_path)
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
    model.centered._configure_viewer(published_viewer, cutaway=False)


def main() -> None:
    for required_path in (
        FULL_DETAIL_BASE_STEP,
        REFERENCE_BUCKET_STEP,
        FROZEN_BAFFLE_STEP,
    ):
        if not required_path.is_file():
            raise FileNotFoundError(required_path)

    full_detail_base = model._single_solid(
        import_step(FULL_DETAIL_BASE_STEP),
        feature="authoritative full-detail enclosure source",
    )
    reference_bucket = model._single_solid(
        import_step(REFERENCE_BUCKET_STEP),
        feature="latest working bucket reference",
    )
    frozen_baffle = model._single_solid(
        import_step(FROZEN_BAFFLE_STEP),
        feature="frozen Front Baffle V1",
    )

    original_bypass_half_width = model.single.SCREW_BYPASS_HALF_WIDTH_MM
    original_bypass_depth = model.single.SCREW_BYPASS_DEPTH_MM
    model.single.SCREW_BYPASS_HALF_WIDTH_MM = model.SERVICE_BYPASS_HALF_WIDTH_MM
    model.single.SCREW_BYPASS_DEPTH_MM = model.SERVICE_BYPASS_DEPTH_MM
    try:
        common = model._lightweight_common_joint(full_detail_base)
        print("candidate: rebuilt simple gasket transition", flush=True)
        fastener_system = model._accessible_fastener_concept(common)
        print("candidate: rebuilt cylindrical screw supports", flush=True)
    finally:
        model.single.SCREW_BYPASS_HALF_WIDTH_MM = original_bypass_half_width
        model.single.SCREW_BYPASS_DEPTH_MM = original_bypass_depth
    bucket = fastener_system["bucket"]
    passages = common["front_fill_passages"]
    final_fill_clearances = common["front_fill_final_clearances"]
    joint_audit = dict(model._JOINT_AUDIT)
    transition_audit = {
        "depth_mm": joint_audit["front_transition_depth_mm"],
        "face_vertical_block_thickness_mm": joint_audit[
            "face_vertical_block_thickness_mm"
        ],
        "root_overlap_mm": joint_audit["front_transition_root_overlap_mm"],
        "land_overlap_mm": joint_audit["front_transition_land_overlap_mm"],
        "root_wall_mm": joint_audit["root_wall_mm"],
        "face_outer_offset_mm": joint_audit["face_outer_offset_mm"],
        "inner_wall_offset_mm": joint_audit["inner_wall_offset_mm"],
        "maximum_angle_from_print_axis_deg": joint_audit[
            "front_transition_maximum_angle_from_print_axis_deg"
        ],
    }
    fastener_audit = dict(model._FASTENER_AUDIT)
    screw_cutters = {}
    intentional_screw_openings = []
    for z_sign, label in ((-1.0, "bottom"), (1.0, "top")):
        direction = model._fastener_direction(z_sign)
        surface = model._fastener_surface(z_sign)
        nut_center = surface + direction * model.NUT_AXIS_DISTANCE_MM
        head_counterbore = model.source._cylinder_between(
            surface - direction * 0.8,
            surface + direction * model.HEAD_COUNTERBORE_DEPTH_MM,
            diameter=model.HEAD_COUNTERBORE_D_MM,
        )
        through_bore = model.source._cylinder_between(
            surface
            + direction * (model.HEAD_COUNTERBORE_DEPTH_MM - 0.1),
            nut_center + direction * 3.2,
            diameter=model.SCREW_CLEARANCE_D_MM,
        )
        screw_cutters[label] = (head_counterbore, through_bore)
        intentional_screw_openings.extend((head_counterbore, through_bore))
    unclosed_corner_volume, fill_passage_blockage = (
        model._audit_bucket_front_closure(
            bucket,
            passages,
            intentional_openings=(
                tuple(final_fill_clearances)
                + tuple(intentional_screw_openings)
            ),
        )
    )
    print("candidate: front closure and fill passages validated", flush=True)

    gasket_probe = model.single._single_face_band(
        model.GASKET_WIDTH_MM,
        model.source.SHOULDER_Y,
        model.source.SHOULDER_Y + 0.05,
        feature="unchanged bucket gasket-face support probe",
    )
    gasket_support_ratio = model._shape_volume(
        gasket_probe.intersect(bucket)
    ) / gasket_probe.volume
    if gasket_support_ratio < model.MINIMUM_GASKET_SUPPORT_RATIO:
        raise ValueError(
            "The simple transition changed the gasket face: "
            f"support={gasket_support_ratio:.6f}"
        )
    print("candidate: unchanged gasket face validated", flush=True)

    exterior_deltas = _bbox_deltas(reference_bucket, bucket)
    if max(abs(value) for value in exterior_deltas.values()) > 1e-5:
        raise ValueError(
            f"The bucket correction changed exterior bounds: {exterior_deltas}"
        )
    frozen_baffle_overlap = model._shape_volume(
        bucket.intersect(frozen_baffle)
    )
    if frozen_baffle_overlap > model.MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            "The corrected bucket interferes with frozen Front Baffle V1 by "
            f"{frozen_baffle_overlap:.6f} mm3"
        )
    print("candidate: exterior bounds and frozen baffle fit validated", flush=True)

    screw_cutter_blockage: dict[str, dict[str, float]] = {}
    for label in ("bottom", "top"):
        head_counterbore, through_bore = screw_cutters[label]
        head_blockage = model._shape_volume(head_counterbore.intersect(bucket))
        shaft_blockage = model._shape_volume(through_bore.intersect(bucket))
        screw_cutter_blockage[label] = {
            "head_pocket_blockage_mm3": head_blockage,
            "shaft_bore_blockage_mm3": shaft_blockage,
        }
        if max(head_blockage, shaft_blockage) > 0.01:
            raise ValueError(
                f"The {label} simple screw recess is obstructed: "
                f"head={head_blockage:.6f}, shaft={shaft_blockage:.6f} mm3"
            )
        audit = fastener_audit[label]
        if audit["bucket_gusset_count"] != 0:
            raise ValueError(f"The {label} screw recess retained a gusset")
        if audit["bucket_blister_root_mm3"] <= 0.01:
            raise ValueError(f"The {label} screw blister is not rooted")
    print("candidate: screw head pockets and shaft bores validated", flush=True)

    candidate_step = job_output_path(CANDIDATE_STEP)
    candidate_step.parent.mkdir(parents=True, exist_ok=True)
    export_step(bucket, candidate_step, unit=Unit.MM, write_pcurves=True)
    print("candidate: bucket STEP exported", flush=True)
    roundtrip = import_step(candidate_step)
    roundtrip_solids = roundtrip.solids()
    step_roundtrip = {
        "source_solid_count": len(bucket.solids()),
        "imported_solid_count": len(roundtrip_solids),
        "all_imported_solids_valid": all(
            solid.is_valid for solid in roundtrip_solids
        ),
    }
    if step_roundtrip != {
        "source_solid_count": 1,
        "imported_solid_count": 1,
        "all_imported_solids_valid": True,
    }:
        raise ValueError(f"Corrected bucket STEP round trip failed: {step_roundtrip}")

    viewer_path = job_output_path(VIEWER_PATH)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
            str(candidate_step),
            "--out",
            str(viewer_path),
        ],
        check=True,
    )
    model.centered._configure_viewer(viewer_path, cutaway=False)

    gasket_section = bucket.intersect(
        Pos(45.0, model.source.SHOULDER_Y + 10.0, 0.0)
        * Box(
            4.0,
            46.0,
            205.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )
    screw_section = bucket.intersect(
        Pos(0.0, -82.0, 88.0)
        * Box(
            8.0,
            34.0,
            30.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )
    if not gasket_section.solids() or not screw_section.solids():
        raise ValueError("A required bucket close-section is empty")
    _publish_viewer(
        gasket_section,
        GASKET_SECTION_STEP,
        GASKET_SECTION_VIEWER_PATH,
    )
    _publish_viewer(
        screw_section,
        SCREW_SECTION_STEP,
        SCREW_SECTION_VIEWER_PATH,
    )

    diagnostics = {
        "scope": "simple gasket underside and cylindrical screw recesses",
        "full_detail_base_step": str(FULL_DETAIL_BASE_STEP),
        "reference_bucket_step": str(REFERENCE_BUCKET_STEP),
        "frozen_baffle_step": str(FROZEN_BAFFLE_STEP),
        "candidate_step": str(CANDIDATE_STEP),
        "bucket_exterior_bounds_difference_mm": exterior_deltas,
        "reference_bucket_volume_mm3": reference_bucket.volume,
        "candidate_bucket_volume_mm3": bucket.volume,
        "added_bucket_material_mm3": bucket.volume - reference_bucket.volume,
        "frozen_front_baffle_v1_overlap_mm3": frozen_baffle_overlap,
        "outside_gasket_corner_closure_count": 4,
        "unclosed_outside_gasket_corner_volume_mm3": (
            unclosed_corner_volume
        ),
        "fill_passage_blockage_mm3": fill_passage_blockage,
        "front_transition_depth_mm": transition_audit["depth_mm"],
        "front_transition_vertical_block_thickness_mm": transition_audit[
            "face_vertical_block_thickness_mm"
        ],
        "front_transition_root_overlap_mm": transition_audit[
            "root_overlap_mm"
        ],
        "front_transition_land_overlap_mm": transition_audit[
            "land_overlap_mm"
        ],
        "front_transition_root_wall_mm": transition_audit["root_wall_mm"],
        "front_transition_face_outer_offset_mm": transition_audit[
            "face_outer_offset_mm"
        ],
        "front_transition_inner_wall_offset_mm": transition_audit[
            "inner_wall_offset_mm"
        ],
        "front_transition_maximum_angle_from_print_axis_deg": (
            transition_audit["maximum_angle_from_print_axis_deg"]
        ),
        "front_transition_support_free_under_45_deg": True,
        "gasket_face_plan_geometry_unchanged": True,
        "gasket_face_support_ratio": gasket_support_ratio,
        "screw_support_construction": (
            "one flush-clipped tilted cylindrical blister per screw"
        ),
        "screw_gusset_count": 0,
        "screw_blister_diameter_mm": model.BUCKET_SLEEVE_D_MM,
        "screw_head_counterbore_diameter_mm": model.HEAD_COUNTERBORE_D_MM,
        "screw_head_counterbore_depth_mm": model.HEAD_COUNTERBORE_DEPTH_MM,
        "screw_clearance_bore_diameter_mm": model.SCREW_CLEARANCE_D_MM,
        "screw_cutter_blockage": screw_cutter_blockage,
        "fastener_audit": fastener_audit,
        "screw_blisters_clipped_to_authoritative_exterior": True,
        "step_roundtrip": step_roundtrip,
        "viewers": {
            "bucket": str(VIEWER_PATH / "index.html"),
            "gasket_section": str(GASKET_SECTION_VIEWER_PATH / "index.html"),
            "screw_section": str(SCREW_SECTION_VIEWER_PATH / "index.html"),
        },
    }
    diagnostics_path = job_output_path(DIAGNOSTICS_PATH)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
