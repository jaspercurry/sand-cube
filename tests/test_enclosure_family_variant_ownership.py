from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.enclosure_family.variant_i import VARIANT_I_BOUNDARY
from src.enclosure_family.variant_r import (
    VARIANT_R_PARAMETERS,
    VARIANT_R_PRINT_CONTRACTS,
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
        "src/enclosure_family/variant_r/parameters.py",
        "src/enclosure_family/variant_r/print_contracts.py",
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
