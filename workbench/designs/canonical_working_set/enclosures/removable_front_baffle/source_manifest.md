# Removable front-baffle source manifest

Inventory date: 2026-07-22

## Reference artifacts

| Local link | Repository path | SHA-256 | Approved contribution |
|---|---|---|---|
| `links/near_perfect_bucket.step` | `build/workbench/enclosure_baffle_recovery/clean_corner_hunks_candidate_viewer/clean_corner_hunks_bucket.step` | `eaeed68103e3110ca3e888ece90002a7f2f98a8b174fab5906e7fb0bd9350b97` | Clean curved seat and removal of four unwanted hunks; not bottom ownership |
| `links/bottom_ownership_assembly.step` | `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/hybrid_seam_assembled.step` | `90558975e0e8fb735534b53a73eb7970d3bdddd6aeda34fb821380915877bab0` | First/larger solid only, approximately `1111212.853475 mm3`, as bottom complement reference |
| `links/flat_bottom_baffle.step` | `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_baffle.step` | `23c4d67927bbec6702c300c9912a7542383de093940378184b3d932fee3971c2` | Full-width flat print edge and associated baffle material ownership |

All three are derived evidence. The near-perfect bucket is explicitly
unpromoted and STEP-derived.

## Current source owners

| Role | Repository path | SHA-256 / state |
|---|---|---|
| Active leaf generator | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle.py` | `496a9d9797e0b27d14b8762a2a7bc5efac8c7c747e13308265c5ca65fa3f6f7c`; modified working-tree file |
| Standalone validator | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/validate_simple_tongue_groove_baffle.py` | `f3f07e1323a32d58404822a860d82e341ff07b4e8025f5889730d5efa4112298`; modified working-tree file |
| Corrective handoff | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/HANDOFF.md` | `6732d270cda9ed509808fffad13e1038b509fe64b3182ed599995f1fd5f4184c` |
| Shared closure owner | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure.py` | `0f318a52cf4148d2f2367a18176867acfad76e5a6827d77ca42e5395ce43ba2a`; directory is untracked |
| Nested-seam ancestor | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts.py` | `02e415cd5a83d61fe9c01d54153c21d8e41a293eb17e45aa6a4bc53986d97f42`; modified working-tree file |

Catalog identity: `development-190x210-tongue-groove` and
`exp-190x210-simple-tongue-groove`.

## Blockers

- The clean-hunk result has not passed a coordinated source build.
- Bottom ownership is not reconciled in the clean-hunk source result.
- The final hinge, fasteners, gasket reroute, and assembly path are not
  accepted.
- Final net acoustic volume is not established.
