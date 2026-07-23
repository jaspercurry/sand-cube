# Input-landing contract

## Baseline and source

- Landing baseline: `origin/main` at
  `73b29e51434e4a139efcb09574f8dc1c94bd485f`.
- Read-only input checkout: primary working tree at
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868`.
- Landing worktree: a separate clean worktree and `codex/input-landing`
  branch.

## Requested outcome

Create a focused, self-contained commit containing only deliberately selected
inputs for a later characterization/refactor task. This intake does not
authorize geometry changes, CAD regeneration, candidate combination, merge,
or push.

## Invariants

1. The primary checkout is never switched, reset, cleaned, stashed, edited, or
   broadly committed.
2. Selected dirty-checkout files retain the exact SHA-256 and byte length
   recorded in `intake_manifest.csv`.
3. The frozen V1 release retains every byte covered by its own
   `verification/checksums.sha256`.
4. Exactly thirteen derived evidence files are copied into deliberately named
   `reference_evidence/` directories. Their aggregate size is `53,707,865`
   bytes and their hashes equal their original ignored build outputs.
5. Evidence is labeled derived and non-authoritative, includes original path,
   producer, semantic contribution, and caveat, and is not placed in normal
   source/output paths.
6. Canonical links are repository-relative, resolve in a fresh checkout, and
   are covered by `reference_checksums.sha256`.
7. The catalog contains only the selected additions: model
   `front-baffle-v1` plus the seven closure experiments named in
   `dependency_closure.md`. Unselected dirty catalog additions are omitted.
8. No cache, environment, broad build tree, unrelated infrastructure, tests,
   docs, experiments, or workbench material is landed.

## Acceptance checks

- dependency lock synchronization succeeds with the existing lockfile;
- project doctor succeeds with the pinned local review runtime available;
- `scripts/cad_review.py check-catalog` succeeds;
- lightweight tests, entry-point safety checks, and lint succeed;
- all catalog paths exist and no selected immediate experiment directory is
  uncataloged;
- the V1 release checksum file verifies every listed payload;
- all canonical symlinks resolve and all canonical checksums verify;
- the committed tree is clean and the commit is based on the stated baseline.

## Visual and geometry review

Not applicable to this intake. No geometry is changed or regenerated. The
evidence identity gate is byte-for-byte SHA-256 verification; visual and
deterministic geometry comparison belongs to the later characterization task.

## Known blockers deliberately preserved

- The clean-corner-hunks candidate did not complete a coordinated
  authoritative source build.
- The lightweight coherent-closure source is newer than its selected STEP
  evidence.
- The historical `hybrid_seam_assembled.step` producing source revision is not
  preserved exactly.
- Landing the source and evidence does not establish reproducibility or
  source/artifact equality.
