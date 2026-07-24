"""Independent ownership boundary for the removable-baffle Variant R."""

from .artifacts import VARIANT_R_ARTIFACTS
from .inputs import (
    AUTHORITATIVE_BASE_FILENAME,
    MODEL_OUTPUT_DIRECTORY,
    PRODUCER_ATTESTATION_FILENAME,
    PRODUCER_ENTRYPOINT,
    RELEASE_ATTESTATION_FILENAME,
)
from .model import VARIANT_R_MODEL
from .parameters import VARIANT_R_PARAMETERS, VariantRParameters
from .print_contracts import VARIANT_R_PRINT_CONTRACTS
from .verification import VARIANT_R_VERIFICATION

__all__ = [
    "VARIANT_R_ARTIFACTS",
    "AUTHORITATIVE_BASE_FILENAME",
    "MODEL_OUTPUT_DIRECTORY",
    "PRODUCER_ATTESTATION_FILENAME",
    "PRODUCER_ENTRYPOINT",
    "RELEASE_ATTESTATION_FILENAME",
    "VARIANT_R_MODEL",
    "VARIANT_R_PARAMETERS",
    "VARIANT_R_PRINT_CONTRACTS",
    "VARIANT_R_VERIFICATION",
    "VariantRParameters",
]
