from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import pytest

from cad_runner.cache import (
    CacheSafetyError,
    DeclaredOutput,
    StageCache,
    StageCacheSpec,
    ToolIdentity,
    fingerprint_file,
)
import cad_runner.cache as cache_module


def _spec(
    root: Path,
    *,
    source_names: tuple[str, ...] = ("source.step",),
    parameters: object = None,
    tool_version: str = "1.0",
    tool_identity: str = "commit-a",
    producer_schema_version: int = 1,
    settings: object = None,
) -> StageCacheSpec:
    return StageCacheSpec(
        stage="test-stage",
        producer="test-producer",
        producer_version="1",
        producer_schema_version=producer_schema_version,
        sources=tuple(fingerprint_file(root, name) for name in source_names),
        parameters={"value": 1} if parameters is None else parameters,
        tools=(ToolIdentity("test-tool", tool_version, tool_identity),),
        settings={"mesh": "default"} if settings is None else settings,
        outputs=(DeclaredOutput("result", "artifacts/result.bin"),),
    )


@pytest.fixture
def cache_repo():
    with tempfile.TemporaryDirectory(prefix="cad-cache-test-") as temporary:
        root = Path(temporary)
        (root / "source.step").write_bytes(b"alpha")
        (root / "second.step").write_bytes(b"beta")
        (root / "generated.bin").write_bytes(b"derived")
        yield root


def test_cache_spec_ordering_and_parameter_serialization_are_deterministic(
    cache_repo: Path,
) -> None:
    first = StageCacheSpec(
        stage="test-stage",
        producer="test-producer",
        producer_version="1",
        producer_schema_version=1,
        sources=(
            fingerprint_file(cache_repo, "second.step"),
            fingerprint_file(cache_repo, "source.step"),
        ),
        parameters={"z": [1, 2.0, True], "a": {"b": -0.0}},
        tools=(
            ToolIdentity("z-tool", "2", "commit-z"),
            ToolIdentity("a-tool", "1", "commit-a"),
        ),
        settings={"z": "last", "a": "first"},
        outputs=(
            DeclaredOutput("z", "artifacts/z.bin"),
            DeclaredOutput("a", "artifacts/a.bin"),
        ),
    )
    second = StageCacheSpec(
        stage="test-stage",
        producer="test-producer",
        producer_version="1",
        producer_schema_version=1,
        sources=tuple(reversed(first.sources)),
        parameters={"a": {"b": -0.0}, "z": [1, 2.0, True]},
        tools=tuple(reversed(first.tools)),
        settings={"a": "first", "z": "last"},
        outputs=tuple(reversed(first.outputs)),
    )

    assert first.identity() == second.identity()
    assert first.key == second.key
    assert first.key != _spec(cache_repo, parameters={"value": 1.0}).key


