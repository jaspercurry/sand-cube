from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.enclosure_family.legacy_runtime import (
    LegacyAttributeBinding,
    bind_legacy_attributes,
)
from src.enclosure_family.variant_i import VARIANT_I_BOUNDARY
from src.enclosure_family.variant_r import (
    AUTHORITATIVE_BASE_FILENAME,
    PRODUCER_ATTESTATION_FILENAME,
    PRODUCER_ENTRYPOINT,
    VARIANT_R_ARTIFACTS,
    VARIANT_R_MODEL,
    VARIANT_R_PARAMETERS,
    VARIANT_R_PRINT_CONTRACTS,
    VARIANT_R_VERIFICATION,
)
from src.enclosure_family.variant_r.inputs import (
    authoritative_base_step,
    producer_attestation_path,
)
from src.enclosure_family.variant_r.provenance import (
    verify_producer_attestation,
)


ROOT = Path(__file__).resolve().parents[1]


def test_variant_r_parameters_preserve_current_values() -> None:
    params = VARIANT_R_PARAMETERS
    assert params.gasket_closed_gap_mm == 1.0
    assert params.path_half_size_mm == 88.125
    assert params.path_bottom_corner_tangency_mm == 73.0
    assert params.screw_bypass_depth_mm == 4.0
    assert params.seal_land_width_mm == 6.75
    assert params.gasket_width_mm == 5.0
    assert params.gasket_edge_margin_mm == 0.875
    assert params.baffle_print_bed_z_mm == -91.5
    assert params.bottom_synthesis_max_z_mm == -80.0
    assert params.bottom_synthesis_overlap_mm == 0.20
    assert params.bottom_print_root_overlap_mm == 0.20


def test_variant_r_print_contracts_are_explicit_and_unverified_physically() -> None:
    by_part = {contract.part_id: contract for contract in VARIANT_R_PRINT_CONTRACTS}
    assert set(by_part) == {"bucket", "baffle"}
    assert by_part["bucket"].build_direction == (0, -1, 0)
    assert by_part["bucket"].brim_assumed is False
    assert by_part["baffle"].build_direction == (0, 0, 1)
    assert by_part["baffle"].brim_assumed is True
    assert all(not contract.physical_print_verified for contract in by_part.values())


def test_variant_r_model_has_one_explicit_owner_per_boundary() -> None:
    model = VARIANT_R_MODEL
    assert model.model_id == "development-190x210-tongue-groove"
    assert model.variant_id == "variant_r"
    assert model.retention_geometry == "absent"
    assert len(
        {
            model.assembly_owner,
            model.seam_owner,
            model.bottom_material_owner,
            model.parameter_owner,
            model.artifact_owner,
            model.input_owner,
            model.provenance_owner,
            model.verification_owner,
        }
    ) == 8


def test_variant_r_artifact_and_verification_contracts_are_complete() -> None:
    by_id = {artifact.artifact_id: artifact for artifact in VARIANT_R_ARTIFACTS}
    assert {artifact.artifact_id for artifact in VARIANT_R_ARTIFACTS} == {
        "bucket",
        "baffle",
        "authoritative_side_seam",
        "authoritative_top_seam",
        "hybrid_bottom_corner_transition",
        "hybrid_flat_bottom",
        "hybrid_side_seam",
        "hybrid_top_seam",
        "validation_diagnostics",
        "producer_attestation",
    }
    assert by_id["bucket"].filename == "simple_tongue_groove_bucket.step"
    assert by_id["baffle"].filename == "simple_tongue_groove_baffle.step"
    assert set(VARIANT_R_VERIFICATION.protected_section_ids) == {
        artifact.artifact_id
        for artifact in VARIANT_R_ARTIFACTS
        if artifact.kind == "protected_section"
    }
    assert VARIANT_R_VERIFICATION.require_step_round_trip is True
    assert VARIANT_R_VERIFICATION.require_attested_authoritative_input is True
    assert (
        VARIANT_R_VERIFICATION.require_complete_loaded_source_closure is True
    )
    assert VARIANT_R_VERIFICATION.tolerances.volume_mm3 == 1e-5


def test_variant_r_input_contract_points_to_cataloged_producer() -> None:
    assert PRODUCER_ENTRYPOINT == Path("scripts/generate_variant_r.py")
    assert (
        authoritative_base_step(ROOT).name
        == AUTHORITATIVE_BASE_FILENAME
    )
    assert (
        producer_attestation_path(ROOT).name
        == PRODUCER_ATTESTATION_FILENAME
    )


