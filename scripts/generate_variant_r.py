"""Thin coordinated entrypoint for the accepted Variant R generator."""

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

import os
from pathlib import Path
import subprocess
import sys
import tarfile

from cad_runner.outputs import job_output_path  # noqa: E402
from src.enclosure_family.variant_r.historical_capture import (  # noqa: E402
    CAPTURE_OUTPUT_ENV,
    GEOMETRY_SOURCE_COMMIT,
    HISTORICAL_VARIANT_R_GENERATOR,
    apply_capture_overlay,
    capture_overlay_sha256,
)
from src.enclosure_family.variant_r.inputs import (  # noqa: E402
    AUTHORITATIVE_BASE_FILENAME,
    model_output_directory,
)


_HISTORICAL_ARCHIVE_PATHS = (
    "AGENTS.md",
    "pyproject.toml",
    "params.py",
    "cad_runner",
    "experiments",
    "objects",
    "src",
)


def _extract_historical_source(destination: Path) -> None:
    archive = destination.parent / "variant-r-historical-source.tar"
    subprocess.run(
        (
            "git",
            "archive",
            "--format=tar",
            f"--output={archive}",
            GEOMETRY_SOURCE_COMMIT,
            *_HISTORICAL_ARCHIVE_PATHS,
        ),
        cwd=_CAD_SAFETY_ROOT,
        check=True,
    )
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter="data")


def main() -> None:
    """Produce the exact accepted base from its immutable source revision."""

    parent_stage = Path(os.environ["CAD_JOB_STAGE_ROOT"]).resolve()
    output_directory = job_output_path(
        model_output_directory(_CAD_SAFETY_ROOT)
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    base_step = output_directory / AUTHORITATIVE_BASE_FILENAME
    historical_workspace = parent_stage.parent / "historical-producer"
    historical_workspace.mkdir()
    historical_root = historical_workspace / "repo"
    historical_root.mkdir()
    _extract_historical_source(historical_root)
    apply_capture_overlay(historical_root)
    historical_stage = historical_workspace / "stage"
    historical_stage.mkdir()
    environment = os.environ.copy()
    environment[CAPTURE_OUTPUT_ENV] = str(base_step)
    environment["CAD_JOB_REPO_ROOT"] = str(historical_root)
    environment["CAD_JOB_STAGE_ROOT"] = str(historical_stage)
    arguments = (
        sys.executable,
        str(
            _CAD_SAFETY_ROOT
            / "scripts"
            / "run_historical_variant_r_base_capture.py"
        ),
        "--historical-root",
        str(historical_root),
        "--historical-entrypoint",
        str(historical_root / HISTORICAL_VARIANT_R_GENERATOR),
        "--current-root",
        str(_CAD_SAFETY_ROOT),
        "--current-entrypoint",
        str(Path(__file__).resolve()),
        "--output-directory",
        str(output_directory),
        "--parent-stage-root",
        str(parent_stage),
        "--geometry-source-commit",
        GEOMETRY_SOURCE_COMMIT,
        "--capture-overlay-sha256",
        capture_overlay_sha256(),
    )
    os.chdir(historical_root)
    os.execve(sys.executable, arguments, environment)


if __name__ == "__main__":
    main()
