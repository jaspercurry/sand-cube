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

For a multi-step or expensive geometry task, create
`workbench/designs/<iteration>/state.json` with `cad_review workflow init`.
The state file stores only the current revision, hash-bound brief/contract and
source references, completed evidence gates, current question, and next action.
It must not duplicate geometry facts, acceptance criteria, or model ownership.

After compaction or handoff, run `cad_review workflow show STATE.json` and
continue from that resume card. Do not reread or reinject the entire long brief
unless the state is stale, the contract must change, or the compact card leaves
a material ambiguity.

## Candidate loop

1. Change one parameter or feature and start a new ledger revision. This clears
   evidence for the previous source hash.
2. Run native-free source, import, contract, and parameter preflight.
3. Build the smallest useful candidate once.
4. Run the cheap `fast` profile checks against that candidate, record their
   evidence, and reuse the same candidate across later checks and cameras.
5. Inspect the smallest useful direct render as a visual smoke test. Record
   acceptance before requesting the `fit` gate.
6. Run `cad_review workflow gate STATE.json --profile fit`. Run fit only when
   the gate allows it and the question needs mating, clearance, interference,
   or section evidence.
7. Publish the exact STEP with a current topology sidecar and complete release
   evidence only after fit passes.
8. Record artifact paths, hashes, evidence, user feedback, and resulting
   changes in `feedback.md`, then advance the ledger one gate.
9. Continue from the current candidate while scratch state remains healthy.

Never skip directly from a candidate to fit or release. If a native job fails
twice for the same target, or `cad_review stats` reports
`stop-and-diagnose`, stop retrying and isolate the failure with the cheapest
fixture or diagnostic that can distinguish geometry rejection, checker error,
preview failure, export failure, and runner failure.

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
