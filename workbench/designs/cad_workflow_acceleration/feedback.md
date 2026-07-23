# CAD workflow acceleration feedback

## 2026-07-23 — isolated start

- Created branch `codex/cad-workflow-acceleration` in
  `/private/tmp/cad-enclosure-workflow-acceleration` at
  `789cf7fb4f63d9567585198c47bc3b5b122e070f`.
- The active seam-refinement worktree and the dirty primary checkout were not
  modified.
- Read-only inspection found that the repository already has a sound
  native-free verification policy and useful job statistics, but no compact
  compaction-resume state, no enforced visual-smoke gate before fit, and no
  actionable failed-time or repeat-failure diagnosis in the statistics
  summary.
- Implementation is intentionally limited to native-free workflow state,
  runner-record analysis, thin CLI wiring, tests, and documentation.

## 2026-07-23 — read-only infrastructure audits

- Job history in the active refinement worktree showed 11 failed jobs and
  2,999.01 seconds of failed runtime. At the audit point, 44.9% of measured
  completed/failed runtime ended in failure.
- Older records reduce checker errors, intentional geometry rejections, export
  failures, preview failures, and other Python exits to generic `worker_exit`.
- Existing geometry checks duplicate empty-intersection, print-contact,
  topology, continuity, and protected-material helpers across many scripts.
  A separate native geometry-check package with tiny coordinated fixtures is a
  high-value follow-up, but it is deferred until the live seam work lands so
  its accepted diagnostics can be migrated rather than copied while changing.
- Sidecar caching and content-addressed stage caching are also separable
  follow-ups. Production preview separation must wait for the live source
  hashes and baselines to stop moving.

## 2026-07-23 — implementation and validation

- Added a standard-library-only iteration state with strict JSON parsing,
  repository-contained hash-bound file identities, atomic persistence, compact
  one-line live context, legal one-step transitions, source/authority revision
  handling, and stale-state blocking.
- Added thin `cad_review workflow` commands for initialization, resume display,
  fast/fit/release gates, evidence advancement, and revision. The existing
  minimal `cad_review verify` checkout remains usable without the optional
  workflow CLI adapter.
- Fit requires accepted visual-smoke evidence; release requires a fit pass.
  A source, brief, contract, or evidence change blocks gates until an explicit
  revision or new evidence restores a current state.
- Extended native-free runner statistics with commands and failure metadata,
  all-time outcome cost, a bounded recent health window, same-name-and-command
  failure streaks, and deterministic guidance. Historical poor outcomes remain
  visible but age out of the active stop/tighten decision.
- Added best-effort structured worker failure envelopes. New jobs distinguish
  Python exceptions, optional semantic phases, stable contract-rejection
  codes, script exits, native/forced termination, resource limits,
  cancellation, and unknown external exits. Telemetry cannot replace the
  original exception, and a successful worker cannot spoof a failed result.
- CLI smoke exercise proved: a candidate allowed `fast`, blocked premature
  `fit`, detected changed source hashes as stale, and returned to a current
  revision only after `workflow revise`.
- Final canonical native-free gate: 104 tests and 19 subtests passed; model
  catalog reported 10 primary models and 38 experiment families; 82 CAD
  entrypoints passed the safety audit; Ruff passed; `git diff --check` passed.
- Independent adversarial review passed with no remaining findings after
  checking path containment, strict authority separation, stale-hash behavior,
  transition gates, bounded health logic, exact target/command streaks,
  failure-envelope spoofing and non-masking, cleanup/no-retry behavior, and
  CLI compatibility with the minimal verification checkout.
- No native CAD, Viewer, Snapshot, browser automation, model catalog mutation,
  or geometry source ran or changed.
