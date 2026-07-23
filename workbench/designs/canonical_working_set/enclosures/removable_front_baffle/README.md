# Removable front-baffle enclosure

## Desired product

The enclosure bucket prints with its rear/GX face on the bed. The removable
front baffle prints vertically. Left, right, and top retain the elegant curved
seating seam; the baffle owns a flat, full-width bottom print edge and the
bucket contains the complementary bottom removal.

## Current state

Stage 1 now has an accepted parameterized source and current bucket/baffle
pair. It reconciles these three exact reference contributions:

1. `near_perfect_bucket.step` is the best enclosure appearance and removes the
   four unwanted corner/fill-port hunks, but has the wrong bottom ownership.
2. `bottom_ownership_assembly.step` contributes only the complementary bottom
   relationship from its first/larger solid. It retains obsolete structures.
3. `flat_bottom_baffle.step` contributes the approved full-width flat print
   edge. Its tongue-and-groove details are not automatically approved.

The active generator reuses the exact authoritative left/right/top and corner
perimeter edges, replaces only the lower-center detour, and transfers the
below-plane baffle material to the bucket. The resulting baffle has one true
planar `187.020979 × 17.552651 mm` print face at `Z = -91.5 mm`, area
`2277.950023 mm²`, with no trimmed topology below it.

Final Stage 1 artifact hashes:

- bucket STEP:
  `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`;
- baffle STEP:
  `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`;
- validation diagnostics:
  `c827b673c83dc925e1a24fe72ad71205e49f7608acb56873de59814273030196`.

Both parts are one valid solid before export and after STEP round-trip, with
zero overlap. Protected left/right/top material differences are zero, gasket
and lower-land support ratios are `1.0`, the lower seal is connected, and
fill and sand-closure checks pass.

## Safe next step

Design the top hinge and lower fasteners as later, separately measured stages.
`BUILD_TOP_HINGE` and `BUILD_BOTTOM_SCREWS` remain disabled in the accepted
Stage 1 pair. Physical first-layer adhesion and print stability are also
unverified; a brim is assumed.

The tube and resonator remain deferred until the completed retained assembly,
final net volume, keepouts, and service path are accepted.

## Local links

| Link | Meaning |
|---|---|
| `links/active_source` | Accepted Stage 1 leaf generator, validator, README, and historical handoff |
| `links/full_perimeter_source` | Authoritative shared closure owner |
| `links/recovery_record` | Chronological diagnosis and candidate evidence |
| `links/near_perfect_bucket.step` | Clean-hunk, wrong-bottom reference |
| `links/bottom_ownership_assembly.step` | Archived two-solid bottom relationship |
| `links/flat_bottom_baffle.step` | Approved flat-bottom baffle reference |

See [source_manifest.md](source_manifest.md) for exact paths and hashes.
