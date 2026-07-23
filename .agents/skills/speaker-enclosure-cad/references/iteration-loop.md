# Design iteration loop

## Contract

Preserve the user's wording in `brief.md`; keep interpretation in `contract.md`.
Ask only when an ambiguity would materially change the result. Otherwise make
a labeled, reversible assumption and begin with the smallest useful candidate.

The contract must name:

- the exact baseline generator, source, and artifact if one exists;
- the requested behavior or geometry;
- geometry and behavior that must not change;
- numeric checks for dimensions, validity, fit, interference, topology, wall
  thickness, and clearances relevant to the request;
- the visual question and the camera, section, or isolation that will answer it;
- a promotion check comparing the accepted candidate with production output.

## Candidate loop

1. Change one parameter or feature.
2. Build once and reuse the candidate across checks and cameras.
3. Run deterministic checks before making visual claims.
4. Publish the exact STEP with a current topology sidecar.
5. Inspect the smallest useful render set and provide the Viewer link.
6. Record the artifact path, hash, evidence, user feedback, and resulting
   change in `feedback.md`.
7. Continue from the current candidate while scratch state remains healthy.

For a diagnostic-only request, stop after establishing the cause and evidence;
do not implement a geometry fix without authorization. For an implementation
request, continue until the relevant acceptance criteria pass.

## Scratch and promotion

Build123d-MCP is an optional disposable scratchpad, not authority. Keep at most
one persistent MCP CAD session per active design and restart it after switching
designs or after an unexplained native failure. A scratch export is evidence.

After acceptance:

1. encode the result in the owning parameterized Python source;
2. run the full relevant generator and validation suite through `cad_runner`;
3. compare dimensions, topology, fit, and visual evidence with the accepted
   candidate;
4. publish new STEP, topology sidecar, Snapshot/focused render, and Viewer link;
5. invalidate all references copied from earlier artifact hashes.

AgentCAD is optional. Use it only when persistent A/B history, overlays, or
returning to prior alternatives is worth the added review layer.
