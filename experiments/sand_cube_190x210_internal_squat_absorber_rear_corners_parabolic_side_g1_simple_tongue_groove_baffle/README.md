# Variant R — sculpted removable front with flat-bottom baffle

This leaf experiment is the accepted parameterized Stage 1 owner for the
Variant R bucket and removable front baffle. It inherits the authoritative
full-detail enclosure and changes only the lower joint band needed to give the
baffle a genuinely planar printing base and the bucket complementary material
ownership.

The owning generator monkeypatches inherited joint hooks only while building
and restores every changed hook and parameter in `finally` blocks. Generated
CAD remains under
`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/`.

## Stage 1 geometry

- The exact authoritative left, right, top, and corner perimeter B-rep edges
  are reused. Ten protected edges are retained, the four lower-center detour
  edges are removed, and one straight lower edge joins the unchanged bottom
  corner tangencies.
- The authoritative joint is retained above `Z = -80 mm`; the flat-bottom
  donor is retained below that plane. The baffle land, gasket, and bucket land
  are joined across a `0.20 mm` splice overlap.
- Material below the nominal baffle print plane at `Z = -91.5 mm` is moved to
  the bucket and rooted across the `1.0 mm` gasket gap with `0.20 mm`
  intentional overlap. This removes the reference baffle's two
  `0.350323 mm` below-plane transition nubs.
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
`20260723T151259-validate-simple-tongue-groove-baffle-74db9f9037`
completed successfully in `1543.325 s` at `1,380,220,928` bytes peak RSS,
with clean teardown and no owned orphan process.

- bucket STEP SHA-256:
  `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`;
- baffle STEP SHA-256:
  `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`;
- validation diagnostics SHA-256:
  `c827b673c83dc925e1a24fe72ad71205e49f7608acb56873de59814273030196`.

Both parts are one valid solid before export and after STEP round-trip, with
zero overlap. Protected left/right/top material mismatch counts are zero.
Bucket and baffle gasket support ratios are `1.0`; both lower-land support
ratios are `1.0` over `5772` samples; the lower seal is one connected
component; fill blockage and unclosed non-fill sand-cap volume are zero.

The baffle terminates at `Z = -91.5 mm` on one planar
`187.020979 × 17.552651 mm` face of `2277.950023 mm²`, with no trimmed
topology below it. A brim is assumed. CAD does not validate first-layer
adhesion, print stability, material behavior, or the final physical assembly.

The complete evidence record is in
`workbench/designs/variant_r_flat_bottom_synthesis/`.
