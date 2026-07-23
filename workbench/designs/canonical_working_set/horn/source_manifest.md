# Horn source manifest

Inventory date: 2026-07-22

| Role | Repository path | SHA-256 |
|---|---|---|
| Stable public API | `src/final_horn.py` | `215f549cdaeed933abb0ac1b1f86def0839952b3b5dcb552ded620064c69f99a` |
| Profile and solid construction | `src/features/horn.py` | `0078a6c58f4cce4310b7d7f4e1c46043b67fb837ee0ef57874513af6789c94d8` |
| Shared current parameters | `params.py` | `47bfaa90eaa62652c944e2d910e3b93dd3d3a1b6b2ec8590668a8c5274c1715c` |
| Existing work summary | `docs/horn-print-and-viewer-work-summary.md` | `bb8c9ad982ce7fd70fb6b1d9cf9fbace82539edb24ee012cb4c4dcccbf4edc46` |
| Square-baffle study entrypoint | `experiments/jmlc_square_baffle/generate_rolled_cube.py` | `4ce10a2ae93041609353824ab8e173040055fcfd4a94264fca12e09a73b630be` |

Catalog identity: `final-jmlc-horn` (stable) for the current large horn and
`exp-jmlc-square-baffle` (study) for profile/package experiments.

## Future owner boundary

The new horn should not overwrite `final-jmlc-horn` until accepted. Create a
new parameter module containing at least throat, target mouth/package, wall,
wavefront factor, throat/exit angles, lip, flange, bolt patterns, driver
interface, enclosure/bracket clearance, and chosen recurrence method. Record
the solved cutoff, physical bounds, axial length, profile error, print
orientation, and mounting stack.

The existing API currently uses the default `legacy_recurrence`; the exact
2007 workbook method is available through `profile_method="le_cleach_2007"`
but is not automatically selected by `src/final_horn.py`.
