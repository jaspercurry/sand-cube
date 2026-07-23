# Chronological feedback

## 2026-07-23 — requested comparison

- Increase terminal rollback from 140° to 160°.
- Hold the 190 mm physical envelope and current acoustic length constant.
- Keep the current 140° horn intact for direct comparison.
- Defer compression-driver and enclosure placement changes.

## 2026-07-23 — first measured probe

- Reused the 140° acoustic-mouth calibration only as a measured probe.
- Exact 160° recurrence and 82.3821368 mm length both passed immediately.
- The resulting physical diameter was 191.3912455 mm, so the old mouth
  calibration was not reused for the accepted candidate.
- The sharper lip also exceeded the 0.003 mm spline-fit contract at
  0.0049172 mm. The shared profile builder now uses a denser, bounded
  constraint set only when the rollback exceeds 150°.

## 2026-07-23 — accepted 160° candidate

- Calibrated acoustic-mouth input: 191.138682846249 mm
- Physical X/Y envelope after STEP round trip: 189.9995012 × 189.9994913 mm
- Acoustic axial length: 82.3821368642 mm
- Exact recurrence terminal angle: 159.9999999996°
- CAD terminal tangent: 160.0000000000°
- Solved Le Cléac'h wavefront `T`: 0.23277150234207514
- Solved cutoff: 1045.0670714624766 Hz
- Maximum measured spline deviation: 0.0028848855 mm
- STEP round trip: valid, one solid
- STEP SHA-256:
  `5836dbd82e8b19bac1e084955bd3a66b7822adc23d9628da2d923b9666fdd689`
- The 140° baseline SHA-256 remained:
  `56b793cb82df63e898ec8039e0353858817101880e84a87a588f9fb55f180df5`

The topology audit found one shell, zero boundary edges, zero non-manifold
edges, and no self-interference.

## 2026-07-23 — visual review

- Isometric render: smooth and symmetric; no visible ripples, facets, or
  broken surfaces. The extra rollback is subtle from above.
- Meridian section: the final lip has a clearly tighter downward hook than the
  140° baseline, while the throat and central flare remain visually stable.
- With acoustic length held constant, the rolled-back outer wall increases the
  full front-to-back STEP envelope from 93.5219652 mm to 98.0356860 mm
  (+4.5137208 mm). This is the clearance change to revisit when the driver and
  enclosure placement are frozen.
- The section renderer omits a few shared-boundary strokes near the throat;
  deterministic topology checks and the STEP audit confirm a closed solid.

## 2026-07-23 — family promotion

- Reorganized entrypoint:
  `workbench/designs/le_cleach_horn_190/variants/rollback_160/build.py`.
- Reorganized artifact:
  `build/workbench/le_cleach_horn_190/variants/rollback_160/le_cleach_horn_190_rollback_160.step`.
- Build job `20260723T200836-build-03f84c8262` completed successfully in
  24.197 seconds with 0.83 GiB peak RSS, published two outputs, cleaned its
  workspace, and left no owned orphan processes.
- Accepted dimensions, solver values, and topology were reproduced.
- Current STEP SHA-256:
  `1651e6bb18b7a2a2f9a06475e6611b8fd1d18086f648840fe7772011e7f05408`.
- Topology audit job `20260723T200932-audit-step-de9087b382` passed.
- Sidecar job `20260723T201004-text-to-cad-artifacts-b1f1c342ea` passed.
- Snapshot job `20260723T201029-text-to-cad-artifacts-5e82610acd`
  reproduced the accepted smooth, symmetric isometric appearance.
