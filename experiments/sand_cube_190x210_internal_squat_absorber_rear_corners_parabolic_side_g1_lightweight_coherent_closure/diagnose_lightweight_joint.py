"""Rebuild only the lightweight closure joint from the last known base STEP."""

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

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from build123d import import_step

_EXPERIMENT_DIR = _CadSafetyPath(__file__).resolve().parent
if str(_EXPERIMENT_DIR) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_EXPERIMENT_DIR))
import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure as model


BASE_STEP = (
    _CAD_SAFETY_ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_systemic_joint_recessed_fasteners"
    / "sand_cube_190x210_single_oval_port_base.step"
)


def main() -> None:
    full_base = model._single_solid(
        import_step(BASE_STEP),
        feature="known-good full-detail enclosure",
    )
    original_bypass = model.single.SCREW_BYPASS_DEPTH_MM
    model.single.SCREW_BYPASS_DEPTH_MM = model.SERVICE_BYPASS_DEPTH_MM
    try:
        common = model._lightweight_common_joint(full_base)
        model._accessible_fastener_concept(common)
    finally:
        model.single.SCREW_BYPASS_DEPTH_MM = original_bypass
    print("Lightweight joint and accessible-fastener diagnostic passed")


if __name__ == "__main__":
    main()
