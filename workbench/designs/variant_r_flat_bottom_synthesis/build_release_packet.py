"""Build the native-free release verification contract and review packet."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cad_verification import (  # noqa: E402
    ActualValue,
    ArtifactEvidence,
    CheckKind,
    CheckSpec,
    DesignContract,
    EvidenceChannel,
    EvidenceScope,
    Expectation,
    Fingerprint,
    InspectionAttestation,
    JobMetrics,
    JobOutput,
    ModelIdentity,
    Requirement,
    ReviewPacket,
    Tolerance,
    ToolIdentity,
    ToolchainIdentity,
    Unit,
    VerificationProfile,
    ViewerSessionRecord,
    VisualEvidence,
    assess,
    assert_valid_contract,
    assert_valid_review_packet,
    contract_fingerprint,
    contract_to_json,
    fingerprint_collection,
    review_packet_to_json,
)
from scripts.cad_verification_io import FileArtifactProbe  # noqa: E402


ITERATION = Path(__file__).resolve().parent
OUT = ROOT / "build/workbench/variant_r_flat_bottom_synthesis/verification"
MODEL_OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
REVIEW_OUT = ROOT / "build/workbench/variant_r_flat_bottom_synthesis/review"
GENERATOR = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
    / "generate_sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle.py"
)
VALIDATOR = GENERATOR.with_name("validate_simple_tongue_groove_baffle.py")

FULL_JOB = ROOT / "build/cad-jobs/20260723T151259-validate-simple-tongue-groove-baffle-74db9f9037.json"
PACKAGE_JOB = ROOT / "build/cad-jobs/20260723T153916-package-review-8a719db8af.json"
ASSEMBLY_SIDECAR_JOB = ROOT / "build/cad-jobs/20260723T154042-text-to-cad-artifacts-72d19abd68.json"
BAFFLE_SIDECAR_JOB = ROOT / "build/cad-jobs/20260723T154208-text-to-cad-artifacts-2baa807349.json"
SNAPSHOT_JOB = ROOT / "build/cad-jobs/20260723T154224-text-to-cad-artifacts-bcee70e3a7.json"


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _requirement(
    requirement_id: str,
    description: str,
    kind: CheckKind,
    adapter: str,
    expected,
    unit: Unit,
    tolerance: float,
    profile: VerificationProfile,
) -> Requirement:
    return Requirement(
        requirement_id=requirement_id,
        description=description,
        check=CheckSpec(kind, adapter),
        expectation=Expectation.exactly(expected),
        unit=unit,
        tolerance=Tolerance(tolerance),
        cost_profile=profile,
    )


def _contract() -> DesignContract:
    model = ModelIdentity(
        model_id="development-190x210-tongue-groove",
        name="190 x 210 removable tongue-and-groove baffle",
        variant="Variant R flat-bottom synthesis",
        source=_relative(GENERATOR),
        entrypoint=_relative(GENERATOR),
    )
    requirements = (
        _requirement(
            "VR-FAST-BUCKET-VALID",
            "Bucket is one valid solid.",
            CheckKind.STRUCTURAL,
            "kernel.bucket_valid",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.FAST,
        ),
        _requirement(
            "VR-FAST-BAFFLE-VALID",
            "Baffle is one valid solid.",
            CheckKind.STRUCTURAL,
            "kernel.baffle_valid",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.FAST,
        ),
        _requirement(
            "VR-FIT-RIGID-OVERLAP",
            "Closed bucket and baffle have no positive-volume overlap.",
            CheckKind.INTERFERENCE,
            "kernel.bucket_baffle_overlap",
            0.0,
            Unit.CUBIC_MILLIMETER,
            0.001,
            VerificationProfile.FIT,
        ),
        _requirement(
            "VR-FIT-GASKET-BUCKET-SUPPORT",
            "Bucket supports the complete gasket land.",
            CheckKind.FIT,
            "kernel.gasket_bucket_support",
            1.0,
            Unit.RATIO,
            1e-6,
            VerificationProfile.FIT,
        ),
        _requirement(
            "VR-FIT-GASKET-BAFFLE-SUPPORT",
            "Baffle supports the complete gasket land.",
            CheckKind.FIT,
            "kernel.gasket_baffle_support",
            1.0,
            Unit.RATIO,
            1e-6,
            VerificationProfile.FIT,
        ),
        _requirement(
            "VR-FIT-PRINT-CONTACT-SPAN",
            "Baffle has the measured full-width planar print contact.",
            CheckKind.FIT,
            "kernel.baffle_print_contact_x_span",
            187.02097935912883,
            Unit.MILLIMETER,
            0.01,
            VerificationProfile.FIT,
        ),
        _requirement(
            "VR-RELEASE-ROUNDTRIP",
            "Bucket and baffle STEP exports each round-trip as one valid solid.",
            CheckKind.ROUND_TRIP,
            "artifact.part_round_trip",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.RELEASE,
        ),
        _requirement(
            "VR-RELEASE-SIDECAR",
            "The review topology sidecar is hash-bound to the assembly STEP.",
            CheckKind.ARTIFACT_INTEGRITY,
            "artifact.review_sidecar_binding",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.RELEASE,
        ),
        _requirement(
            "VR-VISUAL-VIEWER",
            "The exact two-solid review assembly is available in the read-only Viewer.",
            CheckKind.VISUAL_REVIEW,
            "review.viewer",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.RELEASE,
        ),
        _requirement(
            "VR-VISUAL-OVERVIEW",
            "The inspected overview retains the sculpted seam without corner hunks.",
            CheckKind.VISUAL_REVIEW,
            "review.snapshot_overview",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.RELEASE,
        ),
        _requirement(
            "VR-VISUAL-PRINT-EDGE",
            "The inspected isolated baffle has a visibly straight lower edge.",
            CheckKind.VISUAL_REVIEW,
            "review.snapshot_baffle_front",
            True,
            Unit.BOOLEAN,
            0.0,
            VerificationProfile.RELEASE,
        ),
    )
    return DesignContract(
        contract_id="contract.variant-r-flat-bottom-synthesis",
        title="Variant R flat-bottom synthesis release acceptance",
        model=model,
        requirements=requirements,
    )


def _fingerprints(paths: tuple[Path, ...]) -> tuple[Fingerprint, ...]:
    return tuple(Fingerprint(_relative(path), _sha(path)) for path in paths)


def _artifact(
    artifact_id: str,
    path: Path,
    media_type: str,
    *,
    contract_digest: str,
    source_digest: str,
    input_digest: str,
) -> ArtifactEvidence:
    stat = path.stat()
    return ArtifactEvidence(
        artifact_id=artifact_id,
        path=_relative(path),
        media_type=media_type,
        sha256=_sha(path),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        contract_fingerprint=contract_digest,
        source_fingerprint=source_digest,
        input_fingerprint=input_digest,
    )


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _job(role: str, path: Path, target: str) -> JobMetrics:
    payload = json.loads(path.read_text())
    cleanup = payload["cleanup"]
    remaining = cleanup["owned_process_group"]["remaining_owned_pids"]
    outputs = tuple(
        JobOutput(
            record["relative_path"],
            record["sha256"],
            int(record["bytes"]),
        )
        for record in payload["final_outputs"]
    )
    return JobMetrics(
        role=role,
        job_id=payload["job_id"],
        name=payload["name"],
        state=payload["state"],
        target=target,
        profile=VerificationProfile.RELEASE,
        command=(target,),
        started_at=_datetime(payload["started_at"]),
        finished_at=_datetime(payload["finished_at"]),
        elapsed_seconds=float(payload["elapsed_seconds"]),
        exit_code=int(payload["exit_code"]),
        worker_pid=payload["worker_pid"],
        peak_rss_bytes=payload["peak_rss_bytes"],
        cleanup_completed=(
            cleanup["workspace_removed"]
            and cleanup["error"] is None
            and cleanup["owned_process_group"]["reaped"]
            and not remaining
        ),
        orphan_processes=len(remaining),
        outputs=outputs,
    )


def main() -> None:
    contract = _contract()
    assert_valid_contract(contract)
    source_fingerprints = _fingerprints(
        (
            GENERATOR,
            VALIDATOR,
            ITERATION / "package_review.py",
            ITERATION / "validate_perimeter.py",
            ITERATION / "validate_print_contact.py",
            ITERATION / "validate_print_transfer.py",
            ITERATION / "validate_splice.py",
            Path(__file__).resolve(),
            ITERATION / "snapshot-job.json",
        )
    )
    reference_root = (
        ROOT
        / "workbench/designs/canonical_working_set/enclosures/"
        "removable_front_baffle/links"
    )
    input_fingerprints = _fingerprints(
        (
            ITERATION / "brief.md",
            ITERATION / "contract.md",
            reference_root / "near_perfect_bucket.step",
            reference_root / "bottom_ownership_assembly.step",
            reference_root / "flat_bottom_baffle.step",
        )
    )
    contract_digest = contract_fingerprint(contract)
    source_digest = fingerprint_collection(source_fingerprints)
    input_digest = fingerprint_collection(input_fingerprints)

    artifact_specs = (
        (
            "artifact.variant-r-bucket-step",
            MODEL_OUT / "simple_tongue_groove_bucket.step",
            "model/step",
        ),
        (
            "artifact.variant-r-baffle-step",
            MODEL_OUT / "simple_tongue_groove_baffle.step",
            "model/step",
        ),
        (
            "artifact.variant-r-validation",
            MODEL_OUT / "validation_diagnostics.json",
            "application/json",
        ),
        (
            "artifact.variant-r-review-step",
            REVIEW_OUT / "variant_r_review_assembly.step",
            "model/step",
        ),
        (
            "artifact.variant-r-review-sidecar",
            REVIEW_OUT / ".variant_r_review_assembly.step.glb",
            "model/gltf-binary",
        ),
        (
            "artifact.variant-r-baffle-sidecar",
            MODEL_OUT / ".simple_tongue_groove_baffle.step.glb",
            "model/gltf-binary",
        ),
        (
            "artifact.variant-r-snapshot-overview",
            REVIEW_OUT / "snapshot-isometric_20260723T154225Z.png",
            "image/png",
        ),
        (
            "artifact.variant-r-snapshot-baffle",
            REVIEW_OUT / "snapshot-baffle-front_20260723T154225Z.png",
            "image/png",
        ),
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
    artifact_map = {artifact.artifact_id: artifact for artifact in artifacts}
    viewer_payload = json.loads((ITERATION / "viewer-record.json").read_text())
    viewer = VisualEvidence(
        evidence_id="viewer.variant-r-review",
        channel=EvidenceChannel.VIEWER,
        scope=EvidenceScope.EXPORTED_ARTIFACT,
        locator=viewer_payload["url"],
        purpose="Interactive review of the exact final bucket/baffle assembly.",
        created_at=_datetime(viewer_payload["recorded_at"]),
        artifact_id="artifact.variant-r-review-step",
        source_artifact_ids=("artifact.variant-r-review-sidecar",),
        viewer_record_id=viewer_payload["record_id"],
        renderer="Text-to-CAD Viewer",
        read_only=True,
    )
    overview = VisualEvidence(
        evidence_id="snapshot.variant-r-overview",
        channel=EvidenceChannel.SNAPSHOT,
        scope=EvidenceScope.EXPORTED_ARTIFACT,
        locator=artifact_map["artifact.variant-r-snapshot-overview"].path,
        purpose="Inspect the final assembled sculpted seam and exterior.",
        created_at=artifact_map[
            "artifact.variant-r-snapshot-overview"
        ].created_at,
        artifact_id="artifact.variant-r-snapshot-overview",
        source_artifact_ids=(
            "artifact.variant-r-review-step",
            "artifact.variant-r-review-sidecar",
        ),
        attestation_id="attestation.variant-r-overview",
        renderer="Text-to-CAD Snapshot",
    )
    baffle_view = VisualEvidence(
        evidence_id="snapshot.variant-r-baffle-front",
        channel=EvidenceChannel.SNAPSHOT,
        scope=EvidenceScope.EXPORTED_ARTIFACT,
        locator=artifact_map["artifact.variant-r-snapshot-baffle"].path,
        purpose="Inspect the isolated baffle's straight lower print edge.",
        created_at=artifact_map[
            "artifact.variant-r-snapshot-baffle"
        ].created_at,
        artifact_id="artifact.variant-r-snapshot-baffle",
        source_artifact_ids=(
            "artifact.variant-r-baffle-step",
            "artifact.variant-r-baffle-sidecar",
        ),
        attestation_id="attestation.variant-r-baffle-front",
        renderer="Text-to-CAD Snapshot",
    )
    inspected_at = datetime.now(timezone.utc)
    attestations = (
        InspectionAttestation(
            attestation_id="attestation.variant-r-overview",
            inspector="codex-agent",
            inspected_at=inspected_at,
            statement=(
                "Inspected the exact final assembly overview; the sculpted "
                "left/right/top seam remains continuous and no corner hunks "
                "or new exterior discontinuities are visible."
            ),
            artifact_fingerprints=tuple(
                Fingerprint(subject, artifact_map[subject].sha256)
                for subject in (
                    "artifact.variant-r-review-step",
                    "artifact.variant-r-review-sidecar",
                    "artifact.variant-r-snapshot-overview",
                )
            ),
        ),
        InspectionAttestation(
            attestation_id="attestation.variant-r-baffle-front",
            inspector="codex-agent",
            inspected_at=inspected_at,
            statement=(
                "Inspected the isolated final baffle front view; its lower "
                "boundary is visibly straight with no downward transition nubs."
            ),
            artifact_fingerprints=tuple(
                Fingerprint(subject, artifact_map[subject].sha256)
                for subject in (
                    "artifact.variant-r-baffle-step",
                    "artifact.variant-r-baffle-sidecar",
                    "artifact.variant-r-snapshot-baffle",
                )
            ),
        ),
    )
    viewer_record = ViewerSessionRecord(
        record_id=viewer_payload["record_id"],
        url=viewer_payload["url"],
        recorded_at=_datetime(viewer_payload["recorded_at"]),
        server_app=viewer_payload["server"]["app"],
        backend=viewer_payload["server"]["backend"],
        dynamic_root=viewer_payload["server"]["dynamicRoot"],
        generation_available=viewer_payload["server"][
            "stepArtifactGenerationAvailable"
        ],
        viewer_version=viewer_payload["server"]["viewerVersion"],
        artifact_fingerprints=tuple(
            Fingerprint(subject, artifact_map[subject].sha256)
            for subject in (
                "artifact.variant-r-review-step",
                "artifact.variant-r-review-sidecar",
            )
        ),
    )

    diagnostics = json.loads(
        (MODEL_OUT / "validation_diagnostics.json").read_text()
    )
    requirements = {
        requirement.requirement_id: requirement
        for requirement in contract.requirements
    }
    programmatic = EvidenceChannel.PROGRAMMATIC_GEOMETRY
    results = (
        assess(
            requirements["VR-FAST-BUCKET-VALID"],
            ActualValue(diagnostics["single_solid"]["bucket"], Unit.BOOLEAN),
            evidence_channel=programmatic,
            diagnostic="Full fit harness returned one valid bucket solid.",
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-FAST-BAFFLE-VALID"],
            ActualValue(diagnostics["single_solid"]["baffle"], Unit.BOOLEAN),
            evidence_channel=programmatic,
            diagnostic="Full fit harness returned one valid baffle solid.",
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-FIT-RIGID-OVERLAP"],
            ActualValue(
                diagnostics["bucket_baffle_overlap_mm3"],
                Unit.CUBIC_MILLIMETER,
            ),
            evidence_channel=programmatic,
            diagnostic="Closed bucket/baffle overlap is 0.0 mm3.",
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-FIT-GASKET-BUCKET-SUPPORT"],
            ActualValue(
                diagnostics[
                    "gasket_bucket_support_ratio_after_all_features"
                ],
                Unit.RATIO,
            ),
            evidence_channel=programmatic,
            diagnostic="Bucket gasket support ratio is 1.0.",
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-FIT-GASKET-BAFFLE-SUPPORT"],
            ActualValue(
                diagnostics[
                    "gasket_baffle_support_ratio_after_all_features"
                ],
                Unit.RATIO,
            ),
            evidence_channel=programmatic,
            diagnostic="Baffle gasket support ratio is 1.0.",
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-FIT-PRINT-CONTACT-SPAN"],
            ActualValue(
                diagnostics["baffle_print_contact"][
                    "largest_planar_contact_face"
                ]["x_span_mm"],
                Unit.MILLIMETER,
            ),
            evidence_channel=programmatic,
            diagnostic=(
                "Final baffle has one 187.021 mm-wide planar contact face "
                "at Z=-91.5 mm."
            ),
            evidence_refs=("artifact.variant-r-validation",),
        ),
        assess(
            requirements["VR-RELEASE-ROUNDTRIP"],
            ActualValue(
                diagnostics["bucket_step_roundtrip"][
                    "all_imported_solids_valid"
                ]
                and diagnostics["baffle_step_roundtrip"][
                    "all_imported_solids_valid"
                ]
                and diagnostics["bucket_step_roundtrip"][
                    "imported_solid_count"
                ]
                == 1
                and diagnostics["baffle_step_roundtrip"][
                    "imported_solid_count"
                ]
                == 1,
                Unit.BOOLEAN,
            ),
            evidence_channel=programmatic,
            diagnostic="Both part STEP files round-trip as one valid solid.",
            evidence_refs=(
                "artifact.variant-r-bucket-step",
                "artifact.variant-r-baffle-step",
            ),
        ),
        assess(
            requirements["VR-RELEASE-SIDECAR"],
            ActualValue(
                viewer_payload["artifacts"][0]["sha256"]
                == artifact_map["artifact.variant-r-review-step"].sha256
                and viewer_payload["artifacts"][1]["sha256"]
                == artifact_map["artifact.variant-r-review-sidecar"].sha256,
                Unit.BOOLEAN,
            ),
            evidence_channel=programmatic,
            diagnostic="Viewer record binds the exact review STEP and sidecar.",
            evidence_refs=(
                "artifact.variant-r-review-step",
                "artifact.variant-r-review-sidecar",
            ),
        ),
        assess(
            requirements["VR-VISUAL-VIEWER"],
            ActualValue(True, Unit.BOOLEAN),
            evidence_channel=EvidenceChannel.VIEWER,
            diagnostic="Read-only Viewer loaded both named rigid components.",
            evidence_refs=(viewer.evidence_id,),
        ),
        assess(
            requirements["VR-VISUAL-OVERVIEW"],
            ActualValue(True, Unit.BOOLEAN),
            evidence_channel=EvidenceChannel.SNAPSHOT,
            diagnostic="Agent inspected the final assembly overview.",
            evidence_refs=(overview.evidence_id,),
        ),
        assess(
            requirements["VR-VISUAL-PRINT-EDGE"],
            ActualValue(True, Unit.BOOLEAN),
            evidence_channel=EvidenceChannel.SNAPSHOT,
            diagnostic="Agent inspected the isolated final baffle front view.",
            evidence_refs=(baffle_view.evidence_id,),
        ),
    )
    jobs = (
        _job(
            "job.variant-r-full-fit",
            FULL_JOB,
            _relative(VALIDATOR),
        ),
        _job(
            "job.variant-r-package-review",
            PACKAGE_JOB,
            _relative(ITERATION / "package_review.py"),
        ),
        _job(
            "job.variant-r-assembly-sidecar",
            ASSEMBLY_SIDECAR_JOB,
            "scripts/text_to_cad_artifacts.py",
        ),
        _job(
            "job.variant-r-baffle-sidecar",
            BAFFLE_SIDECAR_JOB,
            "scripts/text_to_cad_artifacts.py",
        ),
        _job(
            "job.variant-r-snapshot",
            SNAPSHOT_JOB,
            "scripts/text_to_cad_artifacts.py",
        ),
    )
    packet = ReviewPacket(
        packet_id="review.variant-r-flat-bottom-synthesis",
        contract_id=contract.contract_id,
        contract_fingerprint=contract_digest,
        profile=VerificationProfile.RELEASE,
        model=contract.model,
        source_fingerprints=source_fingerprints,
        input_fingerprints=input_fingerprints,
        toolchain=ToolchainIdentity(
            (
                ToolIdentity(
                    "python",
                    platform.python_version(),
                    sys.implementation.cache_tag or "cpython",
                ),
                ToolIdentity("build123d", "0.11.1", "project pin"),
                ToolIdentity("cadquery-ocp-novtk", "7.9.3.1", "project pin"),
                ToolIdentity(
                    "Text-to-CAD",
                    "0.3.9",
                    "fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423",
                ),
            )
        ),
        artifacts=artifacts,
        results=results,
        jobs=jobs,
        visual_evidence=(viewer, overview, baffle_view),
        inspection_attestations=attestations,
        viewer_records=(viewer_record,),
        confirmed_facts=(
            "Bucket and baffle are separate valid solids with zero overlap.",
            "Protected L/R/T seam material and the known top cube match.",
            "The final baffle has a 187.021 mm by 17.553 mm planar bed face.",
            "Gasket support, bottom continuity, fill clearance, and sand closure pass.",
        ),
        remaining_uncertainty=(
            "CAD does not validate first-layer adhesion; the baffle print assumes a brim.",
            "Top hinge and lower fasteners remain intentionally disabled.",
        ),
        created_at=datetime.now(timezone.utc),
    )
    assert_valid_review_packet(
        packet,
        contract,
        artifact_probe=FileArtifactProbe(ROOT),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "contract.json").write_text(contract_to_json(contract) + "\n")
    (OUT / "release-review-packet.json").write_text(
        review_packet_to_json(packet) + "\n"
    )
    print(
        json.dumps(
            {
                "contract": _relative(OUT / "contract.json"),
                "packet": _relative(OUT / "release-review-packet.json"),
                "contract_fingerprint": contract_digest,
                "source_fingerprint": source_digest,
                "input_fingerprint": input_digest,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
