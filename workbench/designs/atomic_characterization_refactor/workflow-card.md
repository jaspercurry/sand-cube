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
- Next atom: remove disabled retention flags/code and add the explicit model,
  verification/export boundaries, and thin cataloged Variant R entrypoint.
- Last equivalence evidence: Atom 02 generation job
  `20260724T012509-atomic-refactor-atom-02-geometry-dcc2d21bcb` and strict
  job `20260724T015015-atomic-refactor-atom-02-strict-equivalence-68898b111a`.
  Both complete parts and all six protected sections have zero removed/added
  material, matching topology/bounds/volume/area/center of mass, zero overlap,
  and unchanged normalized STEP-round-trip diagnostics.
- Current blocker: none. The Phase-A rail blocker is historical; commit
  `e715300` repaired it before the current base. Stop only on a fresh,
  unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
