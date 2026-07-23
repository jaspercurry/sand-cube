# Feedback log

## 2026-07-22 — working-set map created (historical capture)

- Read the repository and workbench rules, model catalog, enclosure contract,
  complete enclosure recovery directory, both deferred project records, and
  the selected owning source/validator files.
- Rechecked the supplied enclosure hashes and the existing full-perimeter,
  tube, Rev C placement, and Rev D reference hashes.
- Confirmed that the repository has a large pre-existing dirty working tree,
  including modified tube/resonator sources and an untracked
  `lightweight_coherent_closure` directory.
- Created this curated working set with documentation and relative symbolic
  links. Existing experiment source and generated artifacts remain in place.
- No CAD was imported, rebuilt, rendered, regenerated, or promoted.
- The model catalog was not changed because no model identity, owner,
  entrypoint, output location, or lifecycle status was changed.
- Added 29 relative symbolic links to existing source directories, handoff
  records, diagnostics, and STEP references. A scoped `.gitignore` exception
  keeps the STEP links visible to Git without unignoring generated STEP files
  elsewhere in the repository.
- `reference_checksums.sha256` verified all 30 selected source and artifact
  files successfully.
- A broken-link scan in the captured local working tree found zero broken
  symbolic links. A separate clean-`main` worktree found the expected 19
  unresolved links: ignored build evidence plus still-uncommitted source and
  handoff directories. The portable manifests explicitly retain their paths,
  tracking state, roles, and hashes; the PR does not pretend to archive those
  dependencies.
- `scripts/cad_review.py check-catalog` passed with 10 primary models and 41
  experiment families.

## 2026-07-22 — clean input landing and portability update

- Based the landing on clean `origin/main` at
  `73b29e51434e4a139efcb09574f8dc1c94bd485f`; the dirty intake checkout at
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868` remained read-only.
- Landed the selected source, dependency closure, recovery/deferred records,
  and immutable V1 release. The file-by-file intake and exclusions live in
  `workbench/designs/input_landing_2026_07_22/`.
- Copied exactly thirteen selected evidence files, totaling `53,707,865`
  bytes, into component-local `reference_evidence/` directories with exact
  original hashes.
- Repointed the thirteen artifact links away from ignored `build/` paths.
  All canonical links now resolve in a clean checkout.
- Preserved the original generated paths, source/artifact freshness blockers,
  and approved semantic roles in per-component evidence manifests.
- No geometry or evidence was regenerated, modified, or newly approved.
- Final checksum, catalog, lightweight, doctor, and clean-checkout results are
  recorded in the input-landing feedback log.