def test_variant_r_input_attestation_rejects_a_changed_base(
    tmp_path: Path,
) -> None:
    base = tmp_path / AUTHORITATIVE_BASE_FILENAME
    base.write_bytes(b"accepted")
    sources = [
        {
            "path": f"experiments/stage-{index}/generate.py",
            "sha256": "0" * 64,
            "bytes": 1,
            "role": "geometry_or_parameter_dependency",
        }
        for index in range(19)
    ]
    payload = {
        "schema_version": 1,
        "attestation_kind": "variant_r_authoritative_producer",
        "producer_entrypoint": PRODUCER_ENTRYPOINT.as_posix(),
        "git": {"tracked_source_dirty": False},
        "authoritative_base_input": {
            "filename": AUTHORITATIVE_BASE_FILENAME,
            "sha256": hashlib.sha256(b"accepted").hexdigest(),
            "bytes": len(b"accepted"),
        },
        "runtime_dependency_closure": {
            "loaded_generator_stage_count": 19,
            "sources": sources,
        },
    }
    attestation = tmp_path / PRODUCER_ATTESTATION_FILENAME
    attestation.write_text(json.dumps(payload))
    assert (
        verify_producer_attestation(
            repo_root=ROOT,
            base_step=base,
            attestation_path=attestation,
        )
        == payload
    )
    base.write_bytes(b"changed")
    with pytest.raises(ValueError, match="does not match"):
        verify_producer_attestation(
            repo_root=ROOT,
            base_step=base,
            attestation_path=attestation,
        )


def test_legacy_runtime_binding_is_scoped_and_exactly_restored() -> None:
    owner = SimpleNamespace(value=object())
    original = owner.value
    replacement = object()
    with bind_legacy_attributes(
        (LegacyAttributeBinding(owner, "value", replacement),)
    ):
        assert owner.value is replacement
    assert owner.value is original


def test_variant_i_boundary_is_independent_and_has_no_geometry() -> None:
    assert VARIANT_I_BOUNDARY.implementation_status == "future_geometry_absent"
    assert VARIANT_I_BOUNDARY.print_contract.status == "future"
    assert VARIANT_I_BOUNDARY.print_contract.build_direction == (0, 0, 1)
    with pytest.raises(NotImplementedError, match="intentionally absent"):
        VARIANT_I_BOUNDARY.require_geometry_owner()


@pytest.mark.parametrize(
    "relative_path",
    [
        "src/enclosure_family/print_contracts.py",
        "src/enclosure_family/legacy_runtime.py",
        "src/enclosure_family/variant_r/artifacts.py",
        "src/enclosure_family/variant_r/foundation.py",
        "src/enclosure_family/variant_r/inputs.py",
        "src/enclosure_family/variant_r/model.py",
        "src/enclosure_family/variant_r/parameters.py",
        "src/enclosure_family/variant_r/print_contracts.py",
        "src/enclosure_family/variant_r/provenance.py",
        "src/enclosure_family/variant_r/verification.py",
        "src/enclosure_family/variant_i/interface.py",
    ],
)
def test_ownership_modules_are_native_cad_free(relative_path: str) -> None:
    tree = ast.parse((ROOT / relative_path).read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any(
        name.startswith(("build123d", "OCP", "experiments"))
        for name in imported
    )


def test_variant_i_interface_does_not_import_variant_r() -> None:
    tree = ast.parse(
        (ROOT / "src/enclosure_family/variant_i/interface.py").read_text()
    )
    modules = [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any("variant_r" in module for module in modules)


@pytest.mark.parametrize(
    "relative_path",
    [
        "src/enclosure_family/variant_r/assembly.py",
        "src/enclosure_family/variant_r/bottom_ownership.py",
        "src/enclosure_family/variant_r/seam.py",
        "src/enclosure_family/variant_r/model.py",
        "src/enclosure_family/variant_r/verification.py",
    ],
)
def test_variant_r_geometry_owners_do_not_import_experiments(
    relative_path: str,
) -> None:
    tree = ast.parse((ROOT / relative_path).read_text())
    modules = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    modules.extend(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any(module.startswith("experiments") for module in modules)


def test_variant_r_generator_has_no_flag_driven_retention_architecture() -> None:
    generator = ROOT / (
        "experiments/"
        "sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_simple_tongue_groove_baffle/"
        "generate_sand_cube_190x210_internal_squat_absorber_rear_corners_"
        "parabolic_side_g1_simple_tongue_groove_baffle.py"
    )
    source = generator.read_text()
    assert "BUILD_TOP_HINGE" not in source
    assert "BUILD_BOTTOM_SCREWS" not in source
    assert "_add_top_tongue_groove" not in source
    assert "_add_bottom_screws" not in source


def test_variant_r_catalog_points_to_owned_source_and_thin_entrypoint() -> None:
    catalog = (ROOT / ".cad-project/models.toml").read_text()
    assert 'source = "src/enclosure_family/variant_r/model.py"' in catalog
    assert 'entrypoint = "scripts/generate_variant_r.py"' in catalog
    entrypoint = (ROOT / "scripts/generate_variant_r.py").read_text()
    assert "def main()" in entrypoint
    assert "generate_authoritative_base_input" in entrypoint
    assert "build123d" not in entrypoint
