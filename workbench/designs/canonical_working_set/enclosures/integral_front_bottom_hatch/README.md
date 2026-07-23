# Integral-front enclosure with bottom hatch

## Desired product

Create an independent enclosure variant with the ideal full-perimeter exterior
but a permanent, monolithic front. It prints bottom down. After the seam-free
monolithic enclosure is proven, a separately printed bottom hatch will provide
service access.

## Frozen external baseline

The linked `full_perimeter_bucket.step`, `full_perimeter_baffle.step`, and
`full_perimeter_assembled.step` are the selected `lightweight_coherent_closure`
reference. They retain the sculpted nested seam and original bottom-corner
treatment on all four sides.

Do not substitute the flat-bottom removable-baffle branch, hybrid assembly, or
clean-hunk bucket for this variant.

## Construction boundary

Start from parameterized `full_base` before
`_lightweight_common_joint(full_base)` splits it. Do not merely fuse the STEP
bucket and baffle across their intentional gasket/clearance gap. Remove the
removable-front joint, gasket gap, front fasteners, nut slots, and related
service cavities semantically while preserving the exterior fairing, driver
opening/recess, fill passages, bulkhead, sand containment, and corners.

Before any hatch cut, prove one valid connected solid, no external seam or
internal gasket void, exterior equivalence within a declared tolerance,
identical bounds/corner sections, valid wall/fill/driver geometry, and updated
volume accounting.

The hatch is then a structural redesign. It must resolve the interior ceiling
bridge, port/floor re-anchoring, print support, separate sand and acoustic
seals, gasket compression, fasteners, installation, and service access.

## Local links

| Link | Meaning |
|---|---|
| `links/pre_split_source` | Full-perimeter closure owner containing `full_base` split boundary |
| `links/nested_seam_ancestor` | Authoritative nested-seam construction ancestor |
| `links/deferred_project_record` | Existing contract, manifest, feedback, and resume prompt |
| `links/full_perimeter_bucket.step` | Selected bucket reference |
| `links/full_perimeter_baffle.step` | Selected baffle reference |
| `links/full_perimeter_assembled.step` | Installed exterior/fit reference |
| `links/full_perimeter_diagnostics.json` | Existing validation record with freshness caveat |

See [source_manifest.md](source_manifest.md) for exact paths and hashes.
