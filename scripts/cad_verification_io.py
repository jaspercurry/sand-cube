"""Repository file adapters and reports for the portable verification core."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from cad_verification import (
    PROFILE_POLICIES,
    ArtifactObservation,
    DesignContract,
    Requirement,
    ResultStatus,
    ValidationIssue,
    VerificationProfile,
    contract_fingerprint,
    contract_from_json,
    profile_status,
    requirements_for_profile,
    review_packet_from_json,
    review_packet_to_dict,
    validate_review_packet,
)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class FileArtifactProbe:
    """Observe packet artifacts while keeping filesystem policy out of the core."""

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root.resolve()

    def inspect(self, path: str) -> ArtifactObservation:
        candidate = Path(path).expanduser()
        candidate = (
            candidate.resolve()
            if candidate.is_absolute()
            else (self.repository_root / candidate).resolve()
        )
        if (
            candidate != self.repository_root
            and self.repository_root not in candidate.parents
        ):
            return ArtifactObservation(exists=False)
        if not candidate.is_file():
            return ArtifactObservation(exists=False)
        stat = candidate.stat()
        return ArtifactObservation(
            exists=True,
            sha256=_sha256_file(candidate),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )


def _expectation(requirement: Requirement) -> dict[str, Any]:
    expectation = requirement.expectation
    if expectation.exact is not None:
        return {"kind": expectation.kind.value, "exact": expectation.exact}
    return {
        "kind": expectation.kind.value,
        "minimum": expectation.minimum,
        "maximum": expectation.maximum,
    }


def _requirement_base(requirement: Requirement) -> dict[str, Any]:
    return {
        "requirement_id": requirement.requirement_id,
        "description": requirement.description,
        "check_kind": requirement.check.kind.value,
        "adapter": requirement.check.adapter,
        "cost_profile": requirement.cost_profile.value,
        "expectation": _expectation(requirement),
        "unit": requirement.unit.value,
        "tolerance": {"absolute": requirement.tolerance.absolute},
    }


def _read_contract(path: Path) -> DesignContract:
    return contract_from_json(path.read_text(encoding="utf-8"))


def contract_profile_report(
    path: Path,
    profile: VerificationProfile,
) -> dict[str, Any]:
    """Validate a contract and project its authoritative profile composition."""

    contract = _read_contract(path)
    requirements = requirements_for_profile(contract, profile)
    return {
        "document": "design_contract",
        "path": str(path.resolve()),
        "contract_id": contract.contract_id,
        "contract_fingerprint": contract_fingerprint(contract),
        "profile": profile.value,
        "profile_description": PROFILE_POLICIES[profile].description,
        "included_costs": [cost.value for cost in PROFILE_POLICIES[profile].includes],
        "status": "valid",
        "requirements": [
            {**_requirement_base(requirement), "status": "selected", "actual": None}
            for requirement in requirements
        ],
        "issues": [],
    }


def _issue_dict(issue: ValidationIssue) -> dict[str, str]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _fingerprint_issues(
    records,
    *,
    label: str,
    repository_root: Path,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root = repository_root.resolve()
    for index, record in enumerate(records):
        path = Path(record.subject)
        candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
        issue_path = f"{label}_fingerprints[{index}].sha256"
        if candidate != root and root not in candidate.parents:
            issues.append(
                ValidationIssue(
                    f"fingerprint.{label}_outside_repository",
                    issue_path,
                    "fingerprint subject escapes the repository",
                )
            )
        elif not candidate.is_file():
            issues.append(
                ValidationIssue(
                    f"fingerprint.{label}_missing",
                    issue_path,
                    f"fingerprint subject does not exist: {record.subject}",
                )
            )
        elif _sha256_file(candidate) != record.sha256:
            issues.append(
                ValidationIssue(
                    f"fingerprint.{label}_mismatch",
                    issue_path,
                    f"current {label} content does not match the packet",
                )
            )
    return issues


def _viewer_url_issues(packet, repository_root: Path) -> list[ValidationIssue]:
    """Validate the repository's local read-only Viewer link contract."""

    issues: list[ValidationIssue] = []
    artifacts = {artifact.artifact_id: artifact for artifact in packet.artifacts}
    root = repository_root.resolve()
    for index, evidence in enumerate(packet.visual_evidence):
        if evidence.channel.value != "viewer":
            continue
        path = f"visual_evidence[{index}].locator"
        parsed = urlsplit(evidence.locator)
        query = parse_qs(parsed.query, keep_blank_values=True)
        artifact = artifacts.get(evidence.artifact_id or "")
        candidate = None
        if artifact is not None:
            candidate = (root / artifact.path).resolve()
        valid = (
            parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "localhost"}
            and parsed.port is not None
            and parsed.path == "/"
            and not parsed.fragment
            and set(query) == {"dir", "file"}
            and all(len(values) == 1 for values in query.values())
            and candidate is not None
            and query.get("dir") == [str(candidate.parent)]
            and query.get("file") == [candidate.name]
        )
        if not valid:
            issues.append(
                ValidationIssue(
                    "viewer.url_invalid",
                    path,
                    "URL does not match the repository local read-only artifact-link contract",
                )
            )
    return issues


