# Resume prompt — integral front and bottom-hatch variants

Resume the deferred integral-front / bottom-hatch enclosure project in this
speaker-enclosure repository.

First read:

- `AGENTS.md` and `workbench/AGENTS.md`;
- `workbench/designs/deferred_integral_front_bottom_hatch/contract.md`;
- `workbench/designs/deferred_integral_front_bottom_hatch/source_manifest.md`;
- `workbench/designs/deferred_port_tube_resonator/contract.md`; and
- the current decision record under
  `workbench/designs/enclosure_baffle_recovery/`.

The external-package baseline is the full-perimeter
`lightweight_coherent_closure` bucket/baffle pair, not the later flat-bottom
front-hatch hybrid. Use these exact hash-bound artifacts for reference:

- `centered_captive_nut_bucket.step`;
- `centered_captive_nut_baffle.step`; and
- `centered_captive_nut_assembled.step`.

Their absolute paths and SHA-256 values are recorded in `source_manifest.md`.
They preserve the sculpted nested seam and original bottom-corner treatment on
left, right, top, and bottom. The installed exterior package is the invariant.

Create a new, independent variant. Do not mutate or simplify the existing
front-hatch lineage. The first milestone is an integral-front enclosure with
the same external surface as the installed pair but no visible front seam.
Because the baffle is permanent, do not transfer a flat print base to it.

Do not simply Boolean-union the two exported STEP solids. They intentionally
have a gasket/clearance gap and zero overlap. Start in parameterized source
before `_lightweight_common_joint(full_base)` performs the nested split, or use
an equally explicit monolithic construction. Remove the gasket, joint gap,
front-service fasteners, nut-loading slots, and other removable-baffle-only
features semantically. Preserve the driver recess, fill passages/blisters,
front bulkhead, external fairing, four corners, and required internal support.

Before designing any hatch, prove the monolithic-front baseline with:

- one valid connected enclosure solid;
- no external seam or internal gasket/joint void;
- exterior symmetric difference against the installed reference at or below a
  declared kernel tolerance;
- identical bounds and named front/corner sections;
- valid driver opening and mounting land;
- clear fill passages and sealed sand/acoustic volumes; and
- updated acoustic-volume accounting.

Only after that baseline is accepted should you branch into alternative
bottom-hatch concepts. Treat the hatch as a structural redesign, not a leaf
cut. The current bottom supports the port/tube and other structures, and the
bottom-down print orientation creates a large interior ceiling bridge. Resolve
port re-anchoring, bridge/support strategy, hatch installation, separate sand
and acoustic seals, fasteners, gasket compression, and service access before
cutting the production enclosure.

Start each hatch alternative as the smallest useful section or fit model. At
every meaningful checkpoint provide deterministic checks, a read-only Text-to-
CAD Viewer link, and one inspected isometric plus the single bottom-corner or
hatch section that answers the active question. Use Build123d-MCP
`render_view()` for in-memory scratch work and Snapshot or direct headless PNGs
for exported STEP review. Do not automate the interactive Viewer for routine
inspection.

Keep the tube/resonator work deferred until the monolithic enclosure and hatch
architecture are accepted. Then repackage those systems against the final
interior using the separate deferred tube/resonator handoff.
