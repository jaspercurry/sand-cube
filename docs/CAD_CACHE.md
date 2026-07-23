# Verified CAD stage cache

`cad_runner.cache` is the native-free cache primitive for derived CAD stages.
Entries live at:

```text
build/.cad-cache/stages/<stage>/<key>/
```

The directory key is SHA-256 over a canonical specification containing the
stage and producer versions, producer schema, repository-relative source-file
hashes and sizes, type-preserving parameter values, pinned tool versions and
identities, settings, and declared outputs. Mapping and identity-collection
ordering does not affect the key.

Each entry has a versioned `manifest.json` plus files below `artifacts/`. The
manifest repeats the exact specification and records every artifact's size and
SHA-256. Its `entry_fingerprint` binds the specification and artifact records,
so the full entry identity includes the output hashes even though lookup begins
with the input-derived directory key.

A hit is returned only after the current source files, exact manifest schema,
declared artifact paths, sizes, hashes, and entry fingerprint all verify.
Missing, malformed, old, unsafe, or drifted entries are misses with a reason;
timestamps are never evidence of validity. Publication uses a per-key lock,
copies stable regular files into a private sibling directory, writes and syncs
the manifest, then renames the complete directory into place.

## Text-to-CAD sidecars

`scripts/text_to_cad_artifacts.py sidecar` is the first consumer. Its identity
includes the exact STEP SHA-256, sidecar kind, pinned Text-to-CAD version and
commit, Python ABI, actual Build123d and OCP distribution versions, sidecar
producer/schema versions, and the relevant topology and meshing settings
identity. Generation additionally fails if the pinned Text-to-CAD generator
sources have tracked modifications or the native dependency versions differ
from `.cad-project/project.toml`. The manifest binds the generated sidecar
SHA-256.

On a verified hit, the sidecar is restored without importing the Text-to-CAD
generator or retessellating. The shared bounded GLB reader then confirms that
the restored sidecar embeds the current STEP SHA-256 and that its two
`entryKind` records agree with the requested part/assembly kind. A malformed
sidecar, wrong embedded hash, or wrong kind invalidates that entry and triggers
regeneration through `cad_runner`.

Use `--force` for release proof or any intentionally uncached verification:

```bash
.venv/bin/python scripts/cad_review.py sidecar build/path/model.step \
  --kind part --force
```

The command reports `cache hit`, `cache miss` with its reason, or
`cache published`. Forced regeneration still verifies the embedded STEP hash
and publishes a current, fully verified entry; it does not weaken validation.
