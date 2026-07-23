"""Run staged, cache-verified checks against one published candidate."""

# ruff: noqa: E402

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

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
from time import perf_counter
from typing import Any

from cad_runner.cache import (
    DeclaredOutput,
    StageCache,
    StageCacheSpec,
    ToolIdentity,
    fingerprint_file,
)
from cad_runner.outputs import STAGE_ROOT_ENV, job_output_path
from cad_verification import (
    ActualValue,
    EvidenceChannel,
    ResultStatus,
    Unit,
    VerificationProfile,
    WorkflowStage,
    assess,
    assert_valid_contract,
    contract_fingerprint,
    contract_to_dict,
    gate_profile,
    load_iteration,
    profile_status,
    requirements_for_profile,
)
from experiments.sand_cube_190x210_single_oval_port.verification import (
    FIT_IMPORTS,
    FIT_INTERSECTION_PAIRS,
    GENERATOR,
    OUT,
    ROOT,
    STEP_OUTPUTS,
    bind_candidate,
    design_contract,
    validate_candidate,
    validate_visual_acceptance,
)


PRODUCER_VERSION = "1"
PRODUCER_SCHEMA_VERSION = 1
MEASUREMENT_OUTPUT = DeclaredOutput(
    "measurements",
    "artifacts/measurements.json",
)
DEFAULT_CANDIDATE = OUT / "verification" / "candidate.json"
DEFAULT_WORKFLOW = (
    ROOT / "workbench/designs/cad_feedback_loop_rollout/state.json"
)


def _installed_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def _tools() -> tuple[ToolIdentity, ...]:
    return (
        ToolIdentity(
            "python",
            platform.python_version(),
            _cad_safety_sys.implementation.cache_tag
            or platform.python_implementation(),
        ),
        ToolIdentity(
            "build123d",
            _installed_version("build123d"),
            "project-pinned-native-kernel",
        ),
        ToolIdentity(
            "cadquery-ocp-novtk",
            _installed_version("cadquery-ocp-novtk"),
            "project-pinned-native-kernel",
        ),
    )


def _repo_path(value: Path, *, must_exist: bool = True) -> Path:
    candidate = value.expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve(strict=must_exist)
    try:
        candidate.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"path escapes repository root: {candidate}") from error
    return candidate


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _cache_spec(
    profile: VerificationProfile,
    candidate_path: Path,
    candidate: dict[str, Any],
    identity_source: Path | None,
) -> StageCacheSpec:
    source_paths = [
        candidate_path,
        GENERATOR,
        Path(__file__),
        Path(__file__).with_name("verification.py"),
        ROOT / "cad_geometry_checks/native/measurements.py",
        ROOT / "cad_geometry_checks/model.py",
        ROOT / "cad_verification/policy.py",
        *(ROOT / output["path"] for output in candidate["outputs"]),
    ]
    if identity_source is not None:
        source_paths.append(identity_source)
    return StageCacheSpec(
        stage=f"single-oval-port-{profile.value}-measurements",
        producer="single-oval-port-verifier",
        producer_version=PRODUCER_VERSION,
        producer_schema_version=PRODUCER_SCHEMA_VERSION,
        sources=tuple(fingerprint_file(ROOT, path) for path in source_paths),
        parameters={
            "candidate_id": candidate["candidate_id"],
            "profile": profile.value,
        },
        tools=_tools(),
        settings={
            "fit_imports": FIT_IMPORTS,
            "fit_intersection_pairs": FIT_INTERSECTION_PAIRS,
            "release_imports": STEP_OUTPUTS,
            "artifact_import_policy": "once-per-stage",
        },
        outputs=(MEASUREMENT_OUTPUT,),
    )


