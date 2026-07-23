# Atomic characterization/refactor feedback

This is the chronological Phase A record. Findings below are descriptive; the
authoritative structured facts are in `atomic_manifest.json`.

## 2026-07-23 — task and prompt integrity

- Work began only in the dedicated Codex worktree at
  `/Users/jaspercurry/.codex/worktrees/8b9b/CAD - Enclosure`.
- `HEAD` was
  `905ef31a0bea348b6805a2ef215c75b5a9592168`, the tip used for
  `codex/atomic-characterization-base`; the worktree itself is detached and
  the branch remains checked out in its separate base worktree.
- Local `main` is
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868`, and that required commit is an
  ancestor of the task commit.
- The input-landing commit
  `2c94314b8cee90c3733991d48143375227a7d6b8` and its selected files were
  present.
- The complete `brief.md` was read. Its SHA-256 matched
  `7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`.
  It was not modified.

## 2026-07-23 — skill, rules and canonical inputs

- The repository-local `speaker-enclosure-cad` skill and its iteration,
  visual-review, toolchain-safety, model-catalog and geometry-gotcha
  references were read and applied.
- Root/scoped `AGENTS.md`, project/catalog/contract files, development and
  verification documentation, every canonical working-set root/component
  document, the complete enclosure recovery record, all selected manifests,
  the active owner/validator/handoff and relevant generator ancestry were read.
- The canonical README/manifests now describe the landed inputs as committed
  and self-contained. Historic feedback retains historic dirty-checkout
  wording for provenance; it is not a current source statement and was not
  rewritten.
- Verification of `reference_checksums.sha256` passed all 30 selected paths.

## 2026-07-23 — pinned tool preflight

- The task reused Python 3.12.13, build123d 0.11.1 and OCP 7.9.3.1 from the
  existing repository virtual environment. No package was upgraded.
- This clean worktree initially lacked ignored local tool state. The exact
  pinned Text-to-CAD 0.3.9 checkout at commit
  `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423` was cloned locally into ignored
  `build/` state; its already-installed Viewer and Snapshot runtimes were
  linked from the exact existing checkout. No network download or source-tree
  dependency change occurred.
- `scripts/cad_review.py doctor` passed all pins, catalog, read-only Viewer
  overlay and preferred-port checks.
- Catalog validation passed: 10 primary models and 38 experiment families.
- The native-free lightweight suite passed 82 tests and 19 subtests, including
  76 entrypoint-safety checks.

## 2026-07-23 — ownership and mutation characterization

- The apparent leaf owner is not self-contained. It aliases deep experiment
  modules, temporarily replaces perimeter/joint constants and functions, calls
  the complete ancestor `generate()` chain, and restores globals afterward.
- The semantic pre-split branch is the `full_base` argument entering
  lightweight `_lightweight_common_joint`. That function creates nominal and
  clearance envelopes, partitions bucket and baffle, and then adds gasket
  support, bulkhead, fill paths, bridges and braces.
- Current removable-joint dimensions are distributed: simplified closure owns
  sculpted path values and the corrected 184.3 mm/r7 broad reset; hooked owns
  bed/gasket/shoulder helpers; nested owns the 0.28 mm split envelope;
  lightweight patches the leaf gap to 1.0 mm and owns the bulkhead/support
  composition.
- This confirms that a future Variant I owner must branch semantically before
  the removable partition. The selected “integral” STEP set is still a
  removable bucket, baffle, gasket/hardware assembly and cannot be treated as
  Variant I geometry.

## 2026-07-23 — immutable reference measurements

- Ten selected STEP artifacts were imported and measured read-only with
  Build123d Workbench. Exact volume, surface area, bounds, center of mass and
  topology are recorded in `atomic_manifest.json` and projected into
  `baseline_report.md`.
- The clean bucket is one valid solid at `1,091,181.8588 mm³`; the hybrid
  bottom-ownership assembly is two valid solids, with a
  `1,111,212.8535 mm³` larger bucket and `233,360.5156 mm³` baffle.
- The selected flat baffle is one valid `231,910.4722 mm³` solid spanning
  approximately 190.0021 mm in X. Its accepted contribution remains the
  documented flat full-width edge; the measurement did not independently
  establish a continuous stable bed-contact face and minimum seating area.
- Tube and Rev C/Rev D references measured as valid multi-solid evidence.
  Their geometry was not integrated or refactored.

## 2026-07-23 — source reproduction gate

- A first runner invocation contained an incorrect shortened experiment path
  and stopped before loading source. It is not a CAD result.
- The corrected, catalog-resolved lightweight source was run once through
  `cad_runner` as job
  `20260723T040911-generate-sand-cube-190x210-internal-squat-absorb-603368ef69`.
- After 83.797 seconds and peak RSS 1,290,780,672 bytes, the current source
  failed with:
  `ValueError: rear-ramped longitudinal top rail did not produce one valid solid: 2`.
- The runner published no outputs and reaped its process group. There was no
  blind geometry retry.
- Because the authoritative lightweight base STEP was not produced, the leaf
  validator was not run. The accepted source baseline is therefore
  unreproducible at this commit. Immutable STEP references remain evidence and
  were not promoted as source.

## 2026-07-23 — exact visual evidence

- A byte-identical copy of the clean-bucket STEP was placed under ignored
  `build/workbench/atomic_characterization_refactor/near_perfect_bucket/`.
  It retains SHA-256
  `eaeed68103e3110ca3e888ece90002a7f2f98a8b174fab5906e7fb0bd9350b97`.
- Its Text-to-CAD sidecar has SHA-256
  `609bb53774ab6301a4ad724aeb62d0a0ed7b3600c93528d9502d73d8e5dc5d4b`.
- Initial Snapshot job
  `20260723T042549-text-to-cad-artifacts-55fbbd24c2` stopped before rendering
  because the ignored clean-worktree checkout lacked the already-installed
  pinned Snapshot runtime. After linking that exact runtime, sandboxed job
  `20260723T042612-text-to-cad-artifacts-88542cfab5` was cleanly reaped when
  macOS denied Chromium's MachPort rendezvous. Neither attempt produced an
  image or changed geometry.
- Snapshot job
  `20260723T042632-text-to-cad-artifacts-fe2639776f` completed in 3.095 seconds
  at peak RSS 856,621,056 bytes and produced an isometric plus one YZ center
  section from the same STEP/sidecar.
- The agent inspected both images. The isometric shows one coherent open-front
  bucket, the sculpted perimeter seat, top opening, internal rails/posts and no
  four repeated front corner hunks. The center section shows nested wall/shell
  outlines and isolated ledges, but does not prove gasket compression, lower
  ownership or printable overhang angles.
- A hash-bound read-only Viewer record was written under ignored build
  evidence. No transient Viewer selection token was used as source logic.

## 2026-07-23 — checkpoint decision

- `atomic_manifest.json` records 30 selected inputs and 30 semantic atoms.
- The generated inventory, atom map, compatibility matrix, dependency graph,
  baseline report and printability report all derive from that manifest.
- Phase B is blocked by both the required user gate and the failed source
  baseline. Variant R candidate reconciliation, Variant I geometry, acoustic
  integration and printability redesign remain later work.
- The proposed first pilot after explicit approval is the metadata-only
  `family.coordinate_contract`; no geometry atom should be extracted until the
  source baseline is repaired or an accepted reproducible source boundary is
  deliberately selected.

## 2026-07-23 — Viewer frontend repair

- The user reported that the hash-bound Viewer URL displayed `Not found`.
- The read-only 0.3.9 backend, exact STEP, and exact sidecar were all present.
  Browser inspection was used only because the failure was visible UI routing
  behavior that the server metadata endpoint could not diagnose.
- The clean worktree's ignored pinned Viewer checkout lacked its prebuilt
  `viewer/dist` frontend. The exact existing 0.3.9 frontend from the repository
  tool checkout was linked into that ignored checkout; no package, source,
  geometry, STEP, or sidecar changed.
- After reloading the same tab, the Viewer displayed
  `near_perfect_bucket.step`, its STEP tree, view controls, and release 0.3.9.

## 2026-07-23 — Characterization Checkpoint approved

- The user inspected the hash-bound `near_perfect_bucket.step` in the repaired
  read-only Viewer, said it looked good, and authorized the work to proceed.
- This approval opened Phase B. It did not make the failed source baseline
  reproducible and did not authorize geometry synthesis from STEP evidence.
- The first atom remained the proposed metadata-only
  `family.coordinate_contract`.

## 2026-07-23 — coordinate-contract pilot

- Added the native-CAD-free owner `src/enclosure_family/datums.py` for units,
  the 190x210x190 envelope, the +10 mm Y center, named planes, and axis
  polarity.
- The base `Design` now consumes that owner. Existing 190x210 source consumers
  use `Design.center_y` instead of duplicating the +10 mm datum.
- The fast contract validated eight selected requirements in 0.079 seconds at
  30,720,000 bytes peak RSS.
- The complete lightweight suite passed 86 tests and 19 subtests, catalog
  consistency, 76 entrypoint checks, and lint in 5.086 seconds at 59,359,232
  bytes peak RSS.
- Controlled native comparison job
  `20260723T100534-generate-sand-cube-190x210-internal-squat-absorb-c4d37f5ec2`
  failed after 95.849 seconds at 1,288,798,208 bytes peak RSS with the exact
  pre-existing invariant:
  `ValueError: rear-ramped longitudinal top rail did not produce one valid solid: 2`.
- The run published no outputs. It provides same-boundary evidence for the
  metadata refactor, not geometry equivalence.
- The user-accepted frozen STEP and Snapshot remain unchanged continuity
  evidence. No after-STEP or visual delta exists while the source baseline
  fails.

## 2026-07-23 — checkpoint-pause override

- The user explicitly instructed the agent not to keep stopping at checkpoints,
  to attempt the full saved brief, and to re-read the original prompt after
  context compression.
- Subsequent checkpoints will be recorded without pausing. Genuine
  safety/equivalence blockers still remain stop conditions.

## 2026-07-23 — exploratory baseline repair and equivalence stop

- After a context compression, the complete `brief.md` was read again and its
  SHA-256 again matched
  `7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`.
- Scratch Workbench measurement showed that the rear ramp was already located
  at its intended design-coordinate Y/Z envelope before a second placement was
  applied. An uncommitted correction cleared the original two-solid rail
  failure and allowed the leaf base STEP to be exported for diagnosis.
- The experiments remained outside the accepted source boundary. The resulting
  leaf base STEP has SHA-256
  `2b00cc4f7c0d9203758893ffcab2039325d072070fb33c94f001b47ef9b09203`
  and is explicitly diagnostic evidence, not an accepted baseline.
- Fit job
  `20260723T111344-validate-simple-tongue-groove-baffle-51e3ab94c6`
  then failed the protected top-seam occupancy gate at two of 1,248 samples;
  the first point was `[-45.0, -71.75, 86.25]` mm.
- Focused diagnostic job
  `20260723T113000-diagnose-seam-identity-34754b3ab1` completed in
  384.514 seconds at 1,402,896,384 bytes peak RSS. Nine of 75 nearby samples
  confirmed the same direction: the authoritative bucket contains material
  where the flat-bottom hybrid bucket does not.
- In a 4 mm cube around the first mismatch, the authoritative bucket occupied
  `35.80665201146918 mm³`, the hybrid occupied `35.40168722922 mm³`, and their
  overlap equaled the hybrid volume. The reference-only difference was
  `0.40496478224918064 mm³`; the hybrid-only difference was zero.
- Both local diagnostic sections were one valid solid after STEP round-trip.
  Their exact paths and hashes are recorded in `atomic_manifest.json`.
- This is material geometry drift, not a matching-boundary or serialization
  artifact. Correcting it would reconcile the authoritative sculpted seam with
  the flat-bottom reference, which the brief reserves for later synthesis.
- Every exploratory source, viewer-adapter, alias, and validator edit was
  reverted. The committed coordinate-contract pilot remains the only Phase B
  source change.
