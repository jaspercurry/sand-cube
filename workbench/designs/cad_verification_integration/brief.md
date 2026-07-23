You are the integration session for two completed CAD infrastructure foundations in the CAD - Enclosure repository.

Use the repo-local speaker-enclosure-cad skill and follow every AGENTS.md in scope. Start from the supplied current working-tree snapshot. Preserve all in-flight user work and do not alter active enclosure geometry.

Completed inputs:
- Session 2 commit 3282059b413e0d92a747d719a344e52c1dd4ea65 — locked pytest/Ruff dev group, native-free lightweight CI/check runner, CAD-job statistics core and cad_review stats wiring, tests, DEVELOPMENT.md.
- Session 3 commit b7bb8beacf714c5dcc7401562b228adfff61cd10 — standard-library-only cad_verification package with authoritative contract/result/review-packet dataclasses, centralized fast/fit/release policy, evaluation, validation, deterministic serialization/fingerprints, narrow measurement/artifact protocols, examples, tests, README.

The incoming working tree is intentionally dirty and may already contain untracked or modified versions of foundation files. Before integrating, compare the exact file lists and patches of both commits against the current working tree. Do not blindly cherry-pick across untracked collisions. Preserve the user's current versions and unrelated changes. Incorporate the two commits semantically and stage only the integration-owned paths. Record both source commit hashes in your final report.

User priorities, in order:
1. Single source of truth.
2. Separation of concerns.
3. Elegant modular code.
4. Fast, precise feedback at the right stage without unnecessary CAD runtime.
5. Reusable AI-CAD fundamentals that can later be extracted to another repository.

Objective:
Turn the two isolated foundations into one proven repository workflow without refactoring or changing the active production enclosure model.

Required outcomes:
- Integrate all sound Session 2 and Session 3 changes without duplicating policy, schema, dependency, or command definitions.
- Add cad_verification and its tests to the maintained Ruff/lightweight-check surface established by Session 2.
- Add the smallest clean native-CAD-free cad_review CLI seam for validating a design contract/review packet and selecting/reporting fast, fit, and release profiles. Reuse the package API; keep argparse/formatting thin. A missing or UNVERIFIED requirement must never produce success.
- Keep policy, execution/adapters, serialization, and CLI separate. The portable core must continue to import no Build123d, OCP, cad_runner, Viewer, or model module.
- Connect the framework to one repository-owned joint-coupon proof, not the active enclosure model. Inspect .cad-project/models.toml and use the actual cataloged joint-coupon owner/entrypoint. Adapt existing deterministic checks; do not change coupon geometry merely to fit the framework.
- Produce a standard review packet for that proof with stable requirement IDs, source/input/toolchain fingerprints, expected versus actual measurements, units/tolerances, PASS/FAIL/UNVERIFIED status, evidence channel/tier, cost, diagnostics, artifact hash/path, and remaining uncertainty.
- Demonstrate staged feedback: a genuinely cheap fast result; fit checks only where they add mating/clearance/interference/section evidence; release adds round-trip and required visual evidence. Measure/report timings so we can see whether the split is useful.
- Follow the repository visual-tool roles exactly:
  * programmatic geometry checks are authoritative for dimensions, clearance, interference, validity, topology, and fit;
  * Viewer is the human interactive channel, and any copied # reference must be recorded with exact STEP path/hash and translated to a semantic source feature, never retained as source logic;
  * Snapshot is the agent review channel from the exact STEP and sidecar loaded in Viewer, normally isometric plus one question-specific section/detail, importing/tessellating once and reusing it across cameras;
  * Build123d-MCP render_view is scratch-only before a production STEP exists;
  * focused renderer is fallback for a necessary diagnostic Snapshot cannot express;
  * browser automation is last-resort interaction testing only.
- Run the coupon through cad_runner for every heavy/native operation. Generate exact sidecar/Snapshot evidence through scripts/cad_review.py. Inspect the direct render yourself. Do not drive the interactive Viewer.
- Update the minimum authoritative docs/rules so later CAD agents know when to run fast, fit, and release and where the single policy definition lives. Link to the source rather than duplicating the schema/profile rules in prose.
- Add focused integration/CLI tests, including nonzero behavior for failed, malformed, stale, missing, and UNVERIFIED evidence.
- Run the canonical lightweight gate, catalog check, entrypoint safety, lock consistency, and the relevant coupon production checks. Do not add heavy CAD to CI.
- Commit only the integrated scoped changes. Report the integration commit hash, current branch/ref, exact tests and timings, exact STEP/sidecar/packet/Snapshot paths and STEP hash, Viewer URL if available, visual inspection, known limitations, and a concise handoff for an independent reviewer.

Hard boundaries:
- No refactor or functional geometry edit to any active enclosure/baffle/horn/bracket model.
- No model catalog lifecycle change unless integration uncovers a real existing catalog inconsistency; report rather than silently broadening scope.
- No duplicate hand-authored JSON schema beside Python dataclasses.
- No transient Viewer # index in source or contract logic.
- No heavy CAD in CI, watch loops, browser-driven review, surprise dependency upgrades, or broad Ruff cleanup.
- Do not publish, push, merge, or open a PR.

An independent review sub-agent will inspect your completed integration afterward. Optimize for a small, auditable patch and make the reviewer's evidence easy to reproduce.
