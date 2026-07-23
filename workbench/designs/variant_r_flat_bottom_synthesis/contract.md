# Variant R flat-bottom synthesis contract

Status: complete — Stage 1 geometry and release evidence validated

## Authorization and boundary

The verbatim user instruction is preserved in `brief.md`. It follows the
explicit request for authorization to enter later Variant R geometry-synthesis
scope and reconcile the sculpted seam with the flat-bottom references.

This iteration may:

- repair the pre-existing rear-ramp rail placement blocker as a separately
  measured prerequisite;
- preserve the accepted sculpted left, right, and top seating seam;
- replace only the lower center perimeter detour with the accepted flat,
  full-width baffle printing edge and complementary bucket ownership;
- restore a continuous, supported lower gasket run and sealed bottom-corner
  transitions; and
- produce a reproducible parameterized bucket/baffle pair with current
  programmatic and visual evidence.

This iteration may not add the deferred hinge, lower fasteners, integral-front
variant, bottom hatch, horn, tube, resonator, bracket, electronics, or final
support-aware bracing. `BUILD_TOP_HINGE` and `BUILD_BOTTOM_SCREWS` remain
disabled.

## Catalog baseline

- Model: `development-190x210-tongue-groove`
- Lifecycle: `development`
- Owner and entrypoint:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle.py`
- Validator:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/validate_simple_tongue_groove_baffle.py`
- Output:
  `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle`
- Units: millimeters
- Family envelope: 190 mm X, 210 mm Y, 190 mm Z, centered at Y = +10 mm

## Hash-bound reference contributions

- Clean sculpted bucket:
  `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/links/near_perfect_bucket.step`
  (`eaeed68103e3110ca3e888ece90002a7f2f98a8b174fab5906e7fb0bd9350b97`)
- Bottom-ownership assembly:
  `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/links/bottom_ownership_assembly.step`
  (`90558975e0e8fb735534b53a73eb7970d3bdddd6aeda34fb821380915877bab0`)
- Flat-edge baffle:
  `workbench/designs/canonical_working_set/enclosures/removable_front_baffle/links/flat_bottom_baffle.step`
  (`23c4d67927bbec6702c300c9912a7542383de093940378184b3d932fee3971c2`)

The STEP files are evidence only. Parameterized Python remains authoritative.

## Required invariants

1. Bucket and baffle are each one valid solid before export and after STEP
   round-trip.
2. Left/right/top bucket and baffle seam material matches the authoritative
   sculpted joint at every protected 0.5 mm sample. A point-classifier
   disagreement exactly on a reconstructed boundary is acceptable only when a
   1 mm local cube has at most `0.001 mm³` symmetric material difference.
3. The known top-seam mismatch cube near
   `[-45.0, -71.75, 86.25]` contains no unexplained reference-only or
   candidate-only material above `0.01 mm³`.
4. The only perimeter-wire policy change is the bottom-center detour. Exact
   authoritative edge geometry is reused for the protected perimeter.
5. The lower gasket run has one connected component.
6. Bucket and baffle lower lands are supported at or above the existing
   minimum gasket-support ratio.
7. The baffle has a genuinely planar full-width lower bed-contact edge and a
   reported seating span and planar area. The accepted reference was found to
   contain two trimmed-topology transition nubs extending `0.350323 mm` below
   its nominal `Z = -91.5 mm` plane; the synthesized baffle must contain no
   topology below that plane. The final contact must be one planar face at
   `Z = -91.5 mm`, at least `187.0 mm` wide and `2200 mm²` in area.
8. The lower bucket and baffle ownership is complementary: overlap remains at
   or below the existing tolerance, while sealing and corner closures remain
   present.
9. Exterior bounds and the protected visible skin remain unchanged outside
   the explicitly permitted lower band.
10. Fill paths and sand-cap closure checks remain green.
11. All monkeypatched ancestor state is restored after generation.

## Print contracts

- Bucket: rear face on the bed; design-coordinate build direction `-Y`.
- Baffle: narrow lower edge on the bed; design-coordinate build direction
  `+Z`; brim assumed.

The acceptance evidence must report bed-contact span/area and must not infer
support-free printability from appearance alone.

## Verification

- `fast`: native-free contract validity, catalog, entrypoint safety, tests,
  and lint.
- `fit`: rail topology, authoritative/candidate seam occupancy, local mismatch
  volume, bottom support/continuity, corner closure, overlap, fill clearance,
  and print-contact measurements.
- `release`: successful coordinated generation, STEP round-trip, current
  diagnostics and topology sidecars, exact Viewer link, one inspected
  isometric overview, and at most one focused seam/bottom render.

## Visual questions

1. Does the assembled pair retain the accepted sculpted left/right/top seam
   without the unwanted corner hunks?
2. Does a focused bottom-corner/edge view show a continuous transition into a
   genuinely flat baffle printing edge?

## Promotion check

The production entrypoint output must reproduce the accepted candidate's
semantic measurements within the tolerances above. Scratch or failed-job
artifacts cannot be described as complete.

## Validated result

- Coordinated full-fit job:
  `20260723T151259-validate-simple-tongue-groove-baffle-74db9f9037`;
  `1543.325 s`, `1,380,220,928` bytes peak RSS, successful cleanup, and no
  owned orphan process.
- Bucket STEP:
  `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`.
- Baffle STEP:
  `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`.
- Both parts are one valid solid before export and after STEP round-trip, with
  zero positive-volume overlap.
- Protected left/right/top material mismatches are zero; the known top
  comparison cube is also exact.
- Bucket and baffle gasket support ratios are both `1.0`. The lower land
  support ratios are both `1.0` across `5772` samples, and the lower seal is
  one connected component.
- The final baffle terminates at `Z = -91.5 mm` on one planar
  `187.020979 × 17.552651 mm` face of `2277.950023 mm²`. No trimmed topology
  extends below that face.
- Fill blockage and unclosed non-fill sand-cap volume are zero, and all
  bottom-corner closure checks pass.
- `BUILD_TOP_HINGE` and `BUILD_BOTTOM_SCREWS` remain intentionally disabled.
  Their geometry and assembly path are deferred to later stages.
- A brim remains assumed. CAD establishes the contact geometry but does not
  validate first-layer adhesion, print stability, or the completed physical
  assembly.
