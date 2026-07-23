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
