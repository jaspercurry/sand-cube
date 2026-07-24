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

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

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
from src.enclosure_family.variant_r.provenance import (  # noqa: E402
    write_producer_attestation,
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

    output_directory = job_output_path(
        model_output_directory(_CAD_SAFETY_ROOT)
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    base_step = output_directory / AUTHORITATIVE_BASE_FILENAME
    with tempfile.TemporaryDirectory(
        prefix="variant-r-historical-producer-"
    ) as temporary:
        temporary_root = Path(temporary)
        historical_root = temporary_root / "repo"
        historical_root.mkdir()
        _extract_historical_source(historical_root)
        apply_capture_overlay(historical_root)
        closure_path = temporary_root / "loaded-source-closure.json"
        environment = os.environ.copy()
        environment[CAPTURE_OUTPUT_ENV] = str(base_step)
        subprocess.run(
            (
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
                "--closure-out",
                str(closure_path),
            ),
            cwd=historical_root,
            env=environment,
            check=True,
        )
        closure = json.loads(closure_path.read_text(encoding="utf-8"))
    write_producer_attestation(
        repo_root=_CAD_SAFETY_ROOT,
        output_directory=output_directory,
        producer_entrypoint=_CadSafetyPath(__file__),
        historical_sources=closure["sources"],
        geometry_source_commit=GEOMETRY_SOURCE_COMMIT,
        capture_overlay_sha256=capture_overlay_sha256(),
    )


if __name__ == "__main__":
    main()
