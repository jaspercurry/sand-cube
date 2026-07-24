"""Internal child process for one supervised historical base capture."""

from __future__ import annotations


# This guard must remain before all native CAD/threaded-library imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import argparse
import json
import os
from pathlib import Path
import runpy
import sys

from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    collect_loaded_repo_sources,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--historical-entrypoint", type=Path, required=True)
    parser.add_argument("--closure-out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Run the extracted source and retain its actual loaded-source closure."""

    args = _arguments()
    historical_root = args.historical_root.resolve()
    entrypoint = args.historical_entrypoint.resolve()
    if not entrypoint.is_file():
        raise FileNotFoundError(entrypoint)
    sys.path.insert(0, str(historical_root))
    prior_cwd = Path.cwd()
    exit_code: object = 0
    try:
        os.chdir(historical_root)
        try:
            runpy.run_path(str(entrypoint), run_name="__main__")
        except SystemExit as error:
            exit_code = error.code
            if exit_code not in (None, 0):
                raise
    finally:
        os.chdir(prior_cwd)
        records = collect_loaded_repo_sources(
            historical_root,
            explicit_sources=(entrypoint,),
        )
        args.closure_out.parent.mkdir(parents=True, exist_ok=True)
        args.closure_out.write_text(
            json.dumps(
                {
                    "child_exit_code": exit_code,
                    "sources": records,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
