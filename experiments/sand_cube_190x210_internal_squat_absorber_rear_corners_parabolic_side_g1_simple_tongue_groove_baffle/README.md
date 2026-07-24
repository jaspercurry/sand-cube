# Variant R — sculpted removable front with flat-bottom baffle

This leaf experiment is the accepted parameterized Variant R compatibility
adapter for the bucket and removable front baffle. The production owner under
`src/enclosure_family/variant_r/` uses the continuous exact-edge donor directly
and changes only the baffle sub-sole needed for a planar printing base.

The owning generator monkeypatches inherited joint hooks only while building
and restores every changed hook and parameter in `finally` blocks. Generated
CAD remains under
`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/`.

## Stage 1 geometry

- The exact authoritative left, right, top, and corner perimeter B-rep edges
  are reused. Ten protected edges are retained, the four lower-center detour
  edges are removed, and one straight lower edge joins the unchanged bottom
  corner tangencies.
- The continuous flat-bottom donor owns the complete bucket, gasket and visible
  baffle apron. There is no active whole-part horizontal splice and no lower
  baffle-to-bucket material transfer.
- Only baffle material below the single parameter-owned sole at
  `Z = -91.495 mm` is discarded. The exact donor topology has a maximum
  sub-sole band thickness of `0.35532330335 mm`.
- The donor has exactly twelve mirrored, reference-only internal bucket sample
  omissions totaling `0.3032817572227236 mm³` over their 1 mm audit cubes.
  This is the sole authorized material-preservation delta; candidate-added
  material and every baffle/centre-section mismatch remain forbidden.
- The 5 mm × 2 mm weatherstrip contract remains driven by
  `GASKET_CLOSED_GAP_MM = 1.0`.
- Fill passages and their hollow blister supports, sand containment, the
  driver interface, sculpted corner closure, and protected exterior geometry
  remain present.

## Deferred retention

`BUILD_TOP_HINGE = False` and `BUILD_BOTTOM_SCREWS = False`.

The earlier tongue-and-groove hinge and lower-fastener geometry is not part of
the accepted Stage 1 result. Future stages must design and validate retention
against this accepted seam and print-edge baseline, including insertion,
gasket clearance, exterior breakthrough, and assembly-path checks.

## Final validation

Coordinated job
`20260724T174726-variant-r-no-splice-authorized-production-releas-9f64591b8e`
completed successfully in `1594.716 s` at `1,202,077,696` bytes peak RSS,
with clean teardown and twelve atomic outputs.

- bucket STEP SHA-256:
  `7ac00586df7d67a19c5ebaf82c2bccf4069141ea024a7fedc2e85bf6350db5ee`;
- baffle STEP SHA-256:
  `d8da00edcb94654d33b81076d27759bd2fa1049b75493154e26411d5fba30535`;
- review assembly STEP SHA-256:
  `0f04b4abf96d67ecd66a196f325c1cd1c6a1e5d2a9114adc73812961ec347185`;
- validation diagnostics SHA-256:
  `35d2e65b48caa5b5afa71d790011e0eee8ec637d554c901191ac55289c0d099f`.

Every part is one valid solid before and after STEP round-trip; the assembly is
three valid solids and pairwise overlap is zero. Bucket and baffle have zero
old-splice and unrelated full-width lower-apron edges. The exact twelve-point
bucket-only signature passes with no candidate-added material, while all thirty
retained L/R/T edge comparisons remain within `1.4254156828833717e-14 mm`.
Bucket and baffle gasket and lower-land support ratios are `1.0`; the lower
seal is one connected component; fill blockage and unclosed non-fill sand-cap
volume are zero.

The baffle terminates at `Z = -91.495 mm` on one planar
`187.026480 × 17.556411 mm` face of `2280.006033 mm²`, with no trimmed
topology below it. A brim is assumed. CAD does not validate first-layer
adhesion, print stability, material behavior, or the final physical assembly.

The complete evidence record is in
`workbench/designs/variant_r_no_splice_production/`.
