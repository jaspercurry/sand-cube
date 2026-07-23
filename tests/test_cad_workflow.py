from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from cad_verification import (
    VerificationProfile,
    WorkflowError,
    WorkflowStage,
    advance_iteration,
    begin_revision,
    gate_profile,
    load_iteration,
    new_iteration,
    render_resume_card,
    save_iteration,
    validate_iteration,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _state(root: Path):
    brief = _write(root, "workbench/design/brief.md", "durable intent\n")
    contract = _write(root, "workbench/design/contract.md", "acceptance\n")
    source = _write(root, "src/model.py", "PARAMETER = 1\n")
    return new_iteration(
        iteration_id="seam-refinement",
        model_id="removable-front",
        objective="Remove the visible underside seam.",
        brief=brief,
        contract=contract,
        sources=(source,),
        open_question="Is the lower transition visually continuous?",
        next_action="Run native-free fast checks.",
        root=root,
        now=NOW,
    )


def _advance(
    state,
    root: Path,
    target: WorkflowStage,
    evidence: Path,
):
    return advance_iteration(
        state,
        expected_stage=state.stage,
        target_stage=target,
        evidence_files=(evidence,),
        summary=f"{target.value} accepted",
        open_question="What is the next cheapest unresolved question?",
        next_action=f"Prepare {target.value} handoff.",
        root=root,
        now=NOW,
    )


def test_fit_and_release_are_blocked_until_cheaper_gates_pass(
    tmp_path: Path,
) -> None:
    state = _state(tmp_path)
    evidence = _write(tmp_path, "build/evidence.txt", "pass\n")

    assert gate_profile(
        state, VerificationProfile.FAST, root=tmp_path
    ).allowed
    fit_before_visual = gate_profile(
        state, VerificationProfile.FIT, root=tmp_path
    )
    assert not fit_before_visual.allowed
    assert fit_before_visual.required_stage is WorkflowStage.VISUAL_ACCEPTED

    state = _advance(state, tmp_path, WorkflowStage.FAST_PASSED, evidence)
    assert not gate_profile(
        state, VerificationProfile.FIT, root=tmp_path
    ).allowed
    state = _advance(state, tmp_path, WorkflowStage.VISUAL_ACCEPTED, evidence)
    assert gate_profile(
        state, VerificationProfile.FIT, root=tmp_path
    ).allowed
    assert not gate_profile(
        state, VerificationProfile.RELEASE, root=tmp_path
    ).allowed

    state = _advance(state, tmp_path, WorkflowStage.FIT_PASSED, evidence)
    assert gate_profile(
        state, VerificationProfile.RELEASE, root=tmp_path
    ).allowed


def test_state_round_trip_and_resume_card_are_compact(tmp_path: Path) -> None:
    state = _state(tmp_path)
    path = tmp_path / "workbench/design/state.json"

    save_iteration(path, state)
    loaded = load_iteration(path)

    assert loaded == state
    card = render_resume_card(loaded, root=tmp_path)
    assert "seam-refinement r1 [CURRENT]" in card
    assert "brief=workbench/design/brief.md@" in card
    assert "Run native-free fast checks." in card
    assert len(card.splitlines()) == 10


def test_changed_source_marks_state_stale_and_blocks_every_gate(
    tmp_path: Path,
) -> None:
    state = _state(tmp_path)
    _write(tmp_path, "src/model.py", "PARAMETER = 2\n")

    issues = validate_iteration(state, root=tmp_path)
    decision = gate_profile(state, VerificationProfile.FAST, root=tmp_path)

    assert any(issue.kind == "stale" for issue in issues)
    assert not decision.allowed
    assert "stale or invalid" in decision.reason
    assert "[STALE]" in render_resume_card(state, root=tmp_path)


def test_new_revision_rehashes_sources_and_clears_old_evidence(
    tmp_path: Path,
) -> None:
    state = _state(tmp_path)
    evidence = _write(tmp_path, "build/evidence.txt", "pass\n")
    state = _advance(state, tmp_path, WorkflowStage.FAST_PASSED, evidence)
    _write(tmp_path, "src/model.py", "PARAMETER = 2\n")

    revised = begin_revision(
        state,
        sources=(tmp_path / "src/model.py",),
        open_question="Does revision two retain the protected shape?",
        next_action="Run fast checks for revision two.",
        root=tmp_path,
        now=NOW,
    )

    assert revised.revision == 2
    assert revised.stage is WorkflowStage.CANDIDATE
    assert revised.evidence == ()
    assert validate_iteration(revised, root=tmp_path) == ()


def test_contract_change_is_accepted_only_as_a_new_revision(
    tmp_path: Path,
) -> None:
    state = _state(tmp_path)
    old_contract_hash = next(
        item.sha256 for item in state.authority if item.role == "contract"
    )
    _write(tmp_path, "workbench/design/contract.md", "new acceptance\n")

    revised = begin_revision(
        state,
        sources=(tmp_path / "src/model.py",),
        open_question="Does the candidate meet the revised acceptance?",
        next_action="Run the revised fast checks.",
        root=tmp_path,
        now=NOW,
    )

    new_contract_hash = next(
        item.sha256 for item in revised.authority if item.role == "contract"
    )
    assert new_contract_hash != old_contract_hash
    assert revised.revision == 2
    assert validate_iteration(revised, root=tmp_path) == ()


def test_transition_cannot_skip_visual_smoke(tmp_path: Path) -> None:
    state = _state(tmp_path)
    evidence = _write(tmp_path, "build/evidence.txt", "pass\n")

    with pytest.raises(WorkflowError, match="next legal stage"):
        _advance(state, tmp_path, WorkflowStage.FIT_PASSED, evidence)


def test_unchanged_revision_is_rejected(tmp_path: Path) -> None:
    state = _state(tmp_path)

    with pytest.raises(WorkflowError, match="unchanged"):
        begin_revision(
            state,
            sources=(tmp_path / "src/model.py",),
            open_question="Still the same question.",
            next_action="Do not throw away evidence.",
            root=tmp_path,
            now=NOW,
        )


def test_live_state_rejects_a_reinjected_long_prompt(tmp_path: Path) -> None:
    brief = _write(tmp_path, "brief.md", "The long prompt belongs here.\n")
    contract = _write(tmp_path, "contract.md", "Acceptance belongs here.\n")
    source = _write(tmp_path, "model.py", "PARAMETER = 1\n")

    with pytest.raises(WorkflowError, match="one compact line"):
        new_iteration(
            iteration_id="iteration",
            model_id="model",
            objective="First line\nSecond line",
            brief=brief,
            contract=contract,
            sources=(source,),
            open_question="What changed?",
            next_action="Run fast checks.",
            root=tmp_path,
            now=NOW,
        )


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    state = _state(tmp_path)
    path = tmp_path / "state.json"
    save_iteration(path, state)
    encoded = path.read_text(encoding="utf-8").replace(
        '  "model_id":',
        '  "model_id": "duplicate",\n  "model_id":',
        1,
    )
    path.write_text(encoded, encoding="utf-8")

    with pytest.raises(WorkflowError, match="duplicate JSON key"):
        load_iteration(path)


def test_duplicate_source_paths_are_rejected(tmp_path: Path) -> None:
    brief = _write(tmp_path, "brief.md", "Intent.\n")
    contract = _write(tmp_path, "contract.md", "Acceptance.\n")
    source = _write(tmp_path, "model.py", "PARAMETER = 1\n")

    with pytest.raises(WorkflowError, match="must be unique"):
        new_iteration(
            iteration_id="iteration",
            model_id="model",
            objective="Test source identity.",
            brief=brief,
            contract=contract,
            sources=(source, source),
            open_question="Are identities unique?",
            next_action="Reject duplicate paths.",
            root=tmp_path,
            now=NOW,
        )


def test_brief_and_contract_must_be_separate_files(tmp_path: Path) -> None:
    authority = _write(tmp_path, "authority.md", "Intent and acceptance.\n")
    source = _write(tmp_path, "model.py", "PARAMETER = 1\n")

    with pytest.raises(WorkflowError, match="must be distinct"):
        new_iteration(
            iteration_id="iteration",
            model_id="model",
            objective="Keep authority concerns separate.",
            brief=authority,
            contract=authority,
            sources=(source,),
            open_question="Are the authority files separate?",
            next_action="Reject the combined authority file.",
            root=tmp_path,
            now=NOW,
        )
