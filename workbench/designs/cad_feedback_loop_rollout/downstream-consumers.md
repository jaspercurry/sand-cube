# Single-oval-port downstream consumer inventory

Inventory taken at integration base
`7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3` before production-generator
editing.

## Production outputs

The generator publishes nine STEP files:

- `sand_cube_190x210_single_oval_port_base.step`
- `sand_cube_190x210_single_oval_port_internal_tube.step`
- `sand_cube_190x210_single_oval_port_tower.step`
- `sand_cube_190x210_single_oval_port_airway.step`
- `sand_cube_190x210_single_oval_port_gx16.step`
- `sand_cube_190x210_single_oval_port_horn.step`
- `sand_cube_190x210_single_oval_port_assembly.step`
- `sand_cube_190x210_single_oval_port_hardware_check.step`
- `sand_cube_190x210_single_oval_port_cutaway.step`

Every filename remains part of the production export contract. The horn is
called out for direct use in the experiment README. The hardware-check and
cutaway files are the current static-review sources.

## Source and diagnostics consumers

- `experiments/sand_cube_190x210_header_port/generate_sand_cube_190x210_header_port.py`
  imports the generator module as its geometry base and consumes the generated
  `diagnostics.json`.
- The catalog points `exp-190x210-single-oval-port` at the production
  generator.
- The canonical working-set bass-reflex source manifest fingerprints the
  generator source. Its linked tube reference points to a separate derived
  build lineage, not directly to this output directory.

## STEP lineage consumers

The following descendants redirect the inherited generator's `OUT` into their
own build directory, invoke the inherited production pipeline, and then import
the named STEP files:

- `...parabolic_side_g1_conformal_full_system/...py` imports `base` and
  `cutaway`; it replaces the cutaway enclosure surface while retaining the
  inherited internal and hardware solids.
- `...parabolic_side_g1_printable_bucket/...py` imports `base`, `assembly`, and
  `cutaway` to replace the enclosure with printable bucket/baffle parts.
- `...parabolic_side_g1_hooked_gasketed_baffle/...py` imports `base`,
  `assembly`, and `cutaway` to retain inherited system solids around its
  closure.
- `...parabolic_side_g1_centered_captive_nut/...py` imports `base`, `assembly`,
  and `cutaway` for its closure lineage.
- `...parabolic_side_g1_nested_seam_closure_concepts/...py` imports `base`,
  `assembly`, and `cutaway` for its concept lineage.

## Decision

The cutaway STEP is authoritative lineage input, not disposable presentation.
It remains in the production generator with unchanged filename and meaning.
Only the static Viewer directories are review presentation and may move to a
separate job.
