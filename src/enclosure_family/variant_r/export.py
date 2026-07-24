"""STEP publication and round-trip ownership for Variant R artifacts.

Geometry builders return shapes.  This adapter alone chooses the STEP settings,
routes published outputs through the coordinated job stage, reimports them,
and records the stable round-trip contract used by validation evidence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from build123d import Unit, export_step, import_step

from cad_runner.outputs import job_output_path


def publish_step_round_trip(
    step_path: Path,
    shape: Any,
    *,
    require_single_solid: bool,
) -> dict[str, Any]:
    """Atomically publish one STEP and fail closed on its imported topology."""

    published = job_output_path(step_path)
    published.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, published, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published)
    source_solids = tuple(shape.solids())
    imported_solids = tuple(imported.solids())
    result = {
        "source_solid_count": len(source_solids),
        "imported_solid_count": len(imported_solids),
        "all_imported_solids_valid": bool(imported_solids)
        and all(solid.is_valid for solid in imported_solids),
    }
    if (
        not result["all_imported_solids_valid"]
        or (
            require_single_solid
            and (
                result["source_solid_count"] != 1
                or result["imported_solid_count"] != 1
            )
        )
    ):
        raise ValueError(
            f"STEP round trip failed: {step_path.name}: {result}"
        )
    return result


def stabilize_single_solid(shape: Any, scratch_path: Path) -> Any:
    """Round-trip an intermediate shape without publishing it as evidence."""

    scratch_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, scratch_path, unit=Unit.MM, write_pcurves=True)
    try:
        imported = import_step(scratch_path)
    finally:
        scratch_path.unlink(missing_ok=True)
    solids = tuple(imported.solids())
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(
            f"{scratch_path.stem} section input failed STEP stabilization"
        )
    return solids[0]
