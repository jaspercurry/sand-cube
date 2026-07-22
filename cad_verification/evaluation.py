"""Pure requirement evaluation and profile aggregation."""

from __future__ import annotations

from math import isclose
from typing import Iterable

from .model import (
    ActualValue,
    DesignContract,
    Requirement,
    RequirementResult,
)
from .policy import (
    EvidenceChannel,
    ExpectationKind,
    ResultStatus,
    VerificationProfile,
    included_costs,
)


def requirements_for_profile(
    contract: DesignContract,
    profile: VerificationProfile,
) -> tuple[Requirement, ...]:
    """Compose a profile from requirement cost layers."""

    costs = included_costs(profile)
    return tuple(
        requirement
        for requirement in contract.requirements
        if requirement.cost_profile in costs
    )


def actual_satisfies(requirement: Requirement, actual: ActualValue) -> bool:
    """Compare one actual value with the contract expectation."""

    if actual.unit is not requirement.unit:
        return False

    expectation = requirement.expectation
    tolerance = requirement.tolerance.absolute
    if expectation.kind is ExpectationKind.EXACT:
        expected = expectation.exact
        if (
            isinstance(expected, (int, float))
            and not isinstance(expected, bool)
            and isinstance(actual.value, (int, float))
            and not isinstance(actual.value, bool)
        ):
            return isclose(
                float(actual.value),
                float(expected),
                rel_tol=0.0,
                abs_tol=tolerance,
            )
        return actual.value == expected

    if not isinstance(actual.value, (int, float)) or isinstance(
        actual.value, bool
    ):
        return False
    assert expectation.minimum is not None
    assert expectation.maximum is not None
    return (
        expectation.minimum - tolerance
        <= float(actual.value)
        <= expectation.maximum + tolerance
    )


def assess(
    requirement: Requirement,
    actual: ActualValue,
    *,
    evidence_channel: EvidenceChannel,
    diagnostic: str,
    evidence_refs: tuple[str, ...] = (),
) -> RequirementResult:
    """Create a PASS/FAIL result without executing the underlying check."""

    status = (
        ResultStatus.PASS
        if actual_satisfies(requirement, actual)
        else ResultStatus.FAIL
    )
    return RequirementResult(
        requirement_id=requirement.requirement_id,
        status=status,
        actual=actual,
        evidence_channel=evidence_channel,
        diagnostic=diagnostic,
        evidence_refs=evidence_refs,
    )


def unverified(requirement_id: str, diagnostic: str) -> RequirementResult:
    """Represent absence or insufficiency of evidence explicitly."""

    return RequirementResult(
        requirement_id=requirement_id,
        status=ResultStatus.UNVERIFIED,
        actual=None,
        evidence_channel=EvidenceChannel.NONE,
        diagnostic=diagnostic,
    )


def aggregate_status(
    results: Iterable[RequirementResult],
    *,
    missing_requirements: bool = False,
) -> ResultStatus:
    """FAIL dominates; missing or UNVERIFIED evidence can never pass."""

    statuses = tuple(result.status for result in results)
    if ResultStatus.FAIL in statuses:
        return ResultStatus.FAIL
    if (
        missing_requirements
        or not statuses
        or ResultStatus.UNVERIFIED in statuses
    ):
        return ResultStatus.UNVERIFIED
    return ResultStatus.PASS


def profile_status(
    contract: DesignContract,
    profile: VerificationProfile,
    results: Iterable[RequirementResult],
) -> ResultStatus:
    """Aggregate exactly the requirements composed into ``profile``."""

    expected_ids = {
        requirement.requirement_id
        for requirement in requirements_for_profile(contract, profile)
    }
    selected = tuple(
        result for result in results if result.requirement_id in expected_ids
    )
    observed_ids = {result.requirement_id for result in selected}
    return aggregate_status(
        selected,
        missing_requirements=observed_ids != expected_ids,
    )
