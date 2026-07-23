"""Focused validation of the final baffle print-plane ownership transfer."""

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

from build123d import GeomType, export_step, import_step


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


MODEL_OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
OUT = (
    ROOT
    / "build"
    / "workbench"
    / "variant_r_flat_bottom_synthesis"
    / "print_transfer"
)


def _single(name: str):
    imported = import_step(MODEL_OUT / name)
    solids = imported.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{name} is not one valid STEP solid")
    return solids[0]


def _shape_volume(shape) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _contact(solid) -> dict:
    tolerance = 0.01
    bed_z = min(vertex.Z for vertex in solid.vertices())
    contacts = []
    for face in solid.faces():
        face_bounds = face.bounding_box()
        if (
            face.geom_type == GeomType.PLANE
            and face_bounds.size.Z <= tolerance
            and abs(face_bounds.min.Z - bed_z) <= tolerance
            and abs(face_bounds.max.Z - bed_z) <= tolerance
        ):
            contacts.append(
                {
                    "area_mm2": face.area,
                    "x_span_mm": face_bounds.size.X,
                    "y_span_mm": face_bounds.size.Y,
                }
            )
    if not contacts:
        raise ValueError(f"No planar contact at topology bed Z={bed_z}")
    largest = max(contacts, key=lambda record: record["x_span_mm"])
    if largest["x_span_mm"] < 187.0 or largest["area_mm2"] < 2200.0:
        raise ValueError(f"Planar contact is too small: {largest}")
    return {
        "bed_z_mm": bed_z,
        "face_count": len(contacts),
        "total_area_mm2": sum(record["area_mm2"] for record in contacts),
        "largest_face": largest,
    }


def main() -> None:
    bucket = _single("simple_tongue_groove_bucket.step")
    baffle = _single("simple_tongue_groove_baffle.step")
    old_bucket_volume = bucket.volume
    old_baffle_volume = baffle.volume
    new_bucket, new_baffle, transfer = model._transfer_baffle_below_print_plane(
        bucket,
        baffle,
    )
    overlap = _shape_volume(new_bucket.intersect(new_baffle))
    bucket_gain = new_bucket.volume - old_bucket_volume
    baffle_loss = old_baffle_volume - new_baffle.volume
    material_addition = bucket_gain - baffle_loss
    if (
        len(new_bucket.solids()) != 1
        or len(new_baffle.solids()) != 1
        or not new_bucket.is_valid
        or not new_baffle.is_valid
        or overlap > 0.001
        or material_addition < -0.01
        or material_addition > 500.0
    ):
        raise ValueError(
            "Print-plane transfer failed: "
            f"bucket_gain={bucket_gain}, baffle_loss={baffle_loss}, "
            f"material_addition={material_addition}, overlap={overlap}"
        )

    contact = _contact(new_baffle)
    bucket_out = job_output_path(OUT / "candidate_bucket.step")
    baffle_out = job_output_path(OUT / "candidate_baffle.step")
    bucket_out.parent.mkdir(parents=True, exist_ok=True)
    export_step(new_bucket, bucket_out)
    export_step(new_baffle, baffle_out)
    diagnostics = {
        "transfer": transfer,
        "bucket_gain_mm3": bucket_gain,
        "baffle_loss_mm3": baffle_loss,
        "intentional_lower_root_addition_mm3": material_addition,
        "bucket_baffle_overlap_mm3": overlap,
        "print_contact": contact,
        "one_valid_bucket_solid": True,
        "one_valid_baffle_solid": True,
    }
    diagnostics_out = job_output_path(OUT / "diagnostics.json")
    diagnostics_out.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
