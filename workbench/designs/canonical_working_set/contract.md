# Canonical working-set organization contract

## Requested result

Provide one trustworthy, easy-to-navigate directory for the fundamental
enclosure, acoustic, and horn lineages. Preserve current work and make older
variants easy to ignore without destroying their provenance.

## In scope

- A parent overview for the complete working set.
- Separate component folders with local READMEs and exact source manifests.
- Stable, human-readable links to authoritative source directories and
  hash-bound reference artifacts.
- A clear archive/status index for older experiments and rejected candidates.
- Explicit blockers and next steps for a future refactoring agent.

## Out of scope

- Geometry edits, CAD rebuilds, STEP normalization, or artifact promotion.
- Moving, copying, flattening, or renaming existing source dependency chains.
- Declaring any unpromoted STEP-derived candidate to be production source.
- Tube/resonator packaging, monolithic-front construction, hatch cutting, or
  horn resizing.

## Invariants

- Every source link resolves to the existing owner in the current working
  tree.
- Every artifact link resolves to the exact file named in its manifest.
- Recorded SHA-256 values match current contents at this checkpoint.
- Active, supporting, study, historical, released, and archived states remain
  distinguishable.
- Existing uncommitted changes remain untouched.
- `.cad-project/models.toml` remains the lifecycle catalog; this directory is
  a curated working view, not a competing geometry registry.

## Acceptance check

A new agent can enter this directory, identify the correct variant, locate its
owner and evidence, understand what each reference contributes, see what is
blocked, and avoid the known cross-variant substitutions without searching the
entire repository first.
