from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys

import pytest

from cad_geometry_checks import (
    BooleanOutcome,
    DiagnosticStatus,
    FailureReason,
)
from cad_geometry_checks.native import (
    compare_protected_material,
    compare_protected_surfaces,
    measure_difference,
    measure_edge_continuity,
    measure_intersection,
    measure_normal_change,
    measure_print_bed_contact,
    measure_volume,
    normalize_shapes,
    normalize_solids,
    sample_edge_signatures,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeVector:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.X = x
        self.Y = y
        self.Z = z


class FakeBounds:
    def __init__(
        self,
        minimum: tuple[float, float, float],
        maximum: tuple[float, float, float],
    ) -> None:
        self.min = FakeVector(*minimum)
        self.max = FakeVector(*maximum)


class FakeShape:
    shape_type = "Solid"
    is_valid = True

    def __init__(
        self,
        *,
        volume: float = 1.0,
        minimum: tuple[float, float, float] = (0.0, 0.0, 0.0),
        maximum: tuple[float, float, float] = (1.0, 1.0, 1.0),
        valid: bool = True,
    ) -> None:
        self.volume = volume
        self._bounds = FakeBounds(minimum, maximum)
        self.is_valid = valid

    def __bool__(self) -> bool:
        return True

    def bounding_box(self) -> FakeBounds:
        return self._bounds


class FakeFace(FakeShape):
    shape_type = "Face"
    volume = 0.0


class FakeWire(FakeShape):
    shape_type = "Wire"
    volume = 0.0


class FakeCompound:
    shape_type = "Compound"
    is_valid = True

    def __init__(self, children: list[object]) -> None:
        self.children = children

    def __bool__(self) -> bool:
        return True

    def get_top_level_shapes(self) -> list[object]:
        return self.children


def test_public_import_is_native_free_and_does_not_cross_native_boundary() -> None:
    program = (
        "import sys; import cad_geometry_checks; "
        "forbidden=('build123d','OCP','cad_runner'); "
        "loaded=[n for n in sys.modules if n.split('.')[0] in forbidden]; "
        "assert not loaded, loaded; "
        "assert 'cad_geometry_checks.native' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_native_boundary_and_fake_measurements_do_not_load_cad_libraries() -> None:
    forbidden = {"build123d", "OCP", "cadquery"}

    assert not {
        name for name in sys.modules if name.split(".")[0] in forbidden
    }
    assert measure_volume(FakeShape()).value == pytest.approx(1.0)
    assert not {
        name for name in sys.modules if name.split(".")[0] in forbidden
    }


def test_shape_and_solid_normalization_are_explicit_for_all_input_classes() -> None:
    first = FakeShape(volume=2.0)
    second = FakeShape(volume=3.0)

    none_result = normalize_shapes(None)
    assert none_result.diagnostic.status is DiagnosticStatus.INDETERMINATE
    assert none_result.diagnostic.failure_reason is FailureReason.NO_RETURNED_SHAPE

    single = normalize_solids(first)
    listed = normalize_solids([first, second])
    compound = normalize_solids(FakeCompound([first, second]))
    empty = normalize_solids(FakeCompound([]))

    assert single.solids == (first,)
    assert listed.solids == (first, second)
    assert compound.solids == (first, second)
    assert empty.diagnostic.status is DiagnosticStatus.EMPTY
    assert empty.diagnostic.failure_reason is FailureReason.EMPTY_SHAPE

    generated = normalize_solids(item for item in (first, second))
    assert generated.input_count == 2
    assert generated.solids == (first, second)


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        ("not geometry", FailureReason.UNSUPPORTED_INPUT),
        (FakeShape(valid=False), FailureReason.INVALID_TOPOLOGY),
        (FakeFace(), FailureReason.INVALID_TOPOLOGY),
    ),
)
def test_malformed_or_unsupported_inputs_return_actionable_diagnostics(
    value: object,
    reason: FailureReason,
) -> None:
    result = normalize_solids(value)

    assert result.solids == ()
    assert result.diagnostic.status is DiagnosticStatus.INVALID
    assert result.diagnostic.failure_reason is reason
    assert result.diagnostic.message


def test_intersection_rejects_disjoint_bounds_before_boolean_call() -> None:
    calls = 0

    def forbidden_operation(_left: object, _right: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("Boolean must not run")

    result = measure_intersection(
        FakeShape(maximum=(1.0, 1.0, 1.0)),
        FakeShape(minimum=(2.0, 0.0, 0.0), maximum=(3.0, 1.0, 1.0)),
        operation=forbidden_operation,
    )

    assert calls == 0
    assert result.outcome is BooleanOutcome.BOUNDING_BOX_DISJOINT
    assert result.volume_mm3 == 0.0
    assert result.diagnostic.status is DiagnosticStatus.SHORT_CIRCUITED


def test_boolean_outcomes_do_not_collapse_missing_empty_contact_and_volume() -> None:
    left = FakeShape()
    right = FakeShape()
    missing = measure_intersection(left, right, operation=lambda _a, _b: None)
    empty = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: FakeCompound([]),
    )
    touching = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: FakeFace(),
    )
    overlap = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: FakeShape(volume=0.25),
    )
    unexpected = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: FakeWire(),
    )

    assert (missing.outcome, missing.volume_mm3) == (
        BooleanOutcome.NO_RETURNED_SHAPE,
        None,
    )
    assert (empty.outcome, empty.volume_mm3) == (
        BooleanOutcome.EMPTY_SHAPE,
        None,
    )
    assert (touching.outcome, touching.volume_mm3) == (
        BooleanOutcome.ZERO_VOLUME_CONTACT,
        0.0,
    )
    assert (overlap.outcome, overlap.volume_mm3) == (
        BooleanOutcome.POSITIVE_VOLUME,
        pytest.approx(0.25),
    )
    assert unexpected.outcome is BooleanOutcome.INVALID_OR_UNEXPECTED_TOPOLOGY
    assert unexpected.diagnostic.failure_reason is FailureReason.INVALID_TOPOLOGY


