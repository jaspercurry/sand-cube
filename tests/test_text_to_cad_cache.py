from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

import pytest

from cad_runner.cache import StageCache, fingerprint_file
from cad_runner.glb import glb_step_hash
from scripts import text_to_cad_artifacts


def _canonical_glb(step_hash: str, *, kind: str = "part") -> bytes:
    metadata = {
        "schemaVersion": 2,
        "profile": "index",
        "entryKind": kind,
        "sourceKind": "step",
        "sourcePath": "candidate.step",
        "stepPath": "candidate.step",
        "stepHash": step_hash,
    }
    metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    binary_length = len(metadata_bytes)
    binary = metadata_bytes + b"\0" * (-len(metadata_bytes) % 4)
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": binary_length}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(metadata_bytes)}
        ],
        "extensionsUsed": ["STEP_topology"],
        "extensions": {
            "STEP_topology": {
                "schemaVersion": 2,
                "entryKind": kind,
                "indexView": 0,
                "encoding": "utf-8",
            }
        },
    }
    document_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
    document_bytes += b" " * (-len(document_bytes) % 4)
    size = 12 + 8 + len(document_bytes) + 8 + len(binary)
    return (
        b"glTF"
        + struct.pack("<II", 2, size)
        + struct.pack("<II", len(document_bytes), 0x4E4F534A)
        + document_bytes
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


class FakeGenerator:
    def __init__(
        self,
        *,
        wrong_hash: str | None = None,
        wrong_kind: str | None = None,
    ) -> None:
        self.calls = 0
        self.wrong_hash = wrong_hash
        self.wrong_kind = wrong_kind

    def __call__(self, command: list[str]) -> int:
        self.calls += 1
        repo_root = Path(command[command.index("--repo-root") + 1])
        step = Path(command[command.index("--step") + 1])
        kind = self.wrong_kind or command[command.index("--kind") + 1]
        digest = self.wrong_hash or sha256(step.read_bytes()).hexdigest()
        (repo_root / f".{step.name}.glb").write_bytes(_canonical_glb(digest, kind=kind))
        return 0


@pytest.fixture
def sidecar_repo(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="sidecar-cache-test-") as temporary:
        root = Path(temporary)
        step = root / "build/candidate.step"
        step.parent.mkdir(parents=True)
        step.write_bytes(b"STEP alpha")
        stage = root / "build/.cad-runtime/jobs/test/stage"
        stage.mkdir(parents=True)
        monkeypatch.setenv("CAD_JOB_REPO_ROOT", str(root))
        monkeypatch.setenv("CAD_JOB_STAGE_ROOT", str(stage))
        yield root, step, stage


def _args(step: Path, *, kind: str = "part", force: bool = False):
    return argparse.Namespace(
        step=step,
        kind=kind,
        artifact_root=None,
        force=force,
    )


def _staged_sidecar(stage: Path, step: Path, root: Path) -> Path:
    relative = step.with_name(f".{step.name}.glb").relative_to(root)
    return stage / relative


def test_repeated_unchanged_sidecar_request_is_a_verified_hit(
    sidecar_repo,
    capsys,
) -> None:
    root, step, stage = sidecar_repo
    generator = FakeGenerator()

    assert (
        text_to_cad_artifacts._sidecar(
            _args(step),
            repo_root=root,
            generator=generator,
        )
        == 0
    )
    first_output = capsys.readouterr().out
    staged = _staged_sidecar(stage, step, root)
    staged.unlink()
    assert (
        text_to_cad_artifacts._sidecar(
            _args(step),
            repo_root=root,
            generator=generator,
        )
        == 0
    )
    second_output = capsys.readouterr().out

    assert generator.calls == 1
    assert "cache miss" in first_output
    assert "cache published" in first_output
    assert "cache hit" in second_output
    assert glb_step_hash(staged) == sha256(step.read_bytes()).hexdigest()


def test_step_and_sidecar_kind_changes_are_cache_misses(sidecar_repo) -> None:
    root, step, _stage = sidecar_repo
    generator = FakeGenerator()

    text_to_cad_artifacts._sidecar(
        _args(step),
        repo_root=root,
        generator=generator,
    )
    step.write_bytes(b"STEP bravo")
    text_to_cad_artifacts._sidecar(
        _args(step),
        repo_root=root,
        generator=generator,
    )
    text_to_cad_artifacts._sidecar(
        _args(step, kind="assembly"),
        repo_root=root,
        generator=generator,
    )

    assert generator.calls == 3


def test_force_bypasses_reuse_and_produces_current_verified_sidecar(
    sidecar_repo,
    capsys,
) -> None:
    root, step, stage = sidecar_repo
    generator = FakeGenerator()
    text_to_cad_artifacts._sidecar(
        _args(step),
        repo_root=root,
        generator=generator,
    )
    capsys.readouterr()

    text_to_cad_artifacts._sidecar(
        _args(step, force=True),
        repo_root=root,
        generator=generator,
    )
    output = capsys.readouterr().out

    assert generator.calls == 2
    assert "reason=force_regeneration" in output
    assert (
        glb_step_hash(_staged_sidecar(stage, step, root))
        == sha256(step.read_bytes()).hexdigest()
    )


def test_wrong_step_hash_in_cached_sidecar_is_invalidated_and_regenerated(
    sidecar_repo,
    capsys,
) -> None:
    root, step, stage = sidecar_repo
    source = fingerprint_file(root, step)
    spec = text_to_cad_artifacts._sidecar_cache_spec(source, "part")
    wrong = root / "build/wrong.glb"
    wrong.write_bytes(_canonical_glb("0" * 64))
    StageCache(root).publish(spec, {"sidecar": wrong})
    generator = FakeGenerator()

    text_to_cad_artifacts._sidecar(
        _args(step),
        repo_root=root,
        generator=generator,
    )
    output = capsys.readouterr().out

    assert generator.calls == 1
    assert "embedded_step_hash_mismatch" in output
    assert glb_step_hash(_staged_sidecar(stage, step, root)) == source.sha256


def test_generator_sidecar_with_wrong_step_hash_is_never_published(
    sidecar_repo,
) -> None:
    root, step, _stage = sidecar_repo
    generator = FakeGenerator(wrong_hash="0" * 64)
    source = fingerprint_file(root, step)
    spec = text_to_cad_artifacts._sidecar_cache_spec(source, "part")

    with pytest.raises(RuntimeError, match="embedded_step_hash_mismatch"):
        text_to_cad_artifacts._sidecar(
            _args(step),
            repo_root=root,
            generator=generator,
        )

    assert not StageCache(root).lookup(spec).hit


def test_wrong_kind_in_cached_sidecar_is_invalidated_and_regenerated(
    sidecar_repo,
    capsys,
) -> None:
    root, step, stage = sidecar_repo
    source = fingerprint_file(root, step)
    spec = text_to_cad_artifacts._sidecar_cache_spec(source, "part")
    wrong = root / "build/wrong-kind.glb"
    wrong.write_bytes(_canonical_glb(source.sha256, kind="assembly"))
    StageCache(root).publish(spec, {"sidecar": wrong})
    generator = FakeGenerator()

    text_to_cad_artifacts._sidecar(
        _args(step),
        repo_root=root,
        generator=generator,
    )
    output = capsys.readouterr().out

    assert generator.calls == 1
    assert "entry_kind_mismatch" in output
    assert glb_step_hash(_staged_sidecar(stage, step, root)) == source.sha256


def test_generator_sidecar_with_wrong_kind_is_never_published(
    sidecar_repo,
) -> None:
    root, step, _stage = sidecar_repo
    generator = FakeGenerator(wrong_kind="assembly")
    source = fingerprint_file(root, step)
    spec = text_to_cad_artifacts._sidecar_cache_spec(source, "part")

    with pytest.raises(RuntimeError, match="entry_kind_mismatch"):
        text_to_cad_artifacts._sidecar(
            _args(step),
            repo_root=root,
            generator=generator,
        )

    assert not StageCache(root).lookup(spec).hit


def test_native_dependency_versions_participate_in_sidecar_identity(
    sidecar_repo,
    monkeypatch,
) -> None:
    root, step, _stage = sidecar_repo
    source = fingerprint_file(root, step)
    original = text_to_cad_artifacts._sidecar_cache_spec(source, "part")
    real_version = text_to_cad_artifacts._installed_version

    def changed_version(distribution: str) -> str:
        if distribution == "build123d":
            return "changed"
        return real_version(distribution)

    monkeypatch.setattr(
        text_to_cad_artifacts,
        "_installed_version",
        changed_version,
    )
    changed = text_to_cad_artifacts._sidecar_cache_spec(source, "part")

    assert changed.key != original.key


def test_runtime_rejects_dirty_generator_sources_and_dependency_drift(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool_root = tmp_path / "text-to-cad"
    version = tool_root / "plugins/cad/VERSION"
    version.parent.mkdir(parents=True)
    version.write_text(text_to_cad_artifacts.TEXT_TO_CAD_VERSION)
    monkeypatch.setattr(text_to_cad_artifacts, "_tool_root", lambda: tool_root)
    monkeypatch.setattr(
        text_to_cad_artifacts,
        "_installed_version",
        lambda distribution: text_to_cad_artifacts.NATIVE_DEPENDENCY_PINS[distribution],
    )

    def dirty_run(command, **_kwargs):
        if "rev-parse" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                text_to_cad_artifacts.TEXT_TO_CAD_COMMIT + "\n",
                "",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            " M packages/cadpy/src/cadpy/step_artifact.py\n",
            "",
        )

    monkeypatch.setattr(text_to_cad_artifacts.subprocess, "run", dirty_run)
    with pytest.raises(RuntimeError, match="tracked modifications"):
        text_to_cad_artifacts._require_runtime()

    def clean_run(command, **_kwargs):
        stdout = (
            text_to_cad_artifacts.TEXT_TO_CAD_COMMIT + "\n"
            if "rev-parse" in command
            else ""
        )
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(text_to_cad_artifacts.subprocess, "run", clean_run)
    monkeypatch.setattr(
        text_to_cad_artifacts,
        "_installed_version",
        lambda distribution: (
            "changed"
            if distribution == "build123d"
            else text_to_cad_artifacts.NATIVE_DEPENDENCY_PINS[distribution]
        ),
    )
    with pytest.raises(RuntimeError, match="native dependency mismatch"):
        text_to_cad_artifacts._require_runtime()


def test_sidecar_cache_import_path_is_native_free() -> None:
    import subprocess
    import sys

    program = (
        "import scripts.text_to_cad_artifacts, sys; "
        "forbidden=('build123d','OCP','cadquery','vtk'); "
        "loaded=[name for name in sys.modules if name.split('.')[0] in forbidden]; "
        "assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "CAD_JOB_WORKER": "1"},
    )
    assert completed.returncode == 0, completed.stderr
