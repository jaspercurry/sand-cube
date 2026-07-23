Work in `/Users/jaspercurry/Code/CAD - Enclosure`.

Use `$speaker-enclosure-cad`.

# Mission

Create a clean, self-contained input-landing commit for the later atomic characterization and refactor task.

This is an intake, provenance, and portability task only. Do not refactor geometry, redesign a model, regenerate reference CAD, or begin combining enclosure candidates.

The current primary checkout is a dirty, user-owned source of intended inputs. Treat it as read-only. Perform the landing in a new clean worktree and branch based on:

`origin/main` at `73b29e5` or its current descendant.

Do not switch, reset, clean, stash, or broadly commit the dirty primary checkout.

# Required result

Produce a reviewed commit or small series of focused commits that provides:

- all deliberately selected source inputs;
- their complete import/dependency closure;
- recovery and deferred-design records;
- the immutable V1 release;
- portable, hash-bound reference evidence;
- current provenance and manifests;
- a consistent model catalog; and
- a clean checkout that passes the repository’s native-free gates.

Do not merge or push.

# Phase 1 — clean-base proof

Before importing anything:

1. Create a clean worktree and branch from current `origin/main`.
2. Run:
   - the documented native-free lightweight suite;
   - CAD entrypoint safety;
   - lint;
   - model catalog validation; and
   - `scripts/cad_review.py doctor`.
3. Determine whether the `dev` dependency group and documented `uv` command work on the clean base.
4. If the clean base is already green, record that result.
5. If the clean base fails independently of the dirty checkout, diagnose it separately before landing inputs.

Do not copy the dirty versions of these infrastructure files merely to address clean-base failures:

- `cad_runner/`;
- `scripts/cad_review.py`;
- `scripts/check_cad_entrypoints.py`;
- `pyproject.toml`;
- `uv.lock`;
- infrastructure tests;
- project skill or Codex configuration; or
- unrelated repository documentation.

Only include one of those files if a specific selected input genuinely requires it and the change is reviewed independently.

# Phase 2 — authoritative intake manifest

Inspect the dirty primary checkout read-only and create an exact intake manifest before copying or editing anything.

For every intended item, record:

- source checkout and path;
- file type;
- SHA-256;
- size;
- tracked, modified, or untracked state;
- intended repository owner;
- reason it is required;
- catalog identity;
- dependency relationship;
- whether it is authoritative Python, documentation, released material, or derived evidence; and
- whether it is named in the canonical checksum file.

At minimum, investigate:

- `workbench/designs/enclosure_baffle_recovery/`;
- `workbench/designs/deferred_integral_front_bottom_hatch/`;
- `workbench/designs/deferred_port_tube_resonator/`;
- `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/`;
- the active removable-front generator, validator, handoff, and iteration notes;
- `releases/enclosure_v1/`;
- `.cad-project/models.toml`; and
- every source or evidence target referenced by `workbench/designs/canonical_working_set/`.

Compute the actual import and source dependency closure of the active enclosure lineage. Do not assume that landing the leaf generator and one direct ancestor is sufficient.

The dirty catalog currently describes more experiment families than the clean checkout. Either:

- land every selected experiment directory needed by the intended catalog entries; or
- omit unrelated catalog entries and directories together.

Never land catalog records whose source directories are absent, and never land immediate `experiments/` directories without corresponding catalog records.

Exclude caches, `__pycache__`, temporary output, job workspaces, screenshots not named as evidence, and unrelated experiments.

# Phase 3 — land source and records

Land selected files only, preserving their intended owner paths.

Required categories include:

## Authoritative and supporting Python

- Active removable-front source and validator.
- Lightweight coherent closure source.
- Every supporting ancestor required to import and reproduce the selected models.
- Any accompanying parameter or robust-geometry modules required by those owners.

Do not flatten the dependency chain during intake. Refactoring it belongs to the next task.

## Design records

