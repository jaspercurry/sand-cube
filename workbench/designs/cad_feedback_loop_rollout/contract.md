# CAD feedback-loop rollout contract

## Baseline

- Integration base: `7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3`.
- Branch: `codex/cad-feedback-loop-rollout`.
- Catalog model: `exp-190x210-single-oval-port`.
- Authoritative generator: `experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py`.
- Authoritative output directory: `build/sand_cube_190x210_single_oval_port/`.
- Pinned interpreter: `/Users/jaspercurry/Code/CAD - Enclosure/.venv/bin/python`.

## Requested behavior

Integrate the existing staged workflow, reusable geometry checks, and verified
cache around the single-oval-port experiment. Production must construct the
unchanged geometry, export every required STEP, and perform STEP round-trip
diagnostics. Review presentation must run as a separate coordinated job that
consumes an already-published hash-bound STEP and current verified sidecar.

## Invariants

- No enclosure, port, horn, bracket, joint, acoustic, removable-baffle, or
  tongue-and-groove geometry or parameter changes.
- Do not touch PR #2, its candidate, validator, or workbench records.
- Preserve every downstream-consumed STEP filename and semantic meaning,
  including the cutaway if it participates in lineage.
- Python remains authoritative and `build/` remains derived evidence.
- Production success is not invalidated by sidecar, Viewer, Snapshot, or
  static-preview failure.
- Native imports run only in coordinated workers. The
  `cad_geometry_checks` package root remains native-free while
  `cad_geometry_checks.native` is classified as native.
- Cache hits require exact source, parameter, artifact, producer schema, tool
  identity, and output verification. Release proof is forced and uncached.
- No merge, push, or PR creation.

## Measurable checks

- Exact before/after SHA-256 comparison for all production STEP outputs.
- STEP round-trip solid counts and validity remain passing.
- The separated production `generate()` path invokes no Viewer generation and
  no uncontrolled review subprocess.
- One candidate artifact hash is reused through fast, visual acceptance, fit,
  release, and independent-review gates.
- Each native stage imports/tessellates its artifact once and shares that
  result across related checks.
- Geometry claims use `cad_geometry_checks`; visual evidence proves only human
  inspection.
- Cold and warm timings are comparable; at least one verified cache hit and
  controlled source-identity invalidation are recorded.
- A deliberately failing review job leaves the successful production STEP and
  its hash intact.
- Production, review, forced release, and failure jobs report cleanup and no
  owned orphan processes.

## Visual question

Does a separately generated review presentation of the exact published
hardware-check or cutaway STEP remain a faithful inspectable view while being
fully failure-isolated from production? Use one isometric review output and
the exact artifact hash/sidecar; do not infer dimensions or fit from pixels.

## Promotion and gate order

Candidate → fast passed → visual accepted → fit passed → release passed →
independently reviewed. Later stages remain bound to the same production STEP
hash. Final release evidence requires forced uncached production/review
regeneration and a comparison with the baseline production output.

## Reversible assumptions

- Prefer the hardware-check STEP as the normal exterior review source and
  preserve the cutaway STEP when inventory shows it is lineage or review input.
- Add the smallest experiment-local verification/review adapters and thin CLI
  exposure consistent with existing package ownership.

## Genuine blockers

- A production STEP hash or geometry change.
- A required downstream STEP consumer that cannot be preserved.
- A native job with repeated unexplained crash or orphaned worker.
- A final independent review with unresolved actionable findings.
