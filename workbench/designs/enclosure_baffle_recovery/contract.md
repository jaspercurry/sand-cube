# Variant A enclosure/baffle recovery contract

## Baseline

- Repository model: Variant A removable front-baffle hatch, based on the
  authoritative lightweight coherent closure and nested-seam ancestors.
- Approved geometric reference: the current
  `simple_tongue_groove_baffle.step`, specifically its genuinely planar full-
  width bottom print face and its sculpted left/right/top seam.
- Mismatched part: the current `simple_tongue_groove_bucket.step`.
- Current source contains an uncommitted Stage-1 hybrid-seam refactor with the
  hinge and bottom screws disabled. Its `validation_diagnostics.json` predates
  the current baffle and bucket STEP files, so those metrics are not accepted
  as evidence for the current artifacts.

## In scope for this checkpoint

1. Diagnose the upper fill-area curved/triangular bucket material by X/Y/Z
   provenance, identifying the exact creating feature and Boolean.
2. Propose the smallest source change that makes the bucket bottom
   complementary to the approved baffle bottom.
3. Preserve the L/R/top nested seam and functional corner sealing.

No production geometry is to be edited until the user approves the diagnosis
and plan. The hinge and bottom fasteners remain later stages.

## Required behavior and invariants

- The baffle retains one planar, full-width bottom support face suitable for
  vertical printing with a brim.
- Baffle and bucket form complementary, non-overlapping bottom geometry with
  one continuous seal run.
- The actual left/right/top seam occupancy matches the authoritative nested
  seam at explicit sections, not merely at exterior bounds.
- The external bucket silhouette is unchanged except inside the approved
  bottom band below the bottom corner.
- Gasket compression remains 1.0 mm from one tunable constant; both mating
  gasket faces remain fully supported and preserve the canonical inner
  perimeter.
- Both fill passages retain their source locations and diameters, reach the
  live sand void, and have no material blockage after every closure union.
- Wanted hollow fill blisters remain rooted; stray bulkhead or inherited
  closure material is absent from the protected service opening.
- The planar bulkhead face must not create four outer corner tabs: two directly
  in front of the upper fill openings and matching tabs at the lower corners.
  This must be achieved by deleting or redefining the source construction that
  creates those sectors, never by adding a downstream cleanup subtraction.
- All four outside-gasket corners are closed intentionally, with no unrelated
  closure fragments.
- Each candidate and promoted STEP is one valid solid per part and survives a
  1-to-1 valid STEP round trip with negligible bucket/baffle overlap.

## Evidence and views

- Programmatic: component-provenance volume intersections; point occupancy on
  X/Y/Z slices through the complete front bulkhead and both fill approaches;
  bottom complement/overlap; L/R/top seam identity; corner closure; gasket
  support; fill-passage clearance; validity and STEP round trip.
- Human: provide a clickable read-only Text-to-CAD Viewer link to each exact
  STEP with a current topology sidecar; use artifact-local references for the
  approved baffle, current bucket, front-bulkhead/fill section, bottom seam,
  and L/R/top seam only when a new selection is needed.
- Agent overview: use Text-to-CAD Snapshot for an exported STEP, limited to one
  isometric overview.
- Scratch diagnosis: use Build123d-MCP `render_view()` only while the geometry
  remains in memory before a current production STEP exists.
- Production focused diagnosis: use the coordinated repository renderer for
  the one section relevant to the current question when Snapshot is unclear.
- Promoted review: regenerate Snapshot/focused images from the production STEP
  and compare them with the accepted candidate.
- Browser automation is a documented fallback only, not a routine CAD
  inspection path.

## Reversible assumptions

- The attached master prompt is the concrete design brief and is preserved
  verbatim in `brief.md`.
- The current baffle STEP is authoritative for shape despite newer file time
  than the stale validation report.
- Existing uncommitted repository changes belong to the user and will not be
  rewritten or discarded.
- Variant B, the internal acoustic tube, the top hinge, and bottom fasteners
  are outside this first checkpoint.

## Current approved correction gate

The user has approved restoring the seam-bearing pre-mistake construction,
then tracing the artifact-local selected faces back through named source
stages.  The target is the four radiused hunks of plastic sitting on the flat
front face—two directly in front of the fill holes and their two lower-corner
counterparts.  The creating operation must be deleted or redefined; the
curved baffle seat must not be deleted, rebuilt generically, or altered.

Before the target source edit is accepted, all of these must be true at once:

- the selected semantic corner volumes have zero material occupancy;
- the pre-mistake curved L/R/top seating seam has identical protected-section
  occupancy and forward extent;
- the gasket face and its clean inner perimeter are unchanged;
- both fill passages remain clear and both wanted fill blisters remain;
- the exterior shell is unchanged; and
- the bucket and baffle remain one valid STEP-round-trippable solid each.

Read-only Text-to-CAD review is authorized and must not change the current
design merely to exercise the Viewer. Sidecar generation remains coordinated.
