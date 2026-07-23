# Horn-family promotion contract

## Requested result

Promote both accepted 190 mm Le Cléac'h rollback variants to `main` as one
clearly organized family with shared source, separate variant parameters and
validators, separate generated outputs, and a concise comparison README.

## Invariants

- Preserve the accepted 140° and 160° acoustic geometries.
- Keep the 190 mm physical envelope and 82.3821368 mm axial target.
- Keep throat, wall, flange, spigot, and DE250 two-hole mounting geometry.
- Continue solving exact 2007 recurrence wavefront `T` from axial length.
- Keep each STEP valid, one solid, and clean after round trip and topology
  audit.
- Do not stage or commit unrelated worktree changes.

## Organization

- Shared source and parameter schema remain at the family root.
- Variant-owned files live under `variants/rollback_140/` and
  `variants/rollback_160/`.
- Generated artifacts mirror that layout under `build/`.
- The model catalog names both variants and their primary entrypoints.
- `README.md` compares the geometry and likely acoustic tradeoffs.

## Promotion checks

- Both variant builds pass through `cad_runner`.
- Both STEP topology audits pass.
- Both current sidecars and representative renders are regenerated.
- Catalog and style checks pass.
- Only the horn family, required shared horn feature changes, and exact catalog
  records are included in the final commit to `main`.
