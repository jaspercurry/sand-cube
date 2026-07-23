# Variant R underside-seam refinement feedback

## 2026-07-23 — clean worktree and preflight

- Created clean worktree `/private/tmp/cad-enclosure-remove-splice` and branch
  `codex/remove-visible-splice-line` at authoritative commit
  `789cf7fb4f63d9567585198c47bc3b5b122e070f`.
- Left the dirty primary checkout untouched.
- Read the repository CAD skill, applicable iteration/visual/safety/geometry
  references, project configuration, model catalog, enclosure contract, prior
  briefs/contract/feedback/evidence, active owner/validator/README/HANDOFF, and
  canonical removable-front source/evidence manifests.
- Verified the atomic brief SHA-256 remains
  `7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`.
- Verified the generator, validator, and all three canonical reference hashes
  match their recorded values. All 30 canonical working-set checksums pass.
- `cad_review.py check-catalog` passes with 10 primary models and 38 experiment
  families.
- `cad_review.py doctor` passes against the pinned project environment and
  existing read-only Text-to-CAD runtime via `TEXT_TO_CAD_ROOT`; no Viewer was
  started.
- The clean worktree contains no ignored `build/` artifacts, so the baseline
  must be regenerated through `cad_runner`, as required.

## 2026-07-23 — read-only source diagnosis

- The unwanted boundary is source-explained, not merely a Viewer triangle:
  `_splice_flat_bottom_band()` intersects complete bucket, baffle, and gasket
  solids with overlapping Z-aligned boxes at `BOTTOM_SYNTHESIS_MAX_Z_MM =
  -80.0`, then fuses the upper and lower pieces across
  `BOTTOM_SYNTHESIS_OVERLAP_MM = 0.20`.
- `_transfer_baffle_below_print_plane()` performs a second complete Z-plane
  trim at `BAFFLE_PRINT_BED_Z_MM = -91.5`, transfers the removed material to
  the bucket, and adds a rearward overlapping root.
- The corrective candidate will first test whether the exact-edge
  `flat_bottom_donor` can be used without the `-80 mm` whole-part splice, then
  constrain any ownership-changing Boolean to the underside/joint rather than
  the visible exterior.

## 2026-07-23 — baseline cascade and focused base regeneration

- Coordinated job
  `20260723T165543-generate-sand-cube-190x210-internal-squat-absorb-4780612691`
  reproduced the inherited full-cascade failure documented in the active
  HANDOFF. It failed after `280.009 s` at `1,241,284,608` bytes peak RSS while
  the single-oval-port generator created a preview cutaway:
  `_fresh_solids(base & clip)` received a `None` intersection. No production
  or candidate geometry had run yet.
- The coordinator made no final outputs, removed the job workspace, reaped the
  worker process group, and reported no remaining owned processes. The known
  deterministic failure was not retried.
- A focused source build now regenerates the exact one-solid base operations
  that precede the preview (`_path_solids` clearances plus `build_base`) and
  exports the base directly to the active and validator output roots through
  `cad_runner`. It does not copy a STEP from another checkout and does not
  bypass any geometry needed by the standalone Variant R harness.

## 2026-07-23 — authoritative base and current Stage 1 baseline

- Coordinated job
  `20260723T170702-regenerate-authoritative-base-ae5cf4ac34` completed in
  `97.851 s` at `1,240,186,880` bytes peak RSS. It produced one valid
  authoritative base solid in both required roots.
- Coordinated job
  `20260723T181011-validate-simple-tongue-groove-baffle-62ccacdf1c`
  completed in `1518.415 s` at `1,400,471,552` bytes peak RSS. The unchanged
  standalone Stage 1 validator passed complete-body retention, L/R/T identity,
  flat-bottom seal continuity, print contact, overlap, isolation, inspection
  section, and STEP round-trip checks.
- The freshly exported current baffle reproduces the reported topology:
  `103` faces and `282` edges.

## 2026-07-23 — candidate exploration and ownership decision

- The direct exact-edge no-splice candidate was built from the authoritative
  source by patching only the hybrid perimeter and omitting both Z-plane
  whole-part operations. Coordinated job
  `20260723T174206-build-unspliced-candidate-ee8d4dbbff` completed in
  `249.027 s`.
- That direct baffle restored the intended topology (`94` faces, `266` edges)
  and had no old splice edge, but its natural lower surface terminated at
  `Z = -91.850323 mm` without a planar minimum face. It was therefore rejected
  as a printable candidate rather than promoted.
- Coordinated sole sweep
  `20260723T180344-sweep-sole-plane-b300e5d0dc` showed that
  `Z = -91.495 mm` produces one planar contact face with
  `187.026480 mm` width and `2280.006033 mm²` area, clearing the existing
  contact minima.
