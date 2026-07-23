# CAD verification integration contract

## Baseline

- Integration inputs: `3282059b413e0d92a747d719a344e52c1dd4ea65` and `b7bb8beacf714c5dcc7401562b228adfff61cd10`, both based on `42db80c8c5575e8df00c1dddd76b27362f1d42fc`.
- Cataloged proof: model `joint-coupon`, source `workbench/designs/joint_coupon/model.py`, entrypoint `workbench/designs/joint_coupon/build.py`, parameters `workbench/designs/joint_coupon/params.json`, output `build/workbench/joint_coupon`.
- Active enclosure, baffle, horn, bracket, and catalog lifecycle records are outside the change boundary.

## Required behavior

- `cad_verification/policy.py` remains the only definition of profile composition, check costs, and evidence-channel meanings.
- The portable package and `cad_review` verification path import no native CAD, Viewer, runner, or model module.
- `cad_review verify contract` validates and reports the selected profile; `cad_review verify packet` returns zero only for a semantically valid packet whose complete selected profile is PASS and whose artifacts/source/input fingerprints are current.
- Coupon execution uses its unchanged geometry construction and existing deterministic checks, partitioned as native-free fast analytic invariants, fit-only mating/interference/section evidence, and release-only STEP round-trip plus Viewer/Snapshot evidence.
- All coupon, sidecar, and Snapshot native work is coordinated through `cad_runner`; no interactive Viewer automation or transient `#...` reference is used.

## Measurable acceptance

- Source packages from both commits are integrated without duplicate schemas or dependency pins.
- Contract validation covers every nonempty fast/fit/release layer; release includes round-trip and visual requirements.
- Failed, malformed, stale, missing, and UNVERIFIED packet evidence all produce nonzero CLI status.
- Fast, fit, and release jobs each record wall time, worker PID, peak RSS, exit status, cleanup, outputs, and orphan count.
- Release has a current assembly STEP, topology sidecar, isometric Snapshot, one joint-section Snapshot, hash-bound read-only Viewer link, and a standard review packet that validates from disk.
- Canonical lightweight checks, catalog consistency, entrypoint safety, lock consistency, and coupon production checks pass.

## Visual question

Does the exact exported coupon preserve two coherent rigid parts and a readable tongue/groove joint? Answer with one isometric Snapshot and one mid-plane joint section from a single imported/tessellated STEP and sidecar. Programmatic measurements, not pixels, decide dimensions, gasket placement, clearance, interference, topology, and fit.

## Reversible assumptions and blockers

- The worktree-local `.venv` may be absent; reuse the existing repository environment from the main checkout without installing or upgrading runtime CAD packages.
- If the pinned Viewer checkout is absent from this worktree, use an existing matching checkout through `TEXT_TO_CAD_ROOT`; do not fetch or upgrade it during integration.
- Physical printed fit and material behavior remain explicitly uncertain.

## Promotion comparison

The release STEP must reproduce the same parameterized source geometry and existing deterministic volumes/checks as the prior coupon entrypoint. No active production enclosure output is generated or compared because it is outside scope.
