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
- Next atom: commit the explicit coherent-brace dependency in the narrowed
  base-only producer and run it from a clean source state. Require its base STEP
  and complete loaded-source attestation before the standalone validator can
  run. Compare that produced base with the historical accepted input before
  accepting candidate geometry. After that, extract the remaining
  measurement/export adapters and correct stale current-status projections.
- Last equivalence evidence: Atom 03 generation job
  `20260724T023918-atomic-refactor-atom-03-geometry-06d4fd8a26` and strict
  job
  `20260724T030459-atomic-refactor-atom-03-strict-equivalence-e9021d779e`.
  Both complete parts and all six protected sections have zero removed/added
  material, matching topology/bounds/volume/area/center of mass, zero overlap,
  and unchanged normalized STEP-round-trip diagnostics.
- Current blocker: the first full-cascade producer attempt
  `20260724T035352-atomic-refactor-atom-04-authoritative-producer-0a43bf5466`
  failed safely before publication because its unrelated cutaway preview
  received an OCCT null intersection. The base had already been constructed
  but not exported. The first narrowed producer job
  `20260724T040011-atomic-refactor-atom-04-authoritative-producer-ece1683d24`
  succeeded, but the strict base diagnostic
  `20260724T040247-atomic-refactor-atom-04-base-diagnostic-237b0ab821`
  correctly rejected its direct default brace network: the accepted input has
  194 faces and 1,307,808.9213077368 mm³, while that wrong candidate has 230
  faces and 1,154,161.763662898 mm³. The producer now passes the exact
  coherent-brace builder explicitly instead of relying on the inherited
  runtime patch; it has not rerun. Atom 03 itself is equivalent:
  native-free checks pass (197 tests and 19 subtests, 87 entrypoints, catalog
  and scoped lint), and the strict native gate found zero material delta. The
  Phase-A rail blocker is historical; commit `e715300` repaired it before the
  current base. Stop only on a fresh, unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
