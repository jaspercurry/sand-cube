"""Immutable, native-free result objects for reusable geometry measurements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import TypeAlias

from cad_verification import ActualValue, Measurement, Unit


Scalar: TypeAlias = bool | int | float | str


class StringEnum(str, Enum):
    """A stable string-valued enum without a native CAD dependency."""


class DiagnosticStatus(StringEnum):
    """Operational status of a measurement, separate from acceptance policy."""

    SUCCESS = "success"
    SHORT_CIRCUITED = "short_circuited"
    EMPTY = "empty"
    INDETERMINATE = "indeterminate"
    INVALID = "invalid"


class FailureReason(StringEnum):
    """Machine-readable reason that a measurement is not usable."""

    NO_RETURNED_SHAPE = "no_returned_shape"
    EMPTY_SHAPE = "empty_shape"
    UNSUPPORTED_INPUT = "unsupported_input"
    INVALID_TOPOLOGY = "invalid_topology"
    OPERATION_FAILED = "operation_failed"
    MALFORMED_GEOMETRY = "malformed_geometry"


class BooleanOutcome(StringEnum):
    """Exhaustive intersection outcomes that must not collapse to zero."""

    BOUNDING_BOX_DISJOINT = "bounding_box_disjoint"
    NO_RETURNED_SHAPE = "no_returned_shape"
    EMPTY_SHAPE = "empty_shape"
    ZERO_VOLUME_CONTACT = "zero_volume_contact"
    POSITIVE_VOLUME = "positive_volume"
    INVALID_OR_UNEXPECTED_TOPOLOGY = "invalid_or_unexpected_topology"


@dataclass(frozen=True)
class MeasurementTolerance:
    """One explicit tolerance with the unit it applies to."""

    value: float
    unit: Unit
    name: str

    def __post_init__(self) -> None:
        if not isfinite(self.value) or self.value < 0:
            raise ValueError(f"{self.name} tolerance must be finite and non-negative")


@dataclass(frozen=True)
class Diagnostic:
    """Status, diagnostics, tolerances, and an optional failure reason."""

    status: DiagnosticStatus
    message: str
    tolerances: tuple[MeasurementTolerance, ...] = ()
    failure_reason: FailureReason | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("diagnostic message must not be empty")
        failed = self.status in {
            DiagnosticStatus.EMPTY,
            DiagnosticStatus.INDETERMINATE,
            DiagnosticStatus.INVALID,
        }
        if failed != (self.failure_reason is not None):
            raise ValueError(
                "empty, indeterminate, and invalid diagnostics require a failure "
                "reason; successful diagnostics must not have one"
            )

    @property
    def usable(self) -> bool:
        return self.status in {
            DiagnosticStatus.SUCCESS,
            DiagnosticStatus.SHORT_CIRCUITED,
        }

    def describe(self) -> str:
        reason = (
            f"; reason={self.failure_reason.value}" if self.failure_reason else ""
        )
        tolerances = ", ".join(
            f"{item.name}={item.value:g} {item.unit.value}"
            for item in self.tolerances
        )
        suffix = f"; tolerances: {tolerances}" if tolerances else ""
        return f"status={self.status.value}{reason}; {self.message}{suffix}"


@dataclass(frozen=True)
class ShapeNormalization:
    """Normalized topological leaves with explicit count semantics."""

    shapes: tuple[object, ...]
    input_count: int
    diagnostic: Diagnostic
    unit: Unit = Unit.COUNT

    @property
    def count(self) -> int:
        return len(self.shapes)


@dataclass(frozen=True)
class SolidNormalization:
    """Normalized solids with explicit count semantics."""

    solids: tuple[object, ...]
    input_count: int
    diagnostic: Diagnostic
    unit: Unit = Unit.COUNT

    @property
    def count(self) -> int:
        return len(self.solids)


@dataclass(frozen=True)
class ScalarMeasurement:
    """One scalar measurement that can feed ``cad_verification``."""

    value: Scalar | None
    unit: Unit
    diagnostic: Diagnostic

    def as_verification_measurement(self) -> Measurement:
        return verification_measurement(self.value, self.unit, self.diagnostic)


@dataclass(frozen=True)
class BooleanMeasurement:
    """A volume-bearing Boolean result with non-ambiguous outcome semantics."""

    volume_mm3: float | None
    outcome: BooleanOutcome
    diagnostic: Diagnostic
    unit: Unit = Unit.CUBIC_MILLIMETER

    def as_verification_measurement(self) -> Measurement:
        return verification_measurement(
            self.volume_mm3,
            self.unit,
            self.diagnostic,
        )


@dataclass(frozen=True)
class PrintBedContactMeasurement:
    """Planar contact area and its axis-aligned minimum footprint width."""

    area_mm2: float | None
    width_mm: float | None
    face_count: int
    diagnostic: Diagnostic
    area_unit: Unit = Unit.SQUARE_MILLIMETER
    width_unit: Unit = Unit.MILLIMETER

    def area_measurement(self) -> Measurement:
        return verification_measurement(
            self.area_mm2,
            self.area_unit,
            self.diagnostic,
        )

    def width_measurement(self) -> Measurement:
        return verification_measurement(
            self.width_mm,
            self.width_unit,
            self.diagnostic,
        )


@dataclass(frozen=True)
class TopologySummary:
    """Deterministic topological counts and edge-adjacency classification."""

    shape_count: int
    solid_count: int
    shell_count: int
    face_count: int
    edge_count: int
    vertex_count: int
    boundary_edge_count: int
    manifold_edge_count: int
    non_manifold_edge_count: int
    diagnostic: Diagnostic
    unit: Unit = Unit.COUNT


VectorTuple: TypeAlias = tuple[float, float, float]


@dataclass(frozen=True)
class EdgeSample:
    """One canonical point/tangent sample along an edge."""

    position_mm: VectorTuple
    tangent: VectorTuple


@dataclass(frozen=True)
class EdgeSignature:
    """Orientation-independent sampled edge signature."""

    geometry_type: str
    length_mm: float
    samples: tuple[EdgeSample, ...]


@dataclass(frozen=True)
class EdgeSignatureMeasurement:
    """Sorted edge signatures with explicit sampling tolerance."""

    signatures: tuple[EdgeSignature, ...]
    diagnostic: Diagnostic
    unit: Unit = Unit.MILLIMETER


@dataclass(frozen=True)
class ContinuityMeasurement:
    """Endpoint/tangent or adjacent-surface normal continuity."""

    gap_mm: float | None
    angle_change_deg: float | None
    continuous: bool | None
    kind: str
    sample_count: int
    diagnostic: Diagnostic
    gap_unit: Unit = Unit.MILLIMETER
    angle_unit: Unit = Unit.DEGREE

    def gap_measurement(self) -> Measurement:
        return verification_measurement(
            self.gap_mm,
            self.gap_unit,
            self.diagnostic,
        )

    def angle_measurement(self) -> Measurement:
        return verification_measurement(
            self.angle_change_deg,
            self.angle_unit,
            self.diagnostic,
        )


@dataclass(frozen=True)
class ProtectedMaterialComparison:
    """Bidirectional material loss and addition relative to a reference."""

    reference_volume_mm3: float | None
    candidate_volume_mm3: float | None
    removed_volume_mm3: float | None
    added_volume_mm3: float | None
    diagnostic: Diagnostic
    unit: Unit = Unit.CUBIC_MILLIMETER

    def removed_measurement(self) -> Measurement:
        return verification_measurement(
            self.removed_volume_mm3,
            self.unit,
            self.diagnostic,
        )

    def added_measurement(self) -> Measurement:
        return verification_measurement(
            self.added_volume_mm3,
            self.unit,
            self.diagnostic,
        )


@dataclass(frozen=True)
class ProtectedSurfaceComparison:
    """Bidirectional sampled distances between protected surface sets."""

    reference_area_mm2: float | None
    candidate_area_mm2: float | None
    reference_to_candidate_max_mm: float | None
    candidate_to_reference_max_mm: float | None
    reference_sample_count: int
    candidate_sample_count: int
    diagnostic: Diagnostic
    distance_unit: Unit = Unit.MILLIMETER
    area_unit: Unit = Unit.SQUARE_MILLIMETER


def verification_measurement(
    value: Scalar | None,
    unit: Unit,
    diagnostic: Diagnostic,
) -> Measurement:
    """Bridge a usable implementation result into the existing contract type."""

    if value is None or not diagnostic.usable:
        raise ValueError(
            "geometry result cannot feed cad_verification: "
            + diagnostic.describe()
        )
    return Measurement(
        actual=ActualValue(value=value, unit=unit),
        diagnostic=diagnostic.describe(),
    )