- The accepted checkpoint candidate keeps the exact-edge bucket, baffle, and
  gasket joint definitions, intersects only the baffle's sub-sole excess with
  `Z >= -91.495 mm`, and discards the `0.355323 mm` underside band. It does
  not transfer that band to the bucket and does not unify or heal visible
  exterior faces.
- Final gasket-enabled build job
  `20260723T185028-build-trimmed-unspliced-candidate-6c8f3d32c9`
  completed in `270.720 s` at `1,341,063,168` bytes peak RSS. It published
  one valid bucket, baffle, and gasket solid plus a valid three-solid
  assembly.

## 2026-07-23 — exported topology and continuity audit

- Final exported-B-rep audit job
  `20260723T185509-audit-exported-topology-a6df2e3c95` completed in
  `194.551 s`; its output is byte-identical to the previous audit
  (`df0404c14166db6ce6bd0236149fd50d5f8bf505b939cd115f3813d6377233a2`).
- Topology comparison:
  - earlier flat-bottom baffle: `94` faces / `265` edges;
  - current spliced baffle: `103` faces / `282` edges;
  - direct unspliced donor: `94` faces / `266` edges;
  - trimmed no-splice candidate: `91` faces / `257` edges.
- The current baffle contains eight edges at the old splice height and four
  full-width visible lower-apron construction edges. The candidate baffle and
  bucket each contain zero old-splice edges and zero unrelated visible
  lower-apron edges.
- Above the underside sole, bidirectional point deviation between the candidate
  baffle and the unspliced donor is at most
  `1.484022251031871e-8 mm`. The maximum unambiguous interior normal change
  across `574` sampled comparisons is `0.000001207418°`.
- The candidate bucket and unspliced bucket agree within
  `1.4210854715202004e-14 mm` with `0°` sampled normal change.
- Because the candidate creates no new visible boundary, there is no visible
  boundary normal discontinuity to accept. The only new boundary is the
  intentional sole perimeter at `Z = -91.495 mm`, where a normal break is
  required by the planar print-contact face.

## 2026-07-23 — matched visual review and fine sidecar

- Snapshot job
  `20260723T190142-text-to-cad-artifacts-9666593047` rendered the earlier,
  current, and candidate baffles with identical front camera, orthographic
  projection, theme, lighting, framing, and display settings. Separate smooth
  and edge-overlay outputs were produced.
- Direct inspection shows the full-width topology line only in the current
  edge-overlay image. The candidate has no corresponding line, and its smooth
  lower-apron shading has no kink at the former splice height or increased
  lumpiness relative to the earlier reference.
- Snapshot job
  `20260723T190311-text-to-cad-artifacts-1b61110ecc` produced the exact
  three-part assembly isometric, low-underside, and `YZ @ X=86 mm`
  bottom-corner section views. The intended driver/recess, sculpted seam,
  gasket path, and underside parting geometry remain present.
- The first Snapshot launch was blocked by the macOS sandbox's Mach-port
  restriction; it produced no output. The same deterministic repository
  Snapshot command succeeded with the required local renderer permission.
- The first explicit fine sidecars were generated from scratch-path copies.
  Snapshot correctly treated those embedded artifact paths as stale and
  replaced them with adaptive sidecars. The generator was corrected to build
  against staged mirrors of the final repository paths, then rerun through
  `cad_runner`.
- Final fine sidecars use absolute `0.01 mm` chordal deflection and
  `0.03 rad` (`1.718873°`) angular deflection. The exact assembly sidecar is
  `246,875,984` bytes with SHA-256
  `ebc40ca97fd38f04731d1d4f82233da9101a19dfee57c10496a032e7f10db612`.

## 2026-07-23 — existing-check gate and checkpoint

- Coordinated job
  `20260723T190958-validate-trimmed-candidate-existing-checks-f2c9f2d837`
  applied the accepted standalone validator's body-retention, flat-bottom seal,
  sampled land-support, and print-contact methods to the exported candidate.
  It completed in `286.155 s`.
- Both bottom mating lands have `438.0 mm²` planar audit area and `1.0`
  sampled support across `5772` samples each. The bottom seal has one connected
  component. Full gasket support is `1.0` on both parts against a `0.985`
  minimum.
- Exported baffle contact is one planar face at `Z = -91.495 mm`, with
  `187.026458 mm` width and `2280.003992 mm²` area.
- Bucket/baffle, gasket/bucket, and gasket/baffle overlap are all `0.0 mm³`.
  Each part round-trips as one valid solid; the assembly round-trips as three
  valid solids. Patched shared source state is restored.
- The production generator, validator, catalog, canonical references, and
  released artifacts remain unchanged. The candidate is ready for the required
  user checkpoint; production promotion has not begun.
