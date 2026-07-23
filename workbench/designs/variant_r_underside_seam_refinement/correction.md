# Remove the unintended visible splice line and surface lumpiness

The current Stage 1 implementation introduced an unintended horizontal topological boundary across the baffle and enclosure exterior.

Measured comparison:

- earlier flat-bottom baffle: 94 faces and 265 edges;
- current synthesized baffle: 103 faces and 282 edges;
- current geometry contains new B-spline edges at `Z = -80.1 mm`, created by the `Z = -80 mm` lower-band splice with its `0.20 mm` overlap;
- the earlier baffle contains no corresponding edge;
- adjacent central revolved faces have matching normals across this boundary;
- outer B-spline faces have a measured normal change of approximately `0.075°`.

This explains both the irrelevant horizontal line and at least part of the increased lumpy/faceted shading. The Viewer tessellates B-rep faces separately, so unnecessary face splits and small normal discontinuities are visually amplified.

The line is not a desired geometric feature and must be removed from both the baffle and enclosure exterior.

## Required implementation behavior

- Do not slice and re-fuse the complete visible exterior merely to change lower material ownership.
- Confine ownership-changing Booleans to the joint, underside, and internal structure wherever possible.
- Preserve the original continuous exterior surface definitions through the visible front and side regions.
- Do not leave construction-plane edges, same-domain split faces, Boolean scars, or unrelated horizontal boundaries on the visible baffle or bucket exterior.
- If same-domain unification or splitter removal is used, prove that it does not alter intended seam, driver, gasket, or exterior geometry.
- The new underside seam transition must not create another full-width face split higher on the baffle.
- Any necessary topology boundary must correspond to an intentional geometric or part-ownership feature.

## Required validation

- Compare visible face and edge topology against the earlier flat-bottom baffle and the accepted sculpted reference.
- Explicitly search for horizontal or near-horizontal edges crossing the visible lower-front apron.
- Require zero unrelated construction edges on the visible baffle face and corresponding bucket exterior.
- Measure surface-normal continuity across every newly created visible boundary.
- Reject any visible construction boundary with a normal discontinuity; target no boundary at all where the exterior is intended to be one continuous surface.
- Measure localized surface deviation above the permitted corner/underside band.
- Produce matched smooth-shaded close-ups of the earlier and new baffles using identical camera, lighting, edge-overlay, and tessellation settings.
- Provide an edge-overlay view separately so real topology can be distinguished from triangle-mesh shading.
- Generate a sufficiently fine sidecar or print-preparation mesh and record its chordal and angular tolerances.
- Do not dismiss the issue as Viewer-only until both the B-rep continuity audit and matched high-resolution render pass.

Acceptance requires:

1. no irrelevant horizontal line across the baffle;
2. no continuation of that line into the enclosure exterior;
3. no visible shading kink at the former splice height;
4. no increased lumpiness relative to the earlier baffle under matched rendering;
5. preservation of the intentional driver, recess, sculpted seam, and underside parting-line edges; and
6. one valid solid per part with all existing fit, seal, print-contact, and round-trip checks green.
