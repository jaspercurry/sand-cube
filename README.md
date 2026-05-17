# Sand Cube

An AI-assisted, code-CAD speaker enclosure project for an 8 inch FDM-printed,
sand-filled cube using a Dayton Audio Epique E150HE-44 driver and a matching
Epique passive radiator.

This repo is intentionally starting with research and parameters before full
geometry. The goal is to keep every CAD dimension tied to a source, a fit test,
or a measured print.

## Current State

- Research validation notes live in `docs/RESEARCH_VALIDATION.md`.
- CAD import/debugging notes live in `docs/CAD_TROUBLESHOOTING.md`.
- Shared dimensions live in `params.py`.
- Build123d/Codex working rules live in `AGENTS.md`.
- Current 8.5 in enclosure API lives in `src/final_enclosure.py`.
- Current JMLC horn API lives in `src/final_horn.py`.
- Reusable horn and bracket geometry lives under `src/features/`.
- Archived 203 mm enclosure code lives in `archive/old_enclosure.py`.

## Build Current Enclosure

```bash
uv run python scripts/generate_final_enclosure.py
```

Outputs are written to `build/sand_cube_8_5_black_hole/contoured_inner/`:

- `sand_cube_8_5_black_hole_final_enclosure.step`
- `sand_cube_8_5_black_hole_final_enclosure_with_heat_set_inserts.step`
- `sand_cube_8_5_black_hole_final_enclosure_with_inserts_pr_gx16.step`
- `sand_cube_8_5_black_hole_final_complete_assembly.step`

## Build Full System

```bash
uv run python scripts/generate_final_system_assembly.py
```

Outputs are written to `build/final_system/`:

- `final_jmlc_horn_placed.step`
- `final_horn_bracket_4mm_folded.step`
- `final_binding_post_tpu_grommet.step`
- `final_horn_bracket_de250_stack.step`
- `final_sand_cube_horn_system.step`
- `final_system_notes.json`

## Build Archived 203 mm Enclosure

```bash
uv run python scripts/generate_archive_old_enclosure.py
```

Outputs are written to `build/archive/old_enclosure/`. This path is for
comparison and reproducibility; new assembly work should use the 8.5 in final
enclosure scripts above.

## View In OCP CAD Viewer

Install the recommended VS Code extension:

```bash
code --install-extension bernhard-42.ocp-cad-viewer
```

Then start the OCP CAD Viewer from the VS Code/Cursor sidebar and run:

```bash
UV_CACHE_DIR=.uv-cache UV_PYTHON_INSTALL_DIR=.uv-python XDG_CACHE_HOME=.cache \
  uv run python src/show_model.py
```

## Render Local PNG Previews

For cleaner renders than the fallback Matplotlib preview, install `f3d` and run:

```bash
bash scripts/render_f3d_previews.sh
```

The PNG files are written to `previews/`.

## Planned Stack

- Python 3.12
- build123d
- bd_warehouse
- OCP CAD Viewer
- Codex as the implementation agent

## First Milestone

Continue consolidating the final geometry out of experiments:

1. Move the 8.5 in enclosure implementation behind smaller feature modules.
2. Keep `experiments/` for visual/profile studies only.
3. Keep current production exports in `scripts/generate_final_*.py`.
4. Add any future hardware placement helpers under `src/`.