def test_mixed_multisolid_boolean_results_fail_closed() -> None:
    left = [FakeShape(), FakeShape()]
    right = FakeShape()
    positive = FakeShape(volume=0.25)
    responses = iter((None, positive))
    mixed_positive = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: next(responses),
    )
    empty_responses = iter((None, FakeCompound([])))
    mixed_empty = measure_intersection(
        left,
        right,
        operation=lambda _a, _b: next(empty_responses),
    )

    assert mixed_positive.outcome is BooleanOutcome.NO_RETURNED_SHAPE
    assert mixed_positive.volume_mm3 is None
    assert mixed_positive.diagnostic.status is DiagnosticStatus.INDETERMINATE
    assert mixed_empty.outcome is BooleanOutcome.NO_RETURNED_SHAPE
    assert mixed_empty.volume_mm3 is None


def test_difference_uses_bounding_box_rejection_and_reports_failures() -> None:
    left = FakeShape(volume=4.0, maximum=(1.0, 1.0, 1.0))
    right = FakeShape(
        minimum=(2.0, 0.0, 0.0),
        maximum=(3.0, 1.0, 1.0),
    )

    disjoint = measure_difference(
        left,
        right,
        operation=lambda _a, _b: (_ for _ in ()).throw(
            AssertionError("cut must not run")
        ),
    )
    missing = measure_difference(left, FakeShape(), operation=lambda _a, _b: None)

    assert disjoint.value == pytest.approx(4.0)
    assert disjoint.diagnostic.status is DiagnosticStatus.SHORT_CIRCUITED
    assert missing.value is None
    assert missing.diagnostic.failure_reason is FailureReason.NO_RETURNED_SHAPE


def test_results_are_immutable_and_verification_bridge_rejects_unusable_data() -> None:
    measured = measure_volume(FakeShape(volume=2.5))
    missing = measure_volume(None)

    assert measured.as_verification_measurement().actual.value == pytest.approx(2.5)
    with pytest.raises(ValueError, match="cannot feed cad_verification"):
        missing.as_verification_measurement()
    with pytest.raises(FrozenInstanceError):
        measured.value = 4.0  # type: ignore[misc]


def test_invalid_sampling_parameters_return_a_result_instead_of_type_error() -> None:
    result = sample_edge_signatures(FakeShape(), sample_count=1)

    assert result.signatures == ()
    assert result.diagnostic.status is DiagnosticStatus.INVALID
    assert result.diagnostic.failure_reason is FailureReason.UNSUPPORTED_INPUT


def test_duplicate_collection_material_is_measured_once() -> None:
    solid = FakeShape(volume=3.0)
    intersection = FakeShape(volume=1.5)

    volume = measure_volume([solid, solid])
    overlap = measure_intersection(
        [solid, solid],
        solid,
        operation=lambda _left, _right: intersection,
    )

    assert volume.value == pytest.approx(3.0)
    assert overlap.volume_mm3 == pytest.approx(1.5)


@pytest.mark.parametrize(
    "call",
    (
        lambda shape: measure_volume(shape, tolerance_mm3=-1.0),
        lambda shape: measure_intersection(
            shape,
            shape,
            bounding_box_tolerance_mm=float("nan"),
        ),
        lambda shape: measure_difference(
            shape,
            shape,
            volume_tolerance_mm3=None,  # type: ignore[arg-type]
        ),
        lambda shape: compare_protected_material(
            shape,
            shape,
            bounding_box_tolerance_mm="bad",  # type: ignore[arg-type]
        ),
        lambda shape: measure_print_bed_contact(
            shape,
            linear_tolerance_mm=-1.0,
        ),
        lambda shape: sample_edge_signatures(
            shape,
            sample_count="five",  # type: ignore[arg-type]
        ),
        lambda shape: measure_edge_continuity(
            shape,
            shape,
            angular_tolerance_deg=float("inf"),
        ),
        lambda shape: measure_normal_change(
            shape,
            shape,
            shape,
            sample_count=None,  # type: ignore[arg-type]
        ),
        lambda shape: compare_protected_surfaces(
            shape,
            shape,
            sampling_tolerance_mm=0.0,
        ),
    ),
)
def test_invalid_public_parameters_return_diagnostics(call) -> None:
    result = call(FakeShape())

    assert result.diagnostic.status is DiagnosticStatus.INVALID
    assert result.diagnostic.failure_reason is FailureReason.UNSUPPORTED_INPUT
    assert result.diagnostic.message


@pytest.mark.parametrize(
    "reference",
    (
        FakeWire(),
        [FakeFace(), FakeWire()],
    ),
)
def test_protected_surfaces_reject_unsupported_or_mixed_topology(
    reference: object,
) -> None:
    result = compare_protected_surfaces(reference, FakeFace())

    assert result.diagnostic.status is DiagnosticStatus.INVALID
    assert result.diagnostic.failure_reason is FailureReason.INVALID_TOPOLOGY
    assert "unsupported topology" in result.diagnostic.message
