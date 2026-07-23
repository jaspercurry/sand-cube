# CAD workflow acceleration contract

## Priorities

1. Single source of truth.
2. Separation of concerns.
3. Small, elegant, reusable modules.
4. Fast and precise feedback at the cheapest useful stage.
5. A process foundation that can later be extracted from this repository.

## Required behavior

- Preserve long-lived intent in an immutable brief and contract.
- Represent only live task state, source identities, evidence identities, the
  current question, and the next action in a compact iteration ledger.
- Detect stale briefs, contracts, sources, and evidence by SHA-256 before a
  resume or expensive gate can succeed.
- Enforce the cost ladder: candidate, fast checks, visual smoke, fit, release,
  and independent review.
- Require a new revision when authoritative source changes. A new revision
  invalidates prior downstream evidence.
- Make runner statistics actionable by reporting success rate, failed-time
  share, repeated recent failures, and a concise recommendation.
- Preserve Python exception type, expected rejection code, and optional
  semantic phase in a structured worker failure envelope. Never guess a native
  or external failure cause from unstructured log text.
- Keep all new workflow and statistics logic native-CAD-free.
- Expose thin commands through `scripts/cad_review.py`; keep policy and state
  behavior outside the CLI.
- Add focused tests and documentation.

## Hard boundaries

- No enclosure, baffle, horn, bracket, joint, or acoustic geometry changes.
- No native CAD execution, Viewer launch, Snapshot generation, or browser
  automation.
- No edits to the running geometry task's worktree or branch.
- No dependency or model-catalog changes.
- No automatic retries or claims that visual evidence proves dimensions or
  fit.

## Acceptance

- The workflow ledger can be initialized, rendered as a compact resume card,
  advanced only through legal transitions, reset for a source-changing
  revision, and checked before a requested verification profile.
- Fit is blocked until visual smoke is accepted; release is blocked until fit
  passes.
- A changed tracked file makes the ledger stale and blocks the gate.
- Statistics identify avoidable failed runtime and repeated target failures
  without importing native CAD.
- New coordinated jobs distinguish Python exceptions, expected contract
  rejections, native/forced termination, resource limits, cancellation, and
  unknown external worker exits without weakening cleanup or no-retry safety.
- The canonical lightweight suite and focused tests pass.
- An independent agent reviews the exact final patch.
