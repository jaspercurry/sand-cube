"""Authoritative generated-input contract for the accepted Variant R."""

from __future__ import annotations

from pathlib import Path
from typing import Final


PRODUCER_ENTRYPOINT: Final = Path("scripts/generate_variant_r.py")
MODEL_OUTPUT_DIRECTORY: Final = Path(
    "build/"
    "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
AUTHORITATIVE_BASE_FILENAME: Final = (
    "sand_cube_190x210_single_oval_port_base.step"
)
PRODUCER_ATTESTATION_FILENAME: Final = "variant_r_producer_attestation.json"

# This identity belongs to the historical accepted Stage 1 input.  It remains
# here only so old diagnostics can be audited without requiring the ignored
# historical file to exist.
HISTORICAL_ACCEPTED_BASE_SHA256: Final = (
    "441cc122c0383da257b16e80c4b424096f33b267cc95cab9d1278fb05a43a784"
)


def model_output_directory(repo_root: Path) -> Path:
    """Return the cataloged generated-output directory for Variant R."""

    return repo_root / MODEL_OUTPUT_DIRECTORY


def authoritative_base_step(repo_root: Path) -> Path:
    """Return the base STEP produced by the cataloged Variant R entrypoint."""

    return model_output_directory(repo_root) / AUTHORITATIVE_BASE_FILENAME


def producer_attestation_path(repo_root: Path) -> Path:
    """Return the immutable-input attestation paired with the generated base."""

    return (
        model_output_directory(repo_root) / PRODUCER_ATTESTATION_FILENAME
    )
