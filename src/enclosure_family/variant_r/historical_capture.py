"""Immutable capture overlay for the accepted Variant R base producer."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final


GEOMETRY_SOURCE_COMMIT: Final = (
    "789cf7fb4f63d9567585198c47bc3b5b122e070f"
)
HISTORICAL_ROOT_GENERATOR: Final = Path(
    "experiments/sand_cube_190x210_single_oval_port/"
    "generate_sand_cube_190x210_single_oval_port.py"
)
HISTORICAL_VARIANT_R_GENERATOR: Final = Path(
    "experiments/"
    "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle/"
    "generate_sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle.py"
)
CAPTURE_OUTPUT_ENV: Final = "VARIANT_R_HISTORICAL_BASE_OUTPUT"

_CAPTURE_NEEDLE: Final = """\
    base = build_base(
        provisional_brace_clearance,
        provisional_install_clearance,
    )
    _, provisional_tube_displacement = build_internal_tube(
"""
_CAPTURE_REPLACEMENT: Final = """\
    base = build_base(
        provisional_brace_clearance,
        provisional_install_clearance,
    )
    # Capture-only overlay: publish the untouched accepted base immediately
    # after its authoritative construction, before unrelated preview work.
    capture_path = Path(__import__("os").environ[
        "VARIANT_R_HISTORICAL_BASE_OUTPUT"
    ])
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(base, capture_path, unit=Unit.MM, write_pcurves=True)
    imported_capture = import_step(capture_path)
    if (
        len(base.solids()) != 1
        or not base.is_valid
        or len(imported_capture.solids()) != 1
        or not imported_capture.is_valid
    ):
        raise ValueError("Historical Variant R base capture failed round trip")
    raise SystemExit(0)
    _, provisional_tube_displacement = build_internal_tube(
"""


def capture_overlay_sha256() -> str:
    """Return a stable identity for the one exact source transformation."""

    payload = (
        HISTORICAL_ROOT_GENERATOR.as_posix()
        + "\0"
        + _CAPTURE_NEEDLE
        + "\0"
        + _CAPTURE_REPLACEMENT
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def apply_capture_overlay(extracted_repo_root: Path) -> Path:
    """Apply the capture-only transformation to an extracted Git tree."""

    source = extracted_repo_root / HISTORICAL_ROOT_GENERATOR
    original = source.read_text(encoding="utf-8")
    if original.count(_CAPTURE_NEEDLE) != 1:
        raise ValueError(
            "Historical Variant R capture boundary changed or is ambiguous: "
            f"{source}"
        )
    source.write_text(
        original.replace(
            _CAPTURE_NEEDLE,
            _CAPTURE_REPLACEMENT,
            1,
        ),
        encoding="utf-8",
    )
    return source
