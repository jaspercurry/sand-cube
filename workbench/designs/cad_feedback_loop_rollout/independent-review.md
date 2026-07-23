# Independent rollout review

Recorded integration base:
`7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3`.

## First review

The independent reviewer inspected the exact base-to-implementation diff at
`633ec5ab404d0c33080d74db4bce0dc36a0f43f7` and reported three actionable
findings:

1. **P1 — programmatic release could restore cache without force.**
   `run()` accepted a release profile with `force=False`; only the CLI wrapper
   rejected it.
2. **P1 — visual provenance was not revalidated through the owning sidecar
   API.** The release path checked declared hashes but not the current verified
   sidecar cache identity, producer/job identity, renderer counts, or Snapshot
   output-to-accepted-PNG binding.
3. **P2 — two downstream generators declared inherited Viewer outputs that
   production no longer creates.** Header-port declared exterior and cutaway
   Viewers; conformal-full-system declared an inherited exterior Viewer while
   generating only its own cutaway Viewer.

The reviewer found no geometry/parameter edits, no active removable-baffle or
tongue-and-groove edits, no PR #2 edits, and no lost STEP output.

## Dispositions

1. Forced, uncached release is enforced at the start of public `run()` before
   workflow, cache, or native measurement work. A native-free API behavior test
   and supervised unforced-release job both prove rejection.
2. Visual acceptance now requires exact candidate, STEP, sidecar, producer/job,
   renderer-count, Snapshot-source, Snapshot-output, and accepted-PNG
   identities. Release calls `verify_cached_sidecar()` and compares its current
   verified key, kind, paths, hashes, and size before native measurement.
3. Only stale downstream diagnostic declarations were removed. The conformal
   generator retains its own cutaway Viewer. Both downstream files are
   regression-tested and included in compact workflow source hashes.

All affected staged evidence was regenerated in workflow revision 5:
fast, visual acceptance, cold fit, verified warm fit, controlled cache
invalidation, unforced release rejection, and forced uncached release.

## Final re-review

The same independent reviewer inspected the exact amended base-to-HEAD diff at
`7afb9168eef12100560e5e2b3e3465daa6026025` and reported:

**No actionable findings.**

The reviewer explicitly confirmed that all three prior findings were resolved,
82 focused rollout/geometry/cache/workflow/runner tests passed, all 57 CAD
entrypoints passed safety classification, catalog and focused Ruff checks
passed, workflow revision 5 was current through `release_passed`, and the
worktree was clean.

The reviewer again found no geometry or STEP-export changes, artifact-lineage
loss, PR #2 edits, or active removable-baffle/tongue-and-groove edits.

Residual risks noted by the reviewer:

- The production-review policy is a syntactic regression guard and could miss
  unusual indirect launch patterns; the current generator contains none.
- Default review output selection is based on STEP basename; a same-named STEP
  elsewhere should use explicit `--out`. Current release evidence would become
  stale rather than accepting the wrong review.
- Sidecar/review failure isolation is proven by supervised production evidence,
  not a fully mocked unit test.

These are non-actionable residual risks for this contained rollout.
