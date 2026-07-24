# Atomic enclosure refactor workflow card

- Exact base: `c25cddb3eeafe6f6dff3b551be4ceb53d5aee9ce`;
  current geometry lineage `789cf7fb4f63d9567585198c47bc3b5b122e070f`;
  paused PR #2 commit `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75`
  is not an ancestor.
- Working branch: `codex/enclosure-atomic-refactor-implementation`.
- Current scope: geometry-preserving Variant R ownership refactor. Preserve the
  accepted imperfect flat-bottom/missing-material relationship. Variant I is
  an independent future interface only; no Variant I geometry exists.
- Current source/evidence commit:
  `a99ada6266369a854d58f0556021338881345cec` (clean at the amended release).
- Latest producer checkpoint: job
  `20260724T083757-atomic-refactor-final2-producer-5f287edf8b` recreated exact
  input `441cc122...` and attestation `41f7da...` in 87.912 seconds at
  1181417472 bytes peak RSS.
- Latest release checkpoint: job
  `20260724T083930-atomic-refactor-final2-release-a279b8b11a` passed in
  1767.016 seconds at 1399341056 bytes peak RSS and published 11 outputs.
  Attestation `6340ec...` binds clean commit `a99ada6`, 62 complete loaded
  repository sources, 58 geometry/parameter sources, all 33 loaded generator
  stages, the exact portable producer input, and nine model artifacts (bucket,
  baffle, six protected sections and deterministic diagnostics).
- Last completed strict equivalence evidence remains job
  `20260724T074434-atomic-refactor-final-strict-0e704345d5`, report
  `245276011ab4a5cbc3397f250c5d61d54c5b4420138bd138f22b86fc5d8cc4a1`.
  Amended-release strict job
  `20260724T090914-atomic-refactor-final2-strict-894348d891` failed closed
  after one attempt in 2197.002 seconds at 2292236288 bytes peak RSS. The
  candidate diagnostics differ from the accepted/proven prior releases by
  0.0003549875 mm3 in the hybrid bucket audit and 0.0000003974 mm in rear
  span; tolerances were not widened. The runner removed the failed staged
  detail report, so no failed report is represented as current evidence.
- Visual evidence state: inspected Snapshot overview `9150298...` and bottom
  detail `73b5eeb...` are honestly bound to preceding review STEP `cfd4ad3...`
  and sidecar `94c143c...`. They are geometry-equivalent continuity evidence,
  not exact amended-release artifact evidence. Refresh the review assembly,
  sidecar, Viewer record and inspected Snapshot after the amended strict pass.
  No human visual attestation has been supplied.
- Current blocker: `a99ada` prepared release-evidence collection before the
  serialized legacy geometry build. Restore the previously proven pre-geometry
  execution path and make evidence collection strictly post-geometry and
  observational; do not change geometry or acceptance tolerances.
- Next atom: apply and commit that minimal ordering fix; reproduce the affected
  release and strict checkpoint; run lightweight/catalog/entrypoint/lint checks;
  refresh exact visual evidence; reconcile committed records; then run the
  mandatory independent base-to-candidate adversarial review and obtain explicit
  no-unresolved-actionable-findings re-review.
- Resume: read this card, `atomic_manifest.json`,
  `final-acceptance-evidence.json`, and current git state. Consult `brief.md`
  only for a disputed requirement; do not repeat Phase A.
