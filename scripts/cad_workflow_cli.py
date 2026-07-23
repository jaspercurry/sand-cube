"""Thin CLI adapter for compact, hash-bound CAD iteration state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cad_verification import (
    VerificationProfile,
    WorkflowError,
    WorkflowStage,
    advance_iteration,
    begin_revision,
    gate_profile,
    iteration_to_dict,
    load_iteration,
    new_iteration,
    render_resume_card,
    save_iteration,
    validate_iteration,
)


ROOT = Path(__file__).resolve().parents[1]


def _state_path(value: Path) -> Path:
    path = (ROOT / value).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise WorkflowError(f"iteration state path escapes repository: {value}")
    return path


def _print_error(error: Exception) -> int:
    print(f"ERROR: {error}", file=sys.stderr)
    return 2


def command_init(args: argparse.Namespace, _config: dict | None) -> int:
    try:
        state_path = _state_path(args.state)
        if state_path.exists():
            raise WorkflowError(f"iteration state already exists: {state_path}")
        state = new_iteration(
            iteration_id=args.iteration_id,
            model_id=args.model_id,
            objective=args.objective,
            brief=args.brief,
            contract=args.contract,
            sources=args.source,
            open_question=args.open_question,
            next_action=args.next_action,
            root=ROOT,
        )
        save_iteration(state_path, state)
    except (OSError, WorkflowError) as error:
        return _print_error(error)
    print(render_resume_card(state, root=ROOT))
    return 0


def command_show(args: argparse.Namespace, _config: dict | None) -> int:
    try:
        state = load_iteration(_state_path(args.state))
        issues = validate_iteration(state, root=ROOT)
    except (OSError, WorkflowError) as error:
        return _print_error(error)
    if args.json:
        payload = iteration_to_dict(state)
        payload["validation"] = {
            "current": not issues,
            "issues": [
                {
                    "kind": issue.kind,
                    "message": issue.message,
                    "path": issue.path,
                }
                for issue in issues
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_resume_card(state, root=ROOT))
    return 1 if issues else 0


def command_gate(args: argparse.Namespace, _config: dict | None) -> int:
    try:
        state = load_iteration(_state_path(args.state))
        decision = gate_profile(
            state,
            VerificationProfile(args.profile),
            root=ROOT,
        )
    except (OSError, WorkflowError) as error:
        return _print_error(error)
    if args.json:
        print(
            json.dumps(
                {
                    "allowed": decision.allowed,
                    "current_stage": decision.current_stage.value,
                    "issues": [
                        {
                            "kind": issue.kind,
                            "message": issue.message,
                            "path": issue.path,
                        }
                        for issue in decision.issues
                    ],
                    "profile": decision.profile.value,
                    "reason": decision.reason,
                    "required_stage": decision.required_stage.value,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        status = "ALLOW" if decision.allowed else "BLOCK"
        print(f"{status} {decision.profile.value}: {decision.reason}")
        for issue in decision.issues:
            print(f"  {issue.kind.upper()} {issue.path or 'state'}: {issue.message}")
    return 0 if decision.allowed else 1


def command_advance(args: argparse.Namespace, _config: dict | None) -> int:
    try:
        state_path = _state_path(args.state)
        state = load_iteration(state_path)
        advanced = advance_iteration(
            state,
            expected_stage=WorkflowStage(args.expect),
            target_stage=WorkflowStage(args.to),
            evidence_files=args.evidence,
            summary=args.summary,
            open_question=args.open_question,
            next_action=args.next_action,
            root=ROOT,
        )
        save_iteration(state_path, advanced)
    except (OSError, WorkflowError) as error:
        return _print_error(error)
    print(render_resume_card(advanced, root=ROOT))
    return 0


def command_revise(args: argparse.Namespace, _config: dict | None) -> int:
    try:
        state_path = _state_path(args.state)
        state = load_iteration(state_path)
        revised = begin_revision(
            state,
            sources=args.source,
            open_question=args.open_question,
            next_action=args.next_action,
            root=ROOT,
            allow_unchanged=args.allow_unchanged,
        )
        save_iteration(state_path, revised)
    except (OSError, WorkflowError) as error:
        return _print_error(error)
    print(render_resume_card(revised, root=ROOT))
    return 0


def add_workflow_subparser(
    subparsers: argparse._SubParsersAction,
) -> None:
    workflow = subparsers.add_parser(
        "workflow",
        help="manage a compact, hash-bound AI CAD iteration state",
    )
    commands = workflow.add_subparsers(
        dest="workflow_command",
        required=True,
    )

    initialize = commands.add_parser(
        "init",
        help="create a candidate state pointing to its durable brief and contract",
    )
    initialize.add_argument("state", type=Path)
    initialize.add_argument("--iteration-id", required=True)
    initialize.add_argument("--model-id", required=True)
    initialize.add_argument("--objective", required=True)
    initialize.add_argument("--brief", type=Path, required=True)
    initialize.add_argument("--contract", type=Path, required=True)
    initialize.add_argument("--source", type=Path, action="append", required=True)
    initialize.add_argument("--open-question", required=True)
    initialize.add_argument("--next-action", required=True)
    initialize.set_defaults(handler=command_init)

    show = commands.add_parser(
        "show",
        help="render the compact resume card and verify every recorded hash",
    )
    show.add_argument("state", type=Path)
    show.add_argument("--json", action="store_true")
    show.set_defaults(handler=command_show)

    gate = commands.add_parser(
        "gate",
        help="check whether a fast, fit, or release job is permitted",
    )
    gate.add_argument("state", type=Path)
    gate.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        required=True,
    )
    gate.add_argument("--json", action="store_true")
    gate.set_defaults(handler=command_gate)

    advance = commands.add_parser(
        "advance",
        help="record evidence and move through exactly one feedback gate",
    )
    advance.add_argument("state", type=Path)
    advance.add_argument(
        "--expect",
        choices=tuple(stage.value for stage in WorkflowStage),
        required=True,
    )
    advance.add_argument(
        "--to",
        choices=tuple(stage.value for stage in WorkflowStage),
        required=True,
    )
    advance.add_argument(
        "--evidence",
        type=Path,
        action="append",
        required=True,
    )
    advance.add_argument("--summary", required=True)
    advance.add_argument("--open-question", required=True)
    advance.add_argument("--next-action", required=True)
    advance.set_defaults(handler=command_advance)

    revise = commands.add_parser(
        "revise",
        help="start a source-changing revision and invalidate old gate evidence",
    )
    revise.add_argument("state", type=Path)
    revise.add_argument(
        "--source",
        type=Path,
        action="append",
        required=True,
    )
    revise.add_argument("--open-question", required=True)
    revise.add_argument("--next-action", required=True)
    revise.add_argument("--allow-unchanged", action="store_true")
    revise.set_defaults(handler=command_revise)


__all__ = ["add_workflow_subparser"]
