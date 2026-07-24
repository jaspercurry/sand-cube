# Atomic enclosure refactor workflow card

- Exact base: `c25cddb3eeafe6f6dff3b551be4ceb53d5aee9ce`;
  current geometry lineage `789cf7fb4f63d9567585198c47bc3b5b122e070f`;
  paused PR #2 commit `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75`
  is not an ancestor.
- Working branch: `codex/enclosure-atomic-refactor-implementation`.
- Current scope: geometry-preserving Variant R ownership refactor. Preserve the
  accepted imperfect flat-bottom/missing-material relationship. Variant I is
  an independent future interface only; no Variant I geometry exists.
- Current geometry/release commit:
  `d114d7907d5a3fc678d6ca7ac74b0d975c56b2a2`; current evidence-adapter commit
  `388593216e5af2476b36ef9bcc0b1e849c11b61e`.
- Latest producer checkpoint: job
  `20260724T083757-atomic-refactor-final2-producer-5f287edf8b` recreated exact
  input `441cc122...` and attestation `41f7da...` in 87.912 seconds at
  1181417472 bytes peak RSS.
- Final release checkpoint: job
  `20260724T102722-atomic-refactor-landing-restored-release-52bd80460c` passed
  in 1493.266 seconds at 1403142144 bytes peak RSS. Separate observational
  attestation job
  `20260724T105416-atomic-refactor-landing-release-attestation-fina-e1f028f156`
  produced `05b388a7...`, binding release commit `d114d79`, exact producer
  input, nine model artifacts, 62 complete runtime sources, 58
  geometry/parameter sources and all 33 loaded generator stages.
- Final strict equivalence job
  `20260724T105504-atomic-refactor-landing-strict-a9945e2f37` passed in
  2113.045 seconds at 2430173184 bytes peak RSS. Report
  `2cc8b236ce40502642cade4c0d04a57a86792eec530992d3eba84891cf3fe645`
  proves both parts and all six protected sections equivalent with matching
  topology/bounds/mass properties, zero removed/added material, matching
  diagnostics, zero-volume mating contact and unchanged tolerances.
- Final lightweight job
  `20260724T114341-atomic-refactor-landing-final-lightweight-a08026447e`
  passed 212 tests and 19 subtests, catalog 10/38, 91 entrypoints and lint in
  6.117 seconds at 21757952 bytes peak RSS.
- Exact visual evidence: review STEP `a1211ad...`, attestation `30387b5...`,
  sidecar `5914ddf...`, read-only Viewer record `d58949c...`, and Snapshot job
  `20260724T113322-atomic-refactor-landing-snapshot-292020a205`. The inspected
  overview `9150298...` and bottom detail `73b5eeb...` are byte-identical to
  the prior continuity images and now bind the final release. No human visual
  attestation has been supplied.
- Current blocker: none. The mandatory independent adversarial review is the
  remaining acceptance gate.
- Next atom: commit the reconciled candidate evidence, run the independent
  exact base-to-candidate review, fix only actionable findings that materially
  affect this refactor, rerun proportional checks, and obtain explicit
  no-unresolved-actionable-findings re-review.
- Resume: read this card, `atomic_manifest.json`,
  `final-acceptance-evidence.json`, and current git state. Consult `brief.md`
  only for a disputed requirement; do not repeat Phase A.
