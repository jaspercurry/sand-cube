# Local CAD Viewing Workflow

Use this guide when an agent needs to help the user inspect generated CAD
without forcing them through an Onshape upload for every iteration.

## Purpose

This repo supports two complementary local viewing workflows:

- **OCP CAD Viewer**: fastest loop for live build123d geometry and quick
  imported-STEP inspection.
- **Desktop STEP viewer**: best local check of the exact exported STEP file,
  including measurements and section planes.

Keep **Onshape** as the final import check for risky topology, especially horn
or horn-adapter geometry.

## OCP CAD Viewer

OCP CAD Viewer is already a project dependency through `ocp-vscode`. The user
also needs the VS Code/Cursor extension installed and the viewer pane running.

Install the extension if needed:

```bash
code --install-extension bernhard-42.ocp-cad-viewer
```

Then start **OCP CAD Viewer** from the VS Code/Cursor sidebar before running
viewer commands.

Use the wrapper script so cache directories stay inside the repo:

```bash
bash scripts/view_model.sh --list
```

Common commands:

```bash
# Show the current final 8.5 in enclosure.
bash scripts/view_model.sh

# Show all standard final enclosure export bodies in one scene.
bash scripts/view_model.sh --target final-enclosure-exports

# Show the standalone B&C DE250 JMLC horn.
bash scripts/view_model.sh --target final-horn

# Import and show the newest generated STEP under build/.
bash scripts/view_model.sh --latest-step

# Import the newest generated STEP and open the clipping UI.
bash scripts/view_model.sh --latest-step --tab clip

# Start in distance-measurement mode.
bash scripts/view_model.sh --latest-step --tool distance

# Import a specific STEP file back through OpenCASCADE.
bash scripts/view_model.sh build/final_system/final_sand_cube_horn_system.step
```

Available named targets are defined in `src/show_model.py`.

## Desktop STEP Review

For fast local review of the exact exported files, use Open STEP Viewer,
FreeCAD, CAD Assistant, or another local STEP viewer.

The most useful exported files are:

- `build/sand_cube_8_5_black_hole/contoured_inner/`
  `sand_cube_8_5_black_hole_final_complete_assembly.step`
- `build/final_system/final_sand_cube_horn_system.step`
- `build/final_system/final_horn_bracket_de250_stack.step`

Use the desktop viewer for:

- quick render/import sanity checks
- measurements
- section planes / clipping through the sand void and bracing
- checking the exact STEP file the user would otherwise upload to Onshape

## Agent Rules

When making geometry changes:

1. Build or export the relevant CAD files first.
2. Tell the user which local viewer command opens the exact thing you changed.
3. Prefer `bash scripts/view_model.sh --latest-step --tab clip` after exporting
   a STEP file.
4. Prefer `bash scripts/view_model.sh --target <name>` while iterating on live
   build123d geometry.
5. Do not claim an exported STEP is Onshape-safe solely because OCP or a local
   desktop viewer displays it.
6. For horn and adapter changes, still recommend a final Onshape import check.

## Troubleshooting

If `bash scripts/view_model.sh --target final-enclosure-step` reports a missing
file, run the export first:

```bash
uv run python scripts/generate_final_enclosure.py
```

If `bash scripts/view_model.sh --target final-system-step` reports a missing
file, run:

```bash
uv run python scripts/generate_final_system_assembly.py
```

If the command runs but nothing appears, make sure the OCP CAD Viewer pane is
started in VS Code/Cursor.
