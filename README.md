# Sand Cube

An AI-assisted, code-CAD speaker enclosure project for an 8 inch FDM-printed,
sand-filled cube using a Dayton Audio Epique E150HE-44 driver and a matching
Epique passive radiator.

This repo is intentionally starting with research and parameters before full
geometry. The goal is to keep every CAD dimension tied to a source, a fit test,
or a measured print.

## Current State

- Local git repo initialized on `main`.
- Research validation notes live in `docs/RESEARCH_VALIDATION.md`.
- Initial dimensions live in `params.py`.
- Build123d/Codex working rules live in `AGENTS.md`.
- Initial build123d enclosure generator lives in `src/enclosure.py`.

## Build CAD

```bash
UV_CACHE_DIR=.uv-cache UV_PYTHON_INSTALL_DIR=.uv-python XDG_CACHE_HOME=.cache \
  uv run python src/enclosure.py
```

Outputs are written to `build/`:

- `sand_cube.step`
- `sand_cube.3mf`
- `diagnostics.json`

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

## Planned Stack

- Python 3.12
- build123d
- bd_warehouse
- OCP CAD Viewer
- Codex as the implementation agent

## First Milestone

Continue expanding the build123d model one feature at a time:

1. Add full 3x3 per-face bracing posts.
2. Add corner gussets.
3. Add connector, tweeter pass-through, and fill port geometry.
4. Add print coupons for the M20x2 fill plug and heat-set bosses.
5. Add render/check automation.
