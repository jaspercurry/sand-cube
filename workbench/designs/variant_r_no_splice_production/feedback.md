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

## 2026-07-24 — first coordinated candidate publication diagnosis

- The exact base producer completed as job
  `20260724T155031-variant-r-no-splice-base-ef5d5a00d6` in `90.434 s` at
  `1,287,225,344` bytes peak RSS. It reproduced accepted base SHA-256
  `441cc122c0383da257b16e80c4b424096f33b267cc95cab9d1278fb05a43a784`
  and published producer attestation
  `03776b41eb9cdd890439a52e89c0419ccda1d4190a9a6989e9581f5a3b8344a6`.
- Candidate job
  `20260724T155206-variant-r-no-splice-candidate-c9b3f4d573` reached completed
  geometry but failed its first STEP write after `222.201 s` at
  `1,254,932,480` bytes peak RSS. It published zero outputs; the coordinator
  removed its workspace and reaped all owned processes.
- Root cause is isolated: `variant_r/export.py` called Build123d's direct
  path-based XDE writer, which is already documented as unsafe on this macOS
  path/toolchain and for algebra-tree shapes. The repository-safe `src.cad_io`
  writer rebuilds a shallow object from actual solids and serializes through a
  binary stream. Variant R's export owner now uses that existing pinned wrapper;
  geometry and tolerances are unchanged.

## 2026-07-24 — production candidate topology and visual smoke

- Corrected candidate job
  `20260724T155703-variant-r-no-splice-candidate-safe-export-0dddb0df9c`
  completed in `243.211 s` at `1,263,681,536` bytes peak RSS, atomically
  publishing the production bucket, baffle, gasket, three-solid assembly and
  captured continuous donor parts. Cleanup reaped every owned process.
- The production baffle is exactly `91 faces / 257 edges`, matching the
  validated candidate rather than normalizing a mismatch. The bucket is
  `244 faces / 706 edges`. Both parts have zero old-splice-height edges and zero
  unrelated full-width lower-apron edges.
- Bucket, baffle and gasket are one valid solid each; every individual STEP
  round-trips `1 -> 1`, and the assembly round-trips `3 -> 3`.
- The sole is one planar face at `Z=-91.49500000000002 mm`, width
  `187.0264802158104 mm`, depth `17.556411375566057 mm`, and area
  `2280.0060332270587 mm²`, exceeding both prior minima.
- The refactored foundation donor reports a global minimum
  `Z=-95.00105070833588 mm`, so the current global-min audit reports
  `3.506050708335877 mm` below the sole instead of the earlier workbench
  record's `0.355323 mm`. Because accepted output topology/contact match
  exactly, this is retained as a provenance/metric discrepancy for the fit
  audit rather than hidden or relabeled.
- Doctor passes with the existing pinned read-only Viewer runtime at exact
  commit `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`. The first sandboxed
  Snapshot launch failed only on the documented macOS Chromium Mach-port
  restriction and published nothing.
- Snapshot job
  `20260724T160221-text-to-cad-artifacts-7853c78e3c` completed with local
  renderer permission in `5.175 s` at `2,093,301,760` bytes peak RSS. Direct
  inspection of image SHA-256
  `7d7554c776d2954e0acf46669e16672de7b4379a713997b358cbc69100ca0b38`
  shows an uninterrupted lower-front apron and no old horizontal continuation
  on the right bucket side. Intended driver/recess and sculpted seam edges
  remain visible; no detached body is present.

## 2026-07-24 — fit acceptance and donor-band diagnosis

- Coordinated fit job
  `20260724T160314-variant-r-no-splice-fit-audit-0b3301c33a` completed in
  `484.765 s` at `797,343,744` bytes peak RSS; output SHA-256 is
  `f4e90a9c7f9a004f54ff948a5d623ee68e09225f1bfb02f4ebaa07bc8da19fa2`.
- Imported bucket, baffle and gasket are one valid solid each; the assembly is
  three valid solids. Bucket/baffle, gasket/bucket and gasket/baffle overlap
  are each exactly `0.0 mm³`.
- Both lower mating lands are `438.0 mm²`, each with `1.0` support over `5772`
  samples. The bottom seal has one connected component. Gasket support is
  `1.0 / 1.0`.
- Imported baffle contact is one planar face at `Z=-91.495 mm`, width
  `187.02645777936598 mm` and area `2280.003992178324 mm²`.
- Bidirectional protected baffle/donor comparison sampled 743 exterior points
  and 574 unambiguous interior normals. Maximum deviation is
  `1.484022251031871e-8 mm`; maximum normal change is
  `0.0000012074182697257333°`. Bidirectional bucket deviation is
  `1.4210854715202004e-14 mm` with `0°` normal change.
- Named baffle structure, sand-cap and bucket-shoulder thicknesses remain
  `3.0 mm`.
- Read-only donor diagnostic job
  `20260724T161206-variant-r-donor-subsole-diagnostic-5db64d07e5` completed in
  `13.107 s` at `483,098,624` bytes peak RSS. It proves the earlier
  `3.506051 mm` value came from conservative B-spline face bounding boxes:
  actual donor topology vertices bottom at `Z=-91.85032330335 mm`. The real
  sub-sole band is `0.35532330335 mm`, matching the validated specification.
  Production audit metadata now uses vertex topology for this measurement;
  trim geometry is unchanged.
