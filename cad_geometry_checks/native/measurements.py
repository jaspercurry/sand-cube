"""Duck-typed measurements for Build123d/OCP objects.

This module is only reachable through :mod:`cad_geometry_checks.native`.  It
does not import a native CAD module itself, which keeps fake-object semantic
tests lightweight.  Real callers must still enter through ``cad_runner`` before
constructing or importing native objects.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import acos, ceil, degrees, isfinite, log10, radians
from numbers import Real

from cad_verification import Unit

from ..model import (
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
)


_LEAF_TYPES = {"Vertex", "Edge", "Wire", "Face", "Shell", "Solid"}
_EXPECTED_INTERSECTION_TYPES = {"Vertex", "Edge", "Face", "Solid"}


@dataclass(frozen=True)
class _Bounds:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float


class _InvalidTopologyError(ValueError):
    """Internal marker for topology failures during normalization."""


def _diagnostic(
    status: DiagnosticStatus,
    message: str,
    *,
    tolerances: tuple[MeasurementTolerance, ...] = (),
    failure_reason: FailureReason | None = None,
) -> Diagnostic:
    return Diagnostic(
        status=status,
        message=message,
        tolerances=tolerances,
        failure_reason=failure_reason,
    )


def _invalid(
    message: str,
    *,
    reason: FailureReason,
    tolerances: tuple[MeasurementTolerance, ...] = (),
) -> Diagnostic:
    return _diagnostic(
        DiagnosticStatus.INVALID,
        message,
        tolerances=tolerances,
        failure_reason=reason,
    )


def _validated_tolerances(
    *specifications: tuple[str, object, Unit, bool],
) -> tuple[tuple[MeasurementTolerance, ...], str | None]:
    """Build tolerances without allowing public parameter errors to escape."""

    tolerances: list[MeasurementTolerance] = []
    for name, raw_value, unit, strictly_positive in specifications:
        if isinstance(raw_value, bool) or not isinstance(raw_value, Real):
            return (), (
                f"{name} tolerance must be a real number, got "
                f"{type(raw_value).__name__}"
            )
        value = float(raw_value)
        if not isfinite(value):
            return (), f"{name} tolerance must be finite, got {raw_value!r}"
        if value < 0 or (strictly_positive and value == 0):
            qualifier = "positive" if strictly_positive else "non-negative"
            return (), f"{name} tolerance must be {qualifier}, got {value:g}"
        tolerances.append(
            MeasurementTolerance(value=value, unit=unit, name=name)
        )
    return tuple(tolerances), None


def _validated_count(
    name: str,
    value: object,
    *,
    minimum: int,
) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return f"{name} must be an integer, got {type(value).__name__}"
    if value < minimum:
        return f"{name} must be at least {minimum}, got {value}"
    return None


def _validated_finite(name: str, value: object) -> str | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return f"{name} must be a real number, got {type(value).__name__}"
    if not isfinite(float(value)):
        return f"{name} must be finite, got {value!r}"
    return None


def _shape_type(shape: object) -> str:
    raw = getattr(shape, "shape_type")
    raw = raw() if callable(raw) else raw
    value = getattr(raw, "value", raw)
    return str(value).split(".")[-1]


def _looks_like_shape(value: object) -> bool:
    descriptor = getattr(type(value), "shape_type", None)
    instance_marker = getattr(getattr(value, "__dict__", {}), "get", lambda _key: None)(
        "shape_type"
    )
    return descriptor is not None or instance_marker is not None


def _top_level_count(value: object) -> int:
    if value is None or _looks_like_shape(value):
        return 1
    if isinstance(value, (str, bytes, bytearray, dict)):
        return 1
    try:
        return len(value)  # type: ignore[arg-type]
    except (TypeError, AttributeError):
        return 1


def _prepare_input(value: object) -> object:
    """Materialize one-shot top-level iterables once for stable count/use."""

    if (
        value is None
        or _looks_like_shape(value)
        or isinstance(value, (str, bytes, bytearray, dict))
        or not isinstance(value, Iterable)
        or hasattr(value, "__len__")
    ):
        return value
    return tuple(value)


def _is_valid(shape: object) -> bool:
    raw = getattr(shape, "is_valid")
    return bool(raw() if callable(raw) else raw)


def _flatten_shapes(value: object, *, nested: bool = False) -> list[object]:
    if value is None:
        if nested:
            raise ValueError("nested None is not a shape")
        return []
    if _looks_like_shape(value):
        if not bool(value):
            return []
        if not _is_valid(value):
            raise _InvalidTopologyError(
                f"{type(value).__name__}({_shape_type(value)}) is invalid"
            )
        shape_type = _shape_type(value)
        if shape_type in {"Compound", "CompSolid"}:
            getter = getattr(value, "get_top_level_shapes", None)
            if not callable(getter):
                raise ValueError(
                    f"{type(value).__name__} reports {shape_type} but has no "
                    "get_top_level_shapes()"
                )
            children = list(getter())
            leaves: list[object] = []
            for child in children:
                leaves.extend(_flatten_shapes(child, nested=True))
            return leaves
        return [value]
    if isinstance(value, (str, bytes, bytearray, dict)):
        raise ValueError(f"unsupported geometry input type: {type(value).__name__}")
    if isinstance(value, Iterable):
        leaves = []
        for item in value:
            leaves.extend(_flatten_shapes(item, nested=True))
        return leaves
    raise ValueError(f"unsupported geometry input type: {type(value).__name__}")


def normalize_shapes(value: object) -> ShapeNormalization:
    """Normalize ``None``, shapes, iterables, and compounds to leaf shapes."""

    try:
        prepared = _prepare_input(value)
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ShapeNormalization(
            shapes=(),
            input_count=1,
            diagnostic=_invalid(
                f"cannot materialize geometry input: {type(exc).__name__}: {exc}",
                reason=FailureReason.UNSUPPORTED_INPUT,
            ),
        )
    count = _top_level_count(prepared)
    if value is None:
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_diagnostic(
                DiagnosticStatus.INDETERMINATE,
                "the geometry operation returned None",
                failure_reason=FailureReason.NO_RETURNED_SHAPE,
            ),
        )
    try:
        shapes = tuple(_flatten_shapes(prepared))
    except _InvalidTopologyError as exc:
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_invalid(
                f"cannot normalize invalid topology: {exc}",
                reason=FailureReason.INVALID_TOPOLOGY,
            ),
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_invalid(
                f"cannot normalize shapes: {type(exc).__name__}: {exc}",
                reason=FailureReason.UNSUPPORTED_INPUT,
            ),
        )
    if not shapes:
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_diagnostic(
                DiagnosticStatus.EMPTY,
                "geometry input contains no topological leaves",
                failure_reason=FailureReason.EMPTY_SHAPE,
            ),
        )
    try:
        invalid_types = [
            _shape_type(shape)
            for shape in shapes
            if _shape_type(shape) not in _LEAF_TYPES
        ]
        invalid_shapes = [
            f"{type(shape).__name__}({_shape_type(shape)})"
            for shape in shapes
            if not _is_valid(shape)
        ]
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_invalid(
                f"malformed shape during validation: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
            ),
        )
    if invalid_types or invalid_shapes:
        details = ", ".join(invalid_types + invalid_shapes)
        return ShapeNormalization(
            shapes=(),
            input_count=count,
            diagnostic=_invalid(
                f"invalid or unexpected topology: {details}",
                reason=FailureReason.INVALID_TOPOLOGY,
            ),
        )
    return ShapeNormalization(
        shapes=shapes,
        input_count=count,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"normalized {count} input item(s) to {len(shapes)} leaf shape(s)",
        ),
    )


def normalize_solids(value: object) -> SolidNormalization:
    """Normalize supported geometry to valid solids without native type imports."""

    normalized = normalize_shapes(value)
    if not normalized.diagnostic.usable:
        return SolidNormalization(
            solids=(),
            input_count=normalized.input_count,
            diagnostic=normalized.diagnostic,
        )
    unexpected = [
        f"{type(shape).__name__}({_shape_type(shape)})"
        for shape in normalized.shapes
        if _shape_type(shape) != "Solid"
    ]
    if unexpected:
        return SolidNormalization(
            solids=(),
            input_count=normalized.input_count,
            diagnostic=_invalid(
                "solid normalization received non-solid topology: "
                + ", ".join(unexpected),
                reason=FailureReason.INVALID_TOPOLOGY,
            ),
        )
    return SolidNormalization(
        solids=normalized.shapes,
        input_count=normalized.input_count,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"normalized {normalized.input_count} input item(s) to "
            f"{len(normalized.shapes)} solid(s)",
        ),
    )


def _number(value: object, label: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{label} is not finite")
    return number


def _solid_volume(solid: object, *, tolerance_mm3: float) -> float:
    volume = _number(getattr(solid, "volume"), "solid volume")
    if volume < -tolerance_mm3:
        raise ValueError(f"solid volume is negative: {volume:g} mm3")
    return max(0.0, volume)


def _union_solids(solids: Iterable[object]) -> tuple[object, ...]:
    """Return a material union so collections cannot double-count volume."""

    unique = _unique_shapes(solids)
    if len(unique) <= 1:
        return tuple(unique)
    fuse = getattr(unique[0], "fuse", None)
    if not callable(fuse):
        raise ValueError(
            "multi-solid material measurement requires a fuse-capable native shape"
        )
    union = normalize_solids(fuse(*unique[1:]))
    if not union.diagnostic.usable:
        raise ValueError(
            "cannot form a non-overlapping material union: "
            + union.diagnostic.message
        )
    return union.solids


def _union_volume(
    solids: Iterable[object],
    *,
    tolerance_mm3: float,
) -> tuple[float, int]:
    union_solids = _union_solids(solids)
    return (
        sum(
            _solid_volume(solid, tolerance_mm3=tolerance_mm3)
            for solid in union_solids
        ),
        len(union_solids),
    )


def measure_volume(
    value: object,
    *,
    tolerance_mm3: float = 1e-7,
) -> ScalarMeasurement:
    """Measure material-union volume with explicit empty/error semantics."""

    tolerance, parameter_error = _validated_tolerances(
        ("volume", tolerance_mm3, Unit.CUBIC_MILLIMETER, False),
    )
    if parameter_error:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_invalid(
                parameter_error,
                reason=FailureReason.UNSUPPORTED_INPUT,
            ),
        )
    normalized = normalize_solids(value)
    if normalized.diagnostic.status is DiagnosticStatus.EMPTY:
        return ScalarMeasurement(
            value=0.0,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                DiagnosticStatus.EMPTY,
                "empty geometry has no measurable solid volume",
                tolerances=tolerance,
                failure_reason=FailureReason.EMPTY_SHAPE,
            ),
        )
    if not normalized.diagnostic.usable:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                normalized.diagnostic.status,
                normalized.diagnostic.message,
                tolerances=tolerance,
                failure_reason=normalized.diagnostic.failure_reason,
            ),
        )
    try:
        volume, union_count = _union_volume(
            normalized.solids,
            tolerance_mm3=float(tolerance_mm3),
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_invalid(
                f"cannot measure volume: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerance,
            ),
        )
    return ScalarMeasurement(
        value=volume,
        unit=Unit.CUBIC_MILLIMETER,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"measured {volume:.9g} mm3 material union from "
            f"{normalized.count} input solid(s), yielding {union_count} "
            "non-overlapping solid(s)",
            tolerances=tolerance,
        ),
    )


def _coord(vector: object, name: str) -> float:
    return _number(getattr(vector, name), f"coordinate {name}")


def _bounds(shape: object) -> _Bounds:
    getter = getattr(shape, "bounding_box")
    box = getter() if callable(getter) else getter
    result = _Bounds(
        min_x=_coord(box.min, "X"),
        min_y=_coord(box.min, "Y"),
        min_z=_coord(box.min, "Z"),
        max_x=_coord(box.max, "X"),
        max_y=_coord(box.max, "Y"),
        max_z=_coord(box.max, "Z"),
    )
    if (
        result.min_x > result.max_x
        or result.min_y > result.max_y
        or result.min_z > result.max_z
    ):
        raise ValueError(f"inverted bounding box: {result}")
    return result


def _combine_bounds(shapes: Iterable[object]) -> _Bounds:
    boxes = tuple(_bounds(shape) for shape in shapes)
    if not boxes:
        raise ValueError("cannot bound an empty shape collection")
    return _Bounds(
        min(item.min_x for item in boxes),
        min(item.min_y for item in boxes),
        min(item.min_z for item in boxes),
        max(item.max_x for item in boxes),
        max(item.max_y for item in boxes),
        max(item.max_z for item in boxes),
    )


def _disjoint(left: _Bounds, right: _Bounds, tolerance_mm: float) -> bool:
    return (
        left.max_x < right.min_x - tolerance_mm
        or right.max_x < left.min_x - tolerance_mm
        or left.max_y < right.min_y - tolerance_mm
        or right.max_y < left.min_y - tolerance_mm
        or left.max_z < right.min_z - tolerance_mm
        or right.max_z < left.min_z - tolerance_mm
    )


def measure_intersection(
    left: object,
    right: object,
    *,
    bounding_box_tolerance_mm: float = 1e-7,
    boolean_tolerance_mm: float = 1e-7,
    volume_tolerance_mm3: float = 1e-7,
    operation: Callable[[object, object], object] | None = None,
) -> BooleanMeasurement:
    """Measure pairwise solid intersection after bounding-box rejection."""

    tolerances, parameter_error = _validated_tolerances(
        (
            "bounding_box",
            bounding_box_tolerance_mm,
            Unit.MILLIMETER,
            False,
        ),
        ("boolean", boolean_tolerance_mm, Unit.MILLIMETER, False),
        ("volume", volume_tolerance_mm3, Unit.CUBIC_MILLIMETER, False),
    )
    if parameter_error or (operation is not None and not callable(operation)):
        message = parameter_error or (
            f"operation must be callable or None, got {type(operation).__name__}"
        )
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
            diagnostic=_invalid(
                message,
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    bounding_tolerance = float(bounding_box_tolerance_mm)
    boolean_tolerance = float(boolean_tolerance_mm)
    volume_tolerance = float(volume_tolerance_mm3)
    left_solids = normalize_solids(left)
    right_solids = normalize_solids(right)
    for label, normalized in (("left", left_solids), ("right", right_solids)):
        if not normalized.diagnostic.usable:
            outcome = (
                BooleanOutcome.EMPTY_SHAPE
                if normalized.diagnostic.status is DiagnosticStatus.EMPTY
                else BooleanOutcome.NO_RETURNED_SHAPE
                if normalized.diagnostic.failure_reason
                is FailureReason.NO_RETURNED_SHAPE
                else BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY
            )
            return BooleanMeasurement(
                volume_mm3=None,
                outcome=outcome,
                diagnostic=_diagnostic(
                    normalized.diagnostic.status,
                    f"{label} intersection input is unusable: "
                    f"{normalized.diagnostic.message}",
                    tolerances=tolerances,
                    failure_reason=normalized.diagnostic.failure_reason,
                ),
            )
    try:
        if _disjoint(
            _combine_bounds(left_solids.solids),
            _combine_bounds(right_solids.solids),
            bounding_tolerance,
        ):
            return BooleanMeasurement(
                volume_mm3=0.0,
                outcome=BooleanOutcome.BOUNDING_BOX_DISJOINT,
                diagnostic=_diagnostic(
                    DiagnosticStatus.SHORT_CIRCUITED,
                    "aggregate bounding boxes are disjoint; Boolean was not run",
                    tolerances=tolerances,
                ),
            )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
            diagnostic=_invalid(
                f"cannot evaluate intersection bounds: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )

    intersect = operation or (
        lambda left_shape, right_shape: left_shape.intersect(  # type: ignore[attr-defined]
            right_shape,
            tolerance=boolean_tolerance,
            include_touched=True,
        )
    )
    attempted = 0
    missing = 0
    empty = 0
    results: list[object] = []
    try:
        for left_solid in left_solids.solids:
            left_bounds = _bounds(left_solid)
            for right_solid in right_solids.solids:
                if _disjoint(
                    left_bounds,
                    _bounds(right_solid),
                    bounding_tolerance,
                ):
                    continue
                attempted += 1
                raw_result = intersect(left_solid, right_solid)
                if raw_result is None:
                    missing += 1
                    continue
                normalized = normalize_shapes(raw_result)
                if normalized.diagnostic.status is DiagnosticStatus.EMPTY:
                    empty += 1
                    continue
                if not normalized.diagnostic.usable:
                    return BooleanMeasurement(
                        volume_mm3=None,
                        outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
                        diagnostic=_invalid(
                            "intersection returned invalid topology: "
                            + normalized.diagnostic.message,
                            reason=normalized.diagnostic.failure_reason
                            or FailureReason.INVALID_TOPOLOGY,
                            tolerances=tolerances,
                        ),
                    )
                results.extend(normalized.shapes)
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
            diagnostic=_invalid(
                f"intersection operation failed: {type(exc).__name__}: {exc}",
                reason=FailureReason.OPERATION_FAILED,
                tolerances=tolerances,
            ),
        )

    if attempted == 0:
        return BooleanMeasurement(
            volume_mm3=0.0,
            outcome=BooleanOutcome.BOUNDING_BOX_DISJOINT,
            diagnostic=_diagnostic(
                DiagnosticStatus.SHORT_CIRCUITED,
                "all solid-pair bounding boxes are disjoint; Boolean was not run",
                tolerances=tolerances,
            ),
        )
    if missing:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.NO_RETURNED_SHAPE,
            diagnostic=_diagnostic(
                DiagnosticStatus.INDETERMINATE,
                f"intersection returned no shape for {missing}/{attempted} "
                f"attempted pair(s); discarded {len(results)} partial "
                f"topological result(s) and {empty} empty result(s)",
                tolerances=tolerances,
                failure_reason=FailureReason.NO_RETURNED_SHAPE,
            ),
        )
    if empty:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.EMPTY_SHAPE,
            diagnostic=_diagnostic(
                DiagnosticStatus.EMPTY,
                f"intersection returned an explicit empty shape for "
                f"{empty}/{attempted} attempted pair(s); discarded "
                f"{len(results)} partial topological result(s)",
                tolerances=tolerances,
                failure_reason=FailureReason.EMPTY_SHAPE,
            ),
        )
    if not results:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.NO_RETURNED_SHAPE,
            diagnostic=_diagnostic(
                DiagnosticStatus.INDETERMINATE,
                "intersection produced no analyzable pair result",
                tolerances=tolerances,
                failure_reason=FailureReason.NO_RETURNED_SHAPE,
            ),
        )

    unexpected = sorted(
        {_shape_type(shape) for shape in results}
        - _EXPECTED_INTERSECTION_TYPES
    )
    if unexpected:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
            diagnostic=_invalid(
                "intersection returned unexpected topology: "
                + ", ".join(unexpected),
                reason=FailureReason.INVALID_TOPOLOGY,
                tolerances=tolerances,
            ),
        )
    try:
        volume, union_count = _union_volume(
            (
                shape
                for shape in results
                if _shape_type(shape) == "Solid"
            ),
            tolerance_mm3=volume_tolerance,
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return BooleanMeasurement(
            volume_mm3=None,
            outcome=BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY,
            diagnostic=_invalid(
                f"cannot measure intersection result: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    if volume > volume_tolerance:
        return BooleanMeasurement(
            volume_mm3=volume,
            outcome=BooleanOutcome.POSITIVE_VOLUME,
            diagnostic=_diagnostic(
                DiagnosticStatus.SUCCESS,
                f"positive-volume intersection union is {volume:.9g} mm3 "
                f"across {union_count} non-overlapping result solid(s)",
                tolerances=tolerances,
            ),
        )
    return BooleanMeasurement(
        volume_mm3=0.0,
        outcome=BooleanOutcome.ZERO_VOLUME_CONTACT,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"intersection returned contact topology with {volume:.9g} mm3 volume",
            tolerances=tolerances,
        ),
    )


def _difference_default(left: object, right: object) -> object:
    return left.cut(right)  # type: ignore[attr-defined]


def measure_difference(
    minuend: object,
    subtrahend: object,
    *,
    bounding_box_tolerance_mm: float = 1e-7,
    volume_tolerance_mm3: float = 1e-7,
    operation: Callable[[object, object], object] | None = None,
) -> ScalarMeasurement:
    """Measure volume remaining after subtracting all subtrahend solids."""

    tolerances, parameter_error = _validated_tolerances(
        (
            "bounding_box",
            bounding_box_tolerance_mm,
            Unit.MILLIMETER,
            False,
        ),
        ("volume", volume_tolerance_mm3, Unit.CUBIC_MILLIMETER, False),
    )
    if parameter_error or (operation is not None and not callable(operation)):
        message = parameter_error or (
            f"operation must be callable or None, got {type(operation).__name__}"
        )
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_invalid(
                message,
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    bounding_tolerance = float(bounding_box_tolerance_mm)
    volume_tolerance = float(volume_tolerance_mm3)
    left = normalize_solids(minuend)
    right = normalize_solids(subtrahend)
    if left.diagnostic.status is DiagnosticStatus.EMPTY:
        return ScalarMeasurement(
            value=0.0,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                DiagnosticStatus.EMPTY,
                "empty minuend leaves no protected material",
                tolerances=tolerances,
                failure_reason=FailureReason.EMPTY_SHAPE,
            ),
        )
    if not left.diagnostic.usable:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                left.diagnostic.status,
                "unusable minuend: " + left.diagnostic.message,
                tolerances=tolerances,
                failure_reason=left.diagnostic.failure_reason,
            ),
        )
    if right.diagnostic.status is DiagnosticStatus.EMPTY:
        volume = measure_volume(minuend, tolerance_mm3=volume_tolerance)
        return ScalarMeasurement(
            value=volume.value,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                DiagnosticStatus.SHORT_CIRCUITED,
                "empty subtrahend; returned the original minuend volume",
                tolerances=tolerances,
            ),
        )
    if not right.diagnostic.usable:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_diagnostic(
                right.diagnostic.status,
                "unusable subtrahend: " + right.diagnostic.message,
                tolerances=tolerances,
                failure_reason=right.diagnostic.failure_reason,
            ),
        )

    cut = operation or _difference_default
    calls = 0
    empty_results = 0
    try:
        pieces = list(_union_solids(left.solids))
        cutters = _union_solids(right.solids)
        for cutter in cutters:
            next_pieces: list[object] = []
            cutter_bounds = _bounds(cutter)
            for piece in pieces:
                if _disjoint(
                    _bounds(piece),
                    cutter_bounds,
                    bounding_tolerance,
                ):
                    next_pieces.append(piece)
                    continue
                calls += 1
                raw_result = cut(piece, cutter)
                if raw_result is None:
                    return ScalarMeasurement(
                        value=None,
                        unit=Unit.CUBIC_MILLIMETER,
                        diagnostic=_diagnostic(
                            DiagnosticStatus.INDETERMINATE,
                            "difference operation returned None",
                            tolerances=tolerances,
                            failure_reason=FailureReason.NO_RETURNED_SHAPE,
                        ),
                    )
                result = normalize_solids(raw_result)
                if result.diagnostic.status is DiagnosticStatus.EMPTY:
                    empty_results += 1
                    continue
                if not result.diagnostic.usable:
                    return ScalarMeasurement(
                        value=None,
                        unit=Unit.CUBIC_MILLIMETER,
                        diagnostic=_invalid(
                            "difference returned unusable topology: "
                            + result.diagnostic.message,
                            reason=result.diagnostic.failure_reason
                            or FailureReason.INVALID_TOPOLOGY,
                            tolerances=tolerances,
                        ),
                    )
                next_pieces.extend(result.solids)
            pieces = next_pieces
            if not pieces:
                break
        volume, union_count = _union_volume(
            pieces,
            tolerance_mm3=volume_tolerance,
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ScalarMeasurement(
            value=None,
            unit=Unit.CUBIC_MILLIMETER,
            diagnostic=_invalid(
                f"difference operation failed: {type(exc).__name__}: {exc}",
                reason=FailureReason.OPERATION_FAILED,
                tolerances=tolerances,
            ),
        )
    status = (
        DiagnosticStatus.SHORT_CIRCUITED
        if calls == 0
        else DiagnosticStatus.SUCCESS
    )
    return ScalarMeasurement(
        value=volume,
        unit=Unit.CUBIC_MILLIMETER,
        diagnostic=_diagnostic(
            status,
            f"difference leaves a {volume:.9g} mm3 material union across "
            f"{union_count} non-overlapping solid(s) after {calls} Boolean call(s); "
            f"{empty_results} call(s) returned an explicit empty shape",
            tolerances=tolerances,
        ),
    )


def compare_protected_material(
    reference: object,
    candidate: object,
    *,
    bounding_box_tolerance_mm: float = 1e-7,
    volume_tolerance_mm3: float = 1e-7,
) -> ProtectedMaterialComparison:
    """Measure removed and added material with two directed differences."""

    tolerances, parameter_error = _validated_tolerances(
        (
            "bounding_box",
            bounding_box_tolerance_mm,
            Unit.MILLIMETER,
            False,
        ),
        ("volume", volume_tolerance_mm3, Unit.CUBIC_MILLIMETER, False),
    )
    if parameter_error:
        return ProtectedMaterialComparison(
            reference_volume_mm3=None,
            candidate_volume_mm3=None,
            removed_volume_mm3=None,
            added_volume_mm3=None,
            diagnostic=_invalid(
                parameter_error,
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    bounding_tolerance = float(bounding_box_tolerance_mm)
    volume_tolerance = float(volume_tolerance_mm3)
    reference_volume = measure_volume(
        reference,
        tolerance_mm3=volume_tolerance,
    )
    candidate_volume = measure_volume(
        candidate,
        tolerance_mm3=volume_tolerance,
    )
    for label, result in (
        ("reference", reference_volume),
        ("candidate", candidate_volume),
    ):
        if result.value is None:
            return ProtectedMaterialComparison(
                reference_volume_mm3=reference_volume.value,  # type: ignore[arg-type]
                candidate_volume_mm3=candidate_volume.value,  # type: ignore[arg-type]
                removed_volume_mm3=None,
                added_volume_mm3=None,
                diagnostic=_invalid(
                    f"{label} material is unusable: {result.diagnostic.message}",
                    reason=result.diagnostic.failure_reason
                    or FailureReason.MALFORMED_GEOMETRY,
                    tolerances=tolerances,
                ),
            )
    reference_value = float(reference_volume.value)
    candidate_value = float(candidate_volume.value)
    if reference_value <= volume_tolerance:
        removed = 0.0
    else:
        directed = measure_difference(
            reference,
            candidate,
            bounding_box_tolerance_mm=bounding_tolerance,
            volume_tolerance_mm3=volume_tolerance,
        )
        if directed.value is None:
            return ProtectedMaterialComparison(
                reference_volume_mm3=reference_value,
                candidate_volume_mm3=candidate_value,
                removed_volume_mm3=None,
                added_volume_mm3=None,
                diagnostic=directed.diagnostic,
            )
        removed = float(directed.value)
    if candidate_value <= volume_tolerance:
        added = 0.0
    else:
        reverse = measure_difference(
            candidate,
            reference,
            bounding_box_tolerance_mm=bounding_tolerance,
            volume_tolerance_mm3=volume_tolerance,
        )
        if reverse.value is None:
            return ProtectedMaterialComparison(
                reference_volume_mm3=reference_value,
                candidate_volume_mm3=candidate_value,
                removed_volume_mm3=None,
                added_volume_mm3=None,
                diagnostic=reverse.diagnostic,
            )
        added = float(reverse.value)
    removed = 0.0 if removed <= volume_tolerance else removed
    added = 0.0 if added <= volume_tolerance else added
    return ProtectedMaterialComparison(
        reference_volume_mm3=reference_value,
        candidate_volume_mm3=candidate_value,
        removed_volume_mm3=removed,
        added_volume_mm3=added,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"bidirectional comparison: removed={removed:.9g} mm3, "
            f"added={added:.9g} mm3",
            tolerances=tolerances,
        ),
    )


def _faces_from_shapes(
    shapes: Iterable[object],
) -> tuple[tuple[object, ...], tuple[str, ...]]:
    faces: list[object] = []
    unsupported: list[str] = []
    for shape in shapes:
        if _shape_type(shape) == "Face":
            faces.append(shape)
            continue
        getter = getattr(shape, "faces", None)
        if not callable(getter):
            unsupported.append(_shape_type(shape))
            continue
        extracted = tuple(getter())
        if not extracted:
            unsupported.append(_shape_type(shape))
            continue
        faces.extend(extracted)
    return tuple(_unique_shapes(faces)), tuple(sorted(unsupported))


def _plane_normal(face: object) -> tuple[float, float, float] | None:
    plane = getattr(face, "is_planar")
    plane = plane() if callable(plane) else plane
    if plane is None:
        return None
    normal = getattr(plane, "z_dir")
    return (_coord(normal, "X"), _coord(normal, "Y"), _coord(normal, "Z"))


def measure_print_bed_contact(
    value: object,
    *,
    bed_z_mm: float = 0.0,
    linear_tolerance_mm: float = 1e-6,
    area_tolerance_mm2: float = 1e-7,
    angular_tolerance_deg: float = 1e-4,
) -> PrintBedContactMeasurement:
    """Measure planar faces coincident with a horizontal print bed."""

    tolerances, parameter_error = _validated_tolerances(
        ("linear", linear_tolerance_mm, Unit.MILLIMETER, False),
        ("area", area_tolerance_mm2, Unit.SQUARE_MILLIMETER, False),
        ("angular", angular_tolerance_deg, Unit.DEGREE, False),
    )
    bed_error = _validated_finite("bed_z_mm", bed_z_mm)
    if not parameter_error and float(angular_tolerance_deg) > 90:
        parameter_error = (
            f"angular tolerance must not exceed 90 degrees, got "
            f"{float(angular_tolerance_deg):g}"
        )
    if parameter_error or bed_error:
        return PrintBedContactMeasurement(
            area_mm2=None,
            width_mm=None,
            face_count=0,
            diagnostic=_invalid(
                parameter_error or bed_error or "invalid print-bed parameters",
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    bed_z = float(bed_z_mm)
    linear_tolerance = float(linear_tolerance_mm)
    area_tolerance = float(area_tolerance_mm2)
    angular_tolerance = float(angular_tolerance_deg)
    normalized = normalize_shapes(value)
    if not normalized.diagnostic.usable:
        return PrintBedContactMeasurement(
            area_mm2=None,
            width_mm=None,
            face_count=0,
            diagnostic=_diagnostic(
                normalized.diagnostic.status,
                normalized.diagnostic.message,
                tolerances=tolerances,
                failure_reason=normalized.diagnostic.failure_reason,
            ),
        )
    try:
        overall = _combine_bounds(normalized.shapes)
        if overall.min_z < bed_z - linear_tolerance:
            return PrintBedContactMeasurement(
                area_mm2=None,
                width_mm=None,
                face_count=0,
                diagnostic=_invalid(
                    f"geometry penetrates the bed: min Z={overall.min_z:.9g} mm, "
                    f"bed Z={bed_z:.9g} mm",
                    reason=FailureReason.MALFORMED_GEOMETRY,
                    tolerances=tolerances,
                ),
            )
        if overall.min_z > bed_z + linear_tolerance:
            return PrintBedContactMeasurement(
                area_mm2=0.0,
                width_mm=0.0,
                face_count=0,
                diagnostic=_diagnostic(
                    DiagnosticStatus.SUCCESS,
                    f"geometry is {overall.min_z - bed_z:.9g} mm above the bed",
                    tolerances=tolerances,
                ),
            )
        contact_faces: list[object] = []
        faces, _unsupported = _faces_from_shapes(normalized.shapes)
        for face in faces:
            bounds = _bounds(face)
            if (
                abs(bounds.min_z - bed_z) > linear_tolerance
                or abs(bounds.max_z - bed_z) > linear_tolerance
            ):
                continue
            normal = _plane_normal(face)
            if normal is None:
                continue
            z_component = abs(normal[2])
            angle = degrees(acos(max(-1.0, min(1.0, z_component))))
            if angle > angular_tolerance:
                continue
            if _number(getattr(face, "area"), "face area") > area_tolerance:
                contact_faces.append(face)
        if not contact_faces:
            return PrintBedContactMeasurement(
                area_mm2=0.0,
                width_mm=0.0,
                face_count=0,
                diagnostic=_diagnostic(
                    DiagnosticStatus.SUCCESS,
                    "the bed is touched only by non-planar or lower-dimensional "
                    "topology",
                    tolerances=tolerances,
                ),
            )
        area = sum(_number(getattr(face, "area"), "face area") for face in contact_faces)
        contact_bounds = _combine_bounds(contact_faces)
        width = min(
            contact_bounds.max_x - contact_bounds.min_x,
            contact_bounds.max_y - contact_bounds.min_y,
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return PrintBedContactMeasurement(
            area_mm2=None,
            width_mm=None,
            face_count=0,
            diagnostic=_invalid(
                f"cannot measure print-bed contact: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    return PrintBedContactMeasurement(
        area_mm2=area,
        width_mm=width,
        face_count=len(contact_faces),
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"{len(contact_faces)} planar contact face(s): area={area:.9g} mm2, "
            f"axis-aligned minimum footprint width={width:.9g} mm",
            tolerances=tolerances,
        ),
    )


def _same(left: object, right: object) -> bool:
    method = getattr(left, "is_same", None)
    if callable(method):
        return bool(method(right))
    return left is right


def _unique_shapes(shapes: Iterable[object]) -> list[object]:
    result: list[object] = []
    for shape in shapes:
        if not any(_same(shape, existing) for existing in result):
            result.append(shape)
    return result


def _entities(shapes: Iterable[object], singular: str, plural: str) -> list[object]:
    result: list[object] = []
    for shape in shapes:
        if _shape_type(shape) == singular:
            result.append(shape)
            continue
        getter = getattr(shape, plural, None)
        if callable(getter):
            result.extend(getter())
    return _unique_shapes(result)


def _edge_face_use_count(
    edge: object,
    face: object,
    candidates: tuple[object, ...],
) -> int:
    """Count a normal use once and a periodic seam use twice."""

    if not any(_same(edge, candidate) for candidate in candidates):
        return 0
    edge_wrapped = getattr(edge, "wrapped", None)
    face_wrapped = getattr(face, "wrapped", None)
    if edge_wrapped is None or face_wrapped is None:
        return 1

    # Lazy import preserves fake-object/native-boundary import safety.
    from OCP.BRep import BRep_Tool

    return 2 if BRep_Tool.IsClosed_s(edge_wrapped, face_wrapped) else 1


def summarize_topology(value: object) -> TopologySummary:
    """Count topology and classify edge-to-face adjacency."""

    normalized = normalize_shapes(value)
    if not normalized.diagnostic.usable:
        return TopologySummary(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            normalized.diagnostic,
        )
    try:
        solids = _entities(normalized.shapes, "Solid", "solids")
        shells = _entities(normalized.shapes, "Shell", "shells")
        faces = _entities(normalized.shapes, "Face", "faces")
        edges = _entities(normalized.shapes, "Edge", "edges")
        vertices = _entities(normalized.shapes, "Vertex", "vertices")
        face_edges = [
            (face, tuple(face.edges()))  # type: ignore[attr-defined]
            for face in faces
        ]
        adjacency = [
            sum(
                _edge_face_use_count(edge, face, candidates)
                for face, candidates in face_edges
            )
            for edge in edges
        ]
        boundary = sum(count == 1 for count in adjacency)
        manifold = sum(count == 2 for count in adjacency)
        non_manifold = sum(count not in {1, 2} for count in adjacency)
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return TopologySummary(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            _invalid(
                f"cannot summarize topology: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
            ),
        )
    return TopologySummary(
        shape_count=normalized.count,
        solid_count=len(solids),
        shell_count=len(shells),
        face_count=len(faces),
        edge_count=len(edges),
        vertex_count=len(vertices),
        boundary_edge_count=boundary,
        manifold_edge_count=manifold,
        non_manifold_edge_count=non_manifold,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"topology: solids={len(solids)}, shells={len(shells)}, "
            f"faces={len(faces)}, edges={len(edges)}, vertices={len(vertices)}, "
            f"boundary/manifold/non-manifold={boundary}/{manifold}/{non_manifold}",
        ),
    )


def _vector_tuple(vector: object, digits: int) -> tuple[float, float, float]:
    return tuple(
        round(_coord(vector, axis), digits)
        for axis in ("X", "Y", "Z")
    )  # type: ignore[return-value]


def _signature_key(signature: EdgeSignature) -> tuple[object, ...]:
    return (
        signature.geometry_type,
        signature.length_mm,
        tuple((sample.position_mm, sample.tangent) for sample in signature.samples),
    )


def sample_edge_signatures(
    value: object,
    *,
    sample_count: int = 5,
    linear_tolerance_mm: float = 1e-6,
    tangent_tolerance: float = 1e-6,
) -> EdgeSignatureMeasurement:
    """Create sorted, orientation-independent sampled signatures for edges."""

    tolerances, parameter_error = _validated_tolerances(
        ("linear", linear_tolerance_mm, Unit.MILLIMETER, True),
        ("tangent", tangent_tolerance, Unit.RATIO, True),
    )
    count_error = _validated_count("sample_count", sample_count, minimum=2)
    if parameter_error or count_error:
        return EdgeSignatureMeasurement(
            signatures=(),
            diagnostic=_invalid(
                parameter_error or count_error or "invalid signature parameters",
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    normalized = normalize_shapes(value)
    if not normalized.diagnostic.usable:
        return EdgeSignatureMeasurement(
            signatures=(),
            diagnostic=_diagnostic(
                normalized.diagnostic.status,
                normalized.diagnostic.message,
                tolerances=tolerances,
                failure_reason=normalized.diagnostic.failure_reason,
            ),
        )
    try:
        edges = _entities(normalized.shapes, "Edge", "edges")
        position_digits = max(
            0,
            min(12, ceil(-log10(float(linear_tolerance_mm))) + 1),
        )
        tangent_digits = max(
            0,
            min(12, ceil(-log10(float(tangent_tolerance))) + 1),
        )
        signatures: list[EdgeSignature] = []
        for edge in edges:
            geometry = getattr(edge, "geom_type")
            geometry = geometry() if callable(geometry) else geometry
            geometry_name = str(
                getattr(geometry, "name", getattr(geometry, "value", geometry))
            ).split(".")[-1]
            parameters = tuple(index / (sample_count - 1) for index in range(sample_count))
            forward = tuple(
                EdgeSample(
                    position_mm=_vector_tuple(
                        edge.position_at(parameter),
                        position_digits,
                    ),
                    tangent=_vector_tuple(
                        edge.tangent_at(parameter),
                        tangent_digits,
                    ),
                )
                for parameter in parameters
            )
            reverse = tuple(
                EdgeSample(
                    position_mm=sample.position_mm,
                    tangent=tuple(-value for value in sample.tangent),  # type: ignore[arg-type]
                )
                for sample in reversed(forward)
            )
            canonical = min(
                forward,
                reverse,
                key=lambda samples: tuple(
                    (sample.position_mm, sample.tangent) for sample in samples
                ),
            )
            signatures.append(
                EdgeSignature(
                    geometry_type=geometry_name,
                    length_mm=round(
                        _number(getattr(edge, "length"), "edge length"),
                        position_digits,
                    ),
                    samples=canonical,
                )
            )
        signatures.sort(key=_signature_key)
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return EdgeSignatureMeasurement(
            signatures=(),
            diagnostic=_invalid(
                f"cannot sample edge signatures: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    return EdgeSignatureMeasurement(
        signatures=tuple(signatures),
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"sampled {len(signatures)} edge(s) at {sample_count} positions",
            tolerances=tolerances,
        ),
    )


def _distance(left: object, right: object) -> float:
    difference = tuple(
        _coord(left, axis) - _coord(right, axis)
        for axis in ("X", "Y", "Z")
    )
    return sum(value * value for value in difference) ** 0.5


def _unit_vector(vector: object) -> tuple[float, float, float]:
    values = tuple(_coord(vector, axis) for axis in ("X", "Y", "Z"))
    length = sum(value * value for value in values) ** 0.5
    if length <= 1e-15:
        raise ValueError("zero-length direction")
    return tuple(value / length for value in values)  # type: ignore[return-value]


def _angle_change(left: object, right: object) -> float:
    left_unit = _unit_vector(left)
    right_unit = _unit_vector(right)
    dot = abs(sum(a * b for a, b in zip(left_unit, right_unit, strict=True)))
    return degrees(acos(max(-1.0, min(1.0, dot))))


def measure_edge_continuity(
    first: object,
    second: object,
    *,
    linear_tolerance_mm: float = 1e-6,
    angular_tolerance_deg: float = 1e-4,
) -> ContinuityMeasurement:
    """Measure endpoint gap and orientation-independent tangent change."""

    tolerances, parameter_error = _validated_tolerances(
        ("linear", linear_tolerance_mm, Unit.MILLIMETER, False),
        ("angular", angular_tolerance_deg, Unit.DEGREE, False),
    )
    if not parameter_error and float(angular_tolerance_deg) > 90:
        parameter_error = (
            f"angular tolerance must not exceed 90 degrees, got "
            f"{float(angular_tolerance_deg):g}"
        )
    if parameter_error:
        return ContinuityMeasurement(
            gap_mm=None,
            angle_change_deg=None,
            continuous=None,
            kind="edge_tangent",
            sample_count=1,
            diagnostic=_invalid(
                parameter_error,
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    linear_tolerance = float(linear_tolerance_mm)
    angular_tolerance = float(angular_tolerance_deg)
    try:
        if _shape_type(first) != "Edge" or _shape_type(second) != "Edge":
            raise ValueError("edge continuity requires two Edge objects")
        candidates = []
        for first_parameter in (0.0, 1.0):
            first_point = first.position_at(first_parameter)  # type: ignore[attr-defined]
            first_tangent = first.tangent_at(first_parameter)  # type: ignore[attr-defined]
            for second_parameter in (0.0, 1.0):
                second_point = second.position_at(second_parameter)  # type: ignore[attr-defined]
                second_tangent = second.tangent_at(second_parameter)  # type: ignore[attr-defined]
                candidates.append(
                    (
                        _distance(first_point, second_point),
                        _angle_change(first_tangent, second_tangent),
                    )
                )
        gap, angle = min(candidates, key=lambda item: (item[0], item[1]))
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ContinuityMeasurement(
            gap_mm=None,
            angle_change_deg=None,
            continuous=None,
            kind="edge_tangent",
            sample_count=1,
            diagnostic=_invalid(
                f"cannot measure edge continuity: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    continuous = gap <= linear_tolerance and angle <= angular_tolerance
    return ContinuityMeasurement(
        gap_mm=gap,
        angle_change_deg=angle,
        continuous=continuous,
        kind="edge_tangent",
        sample_count=1,
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"edge endpoint gap={gap:.9g} mm, tangent change={angle:.9g} deg",
            tolerances=tolerances,
        ),
    )


def measure_normal_change(
    first_face: object,
    second_face: object,
    shared_edge: object,
    *,
    sample_count: int = 3,
    linear_tolerance_mm: float = 1e-6,
    angular_tolerance_deg: float = 1e-4,
) -> ContinuityMeasurement:
    """Sample face gap and unoriented tangent-plane change along an edge."""

    tolerances, parameter_error = _validated_tolerances(
        ("linear", linear_tolerance_mm, Unit.MILLIMETER, False),
        ("angular", angular_tolerance_deg, Unit.DEGREE, False),
    )
    count_error = _validated_count("sample_count", sample_count, minimum=1)
    if not parameter_error and float(angular_tolerance_deg) > 90:
        parameter_error = (
            f"angular tolerance must not exceed 90 degrees, got "
            f"{float(angular_tolerance_deg):g}"
        )
    if parameter_error or count_error:
        return ContinuityMeasurement(
            None,
            None,
            None,
            "surface_normal",
            0,
            _invalid(
                parameter_error or count_error or "invalid normal-change parameters",
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    linear_tolerance = float(linear_tolerance_mm)
    angular_tolerance = float(angular_tolerance_deg)
    try:
        if (
            _shape_type(first_face) != "Face"
            or _shape_type(second_face) != "Face"
            or _shape_type(shared_edge) != "Edge"
        ):
            raise ValueError("normal change requires two Face objects and one Edge")
        gaps = []
        angles = []
        for index in range(sample_count):
            parameter = (index + 1) / (sample_count + 1)
            point = shared_edge.position_at(parameter)  # type: ignore[attr-defined]
            gaps.append(
                max(
                    _number(first_face.distance_to(point), "face-to-edge distance"),  # type: ignore[attr-defined]
                    _number(second_face.distance_to(point), "face-to-edge distance"),  # type: ignore[attr-defined]
                )
            )
            angles.append(
                _angle_change(
                    first_face.normal_at(point),  # type: ignore[attr-defined]
                    second_face.normal_at(point),  # type: ignore[attr-defined]
                )
            )
        gap = max(gaps)
        angle = max(angles)
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ContinuityMeasurement(
            None,
            None,
            None,
            "surface_normal",
            sample_count,
            _invalid(
                f"cannot measure surface normal change: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    continuous = gap <= linear_tolerance and angle <= angular_tolerance
    return ContinuityMeasurement(
        gap,
        angle,
        continuous,
        "surface_normal",
        sample_count,
        _diagnostic(
            DiagnosticStatus.SUCCESS,
            f"maximum sampled face gap={gap:.9g} mm, normal change={angle:.9g} deg",
            tolerances=tolerances,
        ),
    )


def _point_key(point: object) -> tuple[float, float, float]:
    return tuple(
        round(_coord(point, axis), 12)
        for axis in ("X", "Y", "Z")
    )  # type: ignore[return-value]


def _triangle_centroid(vertices: list[object], triangle: tuple[int, int, int]) -> object:
    points = [vertices[index] for index in triangle]
    coordinates = tuple(
        sum(_coord(point, axis) for point in points) / 3.0
        for axis in ("X", "Y", "Z")
    )
    return type(points[0])(*coordinates)


def _surface_samples(
    faces: Iterable[object],
    *,
    boundary_sample_count: int,
    sampling_tolerance_mm: float,
    sampling_angular_tolerance_deg: float,
) -> list[object]:
    """Sample only points on topological trims, boundaries, and mesh interiors."""

    samples: list[object] = []
    boundary_parameters = tuple(
        index / boundary_sample_count
        for index in range(boundary_sample_count + 1)
    )
    for face in faces:
        vertices, triangles = face.tessellate(  # type: ignore[attr-defined]
            sampling_tolerance_mm,
            radians(sampling_angular_tolerance_deg),
        )
        samples.extend(vertices)
        closest_points = getattr(face, "closest_points")
        for triangle in triangles:
            centroid = _triangle_centroid(vertices, triangle)
            samples.append(closest_points(centroid)[0])
        for edge in face.edges():  # type: ignore[attr-defined]
            samples.extend(
                edge.position_at(parameter)  # type: ignore[attr-defined]
                for parameter in boundary_parameters
            )
    unique = {_point_key(point): point for point in samples}
    return [unique[key] for key in sorted(unique)]


def _directed_surface_distance(
    source_samples: Iterable[object],
    target_faces: tuple[object, ...],
) -> float:
    distances = [
        min(
            _number(face.distance_to(point), "surface sample distance")  # type: ignore[attr-defined]
            for face in target_faces
        )
        for point in source_samples
    ]
    return max(distances, default=0.0)


def compare_protected_surfaces(
    reference: object,
    candidate: object,
    *,
    sample_grid: int = 2,
    linear_tolerance_mm: float = 1e-6,
    area_tolerance_mm2: float = 1e-6,
    sampling_tolerance_mm: float = 0.1,
    sampling_angular_tolerance_deg: float = 5.0,
) -> ProtectedSurfaceComparison:
    """Compare trimmed topological surface sets in both directions."""

    tolerances, parameter_error = _validated_tolerances(
        ("linear", linear_tolerance_mm, Unit.MILLIMETER, False),
        ("area", area_tolerance_mm2, Unit.SQUARE_MILLIMETER, False),
        (
            "sampling",
            sampling_tolerance_mm,
            Unit.MILLIMETER,
            True,
        ),
        (
            "sampling_angular",
            sampling_angular_tolerance_deg,
            Unit.DEGREE,
            True,
        ),
    )
    count_error = _validated_count("sample_grid", sample_grid, minimum=1)
    if (
        not parameter_error
        and float(sampling_angular_tolerance_deg) > 180
    ):
        parameter_error = (
            f"sampling angular tolerance must not exceed 180 degrees, got "
            f"{float(sampling_angular_tolerance_deg):g}"
        )
    if parameter_error or count_error:
        return ProtectedSurfaceComparison(
            None,
            None,
            None,
            None,
            0,
            0,
            _invalid(
                parameter_error or count_error or "invalid surface parameters",
                reason=FailureReason.UNSUPPORTED_INPUT,
                tolerances=tolerances,
            ),
        )
    reference_shapes = normalize_shapes(reference)
    candidate_shapes = normalize_shapes(candidate)
    if (
        reference_shapes.diagnostic.status is DiagnosticStatus.EMPTY
        and candidate_shapes.diagnostic.status is DiagnosticStatus.EMPTY
    ):
        return ProtectedSurfaceComparison(
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            _diagnostic(
                DiagnosticStatus.SUCCESS,
                "both protected surface sets are explicitly empty",
                tolerances=tolerances,
            ),
        )
    for label, normalized in (
        ("reference", reference_shapes),
        ("candidate", candidate_shapes),
    ):
        if not normalized.diagnostic.usable:
            return ProtectedSurfaceComparison(
                None,
                None,
                None,
                None,
                0,
                0,
                _diagnostic(
                    normalized.diagnostic.status,
                    f"{label} surface set is unusable: "
                    f"{normalized.diagnostic.message}",
                    tolerances=tolerances,
                    failure_reason=normalized.diagnostic.failure_reason,
                ),
            )
    try:
        reference_faces, reference_unsupported = _faces_from_shapes(
            reference_shapes.shapes
        )
        candidate_faces, candidate_unsupported = _faces_from_shapes(
            candidate_shapes.shapes
        )
        if reference_unsupported or candidate_unsupported:
            details = []
            if reference_unsupported:
                details.append(
                    "reference=" + ",".join(reference_unsupported)
                )
            if candidate_unsupported:
                details.append(
                    "candidate=" + ",".join(candidate_unsupported)
                )
            return ProtectedSurfaceComparison(
                None,
                None,
                None,
                None,
                0,
                0,
                _invalid(
                    "protected-surface comparison received unsupported "
                    "topology: " + "; ".join(details),
                    reason=FailureReason.INVALID_TOPOLOGY,
                    tolerances=tolerances,
                ),
            )
        if not reference_faces or not candidate_faces:
            missing = "reference" if not reference_faces else "candidate"
            return ProtectedSurfaceComparison(
                None,
                None,
                None,
                None,
                0,
                0,
                _diagnostic(
                    DiagnosticStatus.EMPTY,
                    f"{missing} contains no protected faces",
                    tolerances=tolerances,
                    failure_reason=FailureReason.EMPTY_SHAPE,
                ),
            )
        reference_samples = _surface_samples(
            reference_faces,
            boundary_sample_count=sample_grid,
            sampling_tolerance_mm=float(sampling_tolerance_mm),
            sampling_angular_tolerance_deg=float(
                sampling_angular_tolerance_deg
            ),
        )
        candidate_samples = _surface_samples(
            candidate_faces,
            boundary_sample_count=sample_grid,
            sampling_tolerance_mm=float(sampling_tolerance_mm),
            sampling_angular_tolerance_deg=float(
                sampling_angular_tolerance_deg
            ),
        )
        reference_area = sum(
            _number(getattr(face, "area"), "face area")
            for face in reference_faces
        )
        candidate_area = sum(
            _number(getattr(face, "area"), "face area")
            for face in candidate_faces
        )
        forward = _directed_surface_distance(
            reference_samples,
            candidate_faces,
        )
        reverse = _directed_surface_distance(
            candidate_samples,
            reference_faces,
        )
    except (AssertionError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return ProtectedSurfaceComparison(
            None,
            None,
            None,
            None,
            0,
            0,
            _invalid(
                f"cannot compare protected surfaces: {type(exc).__name__}: {exc}",
                reason=FailureReason.MALFORMED_GEOMETRY,
                tolerances=tolerances,
            ),
        )
    return ProtectedSurfaceComparison(
        reference_area_mm2=reference_area,
        candidate_area_mm2=candidate_area,
        reference_to_candidate_max_mm=forward,
        candidate_to_reference_max_mm=reverse,
        reference_sample_count=len(reference_samples),
        candidate_sample_count=len(candidate_samples),
        diagnostic=_diagnostic(
            DiagnosticStatus.SUCCESS,
            f"bidirectional sampled surface distances: reference->candidate="
            f"{forward:.9g} mm, candidate->reference={reverse:.9g} mm; "
            f"areas={reference_area:.9g}/{candidate_area:.9g} mm2",
            tolerances=tolerances,
        ),
    )
