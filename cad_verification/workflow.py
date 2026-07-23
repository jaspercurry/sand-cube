"""Compact, native-free state for staged AI CAD iteration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .policy import VerificationProfile


WORKFLOW_SCHEMA_VERSION = 1


class WorkflowError(ValueError):
    """Raised when an iteration state or transition is invalid."""


class WorkflowStage(str, Enum):
    """Ordered evidence gates for one geometry revision."""

    CANDIDATE = "candidate"
    FAST_PASSED = "fast_passed"
    VISUAL_ACCEPTED = "visual_accepted"
    FIT_PASSED = "fit_passed"
    RELEASE_PASSED = "release_passed"
    INDEPENDENTLY_REVIEWED = "independently_reviewed"


STAGE_ORDER = (
    WorkflowStage.CANDIDATE,
    WorkflowStage.FAST_PASSED,
    WorkflowStage.VISUAL_ACCEPTED,
    WorkflowStage.FIT_PASSED,
    WorkflowStage.RELEASE_PASSED,
    WorkflowStage.INDEPENDENTLY_REVIEWED,
)

PROFILE_PREREQUISITES = {
    VerificationProfile.FAST: WorkflowStage.CANDIDATE,
    VerificationProfile.FIT: WorkflowStage.VISUAL_ACCEPTED,
    VerificationProfile.RELEASE: WorkflowStage.FIT_PASSED,
}


@dataclass(frozen=True)
class FileIdentity:
    """Hash-bound repository file reference."""

    role: str
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class StageEvidence:
    """Evidence that justified one completed workflow gate."""

    stage: WorkflowStage
    summary: str
    files: tuple[FileIdentity, ...]
    recorded_at: datetime


@dataclass(frozen=True)
class IterationState:
    """The small mutable truth for one task; briefs remain external."""

    iteration_id: str
    model_id: str
    objective: str
    revision: int
    stage: WorkflowStage
    authority: tuple[FileIdentity, ...]
    sources: tuple[FileIdentity, ...]
    evidence: tuple[StageEvidence, ...]
    open_question: str
    next_action: str
    updated_at: datetime
    schema_version: int = WORKFLOW_SCHEMA_VERSION


@dataclass(frozen=True)
class StateIssue:
    kind: str
    path: str
    message: str


@dataclass(frozen=True)
class GateDecision:
    profile: VerificationProfile
    allowed: bool
    required_stage: WorkflowStage
    current_stage: WorkflowStage
    issues: tuple[StateIssue, ...]
    reason: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_path(path: Path, root: Path) -> tuple[Path, str]:
    root = root.resolve()
    resolved = path.expanduser()
    if not resolved.is_absolute():
        resolved = root / resolved
    resolved = resolved.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise WorkflowError(f"path escapes repository root: {path}") from error
    if not resolved.is_file():
        raise WorkflowError(f"tracked file does not exist: {relative}")
    return resolved, relative.as_posix()


def identify_file(path: Path, *, role: str, root: Path) -> FileIdentity:
    if not role.strip():
        raise WorkflowError("file role must not be empty")
    resolved, relative = _repository_path(path, root)
    return FileIdentity(
        role=role.strip(),
        path=relative,
        sha256=_sha256_file(resolved),
        size_bytes=resolved.stat().st_size,
    )


def _require_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise WorkflowError(f"{label} must not be empty")
    return normalized


def _require_compact_text(
    value: str,
    label: str,
    *,
    maximum: int = 280,
) -> str:
    normalized = _require_text(value, label)
    if "\n" in normalized or "\r" in normalized:
        raise WorkflowError(f"{label} must be one compact line")
    if len(normalized) > maximum:
        raise WorkflowError(
            f"{label} must be at most {maximum} characters; "
            "put durable detail in the brief or contract"
        )
    return normalized


def new_iteration(
    *,
    iteration_id: str,
    model_id: str,
    objective: str,
    brief: Path,
    contract: Path,
    sources: Iterable[Path],
    open_question: str,
    next_action: str,
    root: Path,
    now: datetime | None = None,
) -> IterationState:
    source_paths = tuple(sources)
    if not source_paths:
        raise WorkflowError("at least one authoritative source is required")
    authority = (
        identify_file(brief, role="brief", root=root),
        identify_file(contract, role="contract", root=root),
    )
    if len({item.path for item in authority}) != 2:
        raise WorkflowError("brief and contract must be distinct files")
    source_identities = tuple(
        identify_file(path, role="source", root=root) for path in source_paths
    )
    if len({item.path for item in source_identities}) != len(source_identities):
        raise WorkflowError("authoritative source paths must be unique")
    return IterationState(
        iteration_id=_require_compact_text(
            iteration_id, "iteration_id", maximum=128
        ),
        model_id=_require_compact_text(model_id, "model_id", maximum=128),
        objective=_require_compact_text(objective, "objective"),
        revision=1,
        stage=WorkflowStage.CANDIDATE,
        authority=authority,
        sources=source_identities,
        evidence=(),
        open_question=_require_compact_text(open_question, "open_question"),
        next_action=_require_compact_text(next_action, "next_action"),
        updated_at=now or _utc_now(),
    )


def _stage_index(stage: WorkflowStage) -> int:
    return STAGE_ORDER.index(stage)


def _expected_evidence_stages(stage: WorkflowStage) -> tuple[WorkflowStage, ...]:
    return STAGE_ORDER[1 : _stage_index(stage) + 1]


def _identity_issue(identity: FileIdentity, root: Path) -> StateIssue | None:
    try:
        path, relative = _repository_path(Path(identity.path), root)
    except WorkflowError as error:
        return StateIssue("missing", identity.path, str(error))
    if relative != identity.path:
        return StateIssue(
            "state",
            identity.path,
            f"{identity.role} path is not normalized",
        )
    actual_size = path.stat().st_size
    if actual_size != identity.size_bytes:
        return StateIssue(
            "stale",
            identity.path,
            f"{identity.role} size changed: {identity.size_bytes} -> {actual_size}",
        )
    actual_hash = _sha256_file(path)
    if actual_hash != identity.sha256:
        return StateIssue(
            "stale",
            identity.path,
            f"{identity.role} SHA-256 changed",
        )
    return None


def validate_iteration(
    state: IterationState, *, root: Path
) -> tuple[StateIssue, ...]:
    issues: list[StateIssue] = []
    if state.schema_version != WORKFLOW_SCHEMA_VERSION:
        issues.append(
            StateIssue(
                "schema",
                "",
                f"unsupported schema version {state.schema_version}",
            )
        )
    if state.revision < 1:
        issues.append(StateIssue("state", "", "revision must be positive"))
    if len(state.authority) != 2 or {
        item.role for item in state.authority
    } != {"brief", "contract"}:
        issues.append(
            StateIssue(
                "state",
                "",
                "authority must contain one brief and one contract",
            )
        )
    elif len({item.path for item in state.authority}) != 2:
        issues.append(
            StateIssue("state", "", "brief and contract must be distinct files")
        )
    if not state.sources or any(item.role != "source" for item in state.sources):
        issues.append(
            StateIssue("state", "", "sources must contain source identities")
        )
    if len({item.path for item in state.sources}) != len(state.sources):
        issues.append(StateIssue("state", "", "source paths must be unique"))
    for identity in (*state.authority, *state.sources):
        issue = _identity_issue(identity, root)
        if issue:
            issues.append(issue)

    evidence_by_stage = {item.stage: item for item in state.evidence}
    if len(evidence_by_stage) != len(state.evidence):
        issues.append(StateIssue("state", "", "duplicate evidence stage"))
    expected = set(_expected_evidence_stages(state.stage))
    actual = set(evidence_by_stage)
    if tuple(item.stage for item in state.evidence) != _expected_evidence_stages(
        state.stage
    ):
        issues.append(
            StateIssue("state", "", "evidence stages are not in gate order")
        )
    for missing in sorted(expected - actual, key=_stage_index):
        issues.append(
            StateIssue(
                "state",
                "",
                f"{missing.value} has no recorded evidence",
            )
        )
    for premature in sorted(actual - expected, key=_stage_index):
        issues.append(
            StateIssue(
                "state",
                "",
                f"{premature.value} evidence is ahead of current stage",
            )
        )
    for item in state.evidence:
        if not item.files:
            issues.append(
                StateIssue(
                    "state",
                    "",
                    f"{item.stage.value} evidence has no files",
                )
            )
        for identity in item.files:
            if identity.role != f"{item.stage.value}_evidence":
                issues.append(
                    StateIssue(
                        "state",
                        identity.path,
                        f"unexpected evidence role {identity.role}",
                    )
                )
            issue = _identity_issue(identity, root)
            if issue:
                issues.append(issue)
    return tuple(issues)


def gate_profile(
    state: IterationState,
    profile: VerificationProfile,
    *,
    root: Path,
) -> GateDecision:
    issues = validate_iteration(state, root=root)
    required = PROFILE_PREREQUISITES[profile]
    stage_ready = _stage_index(state.stage) >= _stage_index(required)
    if issues:
        reason = "iteration state is stale or invalid"
    elif not stage_ready:
        reason = (
            f"{profile.value} requires {required.value}; "
            f"current stage is {state.stage.value}"
        )
    else:
        reason = f"{profile.value} is permitted from {state.stage.value}"
    return GateDecision(
        profile=profile,
        allowed=not issues and stage_ready,
        required_stage=required,
        current_stage=state.stage,
        issues=issues,
        reason=reason,
    )


def advance_iteration(
    state: IterationState,
    *,
    expected_stage: WorkflowStage,
    target_stage: WorkflowStage,
    evidence_files: Iterable[Path],
    summary: str,
    open_question: str,
    next_action: str,
    root: Path,
    now: datetime | None = None,
) -> IterationState:
    issues = validate_iteration(state, root=root)
    if issues:
        raise WorkflowError("cannot advance a stale or invalid iteration state")
    if state.stage is not expected_stage:
        raise WorkflowError(
            f"expected stage {expected_stage.value}, found {state.stage.value}"
        )
    current_index = _stage_index(state.stage)
    if current_index + 1 >= len(STAGE_ORDER):
        raise WorkflowError(f"{state.stage.value} is already the final stage")
    required_target = STAGE_ORDER[current_index + 1]
    if target_stage is not required_target:
        raise WorkflowError(
            f"next legal stage after {state.stage.value} is {required_target.value}"
        )
    paths = tuple(evidence_files)
    if not paths:
        raise WorkflowError("at least one evidence file is required")
    timestamp = now or _utc_now()
    evidence = StageEvidence(
        stage=target_stage,
        summary=_require_compact_text(summary, "summary"),
        files=tuple(
            identify_file(path, role=f"{target_stage.value}_evidence", root=root)
            for path in paths
        ),
        recorded_at=timestamp,
    )
    return replace(
        state,
        stage=target_stage,
        evidence=(*state.evidence, evidence),
        open_question=_require_compact_text(open_question, "open_question"),
        next_action=_require_compact_text(next_action, "next_action"),
        updated_at=timestamp,
    )


def begin_revision(
    state: IterationState,
    *,
    sources: Iterable[Path],
    open_question: str,
    next_action: str,
    root: Path,
    allow_unchanged: bool = False,
    now: datetime | None = None,
) -> IterationState:
    paths = tuple(sources)
    if not paths:
        raise WorkflowError("at least one authoritative source is required")
    new_authority = tuple(
        identify_file(Path(item.path), role=item.role, root=root)
        for item in state.authority
    )
    new_sources = tuple(
        identify_file(path, role="source", root=root) for path in paths
    )
    if len({item.path for item in new_sources}) != len(new_sources):
        raise WorkflowError("authoritative source paths must be unique")
    old_fingerprints = {
        (item.role, item.path, item.sha256)
        for item in (*state.authority, *state.sources)
    }
    new_fingerprints = {
        (item.role, item.path, item.sha256)
        for item in (*new_authority, *new_sources)
    }
    if not allow_unchanged and old_fingerprints == new_fingerprints:
        raise WorkflowError(
            "authoritative sources are unchanged; do not discard valid evidence"
        )
    return replace(
        state,
        revision=state.revision + 1,
        stage=WorkflowStage.CANDIDATE,
        authority=new_authority,
        sources=new_sources,
        evidence=(),
        open_question=_require_compact_text(open_question, "open_question"),
        next_action=_require_compact_text(next_action, "next_action"),
        updated_at=now or _utc_now(),
    )


def render_resume_card(state: IterationState, *, root: Path) -> str:
    issues = validate_iteration(state, root=root)
    status = "STALE" if issues else "CURRENT"
    next_profile = "none"
    for profile in VerificationProfile:
        if gate_profile(state, profile, root=root).allowed:
            next_profile = profile.value
    evidence = ", ".join(item.stage.value for item in state.evidence) or "none"
    lines = [
        f"AI CAD resume card: {state.iteration_id} r{state.revision} [{status}]",
        f"Model: {state.model_id}",
        f"Stage: {state.stage.value}",
        f"Objective: {state.objective}",
        "Authority: "
        + ", ".join(
            f"{item.role}={item.path}@{item.sha256[:12]}"
            for item in state.authority
        ),
        "Sources: "
        + ", ".join(f"{item.path}@{item.sha256[:12]}" for item in state.sources),
        f"Evidence gates: {evidence}",
        f"Open question: {state.open_question}",
        f"Next action: {state.next_action}",
        f"Highest permitted profile: {next_profile}",
    ]
    for issue in issues:
        lines.append(f"ISSUE {issue.kind}: {issue.path or 'state'} — {issue.message}")
    return "\n".join(lines)


__all__ = [
    "PROFILE_PREREQUISITES",
    "STAGE_ORDER",
    "WORKFLOW_SCHEMA_VERSION",
    "FileIdentity",
    "GateDecision",
    "IterationState",
    "StageEvidence",
    "StateIssue",
    "WorkflowError",
    "WorkflowStage",
    "advance_iteration",
    "begin_revision",
    "gate_profile",
    "identify_file",
    "new_iteration",
    "render_resume_card",
    "validate_iteration",
]
