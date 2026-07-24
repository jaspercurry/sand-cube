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
import os
from pathlib import Path
import runpy
import sys

from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    collect_loaded_repo_sources,
    write_producer_attestation,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--historical-entrypoint", type=Path, required=True)
    parser.add_argument("--current-root", type=Path, required=True)
    parser.add_argument("--current-entrypoint", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--parent-stage-root", type=Path, required=True)
    parser.add_argument("--geometry-source-commit", required=True)
    parser.add_argument("--capture-overlay-sha256", required=True)
    return parser.parse_args()


def main() -> None:
    """Run the extracted source and retain its actual loaded-source closure."""

    args = _arguments()
    historical_root = args.historical_root.resolve()
    entrypoint = args.historical_entrypoint.resolve()
    if not entrypoint.is_file():
        raise FileNotFoundError(entrypoint)
    sys.path.insert(0, str(historical_root))
    current_root = args.current_root.resolve()
    prior_cwd = current_root
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
        os.environ["CAD_JOB_REPO_ROOT"] = str(current_root)
        os.environ["CAD_JOB_STAGE_ROOT"] = str(
            args.parent_stage_root.resolve()
        )
        if exit_code in (None, 0):
            write_producer_attestation(
                repo_root=current_root,
                output_directory=args.output_directory.resolve(),
                producer_entrypoint=args.current_entrypoint.resolve(),
                historical_sources=records,
                geometry_source_commit=args.geometry_source_commit,
                capture_overlay_sha256=args.capture_overlay_sha256,
            )


if __name__ == "__main__":
    main()
