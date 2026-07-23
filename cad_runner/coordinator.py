"""Single reusable lifecycle coordinator for every substantial CAD job.

This module intentionally imports no modeling, visualization, or CAD-native
libraries. The only non-stdlib dependency is psutil, used to account for the
entire process group owned by a job.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Mapping, Sequence
import uuid

import psutil

from .entrypoint import CAD_WORKER_ENV
from .outputs import REPO_ROOT_ENV, STAGE_ROOT_ENV
from .telemetry import FAILURE_PATH_ENV, load_failure_envelope


GIB = 1024**3
DEFAULT_WARNING_RSS_BYTES = 8 * GIB
DEFAULT_HARD_LIMIT_RSS_BYTES = 12 * GIB
DEFAULT_TERMINATION_GRACE_SECONDS = 8.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.5


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _new_job_id(name: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in name)
    safe = safe.strip("-")[:48] or "cad-job"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{safe}-{uuid.uuid4().hex[:10]}"


def default_global_runtime_root() -> Path:
    override = os.environ.get("CAD_GLOBAL_RUNTIME_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(tempfile.gettempdir()) / f"sand-cube-cad-{os.getuid()}"


def default_global_lock_path() -> Path:
    return default_global_runtime_root() / "heavy-worker.lock"


def read_global_lock_status(path: Path | None = None) -> dict[str, Any]:
    """Report whether the kernel lock is held and include holder metadata."""
    lock_path = Path(path or default_global_lock_path())
    if not lock_path.exists():
        return {"path": str(lock_path), "locked": False, "metadata": None}
    fd = os.open(lock_path, os.O_RDONLY)
    locked = True
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = False
            fcntl.flock(fd, fcntl.LOCK_UN)
        except BlockingIOError:
            locked = True
        os.lseek(fd, 0, os.SEEK_SET)
        raw = os.read(fd, 64 * 1024).decode(errors="replace").strip()
    finally:
        os.close(fd)
    try:
        metadata = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        metadata = {"unreadable": raw[:500]}
    return {"path": str(lock_path), "locked": locked, "metadata": metadata}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class ResourceLimits:
    warning_rss_bytes: int = DEFAULT_WARNING_RSS_BYTES
    hard_limit_rss_bytes: int = DEFAULT_HARD_LIMIT_RSS_BYTES
    termination_grace_seconds: float = DEFAULT_TERMINATION_GRACE_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS

    def __post_init__(self) -> None:
        if self.warning_rss_bytes <= 0 or self.hard_limit_rss_bytes <= 0:
            raise ValueError("RSS thresholds must be positive")
        if self.warning_rss_bytes >= self.hard_limit_rss_bytes:
            raise ValueError("RSS warning must be lower than the hard limit")
        if self.termination_grace_seconds <= 0 or self.poll_interval_seconds <= 0:
            raise ValueError("Timing limits must be positive")


@dataclass
class JobResult:
    job_id: str
    name: str
    state: str
    coordinator_pid: int
    worker_pid: int | None
    process_group_id: int | None
    command: list[str]
    queued_at: str
    started_at: str | None
    finished_at: str
    elapsed_seconds: float
    current_rss_bytes: int
    peak_rss_bytes: int
    exit_code: int | None
    exit_status: str
    failure_kind: str | None
    failure_message: str | None
    failure_details: dict[str, Any] | None
    warnings: list[str]
    final_outputs: list[dict[str, Any]]
    cleanup: dict[str, Any]
    attempts: int = 1
    log_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobCancelled(RuntimeError):
    """Raised internally when cancellation happens while queued."""


class GlobalCadLock:
    """Kernel-released interprocess admission lock with holder metadata."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._fd: int | None = None

    def acquire(
        self,
        *,
        cancel_event: threading.Event | None = None,
        poll_interval: float = 0.2,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode):
            os.close(fd)
            raise RuntimeError(f"Unsafe CAD lock path: {self.path}")
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._fd = fd
                    return
                except BlockingIOError:
                    if cancel_event is not None and cancel_event.is_set():
                        raise JobCancelled("cancelled while queued for CAD worker lock")
                    time.sleep(poll_interval)
        except BaseException:
            os.close(fd)
            raise

    def write_metadata(self, payload: Mapping[str, Any]) -> None:
        if self._fd is None:
            raise RuntimeError("CAD lock is not held")
        encoded = (json.dumps(payload, sort_keys=True) + "\n").encode()
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.ftruncate(self._fd, 0)
        os.write(self._fd, encoded)
        os.fsync(self._fd)

    def release(self, metadata: Mapping[str, Any] | None = None) -> None:
        if self._fd is None:
            return
        if metadata is not None:
            self.write_metadata(metadata)
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)
        self._fd = None

    def __enter__(self) -> GlobalCadLock:
        self.acquire()
        return self


