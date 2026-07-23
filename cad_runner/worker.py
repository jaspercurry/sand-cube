"""Fresh worker bootstrap; native CAD imports happen only after this starts."""

from __future__ import annotations

import inspect
import os
from pathlib import Path
import runpy
import sys
from types import FunctionType, ModuleType
from typing import Any

from .outputs import REPO_ROOT_ENV, STAGE_ROOT_ENV, job_output_path
from .telemetry import FAILURE_PATH_ENV, write_failure_envelope


_OUTPUT_GLOBAL_NAMES = {
    "BUILD_DIR",
    "BUILD_ROOT",
    "DEFAULT_OUT",
    "OUT",
    "OUT_DIR",
    "OUTPUT",
    "OUTPUT_DIR",
    "OUTPUT_ROOT",
    "PREVIEW_DIR",
    "RESULTS_DIR",
}
_OUTPUT_PARAMETER_FRAGMENTS = ("build", "dest", "out", "output", "report")


def _module_is_repo_owned(module: ModuleType, repo: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return False
    try:
        relative = Path(module_file).resolve().relative_to(repo)
    except (OSError, ValueError):
        return False
    if not relative.parts or relative.parts[0] in {".venv", "build"}:
        return False
    return True


def _redirect_function_defaults(function: FunctionType) -> None:
    defaults = function.__defaults__
    if defaults:
        parameters = list(inspect.signature(function).parameters.values())
        positional = [
            parameter
            for parameter in parameters
            if parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        if len(defaults) > len(positional):
            return
        names = [parameter.name for parameter in positional[-len(defaults) :]]
        remapped: list[Any] = []
        for name, value in zip(names, defaults, strict=True):
            if isinstance(value, Path) and any(
                fragment in name.lower() for fragment in _OUTPUT_PARAMETER_FRAGMENTS
            ):
                value = job_output_path(value)
            remapped.append(value)
        function.__defaults__ = tuple(remapped)

    if function.__kwdefaults__:
        function.__kwdefaults__ = {
            name: (
                job_output_path(value)
                if isinstance(value, Path)
                and any(
                    fragment in name.lower()
                    for fragment in _OUTPUT_PARAMETER_FRAGMENTS
                )
                else value
            )
            for name, value in function.__kwdefaults__.items()
        }


def _redirect_namespace(namespace: dict[str, Any]) -> None:
    """Redirect one already-loaded module/entry-point namespace."""
    for name in _OUTPUT_GLOBAL_NAMES:
        value = namespace.get(name)
        if isinstance(value, Path):
            namespace[name] = job_output_path(value)
    module_name = namespace.get("__name__")
    for value in list(namespace.values()):
        if isinstance(value, FunctionType) and value.__module__ == module_name:
            _redirect_function_defaults(value)


def redirect_loaded_output_paths(
    repo: Path,
    *,
    entrypoint_namespace: dict[str, Any] | None = None,
) -> None:
    """Redirect outputs in repo modules and an optional external entry point."""
    redirected_namespaces: set[int] = set()
    if entrypoint_namespace is not None:
        _redirect_namespace(entrypoint_namespace)
        redirected_namespaces.add(id(entrypoint_namespace))
    for module in list(sys.modules.values()):
        if not isinstance(module, ModuleType) or not _module_is_repo_owned(module, repo):
            continue
        namespace = vars(module)
        if id(namespace) in redirected_namespaces:
            continue
        redirected_namespaces.add(id(namespace))
        _redirect_namespace(namespace)


def _run_script(script: Path, arguments: list[str]) -> None:
    repo = Path(os.environ[REPO_ROOT_ENV]).resolve()
    redirected = False

    def profile(frame, event, _arg):
        nonlocal redirected
        if (
            not redirected
            and event == "call"
            and frame.f_code.co_name in {"main", "_main"}
            and Path(frame.f_code.co_filename).resolve() == script
        ):
            redirect_loaded_output_paths(
                repo,
                entrypoint_namespace=frame.f_globals,
            )
            redirected = True
            sys.setprofile(None)
        return profile

    sys.argv = [str(script), *arguments]
    sys.setprofile(profile)
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.setprofile(None)


def _record_failure(error: BaseException) -> None:
    """Never let optional telemetry replace the worker's original failure."""

    failure_path = os.environ.get(FAILURE_PATH_ENV)
    if not failure_path:
        return
    try:
        write_failure_envelope(Path(failure_path), error)
    except BaseException:
        pass


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        raise SystemExit("cad_runner.worker requires a script path")
    if not os.environ.get(STAGE_ROOT_ENV) or not os.environ.get(REPO_ROOT_ENV):
        raise SystemExit("cad_runner.worker must be launched by the coordinator")
    script = Path(arguments.pop(0)).resolve()
    try:
        _run_script(script, arguments)
    except SystemExit as error:
        if error.code not in (None, 0):
            _record_failure(error)
        raise
    except BaseException as error:
        _record_failure(error)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
