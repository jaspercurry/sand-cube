# Horn Print and Viewer Work Summary

This documents the CAD and print-prep work captured in the current Codex
worktree before merging it back to `main`.

## Scope

The work focused on making the JMLC horn, its support strategy, and the horn
mount easier to print and inspect locally.

Major additions:

- Custom FDM support learnings in `docs/custom-fdm-support-learnings.md`.
- Horn support experiment geometry in `src/features/horn_support_experiment.py`.
- Mouth-down horn and cradle generation in
  `scripts/generate_horn_mouth_down_experiment.py`.
- Upright horn support and accordion/corrugated support generation in
  `scripts/generate_horn_support_experiment.py`.
- Bambu project generators for horn support, mouth-down horn, and OSS horn
  mount workflows.
- OSS horn mount thinning utility in `scripts/thin_oss_horn_mount.py`.
- Additional OCP viewer targets in `src/show_model.py` for horn support and
  mouth-down experiments.
- Static OCP viewer generator in `scripts/generate_static_ocp_viewer.py`.

## Static OCP Viewer

The live OCP viewer sometimes loaded the bundled blue `OCP` logo and missed the
model payload because the browser websocket registration completed after the
Python sender had already pushed the CAD data.

To avoid that timing issue, `scripts/generate_static_ocp_viewer.py` imports a
STEP file, tessellates it with the same OCP/three-cad-viewer stack, and writes a
static viewer page with the model payload baked in.

Default command:

```bash
MPLCONFIGDIR=.cache/matplotlib \
.venv/bin/python scripts/generate_static_ocp_viewer.py
```

Default input:

```text
build/final_system/final_sand_cube_horn_system.step
```

Default output:

```text
build/static_ocp_viewer/viewer/index.html
build/static_ocp_viewer/model-data.js
```

Serve the generated viewer locally:

```bash
cd build/static_ocp_viewer
python3 -m http.server 3939 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:3939/viewer/
```

## Print Strategy Notes

The print work moved through several support strategies:

- PETG and later Bambu Support for PLA as release-interface material.
- A custom corrugated/accordion support ring for the upright horn.
- Wider support contact under the horn underside where the outer horn portion
  grows before meeting the throat-side horn geometry.
- Mouth-down horn printing with a sacrificial cradle and support interface to
  reduce visible top-surface stepping on the horn mouth.
- Rear mount geometry changes toward a smoother hourglass profile and
  serviceable nut access.

The practical lesson was that support geometry must be printable first, not just
mechanically plausible. Thin isolated support paths and wet support filament can
fail before the horn even starts. Larger continuous contact patches, simpler
paths, and controlled support-interface material are more important than
minimizing every gram.

## Merge Notes

The work was developed in a detached Codex worktree on top of:

```text
8fa04b5 Add local CAD viewing workflow
```

The intended merge target is local `main`.
