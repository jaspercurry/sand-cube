# Full-perimeter enclosure/baffle reference manifest

Inventory date: 2026-07-22

## Selected pair

This is the latest available installed pair in the repository that retains the
complete sculpted nested seam and original bottom-corner geometry on all four
sides. It is the correct external-package reference for the future
integral-front / bottom-hatch branch.

Bucket:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/centered_captive_nut_bucket.step`

- SHA-256:
  `39e6b2d95317d2348afd992ceda2e98d16a383820a3846737e21228ef1c41486`
- STEP round trip: one valid solid, 376 faces.

Baffle:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/centered_captive_nut_baffle.step`

- SHA-256:
  `1dd518458c8fed6792c4acd91f0717b353288c18e49c5b1c6ba31f2c9cc6af03`
- STEP round trip: one valid solid, 166 faces.

Installed assembly reference:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/centered_captive_nut_assembled.step`

- SHA-256:
  `4595684887c4fb239dd8fefaeb7307a797c3673281df19f3d709b659b3440bf2`
- STEP round trip: nine valid solids, 600 faces. This includes the installed
  bucket, baffle, gasket/hardware references and is for fit/exterior review.

Diagnostics:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/diagnostics.json`

- SHA-256:
  `7194ac15b3c78e272ae60d9b1115be6129f0fdfbfd7cbfdcef32593cddbff04d`
- Records zero bucket/baffle hard-part overlap, a continuous 5 mm gasket at a
  modeled 1.15 mm closed gap, unchanged exterior bounds, valid bucket/baffle
  STEP round trips, and the authoritative exterior as preserved. The owning
  source separately constructs and validates four explicit baffle corner-
  closure panels.

## Why this is the correct reference

- `lightweight_coherent_closure/README.md` explicitly says this sibling
  preserves the complete exterior and nested seam.
- Its joint is constructed with the authoritative
  `_nested_split_envelope()`, continuous gasket backing, and four explicit
  `_baffle_corner_closure_panels()`.
- It predates the later hybrid architecture that retained only the left/right/
  top sculpted seam and replaced the bottom with a flat baffle-printing edge.
- Therefore it preserves the bottom corner the user wants for an integral
  front, where vertical baffle printing is no longer required.

Do not use these as the external baseline for the bottom-hatch project:

- `simple_tongue_groove_baffle.step` — flat-bottom removable-baffle branch;
- `hybrid_seam_assembled.step` — hybrid flat-bottom relationship;
- `clean_corner_hunks_bucket.step` — useful front-hatch correction, but paired
  with the flat-bottom baffle architecture; or
- `front_component_removed_bucket.step` — intentionally removed wanted seam
  geometry and was rejected.

## Owning source

Primary closure generator:

`experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure.py`

- Current working-tree SHA-256:
  `0f318a52cf4148d2f2367a18176867acfad76e5a6827d77ca42e5395ce43ba2a`
- The whole experiment directory is currently untracked. Preserve it in place;
  do not reset or replace it.

Authoritative nested-seam ancestor:

`experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts.py`

- Current working-tree SHA-256:
  `02e415cd5a83d61fe9c01d54153c21d8e41a293eb17e45aa6a4bc53986d97f42`
- This tracked source has a pre-existing uncommitted CAD-runner guard change;
  preserve it.

The key future source boundary is
`_lightweight_common_joint(full_base)`: it receives the monolithic `full_base`
and then splits it into the nested baffle and bucket. The integral-front branch
should begin before that split, retaining or selectively reapplying the desired
bulkhead, bracing, fills, and driver structures. It should not reverse-engineer
the monocoque by fusing exported STEP faces.

## Artifact freshness caveat

The three selected STEP files were emitted on 2026-07-21 by coordinated job
`20260721T162419-generate-sand-cube-190x210-internal-squat-absorb-3d6aaab355`.
Their individual STEP round-trip checks passed and the diagnostics were
written, but the overall job later failed in the inherited preview-only robust
cutaway operation. The current untracked generator has a newer modification
time than the STEP files, so the pair is an exact hash-bound artifact reference,
not a claim that the current source has since been fully rebuilt and promoted.

When work resumes, first reproduce this pair or its exterior reference through
the coordinated lifecycle and compare it against the hashes/measurements above
before creating the integral-front branch.
