# Resume prompt — bass-reflex tube and D-squat resonator

Resume the deferred bass-reflex tube and resonator work in this speaker-
enclosure repository.

Before doing anything, read:

- `AGENTS.md` and `workbench/AGENTS.md`;
- `workbench/designs/deferred_port_tube_resonator/contract.md`;
- `workbench/designs/deferred_port_tube_resonator/source_manifest.md`; and
- the current enclosure decision record under
  `workbench/designs/enclosure_baffle_recovery/`.

The existing tube and resonator experiment sources are valuable and may have
uncommitted working-tree changes. Preserve them. Do not reset, overwrite,
flatten, relocate, or duplicate their dependency chain merely to simplify the
repository.

The packaging gate is strict: first identify the final accepted enclosure and
baffle Python source plus the exact exported STEP artifacts and hashes. If the
enclosure/closure is still unpromoted or ambiguous, stop after reporting that
blocker. Do not adapt the tube to a temporary enclosure candidate.

Once the closure is final, continue from these two distinct baselines:

1. The rear-corner 40 mm continuous-bore tube/serviceable-tower lineage,
   currently owned by
   `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners/`.
2. The latest Rev D D-squat resonator study under
   `experiments/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/`.

Do not miss the version boundary: the currently integrated resonator placement
still imports the older Rev C D-squat source with a 7.166388 mm nominal slot;
Rev D uses a 9.066233 mm nominal slot and is not yet integrated or production-
validated. Treat the old integrated STEP as a placement reference and Rev D as
the latest acoustic/calibration reference. Reconcile them deliberately rather
than silently mixing their parameters.

Start the resumed iteration by preserving this prompt verbatim in a new
workbench design folder and writing a measurable contract. At minimum, measure
and record:

- final net enclosure air volume and all displaced volumes;
- final tube centerline, flare geometry, physical/effective length definitions,
  and calculated bass-reflex tuning;
- driver, wall, brace, baffle, fill-path, floor, and installation-sweep
  clearances;
- the resonator's actual path position and pressure coupling;
- continuous 40 mm bore and zero material intrusion;
- resonator cavity volume, slot count/width/length/depth, gasket, retention,
  print orientation, and service sequence; and
- which acoustic assumptions still require a printed impedance or near-field
  measurement.

Do not claim that CAD alone proves the resonator removes the intended mode. Use
the Rev D 338.25 Hz target as a provisional model input until the bare final
port is measured. Recalculate tuning from the final route and volume rather
than inheriting a nominal 39 Hz result.

Make the first candidate the smallest useful packaging model: the final
enclosure interior/keepouts, tube centerline and outer envelope, serviceable
tower interfaces, and resonator envelope/adapter stack. Do not rebuild the
complete cosmetic enclosure if a focused fit model answers the question.

At every meaningful checkpoint provide:

1. deterministic geometry and acoustic-input checks;
2. a read-only Text-to-CAD Viewer link to the exact STEP for human review; and
3. one agent-inspected isometric plus only the single section/detail that
   answers the active fit or airway question.

Use Build123d-MCP `render_view()` for in-memory scratch geometry and Snapshot
or direct headless PNGs for exported STEP review. Do not operate the
interactive Viewer with browser automation for routine inspection. Promote
only after the accepted candidate has been reconciled into parameterized
source and passed its full coordinated build and diagnostics.
