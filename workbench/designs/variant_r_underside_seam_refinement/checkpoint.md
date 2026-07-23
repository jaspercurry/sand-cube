# Variant R no-splice candidate checkpoint

Status: ready for user review; production promotion is not authorized yet.

## Candidate

The candidate removes the two whole-part Z-plane ownership operations. It uses
the original exact-edge bucket/baffle/gasket joint and trims only the baffle's
`0.355323 mm` sub-sole excess at `Z = -91.495 mm`. The removed underside
material is discarded rather than transferred to the bucket.

No same-domain unification, splitter removal, or surface healing is used.
Visible source surface definitions remain unchanged.

## Acceptance measurements

| Check | Current Stage 1 | Candidate | Result |
| --- | ---: | ---: | --- |
| Baffle faces | 103 | 91 | cleaner than 94-face earlier reference |
| Baffle edges | 282 | 257 | cleaner than 265-edge earlier reference |
| Old `Z=-80.1` edges | 8 | 0 | pass |
| Unrelated visible lower-apron edges | 4 | 0 | pass |
| Candidate bucket old-splice edges | — | 0 | pass |
| Protected baffle deviation | — | `1.4841e-8 mm` max | pass |
| Protected baffle normal change | — | `0.000001208°` max | pass |
| Protected bucket deviation | — | `1.4211e-14 mm` max | pass |
| Bottom seal components | — | 1 | pass |
| Gasket support | — | `1.0 / 1.0` | pass |
| Baffle sole | — | `187.026458 mm`, `2280.003992 mm²` | pass |
| Part overlap | — | `0.0 mm³` for every pair | pass |
| STEP round trip | — | 1 valid solid per part; 3 in assembly | pass |

The outer 2/3/2 mm wall stack is inherited unchanged from the authoritative
base. The named baffle structure, corner closure, and bucket bulkhead
thicknesses remain `3.0 mm`.

## Visual evidence

All matched views use the same Snapshot camera, orthographic projection,
theme, lighting, framing, and display settings. The current edge-overlay view
shows the unwanted full-width line; the candidate does not. The smooth
candidate has no kink at the old splice height and no increased lower-apron
lumpiness relative to the earlier reference.

The candidate assembly review includes the bucket, baffle, and gasket as three
separate valid solids. Additional views cover the normal isometric, low
underside, and `YZ @ X=86 mm` bottom-corner section.

## Exact artifacts

- Assembly STEP SHA-256:
  `1429406659903f0c95e112f785dbd0cab27e9aca53190fb914454c3b7d4912f8`
- Fine sidecar SHA-256:
  `ebc40ca97fd38f04731d1d4f82233da9101a19dfee57c10496a032e7f10db612`
- Sidecar tessellation: `0.01 mm` absolute chordal deflection,
  `0.03 rad` (`1.718873°`) angular deflection
- Read-only Viewer:
  <http://127.0.0.1:4178/?dir=%2Fprivate%2Ftmp%2Fcad-enclosure-remove-splice%2Fbuild%2Fworkbench%2Fvariant_r_underside_seam_refinement%2Freview&file=candidate_trimmed_unspliced_assembly.step>

## Promotion gate

Await explicit user approval. After approval, move the accepted construction
into the production generator, update the production validator in the same
focused change, rerun all relevant production checks, refresh canonical
working references only if authorized, and stop before release/merge/push.