def test_publish_lookup_restore_and_manifest_bind_the_output_hash(
    cache_repo: Path,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)

    published = cache.publish(spec, {"result": cache_repo / "generated.bin"})
    restored_path = cache_repo / "build/restored.bin"
    restored = cache.restore(spec, {"result": restored_path})

    assert published.hit and restored.hit
    assert restored.reason == "verified"
    assert restored_path.read_bytes() == b"derived"
    manifest = json.loads(
        (cache.entry_path(spec) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["key"] == spec.key
    assert manifest["artifacts"][0]["sha256"] == restored.artifact("result").sha256
    assert len(manifest["entry_fingerprint"]) == 64


@pytest.mark.parametrize(
    "change",
    (
        lambda root: _spec(root, parameters={"value": 2}),
        lambda root: _spec(root, tool_version="2.0"),
        lambda root: _spec(root, tool_identity="commit-b"),
        lambda root: _spec(root, producer_schema_version=2),
        lambda root: _spec(root, settings={"mesh": "fine"}),
    ),
)
def test_parameter_tool_schema_and_settings_changes_invalidate_identity(
    cache_repo: Path,
    change,
) -> None:
    original = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(original, {"result": cache_repo / "generated.bin"})

    changed = change(cache_repo)

    assert changed.key != original.key
    result = cache.lookup(changed)
    assert not result.hit
    assert result.reason == "entry_missing"


def test_source_content_change_invalidates_old_and_new_identities(
    cache_repo: Path,
) -> None:
    original = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(original, {"result": cache_repo / "generated.bin"})

    (cache_repo / "source.step").write_bytes(b"bravo")

    stale = cache.lookup(original)
    current = _spec(cache_repo)
    assert not stale.hit
    assert stale.reason == "source_hash_drift"
    assert current.key != original.key
    assert cache.lookup(current).reason == "entry_missing"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        (lambda path: path.unlink(), "artifact_missing"),
        (lambda path: path.write_bytes(b"changed"), "artifact_hash_drift"),
    ),
)
def test_missing_or_modified_cached_artifact_is_a_miss(
    cache_repo: Path,
    mutation,
    reason: str,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    result = cache.publish(spec, {"result": cache_repo / "generated.bin"})
    mutation(result.artifact("result").path)

    lookup = cache.lookup(spec)

    assert not lookup.hit
    assert lookup.reason == reason


def test_corrupt_or_missing_manifest_fails_closed(cache_repo: Path) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    manifest = cache.entry_path(spec) / "manifest.json"
    manifest.write_text("{not-json", encoding="utf-8")

    corrupt = cache.lookup(spec)
    assert not corrupt.hit
    assert corrupt.reason == "manifest_malformed"

    manifest.unlink()
    missing = cache.lookup(spec)
    assert not missing.hit
    assert missing.reason == "manifest_missing"

    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["cache_schema_version"] = 0
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    old_schema = cache.lookup(spec)
    assert not old_schema.hit
    assert old_schema.reason == "manifest_schema_mismatch"


def test_duplicate_manifest_members_fail_closed(cache_repo: Path) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    manifest = cache.entry_path(spec) / "manifest.json"
    payload = manifest.read_text(encoding="utf-8").replace(
        '"cache_schema_version": 1,',
        '"cache_schema_version": 0,\n  "cache_schema_version": 1,',
        1,
    )
    manifest.write_text(payload, encoding="utf-8")

    lookup = cache.lookup(spec)

    assert not lookup.hit
    assert lookup.reason == "manifest_malformed"


def test_traversal_outside_paths_and_source_symlinks_are_rejected(
    cache_repo: Path,
) -> None:
    with pytest.raises(ValueError, match="output path"):
        DeclaredOutput("escape", "artifacts/../../escape")
    outside = cache_repo.parent / "outside.step"
    outside.write_bytes(b"outside")
    try:
        with pytest.raises(CacheSafetyError, match="outside the repository"):
            fingerprint_file(cache_repo, outside)
    finally:
        outside.unlink()

    link = cache_repo / "linked.step"
    link.symlink_to(cache_repo / "source.step")
    with pytest.raises(CacheSafetyError, match="symlink"):
        fingerprint_file(cache_repo, link)


@pytest.mark.parametrize(
    "path",
    ("sources/./part.step", "sources//part.step"),
)
def test_noncanonical_source_fingerprint_paths_are_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="source path"):
        cache_module.FileFingerprint(path, "0" * 64, 0)


@pytest.mark.parametrize(
    "path",
    ("artifacts/./result.bin", "artifacts//result.bin"),
)
def test_noncanonical_declared_output_paths_are_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="output path"):
        DeclaredOutput("result", path)


def test_raw_traversal_is_rejected_for_sources_destinations_and_cache_root(
    cache_repo: Path,
) -> None:
    with pytest.raises(CacheSafetyError, match="traversal"):
        fingerprint_file(cache_repo, Path("missing/../source.step"))
    with pytest.raises(CacheSafetyError, match="traversal"):
        StageCache(cache_repo, Path("build/../outside-cache"))

    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})

    restored = cache.restore(
        spec,
        {"result": Path("build/missing/../restored.bin")},
    )

    assert not restored.hit
    assert restored.reason == "unsafe_path"
    assert not (cache_repo / "build/restored.bin").exists()


def test_cached_artifact_symlink_and_manifest_traversal_are_rejected(
    cache_repo: Path,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    published = cache.publish(spec, {"result": cache_repo / "generated.bin"})
    artifact = published.artifact("result").path
    artifact.unlink()
    artifact.symlink_to(cache_repo / "generated.bin")

    symlinked = cache.lookup(spec)
    assert not symlinked.hit
    assert symlinked.reason == "unsafe_path"

    cache.invalidate(spec)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    manifest_path = cache.entry_path(spec) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][0]["path"] = "../../outside"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    traversing = cache.lookup(spec)
    assert not traversing.hit
    assert traversing.reason == "unsafe_path"


