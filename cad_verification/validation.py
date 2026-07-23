"""Semantic validation for contracts and review packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
import re
from typing import Iterable

from .evaluation import actual_satisfies, requirements_for_profile
from .model import (
    ActualValue,
    ArtifactEvidence,
    ArtifactReference,
    DesignContract,
    Fingerprint,
    ModelIdentity,
    ReviewPacket,
    SCHEMA_VERSION,
    VisualEvidenceReference,
)
from .policy import (
    ARTIFACT_POLICIES,
    CHECK_POLICIES,
    EVIDENCE_POLICIES,
    PROFILE_POLICIES,
    ArtifactRole,
    CheckKind,
    EvidenceChannel,
    ExpectationKind,
    ResultStatus,
    Unit,
    VerificationProfile,
    profile_rank,
)
from .protocols import ArtifactProbe


_REQUIREMENT_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
_STABLE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
_ADAPTER_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
_PARAMETER_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message} [{self.code}]"


class VerificationValidationError(ValueError):
    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(issues)
        summary = "\n".join(str(issue) for issue in self.issues)
        super().__init__(summary)


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code, path, message))


def _nonempty(
    value: object,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> bool:
    if not isinstance(value, str) or not value.strip():
        _issue(issues, "value.empty", path, "must be a non-empty string")
        return False
    return True


def _stable_id(
    value: object,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(value, str) or not _STABLE_ID.fullmatch(value):
        _issue(
            issues,
            "id.invalid",
            path,
            "must be a stable lowercase dotted, dashed, or underscored ID",
        )


def _valid_datetime(
    value: object,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> bool:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _issue(
            issues,
            "datetime.invalid",
            path,
            "must be a timezone-aware datetime",
        )
        return False
    return True


def _valid_sha(
    value: object,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> bool:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        _issue(issues, "sha256.invalid", path, "must be lowercase SHA-256 hex")
        return False
    return True


def _validate_model(
    model: ModelIdentity,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    _stable_id(model.model_id, path=f"{path}.model_id", issues=issues)
    for field_name in ("name", "variant", "source", "entrypoint"):
        _nonempty(
            getattr(model, field_name),
            path=f"{path}.{field_name}",
            issues=issues,
        )


def _validate_fingerprints(
    records: tuple[Fingerprint, ...],
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not records:
        _issue(issues, "fingerprints.empty", path, "must not be empty")
        return
    seen: set[str] = set()
    for index, record in enumerate(records):
        item_path = f"{path}[{index}]"
        if _nonempty(record.subject, path=f"{item_path}.subject", issues=issues):
            if record.subject in seen:
                _issue(
                    issues,
                    "fingerprint.duplicate_subject",
                    f"{item_path}.subject",
                    f"duplicate subject {record.subject!r}",
                )
            seen.add(record.subject)
        _valid_sha(record.sha256, path=f"{item_path}.sha256", issues=issues)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_actual(
    actual: ActualValue,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(actual.unit, Unit):
        _issue(issues, "unit.invalid", f"{path}.unit", "must be a Unit")
        return
    value = actual.value
    if not isinstance(value, (bool, int, float, str)):
        _issue(
            issues,
            "actual.invalid",
            f"{path}.value",
            "must be a JSON scalar",
        )
        return
    if isinstance(value, float) and not isfinite(value):
        _issue(issues, "actual.nonfinite", f"{path}.value", "must be finite")
    if isinstance(value, bool) and actual.unit is not Unit.BOOLEAN:
        _issue(
            issues,
            "unit.mismatch",
            f"{path}.unit",
            "boolean values require the boolean unit",
        )
    if isinstance(value, str) and actual.unit is not Unit.NONE:
        _issue(
            issues,
            "unit.mismatch",
            f"{path}.unit",
            "string values require the none unit",
        )
    if _is_number(value) and actual.unit in (Unit.BOOLEAN, Unit.NONE):
        _issue(
            issues,
            "unit.mismatch",
            f"{path}.unit",
            "numeric values require a numeric unit",
        )
    if actual.unit is Unit.COUNT and (
        not _is_number(value) or float(value) != int(value)
    ):
        _issue(
            issues,
            "unit.count",
            f"{path}.value",
            "count values must be integral",
        )


def validate_contract(contract: DesignContract) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if contract.schema_version != SCHEMA_VERSION:
        _issue(
            issues,
            "schema.unsupported",
            "schema_version",
            f"expected {SCHEMA_VERSION}",
        )
    _stable_id(contract.contract_id, path="contract_id", issues=issues)
    _nonempty(contract.title, path="title", issues=issues)
    _validate_model(contract.model, path="model", issues=issues)
    if not contract.requirements:
        _issue(
            issues,
            "requirements.empty",
            "requirements",
            "contract must contain requirements",
        )

    seen_ids: set[str] = set()
    for index, requirement in enumerate(contract.requirements):
        path = f"requirements[{index}]"
        requirement_id = requirement.requirement_id
        if not isinstance(requirement_id, str) or not _REQUIREMENT_ID.fullmatch(
            requirement_id
        ):
            _issue(
                issues,
                "requirement.id_invalid",
                f"{path}.requirement_id",
                "must use a stable uppercase ID such as CAD-FIT-001",
            )
        elif requirement_id in seen_ids:
            _issue(
                issues,
                "requirement.duplicate_id",
                f"{path}.requirement_id",
                f"duplicate requirement ID {requirement_id}",
            )
        seen_ids.add(requirement_id)
        _nonempty(
            requirement.description,
            path=f"{path}.description",
            issues=issues,
        )

        check = requirement.check
        if not isinstance(check.kind, CheckKind):
            _issue(
                issues,
                "check.kind_invalid",
                f"{path}.check.kind",
                "must be a CheckKind",
            )
            check_policy = None
        else:
            check_policy = CHECK_POLICIES[check.kind]
        if not isinstance(check.adapter, str) or not _ADAPTER_ID.fullmatch(
            check.adapter
        ):
            _issue(
                issues,
                "check.adapter_invalid",
                f"{path}.check.adapter",
                "must be a stable namespaced adapter ID",
            )
        parameter_names: set[str] = set()
        for parameter_index, parameter in enumerate(check.parameters):
            parameter_path = f"{path}.check.parameters[{parameter_index}]"
            if not isinstance(parameter, tuple) or len(parameter) != 2:
                _issue(
                    issues,
                    "check.parameter_invalid",
                    parameter_path,
                    "must be a (name, scalar) pair",
                )
                continue
            name, value = parameter
            if not isinstance(name, str) or not _PARAMETER_NAME.fullmatch(name):
                _issue(
                    issues,
                    "check.parameter_name_invalid",
                    f"{parameter_path}[0]",
                    "must be a lowercase identifier",
                )
            elif name in parameter_names:
                _issue(
                    issues,
                    "check.parameter_duplicate",
                    f"{parameter_path}[0]",
                    f"duplicate parameter {name!r}",
                )
            parameter_names.add(name)
            if not isinstance(value, (bool, int, float, str)):
                _issue(
                    issues,
                    "check.parameter_value_invalid",
                    f"{parameter_path}[1]",
                    "must be a JSON scalar",
                )
            elif isinstance(value, float) and not isfinite(value):
                _issue(
                    issues,
                    "check.parameter_nonfinite",
                    f"{parameter_path}[1]",
                    "must be finite",
                )

        expectation = requirement.expectation
        if not isinstance(expectation.kind, ExpectationKind):
            _issue(
                issues,
                "expectation.kind_invalid",
                f"{path}.expectation.kind",
                "must be an ExpectationKind",
            )
        elif expectation.kind is ExpectationKind.EXACT:
            if expectation.exact is None:
                _issue(
                    issues,
                    "expectation.exact_missing",
                    f"{path}.expectation.exact",
                    "exact expectations require a value",
                )
            if expectation.minimum is not None or expectation.maximum is not None:
                _issue(
                    issues,
                    "expectation.exact_has_range",
                    f"{path}.expectation",
                    "exact expectations cannot also define a range",
                )
        elif expectation.kind is ExpectationKind.RANGE:
            if expectation.exact is not None:
                _issue(
                    issues,
                    "expectation.range_has_exact",
                    f"{path}.expectation.exact",
                    "range expectations cannot also define exact",
                )
            if not _is_number(expectation.minimum) or not _is_number(
                expectation.maximum
            ):
                _issue(
                    issues,
                    "expectation.range_invalid",
                    f"{path}.expectation",
                    "range bounds must be numeric",
                )
            elif (
                not isfinite(float(expectation.minimum))
                or not isfinite(float(expectation.maximum))
                or expectation.minimum > expectation.maximum
            ):
                _issue(
                    issues,
                    "expectation.range_invalid",
                    f"{path}.expectation",
                    "range bounds must be finite and ordered",
                )

        if not isinstance(requirement.unit, Unit):
            _issue(
                issues,
                "unit.invalid",
                f"{path}.unit",
                "must be a Unit",
            )
        elif (
            expectation.kind is ExpectationKind.EXACT
            and expectation.exact is not None
        ):
            _validate_actual(
                ActualValue(expectation.exact, requirement.unit),
                path=f"{path}.expectation.exact",
                issues=issues,
            )
        elif expectation.kind is ExpectationKind.RANGE and requirement.unit in (
            Unit.NONE,
            Unit.BOOLEAN,
        ):
            _issue(
                issues,
                "unit.range_invalid",
                f"{path}.unit",
                "range expectations require a numeric unit",
            )

        tolerance = requirement.tolerance.absolute
        if not _is_number(tolerance) or not isfinite(float(tolerance)) or tolerance < 0:
            _issue(
                issues,
                "tolerance.invalid",
                f"{path}.tolerance.absolute",
                "must be a finite non-negative number",
            )
        elif (
            expectation.kind is ExpectationKind.EXACT
            and expectation.exact is not None
            and not _is_number(expectation.exact)
            and tolerance != 0
        ):
            _issue(
                issues,
                "tolerance.nonnumeric",
                f"{path}.tolerance.absolute",
                "non-numeric exact values require zero tolerance",
            )

        if not isinstance(requirement.cost_profile, VerificationProfile):
            _issue(
                issues,
                "profile.invalid",
                f"{path}.cost_profile",
                "must be a VerificationProfile",
            )
        elif check_policy is not None and profile_rank(
            requirement.cost_profile
        ) < profile_rank(check_policy.minimum_profile):
            _issue(
                issues,
                "profile.underpriced_check",
                f"{path}.cost_profile",
                f"{check.kind.value} requires at least "
                f"{check_policy.minimum_profile.value}",
            )

    for profile in VerificationProfile:
        profile_policy = PROFILE_POLICIES[profile]
        layer = tuple(
            requirement
            for requirement in contract.requirements
            if requirement.cost_profile is profile
        )
        if not layer:
            _issue(
                issues,
                "profile.empty",
                f"profiles.{profile.value}",
                "profile cost layer must contain at least one requirement",
            )
        else:
            meaningful = tuple(
                requirement
                for requirement in layer
                if isinstance(requirement.check.kind, CheckKind)
                and CHECK_POLICIES[requirement.check.kind].minimum_profile
                is profile
            )
            if not meaningful:
                _issue(
                    issues,
                    "profile.vacuous",
                    f"profiles.{profile.value}",
                    "profile must add a check native to its cost tier",
                )
        layer_kinds = {
            requirement.check.kind
            for requirement in layer
            if isinstance(requirement.check.kind, CheckKind)
        }
        for required_kind in profile_policy.required_check_kinds:
            if required_kind in layer_kinds:
                continue
            _issue(
                issues,
                "profile.required_check_missing",
                f"profiles.{profile.value}",
                f"profile requires a {required_kind.value} requirement",
            )

    return tuple(issues)


def assert_valid_contract(contract: DesignContract) -> None:
    issues = validate_contract(contract)
    if issues:
        raise VerificationValidationError(issues)


def _validate_artifact_reference(
    reference: object,
    artifacts_by_id: dict[str, ArtifactEvidence],
    *,
    path: str,
    issues: list[ValidationIssue],
) -> ArtifactEvidence | None:
    if not isinstance(reference, ArtifactReference):
        _issue(
            issues,
            "evidence.artifact_reference_invalid",
            path,
            "must be an ArtifactReference",
        )
        return None
    _stable_id(reference.artifact_id, path=f"{path}.artifact_id", issues=issues)
    _valid_sha(reference.sha256, path=f"{path}.sha256", issues=issues)
    if not isinstance(reference.role, ArtifactRole):
        _issue(
            issues,
            "artifact.role_invalid",
            f"{path}.role",
            "must be an ArtifactRole",
        )
        return None
    artifact = artifacts_by_id.get(reference.artifact_id)
    if artifact is None:
        _issue(
            issues,
            "evidence.artifact_unknown",
            f"{path}.artifact_id",
            "does not reference a packet artifact",
        )
        return None
    if reference.sha256 != artifact.sha256:
        _issue(
            issues,
            "evidence.artifact_hash_mismatch",
            f"{path}.sha256",
            "does not match the referenced artifact hash",
        )
    if reference.role is not artifact.role:
        _issue(
            issues,
            "evidence.artifact_role_mismatch",
            f"{path}.role",
            "does not match the referenced artifact role",
        )
    return artifact


def validate_review_packet(
    packet: ReviewPacket,
    contract: DesignContract,
    *,
    artifact_probe: ArtifactProbe | None = None,
) -> tuple[ValidationIssue, ...]:
    from .serialization import (
        contract_fingerprint,
        fingerprint_collection,
    )

    issues: list[ValidationIssue] = []
    if packet.schema_version != SCHEMA_VERSION:
        _issue(
            issues,
            "schema.unsupported",
            "schema_version",
            f"expected {SCHEMA_VERSION}",
        )
    _stable_id(packet.packet_id, path="packet_id", issues=issues)
    if packet.contract_id != contract.contract_id:
        _issue(
            issues,
            "packet.contract_mismatch",
            "contract_id",
            "does not match the supplied contract",
        )
    expected_contract_fingerprint = contract_fingerprint(contract)
    if packet.contract_fingerprint != expected_contract_fingerprint:
        _issue(
            issues,
            "artifact.stale_contract",
            "contract_fingerprint",
            "does not match the current contract",
        )
    if packet.model != contract.model:
        _issue(
            issues,
            "packet.model_mismatch",
            "model",
            "does not match the contract model identity",
        )
    _validate_model(packet.model, path="model", issues=issues)
    if not isinstance(packet.profile, VerificationProfile):
        _issue(issues, "profile.invalid", "profile", "must be a profile")
        selected_requirements = ()
    else:
        selected_requirements = requirements_for_profile(contract, packet.profile)

    _validate_fingerprints(
        packet.source_fingerprints,
        path="source_fingerprints",
        issues=issues,
    )
    _validate_fingerprints(
        packet.input_fingerprints,
        path="input_fingerprints",
        issues=issues,
    )
    source_fingerprint = fingerprint_collection(packet.source_fingerprints)
    input_fingerprint = fingerprint_collection(packet.input_fingerprints)

    if not packet.toolchain.tools:
        _issue(
            issues,
            "toolchain.empty",
            "toolchain.tools",
            "must identify at least one tool",
        )
    tool_names: set[str] = set()
    for index, tool in enumerate(packet.toolchain.tools):
        path = f"toolchain.tools[{index}]"
        for field_name in ("name", "version", "identity"):
            _nonempty(
                getattr(tool, field_name),
                path=f"{path}.{field_name}",
                issues=issues,
            )
        if tool.name in tool_names:
            _issue(
                issues,
                "toolchain.duplicate_tool",
                f"{path}.name",
                f"duplicate tool {tool.name!r}",
            )
        tool_names.add(tool.name)

    artifacts_by_id: dict[str, ArtifactEvidence] = {}
    for index, artifact in enumerate(packet.artifacts):
        path = f"artifacts[{index}]"
        _stable_id(artifact.artifact_id, path=f"{path}.artifact_id", issues=issues)
        if artifact.artifact_id in artifacts_by_id:
            _issue(
                issues,
                "artifact.duplicate_id",
                f"{path}.artifact_id",
                f"duplicate artifact ID {artifact.artifact_id}",
            )
        artifacts_by_id[artifact.artifact_id] = artifact
        if not isinstance(artifact.role, ArtifactRole):
            _issue(
                issues,
                "artifact.role_invalid",
                f"{path}.role",
                "must be an ArtifactRole",
            )
        else:
            artifact_policy = ARTIFACT_POLICIES[artifact.role]
            if (
                artifact_policy.allowed_media_types
                and artifact.media_type not in artifact_policy.allowed_media_types
            ):
                _issue(
                    issues,
                    "artifact.media_type_mismatch",
                    f"{path}.media_type",
                    f"{artifact.role.value} does not allow {artifact.media_type!r}",
                )
        _nonempty(artifact.path, path=f"{path}.path", issues=issues)
        _nonempty(artifact.media_type, path=f"{path}.media_type", issues=issues)
        _valid_sha(artifact.sha256, path=f"{path}.sha256", issues=issues)
        if not isinstance(artifact.size_bytes, int) or artifact.size_bytes < 0:
            _issue(
                issues,
                "artifact.size_invalid",
                f"{path}.size_bytes",
                "must be a non-negative integer",
            )
        _valid_datetime(artifact.created_at, path=f"{path}.created_at", issues=issues)
        for field_name, expected in (
            ("contract_fingerprint", expected_contract_fingerprint),
            ("source_fingerprint", source_fingerprint),
            ("input_fingerprint", input_fingerprint),
        ):
            value = getattr(artifact, field_name)
            _valid_sha(value, path=f"{path}.{field_name}", issues=issues)
            if value != expected:
                _issue(
                    issues,
                    "artifact.stale_provenance",
                    f"{path}.{field_name}",
                    "artifact is not bound to the current packet inputs",
                )
        if artifact_probe is not None:
            try:
                observation = artifact_probe.inspect(artifact.path)
            except Exception as error:
                _issue(
                    issues,
                    "artifact.probe_failed",
                    f"{path}.path",
                    f"artifact probe failed: {error}",
                )
            else:
                if not observation.exists:
                    _issue(
                        issues,
                        "artifact.missing",
                        f"{path}.path",
                        "artifact does not exist",
                    )
                else:
                    if (
                        observation.sha256 is not None
                        and observation.sha256 != artifact.sha256
                    ):
                        _issue(
                            issues,
                            "artifact.hash_mismatch",
                            f"{path}.sha256",
                            "observed hash does not match recorded hash",
                        )
                    if (
                        observation.size_bytes is not None
                        and observation.size_bytes != artifact.size_bytes
                    ):
                        _issue(
                            issues,
                            "artifact.size_mismatch",
                            f"{path}.size_bytes",
                            "observed size does not match recorded size",
                        )

    for index, artifact in enumerate(packet.artifacts):
        path = f"artifacts[{index}].source_artifact_refs"
        referenced_roles: set[ArtifactRole] = set()
        seen_source_ids: set[str] = set()
        for reference_index, reference in enumerate(
            artifact.source_artifact_refs
        ):
            reference_path = f"{path}[{reference_index}]"
            source_artifact = _validate_artifact_reference(
                reference,
                artifacts_by_id,
                path=reference_path,
                issues=issues,
            )
            if source_artifact is None:
                continue
            if source_artifact.artifact_id == artifact.artifact_id:
                _issue(
                    issues,
                    "artifact.source_self_reference",
                    reference_path,
                    "an artifact cannot derive from itself",
                )
            if source_artifact.artifact_id in seen_source_ids:
                _issue(
                    issues,
                    "artifact.source_reference_duplicate",
                    reference_path,
                    "duplicates a source artifact reference",
                )
            seen_source_ids.add(source_artifact.artifact_id)
            if isinstance(source_artifact.role, ArtifactRole):
                referenced_roles.add(source_artifact.role)
        if not isinstance(artifact.role, ArtifactRole):
            continue
        artifact_policy = ARTIFACT_POLICIES[artifact.role]
        for required_role in artifact_policy.required_source_roles:
            if required_role in referenced_roles:
                continue
            _issue(
                issues,
                "artifact.source_role_missing",
                path,
                f"{artifact.role.value} must derive from {required_role.value}",
            )

    visual_by_id = {}
    for index, evidence in enumerate(packet.visual_evidence):
        path = f"visual_evidence[{index}]"
        _stable_id(evidence.evidence_id, path=f"{path}.evidence_id", issues=issues)
        if evidence.evidence_id in visual_by_id:
            _issue(
                issues,
                "visual.duplicate_id",
                f"{path}.evidence_id",
                f"duplicate evidence ID {evidence.evidence_id}",
            )
        visual_by_id[evidence.evidence_id] = evidence
        if not isinstance(evidence.channel, EvidenceChannel) or evidence.channel in (
            EvidenceChannel.NONE,
            EvidenceChannel.PROGRAMMATIC_GEOMETRY,
        ):
            _issue(
                issues,
                "visual.channel_invalid",
                f"{path}.channel",
                "must be a visual evidence channel",
            )
            continue
        policy = EVIDENCE_POLICIES[evidence.channel]
        if evidence.scope not in policy.allowed_scopes:
            _issue(
                issues,
                "visual.scope_invalid",
                f"{path}.scope",
                f"{evidence.channel.value} does not allow {evidence.scope.value}",
            )
        _nonempty(evidence.locator, path=f"{path}.locator", issues=issues)
        _nonempty(evidence.purpose, path=f"{path}.purpose", issues=issues)
        _nonempty(evidence.renderer, path=f"{path}.renderer", issues=issues)
        _valid_datetime(evidence.created_at, path=f"{path}.created_at", issues=issues)
        referenced_roles: set[ArtifactRole] = set()
        seen_artifact_refs: set[tuple[str, ArtifactRole]] = set()
        for reference_index, reference in enumerate(evidence.artifact_refs):
            reference_path = f"{path}.artifact_refs[{reference_index}]"
            artifact = _validate_artifact_reference(
                reference,
                artifacts_by_id,
                path=reference_path,
                issues=issues,
            )
            if artifact is None:
                continue
            key = (reference.artifact_id, reference.role)
            if key in seen_artifact_refs:
                _issue(
                    issues,
                    "visual.artifact_reference_duplicate",
                    reference_path,
                    "duplicates an artifact reference",
                )
            seen_artifact_refs.add(key)
            referenced_roles.add(reference.role)
        for required_role in policy.required_artifact_roles:
            if required_role not in referenced_roles:
                _issue(
                    issues,
                    "visual.artifact_role_missing",
                    f"{path}.artifact_refs",
                    f"{evidence.channel.value} requires {required_role.value}",
                )
        if policy.requires_reason and not (
            isinstance(evidence.reason, str) and evidence.reason.strip()
        ):
            _issue(
                issues,
                "visual.reason_missing",
                f"{path}.reason",
                "fallback or exceptional channel requires a reason",
            )
        if policy.requires_agent_inspection and not evidence.inspected_by_agent:
            _issue(
                issues,
                "visual.not_inspected",
                f"{path}.inspected_by_agent",
                "channel requires explicit agent inspection",
            )
        if policy.requires_read_only and not evidence.read_only:
            _issue(
                issues,
                "visual.not_read_only",
                f"{path}.read_only",
                "Viewer evidence must be read-only",
            )

    if isinstance(packet.profile, VerificationProfile):
        channels = {
            evidence.channel
            for evidence in packet.visual_evidence
            if isinstance(evidence.channel, EvidenceChannel)
        }
        for group in PROFILE_POLICIES[packet.profile].required_evidence_groups:
            if channels.intersection(group):
                continue
            choices = ", ".join(channel.value for channel in group)
            _issue(
                issues,
                "profile.evidence_channel_missing",
                "visual_evidence",
                f"{packet.profile.value} requires one of: {choices}",
            )

    expected_by_id = {
        requirement.requirement_id: requirement
        for requirement in selected_requirements
    }
    results_by_id = {}
    for index, result in enumerate(packet.results):
        path = f"results[{index}]"
        if result.requirement_id in results_by_id:
            _issue(
                issues,
                "result.duplicate_id",
                f"{path}.requirement_id",
                f"duplicate result {result.requirement_id}",
            )
        results_by_id[result.requirement_id] = result
        requirement = expected_by_id.get(result.requirement_id)
        if requirement is None:
            _issue(
                issues,
                "result.unexpected",
                f"{path}.requirement_id",
                "result is not part of the selected profile",
            )
        _nonempty(result.diagnostic, path=f"{path}.diagnostic", issues=issues)
        if not isinstance(result.status, ResultStatus):
            _issue(issues, "result.status_invalid", f"{path}.status", "invalid status")
            continue
        if not isinstance(result.evidence_channel, EvidenceChannel):
            _issue(
                issues,
                "result.channel_invalid",
                f"{path}.evidence_channel",
                "invalid evidence channel",
            )
            continue
        if result.actual is not None:
            _validate_actual(result.actual, path=f"{path}.actual", issues=issues)
        artifact_result_refs: list[ArtifactReference] = []
        visual_result_refs: list[VisualEvidenceReference] = []
        seen_result_refs: set[tuple[str, str]] = set()
        for reference_index, reference in enumerate(result.evidence_refs):
            reference_path = f"{path}.evidence_refs[{reference_index}]"
            if isinstance(reference, ArtifactReference):
                artifact = _validate_artifact_reference(
                    reference,
                    artifacts_by_id,
                    path=reference_path,
                    issues=issues,
                )
                if artifact is not None:
                    artifact_result_refs.append(reference)
                reference_key = ("artifact", reference.artifact_id)
            elif isinstance(reference, VisualEvidenceReference):
                _stable_id(
                    reference.evidence_id,
                    path=f"{reference_path}.evidence_id",
                    issues=issues,
                )
                if reference.evidence_id not in visual_by_id:
                    _issue(
                        issues,
                        "result.visual_evidence_unknown",
                        f"{reference_path}.evidence_id",
                        "does not reference packet visual evidence",
                    )
                else:
                    visual_result_refs.append(reference)
                reference_key = ("visual", reference.evidence_id)
            else:
                _issue(
                    issues,
                    "result.evidence_reference_invalid",
                    reference_path,
                    "must be an artifact or visual evidence reference",
                )
                continue
            if reference_key in seen_result_refs:
                _issue(
                    issues,
                    "result.evidence_reference_duplicate",
                    reference_path,
                    "duplicates an evidence reference",
                )
            seen_result_refs.add(reference_key)

        if result.status is ResultStatus.UNVERIFIED:
            if result.evidence_channel is not EvidenceChannel.NONE:
                _issue(
                    issues,
                    "result.unverified_channel",
                    f"{path}.evidence_channel",
                    "UNVERIFIED results must use the none channel",
                )
            if result.evidence_refs:
                _issue(
                    issues,
                    "result.unverified_evidence",
                    f"{path}.evidence_refs",
                    "UNVERIFIED results cannot claim evidence",
                )
            continue

        if result.actual is None:
            _issue(
                issues,
                "result.actual_missing",
                f"{path}.actual",
                "PASS/FAIL results require an actual value",
            )
        if result.evidence_channel is EvidenceChannel.NONE:
            _issue(
                issues,
                "result.evidence_missing",
                f"{path}.evidence_channel",
                "PASS/FAIL results require evidence",
            )
        if requirement is None:
            continue
        check_policy = CHECK_POLICIES[requirement.check.kind]
        if (
            result.actual is not None
            and result.actual.unit is not requirement.unit
        ):
            _issue(
                issues,
                "result.unit_mismatch",
                f"{path}.actual.unit",
                f"expected {requirement.unit.value}",
            )
        if result.evidence_channel not in check_policy.allowed_channels:
            _issue(
                issues,
                "result.channel_not_authoritative",
                f"{path}.evidence_channel",
                f"{requirement.check.kind.value} does not accept this channel",
            )
        if check_policy.requires_artifact_reference:
            referenced_artifact = bool(artifact_result_refs)
            referenced_visual = any(
                visual_by_id[reference.evidence_id].artifact_refs
                for reference in visual_result_refs
            )
            if not referenced_artifact and not referenced_visual:
                _issue(
                    issues,
                    "result.artifact_evidence_missing",
                    f"{path}.evidence_refs",
                    "check requires evidence bound to an exported artifact",
                )
        if result.evidence_channel is not EvidenceChannel.PROGRAMMATIC_GEOMETRY:
            matching_visual = any(
                visual_by_id[reference.evidence_id].channel
                is result.evidence_channel
                for reference in visual_result_refs
            )
            if not matching_visual:
                _issue(
                    issues,
                    "result.visual_evidence_missing",
                    f"{path}.evidence_refs",
                    "visual result must reference matching visual evidence",
                )
        if result.actual is not None:
            satisfies = actual_satisfies(requirement, result.actual)
            expected_status = ResultStatus.PASS if satisfies else ResultStatus.FAIL
            if result.status is not expected_status:
                _issue(
                    issues,
                    "result.status_mismatch",
                    f"{path}.status",
                    "status does not match expected value, unit, and tolerance",
                )

    missing_ids = set(expected_by_id) - set(results_by_id)
    for requirement_id in sorted(missing_ids):
        _issue(
            issues,
            "result.missing",
            "results",
            f"missing result for {requirement_id}; it remains UNVERIFIED",
        )

    metrics = packet.job_metrics
    _stable_id(metrics.job_id, path="job_metrics.job_id", issues=issues)
    started_valid = _valid_datetime(
        metrics.started_at,
        path="job_metrics.started_at",
        issues=issues,
    )
    finished_valid = _valid_datetime(
        metrics.finished_at,
        path="job_metrics.finished_at",
        issues=issues,
    )
    if started_valid and finished_valid and metrics.finished_at < metrics.started_at:
        _issue(
            issues,
            "job.time_invalid",
            "job_metrics.finished_at",
            "must not precede started_at",
        )
    if (
        not _is_number(metrics.elapsed_seconds)
        or not isfinite(float(metrics.elapsed_seconds))
        or metrics.elapsed_seconds < 0
    ):
        _issue(
            issues,
            "job.elapsed_invalid",
            "job_metrics.elapsed_seconds",
            "must be finite and non-negative",
        )
    if not isinstance(metrics.exit_code, int) or isinstance(metrics.exit_code, bool):
        _issue(issues, "job.exit_invalid", "job_metrics.exit_code", "must be int")
    elif metrics.exit_code != 0:
        _issue(
            issues,
            "job.failed",
            "job_metrics.exit_code",
            "verified review jobs must exit successfully",
        )
    if not isinstance(metrics.cleanup_completed, bool):
        _issue(
            issues,
            "job.cleanup_invalid",
            "job_metrics.cleanup_completed",
            "must be a boolean",
        )
    elif not metrics.cleanup_completed:
        _issue(
            issues,
            "job.cleanup_incomplete",
            "job_metrics.cleanup_completed",
            "verified review jobs must complete cleanup",
        )
    if metrics.worker_pid is not None and (
        not isinstance(metrics.worker_pid, int) or metrics.worker_pid <= 0
    ):
        _issue(
            issues,
            "job.pid_invalid",
            "job_metrics.worker_pid",
            "must be a positive integer or null",
        )
    if metrics.peak_rss_bytes is not None and (
        not isinstance(metrics.peak_rss_bytes, int) or metrics.peak_rss_bytes < 0
    ):
        _issue(
            issues,
            "job.rss_invalid",
            "job_metrics.peak_rss_bytes",
            "must be a non-negative integer or null",
        )
    if (
        not isinstance(metrics.orphan_processes, int)
        or isinstance(metrics.orphan_processes, bool)
        or metrics.orphan_processes < 0
    ):
        _issue(
            issues,
            "job.orphans_invalid",
            "job_metrics.orphan_processes",
            "must be a non-negative integer",
        )
    elif metrics.orphan_processes != 0:
        _issue(
            issues,
            "job.orphans_present",
            "job_metrics.orphan_processes",
            "verified review jobs must leave no owned orphan processes",
        )
    if len(set(metrics.outputs)) != len(metrics.outputs):
        _issue(
            issues,
            "job.outputs_duplicate",
            "job_metrics.outputs",
            "must not contain duplicates",
        )
    for index, output in enumerate(metrics.outputs):
        _nonempty(output, path=f"job_metrics.outputs[{index}]", issues=issues)

    packet_time_valid = _valid_datetime(
        packet.created_at,
        path="created_at",
        issues=issues,
    )
    if packet_time_valid and finished_valid and packet.created_at < metrics.finished_at:
        _issue(
            issues,
            "packet.time_invalid",
            "created_at",
            "review packet cannot predate job completion",
        )
    if packet_time_valid:
        for index, artifact in enumerate(packet.artifacts):
            if (
                isinstance(artifact.created_at, datetime)
                and artifact.created_at.tzinfo is not None
                and artifact.created_at > packet.created_at
            ):
                _issue(
                    issues,
                    "artifact.time_invalid",
                    f"artifacts[{index}].created_at",
                    "artifact cannot postdate the review packet",
                )
        for index, evidence in enumerate(packet.visual_evidence):
            if (
                isinstance(evidence.created_at, datetime)
                and evidence.created_at.tzinfo is not None
                and evidence.created_at > packet.created_at
            ):
                _issue(
                    issues,
                    "visual.time_invalid",
                    f"visual_evidence[{index}].created_at",
                    "visual evidence cannot postdate the review packet",
                )
    for field_name, values in (
        ("confirmed_facts", packet.confirmed_facts),
        ("remaining_uncertainty", packet.remaining_uncertainty),
    ):
        if not values:
            _issue(
                issues,
                f"packet.{field_name}_empty",
                field_name,
                "must contain at least one explicit entry",
            )
        for index, value in enumerate(values):
            _nonempty(value, path=f"{field_name}[{index}]", issues=issues)

    return tuple(issues)


def assert_valid_review_packet(
    packet: ReviewPacket,
    contract: DesignContract,
    *,
    artifact_probe: ArtifactProbe | None = None,
) -> None:
    issues = validate_review_packet(
        packet,
        contract,
        artifact_probe=artifact_probe,
    )
    if issues:
        raise VerificationValidationError(issues)
