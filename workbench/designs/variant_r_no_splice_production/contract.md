# Variant R production no-splice correction contract

Status: implementation authorized; production geometry and review evidence are
not accepted until every gate below passes.

## Baseline and authority

- Start commit and `origin/main`: merge commit
  `5ec998069b790d648a011d04a2dadb6dc1d8b9e3`.
- Catalog model: `development-190x210-tongue-groove`.
- Production composition owner: `src/enclosure_family/variant_r/assembly.py`.
- Lower ownership/sole owner:
  `src/enclosure_family/variant_r/bottom_ownership.py`.
- Sole parameter owner: `src/enclosure_family/variant_r/parameters.py`.
- Validated design evidence: commit
  `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75`; its workbench files are evidence,
  not production source.
- Units and axes: millimetres; X left/right, Y front/rear with front at
  negative Y, Z bottom/top.

## Authorized topology-changing construction

Use the continuous exact-edge flat-bottom donor returned by the existing
`VariantRFoundation` path as the active bucket/baffle/gasket joint. Do not call
the whole-part `Z=-80 mm` band splice or lower baffle-to-bucket material
transfer. Intersect only the donor baffle with the half-space at or above the
single parameter-owned planar sole `Z=-91.495 mm`; discard the approximately
`0.355323 mm` underside-only band. Do not heal, unify same-domain faces, remove
splitters, widen tolerances, or modify the legacy cascade.

This deliberately changes B-rep topology. Preservation claims apply to form,
protected surfaces and interfaces, not literal face/edge identity.

## Preserved product geometry

- Overall enclosure form, bounds and protected visible surfaces above the sole.
- Driver opening/recess and all unrelated mounting/acoustic geometry.
- Exact sculpted left/right/top seam and intended bottom-corner transition.
- Bucket/baffle/gasket separation, gasket path, support and continuous lower
  seal.
- Fill passages/blisters, sand containment, wall structure and corner closure.
- Bucket and baffle print orientation; baffle remains a full-width planar
  contact with brim assumed.
- Retention remains absent; Variant I, horn, electronics and fasteners remain
  untouched.

## Measurable acceptance

- Bucket, baffle and gasket: one valid solid each; assembly: three valid solids.
- STEP round-trip preserves those solid counts and validity.
- Pairwise unintended overlap is at most `0.001 mm³`.
- Baffle topology matches the validated production expectation of 91 faces and
  257 edges, or any mismatch is rejected and diagnosed.
- Bucket and baffle each have zero B-rep edges at the old splice height and zero
  unrelated full-width lower-apron edges.
- Sole is planar at exactly `Z=-91.495 mm`, with contact width at least
  `187.020979 mm` and area at least `2277.950023 mm²`; no baffle topology lies
  below it.
- Gasket support ratios are `1.0 / 1.0`; the lower gasket run and bottom seal
  remain one connected component; bottom corner sealing remains complete.
- Protected visible baffle deviation from the continuous donor is at most
  `0.01 mm`; bucket deviation is at most `0.01 mm`; sampled protected normal
  change is reported and any visible new boundary is rejected.
- Existing driver, fill, closure, wall-thickness, seam-section and full-body
  checks remain green.

## Visual and publication question

Matched smooth and edge-overlay lower-front views must show the old line on the
accepted pre-correction artifact and its absence on the exact final production
artifact, including the side continuation. Inspect one exact production
assembly overview or low view only if needed to confirm intended seams and
part separation. Publish the final three-part STEP and its current sidecar
through the read-only Viewer.
