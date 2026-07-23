# Selected dependency closure

The active catalog model is `development-190x210-tongue-groove`; its active
experiment identity is `exp-190x210-simple-tongue-groove`. Static import
inspection and checkout-local runtime path inspection produced the following
closure.

## Newly landed closure experiments

1. `exp-190x210-lightweight-coherent-closure`
2. `exp-190x210-systemic-recessed-fasteners`
3. `exp-190x210-single-land-fasteners`
4. `exp-190x210-simplified-printable-closure`
5. `exp-190x210-front-fill-perimeter-seal`
6. `exp-190x210-dual-captive-nut-printable`
7. `exp-190x210-forward-captive-nut`

The active leaf imports the lightweight closure, which follows the chain above
into the already tracked centered/nested/hooked/printable and conformal-system
lineages.

## Pre-existing tracked source closure

The conformal-system lineage reaches both of these already tracked chains:

- rear-corner tube route: rear corners → flush absorber → internal absorber →
  serviceable tower → header port → single oval port → black-hole contour,
  curve-to-seat, shared parameters, and horn;
- conformal inner wall: parabolic fairing → G2 fairing → unified square crop →
  square crop R8 → inverse solver → rear-corner route and horn.

The exact pre-existing files and hashes are recorded as `selected-base` rows in
`intake_manifest.csv`, including `cad_runner/entrypoint.py`,
`cad_runner/outputs.py`, `scripts/generate_static_ocp_viewer.py`, and
`scripts/create_bambu_oss_horn_mount_project.py`. The static closure also
includes the sibling support modules
`experiments/sand_cube_8_5_black_hole/generate_variants.py` and
`experiments/jmlc_square_baffle/explore_variants.py`; the former is imported
by both selected black-hole lineage modules and the latter by the canonical
JMLC study target.

## Runtime-source inspection

The selected generators invoke the static viewer helper and import the Bambu
project helper through checkout-local paths. Both were included in the
manifest even though a simple Python import walk would not discover them.

No dependency was satisfied by copying a cache, virtual environment, or
generated build directory.

## Archival diagnostic boundary

`workbench/designs/enclosure_baffle_recovery/capture_front_component_removed_candidate.py`
is preserved byte-for-byte as chronological provenance, not authoritative or
self-contained Python. It dynamically imports the disposable external helper
`/private/tmp/capture_deleted_face_plate_candidate.py`, which in turn depended
on the dirty checkout and an ignored build STEP. Neither external dependency
is part of the active enclosure lineage, and neither is landed. The preserved
script is intentionally classified as non-runnable documentation/provenance.
