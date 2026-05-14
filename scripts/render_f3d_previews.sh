#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

UV_CACHE_DIR=.uv-cache \
UV_PYTHON_INSTALL_DIR=.uv-python \
XDG_CACHE_HOME=.cache \
MPLCONFIGDIR=.cache/matplotlib \
  uv run python src/enclosure.py

COMMON=(
  build/sand_cube.step
  --resolution 1400,1400
  --camera-view-up=0,0,1
  --camera-orthographic
  --camera-zoom-factor=0.85
  --background-color="#f4f1ea"
  --color="#111416"
  --ambient-occlusion
  --anti-aliasing=ssaa
  --tone-mapping
  --grid=0
  --axis=0
  --filename=0
  --notifications=0
)

mkdir -p previews

f3d "${COMMON[@]}" \
  --output previews/sand_cube_f3d_front.png \
  --camera-direction=0,1,0

f3d "${COMMON[@]}" \
  --output previews/sand_cube_f3d_rear.png \
  --camera-direction=0,-1,0

f3d "${COMMON[@]}" \
  --output previews/sand_cube_f3d_iso.png \
  --resolution 1800,1400 \
  --camera-direction=-1,1,0.55 \
  --camera-zoom-factor=0.82
