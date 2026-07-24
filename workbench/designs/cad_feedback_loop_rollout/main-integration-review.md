# Current-main integration review

Integration base:
`143c799bd1463589fd90bc69cfb58370ac487b39`.

Reviewed six-commit content head:
`f8cf5c9294014527ea19d70021ed9859126250e4`.

## Independent review

The independent reviewer verified that:

- all six replayed commits have the same stable patch identities as their
  previously reviewed counterparts;
- the current-main 190 mm Le Cleac'h horn subtree and `.cad-project/models.toml`
  are byte-identical to the integration base;
- paused PR #2 commit
  `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75` is not an ancestor;
- no active removable-baffle geometry or STEP-export behavior entered;
- 170 tests and 19 subtests, the 11-model/31-family catalog, 60 CAD entrypoint
  checks, Ruff, and `git diff --check` passed; and
- no native CAD was rerun for this replay.

The review reported one Should-fix finding: the original `state.json` remained
worded as a live final-stage ledger although its hash-bound files are ignored
derived artifacts absent from clean checkouts.

## Disposition

The ledger is now `historical-state.json`, its objective and resume fields
explicitly describe the clean-checkout boundary, and the evidence summary no
longer claims that the archived state is currently valid outside the original
supervised rollout worktree. No derived `build/` artifact was committed.

The amended base-to-head diff must receive a final read-only re-review before
the branch is pushed to main.
