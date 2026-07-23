"""Assemble standard review packets from coordinated coupon evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
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
    InspectionAttestation,
    JobMetrics,
    JobOutput,
    ResultStatus,
    ReviewPacket,
    ToolIdentity,
    ToolchainIdentity,
    Unit,
    VerificationProfile,
    ViewerSessionRecord,
    VisualEvidence,
    assess,
    contract_fingerprint,
    fingerprint_collection,
    profile_status,
    review_packet_to_json,
    validate_review_packet,
)
from scripts.cad_verification_io import FileArtifactProbe  # noqa: E402
from workbench.designs.joint_coupon.parameters import load_parameters  # noqa: E402
from workbench.designs.joint_coupon.verification import (  # noqa: E402
    design_contract,
    input_fingerprints as current_input_fingerprints,
    sha256_file,
    source_fingerprints as current_source_fingerprints,
)


OUTPUT_ROOT = ROOT / "build/workbench/joint_coupon"
BUILD_TARGET = "workbench/designs/joint_coupon/build.py"
ARTIFACT_TARGET = "scripts/text_to_cad_artifacts.py"
SNAPSHOT_JOB = "workbench/designs/joint_coupon/snapshot-job.json"
SNAPSHOT_PROVENANCE = "build/workbench/joint_coupon/snapshot-job-provenance.json"
ASSEMBLY_ARTIFACT = "artifact.joint-coupon-assembly-step"
LOWER_ARTIFACT = "artifact.joint-coupon-lower-step"
UPPER_ARTIFACT = "artifact.joint-coupon-upper-step"
SIDECAR_ARTIFACT = "artifact.joint-coupon-topology-sidecar"
OVERVIEW_ARTIFACT = "artifact.joint-coupon-snapshot-isometric"
SECTION_ARTIFACT = "artifact.joint-coupon-snapshot-section"
VIEWER_EVIDENCE = "viewer.joint-coupon-assembly"
OVERVIEW_EVIDENCE = "snapshot.joint-coupon-isometric"
SECTION_EVIDENCE = "snapshot.joint-coupon-section"
MAX_GLB_BYTES = 64 * 1024 * 1024
GLB_JSON_CHUNK = 0x4E4F534A
GLB_BIN_CHUNK = 0x004E4942
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        required=True,
    )
    parser.add_argument("--job-record", type=Path, required=True)
    parser.add_argument("--sidecar-job-record", type=Path)
    parser.add_argument("--snapshot-job-record", type=Path)
    parser.add_argument("--viewer-record", type=Path)
    parser.add_argument("--attestation", type=Path)
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


def _relative(path: Path) -> str:
    resolved = path.expanduser().resolve()
    return resolved.relative_to(ROOT).as_posix()


def _valid_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in value
    )


def _job_metrics(
    payload: dict[str, Any],
    *,
    role: str,
    profile: VerificationProfile,
    expected_name: str,
    expected_target: str,
    expected_arguments: tuple[str, ...],
    expected_outputs: set[str],
) -> JobMetrics:
    if payload.get("name") != expected_name:
        raise ValueError(f"{role} job name mismatch")
    if payload.get("state") != "completed" or payload.get("exit_status") != "completed":
        raise ValueError(f"{role} job did not reach a successful terminal state")
    if payload.get("exit_code") != 0:
        raise ValueError(f"{role} job did not exit 0")
    if (
        payload.get("failure_kind") is not None
        or payload.get("failure_message") is not None
    ):
        raise ValueError(f"{role} job retains a failure diagnostic")
    cleanup = payload.get("cleanup", {})
    owned = cleanup.get("owned_process_group", {})
    remaining = tuple(owned.get("remaining_owned_pids", ()))
    cleanup_completed = (
        cleanup.get("workspace_removed") is True
        and cleanup.get("error") is None
        and owned.get("reaped") is True
        and not remaining
    )
    if not cleanup_completed:
        raise ValueError(f"{role} job cleanup is incomplete")

    raw_command = payload.get("command")
    if not isinstance(raw_command, list):
        raise ValueError(f"{role} job command is malformed")
    expected_suffix = (expected_target, *expected_arguments)
    if len(raw_command) < len(expected_suffix):
        raise ValueError(f"{role} job command is truncated")
    raw_target = Path(str(raw_command[-len(expected_suffix)])).expanduser().resolve()
    if _relative(raw_target) != expected_target:
        raise ValueError(f"{role} job target mismatch")
    if tuple(map(str, raw_command[-len(expected_arguments) :])) != expected_arguments:
        raise ValueError(f"{role} job command arguments mismatch")

    outputs: list[JobOutput] = []
    for record in payload.get("final_outputs", ()):
        relative = str(record.get("relative_path", ""))
        if not _valid_relative_path(relative):
            raise ValueError(f"{role} job contains a non-portable output path")
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"{role} job output is missing: {relative}")
        digest = str(record.get("sha256", ""))
        size = record.get("bytes")
        if digest != sha256_file(path) or size != path.stat().st_size:
            raise ValueError(f"{role} job output content drift: {relative}")
        outputs.append(JobOutput(relative, digest, int(size)))
    actual_outputs = {output.path for output in outputs}
    if actual_outputs != expected_outputs:
        raise ValueError(
            f"{role} job outputs mismatch: expected {sorted(expected_outputs)}, "
            f"found {sorted(actual_outputs)}"
        )

    return JobMetrics(
        role=role,
        job_id=str(payload["job_id"]),
        name=expected_name,
        state=str(payload["state"]),
        target=expected_target,
        profile=profile,
        command=expected_suffix,
        started_at=_datetime(payload["started_at"]),
        finished_at=_datetime(payload["finished_at"]),
        elapsed_seconds=float(payload["elapsed_seconds"]),
        exit_code=int(payload["exit_code"]),
        worker_pid=payload.get("worker_pid"),
        peak_rss_bytes=payload.get("peak_rss_bytes"),
        cleanup_completed=cleanup_completed,
        orphan_processes=len(remaining),
        outputs=tuple(outputs),
    )


def _contains_step_hash(value: Any) -> bool:
    """Reject lookalike hashes outside the canonical metadata field."""

    if isinstance(value, dict):
        return "stepHash" in value or any(
            _contains_step_hash(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_step_hash(item) for item in value)
    return False


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object while rejecting duplicate member names."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _glb_step_hash(path: Path) -> str:
    """Read the one canonical STEP hash from a bounded Text-to-CAD GLB."""

    size = path.stat().st_size
    if size > MAX_GLB_BYTES:
        raise ValueError(f"sidecar exceeds the {MAX_GLB_BYTES}-byte safety cap: {path}")
    payload = path.read_bytes()
    if len(payload) < 12 or payload[:4] != b"glTF":
        raise ValueError(f"sidecar is not a GLB file: {path}")
    version, declared_size = struct.unpack_from("<II", payload, 4)
    if version != 2 or declared_size != len(payload) or declared_size % 4:
        raise ValueError(f"sidecar has an invalid GLB header: {path}")

    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(payload):
        if offset + 8 > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk header: {path}")
        chunk_size, chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        if chunk_size % 4:
            raise ValueError(f"sidecar has an unaligned GLB chunk: {path}")
        end = offset + chunk_size
        if end > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk: {path}")
        chunks.append((chunk_type, payload[offset:end]))
        offset = end
    if (
        len(chunks) != 2
        or chunks[0][0] != GLB_JSON_CHUNK
        or chunks[1][0] != GLB_BIN_CHUNK
    ):
        raise ValueError(
            f"sidecar must contain one JSON chunk followed by one BIN chunk: {path}"
        )

    try:
        document = json.loads(
            chunks[0][1].rstrip(b" \t\r\n\0").decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"sidecar JSON chunk is malformed: {path}") from error
    if not isinstance(document, dict):
        raise ValueError(f"sidecar JSON chunk must be an object: {path}")
    extension = document.get("extensions", {}).get("STEP_topology")
    if not isinstance(extension, dict):
        raise ValueError(f"sidecar lacks the STEP_topology extension: {path}")
    index_view = extension.get("indexView")
    if (
        extension.get("schemaVersion") != 2
        or extension.get("encoding") != "utf-8"
        or not isinstance(index_view, int)
    ):
        raise ValueError(f"sidecar STEP_topology extension is not canonical: {path}")
    views = document.get("bufferViews")
    buffers = document.get("buffers")
    if (
        not isinstance(views, list)
        or not 0 <= index_view < len(views)
        or not isinstance(buffers, list)
        or len(buffers) != 1
        or not isinstance(buffers[0], dict)
    ):
        raise ValueError(f"sidecar index buffer metadata is malformed: {path}")
    view = views[index_view]
    if not isinstance(view, dict) or view.get("buffer") != 0:
        raise ValueError(f"sidecar indexView does not reference buffer 0: {path}")
    byte_offset = view.get("byteOffset", 0)
    byte_length = view.get("byteLength")
    declared_buffer_length = buffers[0].get("byteLength")
    binary = chunks[1][1]
    if (
        not isinstance(byte_offset, int)
        or not isinstance(byte_length, int)
        or not isinstance(declared_buffer_length, int)
        or byte_offset < 0
        or byte_length <= 0
        or declared_buffer_length > len(binary)
        or len(binary) - declared_buffer_length > 3
        or byte_offset + byte_length > declared_buffer_length
    ):
        raise ValueError(f"sidecar indexView bounds are invalid: {path}")
    try:
        metadata = json.loads(
            binary[byte_offset : byte_offset + byte_length].decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"sidecar index metadata is malformed: {path}") from error
    if (
        not isinstance(metadata, dict)
        or metadata.get("schemaVersion") != 2
        or metadata.get("profile") != "index"
        or metadata.get("sourceKind") != "step"
    ):
        raise ValueError(f"sidecar index metadata schema is not canonical: {path}")
    step_hash = metadata.get("stepHash")
    nested_values = (item for key, item in metadata.items() if key != "stepHash")
    if (
        not isinstance(step_hash, str)
        or not SHA256_PATTERN.fullmatch(step_hash)
        or any(_contains_step_hash(item) for item in nested_values)
    ):
        raise ValueError(
            "sidecar must contain exactly one lowercase stepHash at the canonical "
            f"index metadata location: {path}"
        )
    return step_hash


def _glb_step_hashes(path: Path) -> set[str]:
    """Compatibility helper returning the one structurally validated hash."""

    return {_glb_step_hash(path)}


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
            raise ValueError(f"stored status drift for {record['requirement_id']}")
        results.append(result)
    return results


def _require_diagnostics_job(diagnostics: dict[str, Any], job: JobMetrics) -> None:
    expected = {
        "job_id": job.job_id,
        "name": job.name,
        "target": job.target,
        "profile": job.profile.value,
        "command": list(job.command),
    }
    if diagnostics.get("job") != expected:
        raise ValueError("diagnostics are not bound to the production coordinator job")
    if diagnostics.get("status") != "passed" or diagnostics.get(
        "missing_native_requirement_ids"
    ):
        raise ValueError(
            "diagnostics do not represent a complete successful measurement job"
        )


def _require_release_arguments(args: argparse.Namespace) -> None:
    required_arguments = {
        "sidecar job record": args.sidecar_job_record,
        "Snapshot job record": args.snapshot_job_record,
        "Viewer record": args.viewer_record,
        "agent inspection attestation": args.attestation,
        "sidecar": args.sidecar,
        "isometric Snapshot": args.snapshot_overview,
        "section Snapshot": args.snapshot_section,
    }
    missing = [name for name, value in required_arguments.items() if value is None]
    if missing:
        raise ValueError(f"release packet missing: {', '.join(missing)}")


def _artifact_fingerprints_from_record(
    records: list[dict[str, Any]],
    artifacts: tuple[ArtifactEvidence, ...],
) -> tuple[Fingerprint, ...]:
    artifacts_by_path = {artifact.path: artifact for artifact in artifacts}
    fingerprints = []
    for record in records:
        artifact = artifacts_by_path.get(str(record.get("path", "")))
        if artifact is None or record.get("sha256") != artifact.sha256:
            raise ValueError(
                "evidence record references the wrong artifact path or hash"
            )
        fingerprints.append(Fingerprint(artifact.artifact_id, artifact.sha256))
    return tuple(fingerprints)


def _inspection_attestation(
    path: Path,
    artifacts: tuple[ArtifactEvidence, ...],
) -> InspectionAttestation:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fingerprints = _artifact_fingerprints_from_record(
        payload.get("artifacts", []), artifacts
    )
    expected_ids = {
        ASSEMBLY_ARTIFACT,
        SIDECAR_ARTIFACT,
        OVERVIEW_ARTIFACT,
        SECTION_ARTIFACT,
    }
    if {item.subject for item in fingerprints} != expected_ids:
        raise ValueError(
            "inspection attestation must cover the STEP, sidecar, and both rendered PNGs"
        )
    return InspectionAttestation(
        attestation_id=str(payload["attestation_id"]),
        inspector=str(payload["inspector"]),
        inspected_at=_datetime(payload["inspected_at"]),
        statement=str(payload["statement"]),
        artifact_fingerprints=fingerprints,
    )


def _viewer_record(
    path: Path,
    artifacts: tuple[ArtifactEvidence, ...],
) -> ViewerSessionRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fingerprints = _artifact_fingerprints_from_record(
        payload.get("artifacts", []), artifacts
    )
    if {item.subject for item in fingerprints} != {ASSEMBLY_ARTIFACT, SIDECAR_ARTIFACT}:
        raise ValueError("Viewer record must bind the assembly STEP and sidecar")
    server = payload.get("server", {})
    return ViewerSessionRecord(
        record_id=str(payload["record_id"]),
        url=str(payload["url"]),
        recorded_at=_datetime(payload["recorded_at"]),
        server_app=str(server.get("app", "")),
        backend=str(server.get("backend", "")),
        dynamic_root=server.get("dynamicRoot") is True,
        generation_available=server.get("stepArtifactGenerationAvailable") is True,
        viewer_version=str(server.get("viewerVersion", "")),
        artifact_fingerprints=fingerprints,
    )


def _validate_snapshot_provenance(
    job: JobMetrics,
    *,
    overview: Path,
    section: Path,
    assembly: Path,
    sidecar: Path,
) -> None:
    path = ROOT / SNAPSHOT_PROVENANCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("job_id") != job.job_id or payload.get("target") != job.target:
        raise ValueError("Snapshot provenance is not bound to the coordinator job")
    if payload.get("command") != list(job.command):
        raise ValueError("Snapshot provenance command mismatch")
    snapshot_job = payload.get("snapshot_job", {})
    if snapshot_job.get("path") != SNAPSHOT_JOB or snapshot_job.get(
        "sha256"
    ) != sha256_file(ROOT / SNAPSHOT_JOB):
        raise ValueError("Snapshot job specification changed after rendering")
    expected_sources = {
        (_relative(assembly), sha256_file(assembly)),
        (_relative(sidecar), sha256_file(sidecar)),
    }
    actual_sources = {
        (str(item.get("path", "")), str(item.get("sha256", "")))
        for item in payload.get("sources", ())
    }
    if actual_sources != expected_sources:
        raise ValueError("Snapshot source STEP or sidecar hash mismatch")
    expected_outputs = {
        (_relative(overview), sha256_file(overview)),
        (_relative(section), sha256_file(section)),
    }
    actual_outputs = {
        (str(item.get("path", "")), str(item.get("sha256", "")))
        for item in payload.get("outputs", ())
    }
    if actual_outputs != expected_outputs:
        raise ValueError("Snapshot rendered output path or hash mismatch")


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
    requirements = {item.requirement_id: item for item in contract.requirements}
    results = _programmatic_results(diagnostics, requirements)

    production_outputs = {
        "build/workbench/joint_coupon/design-contract.json",
        f"build/workbench/joint_coupon/diagnostics-{profile.value}.json",
    }
    if profile is VerificationProfile.RELEASE:
        production_outputs.update(
            {
                "build/workbench/joint_coupon/diagnostics.json",
                "build/workbench/joint_coupon/joint_coupon_assembly.step",
                "build/workbench/joint_coupon/joint_coupon_gaskets.step",
                "build/workbench/joint_coupon/joint_coupon_lower.step",
                "build/workbench/joint_coupon/joint_coupon_upper.step",
            }
        )
    production = _job_metrics(
        json.loads(args.job_record.read_text(encoding="utf-8")),
        role="job.joint-coupon-production",
        profile=profile,
        expected_name=f"joint-coupon-{profile.value}",
        expected_target=BUILD_TARGET,
        expected_arguments=("--profile", profile.value),
        expected_outputs=production_outputs,
    )
    _require_diagnostics_job(diagnostics, production)

    contract_digest = contract_fingerprint(contract)
    source_digest = fingerprint_collection(sources)
    input_digest = fingerprint_collection(inputs)
    artifacts: tuple[ArtifactEvidence, ...] = ()
    jobs = [production]
    visual: tuple[VisualEvidence, ...] = ()
    attestations: tuple[InspectionAttestation, ...] = ()
    viewer_records: tuple[ViewerSessionRecord, ...] = ()

    if profile is VerificationProfile.RELEASE:
        _require_release_arguments(args)
        assert args.sidecar is not None
        assert args.snapshot_overview is not None
        assert args.snapshot_section is not None
        sidecar = _job_metrics(
            json.loads(args.sidecar_job_record.read_text(encoding="utf-8")),
            role="job.joint-coupon-sidecar",
            profile=profile,
            expected_name="text_to_cad_artifacts",
            expected_target=ARTIFACT_TARGET,
            expected_arguments=(
                "sidecar",
                "build/workbench/joint_coupon/joint_coupon_assembly.step",
                "--kind",
                "assembly",
                "--force",
            ),
            expected_outputs={_relative(args.sidecar)},
        )
        snapshot_outputs = {
            _relative(args.snapshot_overview),
            _relative(args.snapshot_section),
            SNAPSHOT_PROVENANCE,
        }
        snapshot = _job_metrics(
            json.loads(args.snapshot_job_record.read_text(encoding="utf-8")),
            role="job.joint-coupon-snapshot",
            profile=profile,
            expected_name="text_to_cad_artifacts",
            expected_target=ARTIFACT_TARGET,
            expected_arguments=("snapshot", "--job", SNAPSHOT_JOB, "--json"),
            expected_outputs=snapshot_outputs,
        )
        jobs.extend((sidecar, snapshot))

        artifact_specs = (
            (
                ASSEMBLY_ARTIFACT,
                OUTPUT_ROOT / "joint_coupon_assembly.step",
                "model/step",
            ),
            (LOWER_ARTIFACT, OUTPUT_ROOT / "joint_coupon_lower.step", "model/step"),
            (UPPER_ARTIFACT, OUTPUT_ROOT / "joint_coupon_upper.step", "model/step"),
            (
                "artifact.joint-coupon-gaskets-step",
                OUTPUT_ROOT / "joint_coupon_gaskets.step",
                "model/step",
            ),
            (SIDECAR_ARTIFACT, args.sidecar, "model/gltf-binary"),
            (OVERVIEW_ARTIFACT, args.snapshot_overview, "image/png"),
            (SECTION_ARTIFACT, args.snapshot_section, "image/png"),
        )
        artifacts = tuple(
            _artifact(
                artifact_id,
                path,
                media_type,
                contract_digest=contract_digest,
                source_digest=source_digest,
                input_digest=input_digest,
            )
            for artifact_id, path, media_type in artifact_specs
        )
        by_id = {artifact.artifact_id: artifact for artifact in artifacts}
        assembly_hash = by_id[ASSEMBLY_ARTIFACT].sha256
        if _glb_step_hash(args.sidecar) != assembly_hash:
            raise ValueError("sidecar does not embed the current assembly STEP SHA-256")
        _validate_snapshot_provenance(
            snapshot,
            overview=args.snapshot_overview,
            section=args.snapshot_section,
            assembly=OUTPUT_ROOT / "joint_coupon_assembly.step",
            sidecar=args.sidecar,
        )
        attestation = _inspection_attestation(args.attestation, artifacts)
        viewer_record = _viewer_record(args.viewer_record, artifacts)
        attestations = (attestation,)
        viewer_records = (viewer_record,)
        created_at = datetime.now(timezone.utc)
        visual = (
            VisualEvidence(
                evidence_id=VIEWER_EVIDENCE,
                channel=EvidenceChannel.VIEWER,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=viewer_record.url,
                purpose="Interactive inspection of the exact assembly STEP and sidecar.",
                created_at=viewer_record.recorded_at,
                renderer="Text-to-CAD Viewer",
                artifact_id=ASSEMBLY_ARTIFACT,
                source_artifact_ids=(SIDECAR_ARTIFACT,),
                viewer_record_id=viewer_record.record_id,
                read_only=True,
            ),
            VisualEvidence(
                evidence_id=OVERVIEW_EVIDENCE,
                channel=EvidenceChannel.SNAPSHOT,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=by_id[OVERVIEW_ARTIFACT].path,
                purpose="Agent-inspected isometric overview from the exact STEP and sidecar.",
                created_at=attestation.inspected_at,
                renderer="Text-to-CAD Snapshot",
                artifact_id=OVERVIEW_ARTIFACT,
                source_artifact_ids=(ASSEMBLY_ARTIFACT, SIDECAR_ARTIFACT),
                attestation_id=attestation.attestation_id,
            ),
            VisualEvidence(
                evidence_id=SECTION_EVIDENCE,
                channel=EvidenceChannel.SNAPSHOT,
                scope=EvidenceScope.EXPORTED_ARTIFACT,
                locator=by_id[SECTION_ARTIFACT].path,
                purpose="Agent-inspected joint section from the exact STEP and sidecar.",
                created_at=attestation.inspected_at,
                renderer="Text-to-CAD Snapshot",
                artifact_id=SECTION_ARTIFACT,
                source_artifact_ids=(ASSEMBLY_ARTIFACT, SIDECAR_ARTIFACT),
                attestation_id=attestation.attestation_id,
            ),
        )
        results.extend(
            (
                assess(
                    requirements["JC-ARTIFACT-SIDECAR"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.PROGRAMMATIC_GEOMETRY,
                    diagnostic=(
                        "Canonical Text-to-CAD index metadata embeds assembly STEP SHA-256 "
                        f"{assembly_hash}."
                    ),
                    evidence_refs=(ASSEMBLY_ARTIFACT, SIDECAR_ARTIFACT),
                ),
                assess(
                    requirements["JC-VIS-VIEWER"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.VIEWER,
                    diagnostic="Probed read-only Viewer record targets the exact STEP and sidecar hashes.",
                    evidence_refs=(VIEWER_EVIDENCE,),
                ),
                assess(
                    requirements["JC-VIS-SNAPSHOT-ISO"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.SNAPSHOT,
                    diagnostic="Explicit agent attestation covers the rendered isometric PNG and its sources.",
                    evidence_refs=(OVERVIEW_EVIDENCE,),
                ),
                assess(
                    requirements["JC-VIS-SNAPSHOT-SECTION"],
                    ActualValue(True, Unit.BOOLEAN),
                    evidence_channel=EvidenceChannel.SNAPSHOT,
                    diagnostic="Explicit agent attestation covers the rendered section PNG and its sources.",
                    evidence_refs=(SECTION_EVIDENCE,),
                ),
            )
        )
    else:
        created_at = datetime.now(timezone.utc)

    packet = ReviewPacket(
        packet_id=f"review.joint-coupon-{profile.value}-{production.job_id.lower()}",
        contract_id=contract.contract_id,
        contract_fingerprint=contract_digest,
        profile=profile,
        model=contract.model,
        source_fingerprints=sources,
        input_fingerprints=inputs,
        toolchain=_tools(profile),
        artifacts=artifacts,
        results=tuple(results),
        jobs=tuple(jobs),
        visual_evidence=visual,
        inspection_attestations=attestations,
        viewer_records=viewer_records,
        confirmed_facts=(
            f"All {profile.value} profile requirements have current PASS evidence.",
            "Dimensions, clearance, interference, and fit claims come from programmatic geometry.",
        ),
        remaining_uncertainty=(
            "The coupon has not been physically printed; material and printer variation remain unverified.",
            "Installed native tool binaries are identified by project pins, not independently attested binaries.",
        ),
        created_at=created_at,
    )
    issues = validate_review_packet(
        packet, contract, artifact_probe=FileArtifactProbe(ROOT)
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
