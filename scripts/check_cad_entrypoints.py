"""Check or mechanically add the pre-import CAD coordinator guard."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
MARKER = "_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)"
NATIVE_PREFIXES = (
    "OCP",
    "build123d",
    "cadquery",
    "ocp_tessellate",
    "ocp_vscode",
    "vtk",
)
NATIVE_PACKAGE_PREFIXES = ("cad_geometry_checks.native",)
NATIVE_FREE_SCRIPT_MODULES = {
    "scripts.cad_review",
    "scripts.cad_verification_io",
    "scripts.cad_workflow_cli",
}
AUDITED_NATIVE_FREE_PATHS = {
    Path("scripts/cad_review.py"),
    Path("scripts/cad_verification_io.py"),
    Path("scripts/cad_workflow_cli.py"),
}
GUARD = """

# This guard must remain before all native CAD/threaded-library imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)
"""


def _repository_python_files() -> list[Path]:
    if (ROOT / ".git").exists():
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "*.py",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return [ROOT / line for line in result.stdout.splitlines() if line]
    return sorted(
        path
        for path in ROOT.rglob("*.py")
        if not any(
            part in {"build", ".venv", "__pycache__"} or part.startswith(".")
            for part in path.relative_to(ROOT).parts
        )
    )


def _imported_modules(text: str) -> tuple[tuple[str, int], ...]:
    tree = ast.parse(text)
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return tuple(imports)


def _module_requires_cad(module: str) -> bool:
    if module in NATIVE_FREE_SCRIPT_MODULES:
        return False
    if module == "src" or module.startswith("src."):
        return True
    if module == "experiments" or module.startswith("experiments."):
        return True
    if module.startswith("scripts."):
        return True
    if module.startswith("generate_"):
        return True
    if any(
        module == prefix or module.startswith(f"{prefix}.")
        for prefix in NATIVE_PACKAGE_PREFIXES
    ):
        return True
    return any(
        module == prefix or module.startswith(f"{prefix}.")
        for prefix in NATIVE_PREFIXES
    )


def source_requires_cad_guard(text: str) -> bool:
    """Return whether imports anywhere in an AST cross into the CAD runtime."""

    return any(
        _module_requires_cad(module) for module, _line in _imported_modules(text)
    )


def _cataloged_entrypoints() -> set[Path]:
    catalog_path = ROOT / ".cad-project/models.toml"
    if not catalog_path.is_file():
        return set()
    with catalog_path.open("rb") as stream:
        catalog = tomllib.load(stream)
    entries: set[Path] = set()
    for section in ("models", "experiments"):
        for record in catalog.get(section, ()):
            for key in ("entrypoint", "generator"):
                value = record.get(key)
                if isinstance(value, str) and value.endswith(".py"):
                    entries.add(Path(value))
    return entries


def _path_is_declared_cad_entrypoint(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative == Path("src/enclosure.py") or relative == Path("src/show_model.py"):
        return True
    if path.name == "render_preview.py":
        return True
    if relative.parts and relative.parts[0] == "scripts":
        return path.name.startswith("generate_")
    if relative.parts and relative.parts[0] == "experiments":
        return path.name.startswith("generate_")
    return False


def repository_cad_entrypoints() -> list[Path]:
    entries: list[Path] = []
    cataloged = _cataloged_entrypoints()
    for path in _repository_python_files():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        if (
            relative.parts
            and relative.parts[0] == "tests"
            and relative not in cataloged
        ):
            continue
        if relative in cataloged or (
            'if __name__ == "__main__":' in text
            and (
                source_requires_cad_guard(text)
                or _path_is_declared_cad_entrypoint(path)
            )
        ):
            entries.append(path)
    return sorted(set(entries))


def entrypoint_source_violations(relative: Path, text: str) -> list[str]:
    """Audit one known entrypoint; exposed for focused policy tests."""

    problems: list[str] = []
    if MARKER not in text:
        return [f"{relative}: missing CAD coordinator guard"]
    marker_offset = text.index(MARKER)
    marker_line = text[:marker_offset].count("\n") + 1
    import_lines = [
        line for module, line in _imported_modules(text) if _module_requires_cad(module)
    ]
    if import_lines and marker_line > min(import_lines):
        problems.append(f"{relative}: guard appears after native CAD import")
    if "preexec_fn" in text or "os.fork(" in text:
        problems.append(f"{relative}: unsafe fork-triggering process code")
    return problems


def production_review_violations(relative: Path, text: str) -> list[str]:
    """Reject review generation and subprocesses from a production generate path."""

    tree = ast.parse(text)
    generate = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "generate"
        ),
        None,
    )
    if generate is None:
        return [f"{relative}: missing production generate() function"]
    problems: list[str] = []
    forbidden_names = {
        "generate_review",
        "model_payload",
        "render_viewer",
        "snapshot",
    }
    for node in ast.walk(generate):
        if not isinstance(node, ast.Call):
            continue
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            value: ast.expr = node.func
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                parts.append(value.id)
            name = ".".join(reversed(parts))
        if name == "subprocess.run" or name == "subprocess.Popen":
            problems.append(
                f"{relative}: production generate() launches subprocess {name}"
            )
        if name.rsplit(".", 1)[-1] in forbidden_names:
            problems.append(
                f"{relative}: production generate() invokes review function {name}"
            )
    for node in ast.walk(generate):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and any(
                marker in node.value.lower()
                for marker in ("viewer", "snapshot", "sidecar", "preview")
            )
        ):
            problems.append(
                f"{relative}: production generate() contains review target "
                f"{node.value!r}"
            )
    return problems


def violations() -> list[str]:
    problems: list[str] = []
    for relative in sorted(AUDITED_NATIVE_FREE_PATHS):
        path = ROOT / relative
        if path.is_file() and source_requires_cad_guard(
            path.read_text(encoding="utf-8")
        ):
            problems.append(f"{relative}: audited native-free module imports CAD code")
    for path in repository_cad_entrypoints():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        problems.extend(entrypoint_source_violations(relative, text))
    return problems


def add_missing_guards() -> list[Path]:
    changed: list[Path] = []
    anchor = "from __future__ import annotations\n"
    for path in repository_cad_entrypoints():
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            continue
        if anchor not in text:
            raise RuntimeError(f"Cannot safely place guard in {path.relative_to(ROOT)}")
        updated = text.replace(anchor, anchor + GUARD, 1)
        path.write_text(updated, encoding="utf-8")
        changed.append(path)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)
    if args.fix:
        for path in add_missing_guards():
            print(path.relative_to(ROOT))
    problems = violations()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"checked {len(repository_cad_entrypoints())} CAD entry points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
