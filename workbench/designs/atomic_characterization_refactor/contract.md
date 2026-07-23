# Atomic characterization/refactor contract

Status: Phase A complete; stopped at the Characterization Checkpoint.

The verbatim governing request is `brief.md`. Its required SHA-256 is
`7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`.
This file records the operational interpretation; it does not replace or
rewrite the brief.

## Authority

- Parameterized Python owns geometry.
- Parameter modules own dimensions and fit tolerances.
- `.cad-project/models.toml` owns model identity and lifecycle.
- The canonical working set owns navigation and provenance.
- `atomic_manifest.json` is the sole Phase A atom/evidence authority.
- Markdown inventory, maps, matrices and reports are generated projections.
- STEP, diagnostics, sidecars and images are hash-bound derived evidence.
- No STEP import may be promoted as authoritative source.

## Phase A boundary

Phase A may read source, run native-free checks, attempt a controlled source
reproduction, measure immutable reference artifacts, and produce records.
It may not edit geometry source, reconcile candidates, redesign printability,
create Variant I geometry, or integrate horn/tube/resonator/bracket/electronics
geometry.

The checkpoint is a hard gate. Phase B requires explicit user approval and a
decision about the failed source baseline. A request to continue the
architecture refactor is not authorization to synthesize the product geometry.

## Required variant separation

- The family layer may own only semantics and geometry proven identical.
- Variant R independently owns its service opening, sculpted left/right/top
  seam, lower material ownership, separate baffle, gasket, future hinge and
  fastener interfaces, and both print contracts.
- Variant I independently owns a monolithic front, open bottom, future hatch
  boundary, and open-bottom-down print contract.
- Variant I must branch before the removable split; suppressing final
  removable parts while retaining their hidden construction is unacceptable.
- No flag-driven all-variant generator is permitted.

## Equivalence gate for Phase B

Before geometry extraction, an owning Python source must generate its accepted
baseline. Equivalence requires semantic measurements, protected sections,
validity/topology, transforms, fit/clearance, volume/center of mass and STEP
round-trip evidence. A matching hash is useful provenance but not geometric
proof; matching bounds alone are insufficient.

At this checkpoint the gate is not met. The current lightweight owner fails
before export because its top longitudinal rail produces two solids. The leaf
validator therefore cannot run.

## Printability boundary

Print orientation is first-class metadata, but Phase A only characterizes it:

- R bucket: rear face down, design-coordinate build direction `-Y`.
- R baffle: narrow lower edge down, build direction `+Z`, brim assumed.
- I enclosure: future open bottom down, build direction `+Z`.

No support, brace, seam, bed-contact or hatch geometry may be corrected in the
equivalence refactor.

## Stop conditions

Stop on any unexplained source/artifact identity conflict, geometry mismatch,
failed single-solid invariant, absent protected-section baseline, or false
claim of shared semantics. Preserve every selected immutable reference and
keep deferred component interfaces descriptive only.
