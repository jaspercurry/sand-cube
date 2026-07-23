from __future__ import annotations

import json
from pathlib import Path

from cad_runner.statistics import (
    collect_job_statistics,
    render_job_statistics,
)


def _write(root: Path, name: str, payload: object) -> None:
    (root / name).write_text(json.dumps(payload), encoding="utf-8")


def test_statistics_cover_states_names_timing_memory_and_targets(
    tmp_path: Path,
) -> None:
    records = tmp_path / "cad-jobs"
    records.mkdir()
    _write(
        records,
        "one.json",
        {
            "job_id": "one",
            "name": "enclosure",
            "state": "completed",
            "elapsed_seconds": 10,
            "peak_rss_bytes": 100,
            "finished_at": "2026-07-20T10:00:00Z",
        },
    )
    _write(
        records,
        "two.json",
        {
            "job_id": "two",
            "name": "enclosure",
            "state": "failed",
            "elapsed_seconds": 20,
            "peak_rss_bytes": 300,
            "finished_at": "2026-07-21T10:00:00Z",
        },
    )
    _write(
        records,
        "three.json",
        {
            "job_id": "three",
            "name": "sidecar",
            "state": "completed",
            "elapsed_seconds": 30,
            "peak_rss_bytes": 200,
            "finished_at": "2026-07-22T10:00:00Z",
        },
    )
    _write(
        records,
        "running.json",
        {
            "job_id": "running",
            "name": "snapshot",
            "state": "running",
            "started_at": "2026-07-23T10:00:00Z",
        },
    )

    statistics = collect_job_statistics(records, target_limit=2)

    assert statistics.counts_by_state == {
        "completed": 2,
        "failed": 1,
        "running": 1,
    }
    assert statistics.counts_by_name == {
        "enclosure": 2,
        "sidecar": 1,
        "snapshot": 1,
    }
    assert statistics.elapsed_percentiles_seconds == {
        "p50": 20.0,
        "p90": 28.0,
        "p95": 29.0,
        "p99": 29.8,
    }
    assert statistics.elapsed_seconds_by_state == {
        "completed": 40.0,
        "failed": 20.0,
    }
    assert statistics.peak_rss == {
        "bytes": 300,
        "gib": 0.0,
        "job_id": "two",
        "name": "enclosure",
        "state": "failed",
    }
    assert [target["job_id"] for target in statistics.recent_targets] == [
        "running",
        "three",
    ]
    assert [target["job_id"] for target in statistics.slow_targets] == [
        "three",
        "two",
    ]
    assert "Time consumed: completed 40.00s | failed 20.00s" in (
        render_job_statistics(statistics)
    )


def test_malformed_and_incomplete_records_are_reported_without_aborting(
    tmp_path: Path,
) -> None:
    records = tmp_path / "cad-jobs"
    records.mkdir()
    (records / "broken.json").write_text("{not json", encoding="utf-8")
    _write(records, "not-object.json", ["job"])
    _write(records, "missing-name.json", {"job_id": "missing", "state": "failed"})
    _write(
        records,
        "queued.json",
        {
            "job_id": "queued",
            "name": "queued-target",
            "state": "queued",
            "queued_at": "2026-07-22T12:00:00Z",
        },
    )

    statistics = collect_job_statistics(records)

    assert statistics.total_files == 4
    assert statistics.valid_records == 1
    assert statistics.counts_by_state == {"queued": 1}
    assert statistics.issue_counts == {"malformed": 2, "incomplete": 1}
    assert len(statistics.to_dict()["data_quality"]["issues"]) == 3


def test_missing_records_directory_returns_an_empty_report(tmp_path: Path) -> None:
    statistics = collect_job_statistics(tmp_path / "missing")

    assert statistics.total_files == 0
    assert statistics.valid_records == 0
    assert statistics.elapsed_percentiles_seconds["p95"] is None
    assert "Recent targets:\n  none" in render_job_statistics(statistics)
