"""Native-free contract and candidate identity for the single-oval-port rollout."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from cad_verification import (
    CheckKind,
    CheckSpec,
    DesignContract,
    Expectation,
    ModelIdentity,
    Requirement,
    Tolerance,
    Unit,
    VerificationProfile,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL_ID = "exp-190x210-single-oval-port"
GENERATOR = (
    ROOT
    / "experiments/sand_cube_190x210_single_oval_port/"
    "generate_sand_cube_190x210_single_oval_port.py"
)
OUT = ROOT / "build" / "sand_cube_190x210_single_oval_port"
CANDIDATE_SCHEMA_VERSION = 1
STEP_OUTPUTS = (
    "sand_cube_190x210_single_oval_port_base.step",
    "sand_cube_190x210_single_oval_port_internal_tube.step",
    "sand_cube_190x210_single_oval_port_tower.step",
    "sand_cube_190x210_single_oval_port_airway.step",
    "sand_cube_190x210_single_oval_port_gx16.step",
    "sand_cube_190x210_single_oval_port_horn.step",
    "sand_cube_190x210_single_oval_port_assembly.step",
    "sand_cube_190x210_single_oval_port_hardware_check.step",
    "sand_cube_190x210_single_oval_port_cutaway.step",
)
FIT_IMPORTS = (
    "sand_cube_190x210_single_oval_port_base.step",
    "sand_cube_190x210_single_oval_port_internal_tube.step",
    "sand_cube_190x210_single_oval_port_tower.step",
    "sand_cube_190x210_single_oval_port_airway.step",
    "sand_cube_190x210_single_oval_port_horn.step",
)
FIT_INTERSECTION_PAIRS = (
    (
        "base_to_tower",
        "sand_cube_190x210_single_oval_port_base.step",
        "sand_cube_190x210_single_oval_port_tower.step",
    ),
    (
        "base_to_internal_tube",
        "sand_cube_190x210_single_oval_port_base.step",
        "sand_cube_190x210_single_oval_port_internal_tube.step",
    ),
    (
        "internal_tube_to_airway",
        "sand_cube_190x210_single_oval_port_internal_tube.step",
        "sand_cube_190x210_single_oval_port_airway.step",
    ),
    (
        "tower_to_airway",
        "sand_cube_190x210_single_oval_port_tower.step",
        "sand_cube_190x210_single_oval_port_airway.step",
    ),
    (
        "tower_to_horn",
        "sand_cube_190x210_single_oval_port_tower.step",
        "sand_cube_190x210_single_oval_port_horn.step",
    ),
)
REVIEW_TARGET = (
    "experiments/sand_cube_190x210_single_oval_port/"
    "review_sand_cube_190x210_single_oval_port.py"
)
SNAPSHOT_TARGET = "scripts/text_to_cad_artifacts.py"


@dataclass(frozen=True)
class VisualAcceptanceBinding:
    evidence_refs: tuple[str, ...]
    step_path: str
    step_sha256: str
    sidecar_path: str
    sidecar_sha256: str
    sidecar_size_bytes: int
    sidecar_kind: str
    sidecar_cache_key: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _relative(path: Path, root: Path) -> str:
    return path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()


def _load_diagnostics(output_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = output_dir / "diagnostics.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("production diagnostics must be a JSON object")
    return path, payload


def bind_candidate(
    *,
    repo_root: Path = ROOT,
    artifact_dir: Path = OUT,
    generator: Path = GENERATOR,
) -> dict[str, Any]:
    """Bind the exact published production output set into one candidate."""

    repo_root = repo_root.resolve(strict=True)
    artifact_dir = artifact_dir.resolve(strict=True)
    diagnostics_path, diagnostics = _load_diagnostics(artifact_dir)
    roundtrip = diagnostics.get("geometry", {}).get("step_roundtrip")
    if not isinstance(roundtrip, dict):
        raise ValueError("production diagnostics have no STEP round-trip map")
    if set(roundtrip) != set(STEP_OUTPUTS):
        raise ValueError("production STEP round-trip map does not match output contract")

    outputs = []
    for filename in STEP_OUTPUTS:
        check = roundtrip[filename]
        if not isinstance(check, dict) or not (
            check.get("solid_count_matches") is True
            and check.get("all_imported_solids_valid") is True
        ):
            raise ValueError(f"production STEP round-trip is not passing: {filename}")
        path = artifact_dir / filename
        outputs.append(
            {
                "name": filename,
                "path": _relative(path, repo_root),
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
                "roundtrip": {
                    "source_solid_count": check.get("source_solid_count"),
                    "imported_solid_count": check.get("imported_solid_count"),
                    "solid_count_matches": True,
                    "all_imported_solids_valid": True,
                },
            }
        )
    identity = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "model_id": MODEL_ID,
        "generator": {
            "path": _relative(generator, repo_root),
            "sha256": _sha256_file(generator),
        },
        "diagnostics": {
            "path": _relative(diagnostics_path, repo_root),
            "sha256": _sha256_file(diagnostics_path),
            "size_bytes": diagnostics_path.stat().st_size,
        },
        "outputs": outputs,
    }
    return {
        **identity,
        "candidate_id": hashlib.sha256(_canonical_bytes(identity)).hexdigest(),
    }


def validate_candidate(
    candidate: dict[str, Any],
    *,
    repo_root: Path = ROOT,
) -> None:
    expected = bind_candidate(
        repo_root=repo_root,
        artifact_dir=repo_root / "build/sand_cube_190x210_single_oval_port",
    )
    if candidate != expected:
        raise ValueError(
            "candidate is stale or does not bind the current production outputs"
        )


def validate_visual_acceptance(
    candidate: dict[str, Any],
    evidence_files: Iterable[tuple[str, str]],
    *,
    repo_root: Path = ROOT,
) -> VisualAcceptanceBinding:
    """Bind accepted visual evidence to the exact current candidate and STEP."""

    repo_root = repo_root.resolve(strict=True)
    evidence = dict(evidence_files)
    acceptance_paths = tuple(
        path for path in evidence if Path(path).name == "visual-acceptance.json"
    )
    if len(acceptance_paths) != 1:
        raise ValueError("visual evidence must contain one acceptance record")
    acceptance_path = acceptance_paths[0]
    acceptance_file = repo_root / acceptance_path
    if _sha256_file(acceptance_file) != evidence[acceptance_path]:
        raise ValueError("visual acceptance record does not match workflow evidence")
    acceptance = json.loads(acceptance_file.read_text(encoding="utf-8"))
    if not isinstance(acceptance, dict):
        raise ValueError("visual acceptance record must be a JSON object")
    if acceptance.get("accepted") is not True:
        raise ValueError("visual acceptance record is not accepted")
    if acceptance.get("channel") != "snapshot":
        raise ValueError("visual acceptance did not use the Snapshot channel")
    if acceptance.get("candidate_id") != candidate.get("candidate_id"):
        raise ValueError("visual acceptance belongs to a different candidate")
    if acceptance.get("measurable_claims_from_pixels") != []:
        raise ValueError("visual acceptance must not make measurable pixel claims")

    referenced_paths = []
    for field in (
        "snapshot",
        "snapshot_provenance",
        "static_review_provenance",
    ):
        reference = acceptance.get(field)
        if not isinstance(reference, dict):
            raise ValueError(f"visual acceptance has no {field} reference")
        path = reference.get("path")
        digest = reference.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str):
            raise ValueError(f"visual acceptance has an invalid {field} reference")
        if evidence.get(path) != digest:
            raise ValueError(f"{field} is not the exact workflow evidence")
        if _sha256_file(repo_root / path) != digest:
            raise ValueError(f"{field} content does not match its accepted hash")
        referenced_paths.append(path)

    static_review = json.loads(
        (repo_root / referenced_paths[2]).read_text(encoding="utf-8")
    )
    snapshot_provenance = json.loads(
        (repo_root / referenced_paths[1]).read_text(encoding="utf-8")
    )
    hardware = next(
        output
        for output in candidate["outputs"]
        if output["name"].endswith("_hardware_check.step")
    )
    if static_review.get("schema_version") != 1:
        raise ValueError("static review provenance schema is unsupported")
    if (
        not isinstance(static_review.get("job_id"), str)
        or not static_review["job_id"]
        or static_review.get("review_target") != REVIEW_TARGET
    ):
        raise ValueError("static review producer/job identity is invalid")
    renderer = static_review.get("renderer")
    if not isinstance(renderer, dict) or (
        renderer.get("name") != "repository static OCP viewer"
        or renderer.get("artifact_import_count") != 1
        or renderer.get("tessellation_count") != 1
    ):
        raise ValueError("static review renderer identity/counts are invalid")
    review_step = static_review.get("step")
    if not isinstance(review_step, dict) or (
        review_step.get("path") != hardware["path"]
        or review_step.get("sha256") != hardware["sha256"]
    ):
        raise ValueError("static review does not bind the candidate hardware STEP")
    review_sidecar = static_review.get("sidecar")
    if not isinstance(review_sidecar, dict) or (
        not isinstance(review_sidecar.get("path"), str)
        or not isinstance(review_sidecar.get("sha256"), str)
        or not isinstance(review_sidecar.get("size_bytes"), int)
        or review_sidecar.get("kind") not in {"part", "assembly"}
        or not isinstance(review_sidecar.get("verified_cache_key"), str)
        or not review_sidecar["verified_cache_key"]
    ):
        raise ValueError("static review has no verified sidecar identity")
    if snapshot_provenance.get("schema_version") != 1:
        raise ValueError("Snapshot provenance schema is unsupported")
    if (
        not isinstance(snapshot_provenance.get("job_id"), str)
        or not snapshot_provenance["job_id"]
        or snapshot_provenance.get("target") != SNAPSHOT_TARGET
    ):
        raise ValueError("Snapshot producer/job identity is invalid")
    snapshot_sources = snapshot_provenance.get("sources")
    if not isinstance(snapshot_sources, list):
        raise ValueError("Snapshot provenance has no source identities")
    source_by_kind = {
        source.get("kind"): source
        for source in snapshot_sources
        if isinstance(source, dict)
    }
    snapshot_step = source_by_kind.get("step")
    snapshot_sidecar = source_by_kind.get("sidecar")
    if not isinstance(snapshot_step, dict) or (
        snapshot_step.get("path") != hardware["path"]
        or snapshot_step.get("sha256") != hardware["sha256"]
    ):
        raise ValueError("Snapshot does not bind the candidate hardware STEP")
    if not isinstance(snapshot_sidecar, dict) or (
        snapshot_sidecar.get("path") != review_sidecar.get("path")
        or snapshot_sidecar.get("sha256") != review_sidecar.get("sha256")
    ):
        raise ValueError("Snapshot does not bind the verified review sidecar")
    snapshot_outputs = snapshot_provenance.get("outputs")
    if not isinstance(snapshot_outputs, list) or not any(
        isinstance(output, dict)
        and output.get("path") == referenced_paths[0]
        and output.get("sha256") == evidence[referenced_paths[0]]
        for output in snapshot_outputs
    ):
        raise ValueError("Snapshot provenance does not bind the accepted PNG")
    return VisualAcceptanceBinding(
        evidence_refs=(acceptance_path, *referenced_paths),
        step_path=hardware["path"],
        step_sha256=hardware["sha256"],
        sidecar_path=review_sidecar["path"],
        sidecar_sha256=review_sidecar["sha256"],
        sidecar_size_bytes=review_sidecar["size_bytes"],
        sidecar_kind=review_sidecar["kind"],
        sidecar_cache_key=review_sidecar["verified_cache_key"],
    )


def _requirement(
    requirement_id: str,
    description: str,
    kind: CheckKind,
    adapter: str,
    expected: bool | int | float,
    unit: Unit,
    tolerance: float,
    profile: VerificationProfile,
) -> Requirement:
    return Requirement(
        requirement_id=requirement_id,
        description=description,
        check=CheckSpec(kind, adapter),
        expectation=Expectation.exactly(expected),
        unit=unit,
        tolerance=Tolerance(tolerance),
        cost_profile=profile,
    )


def design_contract() -> DesignContract:
    """Return the policy-owned fast, fit, and release requirements."""

    fit_requirements = tuple(
        _requirement(
            f"OVAL-FIT-{index:03d}",
            f"{name.replace('_', ' ')} has no positive-volume interference.",
            CheckKind.INTERFERENCE,
            f"kernel.{name}_intersection",
            0.0,
            Unit.CUBIC_MILLIMETER,
            0.001,
            VerificationProfile.FIT,
        )
        for index, (name, _left, _right) in enumerate(
            FIT_INTERSECTION_PAIRS,
            start=1,
        )
    )
    return DesignContract(
        contract_id="contract.single-oval-port-rollout",
        title="Single oval port staged production verification",
        model=ModelIdentity(
            model_id=MODEL_ID,
            name="Single oval 39 Hz port study",
            variant="feedback-loop-rollout",
            source=_relative(GENERATOR, ROOT),
            entrypoint=_relative(GENERATOR, ROOT),
        ),
        requirements=(
            _requirement(
                "OVAL-FAST-001",
                "The complete required production STEP set is published.",
                CheckKind.STRUCTURAL,
                "artifact.output_count",
                len(STEP_OUTPUTS),
                Unit.COUNT,
                0.0,
                VerificationProfile.FAST,
            ),
            _requirement(
                "OVAL-FAST-002",
                "The candidate identity matches every current production artifact.",
                CheckKind.STRUCTURAL,
                "artifact.candidate_current",
                True,
                Unit.BOOLEAN,
                0.0,
                VerificationProfile.FAST,
            ),
            *fit_requirements,
            _requirement(
                "OVAL-FIT-006",
                "Every imported fit-stage artifact has usable topology.",
                CheckKind.FIT,
                "kernel.fit_topology_usable",
                True,
                Unit.BOOLEAN,
                0.0,
                VerificationProfile.FIT,
            ),
            _requirement(
                "OVAL-REL-001",
                "Every production STEP retains passing round-trip diagnostics.",
                CheckKind.ROUND_TRIP,
                "artifact.step_round_trip",
                True,
                Unit.BOOLEAN,
                0.0,
                VerificationProfile.RELEASE,
            ),
            _requirement(
                "OVAL-REL-002",
                "Every production STEP hash still matches the candidate.",
                CheckKind.ARTIFACT_INTEGRITY,
                "artifact.integrity",
                True,
                Unit.BOOLEAN,
                0.0,
                VerificationProfile.RELEASE,
            ),
            _requirement(
                "OVAL-REL-003",
                "The exact candidate has explicit accepted visual-smoke evidence.",
                CheckKind.VISUAL_REVIEW,
                "review.visual_smoke_accepted",
                True,
                Unit.BOOLEAN,
                0.0,
                VerificationProfile.RELEASE,
            ),
        ),
    )
