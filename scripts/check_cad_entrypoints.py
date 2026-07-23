"""Check or mechanically add the pre-import CAD coordinator guard."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MARKER = "_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)"
HEAVY_IMPORT = re.compile(
    r"^(?:from|import)\s+(?:OCP|build123d|cadquery|ocp_tessellate|ocp_vscode|vtk)",
    re.MULTILINE,
)
NATIVE_FREE_SCRIPT_IMPORT = r"(?:cad_review|cad_verification_io)\b"
INDIRECT_CAD_IMPORT = re.compile(
    rf"^(?:from\s+(?:src|experiments)\."
    rf"|from\s+scripts\.(?!{NATIVE_FREE_SCRIPT_IMPORT})"
    rf"|import\s+generate_)",
    re.MULTILINE,
)
GUARD = '''

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
'''


def _repository_python_files() -> list[Path]:
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
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


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
    for path in _repository_python_files():
        text = path.read_text(encoding="utf-8")
        if 'if __name__ == "__main__":' not in text:
            continue
        if (
            HEAVY_IMPORT.search(text)
            or INDIRECT_CAD_IMPORT.search(text)
            or _path_is_declared_cad_entrypoint(path)
        ):
            entries.append(path)
    return entries


def violations() -> list[str]:
    problems: list[str] = []
    for path in repository_cad_entrypoints():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        if MARKER not in text:
            problems.append(f"{relative}: missing CAD coordinator guard")
            continue
        marker_offset = text.index(MARKER)
        heavy = HEAVY_IMPORT.search(text)
        if heavy and marker_offset > heavy.start():
            problems.append(f"{relative}: guard appears after native CAD import")
        if "preexec_fn" in text or re.search(r"\bos\.fork\s*\(", text):
            problems.append(f"{relative}: unsafe fork-triggering process code")
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