def review_packet_report(
    contract_path: Path,
    packet_path: Path,
    *,
    requested_profile: VerificationProfile | None,
    repository_root: Path,
) -> dict[str, Any]:
    """Validate a packet, probe current artifacts, and report PASS only when proven."""

    contract = _read_contract(contract_path)
    packet = review_packet_from_json(packet_path.read_text(encoding="utf-8"))
    issues = list(
        validate_review_packet(
            packet,
            contract,
            artifact_probe=FileArtifactProbe(repository_root),
        )
    )
    issues.extend(
        _fingerprint_issues(
            packet.source_fingerprints,
            label="source",
            repository_root=repository_root,
        )
    )
    issues.extend(_viewer_url_issues(packet, repository_root))
    issues.extend(
        _fingerprint_issues(
            packet.input_fingerprints,
            label="input",
            repository_root=repository_root,
        )
    )
    if requested_profile is not None and requested_profile is not packet.profile:
        issues.append(
            ValidationIssue(
                "profile.mismatch",
                "profile",
                f"packet is {packet.profile.value}, requested {requested_profile.value}",
            )
        )

    status = profile_status(contract, packet.profile, packet.results)
    packet_data = review_packet_to_dict(packet)
    results_by_id = {
        result["requirement_id"]: result for result in packet_data["results"]
    }
    requirements: list[dict[str, Any]] = []
    for requirement in requirements_for_profile(contract, packet.profile):
        result = results_by_id.get(requirement.requirement_id)
        requirements.append(
            {
                **_requirement_base(requirement),
                "status": "missing" if result is None else result["status"],
                "actual": None if result is None else result["actual"],
                "evidence_channel": (
                    "none" if result is None else result["evidence_channel"]
                ),
                "evidence_tier": (
                    "none" if result is None else result["evidence_tier"]
                ),
                "evidence_refs": [] if result is None else result["evidence_refs"],
                "diagnostic": (
                    "required result is missing"
                    if result is None
                    else result["diagnostic"]
                ),
            }
        )

    success = not issues and status is ResultStatus.PASS
    return {
        "document": "review_packet",
        "path": str(packet_path.resolve()),
        "contract_path": str(contract_path.resolve()),
        "packet_id": packet.packet_id,
        "contract_id": packet.contract_id,
        "contract_fingerprint": packet.contract_fingerprint,
        "profile": packet.profile.value,
        "requested_profile": (
            None if requested_profile is None else requested_profile.value
        ),
        "status": status.value,
        "success": success,
        "requirements": requirements,
        "issues": [_issue_dict(issue) for issue in issues],
        "source_fingerprints": packet_data["source_fingerprints"],
        "input_fingerprints": packet_data["input_fingerprints"],
        "toolchain": packet_data["toolchain"],
        "artifacts": packet_data["artifacts"],
        "jobs": packet_data["jobs"],
        "visual_evidence": packet_data["visual_evidence"],
        "inspection_attestations": packet_data["inspection_attestations"],
        "viewer_records": packet_data["viewer_records"],
        "confirmed_facts": packet_data["confirmed_facts"],
        "remaining_uncertainty": packet_data["remaining_uncertainty"],
    }
