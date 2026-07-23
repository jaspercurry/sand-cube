"""Regenerate the enclosure base needed by the standalone Variant R harness.

The inherited full cascade currently fails later while constructing a preview
cutaway.  This focused build executes the exact source operations that precede
that preview and publishes only the authoritative one-solid base STEP.
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

import hashlib
import json
import sys
from pathlib import Path

from build123d import Unit, export_step, import_step


ROOT = Path(__file__).resolve().parents[3]
SOURCE_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_conformal_full_system"
)
if str(SOURCE_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_full_system as conformal  # noqa: E402


source = conformal.base


ACTIVE_BASE = (
    ROOT
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle/"
    "sand_cube_190x210_single_oval_port_base.step"
)
VALIDATOR_BASE = (
    ROOT
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure/"
    "sand_cube_190x210_single_oval_port_base.step"
)
DIAGNOSTICS = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/"
    "authoritative_base_diagnostics.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    _, provisional_brace_clearance = source._path_solids(
        185.0,
        outer_extra=source.D.brace_port_clearance,
    )
    _, provisional_install_clearance = source._path_solids(
        185.0,
        outer_extra=source.D.tube_install_clearance,
    )
    original_acoustic_domain = source._acoustic_domain
    original_front_brace_blends = source._front_brace_blends
    source._acoustic_domain = conformal._conformal_acoustic_domain
    source._front_brace_blends = conformal._conformal_front_brace_blends
    try:
        base = conformal._full_detail_base(
            provisional_brace_clearance,
            provisional_install_clearance,
        )
    finally:
        source._acoustic_domain = original_acoustic_domain
        source._front_brace_blends = original_front_brace_blends
    if len(base.solids()) != 1 or not base.is_valid:
        raise ValueError("Focused authoritative base is not one valid solid")

    records = {}
    for final_path in (ACTIVE_BASE, VALIDATOR_BASE):
        published = job_output_path(final_path)
        published.parent.mkdir(parents=True, exist_ok=True)
        export_step(base, published, unit=Unit.MM, write_pcurves=True)
        imported = import_step(published)
        imported_solids = imported.solids()
        imported_bounds = imported.bounding_box()
        records[str(final_path.relative_to(ROOT))] = {
            "sha256": _sha256(published),
            "source_solid_count": len(base.solids()),
            "imported_solid_count": len(imported_solids),
            "all_imported_solids_valid": all(
                solid.is_valid for solid in imported_solids
            ),
            "imported_volume_mm3": sum(
                solid.volume for solid in imported_solids
            ),
            "imported_face_count": len(imported.faces()),
            "imported_edge_count": len(imported.edges()),
            "imported_bounds_mm": {
                "min": [
                    imported_bounds.min.X,
                    imported_bounds.min.Y,
                    imported_bounds.min.Z,
                ],
                "max": [
                    imported_bounds.max.X,
                    imported_bounds.max.Y,
                    imported_bounds.max.Z,
                ],
            },
        }
    semantic_signatures = {
        (
            record["imported_solid_count"],
            record["all_imported_solids_valid"],
            round(record["imported_volume_mm3"], 6),
            record["imported_face_count"],
            record["imported_edge_count"],
            tuple(round(value, 6) for value in record["imported_bounds_mm"]["min"]),
            tuple(round(value, 6) for value in record["imported_bounds_mm"]["max"]),
        )
        for record in records.values()
    }
    if len(semantic_signatures) != 1:
        raise ValueError(
            "Two authoritative base round trips differ geometrically: "
            f"{records}"
        )

    bounds = base.bounding_box()
    diagnostics = {
        "source": str(SOURCE_EXPERIMENT.relative_to(ROOT)),
        "construction": (
            "source._path_solids clearances plus conformal._full_detail_base "
            "under the same conformal acoustic-domain/front-brace hooks used "
            "by conformal.generate; preview/cutaway stages intentionally not "
            "executed"
        ),
        "single_valid_solid": True,
        "volume_mm3": base.volume,
        "face_count": len(base.faces()),
        "edge_count": len(base.edges()),
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "outputs": records,
        "separate_step_serializations_semantically_identical": True,
        "separate_step_serializations_byte_identical": (
            len({record["sha256"] for record in records.values()}) == 1
        ),
    }
    diagnostics_path = job_output_path(DIAGNOSTICS)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
