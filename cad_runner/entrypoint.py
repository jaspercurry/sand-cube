"""Early entry-point guard that never imports CAD libraries."""

from __future__ import annotations

import os
from pathlib import Path
import sys


CAD_WORKER_ENV = "CAD_JOB_WORKER"
_NATIVE_CAD_PREFIXES = (
    "OCP",
    "build123d",
    "cadquery",
    "ocp_tessellate",
    "ocp_vscode",
    "vtk",
)


def find_repo_root(script_path: str | Path) -> Path:
    """Find the repository without importing project or CAD modules."""
    script = Path(script_path).resolve()
    for parent in (script.parent, *script.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise RuntimeError(f"Cannot locate CAD repository above {script}")


def ensure_coordinated(
    module_name: str,
    script_path: str | Path,
    repo_root: str | Path | None = None,
) -> None:
    """Replace a direct generator with the lightweight coordinator.

    This function must be called before importing build123d, OCP, CadQuery,
    VTK, or ocp-vscode. Imported library modules are allowed to call it: only
    the actual ``__main__`` entry point is re-executed.
    """
    if module_name != "__main__" or os.environ.get(CAD_WORKER_ENV) == "1":
        return

    loaded = sorted(
        name
        for name in sys.modules
        if name in _NATIVE_CAD_PREFIXES
        or name.startswith(tuple(f"{prefix}." for prefix in _NATIVE_CAD_PREFIXES))
    )
    if loaded:
        raise RuntimeError(
            "CAD safety guard ran after native CAD imports: " + ", ".join(loaded[:8])
        )

    script = Path(script_path).resolve()
    root = Path(repo_root).resolve() if repo_root else find_repo_root(script)
    env = os.environ.copy()
    prior_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(root)
        if not prior_pythonpath
        else str(root) + os.pathsep + prior_pythonpath
    )
    argv = [
        sys.executable,
        "-m",
        "cad_runner",
        "run",
        "--repo",
        str(root),
        "--name",
        script.stem,
        "--",
        str(script),
        *sys.argv[1:],
    ]
    # execve replaces this import-clean launcher. It does not fork and leaves
    # no extra parent process to reap.
    os.execve(sys.executable, argv, env)
