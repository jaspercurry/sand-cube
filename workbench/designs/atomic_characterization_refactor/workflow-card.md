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
- Next atom: extract the native-free Variant R parameter and print-contract
  ownership boundary, plus a future-only independent Variant I interface.
- Last equivalence evidence: current combined-base generation job
  `20260723T231130-atomic-refactor-current-baseline-correct-input-593db9d217`
  and strict comparison job
  `20260723T234005-atomic-refactor-baseline-equivalence-008f589a51`. Both full
  parts and all six protected sections match the accepted reference with zero
  removed/added material at `1e-5 mm³`, identical topology/bounds/volume/area/
  center of mass, zero bucket/baffle overlap, and matching normalized
  STEP-round-trip diagnostics. The detailed derived report hash is
  `6727ff1a...`; durable facts are in `current-baseline-evidence.json`.
- Current blocker: none. The Phase-A rail blocker is historical; commit
  `e715300` repaired it before the current base. Stop only on a fresh,
  unexplained geometry/evidence mismatch.
- Resume: read this card, `atomic_manifest.json`, and current `git status` /
  `git log`; inspect the latest appended manifest evidence and focused commits.
  Do not repeat Phase A or reread `brief.md` unless a requirement is disputed.