def owned_process_group_pids(process_group_id: int) -> list[int]:
    """Return only processes in the exact job-owned process group."""
    if not _group_exists(process_group_id):
        return []
    try:
        root = psutil.Process(process_group_id)
    except psutil.Error:
        # The group can briefly outlive a reaped leader. The caller still uses
        # killpg/killpg(0) for exact cleanup and verification; no broad process
        # enumeration or unrelated PID signaling is needed.
        return []
    candidates = [root]
    try:
        candidates.extend(root.children(recursive=True))
    except (PermissionError, psutil.Error):
        # Sandboxed macOS processes can deny the all-PID sysctl used by
        # psutil.children(). The known group leader is still measured, and
        # killpg(0) continues to verify/clean the complete owned group. Normal
        # terminal sessions account for the recursively discovered children.
        pass
    pids: list[int] = []
    for process in candidates:
        try:
            if os.getpgid(process.pid) == process_group_id:
                pids.append(process.pid)
        except (OSError, psutil.Error):
            continue
    return sorted(pids)


def process_group_rss(process_group_id: int) -> tuple[int, list[int]]:
    """Measure aggregate current RSS for the worker and all descendants."""
    total = 0
    pids = owned_process_group_pids(process_group_id)
    for pid in pids:
        try:
            total += psutil.Process(pid).memory_info().rss
        except psutil.Error:
            continue
    return total, pids


