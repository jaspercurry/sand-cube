"""Generate pinned Text-to-CAD sidecars and snapshots through cad_runner."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
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

from cad_runner.cache import (  # noqa: E402
    DeclaredOutput,
    FileFingerprint,
    StageCache,
    StageCacheSpec,
    ToolIdentity,
    fingerprint_file,
)
from cad_runner.glb import glb_step_identity  # noqa: E402


ROOT = _CAD_SAFETY_ROOT
with (ROOT / ".cad-project/project.toml").open("rb") as _config_stream:
    _PROJECT_CONFIG = tomllib.load(_config_stream)
TEXT_TO_CAD_VERSION = str(_PROJECT_CONFIG["viewer"]["version"])
TEXT_TO_CAD_COMMIT = str(_PROJECT_CONFIG["viewer"]["commit"])
DEFAULT_TOOL_ROOT = ROOT / str(_PROJECT_CONFIG["viewer"]["tool_root"])
SIDECAR_CACHE_STAGE = "text-to-cad-sidecar"
SIDECAR_PRODUCER_VERSION = "1"
SIDECAR_PRODUCER_SCHEMA_VERSION = 1
SIDECAR_OUTPUT = DeclaredOutput("sidecar", "artifacts/topology.glb")
SIDECAR_SETTINGS = {
    "generator": "cadpy.step_artifact",
    "topology_profile": "index",
    "meshing": {
        "configuration": "text-to-cad-defaults",
        "identity": "pinned-tool-commit",
    },
    "command_schema_version": 1,
}
NATIVE_DEPENDENCY_PINS = {
    "build123d": str(_PROJECT_CONFIG["dependencies"]["build123d"]),
    "cadquery-ocp-novtk": str(_PROJECT_CONFIG["dependencies"]["cadquery_ocp_novtk"]),
}


@dataclass(frozen=True)
class VerifiedSidecar:
    step_path: str
    step_sha256: str
    sidecar_path: str
    sidecar_sha256: str
    sidecar_size_bytes: int
    kind: str
    cache_key: str


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
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(tool_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=no",
            "--",
            "packages/cadpy",
            "plugins/cad",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if dirty.returncode != 0:
        raise RuntimeError(
            f"Could not verify Text-to-CAD generator sources under {tool_root}"
        )
    if dirty.stdout.strip():
        raise RuntimeError(
            "Pinned Text-to-CAD generator sources have tracked modifications: "
            f"{dirty.stdout.strip()}"
        )
    mismatches = []
    for distribution, expected in NATIVE_DEPENDENCY_PINS.items():
        actual = _installed_version(distribution)
        if actual != expected:
            mismatches.append(f"{distribution}: expected {expected}, found {actual}")
    if mismatches:
        raise RuntimeError(
            "Text-to-CAD native dependency mismatch: " + "; ".join(mismatches)
        )
    return tool_root


def _installed_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def _sidecar_tools() -> tuple[ToolIdentity, ...]:
    return (
        ToolIdentity(
            name="python",
            version=platform.python_version(),
            identity=sys.implementation.cache_tag or platform.python_implementation(),
        ),
        *(
            ToolIdentity(
                name=distribution,
                version=_installed_version(distribution),
                identity=f"project-pin:{expected}",
            )
            for distribution, expected in NATIVE_DEPENDENCY_PINS.items()
        ),
        ToolIdentity(
            name="text-to-cad",
            version=TEXT_TO_CAD_VERSION,
            identity=TEXT_TO_CAD_COMMIT,
        ),
    )


def _sidecar_cache_spec(
    step: FileFingerprint,
    kind: str,
    *,
    settings: object = SIDECAR_SETTINGS,
) -> StageCacheSpec:
    return StageCacheSpec(
        stage=SIDECAR_CACHE_STAGE,
        producer="text-to-cad-sidecar",
        producer_version=SIDECAR_PRODUCER_VERSION,
        producer_schema_version=SIDECAR_PRODUCER_SCHEMA_VERSION,
        sources=(step,),
        parameters={
            "step_sha256": step.sha256,
            "sidecar_kind": kind,
        },
        tools=_sidecar_tools(),
        settings=settings,
        outputs=(SIDECAR_OUTPUT,),
    )


def _load_sidecar_generator():
    tool_root = _require_runtime()
    cadpy_src = tool_root / "packages/cadpy/src"
    if not cadpy_src.is_dir():
        raise RuntimeError(f"Pinned cadpy source is missing: {cadpy_src}")
    sys.path.insert(0, str(cadpy_src))
    from cadpy.step_artifact import main as step_artifact_main

    return step_artifact_main


def _validate_sidecar(
    path: Path,
    source: FileFingerprint,
    kind: str,
) -> None:
    identity = glb_step_identity(path)
    if identity.step_hash != source.sha256:
        raise ValueError(
            "embedded_step_hash_mismatch: "
            f"expected {source.sha256}, found {identity.step_hash}"
        )
    if identity.entry_kind != kind:
        raise ValueError(
            f"entry_kind_mismatch: expected {kind}, found {identity.entry_kind}"
        )


def _require_current_source(
    repo_root: Path,
    step_path: Path,
    expected: FileFingerprint,
) -> None:
    current = fingerprint_file(repo_root, step_path)
    if current != expected:
        raise RuntimeError(
            "STEP artifact changed during sidecar processing: "
            f"expected {expected.sha256}, found {current.sha256}"
        )


def verify_cached_sidecar(
    repo_root: Path,
    step_path: Path,
    sidecar_path: Path,
    kind: str,
) -> VerifiedSidecar:
    """Require one current sidecar to match its verified cache entry and STEP."""

    repo_root = repo_root.resolve(strict=True)
    source = fingerprint_file(repo_root, step_path)
    spec = _sidecar_cache_spec(source, kind)
    cached = StageCache(repo_root).lookup(spec)
    if not cached.hit:
        raise RuntimeError(
            "sidecar has no current verified cache entry: "
            f"{cached.diagnostic()}"
        )
    resolved_sidecar = sidecar_path.expanduser()
    if not resolved_sidecar.is_absolute():
        resolved_sidecar = repo_root / resolved_sidecar
    resolved_sidecar = resolved_sidecar.resolve(strict=True)
    try:
        relative_sidecar = resolved_sidecar.relative_to(repo_root).as_posix()
    except ValueError as error:
        raise RuntimeError(
            f"sidecar escapes repository root: {resolved_sidecar}"
        ) from error
    _validate_sidecar(resolved_sidecar, source, kind)
    digest = _sha256_file(resolved_sidecar)
    size = resolved_sidecar.stat().st_size
    artifact = cached.artifact("sidecar")
    if digest != artifact.sha256 or size != artifact.size_bytes:
        raise RuntimeError(
            "sidecar file does not match its verified cache artifact: "
            f"expected {artifact.sha256}/{artifact.size_bytes}, found "
            f"{digest}/{size}"
        )
    _require_current_source(repo_root, repo_root / source.path, source)
    return VerifiedSidecar(
        step_path=source.path,
        step_sha256=source.sha256,
        sidecar_path=relative_sidecar,
        sidecar_sha256=digest,
        sidecar_size_bytes=size,
        kind=kind,
        cache_key=spec.key,
    )


def _sidecar(
    args: argparse.Namespace,
    *,
    repo_root: Path = ROOT,
    generator=None,
) -> int:
    repo_root = repo_root.resolve(strict=True)
    requested_step = args.step.expanduser()
    try:
        source = fingerprint_file(repo_root, requested_step)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"STEP artifact does not exist: {requested_step}"
        ) from None
    step_path = repo_root / source.path
    spec = _sidecar_cache_spec(source, args.kind)
    cache = StageCache(repo_root)
    final_sidecar = step_path.with_name(f".{step_path.name}.glb")
    staged_sidecar = job_output_path(final_sidecar)

    miss_reason = "force_regeneration" if args.force else ""
    replace_cache = bool(args.force)
    if not args.force:
        restored = cache.restore(spec, {"sidecar": staged_sidecar})
        if restored.hit:
            try:
                _validate_sidecar(staged_sidecar, source, args.kind)
            except ValueError as error:
                miss_reason = f"sidecar_validation_failed: {error}"
            else:
                _require_current_source(repo_root, step_path, source)
                artifact = restored.artifact("sidecar")
                print(
                    "cache hit "
                    f"stage={spec.stage} key={spec.key} "
                    f"sidecar_sha256={artifact.sha256}"
                )
                return 0
            cache.invalidate(spec)
            replace_cache = True
        else:
            miss_reason = f"{restored.reason}: {restored.detail}"
    print(f"cache miss stage={spec.stage} key={spec.key} reason={miss_reason}")

    step_artifact_main = generator or _load_sidecar_generator()
    stage_root = Path(os.environ[STAGE_ROOT_ENV]).resolve()
    scratch = stage_root.parent / "scratch" / "sidecar"
    scratch.mkdir(parents=True, exist_ok=True)
    scratch_step = scratch / step_path.name
    shutil.copy2(step_path, scratch_step)
    scratch_hash = _sha256_file(scratch_step)
    if scratch_hash != source.sha256:
        raise RuntimeError(
            "STEP artifact changed while preparing sidecar generation: "
            f"expected {source.sha256}, copied {scratch_hash}"
        )
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
    try:
        _validate_sidecar(generated, source, args.kind)
    except ValueError as error:
        raise RuntimeError(
            f"Text-to-CAD produced an invalid sidecar: {error}"
        ) from error

    published = cache.publish(
        spec,
        {"sidecar": generated},
        replace=replace_cache,
    )
    restored = cache.restore(spec, {"sidecar": staged_sidecar})
    if not restored.hit:
        raise RuntimeError(
            f"new sidecar cache entry could not be restored: {restored.diagnostic()}"
        )
    try:
        _validate_sidecar(staged_sidecar, source, args.kind)
    except ValueError as error:
        raise RuntimeError(f"restored sidecar failed validation: {error}") from error
    _require_current_source(repo_root, step_path, source)
    artifact = published.artifact("sidecar")
    print(
        "cache published "
        f"stage={spec.stage} key={spec.key} sidecar_sha256={artifact.sha256}"
    )
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
