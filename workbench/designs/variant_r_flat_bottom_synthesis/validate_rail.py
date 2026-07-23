"""Focused native validation for the repaired printable longitudinal rails."""

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

from build123d import Unit, export_step, import_step


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simplified_printable_closure"
)
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simplified_printable_closure as model  # noqa: E402


OUT = ROOT / "build" / "workbench" / "variant_r_flat_bottom_synthesis" / "rail"
STEP_PATH = OUT / "printable_longitudinal_rails.step"
DIAGNOSTICS_PATH = OUT / "diagnostics.json"


def _bounds(solid) -> dict[str, list[float]]:
    bounds = solid.bounding_box()
    return {
        "min_mm": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max_mm": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size_mm": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def main() -> None:
    rails = model._printable_longitudinal_rails()
    solids = rails.solids()
    if len(solids) != 3 or not all(solid.is_valid for solid in solids):
        raise ValueError(
            "Printable rail set must contain three valid solids: "
            f"count={len(solids)}, validity={[s.is_valid for s in solids]}"
        )

    volumes = [solid.volume for solid in solids]
    if max(volumes) - min(volumes) > 1e-5:
        raise ValueError(f"Rotated printable rails changed volume: {volumes}")

    top = min(solids, key=lambda solid: solid.bounding_box().size.X)
    top_bounds = top.bounding_box()
    if (
        len(top.solids()) != 1
        or abs(top_bounds.min.Y - model.base.REAR_INNER_Y) < 1e-3
        or abs(top_bounds.max.Y - model.base.REAR_INNER_Y) > 1e-3
        or top_bounds.max.Z > model.base.D.height / 2.0 - 5.0
    ):
        raise ValueError(
            "Rear ramp is not fused into one rail at the intended rear "
            f"envelope: {_bounds(top)}"
        )

    published_step = job_output_path(STEP_PATH)
    published_step.parent.mkdir(parents=True, exist_ok=True)
    export_step(rails, published_step, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published_step)
    imported_solids = imported.solids()
    if len(imported_solids) != 3 or not all(solid.is_valid for solid in imported_solids):
        raise ValueError(
            "Printable rail STEP round-trip failed: "
            f"count={len(imported_solids)}, "
            f"validity={[solid.is_valid for solid in imported_solids]}"
        )

    diagnostics = {
        "solid_count": len(solids),
        "all_solids_valid": True,
        "volume_per_rail_mm3": volumes,
        "top_rail_bounds": _bounds(top),
        "rear_inner_y_mm": model.base.REAR_INNER_Y,
        "roundtrip_solid_count": len(imported_solids),
        "roundtrip_all_solids_valid": True,
    }
    published_diagnostics = job_output_path(DIAGNOSTICS_PATH)
    published_diagnostics.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
