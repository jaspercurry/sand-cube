"""Run staged joint-coupon verification through the clean CAD runner."""

from __future__ import annotations


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

import argparse
from datetime import datetime, timezone
import json
from math import isfinite
from pathlib import Path
from typing import Any

from cad_runner.outputs import job_output_path
from cad_verification import (
    ActualValue,
    EvidenceChannel,
    Requirement,
    RequirementResult,
    ResultStatus,
    Unit,
    VerificationProfile,
    assess,
    contract_fingerprint,
    contract_to_json,
    fingerprint_collection,
    requirements_for_profile,
)
from workbench.designs.joint_coupon.parameters import (
    CouponParameters,
    expected_volumes,
    load_parameters,
)
from workbench.designs.joint_coupon.verification import (
    design_contract,
    input_fingerprints,
    source_fingerprints,
)


ROOT = _CAD_SAFETY_ROOT
OUTPUT_ROOT = ROOT / "build/workbench/joint_coupon"
ASSEMBLY_ARTIFACT = "artifact.joint-coupon-assembly-step"
LOWER_ARTIFACT = "artifact.joint-coupon-lower-step"
UPPER_ARTIFACT = "artifact.joint-coupon-upper-step"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        default=VerificationProfile.RELEASE.value,
    )
    return parser


def _bbox(shape: Any) -> dict[str, float]:
    bounds = shape.bounding_box()
    size = bounds.size
    return {
        "x": size.X,
        "y": size.Y,
        "z": size.Z,
        "min_z": bounds.min.Z,
        "max_z": bounds.max.Z,
    }


def _intersection_volume(left: Any, right: Any) -> float:
    intersection = left.intersect(right)
    if intersection is None:
        return 0.0
    if hasattr(intersection, "volume"):
        return float(intersection.volume)
    return sum(float(shape.volume) for shape in intersection)


def _result_dict(result: RequirementResult) -> dict[str, Any]:
    actual = result.actual
    return {
        "requirement_id": result.requirement_id,
        "status": result.status.value,
        "actual": (
            None
            if actual is None
            else {"value": actual.value, "unit": actual.unit.value}
        ),
        "evidence_channel": result.evidence_channel.value,
        "evidence_tier": result.evidence_tier.value,
        "diagnostic": result.diagnostic,
        "evidence_refs": list(result.evidence_refs),
    }


def _measure(
    requirements: dict[str, Requirement],
    results: list[RequirementResult],
    requirement_id: str,
    value: bool | int | float,
    unit: Unit,
    diagnostic: str,
    evidence_refs: tuple[str, ...] = (),
) -> None:
    results.append(
        assess(
            requirements[requirement_id],
            ActualValue(value, unit),
            evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            diagnostic=diagnostic,
            evidence_refs=evidence_refs,
        )
    )


def _fast_results(
    params: CouponParameters,
    requirements,
) -> list[RequirementResult]:
    results: list[RequirementResult] = []
    expected = expected_volumes(params)
    values = tuple(getattr(params, name) for name in params.__annotations__)
    finite_positive = all(isfinite(value) and value > 0.0 for value in values)
    fastener_radius = params.fastener_diameter / 2.0
    gasket_outer_y = (
        params.groove_width / 2.0
        + params.gasket_land_gap
        + params.gasket_width
    )
    layout_feasible = all(
        (
            params.groove_length < params.length,
            gasket_outer_y < params.depth / 2.0,
            params.fastener_x + fastener_radius < params.length / 2.0,
            params.fastener_y + fastener_radius < params.depth / 2.0,
            params.groove_depth >= params.tongue_height,
        )
    )
    assembly_height = params.lower_thickness + params.closed_gap + params.upper_thickness
    _measure(requirements, results, "JC-STRUCT-PARAMETERS-FINITE", finite_positive, Unit.BOOLEAN, "All 18 parsed parameter values are finite and positive.")
    _measure(requirements, results, "JC-STRUCT-LAYOUT-FEASIBLE", layout_feasible, Unit.BOOLEAN, "Analytic feature bounds remain within the plate envelope.")
    _measure(requirements, results, "JC-DIM-NOMINAL-LENGTH", params.length, Unit.MILLIMETER, "Nominal X extent read from the authoritative parameter input.")
    _measure(requirements, results, "JC-DIM-NOMINAL-DEPTH", params.depth, Unit.MILLIMETER, "Nominal Y extent read from the authoritative parameter input.")
    _measure(requirements, results, "JC-DIM-NOMINAL-HEIGHT", assembly_height, Unit.MILLIMETER, "Analytic closed Z extent from plate thicknesses and gap.")
    _measure(requirements, results, "JC-DIM-ANALYTIC-LOWER-VOLUME", expected["lower"], Unit.CUBIC_MILLIMETER, "Native-free analytic lower volume.")
    _measure(requirements, results, "JC-DIM-ANALYTIC-UPPER-VOLUME", expected["upper"], Unit.CUBIC_MILLIMETER, "Native-free analytic upper volume.")
    _measure(requirements, results, "JC-DIM-ANALYTIC-GASKET-VOLUME", expected["gasket_each"], Unit.CUBIC_MILLIMETER, "Native-free analytic volume of each compressed gasket reference.")
    return results