def _native_measurements(
    profile: VerificationProfile,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    from build123d import import_step
    from cad_geometry_checks.native import measure_intersection, summarize_topology

    names = FIT_IMPORTS if profile is VerificationProfile.FIT else STEP_OUTPUTS
    by_name = {item["name"]: item for item in candidate["outputs"]}
    imported = {
        name: import_step(ROOT / by_name[name]["path"])
        for name in names
    }
    topology = {}
    topology_usable = True
    for name, shape in imported.items():
        summary = summarize_topology(shape)
        usable = summary.diagnostic.usable
        topology_usable = topology_usable and usable
        topology[name] = {
            "usable": usable,
            "diagnostic": summary.diagnostic.describe(),
            "shape_count": summary.shape_count,
            "solid_count": summary.solid_count,
            "shell_count": summary.shell_count,
            "face_count": summary.face_count,
            "edge_count": summary.edge_count,
            "boundary_edge_count": summary.boundary_edge_count,
            "non_manifold_edge_count": summary.non_manifold_edge_count,
        }

    intersections = {}
    for name, left, right in FIT_INTERSECTION_PAIRS:
        measured = measure_intersection(imported[left], imported[right])
        if not measured.diagnostic.usable or measured.volume_mm3 is None:
            raise RuntimeError(
                f"{name} intersection is unusable: "
                f"{measured.diagnostic.describe()}"
            )
        intersections[name] = {
            "volume_mm3": measured.volume_mm3,
            "outcome": measured.outcome.value,
            "diagnostic": measured.diagnostic.describe(),
        }
    return {
        "schema_version": PRODUCER_SCHEMA_VERSION,
        "profile": profile.value,
        "candidate_id": candidate["candidate_id"],
        "artifact_import_count": len(imported),
        "artifact_imports": list(imported),
        "topology_usable": topology_usable,
        "topology": topology,
        "intersections": intersections,
    }


def _actuals(
    profile: VerificationProfile,
    candidate: dict[str, Any],
    measurements: dict[str, Any] | None,
    visual_refs: tuple[str, ...],
) -> dict[
    str,
    tuple[ActualValue, str, tuple[str, ...], EvidenceChannel],
]:
    artifact_refs = tuple(item["path"] for item in candidate["outputs"])
    values: dict[
        str,
        tuple[ActualValue, str, tuple[str, ...], EvidenceChannel],
    ] = {
        "artifact.output_count": (
            ActualValue(len(candidate["outputs"]), unit=Unit.COUNT),
            "Candidate binds the complete production STEP output set.",
            artifact_refs,
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        ),
        "artifact.candidate_current": (
            ActualValue(True, unit=Unit.BOOLEAN),
            "Candidate identities were recomputed from current published files.",
            artifact_refs,
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        ),
    }
    if measurements is not None:
        for name, measured in measurements["intersections"].items():
            values[f"kernel.{name}_intersection"] = (
                ActualValue(
                    measured["volume_mm3"],
                    unit=Unit.CUBIC_MILLIMETER,
                ),
                measured["diagnostic"],
                (name,),
                EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            )
        values["kernel.fit_topology_usable"] = (
            ActualValue(
                measurements["topology_usable"],
                unit=Unit.BOOLEAN,
            ),
            (
                f"All {measurements['artifact_import_count']} stage imports "
                "produced usable topology summaries."
            ),
            tuple(measurements["artifact_imports"]),
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        )
    if profile is VerificationProfile.RELEASE:
        roundtrip_ok = all(
            item["roundtrip"]["solid_count_matches"]
            and item["roundtrip"]["all_imported_solids_valid"]
            for item in candidate["outputs"]
        )
        values["artifact.step_round_trip"] = (
            ActualValue(roundtrip_ok, unit=Unit.BOOLEAN),
            "Production diagnostics retain passing solid-count and validity checks.",
            artifact_refs,
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        )
        values["artifact.integrity"] = (
            ActualValue(True, unit=Unit.BOOLEAN),
            "Current artifact hashes exactly match the release candidate.",
            artifact_refs,
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        )
        values["review.visual_smoke_accepted"] = (
            ActualValue(True, unit=Unit.BOOLEAN),
            (
                "The compact workflow contains hash-bound visual-accepted "
                "evidence for this unchanged candidate revision."
            ),
            visual_refs,
            EvidenceChannel.FOCUSED_RENDERER,
        )
    return values


def _result_dict(result) -> dict[str, Any]:
    actual = None
    if result.actual is not None:
        actual = {
            "value": result.actual.value,
            "unit": result.actual.unit.value,
        }
    return {
        "requirement_id": result.requirement_id,
        "status": result.status.value,
        "actual": actual,
        "evidence_channel": result.evidence_channel.value,
        "diagnostic": result.diagnostic,
        "evidence_refs": list(result.evidence_refs),
    }


def _evaluate(
    profile: VerificationProfile,
    candidate: dict[str, Any],
    measurements: dict[str, Any] | None,
    visual_refs: tuple[str, ...],
) -> tuple[object, ...]:
    contract = design_contract()
    actuals = _actuals(profile, candidate, measurements, visual_refs)
    results = []
    for requirement in requirements_for_profile(contract, profile):
        actual, diagnostic, refs, channel = actuals[requirement.check.adapter]
        results.append(
            assess(
                requirement,
                actual,
                evidence_channel=channel,
                diagnostic=diagnostic,
                evidence_refs=refs,
            )
        )
    return tuple(results)


def _require_workflow_gate(profile: VerificationProfile, state_path: Path):
    state = load_iteration(state_path)
    decision = gate_profile(state, profile, root=ROOT)
    if not decision.allowed:
        raise RuntimeError(decision.reason)
    return state


def run(args: argparse.Namespace) -> dict[str, Any]:
    profile = VerificationProfile(args.profile)
    state_path = _repo_path(args.workflow_state)
    state = _require_workflow_gate(profile, state_path)
    contract = design_contract()
    assert_valid_contract(contract)
    candidate_path = _repo_path(args.candidate, must_exist=profile is not VerificationProfile.FAST)
    if profile is VerificationProfile.FAST:
        candidate = bind_candidate()
        staged_candidate = job_output_path(candidate_path)
        _write_json(staged_candidate, candidate)
        cache_info = {
            "status": "not_applicable",
            "reason": "fast_candidate_binding",
            "key": None,
        }
        measurements = None
        measurement_seconds = 0.0
    else:
        candidate = _load_json(candidate_path)
        validate_candidate(candidate)
        identity_source = (
            _repo_path(args.identity_source) if args.identity_source else None
        )
        spec = _cache_spec(profile, candidate_path, candidate, identity_source)
        cache = StageCache(ROOT)
        stage_root = Path(os.environ[STAGE_ROOT_ENV]).resolve()
        scratch = stage_root.parent / "scratch" / profile.value
        scratch.mkdir(parents=True, exist_ok=True)
        cached_measurements = scratch / "measurements.json"
        restored = None if args.force else cache.restore(
            spec,
            {"measurements": cached_measurements},
        )
        if restored is not None and restored.hit:
            measurements = _load_json(cached_measurements)
            measurement_seconds = 0.0
            cache_info = {
                "status": "hit",
                "reason": restored.reason,
                "key": restored.key,
            }
        else:
            started = perf_counter()
            measurements = _native_measurements(profile, candidate)
            measurement_seconds = perf_counter() - started
            _write_json(cached_measurements, measurements)
            published = cache.publish(
                spec,
                {"measurements": cached_measurements},
                replace=bool(args.force),
            )
            cache_info = {
                "status": "forced_regeneration" if args.force else "published",
                "reason": (
                    "force_regeneration"
                    if args.force
                    else restored.reason if restored is not None else "entry_missing"
                ),
                "key": published.key,
            }

    visual_evidence = tuple(
        (identity.path, identity.sha256)
        for evidence in state.evidence
        if evidence.stage is WorkflowStage.VISUAL_ACCEPTED
        for identity in evidence.files
    )
    visual_refs = (
        validate_visual_acceptance(candidate, visual_evidence)
        if profile is VerificationProfile.RELEASE
        else tuple(path for path, _sha256 in visual_evidence)
    )
    results = _evaluate(profile, candidate, measurements, visual_refs)
    status = profile_status(contract, profile, results)
    if status is not ResultStatus.PASS:
        failures = [
            result.requirement_id
            for result in results
            if result.status is not ResultStatus.PASS
        ]
        raise RuntimeError(f"{profile.value} verification failed: {failures}")
    report = {
        "schema_version": 1,
        "profile": profile.value,
        "status": status.value,
        "forced_uncached": bool(args.force),
        "candidate": {
            "path": candidate_path.relative_to(ROOT).as_posix(),
            "candidate_id": candidate["candidate_id"],
        },
        "contract": contract_to_dict(contract),
        "contract_fingerprint": contract_fingerprint(contract),
        "cache": cache_info,
        "measurement_seconds": measurement_seconds,
        "measurements": measurements,
        "results": [_result_dict(result) for result in results],
    }
    output = job_output_path(_repo_path(args.out, must_exist=False))
    _write_json(output, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one gated verification profile against one candidate."
    )
    parser.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        required=True,
    )
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--workflow-state", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--identity-source", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    profile = VerificationProfile(args.profile)
    if profile is VerificationProfile.RELEASE and not args.force:
        raise SystemExit("release verification requires --force")
    if args.out is None:
        args.out = OUT / "verification" / f"{profile.value}-evidence.json"
    print(json.dumps(run(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
