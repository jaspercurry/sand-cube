# Variant R production no-splice correction feedback

## 2026-07-24 — preflight and accepted specification

- Verified the fresh worktree started clean at
  `5ec998069b790d648a011d04a2dadb6dc1d8b9e3`, exactly matching
  `origin/main`; created branch `codex/variant-r-no-splice`.
- Read the repository CAD skill and all required iteration, visual, toolchain,
  model-catalog and geometry references, plus the applicable repository and
  workbench `AGENTS.md` files.
- Pinned Build123d `0.11.1`, `cadquery-ocp-novtk` `7.9.3.1`, Build123d-MCP
  `0.3.79` and the model catalog pass. Doctor is blocked only by the missing
  ignored Text-to-CAD checkout in this fresh worktree; it will be restored at
  pinned commit `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423` before artifact work.
- Read commit `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75` and every file under its
  `workbench/designs/variant_r_underside_seam_refinement/` tree through Git.
- Accepted construction evidence: use the exact-edge donor already returned by
  the production foundation, leave bucket and gasket untouched, trim only the
  baffle to the parameter-owned `Z=-91.495 mm` sole, and discard the
  approximately `0.355323 mm` sub-sole band. The candidate expectation is 91
  baffle faces, 257 baffle edges, zero old-splice and unrelated lower-apron
  edges, not a topology-identity claim.
- No source or catalog geometry owner has changed yet.

## 2026-07-24 — localized owner implementation and native-free gate

- `assembly.py` now uses the foundation's continuous exact-edge donor directly,
  leaves donor bucket and gasket untouched, and invokes one baffle-only sole
  trim. The active composer no longer calls either historical whole-part splice
  or lower material-transfer helper.
- `bottom_ownership.py` owns one exact half-space intersection with no explicit
  clean/fix, same-domain unification, splitter removal, healing or tolerance
  widening. Its audit records the removed band and those disabled operations.
- `parameters.py` now owns the single production sole datum
  `baffle_planar_sole_z_mm = -91.495`; the former print-bed property is a
  compatibility alias to that datum. The print contract and current model
  boundary use the same source.
- The historical splice/transfer helpers remain available only for old
  workbench provenance; they are not imported or called by the active composer.
- Focused native-free tests passed `39/39`. The authoritative lightweight gate
  passed 213 tests plus 19 subtests, catalog `12/38`, all 94 CAD entrypoints and
  lint in 5.06 seconds. No native CAD library was imported by this gate.