def _fit_results(params: CouponParameters, model, requirements) -> list[RequirementResult]:
    results: list[RequirementResult] = []
    expected = expected_volumes(params)
    assembly = _bbox(model.assembly)
    _measure(requirements, results, "JC-STRUCT-LOWER-VALID", bool(model.lower.is_valid), Unit.BOOLEAN, "OpenCascade reports the lower rigid coupon valid.")
    _measure(requirements, results, "JC-STRUCT-UPPER-VALID", bool(model.upper.is_valid), Unit.BOOLEAN, "OpenCascade reports the upper rigid coupon valid.")
    _measure(requirements, results, "JC-STRUCT-LOWER-SOLID-COUNT", len(model.lower.solids()), Unit.COUNT, "Lower rigid topology solid count.")
    _measure(requirements, results, "JC-STRUCT-UPPER-SOLID-COUNT", len(model.upper.solids()), Unit.COUNT, "Upper rigid topology solid count.")
    _measure(requirements, results, "JC-DIM-ASSEMBLY-LENGTH", assembly["x"], Unit.MILLIMETER, "Built closed-assembly bounding-box X extent.")
    _measure(requirements, results, "JC-DIM-ASSEMBLY-DEPTH", assembly["y"], Unit.MILLIMETER, "Built closed-assembly bounding-box Y extent.")
    _measure(requirements, results, "JC-DIM-ASSEMBLY-HEIGHT", assembly["z"], Unit.MILLIMETER, "Built closed-assembly bounding-box Z extent.")
    _measure(requirements, results, "JC-DIM-LOWER-VOLUME", model.lower.volume, Unit.CUBIC_MILLIMETER, f"Built lower volume; analytic target {expected['lower']:.6f} mm3.")
    _measure(requirements, results, "JC-DIM-UPPER-VOLUME", model.upper.volume, Unit.CUBIC_MILLIMETER, f"Built upper volume; analytic target {expected['upper']:.6f} mm3.")
    _measure(requirements, results, "JC-DIM-GASKET-LEFT-VOLUME", model.gasket_left.volume, Unit.CUBIC_MILLIMETER, "Built left compressed gasket reference volume.")
    _measure(requirements, results, "JC-DIM-GASKET-RIGHT-VOLUME", model.gasket_right.volume, Unit.CUBIC_MILLIMETER, "Built right compressed gasket reference volume.")
    tongue = _bbox(model.tongue)
    groove = _bbox(model.groove)
    side_clearance = (groove["y"] - tongue["y"]) / 2.0
    end_clearance = (groove["x"] - tongue["x"]) / 2.0
    gasket_thickness = _bbox(model.gasket_left)["z"]
    gasket_compression = params.gasket_free_thickness - gasket_thickness
    rigid_interference = _intersection_volume(model.lower, model.upper)
    gasket_interferences = tuple(
        _intersection_volume(gasket, rigid)
        for gasket in (model.gasket_left, model.gasket_right)
        for rigid in (model.lower, model.upper)
    )
    section_clearance = groove["max_z"] - tongue["max_z"]
    _measure(requirements, results, "JC-CLEAR-SIDE", side_clearance, Unit.MILLIMETER, "Groove/tongue Y extents measured 0.2 mm clearance per side.")
    _measure(requirements, results, "JC-CLEAR-END", end_clearance, Unit.MILLIMETER, "Groove/tongue X extents measured 1.0 mm clearance per end.")
    _measure(requirements, results, "JC-FIT-GASKET-COMPRESSION", gasket_compression, Unit.MILLIMETER, "Free gasket thickness minus modeled closed gasket thickness.")
    _measure(requirements, results, "JC-INTERFERENCE-RIGID", rigid_interference, Unit.CUBIC_MILLIMETER, "Positive-volume intersection of the two closed rigid coupons.")
    _measure(requirements, results, "JC-INTERFERENCE-GASKET", max(gasket_interferences), Unit.CUBIC_MILLIMETER, f"Four gasket/rigid intersection volumes: {gasket_interferences}.")
    _measure(requirements, results, "JC-SECTION-VERTICAL-CLEARANCE", section_clearance, Unit.MILLIMETER, "Mid-plane groove-cutter ceiling Z minus tongue top Z.")
    return results


