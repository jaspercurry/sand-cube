# Joint Coupon Feedback Log

## Contract

- Two valid printable solids: lower bucket-side coupon and upper baffle-side coupon.
- Closed plate gap: 1.0 mm.
- Tongue/groove side clearance: 0.2 mm per side.
- Tongue/groove end clearance: 1.0 mm per end.
- Free gasket compression at closure: 0.5 mm.
- Four aligned 4.5 mm fastener holes in each rigid part.
- No positive-volume interference in the closed assembly.

## Cycle template

### Cycle N — date

Requested change:

Programmatic evidence:

Agent visual observation:

Human visual feedback:

Decision: accept / revise / reject

Accepted checkpoint or source revision:

## Verification-integration repair — 2026-07-23

The review packets and generated artifacts from the earlier dirty-tree run are
superseded and must not be cited for the repaired integration.

Source-stable coordinated evidence:

- Fast: `20260723T015305-joint-coupon-fast-a80e9d29bc`, 0.508 s,
  180224-byte peak RSS, PASS packet at
  `build/workbench/joint_coupon/review-packet-fast.json`.
- Fit: `20260723T015311-joint-coupon-fit-f6ab9239bb`, 5.056 s,
  479576064-byte peak RSS, PASS packet at
  `build/workbench/joint_coupon/review-packet-fit.json`.
- Release: `20260723T015326-joint-coupon-release-375d971650`, 3.036 s,
  489357312-byte peak RSS, PASS packet at
  `build/workbench/joint_coupon/review-packet-release.json`.
- Sidecar: `20260723T015334-text-to-cad-artifacts-6e9e80a141`, 1.018 s,
  243367936-byte peak RSS.
- Snapshot: `20260723T015348-text-to-cad-artifacts-3ab3bb5add`, 3.114 s,
  453263360-byte peak RSS. Its deterministic camera recipe is tracked at
  `workbench/designs/joint_coupon/snapshot-job.json` and included in the
  source fingerprint.

Exact reviewed evidence:

- Assembly STEP:
  `build/workbench/joint_coupon/joint_coupon_assembly.step`, SHA-256
  `f3aab81763af3c6ae3c4c7113b9dd5d0a2c230f1656f18563432fc40303e089c`.
- Sidecar: `build/workbench/joint_coupon/.joint_coupon_assembly.step.glb`,
  SHA-256
  `367f95ab98258915d72178d5a9d5d828218150ce5d492c601bfa3157f51f9e8f`.
- Isometric Snapshot:
  `build/workbench/joint_coupon/snapshot-isometric_20260723T015349Z.png`,
  SHA-256
  `b8c0e137f134db0bdacc1db92432530770560dc007d95b35f5cf40f10dcc9207`.
- Section Snapshot:
  `build/workbench/joint_coupon/snapshot-joint-section_20260723T015349Z.png`,
  SHA-256
  `2dad5e9425495e8bf8322748f87c9fb34b6fbca7b1ad9e172998d69606f64ae1`.

The agent inspection attestation is
`build/workbench/joint_coupon/inspection-attestation.json`. The isometric shows
two coherent rigid solids, four aligned through-holes, and the intended gap;
the YZ section clearly shows the tongue nested in the wider/deeper groove.
Gasket references are programmatically verified and exported separately, not
visible in the rigid assembly STEP.

The Viewer URL in `build/workbench/joint_coupon/viewer-record.json` was probed
read-only at `http://127.0.0.1:4179`; it is transient and local, not portable
evidence. The immutable baseline comparison passed 6 fast, 19 fit, and 23
release measurements with zero mismatches. Clean-export verification is
recorded in the integration handoff; generated evidence remains outside the
source commit.
