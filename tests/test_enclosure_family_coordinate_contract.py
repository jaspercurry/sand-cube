from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from src.enclosure_family.datums import ENCLOSURE_190X210_COORDINATES


ROOT = Path(__file__).resolve().parents[1]
DATUMS_SOURCE = ROOT / "src" / "enclosure_family" / "datums.py"
BASE_SOURCE = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_single_oval_port"
    / "generate_sand_cube_190x210_single_oval_port.py"
)
FAMILY_SOURCES = tuple(
    ROOT.glob("experiments/sand_cube_190x210*/**/*.py")
)


def _is_number(node: ast.AST, value: float) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _nodes_contain_depth_and_ten(nodes: Iterable[ast.AST]) -> bool:
    contains_ten = any(_is_number(node, 10.0) for node in nodes)
    contains_depth = any(
        isinstance(node, ast.Attribute) and node.attr == "depth" for node in nodes
    )
    return contains_ten and contains_depth


def test_coordinate_contract_preserves_the_frozen_family_frame() -> None:
    coordinates = ENCLOSURE_190X210_COORDINATES

    assert coordinates.units == "mm"
    assert (
        coordinates.width_mm,
        coordinates.depth_mm,
        coordinates.height_mm,
    ) == (190.0, 210.0, 190.0)
    assert (
        coordinates.center_x_mm,
        coordinates.center_y_mm,
        coordinates.center_z_mm,
    ) == (0.0, 10.0, 0.0)
    assert (
        coordinates.left_x_mm,
        coordinates.right_x_mm,
        coordinates.front_y_mm,
        coordinates.rear_y_mm,
        coordinates.bottom_z_mm,
        coordinates.top_z_mm,
    ) == (-95.0, 95.0, -95.0, 115.0, -95.0, 95.0)
    assert (
        coordinates.width_axis,
        coordinates.depth_axis,
        coordinates.height_axis,
    ) == ("X", "Y", "Z")
    assert coordinates.left_direction == (-1, 0, 0)
    assert coordinates.right_direction == (1, 0, 0)
    assert coordinates.front_direction == (0, -1, 0)
    assert coordinates.rear_direction == (0, 1, 0)
    assert coordinates.bottom_direction == (0, 0, -1)
    assert coordinates.top_direction == (0, 0, 1)


def test_coordinate_contract_has_no_native_cad_imports() -> None:
    imported_roots: set[str] = set()
    for node in ast.walk(ast.parse(DATUMS_SOURCE.read_text())):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "build123d" not in imported_roots
    assert "OCP" not in imported_roots


def test_base_design_consumes_the_coordinate_owner() -> None:
    tree = ast.parse(BASE_SOURCE.read_text())
    design = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Design"
    )
    defaults = {
        node.target.id: ast.unparse(node.value)
        for node in design.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    }

    assert defaults["width"] == "ENCLOSURE_190X210_COORDINATES.width_mm"
    assert defaults["depth"] == "ENCLOSURE_190X210_COORDINATES.depth_mm"
    assert defaults["height"] == "ENCLOSURE_190X210_COORDINATES.height_mm"
    assert defaults["center_y"] == "ENCLOSURE_190X210_COORDINATES.center_y_mm"


def test_existing_family_sources_do_not_duplicate_the_y_center_datum() -> None:
    duplicate_expressions: list[str] = []
    for path in FAMILY_SOURCES:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and _nodes_contain_depth_and_ten(
                ast.walk(node)
            ):
                duplicate_expressions.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: {ast.unparse(node)}"
                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Pos"
                and len(node.args) >= 3
                and _is_number(node.args[0], 0.0)
                and _is_number(node.args[1], 10.0)
                and _is_number(node.args[2], 0.0)
            ):
                duplicate_expressions.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: {ast.unparse(node)}"
                )

    assert duplicate_expressions == []
