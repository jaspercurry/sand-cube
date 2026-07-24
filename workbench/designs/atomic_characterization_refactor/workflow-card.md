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
- Next atom: commit and run the immutable `789cf7f` base producer recipe from
  a clean current source state. It must archive that exact Git tree, apply the
  committed capture-only overlay, publish the base through the current
  `cad_runner` job, and attest the historical child plus current orchestrator
  source closures. Compare that output with the historical accepted input
  before the standalone validator can run.
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
  runtime patch. That current-source recomposition was also rejected: it
  remained 13,379.9953175602 mm³ short. A capture-only overlay at exact
  geometry commit `789cf7f` then produced STEP
  `46b0cde6306050b413923f1ca8a4b6b65c823e497fd63be7dd638b95701e75a4`;
  job `20260724T042646-historical-789-base-equivalence-d5f150a2ff`
  proved its full ISO-10303 DATA section byte-identical to historical accepted
  hash `441cc122...` and all topology/mass properties exact. The generic OCCT
  symmetric difference was unstable for the separately imported coincident
  copies and remains recorded, not hidden. The clean immutable producer recipe
  is implemented but not yet rerun. Atom 03 itself is equivalent:
  native-free checks pass (197 tests and 19 subtests, 87 entrypoints, catalog
  and scoped lint), and the strict native gate found zero material delta. The
  Phase-A rail blocker is historical; commit `e715300` repaired it before the
  current base. Stop only on a fresh, unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
