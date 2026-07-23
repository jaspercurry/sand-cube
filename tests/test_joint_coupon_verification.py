from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import replace
import argparse
from hashlib import sha256
from unittest.mock import patch

import pytest

from cad_verification import (
    VerificationProfile,
    requirements_for_profile,
    validate_contract,
)
from workbench.designs.joint_coupon.parameters import load_parameters
from workbench.designs.joint_coupon.parameters import expected_volumes
from workbench.designs.joint_coupon.verification import (
    SOURCE_PATHS,
    design_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def test_joint_coupon_contract_uses_the_cataloged_owner_and_entrypoint() -> None:
    with (ROOT / ".cad-project/models.toml").open("rb") as stream:
        catalog = tomllib.load(stream)
    record = next(model for model in catalog["models"] if model["id"] == "joint-coupon")
    _, parameters = load_parameters()
    contract = design_contract(parameters)

    assert validate_contract(contract) == ()
    assert contract.model.model_id == record["id"]
    assert contract.model.source == record["source"]
    assert contract.model.entrypoint == record["entrypoint"]


def test_joint_coupon_profiles_add_only_their_intended_cost_layers() -> None:
    _, parameters = load_parameters()
    contract = design_contract(parameters)
    fast = requirements_for_profile(contract, VerificationProfile.FAST)
    fit = requirements_for_profile(contract, VerificationProfile.FIT)
    release = requirements_for_profile(contract, VerificationProfile.RELEASE)

    assert len(fast) == 8
    assert len(fit) == 25
    assert len(release) == 36
    assert {item.cost_profile for item in fit[len(fast) :]} == {VerificationProfile.FIT}
    assert {item.cost_profile for item in release[len(fit) :]} == {
        VerificationProfile.RELEASE
    }


def test_joint_coupon_contract_import_is_native_free() -> None:
    program = (
        "from workbench.designs.joint_coupon.verification import design_contract; "
        "from workbench.designs.joint_coupon.parameters import load_parameters; "
        "import sys; _, p=load_parameters(); design_contract(p); "
        "forbidden=('build123d','OCP','cad_runner'); "
        "loaded=[name for name in sys.modules if name.split('.')[0] in forbidden]; "
        "assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_release_snapshot_recipe_is_tracked_and_source_fingerprinted() -> None:
    recipe = ROOT / "workbench/designs/joint_coupon/snapshot-job.json"
    payload = json.loads(recipe.read_text(encoding="utf-8"))

    assert recipe in SOURCE_PATHS
    assert payload["provenanceOutput"] == (
        "build/workbench/joint_coupon/snapshot-job-provenance.json"
    )
    assert [job["mode"] for job in payload["jobs"]] == ["view", "section"]
    assert payload["jobs"][1]["section"] == {"plane": "YZ", "offset": 0.0}


def _canonical_glb(
    metadata: dict | bytes,
    *,
    unrelated_binary: bytes = b"",
    document_update: dict | None = None,
) -> bytes:
    metadata_bytes = (
        metadata
        if isinstance(metadata, bytes)
        else json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    )
    binary_length = len(metadata_bytes) + len(unrelated_binary)
    binary = metadata_bytes + unrelated_binary
    binary += b"\0" * (-len(binary) % 4)
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": binary_length}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(metadata_bytes)}
        ],
        "extensionsUsed": ["STEP_topology"],
        "extensions": {
            "STEP_topology": {
                "schemaVersion": 2,
                "entryKind": "assembly",
                "indexView": 0,
                "encoding": "utf-8",
            }
        },
    }
    document.update(document_update or {})
    document_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
    document_bytes += b" " * (-len(document_bytes) % 4)
    size = 12 + 8 + len(document_bytes) + 8 + len(binary)
    return (
        b"glTF"
        + struct.pack("<II", 2, size)
        + struct.pack("<II", len(document_bytes), 0x4E4F534A)
        + document_bytes
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


def _metadata(step_hash: str | None = "a" * 64) -> dict:
    result = {
        "schemaVersion": 2,
        "profile": "index",
        "entryKind": "assembly",
        "sourceKind": "step",
        "sourcePath": "joint_coupon_assembly.step",
        "stepPath": "joint_coupon_assembly.step",
    }
    if step_hash is not None:
        result["stepHash"] = step_hash
    return result


def _read_glb(payload: bytes) -> set[str]:
    from workbench.designs.joint_coupon.packet import _glb_step_hashes

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sidecar.glb"
        path.write_bytes(payload)
        return _glb_step_hashes(path)


def test_sidecar_binding_reader_follows_the_real_index_view_schema() -> None:
    step_hash = "a" * 64

    assert _read_glb(_canonical_glb(_metadata(step_hash))) == {step_hash}


def test_sidecar_reader_ignores_unrelated_bin_strings() -> None:
    unrelated = b'"stepHash":"' + b"b" * 64 + b'"'

    assert _read_glb(
        _canonical_glb(_metadata("a" * 64), unrelated_binary=unrelated)
    ) == {"a" * 64}


def test_sidecar_reader_rejects_nested_only_hash() -> None:
    nested_only = {**_metadata(None), "unrelated": {"stepHash": "a" * 64}}

    with pytest.raises(ValueError, match="canonical index metadata location"):
        _read_glb(_canonical_glb(nested_only))


def test_sidecar_reader_rejects_raw_duplicate_step_hash_keys() -> None:
    metadata = json.dumps(_metadata("a" * 64), separators=(",", ":")).encode()
    duplicate = metadata[:-1] + b',"stepHash":"' + b"b" * 64 + b'"}'

    with pytest.raises(ValueError, match="duplicate JSON object key: stepHash"):
        _read_glb(_canonical_glb(duplicate))


@pytest.mark.parametrize(
    "payload_factory",
    (
        lambda: _canonical_glb(_metadata(None)),
        lambda: _canonical_glb(
            {**_metadata("a" * 64), "duplicate": {"stepHash": "b" * 64}}
        ),
        lambda: _canonical_glb(_metadata("A" * 64)),
        lambda: _canonical_glb(_metadata("a" * 63)),
    ),
)
def test_sidecar_reader_rejects_missing_duplicate_or_noncanonical_hashes(
    payload_factory,
) -> None:
    with pytest.raises(ValueError):
        _read_glb(payload_factory())


def test_sidecar_reader_rejects_truncation_and_malformed_chunks() -> None:
    valid = _canonical_glb(_metadata())
    malformed = bytearray(valid)
    document_length = struct.unpack_from("<I", malformed, 12)[0]
    struct.pack_into("<I", malformed, 12, document_length - 1)

    for payload in (valid[:-1], bytes(malformed)):
        with pytest.raises(ValueError):
            _read_glb(payload)


def test_sidecar_reader_applies_a_pre_read_size_cap() -> None:
    from workbench.designs.joint_coupon.packet import _glb_step_hashes

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "oversized.glb"
        path.write_bytes(_canonical_glb(_metadata()))
        with patch(
            "workbench.designs.joint_coupon.packet.MAX_GLB_BYTES",
            path.stat().st_size - 1,
        ):
            with pytest.raises(ValueError, match="safety cap"):
                _glb_step_hashes(path)


def test_expected_volumes_use_each_plate_thickness_for_its_holes() -> None:
    _, params = load_parameters()
    unequal = replace(params, lower_thickness=4.0, upper_thickness=7.0)
    volumes = expected_volumes(unequal)
    hole_area = 4.0 * 3.141592653589793 * (unequal.fastener_diameter / 2.0) ** 2

    assert volumes["lower"] == pytest.approx(
        unequal.length * unequal.depth * unequal.lower_thickness
        + unequal.tongue_length * unequal.tongue_width * unequal.tongue_height
        - hole_area * unequal.lower_thickness
    )
    assert volumes["upper"] == pytest.approx(
        unequal.length * unequal.depth * unequal.upper_thickness
        - unequal.groove_length * unequal.groove_width * unequal.groove_depth
        - hole_area * unequal.upper_thickness
    )


def test_current_parameters_reproduce_the_immutable_preintegration_baseline() -> None:
    baseline_root = ROOT / "workbench/designs/joint_coupon/baseline"
    baseline = json.loads((baseline_root / "measurements.json").read_text())
    _, params = load_parameters()
    volumes = expected_volumes(params)

    assert volumes["lower"] == pytest.approx(
        baseline["measurements"]["JC-DIM-ANALYTIC-LOWER-VOLUME"]["value"]
    )
    assert volumes["upper"] == pytest.approx(
        baseline["measurements"]["JC-DIM-ANALYTIC-UPPER-VOLUME"]["value"]
    )


def _coordinator_payload(relative_output: str, *, digest: str) -> dict:
    return {
        "job_id": "20260723T010203-joint-coupon-fast-abcdef1234",
        "name": "joint-coupon-fast",
        "state": "completed",
        "exit_status": "completed",
        "exit_code": 0,
        "failure_kind": None,
        "failure_message": None,
        "command": [
            sys.executable,
            "-m",
            "cad_runner.worker",
            str(ROOT / "workbench/designs/joint_coupon/build.py"),
            "--profile",
            "fast",
        ],
        "started_at": "2026-07-23T01:02:03Z",
        "finished_at": "2026-07-23T01:02:04Z",
        "elapsed_seconds": 1.0,
        "worker_pid": 123,
        "peak_rss_bytes": 456,
        "cleanup": {
            "workspace_removed": True,
            "error": None,
            "owned_process_group": {
                "reaped": True,
                "remaining_owned_pids": [],
            },
        },
        "final_outputs": [
            {
                "relative_path": relative_output,
                "bytes": 5,
                "sha256": digest,
            }
        ],
    }


def test_coupon_job_adapter_rejects_unrelated_profile_and_output_hashes() -> None:
    from workbench.designs.joint_coupon.packet import (
        _job_metrics,
        _require_diagnostics_job,
    )

    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="job-binding-", dir=build) as directory:
        output = Path(directory) / "diagnostics-fast.json"
        output.write_bytes(b"proof")
        relative = str(output.relative_to(ROOT))
        digest = sha256(b"proof").hexdigest()
        payload = _coordinator_payload(relative, digest=digest)
        keyword = {
            "role": "job.joint-coupon-production",
            "profile": VerificationProfile.FAST,
            "expected_name": "joint-coupon-fast",
            "expected_target": "workbench/designs/joint_coupon/build.py",
            "expected_arguments": ("--profile", "fast"),
            "expected_outputs": {relative},
        }

        unrelated = {**payload, "name": "unrelated-job"}
        with pytest.raises(ValueError, match="name mismatch"):
            _job_metrics(unrelated, **keyword)

        wrong_profile = {**payload, "command": [*payload["command"][:-1], "fit"]}
        with pytest.raises(ValueError, match="arguments mismatch"):
            _job_metrics(wrong_profile, **keyword)

        wrong_hash = json.loads(json.dumps(payload))
        wrong_hash["final_outputs"][0]["sha256"] = "0" * 64
        with pytest.raises(ValueError, match="content drift"):
            _job_metrics(wrong_hash, **keyword)

        with pytest.raises(ValueError, match="outputs mismatch"):
            _job_metrics(payload, **{**keyword, "expected_outputs": {"wrong.step"}})

        metrics = _job_metrics(payload, **keyword)
        diagnostics = {
            "job": {
                "job_id": "unrelated-job-id",
                "name": metrics.name,
                "target": metrics.target,
                "profile": metrics.profile.value,
                "command": list(metrics.command),
            },
            "status": "passed",
            "missing_native_requirement_ids": [],
        }
        with pytest.raises(ValueError, match="not bound"):
            _require_diagnostics_job(diagnostics, metrics)


def test_release_packet_requires_sidecar_and_snapshot_job_records() -> None:
    from workbench.designs.joint_coupon.packet import _require_release_arguments

    values = {
        "sidecar_job_record": Path("sidecar-job.json"),
        "snapshot_job_record": Path("snapshot-job.json"),
        "viewer_record": Path("viewer.json"),
        "attestation": Path("attestation.json"),
        "sidecar": Path("sidecar.glb"),
        "snapshot_overview": Path("overview.png"),
        "snapshot_section": Path("section.png"),
    }
    for field, message in (
        ("sidecar_job_record", "sidecar job record"),
        ("snapshot_job_record", "Snapshot job record"),
    ):
        args = argparse.Namespace(**{**values, field: None})
        with pytest.raises(ValueError, match=message):
            _require_release_arguments(args)
