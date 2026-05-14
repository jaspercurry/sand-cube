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

## Planned Stack

- Python 3.12
- build123d
- bd_warehouse
- OCP CAD Viewer
- Codex as the implementation agent

## First Milestone

Create a buildable `src/enclosure.py` skeleton that exports STEP/3MF-like CAD
artifacts, then implement one feature at a time:

1. Outer and inner dual-skin shell.
2. Recessed front baffle profile.
3. Driver and passive radiator cutouts.
4. Bracing posts, corner gussets, and reinforcement rings.
5. Connector, tweeter pass-through, and fill port geometry.