def _group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_for_group_exit(
    process_group_id: int,
    timeout: float,
    process: subprocess.Popen[Any] | None = None,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process is not None:
            process.poll()
        if not _group_exists(process_group_id):
            return True
        time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
    if process is not None:
        process.poll()
    return not _group_exists(process_group_id)


def terminate_owned_process_group(
    process: subprocess.Popen[Any],
    *,
    process_group_id: int,
    grace_seconds: float,
) -> dict[str, Any]:
    """Terminate one exact job group, escalate, and reap the direct child."""
    sent: list[str] = []
    if _group_exists(process_group_id):
        try:
            os.killpg(process_group_id, signal.SIGTERM)
            sent.append("SIGTERM")
        except ProcessLookupError:
            pass
    graceful = _wait_for_group_exit(process_group_id, grace_seconds, process)
    if not graceful and _group_exists(process_group_id):
        try:
            os.killpg(process_group_id, signal.SIGKILL)
            sent.append("SIGKILL")
        except ProcessLookupError:
            pass
        _wait_for_group_exit(process_group_id, grace_seconds, process)
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        # The exact process group has already received SIGKILL. Waiting here is
        # required to reap the direct child; no unrelated process is signaled.
        process.wait()
    remaining = owned_process_group_pids(process_group_id)
    return {
        "signals_sent": sent,
        "graceful": graceful,
        "remaining_owned_pids": remaining,
        "reaped": process.returncode is not None,
    }


class JobSupervisor:
    """Queue, spawn, monitor, publish, clean, and record one CAD worker."""

    def __init__(
        self,
        repo_root: Path,
        *,
        limits: ResourceLimits | None = None,
        lock_path: Path | None = None,
        workspace_root: Path | None = None,
        state_root: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.limits = limits or ResourceLimits()
        self.lock_path = Path(lock_path or default_global_lock_path())
        self.workspace_root = Path(
            workspace_root or self.repo_root / "build" / ".cad-runtime" / "jobs"
        )
        self.state_root = Path(state_root or self.repo_root / "build" / "cad-jobs")

    def _state_path(self, job_id: str) -> Path:
        return self.state_root / f"{job_id}.json"

    def _record(self, job_id: str, payload: Mapping[str, Any]) -> None:
        _atomic_write_json(self._state_path(job_id), payload)

    def _spawn_worker(
        self,
        command: Sequence[str],
        *,
        environment: Mapping[str, str],
        log_stream,
    ) -> subprocess.Popen[Any]:
        """Start a clean session without preexec_fn or multiprocessing fork."""
        return subprocess.Popen(
            list(command),
            cwd=self.repo_root,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
        )

    def _publish_outputs(self, stage_root: Path) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        if not stage_root.exists():
            return outputs
        for source in sorted(stage_root.rglob("*")):
            if source.is_symlink():
                raise RuntimeError(f"Refusing to publish staged symlink: {source}")
            if not source.is_file():
                continue
            relative = source.relative_to(stage_root)
            destination = self.repo_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            size = source.stat().st_size
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            os.replace(source, destination)
            outputs.append(
                {
                    "path": str(destination),
                    "relative_path": str(relative),
                    "bytes": size,
                    "sha256": digest.hexdigest(),
                    "publication": "atomic_replace",
                }
            )
        return outputs

    def run(
        self,
        script: Path,
        arguments: Sequence[str] = (),
        *,
        name: str | None = None,
        cancel_event: threading.Event | None = None,
        extra_environment: Mapping[str, str] | None = None,
    ) -> JobResult:
        script = Path(script).resolve()
        job_name = name or script.stem
        job_id = _new_job_id(job_name)
        queued_at = _utc_now()
        coordinator_pid = os.getpid()
        workspace = self.workspace_root / job_id
        stage_root = workspace / "stage"
        log_temporary = workspace / "worker.log"
        durable_log = self.state_root / f"{job_id}.log"
        failure_envelope_path = workspace / "failure.json"
        workspace.mkdir(parents=True, exist_ok=False)
        stage_root.mkdir(parents=True, exist_ok=False)

        command = [
            sys.executable,
            "-m",
            "cad_runner.worker",
            str(script),
            *map(str, arguments),
        ]
        state: dict[str, Any] = {
            "job_id": job_id,
            "name": job_name,
            "state": "queued",
            "coordinator_pid": coordinator_pid,
            "worker_pid": None,
            "process_group_id": None,
            "command": command,
            "queued_at": queued_at,
            "started_at": None,
            "warning_rss_bytes": self.limits.warning_rss_bytes,
            "hard_limit_rss_bytes": self.limits.hard_limit_rss_bytes,
            "attempts": 1,
        }
        self._record(job_id, state)
        print(f"[cad-job {job_id}] queued", flush=True)

        lock = GlobalCadLock(self.lock_path)
        process: subprocess.Popen[Any] | None = None
        process_group_id: int | None = None
        started_at: str | None = None
        start_monotonic = time.monotonic()
        peak_rss = 0
        current_rss = 0
        warnings: list[str] = []
        final_outputs: list[dict[str, Any]] = []
        failure_kind: str | None = None
        failure_message: str | None = None
        failure_details: dict[str, Any] | None = None
        requested_stop: str | None = None
        exit_code: int | None = None
        exit_status = "not_started"
        termination: dict[str, Any] = {
            "signals_sent": [],
            "remaining_owned_pids": [],
            "reaped": False,
        }
        lock_acquired = False
        log_published = False
        cleanup_error: str | None = None

        try:
            lock.acquire(cancel_event=cancel_event)
            lock_acquired = True
            lock.write_metadata(
                {
                    "state": "admitted",
                    "job_id": job_id,
                    "name": job_name,
                    "coordinator_pid": coordinator_pid,
                    "worker_pid": None,
                    "acquired_at": _utc_now(),
                }
            )
            if cancel_event is not None and cancel_event.is_set():
                raise JobCancelled("cancelled before worker start")

            environment = os.environ.copy()
            environment.update(extra_environment or {})
            runner_root = str(Path(__file__).resolve().parents[1])
            prior_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = (
                runner_root
                if not prior_pythonpath
                else runner_root + os.pathsep + prior_pythonpath
            )
            environment.update(
                {
                    CAD_WORKER_ENV: "1",
                    "CAD_JOB_ID": job_id,
                    REPO_ROOT_ENV: str(self.repo_root),
                    STAGE_ROOT_ENV: str(stage_root),
                    FAILURE_PATH_ENV: str(failure_envelope_path),
                    "PYTHONUNBUFFERED": "1",
                }
            )
            with log_temporary.open("wb") as log_stream:
                process = self._spawn_worker(
                    command,
                    environment=environment,
                    log_stream=log_stream,
                )
                process_group_id = process.pid
                started_at = _utc_now()
                start_monotonic = time.monotonic()
                state.update(
                    {
                        "state": "running",
                        "worker_pid": process.pid,
                        "process_group_id": process_group_id,
                        "started_at": started_at,
                    }
                )
                self._record(job_id, state)
                lock.write_metadata(
                    {
                        "state": "running",
                        "job_id": job_id,
                        "name": job_name,
                        "coordinator_pid": coordinator_pid,
                        "worker_pid": process.pid,
                        "process_group_id": process_group_id,
                        "started_at": started_at,
                    }
                )
                print(
                    f"[cad-job {job_id}] running worker PID {process.pid}",
                    flush=True,
                )

                next_progress_record = time.monotonic()
                while process.poll() is None:
                    current_rss, _owned_pids = process_group_rss(process_group_id)
                    peak_rss = max(peak_rss, current_rss)
                    now = time.monotonic()
                    if now >= next_progress_record:
                        state.update(
                            {
                                "current_rss_bytes": current_rss,
                                "peak_rss_bytes": peak_rss,
                                "elapsed_seconds": round(now - start_monotonic, 3),
                                "last_progress_at": _utc_now(),
                            }
                        )
                        self._record(job_id, state)
                        next_progress_record = now + 5.0
                    if current_rss >= self.limits.warning_rss_bytes and not warnings:
                        warning = (
                            "RSS warning: owned process group reached "
                            f"{current_rss / GIB:.2f} GiB"
                        )
                        warnings.append(warning)
                        print(f"[cad-job {job_id}] {warning}", flush=True)
                    if current_rss >= self.limits.hard_limit_rss_bytes:
                        requested_stop = "resource_limit"
                        failure_kind = "resource_limit"
                        failure_message = (
                            "CAD worker exceeded hard RSS limit: "
                            f"{current_rss / GIB:.2f} GiB >= "
                            f"{self.limits.hard_limit_rss_bytes / GIB:.2f} GiB"
                        )
                        break
                    if cancel_event is not None and cancel_event.is_set():
                        requested_stop = "cancelled"
                        failure_kind = "cancelled"
                        failure_message = "CAD job was cancelled"
                        break
                    time.sleep(self.limits.poll_interval_seconds)

                if requested_stop:
                    termination = terminate_owned_process_group(
                        process,
                        process_group_id=process_group_id,
                        grace_seconds=self.limits.termination_grace_seconds,
                    )
                else:
                    exit_code = process.wait()
                    termination["reaped"] = True
                    # A successful parent is not enough: nested helpers must
                    # also leave the owned process group before publication.
                    if not _wait_for_group_exit(process_group_id, 1.0):
                        termination = terminate_owned_process_group(
                            process,
                            process_group_id=process_group_id,
                            grace_seconds=self.limits.termination_grace_seconds,
                        )
                        failure_kind = "owned_descendants_remained"
                        failure_message = (
                            "Worker exited but owned descendants remained; "
                            "the job process group was terminated"
                        )
                exit_code = process.returncode

            try:
                failure_details = load_failure_envelope(failure_envelope_path)
            except ValueError as error:
                warnings.append(str(error))

            if failure_kind == "cancelled":
                exit_status = "cancelled"
            elif failure_kind:
                exit_status = "failed"
            elif exit_code == 0:
                if failure_details is not None:
                    warnings.append(
                        "ignored worker failure envelope after successful exit"
                    )
                    failure_details = None
                final_outputs = self._publish_outputs(stage_root)
                exit_status = "completed"
            elif exit_code is not None and exit_code < 0:
                signal_number = -exit_code
                try:
                    signal_name = signal.Signals(signal_number).name
                except ValueError:
                    signal_name = f"signal {signal_number}"
                failure_kind = "native_or_forced_termination"
                failure_message = (
                    f"CAD worker terminated by {signal_name}; no retry was attempted"
                )
                exit_status = "failed"
            else:
                if failure_details is not None:
                    failure_kind = str(failure_details["kind"])
                    detail = str(failure_details["exception_type"])
                    if failure_details.get("phase"):
                        detail += f" during {failure_details['phase']}"
                    if failure_details.get("code") is not None:
                        detail += f" [{failure_details['code']}]"
                    message = str(failure_details.get("message") or "").strip()
                    failure_message = detail + (f": {message}" if message else "")
                else:
                    failure_kind = "worker_exit"
                    failure_message = (
                        f"CAD worker exited with status {exit_code}; "
                        "no retry was attempted"
                    )
                exit_status = "failed"
        except JobCancelled as exc:
            failure_kind = "cancelled"
            failure_message = str(exc)
            exit_status = "cancelled"
        except BaseException as exc:
            failure_kind = failure_kind or "coordinator_error"
            failure_message = failure_message or f"{type(exc).__name__}: {exc}"
            exit_status = "failed"
            if process is not None and process_group_id is not None:
                termination = terminate_owned_process_group(
                    process,
                    process_group_id=process_group_id,
                    grace_seconds=self.limits.termination_grace_seconds,
                )
                exit_code = process.returncode
        finally:
            if process is not None and process.poll() is None and process_group_id:
                termination = terminate_owned_process_group(
                    process,
                    process_group_id=process_group_id,
                    grace_seconds=self.limits.termination_grace_seconds,
                )
                exit_code = process.returncode

            if log_temporary.exists():
                durable_log.parent.mkdir(parents=True, exist_ok=True)
                os.replace(log_temporary, durable_log)
                log_published = True

            try:
                shutil.rmtree(workspace)
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_error = f"{type(exc).__name__}: {exc}"
                if exit_status == "completed":
                    exit_status = "failed"
                    failure_kind = "cleanup_failed"
                    failure_message = f"Job workspace cleanup failed: {exc}"

            if lock_acquired:
                lock.release(
                    {
                        "state": "released",
                        "job_id": job_id,
                        "name": job_name,
                        "coordinator_pid": coordinator_pid,
                        "worker_pid": process.pid if process else None,
                        "released_at": _utc_now(),
                        "exit_status": exit_status,
                    }
                )

        finished_at = _utc_now()
        elapsed = time.monotonic() - start_monotonic
        remaining = (
            owned_process_group_pids(process_group_id) if process_group_id else []
        )
        termination["remaining_owned_pids"] = remaining
        workspace_removed = not workspace.exists()
        state_name = (
            "completed"
            if exit_status == "completed"
            else "cancelled"
            if exit_status == "cancelled"
            else "failed"
        )
        result = JobResult(
            job_id=job_id,
            name=job_name,
            state=state_name,
            coordinator_pid=coordinator_pid,
            worker_pid=process.pid if process else None,
            process_group_id=process_group_id,
            command=command,
            queued_at=queued_at,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=round(elapsed, 3),
            current_rss_bytes=current_rss,
            peak_rss_bytes=peak_rss,
            exit_code=exit_code,
            exit_status=exit_status,
            failure_kind=failure_kind,
            failure_message=failure_message,
            failure_details=failure_details,
            warnings=warnings,
            final_outputs=final_outputs,
            cleanup={
                "workspace": str(workspace),
                "workspace_removed": workspace_removed,
                "error": cleanup_error,
                "log_published": log_published,
                "owned_process_group": termination,
            },
            log_path=str(durable_log) if log_published else None,
        )
        self._record(job_id, result.to_dict())
        print(
            f"[cad-job {job_id}] {state_name}; peak RSS "
            f"{peak_rss / GIB:.2f} GiB; outputs {len(final_outputs)}",
            flush=True,
        )
        return result


def read_job_states(state_root: Path, limit: int = 20) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    if not state_root.exists():
        return states
    for path in sorted(state_root.glob("*.json"), reverse=True)[:limit]:
        try:
            states.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            states.append({"state": "unreadable", "path": str(path)})
    return states
