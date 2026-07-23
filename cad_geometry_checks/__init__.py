"""Native-free public result model for reusable geometry checks.

Import :mod:`cad_geometry_checks.native` explicitly to execute kernel-backed
measurements.
"""

from .model import (
    BooleanMeasurement,
    BooleanOutcome,
    ContinuityMeasurement,
    Diagnostic,
    DiagnosticStatus,
    EdgeSample,
    EdgeSignature,
    EdgeSignatureMeasurement,
    FailureReason,
    MeasurementTolerance,
    PrintBedContactMeasurement,
    ProtectedMaterialComparison,
    ProtectedSurfaceComparison,
    ScalarMeasurement,
    ShapeNormalization,
    SolidNormalization,
    TopologySummary,
    verification_measurement,
)


__all__ = [
    "BooleanMeasurement",
    "BooleanOutcome",
    "ContinuityMeasurement",
    "Diagnostic",
    "DiagnosticStatus",
    "EdgeSample",
    "EdgeSignature",
    "EdgeSignatureMeasurement",
    "FailureReason",
    "MeasurementTolerance",
    "PrintBedContactMeasurement",
    "ProtectedMaterialComparison",
    "ProtectedSurfaceComparison",
    "ScalarMeasurement",
    "ShapeNormalization",
    "SolidNormalization",
    "TopologySummary",
    "verification_measurement",
]