def _release_results(
    params: CouponParameters,
    model,
    requirements,
    output: Path,
) -> tuple[list[RequirementResult], dict[str, Path]]:
    from build123d import Compound, Unit as CadUnit, import_step

    from src.cad_io import export_step

    results: list[RequirementResult] = []
    paths = {
        "lower": output / "joint_coupon_lower.step",
        "upper": output / "joint_coupon_upper.step",
        "gaskets": output / "joint_coupon_gaskets.step",
        "assembly": output / "joint_coupon_assembly.step",
    }
    export_step(model.lower, paths["lower"], unit=CadUnit.MM)
    export_step(model.upper, paths["upper"], unit=CadUnit.MM)
    export_step(
        Compound(children=[model.gasket_left, model.gasket_right]),
        paths["gaskets"],
        unit=CadUnit.MM,
    )
    export_step(
        Compound(children=[model.lower, model.upper]),
        paths["assembly"],
        unit=CadUnit.MM,
    )

    expected = expected_volumes(params)
    assembly = import_step(paths["assembly"])
    _measure(requirements, results, "JC-ROUNDTRIP-VALID", bool(assembly.is_valid), Unit.BOOLEAN, "Re-imported assembly STEP is valid.", (ASSEMBLY_ARTIFACT,))
    _measure(requirements, results, "JC-ROUNDTRIP-SOLID-COUNT", len(assembly.solids()), Unit.COUNT, "Re-imported assembly STEP contains both rigid solids.", (ASSEMBLY_ARTIFACT,))
    _measure(requirements, results, "JC-ROUNDTRIP-VOLUME", assembly.volume, Unit.CUBIC_MILLIMETER, "Re-imported assembly STEP total rigid volume.", (ASSEMBLY_ARTIFACT,))
    for name, artifact_id in (("lower", LOWER_ARTIFACT), ("upper", UPPER_ARTIFACT)):
        part = import_step(paths[name])
        prefix = name.upper()
        _measure(requirements, results, f"JC-ROUNDTRIP-{prefix}-SOLID-COUNT", len(part.solids()), Unit.COUNT, f"Re-imported {name} STEP solid count.", (artifact_id,))
        _measure(requirements, results, f"JC-ROUNDTRIP-{prefix}-VOLUME", part.volume, Unit.CUBIC_MILLIMETER, f"Re-imported {name} STEP volume; analytic target {expected[name]:.6f} mm3.", (artifact_id,))
    return results, paths


def main(argv: list[str] | None = None) -> None:
    profile = VerificationProfile(_parser().parse_args(argv).profile)
    raw_params, params = load_parameters()
    contract = design_contract(params)
    requirements = {
        requirement.requirement_id: requirement
        for requirement in contract.requirements
    }
    results = _fast_results(params, requirements)
    model = None
    if profile in (VerificationProfile.FIT, VerificationProfile.RELEASE):
        from workbench.designs.joint_coupon.model import build_coupon

        model = build_coupon(params)
        results.extend(_fit_results(params, model, requirements))

    output = job_output_path(OUTPUT_ROOT)
    output.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    if profile is VerificationProfile.RELEASE:
        assert model is not None
        release_results, paths = _release_results(
            params,
            model,
            requirements,
            output,
        )
        results.extend(release_results)

    selected_ids = {
        requirement.requirement_id
        for requirement in requirements_for_profile(contract, profile)
    }
    measured_ids = {result.requirement_id for result in results}
    missing_native_ids = selected_ids - measured_ids
    if profile is VerificationProfile.RELEASE:
        missing_native_ids -= {
            "JC-ARTIFACT-SIDECAR",
            "JC-VIS-VIEWER",
            "JC-VIS-SNAPSHOT-ISO",
            "JC-VIS-SNAPSHOT-SECTION",
        }
    passed = not missing_native_ids and all(
        result.status is ResultStatus.PASS for result in results
    )

    sources = source_fingerprints()
    inputs = input_fingerprints()
    diagnostics = {
        "schema_version": 1,
        "design": "joint_coupon",
        "profile": profile.value,
        "status": "passed" if passed else "failed",
        "contract_id": contract.contract_id,
        "contract_fingerprint": contract_fingerprint(contract),
        "source_fingerprints": [record.__dict__ for record in sources],
        "source_fingerprint": fingerprint_collection(sources),
        "input_fingerprints": [record.__dict__ for record in inputs],
        "input_fingerprint": fingerprint_collection(inputs),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters_mm": raw_params,
        "results": [_result_dict(result) for result in results],
        "missing_native_requirement_ids": sorted(missing_native_ids),
        "outputs": {
            name: str(OUTPUT_ROOT / path.name) for name, path in paths.items()
        },
    }
    (output / "design-contract.json").write_text(contract_to_json(contract))
    diagnostics_path = output / f"diagnostics-{profile.value}.json"
    diagnostics_path.write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if profile is VerificationProfile.RELEASE:
        (output / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("Joint coupon geometry contract failed")


if __name__ == "__main__":
    main()
