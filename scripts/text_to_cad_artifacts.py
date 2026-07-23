"""Generate pinned Text-to-CAD sidecars and snapshots through cad_runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


# This guard must remain before all native CAD and Snapshot runtime imports.
_CAD_SAFETY_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in sys.path:
    sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated  # noqa: E402
from cad_runner.outputs import STAGE_ROOT_ENV, job_output_path  # noqa: E402

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)


ROOT = _CAD_SAFETY_ROOT
with (ROOT / ".cad-project/project.toml").open("rb") as _config_stream:
    _PROJECT_CONFIG = tomllib.load(_config_stream)
TEXT_TO_CAD_VERSION = str(_PROJECT_CONFIG["viewer"]["version"])
TEXT_TO_CAD_COMMIT = str(_PROJECT_CONFIG["viewer"]["commit"])
DEFAULT_TOOL_ROOT = ROOT / str(_PROJECT_CONFIG["viewer"]["tool_root"])


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tool_root() -> Path:
    configured = os.environ.get("TEXT_TO_CAD_ROOT")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_TOOL_ROOT


def _require_runtime() -> Path:
    tool_root = _tool_root()
    version_path = tool_root / "plugins/cad/VERSION"
    actual_version = version_path.read_text().strip() if version_path.is_file() else ""
    if actual_version != TEXT_TO_CAD_VERSION:
        raise RuntimeError(
            f"Expected Text-to-CAD {TEXT_TO_CAD_VERSION} under {tool_root}; "
            f"found {actual_version or 'no version marker'}"
        )
    completed = subprocess.run(
        ["git", "-C", str(tool_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    actual_commit = completed.stdout.strip() if completed.returncode == 0 else ""
    if actual_commit != TEXT_TO_CAD_COMMIT:
        raise RuntimeError(
            f"Expected Text-to-CAD commit {TEXT_TO_CAD_COMMIT}; "
            f"found {actual_commit or 'unknown'}"
        )
    return tool_root


def _sidecar(args: argparse.Namespace) -> int:
    tool_root = _require_runtime()
    cadpy_src = tool_root / "packages/cadpy/src"
    if not cadpy_src.is_dir():
        raise RuntimeError(f"Pinned cadpy source is missing: {cadpy_src}")
    sys.path.insert(0, str(cadpy_src))

    from cadpy.step_artifact import main as step_artifact_main

    step_path = args.step.expanduser().resolve()
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP artifact does not exist: {step_path}")
    stage_root = Path(os.environ[STAGE_ROOT_ENV]).resolve()
    scratch = stage_root.parent / "scratch" / "sidecar"
    scratch.mkdir(parents=True, exist_ok=True)
    scratch_step = scratch / step_path.name
    shutil.copy2(step_path, scratch_step)
    command = [
        "--repo-root",
        str(scratch),
        "--step",
        str(scratch_step),
        "--kind",
        args.kind,
        "--verbose",
    ]
    if args.force:
        command.append("--force")
    exit_code = int(step_artifact_main(command))
    if exit_code != 0:
        return exit_code
    generated = scratch / f".{step_path.name}.glb"
    if not generated.is_file():
        raise RuntimeError(
            f"Text-to-CAD did not produce the expected sidecar: {generated}"
        )
    final_sidecar = step_path.with_name(f".{step_path.name}.glb")
    staged_sidecar = job_output_path(final_sidecar)
    staged_sidecar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generated, staged_sidecar)
    return 0


def _snapshot(args: argparse.Namespace) -> int:
    tool_root = _require_runtime()
    python_runtime = tool_root / ".snapshot-python"
    browser_runtime = tool_root / ".snapshot-browsers"
    snapshot_scripts = tool_root / "skills/cad/scripts"
    if not (python_runtime / "playwright").is_dir():
        raise RuntimeError(
            f"Snapshot Python runtime is missing: {python_runtime}. "
            "Follow docs/LOCAL_CAD_VIEWING.md."
        )
    if not browser_runtime.is_dir():
        raise RuntimeError(
            f"Snapshot browser runtime is missing: {browser_runtime}. "
            "Follow docs/LOCAL_CAD_VIEWING.md."
        )
    sys.path.insert(0, str(python_runtime))
    sys.path.insert(0, str(snapshot_scripts))
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browser_runtime))

    from snapshot.__main__ import main as snapshot_main

    job_path = args.job.expanduser().resolve()
    if not job_path.is_file():
        raise FileNotFoundError(f"Snapshot job does not exist: {job_path}")
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    provenance_value = payload.pop("provenanceOutput", None)
    if provenance_value is None:
        provenance_target = job_path.with_name(f"{job_path.stem}-provenance.json")
    else:
        if not isinstance(provenance_value, str):
            raise ValueError("Snapshot provenance output must be a string path")
        relative_provenance = Path(provenance_value)
        if relative_provenance.is_absolute() or ".." in relative_provenance.parts:
            raise ValueError("Snapshot provenance output must be repository-relative")
        provenance_target = ROOT / relative_provenance
    for job in payload.get("jobs", ()):
        for output in job.get("outputs", ()):
            output["path"] = str(job_output_path(output["path"]))
    stage_root = Path(os.environ[STAGE_ROOT_ENV]).resolve()
    scratch = stage_root.parent / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    staged_job = scratch / "snapshot-job.json"
    staged_job.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    command = ["--job", str(staged_job)]
    if args.json:
        command.append("--json")
    exit_code = int(snapshot_main(command))
    if exit_code != 0:
        return exit_code

    rendered_outputs = []
    for job in payload.get("jobs", ()):
        for output in job.get("outputs", ()):
            requested = Path(output["path"])
            matches = sorted(requested.parent.glob(f"{requested.stem}*.png"))
            if len(matches) != 1:
                raise RuntimeError(
                    f"Snapshot must produce exactly one PNG for {requested}; found {matches}"
                )
            rendered = matches[0]
            rendered_outputs.append(
                {
                    "path": str(rendered.relative_to(stage_root)),
                    "sha256": _sha256_file(rendered),
                    "size_bytes": rendered.stat().st_size,
                }
            )

    sources = []
    for input_value in dict.fromkeys(job["input"] for job in payload.get("jobs", ())):
        input_path = (ROOT / input_value).resolve()
        sidecar_path = input_path.with_name(f".{input_path.name}.glb")
        for kind, source in (("step", input_path), ("sidecar", sidecar_path)):
            if not source.is_file():
                raise FileNotFoundError(source)
            sources.append(
                {
                    "kind": kind,
                    "path": str(source.relative_to(ROOT)),
                    "sha256": _sha256_file(source),
                    "size_bytes": source.stat().st_size,
                }
            )
    provenance = {
        "schema_version": 1,
        "job_id": os.environ["CAD_JOB_ID"],
        "target": "scripts/text_to_cad_artifacts.py",
        "command": [
            "scripts/text_to_cad_artifacts.py",
            "snapshot",
            "--job",
            str(job_path.relative_to(ROOT)),
            *(["--json"] if args.json else []),
        ],
        "snapshot_job": {
            "path": str(job_path.relative_to(ROOT)),
            "sha256": _sha256_file(job_path),
        },
        "sources": sources,
        "outputs": rendered_outputs,
    }
    provenance_path = job_output_path(provenance_target)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            f"Run pinned Text-to-CAD {TEXT_TO_CAD_VERSION} topology and Snapshot "
            "tools through the repository CAD coordinator."
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Text-to-CAD {TEXT_TO_CAD_VERSION} ({TEXT_TO_CAD_COMMIT})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sidecar = subparsers.add_parser(
        "sidecar", help="Generate the hidden GLB/topology sidecar for one STEP."
    )
    sidecar.add_argument("step", type=Path)
    sidecar.add_argument("--kind", choices=("part", "assembly"), default="part")
    sidecar.add_argument(
        "--artifact-root",
        type=Path,
        help="Metadata root; defaults to the STEP artifact directory.",
    )
    sidecar.add_argument("--force", action="store_true")
    sidecar.set_defaults(handler=_sidecar)

    snapshot = subparsers.add_parser(
        "snapshot", help="Render one deterministic Text-to-CAD Snapshot job."
    )
    snapshot.add_argument("--job", type=Path, required=True)
    snapshot.add_argument("--json", action="store_true")
    snapshot.set_defaults(handler=_snapshot)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
