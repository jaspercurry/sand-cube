# Variant R flat-bottom synthesis feedback

## 2026-07-23 — authorization and preflight

- The user explicitly authorized entry into the later Variant R synthesis
  scope after the atomic refactor stopped at the material seam discrepancy.
- The complete original atomic-characterization brief was re-read. Its
  SHA-256 remained
  `7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`;
  it was not modified.
- Work continued only in the clean dedicated worktree on
  `codex/atomic-characterization-refactor` at
  `3ff46c29138e8b4cbdcfe542b1dc075591701eb8`.
- Local `main` remained
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868`, satisfying the saved brief's
  required ancestry check.
- The repository-local `speaker-enclosure-cad` skill and all five applicable
  references were re-read and applied.
- Pinned versions passed `cad_review.py doctor`: build123d 0.11.1, OCP
  7.9.3.1, Build123d-MCP 0.3.79, Text-to-CAD 0.3.9.
- Catalog validation passed: 10 primary models and 38 experiment families.
- The complete native-free suite passed 86 tests and 19 subtests, 76 CAD
  entrypoint checks, catalog consistency, and lint.
- The canonical checksum verification found one stale source checksum: the
  bass-reflex route source had consumed the already-approved coordinate datum
  in commit `fe33191`. The source change was exactly the geometry-preserving
  substitutions `10.0` to `d.center_y` and `base.D.center_y`; the checksum map
  was refreshed from
  `1b2fcd344726f192b37e9081b6e41588b797a1a35e3301600ba2dbe77455307d`
  to
  `8464d717b16157d3aadc7881c537c687484c08ece51aed093ccc2da52f60f872`.
- The three removable-front reference hashes still matched their canonical
  records.

## 2026-07-23 — synthesis hypothesis

- The existing hybrid perimeter reconstructs the complete wire even though
  only the bottom-center path is intended to change.
- Prior protected-section evidence found reference-only material near the top
  seam and no hybrid-only material, so reconstructing protected edges is not a
  safe implementation of the “bottom only” policy.
- The first candidate will reuse exact edge geometry from the authoritative
  perimeter for the left, right, and top, remove only the four bottom-center
  detour edges, and insert one flat lower edge between the unchanged bottom
  corner tangency points.

## 2026-07-23 — rear-ramp rail prerequisite

- A Build123d Workbench scratch reproduction confirmed that `Plane.YZ`
  preserved the ramp polygon's global Y/Z coordinates. The unplaced ramp
  occupied X `[-5, 5]`, Y `[98, 108]`, Z `[78, 89]` mm and intersected the
  main rail over the intended 1 mm Y overlap.
- Applying the source's second placement moved that same ramp to Y
  `[201, 211]`, Z `[161.5, 172.5]` mm and produced a two-solid compound.
- Removing only the redundant placement produced one valid rail solid at
  `18,459.833333 mm³`, with bounds X `[-5, 5]`, Y
  `[-64.3166667, 108]`, Z `[78, 89]` mm.
- Focused coordinated job
  `20260723T125800-validate-rail-50fbe655ec` completed in 27.341 seconds at
  552,828,928 bytes peak RSS. It validated all three rotated rails as valid
  equal-volume solids and retained three valid solids after STEP round-trip.
- The runner published the rail STEP with SHA-256
  `c0fb5fff731a3ee0603dd85309f7283964f3a1e51fd58a5522ac1d72beeda1f5`
  and diagnostics with SHA-256
  `19e56b5260941821ccab66a0013d13761ab5a8981bcd12311b3d7880dfdb4dc6`.
  The job workspace was removed and no owned process remained.
- After the change, the native-free suite again passed 86 tests and 19
  subtests, 77 CAD entrypoint checks, catalog consistency, and lint.

## 2026-07-23 — exact perimeter and lower-band synthesis

- Focused job
  `20260723T130214-validate-perimeter-c591164fdd` completed in `24.848 s`
  at `532,414,464` bytes peak RSS. It proved that each hybrid perimeter
  retains the ten exact authoritative left/right/top and corner edges,
  removes only the four lower-center detour edges, inserts one flat lower
  edge at the unchanged corner tangencies, and closes as one wire.
- Its diagnostics SHA-256 is
  `8e44f62cb1a87afe91bee13ab4a116cc51cad5df13f4802b84c1c26618e9837a`.
- Rebuilding an entire seam from sampled points was rejected because it had
  already produced protected top material drift despite similar dimensions.
  The accepted implementation instead uses the authoritative B-rep edges
  themselves.
- Focused job `20260723T131729-validate-splice-8db0a3f7de` completed in
  `29.276 s` at `565,575,680` bytes peak RSS. It proved the baffle land,
  gasket, and bucket land each form one valid solid while retaining the
  authoritative material above `Z = -80 mm` and the flat donor below it,
  joined across a `0.20 mm` overlap.
- Its diagnostics SHA-256 is
  `090844cbb11d192f30849f5ea89041c2a4e9fb5e707f062519e4b7bf13de5a08`.

## 2026-07-23 — first full fit pass and visual review

- Coordinated full job
  `20260723T133625-validate-simple-tongue-groove-baffle-7dcf39478d`
  completed successfully in `1880.163 s` at `1,348,157,440` bytes peak RSS.
  It established the exact protected seam, complementary lower ownership,
  gasket support, closure, fill, state-restoration, repeatability, and STEP
  round-trip checks.
- The first review assembly and sidecar were produced by
  `20260723T144335-package-review-5d3941813a` and
  `20260723T144429-text-to-cad-artifacts-c415ac9e32`; their assembly and
  sidecar hashes were respectively
  `f0c0c4bb5c4b25927a3f37040f11199668e3449e6358793787ad2021cbdd7b3c`
  and
  `498b178ba438578400ba4a0de3786575761b239ab5acd352eedd96dd5092e2bd`.
- Snapshot inspection exposed a remaining print-contract problem that the
  first validator did not encode: apparent straightness did not prove that
  the baffle's lowest trimmed topology lay on a planar bed face. Those
  artifacts are superseded and are not final evidence.

## 2026-07-23 — print-contact diagnosis and failed correction attempts

- Jobs `20260723T140849-validate-print-contact-042818854f`,
  `20260723T141011-validate-print-contact-11c9b4acb2`,
  `20260723T144802-validate-print-contact-90288bf53b`, and
  `20260723T144914-validate-print-contact-7397ac73d4` failed while the audit
  used conservative B-spline surface bounding boxes and minimum-bound edge
  selection. Both the candidate and reference were incorrectly reported as
  lacking contact.
- Trimmed B-rep topology then established the real condition. The accepted
  reference had a broad planar face at `Z = -91.5 mm`, `145.0 mm` wide and
  approximately `400.673 mm²`, but two transition nubs reached
  `0.350323 mm` below it. It was almost flat rather than genuinely bed-flat.
- Direct lower-material reassignment in
  `20260723T145324-validate-print-transfer-41e63a4016` left the bucket as two
  solids. The first two root formulations in
  `20260723T145446-validate-print-transfer-9f54cc9e89` and
  `20260723T145555-validate-print-transfer-5410ec3d11` failed to form one
  valid receiving bucket.
- Jobs `20260723T145709-validate-print-transfer-0cf663c4f9` and
  `20260723T145857-validate-print-transfer-ebec32f0b8` reached a valid helper
  result, but the diagnostic treated a `None` zero-overlap result as a shape
  and failed. The diagnostic was corrected without changing the geometry.
- Jobs `20260723T150106-validate-print-transfer-420d6e026d` and
  `20260723T150334-validate-print-transfer-3791f8a2a9` then reached the
  intended transfer, but still selected the loose surface-box minimum rather
  than the trimmed topology. Follow-up audits
  `20260723T150730-validate-print-contact-223ae10295` and
  `20260723T150811-validate-print-contact-17ed80f8b6` narrowed the remaining
  issue to that measurement policy.
- All failed jobs cleaned their own workspaces and left no owned orphan
  process. They are diagnostic history, not acceptance evidence.

## 2026-07-23 — final print-plane transfer

- The final source trims the baffle at the nominal `Z = -91.5 mm` print
  plane, transfers the removed lower material to the bucket, and roots it
  across the `1.0 mm` gasket gap with `0.20 mm` intentional overlap.
- Focused job
  `20260723T150947-validate-print-transfer-17f22c836f` completed in
  `103.528 s` at `943,128,576` bytes peak RSS with clean teardown and no
  owned orphan process.
- It produced one valid bucket and one valid baffle with zero overlap. The
  baffle lost `3622.016297 mm³`, the bucket gained `3827.154114 mm³`, and
  the deliberate lower root added `205.137817 mm³`.
- Its baffle contact is one planar face at `Z = -91.5 mm`, spanning
  `187.020979 × 17.552651 mm` and `2277.950023 mm²`.
- Focused candidate hashes are:
  bucket
  `ae845758e23878b781b8c71037dec802f5be3761e33829b8c6430bfd776845f2`,
  baffle
  `217fe8df7717c8e8f6576b20dbcecf9f8ca14b6058bd5b865d6c07771664be3c`,
  and diagnostics
  `31da9344a96967a87165a4938e32682dab07228c39144c13fce89e2148a3d65d`.

## 2026-07-23 — final coordinated validation

- Final full-fit job
  `20260723T151259-validate-simple-tongue-groove-baffle-74db9f9037`
  completed in `1543.325 s` at `1,380,220,928` bytes peak RSS. It exited
  successfully, removed its workspace, and left no owned orphan process.
- Final output hashes:
  - bucket STEP:
    `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`;
  - baffle STEP:
    `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`;
  - diagnostics:
    `c827b673c83dc925e1a24fe72ad71205e49f7608acb56873de59814273030196`.
- Bucket and baffle are each one valid solid before export and after STEP
  round-trip, with `0.0 mm³` overlap. All protected left/right/top material
  mismatch counts are zero, including the previously known top cube.
- Gasket support ratios are `1.0` on both parts. Each lower land supports all
  `5772` samples, the lower seal is one connected component, fill blockage is
  `0.0 mm³`, unclosed non-fill sand cap is `0.0 mm³`, and the corner closure
  audits pass.
- The print-contact check measures one `2277.950023 mm²` planar face at
  `Z = -91.5 mm`, `187.020979 mm` wide and `17.552651 mm` deep. A brim is
  assumed; physical first-layer adhesion is not validated.
- `BUILD_TOP_HINGE=False` and `BUILD_BOTTOM_SCREWS=False`. The final Stage 1
  pair intentionally contains no retention hardware.

## 2026-07-23 — exported-artifact audit and visual evidence

- Independent exported-STEP audit
  `20260723T153848-validate-print-contact-e0d9ded786` completed in
  `17.144 s` at `545,046,528` bytes peak RSS. Its diagnostics SHA-256 is
  `831a8d59c1224810539bdd4017c862c68a89c93e0a72cf3c963831f36f2830ea`.
  It measured the reference's `0.350323 mm` below-plane transition and the
  final candidate's `0.0 mm`.
- Final review package job
  `20260723T153916-package-review-8a719db8af` completed in `76.822 s` at
  `1,067,237,376` bytes peak RSS. The two-solid, zero-overlap assembly STEP
  SHA-256 is
  `ffcd16f32f113f992666eadadb3c29a82fc4b0b339e38affc2fc49495aaa31c8`;
  its diagnostics SHA-256 is
  `caeca3626142101a0946e1f307b3ecbb034832fbb642e7d5e6981addfef755f8`.
- Assembly sidecar job
  `20260723T154042-text-to-cad-artifacts-72d19abd68` completed in `6.057 s`
  at `484,720,640` bytes peak RSS. The current sidecar SHA-256 is
  `316766b458c6ccfe46db22ad69b1382ab08f053ddac328b1667dc3ed3dfe7b66`.
- Baffle sidecar job
  `20260723T154208-text-to-cad-artifacts-2baa807349` completed in `4.552 s`
  at `425,508,864` bytes peak RSS. Its SHA-256 is
  `ce23059d97ac3d5a9fc56bfbffa6a7c03d3bd22ab5a843d7ccf2f431d016c0d4`.
- Snapshot job
  `20260723T154224-text-to-cad-artifacts-bcee70e3a7` completed in `4.648 s`
  at `1,524,334,592` bytes peak RSS. The inspected isometric overview SHA is
  `9150298aca8a3ed8752708f338d65d2e4271ef67ddde1e2a26177ea3ef33620d`;
  the inspected isolated baffle-front SHA is
  `23f0d231d12607f0f189a3e0fd78479f0d1f8c6eaab6261c697dadb7cd7d8944`.
- The overview shows a continuous sculpted left/right/top seat, no unwanted
  corner hunks, and no new exterior discontinuity. The isolated baffle view
  shows a straight lower boundary with no transition nubs.
- The read-only Viewer loaded the exact final review assembly and current
  sidecar as two named components: `Variant R bucket` and
  `Variant R removable baffle`. The hash-bound URL and session record are in
  `viewer-record.json`.
- All final native jobs cleaned their workspaces and left no owned orphan
  process.

## 2026-07-23 — release verification packet

- The standard contract validated for the composed `fast`, `fit`, and
  `release` profiles.
- The release review packet validated with status `pass` and no issues. Its
  contract fingerprint is
  `11b0b386b1ed207b18ebb501ec293106923a3ab83f8a14f39844ff06b1af33cb`;
  source fingerprint is
  `cbb0a31f2da36fd65c557a6d6256a71f90f04680c019293cc55eb07d5c005c5c`;
  and final input fingerprint is
  `ec3048be60f487964be7d559304652d547bc68d43dd073cab28682e3a2194d38`.
- The final generated contract JSON SHA-256 is
  `6c4a7c59823edca82a454e07ffe481de88fe17b35feeb95c09b39fd6465d624e`;
  the release packet SHA-256 is
  `73876c49d0055d204c6d841061e348282a4d10c67678c9431031f2978592d7a2`.
- `evidence_manifest.json` records the exact authoritative source, jobs,
  measurements, artifact hashes, Viewer record, inspected Snapshots, release
  verification, and deferred uncertainties for the accepted Stage 1 result.

## 2026-07-23 — final repository checks

- All 30 entries in the canonical working-set checksum map passed after
  deliberately refreshing only the active generator, validator, and
  superseded handoff hashes. The three immutable removable-front reference
  artifacts retained their original hashes.
- `cad_review.py doctor` passed the pinned build123d `0.11.1`,
  cadquery-ocp-novtk `7.9.3.1`, Build123d-MCP `0.3.79`, read-only Viewer
  overlay, and model-catalog checks.
- `cad_review.py check-catalog` passed with 10 primary models and 38
  experiment families.
- The complete native-free suite passed 86 tests and 19 subtests, all 82 CAD
  entrypoint-safety checks, catalog consistency, and its maintained lint
  baseline.
- The changed Python files compiled successfully; the iteration scripts had
  no Ruff findings outside the repository's intentional coordinated-entrypoint
  import pattern and legacy unused imports; JSON records parsed; and
  `git diff --check` passed.
