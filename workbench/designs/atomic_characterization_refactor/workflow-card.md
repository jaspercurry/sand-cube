# Atomic enclosure refactor workflow card

- Exact base: `c25cddb3eeafe6f6dff3b551be4ceb53d5aee9ce`
  (`codex/enclosure-atomic-refactor-current`), with current enclosure lineage
  `789cf7fb4f63d9567585198c47bc3b5b122e070f` present and paused PR #2 commit
  `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75` absent.
- Working branch: `codex/enclosure-atomic-refactor-implementation`.
- Current scope: geometry-preserving ownership refactor of the accepted current
  Variant R bucket/baffle source and verification path. Preserve the accepted
  flat-bottom closure, including its known imperfect/missing-material
  relationship. Establish only an explicit independent future Variant I
  interface; create no Variant I geometry.
- Next atom: commit the completed authoritative-input/producer boundary, then
  run the cataloged producer from a clean source state. Require its base STEP
  and complete loaded-source attestation before the standalone validator can
  run. Compare that produced base with the historical accepted input before
  accepting the candidate geometry. After that, extract the remaining
  measurement/export adapters and correct stale current-status projections.
- Last equivalence evidence: Atom 03 generation job
  `20260724T023918-atomic-refactor-atom-03-geometry-06d4fd8a26` and strict
  job
  `20260724T030459-atomic-refactor-atom-03-strict-equivalence-e9021d779e`.
  Both complete parts and all six protected sections have zero removed/added
  material, matching topology/bounds/volume/area/center of mass, zero overlap,
  and unchanged normalized STEP-round-trip diagnostics.
- Current blocker: the Atom 04 source boundary is implemented and its focused
  native-free tests pass, but the required clean-source producer run and base
  equivalence proof have not run yet. Atom 03 itself is equivalent:
  native-free checks pass (197 tests and 19 subtests, 87 entrypoints, catalog
  and scoped lint), and the strict native gate found zero material delta. The
  Phase-A rail blocker is historical; commit `e715300` repaired it before the
  current base. Stop only on a fresh, unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
