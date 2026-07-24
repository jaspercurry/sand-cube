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
- Next atom: extract the Variant R seam and bottom-material ownership builders,
  with the deep experiment cascade isolated behind an explicit foundation
  adapter.
- Last equivalence evidence: Atom 01 generation job
  `20260724T002420-atomic-refactor-atom-01-parameters-abc939b859` and
  proportional metrics job
  `20260724T004959-atomic-refactor-atom-01-metrics-711d720604`. Both complete
  parts and all six protected sections match validity/topology/bounds/volume/
  area/center of mass, overlap remains zero, and normalized round-trip
  diagnostics match. Release baseline job
  `20260723T234005-atomic-refactor-baseline-equivalence-008f589a51` remains
  the strict zero bidirectional material proof.
- Current blocker: none. The Phase-A rail blocker is historical; commit
  `e715300` repaired it before the current base. Stop only on a fresh,
  unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
