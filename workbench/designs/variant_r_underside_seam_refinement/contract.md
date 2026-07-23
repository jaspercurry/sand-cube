# Variant R underside-seam refinement contract

Status: candidate checkpoint complete and awaiting user review; production
promotion remains gated on the single approval required by the brief.

## Baseline and authority

- Catalog model: `development-190x210-tongue-groove`
- Commit: `789cf7fb4f63d9567585198c47bc3b5b122e070f`
- Units: millimetres
- Authoritative generator:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle.py`
- Baseline generator SHA-256:
  `6d8072eb32a1e86b54528fe80144155d0fc2b9d0996bdc76a8168c06e4c91f0c`
- Baseline validator SHA-256:
  `13e0dc227c64cfaa555e0a709ba7220c373319c5289f23bd3769aee871e7ddef`
- Design coordinates: X left/right, Y front/rear with front at negative Y,
  and Z bottom/top.

The three canonical STEP files are immutable, hash-bound evidence only. Python
remains authoritative.

## Requested change

Remove the `Z = -80.1 mm` construction boundary and associated normal kink from
both visible exteriors. Replace the lower-ownership policy with a baffle-owned
front apron/planar sole and complementary bucket recess whose shared lower
boundary is intentional, mirrored, and hidden on or behind the underside.

The candidate must not modify the production owner before its seam placement,
ownership, print sole, wall thickness, gasket continuity, and visual result
have been shown at the required checkpoint.

## Checkpoint candidate architecture

- Reuse the authoritative exact-edge common joint with the hybrid perimeter;
  do not call the whole-part `Z = -80 mm` splice.
- Keep the unspliced bucket and gasket definitions unchanged.
- Intersect only the baffle's `0.355323 mm` sub-sole excess with the half-space
  `Z >= -91.495 mm`.
- Discard that underside-only excess instead of transferring it to the bucket.
- Do not apply same-domain unification, splitter removal, or healing to any
  visible exterior face.

The only newly required topology is the intentional planar baffle sole and its
underside perimeter at `Z = -91.495 mm`. There is no new boundary above the
sole or across the visible lower-front apron.

## Geometry invariants

1. Preserve the original continuous exterior surface definitions above the
   explicitly measured lower-corner/underside band.
2. Preserve the accepted sculpted left/right/top seam and corner closures
   above the new transition.
3. Preserve driver opening/recess, mounting interfaces, fill passages and
   blisters, sand containment, wall structure, and protected exterior.
4. Keep bucket and baffle separate, single valid solids before and after STEP
   round-trip, with overlap at or below `0.001 mm³`.
5. Keep both gasket support ratios at `1.0`, the lower gasket run as one
   connected component, and bottom-corner sealing complete.
6. Keep all baffle minimum-Z topology on one planar sole. Contact width and
   area must be at least `187.020979 mm` and `2277.950023 mm²`, respectively.
7. Do not recreate the reference baffle's `0.350323 mm` transition nubs.
8. Keep `BUILD_TOP_HINGE=False` and `BUILD_BOTTOM_SCREWS=False`, and restore
   every patched ancestor attribute.

## Topology and continuity acceptance

- Zero unrelated horizontal or near-horizontal B-rep edges may cross the
  visible lower-front baffle apron or corresponding bucket exterior.
- No construction-plane or same-domain Boolean boundary may remain at the old
  splice height.
- Every new visible boundary must be an intentional ownership or geometric
  feature; its paired surface normals must be continuous or the candidate is
  rejected.
- Localized surface deviation above the permitted lower band must remain
  within `0.01 mm`, with zero material difference preferred.
- Visible face/edge topology is compared to both the earlier flat-bottom
  baffle and the accepted sculpted reference.

## Checkpoint evidence

The exact candidate must provide:

- deterministic topology, continuity, deviation, validity, overlap, fit,
  gasket, wall-thickness, and print-contact measurements;
- a normal desk-level front render, a low underside render, and one
  bottom-corner ownership section;
- matched smooth-shaded earlier/new close-ups with identical camera, lighting,
  edge-overlay, and tessellation settings;
- a separate edge-overlay render;
- a fine review mesh with recorded chordal and angular tolerances; and
- a current topology sidecar plus a read-only Viewer link.

The production generator and validator remain unchanged until the user accepts
this checkpoint.
