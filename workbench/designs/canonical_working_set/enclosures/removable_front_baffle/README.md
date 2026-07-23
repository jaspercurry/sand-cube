# Removable front-baffle enclosure

## Desired product

The enclosure bucket prints with its rear/GX face on the bed. The removable
front baffle prints vertically. Left, right, and top retain the elegant curved
seating seam; the baffle owns a flat, full-width bottom print edge and the
bucket contains the complementary bottom removal.

## Current state

No single source or STEP pair yet contains the accepted result. Three exact
references contribute different facts:

1. `near_perfect_bucket.step` is the best enclosure appearance and removes the
   four unwanted corner/fill-port hunks, but has the wrong bottom ownership.
2. `bottom_ownership_assembly.step` contributes only the complementary bottom
   relationship from its first/larger solid. It retains obsolete structures.
3. `flat_bottom_baffle.step` contributes the approved full-width flat print
   edge. Its tongue-and-groove details are not automatically approved.

The current active generator contains the minimal corner-hunk source change,
but its full source build stalled and has not promoted the STEP-derived
candidate. Its README contains stale “green” claims; the later `HANDOFF.md`
and `workbench/designs/enclosure_baffle_recovery/feedback.md` supersede them.

## Safe next step

Refactor the parameterized source so the bucket and baffle own complementary
bottom material while preserving the clean curved L/R/T seat, exterior,
gasket support, fill passages/blisters, driver opening, and sand containment.
Do not Boolean-combine the reference STEP files.

The top hinge and bottom fasteners remain later features. The tube and
resonator remain deferred until the final pair, source, STEP files, hashes,
volume, and service path are accepted.

## Local links

| Link | Meaning |
|---|---|
| `links/active_source` | Current leaf generator, validator, README, and handoff |
| `links/full_perimeter_source` | Authoritative shared closure owner |
| `links/recovery_record` | Chronological diagnosis and candidate evidence |
| `links/near_perfect_bucket.step` | Clean-hunk, wrong-bottom reference |
| `links/bottom_ownership_assembly.step` | Archived two-solid bottom relationship |
| `links/flat_bottom_baffle.step` | Approved flat-bottom baffle reference |

See [source_manifest.md](source_manifest.md) for exact paths and hashes.
