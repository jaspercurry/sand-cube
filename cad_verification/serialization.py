"""Strict deterministic JSON serialization for verification models."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, TypeVar

from .model import (
    ActualValue,
    ArtifactEvidence,
    ArtifactReference,
    CheckSpec,
    DesignContract,
    Expectation,
    Fingerprint,
    JobMetrics,
    ModelIdentity,
    Requirement,
    RequirementResult,
    ReviewPacket,
    Scalar,
    Tolerance,
    ToolIdentity,
    ToolchainIdentity,
    VisualEvidence,
    VisualEvidenceReference,
)
from .policy import (
    ArtifactRole,
    CheckKind,
    EvidenceChannel,
    EvidenceScope,
    EvidenceTier,
    ExpectationKind,
    ResultStatus,
    Unit,
    VerificationProfile,
)


class SerializationError(ValueError):
    pass


EnumT = TypeVar("EnumT")


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SerializationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_json_object)
    except SerializationError:
        raise
    except (json.JSONDecodeError, TypeError) as error:
        raise SerializationError(f"invalid JSON: {error}") from error


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SerializationError(f"{path} must be an object")
    return value


def _exact_keys(
    value: Mapping[str, Any],
    *,
    path: str,
    required: Iterable[str],
) -> None:
    required_set = set(required)
    actual = set(value)
    missing = sorted(required_set - actual)
    extra = sorted(actual - required_set)
    if missing:
        raise SerializationError(f"{path} missing keys: {', '.join(missing)}")
    if extra:
        raise SerializationError(f"{path} unknown keys: {', '.join(extra)}")


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise SerializationError(f"{path} must be a string")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise SerializationError(f"{path} must be a boolean")
    return value


def _integer(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SerializationError(f"{path} must be an integer")
    return value


def _number(value: Any, path: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SerializationError(f"{path} must be a number")
    return float(value)


def _optional_integer(value: Any, path: str) -> int | None:
    return None if value is None else _integer(value, path)


def _optional_string(value: Any, path: str) -> str | None:
    return None if value is None else _string(value, path)


def _scalar(value: Any, path: str) -> Scalar:
    if not isinstance(value, (bool, int, float, str)):
        raise SerializationError(f"{path} must be a JSON scalar")
    return value


def _enum(enum_type: type[EnumT], value: Any, path: str) -> EnumT:
    raw = _string(value, path)
    try:
        return enum_type(raw)
    except ValueError as error:
        raise SerializationError(f"{path} has unknown value {raw!r}") from error


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise SerializationError("cannot serialize a naive datetime")
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: Any, path: str) -> datetime:
    raw = _string(value, path)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise SerializationError(f"{path} is not an RFC 3339 datetime") from error
    if parsed.tzinfo is None:
        raise SerializationError(f"{path} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _model_to_dict(model: ModelIdentity) -> dict[str, Any]:
    return {
        "entrypoint": model.entrypoint,
        "model_id": model.model_id,
        "name": model.name,
        "source": model.source,
        "variant": model.variant,
    }


def _model_from_dict(value: Any, path: str) -> ModelIdentity:
    data = _mapping(value, path)
    keys = ("model_id", "name", "variant", "source", "entrypoint")
    _exact_keys(data, path=path, required=keys)
    return ModelIdentity(
        model_id=_string(data["model_id"], f"{path}.model_id"),
        name=_string(data["name"], f"{path}.name"),
        variant=_string(data["variant"], f"{path}.variant"),
        source=_string(data["source"], f"{path}.source"),
        entrypoint=_string(data["entrypoint"], f"{path}.entrypoint"),
    )


def _expectation_to_dict(expectation: Expectation) -> dict[str, Any]:
    if expectation.kind is ExpectationKind.EXACT:
        return {"exact": expectation.exact, "kind": expectation.kind.value}
    return {
        "kind": expectation.kind.value,
        "maximum": expectation.maximum,
        "minimum": expectation.minimum,
    }


def _expectation_from_dict(value: Any, path: str) -> Expectation:
    data = _mapping(value, path)
    if "kind" not in data:
        raise SerializationError(f"{path} missing keys: kind")
    kind = _enum(ExpectationKind, data["kind"], f"{path}.kind")
    if kind is ExpectationKind.EXACT:
        _exact_keys(data, path=path, required=("kind", "exact"))
        return Expectation.exactly(_scalar(data["exact"], f"{path}.exact"))
    _exact_keys(data, path=path, required=("kind", "minimum", "maximum"))
    return Expectation.between(
        _number(data["minimum"], f"{path}.minimum"),
        _number(data["maximum"], f"{path}.maximum"),
    )


def _requirement_to_dict(requirement: Requirement) -> dict[str, Any]:
    return {
        "check": {
            "adapter": requirement.check.adapter,
            "kind": requirement.check.kind.value,
            "parameters": {
                key: value
                for key, value in sorted(requirement.check.parameters)
            },
        },
        "cost_profile": requirement.cost_profile.value,
        "description": requirement.description,
        "expectation": _expectation_to_dict(requirement.expectation),
        "requirement_id": requirement.requirement_id,
        "tolerance": {"absolute": requirement.tolerance.absolute},
        "unit": requirement.unit.value,
    }


def _requirement_from_dict(value: Any, path: str) -> Requirement:
    data = _mapping(value, path)
    _exact_keys(
        data,
        path=path,
        required=(
            "requirement_id",
            "description",
            "check",
            "expectation",
            "unit",
            "tolerance",
            "cost_profile",
        ),
    )
    check_data = _mapping(data["check"], f"{path}.check")
    _exact_keys(
        check_data,
        path=f"{path}.check",
        required=("kind", "adapter", "parameters"),
    )
    parameters = _mapping(check_data["parameters"], f"{path}.check.parameters")
    tolerance_data = _mapping(data["tolerance"], f"{path}.tolerance")
    _exact_keys(
        tolerance_data,
        path=f"{path}.tolerance",
        required=("absolute",),
    )
    return Requirement(
        requirement_id=_string(
            data["requirement_id"], f"{path}.requirement_id"
        ),
        description=_string(data["description"], f"{path}.description"),
        check=CheckSpec(
            kind=_enum(CheckKind, check_data["kind"], f"{path}.check.kind"),
            adapter=_string(check_data["adapter"], f"{path}.check.adapter"),
            parameters=tuple(
                (key, _scalar(parameter, f"{path}.check.parameters.{key}"))
                for key, parameter in sorted(parameters.items())
            ),
        ),
        expectation=_expectation_from_dict(
            data["expectation"], f"{path}.expectation"
        ),
        unit=_enum(Unit, data["unit"], f"{path}.unit"),
        tolerance=Tolerance(
            _number(
                tolerance_data["absolute"],
                f"{path}.tolerance.absolute",
            )
        ),
        cost_profile=_enum(
            VerificationProfile,
            data["cost_profile"],
            f"{path}.cost_profile",
        ),
    )


def contract_to_dict(contract: DesignContract) -> dict[str, Any]:
    return {
        "contract_id": contract.contract_id,
        "model": _model_to_dict(contract.model),
        "requirements": [
            _requirement_to_dict(requirement)
            for requirement in sorted(
                contract.requirements,
                key=lambda item: item.requirement_id,
            )
        ],
        "schema_version": contract.schema_version,
        "title": contract.title,
    }


def contract_from_dict(value: Any, *, validate: bool = True) -> DesignContract:
    data = _mapping(value, "contract")
    _exact_keys(
        data,
        path="contract",
        required=(
            "schema_version",
            "contract_id",
            "title",
            "model",
            "requirements",
        ),
    )
    requirements = data["requirements"]
    if not isinstance(requirements, list):
        raise SerializationError("contract.requirements must be an array")
    contract = DesignContract(
        schema_version=_integer(data["schema_version"], "contract.schema_version"),
        contract_id=_string(data["contract_id"], "contract.contract_id"),
        title=_string(data["title"], "contract.title"),
        model=_model_from_dict(data["model"], "contract.model"),
        requirements=tuple(
            _requirement_from_dict(item, f"contract.requirements[{index}]")
            for index, item in enumerate(requirements)
        ),
    )
    if validate:
        from .validation import assert_valid_contract

        assert_valid_contract(contract)
    return contract


def _fingerprint_to_dict(fingerprint: Fingerprint) -> dict[str, str]:
    return {"sha256": fingerprint.sha256, "subject": fingerprint.subject}


def _fingerprint_from_dict(value: Any, path: str) -> Fingerprint:
    data = _mapping(value, path)
    _exact_keys(data, path=path, required=("subject", "sha256"))
    return Fingerprint(
        subject=_string(data["subject"], f"{path}.subject"),
        sha256=_string(data["sha256"], f"{path}.sha256"),
    )


def _actual_to_dict(actual: ActualValue | None) -> dict[str, Any] | None:
    if actual is None:
        return None
    return {"unit": actual.unit.value, "value": actual.value}


def _actual_from_dict(value: Any, path: str) -> ActualValue | None:
    if value is None:
        return None
    data = _mapping(value, path)
    _exact_keys(data, path=path, required=("value", "unit"))
    return ActualValue(
        value=_scalar(data["value"], f"{path}.value"),
        unit=_enum(Unit, data["unit"], f"{path}.unit"),
    )


def _artifact_reference_to_dict(reference: ArtifactReference) -> dict[str, str]:
    return {
        "artifact_id": reference.artifact_id,
        "role": reference.role.value,
        "sha256": reference.sha256,
    }


def _artifact_reference_from_dict(value: Any, path: str) -> ArtifactReference:
    data = _mapping(value, path)
    _exact_keys(
        data,
        path=path,
        required=("artifact_id", "role", "sha256"),
    )
    return ArtifactReference(
        artifact_id=_string(data["artifact_id"], f"{path}.artifact_id"),
        role=_enum(ArtifactRole, data["role"], f"{path}.role"),
        sha256=_string(data["sha256"], f"{path}.sha256"),
    )


def _evidence_reference_to_dict(
    reference: ArtifactReference | VisualEvidenceReference,
) -> dict[str, Any]:
    if isinstance(reference, ArtifactReference):
        return {"kind": "artifact", **_artifact_reference_to_dict(reference)}
    if isinstance(reference, VisualEvidenceReference):
        return {
            "evidence_id": reference.evidence_id,
            "kind": "visual",
        }
    raise SerializationError(f"unsupported evidence reference: {reference!r}")


def _evidence_reference_from_dict(
    value: Any,
    path: str,
) -> ArtifactReference | VisualEvidenceReference:
    data = _mapping(value, path)
    if "kind" not in data:
        raise SerializationError(f"{path} missing keys: kind")
    kind = _string(data["kind"], f"{path}.kind")
    if kind == "artifact":
        _exact_keys(
            data,
            path=path,
            required=("kind", "artifact_id", "role", "sha256"),
        )
        return _artifact_reference_from_dict(
            {key: value for key, value in data.items() if key != "kind"},
            path,
        )
    if kind == "visual":
        _exact_keys(data, path=path, required=("kind", "evidence_id"))
        return VisualEvidenceReference(
            evidence_id=_string(data["evidence_id"], f"{path}.evidence_id")
        )
    raise SerializationError(f"{path}.kind has unknown value {kind!r}")


def _evidence_reference_sort_key(
    reference: ArtifactReference | VisualEvidenceReference,
) -> tuple[str, str, str, str]:
    if isinstance(reference, ArtifactReference):
        return (
            "artifact",
            reference.artifact_id,
            reference.role.value,
            reference.sha256,
        )
    return ("visual", reference.evidence_id, "", "")


def _result_to_dict(result: RequirementResult) -> dict[str, Any]:
    return {
        "actual": _actual_to_dict(result.actual),
        "diagnostic": result.diagnostic,
        "evidence_channel": result.evidence_channel.value,
        "evidence_refs": [
            _evidence_reference_to_dict(reference)
            for reference in sorted(
                result.evidence_refs,
                key=_evidence_reference_sort_key,
            )
        ],
        "evidence_tier": result.evidence_tier.value,
        "requirement_id": result.requirement_id,
        "status": result.status.value,
    }


def _result_from_dict(value: Any, path: str) -> RequirementResult:
    data = _mapping(value, path)
    _exact_keys(
        data,
        path=path,
        required=(
            "requirement_id",
            "status",
            "actual",
            "evidence_channel",
            "evidence_tier",
            "diagnostic",
            "evidence_refs",
        ),
    )
    channel = _enum(
        EvidenceChannel,
        data["evidence_channel"],
        f"{path}.evidence_channel",
    )
    tier = _enum(EvidenceTier, data["evidence_tier"], f"{path}.evidence_tier")
    from .policy import evidence_tier

    if tier is not evidence_tier(channel):
        raise SerializationError(
            f"{path}.evidence_tier does not match the channel policy"
        )
    references = data["evidence_refs"]
    if not isinstance(references, list):
        raise SerializationError(f"{path}.evidence_refs must be an array")
    return RequirementResult(
        requirement_id=_string(
            data["requirement_id"], f"{path}.requirement_id"
        ),
        status=_enum(ResultStatus, data["status"], f"{path}.status"),
        actual=_actual_from_dict(data["actual"], f"{path}.actual"),
        evidence_channel=channel,
        diagnostic=_string(data["diagnostic"], f"{path}.diagnostic"),
        evidence_refs=tuple(
            _evidence_reference_from_dict(
                reference,
                f"{path}.evidence_refs[{index}]",
            )
            for index, reference in enumerate(references)
        ),
    )


def _artifact_to_dict(artifact: ArtifactEvidence) -> dict[str, Any]:
    return {
        "artifact_id": artifact.artifact_id,
        "contract_fingerprint": artifact.contract_fingerprint,
        "created_at": _datetime_text(artifact.created_at),
        "input_fingerprint": artifact.input_fingerprint,
        "media_type": artifact.media_type,
        "path": artifact.path,
        "role": artifact.role.value,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "source_artifact_refs": [
            _artifact_reference_to_dict(reference)
            for reference in sorted(
                artifact.source_artifact_refs,
                key=lambda item: (
                    item.role.value,
                    item.artifact_id,
                    item.sha256,
                ),
            )
        ],
        "source_fingerprint": artifact.source_fingerprint,
    }


def _artifact_from_dict(value: Any, path: str) -> ArtifactEvidence:
    data = _mapping(value, path)
    keys = (
        "artifact_id",
        "role",
        "path",
        "media_type",
        "sha256",
        "size_bytes",
        "created_at",
        "contract_fingerprint",
        "source_fingerprint",
        "input_fingerprint",
        "source_artifact_refs",
    )
    _exact_keys(data, path=path, required=keys)
    source_artifact_refs = data["source_artifact_refs"]
    if not isinstance(source_artifact_refs, list):
        raise SerializationError(f"{path}.source_artifact_refs must be an array")
    return ArtifactEvidence(
        artifact_id=_string(data["artifact_id"], f"{path}.artifact_id"),
        role=_enum(ArtifactRole, data["role"], f"{path}.role"),
        path=_string(data["path"], f"{path}.path"),
        media_type=_string(data["media_type"], f"{path}.media_type"),
        sha256=_string(data["sha256"], f"{path}.sha256"),
        size_bytes=_integer(data["size_bytes"], f"{path}.size_bytes"),
        created_at=_parse_datetime(data["created_at"], f"{path}.created_at"),
        contract_fingerprint=_string(
            data["contract_fingerprint"], f"{path}.contract_fingerprint"
        ),
        source_fingerprint=_string(
            data["source_fingerprint"], f"{path}.source_fingerprint"
        ),
        input_fingerprint=_string(
            data["input_fingerprint"], f"{path}.input_fingerprint"
        ),
        source_artifact_refs=tuple(
            _artifact_reference_from_dict(
                reference,
                f"{path}.source_artifact_refs[{index}]",
            )
            for index, reference in enumerate(source_artifact_refs)
        ),
    )


def _visual_to_dict(evidence: VisualEvidence) -> dict[str, Any]:
    return {
        "artifact_refs": [
            _artifact_reference_to_dict(reference)
            for reference in sorted(
                evidence.artifact_refs,
                key=lambda item: (
                    item.role.value,
                    item.artifact_id,
                    item.sha256,
                ),
            )
        ],
        "channel": evidence.channel.value,
        "created_at": _datetime_text(evidence.created_at),
        "evidence_id": evidence.evidence_id,
        "inspected_by_agent": evidence.inspected_by_agent,
        "locator": evidence.locator,
        "purpose": evidence.purpose,
        "read_only": evidence.read_only,
        "reason": evidence.reason,
        "renderer": evidence.renderer,
        "scope": evidence.scope.value,
    }


def _visual_from_dict(value: Any, path: str) -> VisualEvidence:
    data = _mapping(value, path)
    keys = (
        "evidence_id",
        "channel",
        "scope",
        "locator",
        "purpose",
        "created_at",
        "artifact_refs",
        "renderer",
        "inspected_by_agent",
        "read_only",
        "reason",
    )
    _exact_keys(data, path=path, required=keys)
    artifact_refs = data["artifact_refs"]
    if not isinstance(artifact_refs, list):
        raise SerializationError(f"{path}.artifact_refs must be an array")
    return VisualEvidence(
        evidence_id=_string(data["evidence_id"], f"{path}.evidence_id"),
        channel=_enum(EvidenceChannel, data["channel"], f"{path}.channel"),
        scope=_enum(EvidenceScope, data["scope"], f"{path}.scope"),
        locator=_string(data["locator"], f"{path}.locator"),
        purpose=_string(data["purpose"], f"{path}.purpose"),
        created_at=_parse_datetime(data["created_at"], f"{path}.created_at"),
        artifact_refs=tuple(
            _artifact_reference_from_dict(
                reference,
                f"{path}.artifact_refs[{index}]",
            )
            for index, reference in enumerate(artifact_refs)
        ),
        renderer=_string(data["renderer"], f"{path}.renderer"),
        inspected_by_agent=_boolean(
            data["inspected_by_agent"], f"{path}.inspected_by_agent"
        ),
        read_only=_boolean(data["read_only"], f"{path}.read_only"),
        reason=_optional_string(data["reason"], f"{path}.reason"),
    )


def _job_to_dict(metrics: JobMetrics) -> dict[str, Any]:
    return {
        "cleanup_completed": metrics.cleanup_completed,
        "elapsed_seconds": metrics.elapsed_seconds,
        "exit_code": metrics.exit_code,
        "finished_at": _datetime_text(metrics.finished_at),
        "job_id": metrics.job_id,
        "orphan_processes": metrics.orphan_processes,
        "outputs": sorted(metrics.outputs),
        "peak_rss_bytes": metrics.peak_rss_bytes,
        "started_at": _datetime_text(metrics.started_at),
        "worker_pid": metrics.worker_pid,
    }


def _job_from_dict(value: Any, path: str) -> JobMetrics:
    data = _mapping(value, path)
    keys = (
        "job_id",
        "started_at",
        "finished_at",
        "elapsed_seconds",
        "exit_code",
        "worker_pid",
        "peak_rss_bytes",
        "cleanup_completed",
        "orphan_processes",
        "outputs",
    )
    _exact_keys(data, path=path, required=keys)
    outputs = data["outputs"]
    if not isinstance(outputs, list):
        raise SerializationError(f"{path}.outputs must be an array")
    return JobMetrics(
        job_id=_string(data["job_id"], f"{path}.job_id"),
        started_at=_parse_datetime(data["started_at"], f"{path}.started_at"),
        finished_at=_parse_datetime(data["finished_at"], f"{path}.finished_at"),
        elapsed_seconds=_number(
            data["elapsed_seconds"], f"{path}.elapsed_seconds"
        ),
        exit_code=_integer(data["exit_code"], f"{path}.exit_code"),
        worker_pid=_optional_integer(data["worker_pid"], f"{path}.worker_pid"),
        peak_rss_bytes=_optional_integer(
            data["peak_rss_bytes"], f"{path}.peak_rss_bytes"
        ),
        cleanup_completed=_boolean(
            data["cleanup_completed"], f"{path}.cleanup_completed"
        ),
        orphan_processes=_integer(
            data["orphan_processes"], f"{path}.orphan_processes"
        ),
        outputs=tuple(
            _string(output, f"{path}.outputs[{index}]")
            for index, output in enumerate(outputs)
        ),
    )


def review_packet_to_dict(packet: ReviewPacket) -> dict[str, Any]:
    return {
        "artifacts": [
            _artifact_to_dict(artifact)
            for artifact in sorted(packet.artifacts, key=lambda item: item.artifact_id)
        ],
        "confirmed_facts": list(packet.confirmed_facts),
        "contract_fingerprint": packet.contract_fingerprint,
        "contract_id": packet.contract_id,
        "created_at": _datetime_text(packet.created_at),
        "input_fingerprints": [
            _fingerprint_to_dict(fingerprint)
            for fingerprint in sorted(
                packet.input_fingerprints,
                key=lambda item: item.subject,
            )
        ],
        "job_metrics": _job_to_dict(packet.job_metrics),
        "model": _model_to_dict(packet.model),
        "packet_id": packet.packet_id,
        "profile": packet.profile.value,
        "remaining_uncertainty": list(packet.remaining_uncertainty),
        "results": [
            _result_to_dict(result)
            for result in sorted(packet.results, key=lambda item: item.requirement_id)
        ],
        "schema_version": packet.schema_version,
        "source_fingerprints": [
            _fingerprint_to_dict(fingerprint)
            for fingerprint in sorted(
                packet.source_fingerprints,
                key=lambda item: item.subject,
            )
        ],
        "toolchain": {
            "tools": [
                {
                    "identity": tool.identity,
                    "name": tool.name,
                    "version": tool.version,
                }
                for tool in sorted(packet.toolchain.tools, key=lambda item: item.name)
            ]
        },
        "visual_evidence": [
            _visual_to_dict(evidence)
            for evidence in sorted(
                packet.visual_evidence,
                key=lambda item: item.evidence_id,
            )
        ],
    }


def review_packet_from_dict(
    value: Any,
    *,
    contract: DesignContract | None = None,
) -> ReviewPacket:
    data = _mapping(value, "review_packet")
    keys = (
        "schema_version",
        "packet_id",
        "contract_id",
        "contract_fingerprint",
        "profile",
        "model",
        "source_fingerprints",
        "input_fingerprints",
        "toolchain",
        "artifacts",
        "results",
        "job_metrics",
        "visual_evidence",
        "confirmed_facts",
        "remaining_uncertainty",
        "created_at",
    )
    _exact_keys(data, path="review_packet", required=keys)

    def array(name: str) -> list[Any]:
        value = data[name]
        if not isinstance(value, list):
            raise SerializationError(f"review_packet.{name} must be an array")
        return value

    toolchain_data = _mapping(data["toolchain"], "review_packet.toolchain")
    _exact_keys(
        toolchain_data,
        path="review_packet.toolchain",
        required=("tools",),
    )
    tools_data = toolchain_data["tools"]
    if not isinstance(tools_data, list):
        raise SerializationError("review_packet.toolchain.tools must be an array")
    tools = []
    for index, tool_value in enumerate(tools_data):
        path = f"review_packet.toolchain.tools[{index}]"
        tool_data = _mapping(tool_value, path)
        _exact_keys(
            tool_data,
            path=path,
            required=("name", "version", "identity"),
        )
        tools.append(
            ToolIdentity(
                name=_string(tool_data["name"], f"{path}.name"),
                version=_string(tool_data["version"], f"{path}.version"),
                identity=_string(tool_data["identity"], f"{path}.identity"),
            )
        )

    facts = array("confirmed_facts")
    uncertainty = array("remaining_uncertainty")
    packet = ReviewPacket(
        schema_version=_integer(
            data["schema_version"], "review_packet.schema_version"
        ),
        packet_id=_string(data["packet_id"], "review_packet.packet_id"),
        contract_id=_string(data["contract_id"], "review_packet.contract_id"),
        contract_fingerprint=_string(
            data["contract_fingerprint"],
            "review_packet.contract_fingerprint",
        ),
        profile=_enum(
            VerificationProfile,
            data["profile"],
            "review_packet.profile",
        ),
        model=_model_from_dict(data["model"], "review_packet.model"),
        source_fingerprints=tuple(
            _fingerprint_from_dict(
                item,
                f"review_packet.source_fingerprints[{index}]",
            )
            for index, item in enumerate(array("source_fingerprints"))
        ),
        input_fingerprints=tuple(
            _fingerprint_from_dict(
                item,
                f"review_packet.input_fingerprints[{index}]",
            )
            for index, item in enumerate(array("input_fingerprints"))
        ),
        toolchain=ToolchainIdentity(tuple(tools)),
        artifacts=tuple(
            _artifact_from_dict(item, f"review_packet.artifacts[{index}]")
            for index, item in enumerate(array("artifacts"))
        ),
        results=tuple(
            _result_from_dict(item, f"review_packet.results[{index}]")
            for index, item in enumerate(array("results"))
        ),
        job_metrics=_job_from_dict(
            data["job_metrics"], "review_packet.job_metrics"
        ),
        visual_evidence=tuple(
            _visual_from_dict(
                item,
                f"review_packet.visual_evidence[{index}]",
            )
            for index, item in enumerate(array("visual_evidence"))
        ),
        confirmed_facts=tuple(
            _string(item, f"review_packet.confirmed_facts[{index}]")
            for index, item in enumerate(facts)
        ),
        remaining_uncertainty=tuple(
            _string(item, f"review_packet.remaining_uncertainty[{index}]")
            for index, item in enumerate(uncertainty)
        ),
        created_at=_parse_datetime(data["created_at"], "review_packet.created_at"),
    )
    if contract is not None:
        from .validation import assert_valid_review_packet

        assert_valid_review_packet(packet, contract)
    return packet


def _dumps(value: Any, *, indent: int | None) -> str:
    if indent is None:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )
        + "\n"
    )


def contract_to_json(contract: DesignContract, *, indent: int | None = 2) -> str:
    return _dumps(contract_to_dict(contract), indent=indent)


def contract_from_json(text: str, *, validate: bool = True) -> DesignContract:
    return contract_from_dict(_load_json(text), validate=validate)


def review_packet_to_json(
    packet: ReviewPacket,
    *,
    indent: int | None = 2,
) -> str:
    return _dumps(review_packet_to_dict(packet), indent=indent)


def review_packet_from_json(
    text: str,
    *,
    contract: DesignContract | None = None,
) -> ReviewPacket:
    return review_packet_from_dict(_load_json(text), contract=contract)


def contract_fingerprint(contract: DesignContract) -> str:
    payload = contract_to_json(contract, indent=None).encode("utf-8")
    return sha256(payload).hexdigest()


def fingerprint_collection(fingerprints: Iterable[Fingerprint]) -> str:
    payload = [
        _fingerprint_to_dict(fingerprint)
        for fingerprint in sorted(fingerprints, key=lambda item: item.subject)
    ]
    return sha256(_dumps(payload, indent=None).encode("utf-8")).hexdigest()
