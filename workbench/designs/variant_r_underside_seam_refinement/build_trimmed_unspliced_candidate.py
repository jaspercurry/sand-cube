"""Build the no-splice joint and shave only the sub-sole underside excess."""

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
import sys
from pathlib import Path
from typing import Any

from build123d import Align, Box, Compound, Pos


ROOT = Path(__file__).resolve().parents[3]
ITERATION = Path(__file__).resolve().parent
if str(ITERATION) not in sys.path:
    sys.path.insert(0, str(ITERATION))

import build_unspliced_candidate as support  # noqa: E402


model = support.model
SOURCE_BASE_STEP = support.SOURCE_BASE_STEP
OUT = ROOT / "build/workbench/variant_r_underside_seam_refinement/trimmed_candidate"
SOLE_Z_MM = -91.495


def _difference_volume(left: Any, right: Any) -> float:
    left_volume = support._shape_volume(left)
    if left_volume <= 1e-9:
        return 0.0
    if support._shape_volume(right) <= 1e-9:
        return left_volume
    return support._shape_volume(left.cut(right))


def _sole_trim(baffle: Any) -> tuple[Any, dict[str, Any]]:
    bounds = baffle.bounding_box()
    margin = 1.0
    trim_box = Pos(
        (bounds.min.X + bounds.max.X) / 2.0,
        (bounds.min.Y + bounds.max.Y) / 2.0,
        (SOLE_Z_MM + bounds.max.Z + margin) / 2.0,
    ) * Box(
        bounds.size.X + 2.0 * margin,
        bounds.size.Y + 2.0 * margin,
        bounds.max.Z + margin - SOLE_Z_MM,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    trimmed = model._single_solid(
        (baffle & trim_box).clean().fix(),
        feature="unspliced baffle with only sub-sole excess removed",
    )
    return trimmed, {
        "sole_z_mm": SOLE_Z_MM,
        "original_min_z_mm": min(vertex.Z for vertex in baffle.vertices()),
        "trimmed_min_z_mm": min(vertex.Z for vertex in trimmed.vertices()),
        "removed_volume_mm3": baffle.volume - trimmed.volume,
        "retained_volume_mm3": trimmed.volume,
        "removed_band_max_thickness_mm": (
            SOLE_Z_MM
            - min(vertex.Z for vertex in baffle.vertices())
        ),
    }


def main() -> None:
    if not SOURCE_BASE_STEP.is_file():
        raise FileNotFoundError(SOURCE_BASE_STEP)
    full_base = model._single_solid(
        support.import_step(SOURCE_BASE_STEP),
        feature="regenerated authoritative full-detail enclosure base",
    )
    print("trimmed candidate: authoritative base loaded", flush=True)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    original_perimeter = model.single._perimeter_wire
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        unspliced = model._AUTHORITATIVE_COMMON_JOINT(full_base)
    finally:
        model.single._perimeter_wire = original_perimeter
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder
    print("trimmed candidate: exact-edge unspliced joint built", flush=True)

    bucket = unspliced["bucket"]
    original_baffle = unspliced["baffle"]
    baffle, trim_audit = _sole_trim(original_baffle)
    gasket = unspliced["gasket"]
    overlap = support._shape_volume(bucket.intersect(baffle))
    if (
        len(bucket.solids()) != 1
        or len(baffle.solids()) != 1
        or not bucket.is_valid
        or not baffle.is_valid
        or overlap > model.MAX_ALLOWED_INTERFERENCE_MM3
    ):
        raise ValueError(
            "Trimmed no-splice candidate failed validity/overlap: "
            f"bucket_solids={len(bucket.solids())}, "
            f"baffle_solids={len(baffle.solids())}, "
            f"bucket_valid={bucket.is_valid}, baffle_valid={baffle.is_valid}, "
            f"overlap={overlap:.6f} mm3"
        )

    protected_difference = {
        "builder_claim": (
            "intersection keeps the half-space Z >= -91.495 mm; exported-B-rep "
            "surface/deviation audit is the acceptance authority above it"
        ),
        "original_volume_mm3": original_baffle.volume,
        "trimmed_volume_mm3": baffle.volume,
        "removed_volume_by_conservation_mm3": (
            original_baffle.volume - baffle.volume
        ),
        "permitted_max_z_mm": SOLE_Z_MM,
    }

    support.OUT = OUT
    outputs = {
        "trimmed_unspliced_bucket.step": bucket,
        "trimmed_unspliced_baffle.step": baffle,
        "trimmed_unspliced_gasket.step": gasket,
        "trimmed_unspliced_assembly.step": Compound(
            children=[bucket, baffle, gasket]
        ),
    }
    round_trip = {
        filename: support._export_and_round_trip(filename, shape)
        for filename, shape in outputs.items()
    }
    print_contact = support._print_contact(baffle)
    largest_contact = max(
        print_contact["contacts"],
        key=lambda item: item["area_mm2"],
        default=None,
    )
    if (
        largest_contact is None
        or largest_contact["x_span_mm"] < 187.020979 - 0.001
        or largest_contact["area_mm2"] < 2277.950023 - 0.001
    ):
        raise ValueError(
            "Trimmed candidate misses the current print-contact contract: "
            f"{print_contact}"
        )

    diagnostics = {
        "scope": "focused no-Z-splice candidate with underside-only sole trim",
        "source_base_step": str(SOURCE_BASE_STEP.relative_to(ROOT)),
        "construction": (
            "exact-edge unspliced authoritative joint; intersect only the "
            "0.355323 mm sub-sole baffle excess at Z=-91.495 mm; discard the "
            "removed underside band instead of transferring it to the bucket"
        ),
        "bucket": support._topology(bucket),
        "baffle": support._topology(baffle),
        "gasket": support._topology(gasket),
        "sole_trim": trim_audit,
        "protected_material_difference_at_or_above_sole": protected_difference,
        "bucket_baffle_overlap_mm3": overlap,
        "gasket_bucket_overlap_mm3": support._shape_volume(
            gasket.intersect(bucket)
        ),
        "gasket_baffle_overlap_mm3": support._shape_volume(
            gasket.intersect(baffle)
        ),
        "ancestor_state_restored": (
            model.single._perimeter_wire is original_perimeter
            and model.source.GASKET_CLOSED_GAP_MM == original_gap
            and model.source.SHOULDER_Y == original_shoulder
        ),
        "joint_audit": dict(model.previous._JOINT_AUDIT),
        "round_trip": round_trip,
    }
    diagnostics_path = job_output_path(OUT / "diagnostics.json")
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
