"""Parse and summarize CAD job records without loading native CAD libraries."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any, Mapping


TERMINAL_STATES = frozenset({"cancelled", "completed", "failed"})
PERCENTILES = (50, 90, 95, 99)


@dataclass(frozen=True)
class JobRecord:
    """The stable, statistics-relevant subset of one coordinator record."""

    path: Path
    job_id: str
    name: str
    state: str
    elapsed_seconds: float | None
    peak_rss_bytes: int | None
    timestamp: str | None
    timestamp_value: datetime | None


@dataclass(frozen=True)
class RecordIssue:
    """One recoverable problem found while reading a job record."""

    path: Path
    kind: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "kind": self.kind,
            "message": self.message,
        }


@dataclass(frozen=True)
class JobRecordSet:
    root: Path
    total_files: int
    records: tuple[JobRecord, ...]
    issues: tuple[RecordIssue, ...]


@dataclass(frozen=True)
class JobStatistics:
    """Serializable aggregate statistics for a directory of job records."""

    root: Path
    total_files: int
    valid_records: int
    counts_by_state: Mapping[str, int]
    counts_by_name: Mapping[str, int]
    elapsed_samples: int
    elapsed_percentiles_seconds: Mapping[str, float | None]
    elapsed_seconds_by_state: Mapping[str, float]
    peak_rss: Mapping[str, Any] | None
    recent_targets: tuple[Mapping[str, Any], ...]
    slow_targets: tuple[Mapping[str, Any], ...]
    issue_counts: Mapping[str, int]
    issues: tuple[RecordIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "records_root": str(self.root),
            "total_files": self.total_files,
            "valid_records": self.valid_records,
            "counts_by_state": dict(self.counts_by_state),
            "counts_by_name": dict(self.counts_by_name),
            "elapsed": {
                "samples": self.elapsed_samples,
                "percentiles_seconds": dict(self.elapsed_percentiles_seconds),
                "seconds_by_state": dict(self.elapsed_seconds_by_state),
            },
            "peak_rss": dict(self.peak_rss) if self.peak_rss else None,
            "recent_targets": [dict(item) for item in self.recent_targets],
            "slow_targets": [dict(item) for item in self.slow_targets],
            "data_quality": {
                "counts": dict(self.issue_counts),
                "issues": [issue.to_dict() for issue in self.issues],
            },
        }


def _nonempty_string(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _optional_nonnegative_number(
    payload: Mapping[str, Any], key: str, *, integer: bool = False
) -> float | int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{key} must be a non-negative number")
    return int(number) if integer else number


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _record_timestamp(payload: Mapping[str, Any]) -> tuple[str | None, datetime | None]:
    for key in ("finished_at", "last_progress_at", "started_at", "queued_at"):
        value = _nonempty_string(payload, key)
        if value:
            return value, _parse_timestamp(value)
    return None, None


def _parse_record(path: Path) -> tuple[JobRecord | None, list[RecordIssue]]:
    issues: list[RecordIssue] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [RecordIssue(path, "malformed", str(error))]
    if not isinstance(payload, dict):
        return None, [RecordIssue(path, "malformed", "record must be a JSON object")]

    name = _nonempty_string(payload, "name")
    state = _nonempty_string(payload, "state")
    missing = [key for key, value in (("name", name), ("state", state)) if not value]
    if missing:
        return None, [
            RecordIssue(path, "incomplete", f"missing {', '.join(missing)}")
        ]

    job_id = _nonempty_string(payload, "job_id")
    if job_id is None:
        job_id = path.stem
        issues.append(
            RecordIssue(path, "incomplete", "missing job_id; using filename")
        )

    try:
        elapsed = _optional_nonnegative_number(payload, "elapsed_seconds")
        peak_rss = _optional_nonnegative_number(
            payload, "peak_rss_bytes", integer=True
        )
        timestamp, timestamp_value = _record_timestamp(payload)
    except (TypeError, ValueError) as error:
        return None, [RecordIssue(path, "malformed", str(error))]

    if state in TERMINAL_STATES:
        for key, value in (
            ("elapsed_seconds", elapsed),
            ("peak_rss_bytes", peak_rss),
            ("completion timestamp", timestamp),
        ):
            if value is None:
                issues.append(RecordIssue(path, "incomplete", f"missing {key}"))

    return (
        JobRecord(
            path=path,
            job_id=job_id,
            name=name,
            state=state,
            elapsed_seconds=float(elapsed) if elapsed is not None else None,
            peak_rss_bytes=int(peak_rss) if peak_rss is not None else None,
            timestamp=timestamp,
            timestamp_value=timestamp_value,
        ),
        issues,
    )


def load_job_records(root: Path) -> JobRecordSet:
    """Read every JSON record under *root*, retaining recoverable diagnostics."""

    root = Path(root)
    paths = sorted(root.glob("*.json")) if root.is_dir() else []
    records: list[JobRecord] = []
    issues: list[RecordIssue] = []
    for path in paths:
        record, record_issues = _parse_record(path)
        if record is not None:
            records.append(record)
        issues.extend(record_issues)
    return JobRecordSet(root, len(paths), tuple(records), tuple(issues))


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _target(record: JobRecord) -> dict[str, Any]:
    return {
        "job_id": record.job_id,
        "name": record.name,
        "state": record.state,
        "elapsed_seconds": record.elapsed_seconds,
        "peak_rss_bytes": record.peak_rss_bytes,
        "timestamp": record.timestamp,
    }


def summarize_job_records(
    record_set: JobRecordSet, *, target_limit: int = 5
) -> JobStatistics:
    if target_limit < 1:
        raise ValueError("target_limit must be positive")

    records = record_set.records
    durations = [
        record.elapsed_seconds
        for record in records
        if record.elapsed_seconds is not None
    ]
    duration_by_state: defaultdict[str, float] = defaultdict(float)
    for record in records:
        if record.elapsed_seconds is not None:
            duration_by_state[record.state] += record.elapsed_seconds

    peak_record = max(
        (record for record in records if record.peak_rss_bytes is not None),
        key=lambda record: record.peak_rss_bytes or 0,
        default=None,
    )
    peak_rss = None
    if peak_record is not None:
        peak_rss = {
            "bytes": peak_record.peak_rss_bytes,
            "gib": round((peak_record.peak_rss_bytes or 0) / 1024**3, 3),
            "job_id": peak_record.job_id,
            "name": peak_record.name,
            "state": peak_record.state,
        }

    recent = sorted(
        (record for record in records if record.timestamp_value is not None),
        key=lambda record: record.timestamp_value or datetime.min,
        reverse=True,
    )[:target_limit]
    slow = sorted(
        (record for record in records if record.elapsed_seconds is not None),
        key=lambda record: record.elapsed_seconds or 0,
        reverse=True,
    )[:target_limit]

    issue_paths: defaultdict[str, set[Path]] = defaultdict(set)
    for issue in record_set.issues:
        issue_paths[issue.kind].add(issue.path)

    return JobStatistics(
        root=record_set.root,
        total_files=record_set.total_files,
        valid_records=len(records),
        counts_by_state=dict(sorted(Counter(r.state for r in records).items())),
        counts_by_name=dict(sorted(Counter(r.name for r in records).items())),
        elapsed_samples=len(durations),
        elapsed_percentiles_seconds={
            f"p{percentile}": _percentile(durations, percentile)
            for percentile in PERCENTILES
        },
        elapsed_seconds_by_state=dict(sorted(duration_by_state.items())),
        peak_rss=peak_rss,
        recent_targets=tuple(_target(record) for record in recent),
        slow_targets=tuple(_target(record) for record in slow),
        issue_counts={
            kind: len(issue_paths.get(kind, set()))
            for kind in ("malformed", "incomplete")
        },
        issues=record_set.issues,
    )


def collect_job_statistics(root: Path, *, target_limit: int = 5) -> JobStatistics:
    return summarize_job_records(load_job_records(root), target_limit=target_limit)


def _format_counts(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{name}={count}" for name, count in counts.items()) or "none"


def _format_seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}s"


def _format_target(target: Mapping[str, Any]) -> str:
    elapsed = _format_seconds(target.get("elapsed_seconds"))
    timestamp = target.get("timestamp") or "time unknown"
    return (
        f"  {target['name']} [{target['state']}] {elapsed} "
        f"{timestamp} ({target['job_id']})"
    )


def render_job_statistics(statistics: JobStatistics) -> str:
    """Render a compact report suitable for an agent or terminal."""

    percentiles = " | ".join(
        f"{name} {_format_seconds(value)}"
        for name, value in statistics.elapsed_percentiles_seconds.items()
    )
    completed = statistics.elapsed_seconds_by_state.get("completed", 0.0)
    failed = statistics.elapsed_seconds_by_state.get("failed", 0.0)
    peak = "none"
    if statistics.peak_rss:
        peak = (
            f"{statistics.peak_rss['gib']:.3f} GiB "
            f"({statistics.peak_rss['name']}, {statistics.peak_rss['job_id']})"
        )

    lines = [
        f"CAD job statistics: {statistics.valid_records}/{statistics.total_files} "
        "readable records",
        f"States: {_format_counts(statistics.counts_by_state)}",
        f"Names: {_format_counts(statistics.counts_by_name)}",
        f"Elapsed ({statistics.elapsed_samples} samples): {percentiles}",
        f"Time consumed: completed {_format_seconds(completed)} | "
        f"failed {_format_seconds(failed)}",
        f"Peak RSS: {peak}",
        "Data quality: "
        f"malformed={statistics.issue_counts.get('malformed', 0)}, "
        f"incomplete={statistics.issue_counts.get('incomplete', 0)}",
        "Recent targets:",
    ]
    lines.extend(
        _format_target(target) for target in statistics.recent_targets
    )
    if not statistics.recent_targets:
        lines.append("  none")
    lines.append("Slow targets:")
    lines.extend(_format_target(target) for target in statistics.slow_targets)
    if not statistics.slow_targets:
        lines.append("  none")
    return "\n".join(lines)
