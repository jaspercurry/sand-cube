"""Focused lower-band splice validation before the full enclosure fit run."""

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

from build123d import Align, Box, Pos


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


OUT = (
    ROOT
    / "build"
    / "workbench"
    / "variant_r_flat_bottom_synthesis"
    / "splice"
)
DIAGNOSTICS_PATH = OUT / "diagnostics.json"


def _shape_volume(shape) -> float:
    if shape is None:
        return 0.0
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(
        solid.volume
        for item in shape
        for solid in item.solids()
    )


def _clipped_difference_volume(left, right, probe) -> float:
    difference = left - right
    if _shape_volume(difference) <= 1e-9:
        return 0.0
    return _shape_volume(difference & probe)


def _band(
    perimeter,
    width_mm: float,
    y0_mm: float,
    y1_mm: float,
    *,
    feature: str,
):
    original = model.single._perimeter_wire
    model.single._perimeter_wire = perimeter
    try:
        return model.single._single_face_band(
            width_mm,
            y0_mm,
            y1_mm,
            feature=feature,
        )
    finally:
        model.single._perimeter_wire = original


def _validate_band(
    label: str,
    width_mm: float,
    y0_mm: float,
    y1_mm: float,
) -> dict:
    authoritative = _band(
        model._AUTHORITATIVE_PERIMETER_WIRE,
        width_mm,
        y0_mm,
        y1_mm,
        feature=f"{label} authoritative band",
    )
    donor = _band(
        model._hybrid_perimeter_wire,
        width_mm,
        y0_mm,
        y1_mm,
        feature=f"{label} flat-bottom donor band",
    )
    spliced = model._splice_flat_bottom_band(
        authoritative,
        donor,
        feature=f"{label} focused splice",
    )
    if len(spliced.solids()) != 1 or not spliced.is_valid:
        raise ValueError(f"{label} splice is not one valid solid")

    upper_min_z = (
        model.BOTTOM_SYNTHESIS_MAX_Z_MM
        + model.BOTTOM_SYNTHESIS_OVERLAP_MM / 2.0
        + 0.05
    )
    upper_max_z = 200.0
    lower_min_z = -200.0
    lower_max_z = (
        model.BOTTOM_SYNTHESIS_MAX_Z_MM
        - model.BOTTOM_SYNTHESIS_OVERLAP_MM / 2.0
        - 0.05
    )
    upper_probe = Pos(
        0.0,
        model.base.D.center_y,
        (upper_min_z + upper_max_z) / 2.0,
    ) * Box(
        240.0,
        240.0,
        upper_max_z - upper_min_z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    lower_probe = Pos(
        0.0,
        model.base.D.center_y,
        (lower_min_z + lower_max_z) / 2.0,
    ) * Box(
        240.0,
        240.0,
        lower_max_z - lower_min_z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    authoritative_only_upper = _clipped_difference_volume(
        authoritative,
        spliced,
        upper_probe,
    )
    spliced_only_upper = _clipped_difference_volume(
        spliced,
        authoritative,
        upper_probe,
    )
    donor_only_lower = _clipped_difference_volume(donor, spliced, lower_probe)
    spliced_only_lower = _clipped_difference_volume(spliced, donor, lower_probe)
    if max(
        authoritative_only_upper,
        spliced_only_upper,
        donor_only_lower,
        spliced_only_lower,
    ) > 0.01:
        raise ValueError(
            f"{label} splice did not preserve its two donors: "
            f"upper_ref_only={authoritative_only_upper}, "
            f"upper_splice_only={spliced_only_upper}, "
            f"lower_donor_only={donor_only_lower}, "
            f"lower_splice_only={spliced_only_lower}"
        )
    return {
        "authoritative_volume_mm3": authoritative.volume,
        "flat_bottom_donor_volume_mm3": donor.volume,
        "spliced_volume_mm3": spliced.volume,
        "authoritative_only_upper_mm3": authoritative_only_upper,
        "spliced_only_upper_mm3": spliced_only_upper,
        "donor_only_lower_mm3": donor_only_lower,
        "spliced_only_lower_mm3": spliced_only_lower,
        "one_valid_solid": True,
    }


def main() -> None:
    bed_y = model.source.BAFFLE_BED_Y
    shoulder_y = bed_y + model.GASKET_CLOSED_GAP_MM
    diagnostics = {
        "splice_max_z_mm": model.BOTTOM_SYNTHESIS_MAX_Z_MM,
        "splice_overlap_mm": model.BOTTOM_SYNTHESIS_OVERLAP_MM,
        "bands": {
            "baffle_land": _validate_band(
                "baffle land",
                model.SEAL_LAND_WIDTH_MM,
                bed_y - model.BAFFLE_STRUCTURE_THICKNESS_MM,
                bed_y,
            ),
            "gasket": _validate_band(
                "gasket",
                model.GASKET_WIDTH_MM,
                bed_y,
                shoulder_y,
            ),
            "bucket_land": _validate_band(
                "bucket land",
                model.SEAL_LAND_WIDTH_MM,
                shoulder_y,
                shoulder_y + model.BUCKET_SHOULDER_THICKNESS_MM,
            ),
        },
    }
    published = job_output_path(DIAGNOSTICS_PATH)
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
