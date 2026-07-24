# Atomic enclosure refactor workflow card

- Exact base: `c25cddb3eeafe6f6dff3b551be4ceb53d5aee9ce`;
  current geometry lineage `789cf7fb4f63d9567585198c47bc3b5b122e070f`;
  paused PR #2 commit `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75`
  is not an ancestor.
- Working branch: `codex/enclosure-atomic-refactor-implementation`.
- Current scope: geometry-preserving Variant R ownership refactor. Preserve the
  accepted imperfect flat-bottom/missing-material relationship. Variant I is
  an independent future interface only; no Variant I geometry exists.
- Current source/evidence commit: `5a076262d109ce11d0ce43df6b5410be8764779b`.
- Last equivalence evidence: producer job
  `20260724T071800-atomic-refactor-final-producer-fa1def52ae` recreated exact
  input `441cc122...`; release job
  `20260724T071935-atomic-refactor-final-release-5a33762429` published ten
  artifacts; strict job
  `20260724T074434-atomic-refactor-final-strict-0e704345d5` passed complete
  bucket/baffle plus six protected sections with matching topology, bounds,
  volume, area and center of mass, zero removed/added material, matching
  diagnostics, zero-volume mating contact and STEP round trips. Full report
  hash: `245276011ab4a5cbc3397f250c5d61d54c5b4420138bd138f22b86fc5d8cc4a1`.
- Visual evidence: inspected Snapshot overview `9150298...` and bottom detail
  `73b5eeb...` rendered from review STEP `cfd4ad3...` and sidecar `94c143c...`.
  Exact Viewer link/provenance is in `final-acceptance-evidence.json`.
- Current blocker: none. Mandatory independent adversarial review is the next
  acceptance gate, not a product-authority pause.
- Next atom: commit the complete candidate evidence, run the independent
  base-to-candidate review, fix every actionable finding, rerun proportional
  verification, and obtain explicit no-unresolved-actionable-findings re-review.
- Resume: read this card, `atomic_manifest.json`,
  `final-acceptance-evidence.json`, and current git state. Consult `brief.md`
  only for a disputed requirement; do not repeat Phase A.
