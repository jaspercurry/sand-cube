---
name: speaker-enclosure-cad
description: Run measured design, diagnosis, validation, and visual-review loops for this Build123d speaker-enclosure repository. Use for enclosure, baffle, driver recess, horn, horn bracket, joint, clearance, fit, STEP/STP artifact, Text-to-CAD Viewer, Snapshot, artifact-reference, Build123d-MCP scratch, CAD rendering, or geometry-promotion work. Also use when reviewing or changing a generated CAD artifact even if no source edit is requested.
---

# Speaker Enclosure CAD

Treat parameterized Python as the source of truth and generated CAD as
hash-bound review evidence. Use the smallest candidate that can answer the
current design question, then promote an accepted result through the guarded
production build.

## Start every iteration

1. Read `.cad-project/project.toml`, `.cad-project/models.toml`, and
   `.cad-project/enclosure-contract.md`. Use
   `.venv/bin/python scripts/cad_review.py models` to distinguish stable,
   development, released, workbench, and archived baselines.
2. Identify the exact catalog record, then read its owning source, parameters,
   generator, validation script, nearest README, and existing iteration notes.
   Never assume a different enclosure variant's dimensions.
3. Preserve the user's brief verbatim in
   `workbench/designs/<iteration>/brief.md`. Translate it into a concise
   `contract.md`: baseline, requested change, invariants, measurable checks,
   visual questions, reversible assumptions, and genuine blockers.
4. For a multi-step or expensive geometry task, initialize the compact,
   hash-bound `state.json` described in `references/iteration-loop.md`. After a
   compaction or handoff, resume from `cad_review workflow show`; reread the
   long brief only when the state is stale or a material ambiguity remains.
5. Run `.venv/bin/python scripts/cad_review.py doctor` before starting Viewer
   or artifact work. Resolve safety failures; do not bypass them.
6. Read the relevant references before changing geometry:
   - [iteration-loop.md](references/iteration-loop.md) for candidate and
     promotion procedure;
   - [visual-review.md](references/visual-review.md) for evidence channels and
     artifact-local references;
   - [toolchain-safety.md](references/toolchain-safety.md) before running CAD,
     Viewer, Snapshot, MCP, or dependency commands;
   - [model-catalog.md](references/model-catalog.md) when adding, renaming,
     promoting, releasing, archiving, or moving a model;
   - [geometry-gotchas.md](references/geometry-gotchas.md) for Build123d, horn,
     bracket, sand-void, or Onshape-sensitive geometry.

## Choose the lightest useful path

Use the staged verification profiles before escalating native work: start with
`fast`, add `fit` when mating/clearance/interference/section evidence is relevant,
and require `release` for exported round-trip and visual handoff evidence. The
single policy definition is `cad_verification/policy.py`; use
`scripts/cad_review.py verify` rather than restating profile rules.
For a tracked iteration, the separate workflow state requires accepted visual
smoke evidence before fit and a fit pass before release.

- **Review an existing STEP:** validate its current sidecar, start the
  read-only Viewer, create a hash-bound link, and inspect one Snapshot overview
  plus one repository-rendered focused view only when Snapshot cannot answer
  the question.
- **Answer a localized geometry question:** use a small parameterized coupon or
  one Build123d-MCP scratch session. Export scratch only when it adds review
  value. Do not load the whole enclosure merely for context.
- **Change production geometry:** edit one owning parameter or feature at a
  time, run its deterministic checks through `cad_runner`, and publish review
  artifacts only after the build succeeds.
- **Compare alternatives:** prefer separate artifact directories and Viewer
  tabs. Add AgentCAD only when persistent A/B history, overlays, or returning
  to an earlier alternative materially helps.

## Require three evidence channels

At a meaningful visible checkpoint, provide:

1. programmatic geometry checks for measurable claims;
2. a clickable read-only Text-to-CAD Viewer link to the exact STEP and current
   topology sidecar for the user; and
3. one agent-inspected Snapshot or focused direct render: MCP rendering for
   in-memory scratch, or the repository renderer for an exported production
   STEP that Snapshot cannot show clearly.

Normally use one isometric overview and no more than one question-specific
section, clip, orthographic, highlight, or detail. State confirmed facts and
remaining visual uncertainty separately.

## Finish only after promotion

Record feedback chronologically. When the user accepts a direction, reconcile
scratch work into normal parameterized Python, run the complete relevant build
and diagnostics through `cad_runner`, regenerate the sidecar and renders,
compare the promoted result with the accepted candidate, and provide refreshed
artifact links. Update `.cad-project/models.toml` in the same change when model
identity, status, ownership, primary entrypoint, or output location changes,
and finish with `.venv/bin/python scripts/cad_review.py check-catalog`. Do not
describe scratch or stale output as complete.
