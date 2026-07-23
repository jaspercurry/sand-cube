# Removable front-baffle source manifest

Inventory date: 2026-07-23

## Reference artifacts

| Local link | Repository path | SHA-256 | Approved contribution |
|---|---|---|---|
| `links/near_perfect_bucket.step` | `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/reference_evidence/clean_corner_hunks_bucket.step` | `eaeed68103e3110ca3e888ece90002a7f2f98a8b174fab5906e7fb0bd9350b97` | Clean curved seat and removal of four unwanted hunks; not bottom ownership |
| `links/bottom_ownership_assembly.step` | `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/reference_evidence/hybrid_seam_assembled.step` | `90558975e0e8fb735534b53a73eb7970d3bdddd6aeda34fb821380915877bab0` | First/larger solid only, approximately `1111212.853475 mm3`, as bottom complement reference |
| `links/flat_bottom_baffle.step` | `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/reference_evidence/simple_tongue_groove_baffle.step` | `23c4d67927bbec6702c300c9912a7542383de093940378184b3d932fee3971c2` | Full-width flat print edge and associated baffle material ownership |

All three are derived evidence. The near-perfect bucket is explicitly
unpromoted and STEP-derived.

## Current source owners

| Role | Repository path | SHA-256 / state |
|---|---|---|
| Active leaf generator | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle.py` | `6d8072eb32a1e86b54528fe80144155d0fc2b9d0996bdc76a8168c06e4c91f0c`; accepted Stage 1 source |
| Standalone validator | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/validate_simple_tongue_groove_baffle.py` | `13e0dc227c64cfaa555e0a709ba7220c373319c5289f23bd3769aee871e7ddef`; current Stage 1 validator |
| Corrective handoff | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/HANDOFF.md` | `fce0245bbc2227152ee27b23b2cf2740a9ae50b2a771c68028ee6647bdf92b5d`; historical course correction with current supersession note |
| Shared closure owner | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure.py` | `0f318a52cf4148d2f2367a18176867acfad76e5a6827d77ca42e5395ce43ba2a`; landed source |
| Nested-seam ancestor | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts.py` | `02e415cd5a83d61fe9c01d54153c21d8e41a293eb17e45aa6a4bc53986d97f42`; pre-existing tracked source |

Catalog identity: `development-190x210-tongue-groove` and
`exp-190x210-simple-tongue-groove`.

## Accepted Stage 1 outputs

- Bucket STEP:
  `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`.
- Baffle STEP:
  `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`.
- Validation diagnostics:
  `c827b673c83dc925e1a24fe72ad71205e49f7608acb56873de59814273030196`.
- Review assembly:
  `ffcd16f32f113f992666eadadb3c29a82fc4b0b339e38affc2fc49495aaa31c8`.

## Deferred work

- Top hinge and lower fasteners are intentionally disabled and unaccepted.
- Physical print adhesion, stability, and final assembly are not validated.
- Final retained-assembly net acoustic volume is not established.
