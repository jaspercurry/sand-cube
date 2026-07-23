# Integral-front / bottom-hatch source manifest

Inventory date: 2026-07-22

## Selected full-perimeter reference

| Local link | Repository path | SHA-256 |
|---|---|---|
| `links/full_perimeter_bucket.step` | `workbench/designs/canonical_working_set/enclosures/integral_front_bottom_hatch/reference_evidence/centered_captive_nut_bucket.step` | `39e6b2d95317d2348afd992ceda2e98d16a383820a3846737e21228ef1c41486` |
| `links/full_perimeter_baffle.step` | `workbench/designs/canonical_working_set/enclosures/integral_front_bottom_hatch/reference_evidence/centered_captive_nut_baffle.step` | `1dd518458c8fed6792c4acd91f0717b353288c18e49c5b1c6ba31f2c9cc6af03` |
| `links/full_perimeter_assembled.step` | `workbench/designs/canonical_working_set/enclosures/integral_front_bottom_hatch/reference_evidence/centered_captive_nut_assembled.step` | `4595684887c4fb239dd8fefaeb7307a797c3673281df19f3d709b659b3440bf2` |
| `links/full_perimeter_diagnostics.json` | `workbench/designs/canonical_working_set/enclosures/integral_front_bottom_hatch/reference_evidence/diagnostics.json` | `7194ac15b3c78e272ae60d9b1115be6129f0fdfbfd7cbfdcef32593cddbff04d` |

The bucket and baffle each round-trip as one valid solid. The assembly contains
nine valid solids because it also contains gasket/hardware references.

## Owning source

| Role | Repository path | SHA-256 / state |
|---|---|---|
| Pre-split/full-perimeter owner | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure.py` | `0f318a52cf4148d2f2367a18176867acfad76e5a6827d77ca42e5395ce43ba2a`; landed source |
| Nested-seam ancestor | `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_nested_seam_closure_concepts.py` | `02e415cd5a83d61fe9c01d54153c21d8e41a293eb17e45aa6a4bc53986d97f42`; pre-existing tracked source |

Catalog identity: `exp-190x210-lightweight-coherent-closure` (supporting).

## Freshness caveat

The selected STEP files are hash-bound review evidence from a coordinated job
whose individual STEP checks passed before a later preview-only cutaway failed.
The landed generator is newer than the STEP files. Reproduce and compare the
reference before branching; do not claim the current source already rebuilds
these exact artifacts.
