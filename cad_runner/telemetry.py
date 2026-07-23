"""Native-free structured failure context for coordinated CAD workers."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
from typing import Any, Iterator, Mapping


FAILURE_ENVELOPE_SCHEMA_VERSION = 1
FAILURE_PATH_ENV = "CAD_JOB_FAILURE_PATH"
_CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_CURRENT_PHASE: ContextVar[str | None] = ContextVar(
    "cad_runner_current_phase",
    default=None,
)


class ContractRejection(RuntimeError):
    """An expected, identified rejection of geometry or evidence."""

    def __init__(self, code: str, message: str) -> None:
        normalized_code = code.strip()
        normalized_message = message.strip()
        if not _CODE_PATTERN.fullmatch(normalized_code):
            raise ValueError(
                "contract rejection code must be a lowercase dotted/dashed slug"
            )
        if not normalized_message:
            raise ValueError("contract rejection message must not be empty")
        super().__init__(normalized_message)
        self.code = normalized_code


@contextmanager
def phase(name: str) -> Iterator[None]:
    """Attach one optional semantic phase to an escaping exception."""

    normalized = name.strip()
    if not normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError("phase name must be one nonempty line")
    token = _CURRENT_PHASE.set(normalized)
    try:
        yield
    except BaseException as error:
        if not hasattr(error, "__cad_job_phase__"):
            try:
                setattr(error, "__cad_job_phase__", normalized)
            except (AttributeError, TypeError):
                pass
        raise
    finally:
        _CURRENT_PHASE.reset(token)


def failure_envelope(error: BaseException) -> dict[str, Any]:
    """Return deterministic structured context for one Python-side failure."""

    exception_type = f"{type(error).__module__}.{type(error).__qualname__}"
    phase_name = getattr(error, "__cad_job_phase__", None)
    if not isinstance(phase_name, str):
        phase_name = _CURRENT_PHASE.get()
    kind = "python_exception"
    code: int | str | None = None
    if isinstance(error, ContractRejection):
        kind = "contract_rejection"
        code = error.code
    elif isinstance(error, SystemExit):
        kind = "script_exit"
        if isinstance(error.code, (int, str)) and not isinstance(error.code, bool):
            code = error.code
    return {
        "schema_version": FAILURE_ENVELOPE_SCHEMA_VERSION,
        "kind": kind,
        "exception_type": exception_type,
        "message": str(error),
        "code": code,
        "phase": phase_name,
    }


def write_failure_envelope(path: Path, error: BaseException) -> None:
    """Best-effort atomic write inside a coordinator-owned workspace."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(failure_envelope(error), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _optional_scalar(value: Any, label: str) -> int | str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{label} must be an integer, string, or null")
    return value


def load_failure_envelope(path: Path) -> dict[str, Any] | None:
    """Read and strictly validate a worker envelope if one exists."""

    if not path.is_file():
        return None
    if path.is_symlink():
        raise ValueError("worker failure envelope must not be a symlink")
    if path.stat().st_size > 64 * 1024:
        raise ValueError("worker failure envelope exceeds 64 KiB")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid worker failure envelope: {error}") from error
    if not isinstance(value, Mapping):
        raise ValueError("worker failure envelope must be an object")
    expected = {
        "schema_version",
        "kind",
        "exception_type",
        "message",
        "code",
        "phase",
    }
    if set(value) != expected:
        raise ValueError("worker failure envelope has missing or unknown keys")
    if value["schema_version"] != FAILURE_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("unsupported worker failure envelope schema")
    kind = value["kind"]
    if kind not in {"contract_rejection", "python_exception", "script_exit"}:
        raise ValueError(f"unknown worker failure kind: {kind!r}")
    for key in ("exception_type", "message"):
        if not isinstance(value[key], str):
            raise ValueError(f"worker failure {key} must be a string")
    phase_name = value["phase"]
    if phase_name is not None and not isinstance(phase_name, str):
        raise ValueError("worker failure phase must be a string or null")
    code = _optional_scalar(value["code"], "worker failure code")
    if kind == "contract_rejection" and (
        not isinstance(code, str) or not _CODE_PATTERN.fullmatch(code)
    ):
        raise ValueError("contract rejection envelope requires a stable code")
    if kind == "python_exception" and code is not None:
        raise ValueError("python exception envelope code must be null")
    return {
        "schema_version": FAILURE_ENVELOPE_SCHEMA_VERSION,
        "kind": kind,
        "exception_type": value["exception_type"],
        "message": value["message"],
        "code": code,
        "phase": phase_name,
    }


__all__ = [
    "FAILURE_ENVELOPE_SCHEMA_VERSION",
    "FAILURE_PATH_ENV",
    "ContractRejection",
    "failure_envelope",
    "load_failure_envelope",
    "phase",
    "write_failure_envelope",
]
