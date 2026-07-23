"""Build and validate the separate 160-degree rollback horn."""

from __future__ import annotations

# ruff: noqa: E402


# This guard must remain before all native CAD imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import hashlib
import json
from dataclasses import asdict
from math import isclose
from pathlib import Path
from typing import Any

from build123d import GeomType, Shape, Unit, import_step

from cad_runner.outputs import job_output_path
from src.cad_io import export_step
from workbench.designs.le_cleach_horn_190.model import build_horn
from workbench.designs.le_cleach_horn_190.variants.rollback_160.params import (
    PARAMS_160,
)


ROOT = _CAD_SAFETY_ROOT
OUTPUT_ROOT = (
    ROOT
    / "build/workbench/le_cleach_horn_190/variants/rollback_160"
)
BASELINE_STEP = (
    ROOT
    / "build/workbench/le_cleach_horn_190/variants/rollback_140/"
    "le_cleach_horn_190_rollback_140.step"
)


def _bbox(shape: Shape) -> dict[str, list[float]]:
    bbox = shape.bounding_box()
    return {
        "min_mm": [bbox.min.X, bbox.min.Y, bbox.min.Z],
        "max_mm": [bbox.max.X, bbox.max.Y, bbox.max.Z],
        "size_mm": [bbox.size.X, bbox.size.Y, bbox.size.Z],
    }


def _check(
    checks: list[dict[str, Any]],
    name: str,
    actual: float,
    expected: float,
    tolerance: float,
) -> None:
    checks.append(
        {
            "name": name,
            "passed": isclose(actual, expected, abs_tol=tolerance),
            "actual": actual,
            "expected": expected,
            "tolerance": tolerance,
        }
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    params = PARAMS_160
    baseline_sha_before = _sha256(BASELINE_STEP)
    solved = build_horn(params)
    horn = solved.horn
    bbox = _bbox(horn)
    physical_mouth_d = max(bbox["size_mm"][0], bbox["size_mm"][1])
    profile = solved.profile_metadata

    cylindrical_faces = horn.faces().filter_by(GeomType.CYLINDER)
    bolt_hole_faces = [
        face
        for face in cylindrical_faces
        if hasattr(face, "radius")
        and isclose(
            float(face.radius),
            params.bolt_clearance_d / 2.0,
            abs_tol=0.01,
        )
    ]

    checks: list[dict[str, Any]] = [
        {"name": "source_valid", "passed": bool(horn.is_valid)},
        {
            "name": "source_one_solid",
            "passed": len(horn.solids()) == 1,
            "actual": len(horn.solids()),
            "expected": 1,
        },
        {
            "name": "profile_method_exact_2007",
            "passed": profile["profile_method"] == "le_cleach_2007",
            "actual": profile["profile_method"],
            "expected": "le_cleach_2007",
        },
        {
            "name": "two_hole_pattern_only",
            "passed": (
                len(bolt_hole_faces) == 2
                and params.include_two_bolt_pattern
                and not params.include_three_bolt_pattern
            ),
            "actual_cylindrical_hole_face_count": len(bolt_hole_faces),
            "expected_cylindrical_hole_face_count": 2,
        },
        {
            "name": "baseline_140_artifact_preserved",
            "passed": _sha256(BASELINE_STEP) == baseline_sha_before,
            "sha256": baseline_sha_before,
        },
    ]
    _check(
        checks,
        "physical_mouth_envelope_d",
        physical_mouth_d,
        params.physical_mouth_target_d,
        0.01,
    )
    _check(
        checks,
        "target_axial_length",
        float(profile["axial_length_mm_exact"]),
        params.target_axial_length,
        0.001,
    )
    _check(
        checks,
        "direct_solver_axial_length",
        float(profile["direct_axial_length_mm"]),
        params.target_axial_length,
        params.axial_solve_tolerance,
    )
    _check(
        checks,
        "recurrence_terminal_angle",
        float(profile["recurrence_terminal_angle_deg"]),
        params.exit_angle_deg,
        0.001,
    )
    _check(
        checks,
        "cad_spline_terminal_tangent",
        float(profile["cad_spline_terminal_tangent_deg"]),
        params.exit_angle_deg,
        0.001,
    )
    checks.append(
        {
            "name": "cad_spline_max_profile_deviation",
            "passed": float(profile["cad_spline_max_profile_deviation_mm"])
            < 0.003,
            "actual": float(profile["cad_spline_max_profile_deviation_mm"]),
            "maximum": 0.003,
        }
    )

    out = job_output_path(OUTPUT_ROOT)
    out.mkdir(parents=True, exist_ok=True)
    step_path = out / "le_cleach_horn_190_rollback_160.step"
    export_step(horn, step_path, unit=Unit.MM, write_pcurves=True)

    imported = import_step(step_path)
    imported_bbox = _bbox(imported)
    checks.extend(
        [
            {
                "name": "step_round_trip_valid",
                "passed": bool(imported.is_valid),
            },
            {
                "name": "step_round_trip_one_solid",
                "passed": len(imported.solids()) == 1,
                "actual": len(imported.solids()),
                "expected": 1,
            },
        ]
    )
    _check(
        checks,
        "step_round_trip_volume",
        imported.volume,
        horn.volume,
        0.1,
    )
    _check(
        checks,
        "step_round_trip_physical_mouth_envelope_d",
        max(imported_bbox["size_mm"][0], imported_bbox["size_mm"][1]),
        params.physical_mouth_target_d,
        0.01,
    )

    passed = all(check["passed"] for check in checks)
    diagnostics = {
        "design": "le_cleach_horn_190_rollback_160",
        "status": "passed" if passed else "failed",
        "baseline_terminal_angle_deg": 140.0,
        "parameters": asdict(params),
        "solver": {
            "independent_input": "target_axial_length",
            "solved_wavefront_t": solved.wavefront_t,
            "solved_cutoff_hz": profile["solved_cutoff_hz_exact"],
            "spreadsheet_row_step_mm": profile["calculation_step_mm"],
            "sample_count": profile["sample_count"],
        },
        "profile": profile,
        "geometry": {
            "source_bbox": bbox,
            "step_round_trip_bbox": imported_bbox,
            "source_volume_mm3": horn.volume,
            "step_round_trip_volume_mm3": imported.volume,
            "source_face_count": len(horn.faces()),
            "step_round_trip_face_count": len(imported.faces()),
            "bolt_hole_cylindrical_face_count": len(bolt_hole_faces),
        },
        "checks": checks,
        "outputs": {
            "step": (
                "build/workbench/le_cleach_horn_190/variants/rollback_160/"
                "le_cleach_horn_190_rollback_160.step"
            ),
            "step_sha256": _sha256(step_path),
            "baseline_140_step_sha256": baseline_sha_before,
        },
    }
    diagnostics_path = out / "diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("160-degree rollback geometry contract failed")


if __name__ == "__main__":
    main()
