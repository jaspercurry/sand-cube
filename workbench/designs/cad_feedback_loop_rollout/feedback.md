# CAD feedback-loop rollout feedback

- 2026-07-23: Coordinator corrected the integration base to
  `7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3`; clean detached worktree matched
  before branch creation.
- 2026-07-23: Native-free preflight passed 162 tests and 19 subtests, catalog
  validation, 55 CAD entrypoint checks, and lint. Doctor found the pinned
  dependencies but reported the ignored Text-to-CAD checkout absent in the new
  worktree.
- 2026-07-23: Downstream inventory proved that the cutaway STEP is lineage
  input for multiple descendant enclosure generators. All nine STEP outputs
  remain production artifacts; only the two static Viewer directories are
  presentation work.
- 2026-07-23: Unchanged baseline production job
  `20260723T211801-generate-sand-cube-190x210-single-oval-port-43ef802b42`
  completed in 105.594 seconds at 0.82 GiB peak RSS, published all nine STEP
  files plus coupled static viewers, removed its workspace, reaped its process
  group, and left zero owned orphans.
- 2026-07-23: Separated production completed in 88.353 seconds with the same
  nine STEP exports and diagnostics and no presentation output. Every STEP
  matched the baseline byte-for-byte after normalizing only its generated
  header timestamp.
- 2026-07-23: Separate sidecar, static-review, and Snapshot jobs bound the exact
  hardware STEP. Visual inspection accepted overall assembly completeness
  without making dimension or fit claims.
- 2026-07-23: Revision 4 strengthened visual acceptance so release rejects a
  stale candidate, STEP, sidecar, static review, Snapshot provenance, Snapshot,
  or measurable pixel claim.
- 2026-07-23: Final fit evidence measured 89.636 seconds cold and 0 seconds on
  a 0.508-second verified warm hit. Changing a controlled source identity
  caused an 88.592-second recomputation under a new cache key.
- 2026-07-23: Final forced release measured 133.721 seconds inside a
  134.486-second supervised job, imported all nine outputs once, bypassed cache
  restoration, passed exact visual-lineage validation, and cleaned its process
  group and workspace.
- 2026-07-23: A deliberately invalid review sidecar failed with zero published
  outputs after 4.568 seconds while preserving the successful production STEP
  and prior review provenance exactly.
