# Input-landing feedback

## 2026-07-22 — baseline and inventory

- Fetched `origin/main` and created `codex/input-landing` from
  `73b29e51434e4a139efcb09574f8dc1c94bd485f`.
- Left the primary checkout at
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868` untouched.
- Synchronized the clean worktree from the existing lockfile.
- Clean-baseline lightweight verification passed: 82 tests, 19 subtests, 9
  primary catalog models, 31 experiment families, 55 CAD entry points, and
  lint.
- Project doctor passed after installing an exact local copy of the pinned,
  ignored Text-to-CAD 0.3.9 review runtime. That environment-only copy is not
  part of the commit.
- Inventoried every selected file in `intake_manifest.csv` before copying it.
  The manifest records exact source path, state, hash, size, intended owner,
  dependency relationship, classification, and evidence mapping.

## 2026-07-22 — selected landing

- Copied 58 selected source/design/release files with exact byte identity.
- Reconstructed the selected catalog subset rather than copying the dirty
  catalog wholesale.
- Promoted exactly thirteen ignored derived files into four component-local
  `reference_evidence/` directories: 53,707,865 bytes total.
- Repointed all thirteen artifact links to repository-relative durable
  evidence targets.
- Added per-component evidence manifests. Each records the original build
  path, hash, byte size, producer information, approved semantic
  contribution, caveat, and evidence-only status.
- Preserved the release files without editing them; scoped ignore exceptions
  only make the immutable STEP and 3MF payloads trackable.
- No CAD libraries were imported and no geometry, sidecar, Snapshot, or
  release artifact was generated.

## Verification

- `UV_CACHE_DIR=/private/tmp/cad-enclosure-uv-cache uv sync --locked --group
  dev` succeeded without changing `pyproject.toml` or `uv.lock`.
- `UV_CACHE_DIR=/private/tmp/cad-enclosure-uv-cache uv run --locked --group
  dev python scripts/check_lightweight.py` passed: 82 tests, 19 subtests, 10
  primary models, 38 experiment families, 76 CAD entry points, and lint.
- `UV_CACHE_DIR=/private/tmp/cad-enclosure-uv-cache uv run --locked --group
  dev python scripts/cad_review.py doctor` passed with Build123d 0.11.1,
  OCP 7.9.3.1, Build123d-MCP 0.3.79, the 10/38 catalog, and the pinned
  read-only Text-to-CAD 0.3.9 runtime.
- A manifest identity audit passed all 107 rows: 58 copied inputs, 35
  base-satisfied inputs, 13 promoted evidence files, and one reviewed catalog
  source.
- The four evidence manifests describe exactly 13 files and `53,707,865`
  bytes; every recorded hash and size matches its promoted file.
- `shasum -a 256 -c verification/checksums.sha256` passed all 15 V1 release
  entries from `releases/enclosure_v1/front_baffle/`.
- A deliberate recomputation of
  `workbench/designs/canonical_working_set/reference_checksums.sha256`
  produced no diff, then all 30 entries verified.
- The canonical working set contains 29 repository-relative symbolic links:
  zero broken and zero absolute.
- A staged whitespace audit found only preserved input bytes: conventional
  STEP formatting, the frozen release README's Markdown hard break, and two
  trailing spaces inside copied recovery diagnostic strings. Authored intake
  and provenance records have no whitespace errors. No cache, bytecode,
  general build output, Snapshot, preview, or unrelated dirty-checkout path is
  trackable.
- Pre-staging size audit: 78 new files plus focused tracked changes increase
  Git blob content by `83,237,494` bytes. Binary STEP/3MF payload is
  `82,371,050` bytes, of which `53,567,306` bytes are evidence STEP; the three
  evidence JSON files contribute the remaining `140,559` evidence bytes.

The exact commit hash and fresh-checkout adversarial review are reported in the
task handoff because a Git commit cannot embed its own hash.
