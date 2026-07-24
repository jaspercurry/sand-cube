"""Thin coordinated entrypoint for the accepted Variant R generator."""

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

from experiments.sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle import (  # noqa: E402
    generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as _model,
)
from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    write_producer_attestation,
)


def main() -> None:
    """Generate the cataloged Variant R artifact set."""

    _model.base.generate_authoritative_base_input(_model.OUT)
    write_producer_attestation(
        repo_root=_CAD_SAFETY_ROOT,
        output_directory=_model.OUT,
        producer_entrypoint=_CadSafetyPath(__file__),
    )


if __name__ == "__main__":
    main()
