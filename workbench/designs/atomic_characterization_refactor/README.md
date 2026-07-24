# Atomic characterization/refactor

Status: **Phase B implementation in progress; current Variant R baseline
reproduced.**

The user accepted the Phase A visual evidence and authorized Phase B. The
metadata-only `family.coordinate_contract` pilot is complete. The user then
explicitly instructed the agent to record but not pause at later checkpoints.
No removable-front references have been reconciled, no Variant I geometry has
been created, and no deferred component has been integrated.

## Governing records

- `brief.md` — verbatim user request; do not edit
- `contract.md` — interpreted operational boundary
- `feedback.md` — chronological work log
- `atomic_manifest.json` — authoritative input, atom, evidence and checkpoint
  description
- `workflow-card.md` — concise resume state for the current implementation
- `current-baseline-evidence.json` — durable current-base fit/equivalence facts
- `render_phase_a_reports.py` — deterministic Markdown projection
- `coordinate_contract.json` — staged verification contract for the first atom

## Generated checkpoint views

- `inventory.md`
- `atomic_map.md`
- `compatibility_matrix.md`
- `dependency_graph.md`
- `baseline_report.md`
- `printability_report.md`
- `pilot_report.md`

## Architecture proposal

- `proposed_architecture.md`

## Current geometry boundary

The failed rail reproduction recorded during the earlier Phase B pilot is
historical. Commits through `789cf7f` repaired that deterministic failure and
established the current flat-bottom Variant R closure. On exact combined base
`c25cddb`, the active Python source and validator reproduce the accepted bucket,
baffle, and six protected sections with zero bidirectional material difference
at `1e-5 mm³`, matching topology and mass properties, zero overlap, and passing
STEP round-trips.

The accepted geometry intentionally includes the known imperfect flat-bottom
missing-material relationship. This refactor must preserve it; correcting that
relationship is the next geometry-change task after the architecture work.
