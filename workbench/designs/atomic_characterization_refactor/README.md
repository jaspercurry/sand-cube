# Atomic characterization/refactor — Phase A checkpoint

Status: **Characterization Checkpoint — waiting for user approval.**

No geometry source was edited. No removable-front references were reconciled,
no Variant I geometry was created, and no deferred component was integrated.

## Governing records

- `brief.md` — verbatim user request; do not edit
- `contract.md` — interpreted operational boundary
- `feedback.md` — chronological work log
- `atomic_manifest.json` — authoritative input, atom, evidence and checkpoint
  description
- `render_phase_a_reports.py` — deterministic Markdown projection

## Generated checkpoint views

- `inventory.md`
- `atomic_map.md`
- `compatibility_matrix.md`
- `dependency_graph.md`
- `baseline_report.md`
- `printability_report.md`

## Architecture proposal

- `proposed_architecture.md`

## Blocking result

The current owning lightweight source does not reproduce a baseline. Its
single controlled native run failed because the rear-ramped longitudinal top
rail produced two solids rather than one, so the dependent leaf validator
could not run.

Phase B must not start until the user approves the checkpoint and decides how
to resolve the source-baseline boundary.
