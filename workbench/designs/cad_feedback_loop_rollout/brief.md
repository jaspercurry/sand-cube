# Session 3 — feedback-loop integration and first production rollout

Work only in your new Codex worktree for `/Users/jaspercurry/Code/CAD - Enclosure`. This worktree must start from branch `codex/cad-feedback-loop-integration` at exact commit `7f2ee3187d4d83a296d79af7bdb85bccf4564278` or, if the abbreviated hash does not resolve to that exact value, stop and report the actual SHA. Create/switch to a dedicated `codex/cad-feedback-loop-rollout` branch if needed. Never work in or modify the dirty primary checkout.

The base already contains, in order:
- staged workflow/telemetry gates;
- the independently reviewed reusable geometry-check foundation;
- the independently reviewed verified caching foundation.

Do not cherry-pick or recreate them. Integrate and exercise them.

Preflight:
1. Read `AGENTS.md` and the complete repo-local `speaker-enclosure-cad` skill, including all references it routes to for iteration, toolchain safety, visual review, geometry gotchas, and catalog policy relevant to this task.
2. Read `.cad-project/project.toml`, `.cad-project/models.toml`, and `.cad-project/enclosure-contract.md`.
3. Record the exact base SHA and prove the worktree is clean.
4. Run the native-free/lightweight preflight. Reuse `/Users/jaspercurry/Code/CAD - Enclosure/.venv/bin/python` as the pinned interpreter while invoking scripts from your isolated worktree. Do not install alternate dependencies.
5. Initialize a compact workflow state for this rollout. Preserve this delegation as the task brief, make the interpreted contract explicit, and after compaction resume from the compact workflow card instead of repeatedly rereading the long brief.

Hard boundaries:
- PR #2 is paused. Do not merge, modify, promote, or declare its candidate accepted.
- Do not change the active removable-baffle or tongue-and-groove geometry, parameters, validator, or workbench records.
- Do not change any enclosure, port, horn, bracket, joint, or acoustic geometry.
- Python source remains authoritative; `build/` remains derived evidence.
- Do not merge to `main`, push, or open a PR unless the coordinator explicitly asks.

Architecture ownership:
- `cad_verification`: contracts, policy, evidence, and compact workflow state.
- `cad_geometry_checks`: authoritative reusable measurement semantics and native adapters.
- `cad_runner`: coordination, staging, telemetry, and content-addressed cache mechanics.
- `scripts`: thin command-line adapters.
- model generators: authoritative geometry and STEP export.
- separate review entrypoints: sidecars, Snapshot, static viewers, and other presentation artifacts.

Integration wiring:
- Wire `cad_geometry_checks.native` into the repository’s native-entrypoint safety classification without making its top-level package native.
- Expose only thin, non-duplicative CLI paths needed for the staged workflow and verified artifact reuse.
- Keep policy in the owning packages rather than restating it in commands or model scripts.
- Ensure the combined foundations retain all existing focused and lightweight tests.

First production/review separation target:
Use `experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py` as the contained rollout target.

Before editing, inventory every downstream consumer of its STEP outputs. In particular, determine whether the cutaway STEP is used as lineage input; preserve it if so.

Required behavior:
- Keep authoritative geometry construction, required STEP exports, and STEP round-trip diagnostics in the production generator.
- Remove static Viewer/preview generation from the production generator.
- Add a separate coordinated review entrypoint that consumes the exact already-published STEP and current verified sidecar.
- A Viewer, sidecar, Snapshot, or static-preview failure must not discard or invalidate an otherwise successful production geometry/export job.
- Do not merely move the preview call later in the same atomic worker; it must be a distinct job consuming published artifacts.
- Add a native-free policy test proving the production `generate()` path does not invoke Viewer generation or uncontrolled review subprocesses.
- Preserve every downstream-consumed STEP and its meaning. No geometric output may change.

Progressive validation rollout:
Implement a focused representative `fast` → `visual smoke` → `fit` → `release` path for this target or the smallest existing validator/verification adapter that cleanly owns these stages.

- Reuse one hash-bound candidate across later stages.
- Import or tessellate an artifact once per stage and share the result across related checks.
- Use `cad_geometry_checks` instead of reimplementing Boolean, contact, topology, continuity, or protected-surface semantics.
- Use content-addressed cache entries only for immutable imports and measurements whose source, parameters, artifact, producer schema, and tool identities all match.
- Require forced, uncached regeneration for the final release proof.
- Enforce candidate → fast → visual acceptance → fit → release → independent review.
- Keep programmatic geometry checks authoritative for measurable claims. Visual tooling must not prove dimensions or fit.

Performance and failure-isolation evidence:
- Record comparable cold and warm timings.
- Demonstrate at least one real verified cache hit.
- Demonstrate invalidation after changing a controlled source identity.
- Demonstrate that a deliberately failing review-generation step cannot erase or roll back a successful production STEP export.
- Report successful runtime separately from unsuccessful runtime.
- Do not introduce arbitrary hard performance thresholds; gather evidence and expose the slow stage.

Verification:
- native-free/lightweight suite;
- focused new integration tests;
- entrypoint safety;
- catalog validation;
- production generator through `cad_runner`;
- separate review generation through `cad_runner`;
- one forced uncached release path;
- exact output hash/geometry comparison proving the separation refactor did not change production STEP geometry;
- clean job cleanup and no owned orphan processes.

Mandatory independent review gate:
After implementation is committed and all checks are green, spawn a separate review sub-agent. Give it this review brief verbatim:

“Review the exact diff from the recorded integration-base SHA to current HEAD as a senior CAD workflow, release-safety, and architecture reviewer. Do not implement changes. Look for accidental geometry or artifact changes, broken downstream STEP lineage, preview work still coupled to production success, stale cache/evidence acceptance, release paths that can use cache, duplicated policy or sources of truth, native imports outside cad_runner, incorrect workflow gate transitions, artifact hash drift, tests that assert implementation rather than behavior, cleanup/orphan risks, and any edits to PR #2 or the active removable-baffle model. Report findings first in severity order with precise file and line references, then residual risks and missing tests. Explicitly say when there are no actionable findings.”

Address every actionable finding, rerun affected tests and production evidence, then ask the reviewer to inspect the exact amended diff once more. Do not finalize until the final review has no unresolved actionable findings.

Commit the reviewed rollout but do not merge it. Return: exact base and final commit SHAs; files changed; architecture decisions; downstream consumer inventory; before/after and cold/warm timings; geometry/artifact hash comparison; all commands/tests/jobs and cleanup evidence; reviewer findings and dispositions; remaining risks; and whether the branch is ready for a draft process PR. Do not stop at a plan—implement, verify, independently review, and commit.

## Coordinator correction

Coordinator correction: the exact integration-base commit is `7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3`. The longer SHA in the initial delegation was a transcription error; do not treat it as authoritative. Verify your clean worktree HEAD equals `7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3` and proceed only if it matches.
