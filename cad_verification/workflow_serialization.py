"""Strict JSON persistence for compact CAD iteration state."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping

from .workflow import (
    FileIdentity,
    IterationState,
    StageEvidence,
    WorkflowError,
    WorkflowStage,
    _require_compact_text,
    _require_text,
)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise WorkflowError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise WorkflowError("timestamps must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _identity_to_dict(identity: FileIdentity) -> dict[str, Any]:
    return {
        "path": identity.path,
        "role": identity.role,
        "sha256": identity.sha256,
        "size_bytes": identity.size_bytes,
    }


def iteration_to_dict(state: IterationState) -> dict[str, Any]:
    return {
        "authority": [_identity_to_dict(item) for item in state.authority],
        "evidence": [
            {
                "files": [_identity_to_dict(file) for file in item.files],
                "recorded_at": _datetime_text(item.recorded_at),
                "stage": item.stage.value,
                "summary": item.summary,
            }
            for item in state.evidence
        ],
        "iteration_id": state.iteration_id,
        "model_id": state.model_id,
        "next_action": state.next_action,
        "objective": state.objective,
        "open_question": state.open_question,
        "revision": state.revision,
        "schema_version": state.schema_version,
        "sources": [_identity_to_dict(item) for item in state.sources],
        "stage": state.stage.value,
        "updated_at": _datetime_text(state.updated_at),
    }


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkflowError(f"{label} must be an object")
    return value


def _exact_keys(
    value: Mapping[str, Any], *, label: str, expected: Iterable[str]
) -> None:
    expected_set = set(expected)
    missing = sorted(expected_set - set(value))
    extra = sorted(set(value) - expected_set)
    if missing:
        raise WorkflowError(f"{label} missing keys: {', '.join(missing)}")
    if extra:
        raise WorkflowError(f"{label} unknown keys: {', '.join(extra)}")


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise WorkflowError(f"{label} must be a string")
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise WorkflowError(f"{label} must be an integer")
    return value


def _parse_datetime(value: Any, label: str) -> datetime:
    raw = _string(value, label)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise WorkflowError(f"{label} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None:
        raise WorkflowError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _identity_from_dict(value: Any, label: str) -> FileIdentity:
    data = _mapping(value, label)
    keys = ("path", "role", "sha256", "size_bytes")
    _exact_keys(data, label=label, expected=keys)
    digest = _string(data["sha256"], f"{label}.sha256")
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise WorkflowError(f"{label}.sha256 must be a lowercase SHA-256")
    size = _integer(data["size_bytes"], f"{label}.size_bytes")
    if size < 0:
        raise WorkflowError(f"{label}.size_bytes must not be negative")
    return FileIdentity(
        role=_require_text(_string(data["role"], f"{label}.role"), f"{label}.role"),
        path=_require_text(_string(data["path"], f"{label}.path"), f"{label}.path"),
        sha256=digest,
        size_bytes=size,
    )


def iteration_from_dict(value: Any) -> IterationState:
    data = _mapping(value, "iteration")
    keys = (
        "authority",
        "evidence",
        "iteration_id",
        "model_id",
        "next_action",
        "objective",
        "open_question",
        "revision",
        "schema_version",
        "sources",
        "stage",
        "updated_at",
    )
    _exact_keys(data, label="iteration", expected=keys)
    authority_raw = data["authority"]
    sources_raw = data["sources"]
    evidence_raw = data["evidence"]
    if not isinstance(authority_raw, list):
        raise WorkflowError("iteration.authority must be an array")
    if not isinstance(sources_raw, list):
        raise WorkflowError("iteration.sources must be an array")
    if not isinstance(evidence_raw, list):
        raise WorkflowError("iteration.evidence must be an array")
    authority = tuple(
        _identity_from_dict(item, f"iteration.authority[{index}]")
        for index, item in enumerate(authority_raw)
    )
    if (
        len(authority) != 2
        or {item.role for item in authority} != {"brief", "contract"}
        or len({item.path for item in authority}) != 2
    ):
        raise WorkflowError(
            "iteration.authority must contain distinct brief and contract files"
        )
    sources = tuple(
        _identity_from_dict(item, f"iteration.sources[{index}]")
        for index, item in enumerate(sources_raw)
    )
    if not sources or any(item.role != "source" for item in sources):
        raise WorkflowError("iteration.sources must contain source file identities")
    evidence: list[StageEvidence] = []
    for index, raw in enumerate(evidence_raw):
        label = f"iteration.evidence[{index}]"
        item = _mapping(raw, label)
        _exact_keys(
            item,
            label=label,
            expected=("files", "recorded_at", "stage", "summary"),
        )
        files_raw = item["files"]
        if not isinstance(files_raw, list):
            raise WorkflowError(f"{label}.files must be an array")
        try:
            stage = WorkflowStage(_string(item["stage"], f"{label}.stage"))
        except ValueError as error:
            raise WorkflowError(f"{label}.stage is unknown") from error
        evidence.append(
            StageEvidence(
                stage=stage,
                summary=_require_compact_text(
                    _string(item["summary"], f"{label}.summary"),
                    f"{label}.summary",
                ),
                files=tuple(
                    _identity_from_dict(file, f"{label}.files[{file_index}]")
                    for file_index, file in enumerate(files_raw)
                ),
                recorded_at=_parse_datetime(
                    item["recorded_at"], f"{label}.recorded_at"
                ),
            )
        )
    try:
        stage = WorkflowStage(_string(data["stage"], "iteration.stage"))
    except ValueError as error:
        raise WorkflowError("iteration.stage is unknown") from error
    return IterationState(
        iteration_id=_require_compact_text(
            _string(data["iteration_id"], "iteration.iteration_id"),
            "iteration.iteration_id",
            maximum=128,
        ),
        model_id=_require_compact_text(
            _string(data["model_id"], "iteration.model_id"),
            "iteration.model_id",
            maximum=128,
        ),
        objective=_require_compact_text(
            _string(data["objective"], "iteration.objective"),
            "iteration.objective",
        ),
        revision=_integer(data["revision"], "iteration.revision"),
        stage=stage,
        authority=authority,
        sources=sources,
        evidence=tuple(evidence),
        open_question=_require_compact_text(
            _string(data["open_question"], "iteration.open_question"),
            "iteration.open_question",
        ),
        next_action=_require_compact_text(
            _string(data["next_action"], "iteration.next_action"),
            "iteration.next_action",
        ),
        updated_at=_parse_datetime(data["updated_at"], "iteration.updated_at"),
        schema_version=_integer(
            data["schema_version"], "iteration.schema_version"
        ),
    )


def load_iteration(path: Path) -> IterationState:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_json_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WorkflowError(f"cannot read iteration state {path}: {error}") from error
    return iteration_from_dict(value)


def save_iteration(path: Path, state: IterationState) -> None:
    """Atomically write one deterministic iteration-state document."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(iteration_to_dict(state), indent=2, sort_keys=True) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


__all__ = [
    "iteration_from_dict",
    "iteration_to_dict",
    "load_iteration",
    "save_iteration",
]
