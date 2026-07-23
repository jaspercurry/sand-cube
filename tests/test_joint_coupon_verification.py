from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import tomllib

from cad_verification import (
    VerificationProfile,
    requirements_for_profile,
    validate_contract,
)
from workbench.designs.joint_coupon.parameters import load_parameters
from workbench.designs.joint_coupon.verification import design_contract


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
    assert {item.cost_profile for item in fit[len(fast) :]} == {
        VerificationProfile.FIT
    }
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


def test_sidecar_binding_reader_extracts_embedded_step_hash() -> None:
    from workbench.designs.joint_coupon.packet import _glb_step_hashes

    step_hash = "a" * 64
    document = json.dumps(
        {"asset": {"version": "2.0"}, "extras": {"stepHash": step_hash}},
        separators=(",", ":"),
    ).encode("utf-8")
    document += b" " * (-len(document) % 4)
    size = 12 + 8 + len(document)
    glb = b"glTF" + struct.pack("<II", 2, size)
    glb += struct.pack("<II", len(document), 0x4E4F534A) + document
    with tempfile.TemporaryDirectory(dir=ROOT / "build") as directory:
        path = Path(directory) / "sidecar.glb"
        path.write_bytes(glb)
        hashes = _glb_step_hashes(path)

    assert hashes == {step_hash}
    assert "b" * 64 not in hashes
