#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-.uv-python}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-.cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-.cache/matplotlib}"

exec uv run python src/show_model.py "$@"
