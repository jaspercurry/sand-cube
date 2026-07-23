"""Command-line interface for the resource-safe CAD coordinator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import threading

from .coordinator import (
    GIB,
    JobSupervisor,
    ResourceLimits,
    read_global_lock_status,
    read_job_states,
)


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cad-run",
        description="Queue and supervise one fresh CAD worker process.",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    run = subparsers.add_parser("run", help="queue and run a CAD entry point")
    run.add_argument("--repo", type=Path, required=True)
    run.add_argument("--name")
    run.add_argument(
        "--warning-gib",
        type=_positive_float,
        default=float(os.environ.get("CAD_RSS_WARNING_GIB", "8")),
    )
    run.add_argument(
        "--hard-limit-gib",
        type=_positive_float,
        default=float(os.environ.get("CAD_RSS_HARD_LIMIT_GIB", "12")),
    )
    run.add_argument(
        "--grace-seconds",
        type=_positive_float,
        default=float(os.environ.get("CAD_TERMINATION_GRACE_SECONDS", "8")),
    )
    run.add_argument(
        "--poll-seconds",
        type=_positive_float,
        default=float(os.environ.get("CAD_POLL_INTERVAL_SECONDS", "0.5")),
    )
    run.add_argument("command", nargs=argparse.REMAINDER)

    status = subparsers.add_parser("status", help="show queued and recent jobs")
    status.add_argument("--repo", type=Path, required=True)
    status.add_argument("--limit", type=int, default=20)
    return parser


def _run(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise SystemExit("cad-run run requires '-- SCRIPT [ARG ...]'")
    script = Path(command.pop(0))
    if not script.is_absolute():
        script = args.repo / script
    limits = ResourceLimits(
        warning_rss_bytes=int(args.warning_gib * GIB),
        hard_limit_rss_bytes=int(args.hard_limit_gib * GIB),
        termination_grace_seconds=args.grace_seconds,
        poll_interval_seconds=args.poll_seconds,
    )
    cancelled = threading.Event()

    def request_cancel(_signum, _frame) -> None:
        cancelled.set()

    prior_handlers = {
        signum: signal.signal(signum, request_cancel)
        for signum in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        result = JobSupervisor(args.repo, limits=limits).run(
            script,
            command,
            name=args.name,
            cancel_event=cancelled,
        )
    finally:
        for signum, handler in prior_handlers.items():
            signal.signal(signum, handler)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.state == "completed":
        return 0
    if result.state == "cancelled":
        return 130
    return 1


def _status(args: argparse.Namespace) -> int:
    state_root = args.repo.resolve() / "build" / "cad-jobs"
    payload = {
        "global_lock": read_global_lock_status(),
        "jobs": read_job_states(state_root, limit=args.limit),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.action == "run":
        return _run(args)
    return _status(args)
