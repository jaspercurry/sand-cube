"""Assemble standard review packets from coordinated coupon evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import struct
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cad_verification import (  # noqa: E402
    ActualValue,
    ArtifactEvidence,
    EvidenceChannel,
    EvidenceScope,
    Fingerprint,
    JobMetrics,
    ResultStatus,
    ReviewPacket,
    ToolIdentity,
    ToolchainIdentity,
    Unit,
    VerificationProfile,
    VisualEvidence,
    assess,
    contract_fingerprint,
    fingerprint_collection,
    profile_status,
    review_packet_to_json,
    validate_review_packet,
)
from scripts.cad_verification_io import FileArtifactProbe  # noqa: E402
from workbench.designs.joint_coupon.parameters import (  # noqa: E402
    load_parameters,
)
from workbench.designs.joint_coupon.verification import (  # noqa: E402
    design_contract,
    input_fingerprints as current_input_fingerprints,
    sha256_file,
    source_fingerprints as current_source_fingerprints,
)


OUTPUT_ROOT = ROOT / "build/workbench/joint_coupon"
ASSEMBLY_ARTIFACT = "artifact.joint-coupon-assembly-step"
LOWER_ARTIFACT = "artifact.joint-coupon-lower-step"
UPPER_ARTIFACT = "artifact.joint-coupon-upper-step"
SIDECAR_ARTIFACT = "artifact.joint-coupon-topology-sidecar"
OVERVIEW_ARTIFACT = "artifact.joint-coupon-snapshot-isometric"
SECTION_ARTIFACT = "artifact.joint-coupon-snapshot-section"
VIEWER_EVIDENCE = "viewer.joint-coupon-assembly"
OVERVIEW_EVIDENCE = "snapshot.joint-coupon-isometric"
SECTION_EVIDENCE = "snapshot.joint-coupon-section"
STEP_HASH_FIELD = re.compile(rb'"stepHash"\s*:\s*"([0-9a-f]{64})"')


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        required=True,
    )
    parser.add_argument("--job-record", type=Path, required=True)
    parser.add_argument("--viewer-url")
    parser.add_argument("--sidecar", type=Path)
    parser.add_argument("--snapshot-overview", type=Path)
    parser.add_argument("--snapshot-section", type=Path)
    return parser


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"datetime lacks a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def _fingerprints(records: list[dict[str, str]]) -> tuple[Fingerprint, ...]:
    return tuple(Fingerprint(record["subject"], record["sha256"]) for record in records)


def _require_current_fingerprints(
    recorded: tuple[Fingerprint, ...],
    current: tuple[Fingerprint, ...],
    label: str,
) -> None:
    if recorded != current:
        raise ValueError(f"{label} changed after the coordinated measurement job")


def _job_metrics(payload: dict[str, Any]) -> JobMetrics:
    if payload.get("state") != "completed" or payload.get("exit_code") != 0:
        raise ValueError("review packets require a completed zero-exit CAD job")
    cleanup = payload.get("cleanup", {})
    owned = cleanup.get("owned_process_group", {})
    remaining = tuple(owned.get("remaining_owned_pids", ()))
    outputs = tuple(
        str(record["path"]) for record in payload.get("final_outputs", ())
    )
    return JobMetrics(
        job_id=str(payload["job_id"]),
        started_at=_datetime(payload["started_at"]),
        finished_at=_datetime(payload["finished_at"]),
        elapsed_seconds=float(payload["elapsed_seconds"]),
        exit_code=int(payload["exit_code"]),
        worker_pid=payload.get("worker_pid"),
        peak_rss_bytes=payload.get("peak_rss_bytes"),
        cleanup_completed=(
            cleanup.get("workspace_removed") is True
            and cleanup.get("error") is None
            and owned.get("reaped") is True
            and not remaining
        ),
        orphan_processes=len(remaining),
        outputs=outputs,
    )


def _relative(path: Path) -> str:
    resolved = path.expanduser().resolve()
    return str(resolved.relative_to(ROOT))


def _glb_step_hashes(path: Path) -> set[str]:
    """Read STEP bindings from a GLB JSON chunk without a graphics runtime."""

    payload = path.read_bytes()
    if len(payload) < 12 or payload[:4] != b"glTF":
        raise ValueError(f"sidecar is not a GLB file: {path}")
    version, declared_size = struct.unpack_from("<II", payload, 4)
    if version != 2 or declared_size != len(payload):
        raise ValueError(f"sidecar has an invalid GLB header: {path}")

    hashes = {
        match.decode("ascii") for match in STEP_HASH_FIELD.findall(payload)
    }
    offset = 12
    while offset < len(payload):
        if offset + 8 > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk header: {path}")
        chunk_size, _chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        end = offset + chunk_size
        if end > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk: {path}")
        offset = end
    return hashes


def _artifact(
    artifact_id: str,
    path: Path,
    media_type: str,
    *,
    contract_digest: str,
    source_digest: str,
    input_digest: str,
) -> ArtifactEvidence:
    resolved = path.expanduser().resolve()
    stat = resolved.stat()
    return ArtifactEvidence(
        artifact_id=artifact_id,
        path=_relative(resolved),
        media_type=media_type,
        sha256=sha256_file(resolved),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        contract_fingerprint=contract_digest,
        source_fingerprint=source_digest,
        input_fingerprint=input_digest,
    )


def _tools(profile: VerificationProfile) -> ToolchainIdentity:
    with (ROOT / ".cad-project/project.toml").open("rb") as stream:
        config = tomllib.load(stream)
    project_identity = sha256_file(ROOT / ".cad-project/project.toml")
    tools = [
        ToolIdentity(
            "python",
            platform.python_version(),
            sys.implementation.cache_tag or platform.python_implementation(),
        ),
        ToolIdentity(
            "build123d",
            str(config["dependencies"]["build123d"]),
            f"project-config:{project_identity}",
        ),
        ToolIdentity(
            "cadquery-ocp-novtk",
            str(config["dependencies"]["cadquery_ocp_novtk"]),
            f"project-config:{project_identity}",
        ),
    ]
    if profile is VerificationProfile.RELEASE:
        tools.append(
            ToolIdentity(
                "Text-to-CAD",
                str(config["viewer"]["version"]),
                str(config["viewer"]["commit"]),
            )
        )
    return ToolchainIdentity(tuple(tools))


def _programmatic_results(diagnostics, requirements):
    results = []
    for record in diagnostics["results"]:
        actual = record.get("actual")
        if actual is None:
            raise ValueError(f"native result is missing: {record['requirement_id']}")
        result = assess(
            requirements[record["requirement_id"]],
            ActualValue(actual["value"], Unit(actual["unit"])),
            evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
            diagnostic=record["diagnostic"],
            evidence_refs=tuple(record.get("evidence_refs", ())),
        )
        if result.status.value != record["status"]:
            raise ValueError(
                f"stored status drift for {record['requirement_id']}"
            )
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    profile = VerificationProfile(args.profile)
    diagnostics_path = OUTPUT_ROOT / f"diagnostics-{profile.value}.json"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    if diagnostics.get("profile") != profile.value:
        raise ValueError("diagnostics profile mismatch")

    _, params = load_parameters()
    contract = design_contract(params)
    if diagnostics.get("contract_fingerprint") != contract_fingerprint(contract):
        raise ValueError("contract changed after the coordinated measurement job")
    sources = _fingerprints(diagnostics["source_fingerprints"])
    inputs = _fingerprints(diagnostics["input_fingerprints"])
    _require_current_fingerprints(sources, current_source_fingerprints(), "source")
    _require_current_fingerprints(inputs, current_input_fingerprints(), "input")

    requirements = {
        requirement.requirement_id: requirement
        for requirement in contract.requirements
    }
    results = _programmatic_results(diagnostics, requirements)
    job_payload = json.loads(args.job_record.read_text(encoding="utf-8"))
    metrics = _job_metrics(job_payload)
    created_at = datetime.now(timezone.utc)
    contract_digest = contract_fingerprint(contract)
    source_digest = fingerprint_collection(sources)
    input_digest = fingerprint_collection(inputs)
    artifacts: list[ArtifactEvidence] = []
    visual: list[VisualEvidence] = []

    if profile is VerificationProfile.RELEASE:
        required_arguments = {
            "viewer URL": args.viewer_url,
            "sidecar": args.sidecar,
            "isometric Snapshot": args.snapshot_overview,
            "section Snapshot": args.snapshot_section,
        }
        missing = [name for name, value in required_arguments.items() if not value]
        if missing:
            raise ValueError(f"release packet missing: {', '.join(missing)}")
        artifact_specs = (
            (ASSEMBLY_ARTIFACT, OUTPUT_ROOT / "joint_coupon_assembly.step", "model/step"),
            (LOWER_ARTIFACT, OUTPUT_ROOT / "joint_coupon_lower.step", "model/step"),
            (UPPER_ARTIFACT, OUTPUT_ROOT / "joint_coupon_upper.step", "model/step"),
            ("artifact.joint-coupon-gaskets-step", OUTPUT_ROOT / "joint_coupon_gaskets.step", "model/step"),
            (SIDECAR_ARTIFACT, args.sidecar, "model/gltf-binary"),
            (OVERVIEW_ARTIFACT, args.snapshot_overview, "image/png"),
            (SECTION_ARTIFACT, args.snapshot_section, "image/png"),
        )
        artifacts = [
            _artifact(
                artifact_id,
                path,
                media_type,
                contract_digest=contract_digest,
                source_digest=source_digest,
                input_digest=input_digest,
            )
            for artifact_id, path, media_type in artifact_specs
        ]
        assembly_hash = next(
            item.sha256
            for item in artifacts
            if item.artifact_id == ASSEMBLY_ARTIFACT
        )
        if assembly_hash not in _glb_step_hashes(args.sidecar):
            raise ValueError(
                "sidecar does not embed the current assembly STEP SHA-256"
            )
        visual = [
            VisualEvidence(
                evidence_id=VIEWER_EVIDENCE,
                channel=EvidenceChannel.VIEWER,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=str(args.viewer_url),
                purpose="Interactive inspection of the exact assembly STEP and sidecar.",
                created_at=created_at,
                renderer="Text-to-CAD Viewer",
                artifact_id=ASSEMBLY_ARTIFACT,
                read_only=True,
            ),
            VisualEvidence(
                evidence_id=OVERVIEW_EVIDENCE,
                channel=EvidenceChannel.SNAPSHOT,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=_relative(args.snapshot_overview),
                purpose="Agent-inspected isometric overview from the exact STEP and sidecar.",
                created_at=created_at,
                renderer="Text-to-CAD Snapshot",
                artifact_id=ASSEMBLY_ARTIFACT,
                inspected_by_agent=True,
            ),
            VisualEvidence(
                evidence_id=SECTION_EVIDENCE,
                channel=EvidenceChannel.SNAPSHOT,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=_relative(args.snapshot_section),
                purpose="Agent-inspected joint section from the exact STEP and sidecar.",
                created_at=created_at,
                renderer="Text-to-CAD Snapshot",
                artifact_id=ASSEMBLY_ARTIFACT,
                inspected_by_agent=True,
            ),
        ]
        results.extend(
            (
                assess(
                    requirements["JC-ARTIFACT-SIDECAR"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
                    diagnostic=(
                        "Pinned sidecar embeds assembly STEP SHA-256 "
                        f"{assembly_hash}; "
                        f"sidecar SHA-256 {next(item.sha256 for item in artifacts if item.artifact_id == SIDECAR_ARTIFACT)}."
                    ),
                    evidence_refs=(ASSEMBLY_ARTIFACT, SIDECAR_ARTIFACT),
                ),
                assess(
                    requirements["JC-VIS-VIEWER"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.VIEWER,
                    diagnostic="Read-only Viewer link targets the exact assembly STEP directory and filename.",
                    evidence_refs=(VIEWER_EVIDENCE,),
                ),
                assess(
                    requirements["JC-VIS-SNAPSHOT-ISO"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.SNAPSHOT,
                    diagnostic="Agent inspected the isometric Snapshot and found coherent separated rigid parts.",
                    evidence_refs=(OVERVIEW_EVIDENCE,),
                ),
                assess(
                    requirements["JC-VIS-SNAPSHOT-SECTION"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.SNAPSHOT,
                    diagnostic="Agent inspected the section Snapshot for tongue/groove and gasket placement.",
                    evidence_refs=(SECTION_EVIDENCE,),
                ),
            )
        )

    packet = ReviewPacket(
        packet_id=f"review.joint-coupon-{profile.value}-{metrics.job_id.lower()}",
        contract_id=contract.contract_id,
        contract_fingerprint=contract_digest,
        profile=profile,
        model=contract.model,
        source_fingerprints=sources,
        input_fingerprints=inputs,
        toolchain=_tools(profile),
        artifacts=tuple(artifacts),
        results=tuple(results),
        job_metrics=metrics,
        visual_evidence=tuple(visual),
        confirmed_facts=(
            f"All {profile.value} profile requirements have current PASS evidence.",
            "Dimensions, clearance, interference, and fit claims come from programmatic geometry.",
        ),
        remaining_uncertainty=(
            "The coupon has not been physically printed; material and printer variation remain unverified.",
        ),
        created_at=created_at,
    )
    issues = validate_review_packet(
        packet,
        contract,
        artifact_probe=FileArtifactProbe(ROOT),
    )
    status = profile_status(contract, profile, packet.results)
    if issues or status is not ResultStatus.PASS:
        detail = "\n".join(str(issue) for issue in issues)
        raise ValueError(f"review packet is not complete:\n{detail or status.value}")

    packet_path = OUTPUT_ROOT / f"review-packet-{profile.value}.json"
    packet_path.write_text(review_packet_to_json(packet), encoding="utf-8")
    print(packet_path)


if __name__ == "__main__":
    main()