def test_restore_symlink_parent_causes_no_outside_mutation(
    cache_repo: Path,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    outside = cache_repo.parent / f"{cache_repo.name}-outside"
    outside.mkdir()
    linked = cache_repo / "build/linked"
    linked.symlink_to(outside, target_is_directory=True)
    try:
        result = cache.restore(
            spec,
            {"result": linked / "created/result.bin"},
        )

        assert not result.hit
        assert result.reason == "unsafe_path"
        assert not (outside / "created").exists()
    finally:
        linked.unlink()
        outside.rmdir()


def test_restore_rejects_parent_swapped_to_symlink_without_outside_mutation(
    cache_repo: Path,
    monkeypatch,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    destination_parent = cache_repo / "build/restore"
    destination_parent.mkdir()
    moved_parent = cache_repo / "build/restore-original"
    outside = cache_repo.parent / f"{cache_repo.name}-swapped-outside"
    outside.mkdir()
    original = cache_module._require_directory_binding
    swapped = False

    def swap_before_replace(repo_root, directory, descriptor):
        nonlocal swapped
        if Path(directory).name == destination_parent.name and not swapped:
            swapped = True
            destination_parent.rename(moved_parent)
            destination_parent.symlink_to(outside, target_is_directory=True)
        return original(repo_root, directory, descriptor)

    monkeypatch.setattr(
        cache_module,
        "_require_directory_binding",
        swap_before_replace,
    )
    try:
        result = cache.restore(
            spec,
            {"result": destination_parent / "result.bin"},
        )

        assert not result.hit
        assert result.reason == "unsafe_path"
        assert not tuple(outside.iterdir())
        assert not tuple(moved_parent.iterdir())
    finally:
        if destination_parent.is_symlink():
            destination_parent.unlink()
        if moved_parent.exists():
            moved_parent.rmdir()
        outside.rmdir()


def test_restore_rechecks_sources_after_copy(
    cache_repo: Path,
    monkeypatch,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    cache.publish(spec, {"result": cache_repo / "generated.bin"})
    original = cache_module._copy_verified_file

    def mutate_source_after_copy(*args, **kwargs):
        result = original(*args, **kwargs)
        (cache_repo / "source.step").write_bytes(b"bravo")
        return result

    monkeypatch.setattr(
        cache_module,
        "_copy_verified_file",
        mutate_source_after_copy,
    )

    restored = cache.restore(
        spec,
        {"result": cache_repo / "build/restored.bin"},
    )

    assert not restored.hit
    assert restored.reason == "source_hash_drift"


def test_publish_cleanup_failure_still_releases_lock_descriptor(
    cache_repo: Path,
    monkeypatch,
) -> None:
    spec = _spec(cache_repo)
    cache = StageCache(cache_repo)
    captured_locks: list[int] = []
    captured_stage_directories: list[int] = []
    original_open_lock = cache_module._open_lock
    original_open_directory = cache_module._open_repo_directory

    def capture_lock(*args, **kwargs):
        descriptor = original_open_lock(*args, **kwargs)
        captured_locks.append(descriptor)
        return descriptor

    def capture_directory(repo_root, directory, **kwargs):
        descriptor = original_open_directory(repo_root, directory, **kwargs)
        if Path(directory) == cache.cache_root / spec.stage:
            captured_stage_directories.append(descriptor)
        return descriptor

    def fail_copy(*args, **kwargs):
        raise RuntimeError("copy failed")

    def fail_cleanup(*args, **kwargs):
        raise OSError("cleanup failed")

    monkeypatch.setattr(cache_module, "_open_lock", capture_lock)
    monkeypatch.setattr(cache_module, "_open_repo_directory", capture_directory)
    monkeypatch.setattr(cache_module, "_copy_verified_file", fail_copy)
    monkeypatch.setattr(cache_module.shutil, "rmtree", fail_cleanup)

    with pytest.raises(OSError, match="cleanup failed"):
        cache.publish(spec, {"result": cache_repo / "generated.bin"})

    assert len(captured_locks) == 1
    assert captured_stage_directories
    with pytest.raises(OSError):
        os.fstat(captured_locks[0])
    for descriptor in captured_stage_directories:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_duplicate_output_paths_are_rejected(cache_repo: Path) -> None:
    with pytest.raises(ValueError, match="duplicate output path"):
        StageCacheSpec(
            stage="test-stage",
            producer="test-producer",
            producer_version="1",
            producer_schema_version=1,
            sources=(fingerprint_file(cache_repo, "source.step"),),
            parameters={},
            tools=(ToolIdentity("tool", "1", "commit"),),
            settings={},
            outputs=(
                DeclaredOutput("first", "artifacts/result.bin"),
                DeclaredOutput("second", "artifacts/result.bin"),
            ),
        )


def test_cache_modules_import_without_native_cad_libraries() -> None:
    import subprocess
    import sys

    program = (
        "import cad_runner.cache, cad_runner.glb, sys; "
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
    )
    assert completed.returncode == 0, completed.stderr
