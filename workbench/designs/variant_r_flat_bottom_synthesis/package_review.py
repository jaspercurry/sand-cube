"""Package the exact validated Variant R pair for read-only visual review."""

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
from pathlib import Path

from build123d import Compound, Unit, export_step, import_step


ROOT = Path(__file__).resolve().parents[3]
SOURCE_OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
BUCKET_STEP = SOURCE_OUT / "simple_tongue_groove_bucket.step"
BAFFLE_STEP = SOURCE_OUT / "simple_tongue_groove_baffle.step"
OUT = (
    ROOT
    / "build"
    / "workbench"
    / "variant_r_flat_bottom_synthesis"
    / "review"
)
ASSEMBLY_STEP = OUT / "variant_r_review_assembly.step"
DIAGNOSTICS_PATH = OUT / "diagnostics.json"


def _one_solid(path: Path, label: str):
    imported = import_step(path)
    solids = imported.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(
            f"{label} input is not one valid solid: "
            f"count={len(solids)}, validity={[solid.is_valid for solid in solids]}"
        )
    solid = solids[0]
    solid.label = label
    return solid


def _shape_volume(shape) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def main() -> None:
    bucket = _one_solid(BUCKET_STEP, "Variant R bucket")
    baffle = _one_solid(BAFFLE_STEP, "Variant R removable baffle")
    overlap_mm3 = _shape_volume(bucket & baffle)
    if overlap_mm3 > 0.001:
        raise ValueError(
            f"Validated review pair overlaps by {overlap_mm3:.6f} mm3"
        )

    assembly = Compound(
        children=[bucket, baffle],
        label="Variant R flat-bottom removable-front assembly",
    )
    published_step = job_output_path(ASSEMBLY_STEP)
    published_step.parent.mkdir(parents=True, exist_ok=True)
    export_step(assembly, published_step, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published_step)
    imported_solids = imported.solids()
    if len(imported_solids) != 2 or not all(
        solid.is_valid for solid in imported_solids
    ):
        raise ValueError(
            "Review assembly STEP round-trip failed: "
            f"count={len(imported_solids)}, "
            f"validity={[solid.is_valid for solid in imported_solids]}"
        )

    bounds = assembly.bounding_box()
    diagnostics = {
        "source_bucket": str(BUCKET_STEP.relative_to(ROOT)),
        "source_baffle": str(BAFFLE_STEP.relative_to(ROOT)),
        "source_solid_count": 2,
        "source_all_solids_valid": True,
        "bucket_baffle_overlap_mm3": overlap_mm3,
        "roundtrip_solid_count": len(imported_solids),
        "roundtrip_all_solids_valid": True,
        "assembly_bounds_min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "assembly_bounds_max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
    }
    published_diagnostics = job_output_path(DIAGNOSTICS_PATH)
    published_diagnostics.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
