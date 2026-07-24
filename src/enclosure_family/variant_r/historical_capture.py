"""Immutable capture overlay for the accepted Variant R base producer."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

from .inputs import (
    HISTORICAL_ACCEPTED_BASE_DATA_SHA256,
    HISTORICAL_ACCEPTED_BASE_SHA256,
    HISTORICAL_ACCEPTED_STEP_TIMESTAMP,
)


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


def canonicalize_accepted_step_header(
    step_path: Path,
    *,
    expected_sha256: str = HISTORICAL_ACCEPTED_BASE_SHA256,
    expected_data_sha256: str = HISTORICAL_ACCEPTED_BASE_DATA_SHA256,
) -> dict[str, str]:
    """Reproduce the accepted STEP serialization without changing its DATA."""

    content = step_path.read_bytes()
    marker = b"DATA;"
    data_offset = content.find(marker)
    if data_offset < 0:
        raise ValueError(f"STEP DATA section is missing: {step_path}")
    prefix = b"FILE_NAME('Open CASCADE Shape Model','"
    timestamp_offset = content.find(prefix)
    if timestamp_offset < 0 or timestamp_offset >= data_offset:
        raise ValueError(f"STEP FILE_NAME header is missing: {step_path}")
    timestamp_offset += len(prefix)
    timestamp_end = timestamp_offset + len(HISTORICAL_ACCEPTED_STEP_TIMESTAMP)
    if (
        timestamp_end >= data_offset
        or content[timestamp_end : timestamp_end + 1] != b"'"
    ):
        raise ValueError(f"Unexpected STEP FILE_NAME timestamp: {step_path}")
    canonical = (
        content[:timestamp_offset]
        + HISTORICAL_ACCEPTED_STEP_TIMESTAMP.encode("ascii")
        + content[timestamp_end:]
    )
    data_sha256 = hashlib.sha256(canonical[data_offset:]).hexdigest()
    if data_sha256 != expected_data_sha256:
        raise ValueError(
            "Canonicalized Variant R STEP DATA differs from accepted input: "
            f"{data_sha256}"
        )
    full_sha256 = hashlib.sha256(canonical).hexdigest()
    if full_sha256 != expected_sha256:
        raise ValueError(
            "Canonicalized Variant R STEP file differs from accepted input: "
            f"{full_sha256}"
        )
    step_path.write_bytes(canonical)
    return {
        "canonical_file_name_timestamp": HISTORICAL_ACCEPTED_STEP_TIMESTAMP,
        "sha256": full_sha256,
        "step_data_section_sha256": data_sha256,
    }