- Enclosure/baffle recovery history.
- Deferred integral-front/bottom-hatch record.
- Deferred port/tube/resonator record.
- Required handoffs, briefs, contracts, feedback logs, and source manifests.

Preserve chronological feedback and original briefs.

## Release

Land `releases/enclosure_v1/` as an immutable release boundary, including its source, inputs, manifests, checksums, verification records, and canonical deliverables.

Do not modify or regenerate its release artifacts.

# Phase 4 — make reference evidence portable

A clean checkout currently loses selected STEP and diagnostic targets because the canonical links point into ignored `build/` directories.

Do not commit `build/` wholesale.

For each selected evidence file:

1. Verify its current SHA-256 against `reference_checksums.sha256` and its component manifest.
2. Preserve the exact existing bytes; do not regenerate them during landing.
3. Promote only the exact selected artifact into a deliberately named immutable reference-evidence area adjacent to the owning design record or component manifest.
4. Record:
   - original generated path;
   - original and promoted hashes;
   - size;
   - producing model/source, if known;
   - provenance and freshness caveats;
   - approved semantic contribution; and
   - an explicit statement that it is evidence, not production source.
5. Update the canonical symbolic link to the durable evidence owner.
6. Ensure the promoted file’s hash is byte-for-byte identical to the original.
7. Never promote `__pycache__`, complete build directories, intermediate previews, or unselected artifacts.

Before committing binary evidence, report the exact selected file list and total repository size increase. Keep the set minimal.

The resulting clean checkout must have zero broken canonical links and must verify all selected checksums without access to the dirty checkout.

# Phase 5 — refresh provenance

Update the canonical working-set documentation only where its state statements have become obsolete.

In particular:

- replace the old observed HEAD with the new landing base/commit context;
- remove statements that landed files remain untracked or modified;
- preserve historical statements when clearly labeled as historical;
- identify the new durable owner of promoted reference evidence;
- preserve every source/artifact freshness caveat that remains true;
- do not claim that a reference is reproducible unless its Python source has actually reproduced it; and
- keep the canonical working set a navigation/provenance layer rather than a second model registry.

Recompute `reference_checksums.sha256` deliberately after all targets are final.

# Phase 6 — verification

From the clean landing worktree, require:

- zero broken canonical links;
- all canonical checksums passing;
- catalog consistency;
- every cataloged source and entrypoint present;
- native-free lightweight tests passing;
- entrypoint safety passing;
- lint passing;
- lock/dependency consistency passing;
- CAD doctor passing without bypasses; and
- a clean `git status`.

Do not run full enclosure geometry merely to land files. Run only a minimal coordinated reproduction if required to prove that an authoritative entrypoint is importable and its dependency closure is complete. Do not overwrite the frozen evidence.

Record exact commands, results, commit hashes, and any remaining artifact-freshness blockers.

# Independent review

After implementation, spawn a separate read-only adversarial review agent against the exact landing commit in a fresh clean checkout.

Ask it to check:

- omitted source dependencies;
- broken or non-portable links;
- catalog/source mismatches;
- accidental inclusion of unrelated dirty files;
- copied caches or generated clutter;
- duplicate sources of truth;
- changed release bytes;
- changed reference-evidence bytes;
- misleading freshness or reproducibility claims;
- missing checksums;
- infrastructure regressions; and
- whether the later characterization task is genuinely unblocked.

Classify findings as Blocker, Should-fix, or Nit. Fix every Blocker and Should-fix finding and repeat the review until none remain.

# Final handoff

Report:

- clean base commit;
- landing commit or commits;
- exact landed paths;
- exact exclusions;
- source dependency closure;
- catalog changes;
- promoted evidence paths, hashes, and total size;
- release hash verification;
- checksum and broken-link results;
- clean-suite results;
- independent-review findings and resolutions; and
- the exact commit from which the atomic characterization/refactor task should create its clean worktree.

Do not begin Phase A characterization, modify geometry, merge, or push.
