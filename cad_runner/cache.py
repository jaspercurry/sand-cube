"""Content-addressed, native-free cache primitives for derived CAD stages."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from typing import Any, Mapping, Sequence
import uuid


CACHE_SCHEMA_VERSION = 1
MAX_MANIFEST_BYTES = 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class CacheSafetyError(RuntimeError):
    """A cache or repository path could not be used safely."""


class _DuplicateJsonKey(ValueError):
    pass


@dataclass(frozen=True)
class FileFingerprint:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _validate_relative_path(self.path, label="source path")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError(f"invalid source SHA-256: {self.sha256!r}")
        if (
            not isinstance(self.size_bytes, int)
            or isinstance(self.size_bytes, bool)
            or self.size_bytes < 0
        ):
            raise ValueError("source size must be a non-negative integer")


@dataclass(frozen=True)
class ToolIdentity:
    name: str
    version: str
    identity: str

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "tool name")
        if (
            not isinstance(self.version, str)
            or not self.version
            or not isinstance(self.identity, str)
            or not self.identity
        ):
            raise ValueError("tool version and identity must be non-empty")


@dataclass(frozen=True)
class DeclaredOutput:
    name: str
    path: str

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "output name")
        relative = _validate_relative_path(self.path, label="output path")
        if len(relative.parts) < 2 or relative.parts[0] != "artifacts":
            raise ValueError("cache outputs must live below artifacts/")


@dataclass(frozen=True)
class StageCacheSpec:
    stage: str
    producer: str
    producer_version: str
    producer_schema_version: int
    sources: tuple[FileFingerprint, ...]
    parameters: Any
    tools: tuple[ToolIdentity, ...]
    settings: Any
    outputs: tuple[DeclaredOutput, ...]

    def __post_init__(self) -> None:
        _validate_identifier(self.stage, "stage")
        _validate_identifier(self.producer, "producer")
        if not isinstance(self.producer_version, str) or not self.producer_version:
            raise ValueError("producer version must be non-empty")
        if (
            not isinstance(self.producer_schema_version, int)
            or isinstance(self.producer_schema_version, bool)
            or self.producer_schema_version < 1
        ):
            raise ValueError("producer schema version must be a positive integer")
        sources = tuple(sorted(self.sources, key=lambda item: item.path))
        tools = tuple(sorted(self.tools, key=lambda item: item.name))
        outputs = tuple(sorted(self.outputs, key=lambda item: item.name))
        _require_unique((item.path for item in sources), "source path")
        _require_unique((item.name for item in tools), "tool name")
        _require_unique((item.name for item in outputs), "output name")
        _require_unique((item.path for item in outputs), "output path")
        if not sources or not tools or not outputs:
            raise ValueError(
                "cache specifications require sources, tools, and declared outputs"
            )
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "tools", tools)
        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(
            self, "parameters", canonical_parameter_value(self.parameters)
        )
        object.__setattr__(self, "settings", canonical_parameter_value(self.settings))

    def identity(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "producer": {
                "name": self.producer,
                "version": self.producer_version,
                "schema_version": self.producer_schema_version,
            },
            "sources": [
                {
                    "path": source.path,
                    "sha256": source.sha256,
                    "size_bytes": source.size_bytes,
                }
                for source in self.sources
            ],
            "parameters": self.parameters,
            "tools": [
                {
                    "name": tool.name,
                    "version": tool.version,
                    "identity": tool.identity,
                }
                for tool in self.tools
            ],
            "settings": self.settings,
            "outputs": [
                {"name": output.name, "path": output.path} for output in self.outputs
            ],
        }

    @property
    def key(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.identity())).hexdigest()


@dataclass(frozen=True)
class CachedArtifact:
    name: str
    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class CacheResult:
    hit: bool
    reason: str
    detail: str
    key: str
    artifacts: tuple[CachedArtifact, ...] = ()

    @property
    def status(self) -> str:
        return "hit" if self.hit else "miss"

    def artifact(self, name: str) -> CachedArtifact:
        for artifact in self.artifacts:
            if artifact.name == name:
                return artifact
        raise KeyError(name)

    def diagnostic(self) -> str:
        return (
            f"{self.status} reason={self.reason} key={self.key} {self.detail}".strip()
        )


def canonical_parameter_value(value: Any) -> Any:
    """Return a type-preserving JSON value for deterministic parameter hashing."""

    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("cache parameters must not contain NaN or infinity")
        return {"type": "float", "value": value.hex()}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    if isinstance(value, Mapping):
        items = []
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("cache parameter mapping keys must be strings")
            items.append({"key": key, "value": canonical_parameter_value(value[key])})
        return {"type": "mapping", "items": items}
    if isinstance(value, (list, tuple)):
        return {
            "type": "sequence",
            "items": [canonical_parameter_value(item) for item in value],
        }
    raise TypeError(f"unsupported cache parameter type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def fingerprint_file(repo_root: str | Path, path: str | Path) -> FileFingerprint:
    root = Path(repo_root).resolve(strict=True)
    candidate, relative = _repo_path(root, path)
    digest, size = _measure_file(root, candidate)
    return FileFingerprint(relative.as_posix(), digest, size)


class StageCache:
    """Verified cache storage under ``build/.cad-cache/stages``."""

    def __init__(
        self,
        repo_root: str | Path,
        cache_root: str | Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve(strict=True)
        requested = cache_root or Path("build/.cad-cache/stages")
        self.cache_root, _ = _repo_path(
            self.repo_root,
            requested,
            allow_missing=True,
        )

    def entry_path(self, spec: StageCacheSpec) -> Path:
        return self.cache_root / spec.stage / spec.key

    def lookup(self, spec: StageCacheSpec) -> CacheResult:
        source_result = self._verify_sources(spec)
        if source_result is not None:
            return source_result
        entry = self.entry_path(spec)
        if not entry.exists() and not entry.is_symlink():
            return self._miss(spec, "entry_missing", "no entry for current identity")
        try:
            _require_safe_tree_path(self.repo_root, entry, kind="directory")
            manifest_path = entry / "manifest.json"
            payload = _read_json_manifest(self.repo_root, manifest_path)
            artifacts = self._validate_manifest(spec, entry, payload)
        except (CacheSafetyError, OSError, ValueError, TypeError) as error:
            return self._miss(
                spec,
                _reason_for_error(error),
                str(error),
            )
        return CacheResult(
            True,
            "verified",
            f"verified {len(artifacts)} declared artifact(s)",
            spec.key,
            tuple(artifacts),
        )

    def restore(
        self,
        spec: StageCacheSpec,
        destinations: Mapping[str, str | Path],
    ) -> CacheResult:
        result = self.lookup(spec)
        if not result.hit:
            return result
        expected_names = {output.name for output in spec.outputs}
        if set(destinations) != expected_names:
            return self._miss(
                spec,
                "destination_mismatch",
                "restore destinations do not match declared outputs",
            )
        try:
            for artifact in result.artifacts:
                destination, _ = _repo_path(
                    self.repo_root,
                    destinations[artifact.name],
                    allow_missing=True,
                )
                _copy_verified_file(
                    self.repo_root,
                    artifact.path,
                    destination,
                    artifact.sha256,
                    artifact.size_bytes,
                )
        except (CacheSafetyError, OSError, ValueError) as error:
            return self._miss(spec, _reason_for_error(error), str(error))
        source_result = self._verify_sources(spec)
        if source_result is not None:
            return source_result
        return result

    def publish(
        self,
        spec: StageCacheSpec,
        artifacts: Mapping[str, str | Path],
        *,
        replace: bool = False,
    ) -> CacheResult:
        source_result = self._verify_sources(spec)
        if source_result is not None:
            raise CacheSafetyError(source_result.detail)
        expected_names = {output.name for output in spec.outputs}
        if set(artifacts) != expected_names:
            raise ValueError("published artifacts do not match declared outputs")
        sources: dict[str, Path] = {}
        for name, value in artifacts.items():
            source, _ = _repo_path(self.repo_root, value)
            _require_safe_tree_path(self.repo_root, source, kind="file")
            sources[name] = source

        stage_root = self.cache_root / spec.stage
        _ensure_safe_directory(self.repo_root, stage_root)
        lock_root = stage_root / ".locks"
        _ensure_safe_directory(self.repo_root, lock_root)
        lock_path = lock_root / f"{spec.key}.lock"
        descriptor = _open_lock(self.repo_root, lock_path)
        try:
            stage_descriptor = _open_repo_directory(self.repo_root, stage_root)
        except BaseException:
            os.close(descriptor)
            raise
        temporary: Path | None = None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            _require_directory_binding(
                self.repo_root,
                stage_root,
                stage_descriptor,
            )
            current = self.lookup(spec)
            if current.hit and not replace:
                return current

            entry = self.entry_path(spec)
            _require_directory_binding(
                self.repo_root,
                stage_root,
                stage_descriptor,
            )
            if entry.exists() or entry.is_symlink():
                _remove_cache_entry(self.repo_root, entry)
            temporary = stage_root / f".tmp-{spec.key}-{uuid.uuid4().hex}"
            _require_directory_binding(
                self.repo_root,
                stage_root,
                stage_descriptor,
            )
            os.mkdir(temporary.name, mode=0o700, dir_fd=stage_descriptor)
            artifact_records: list[dict[str, Any]] = []
            by_name = {output.name: output for output in spec.outputs}
            for name in sorted(sources):
                output = by_name[name]
                destination = temporary / PurePosixPath(output.path)
                digest, size = _copy_verified_file(
                    self.repo_root,
                    sources[name],
                    destination,
                )
                artifact_records.append(
                    {
                        "name": name,
                        "path": output.path,
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )

            identity = spec.identity()
            entry_fingerprint = _entry_fingerprint(
                spec.key,
                identity,
                artifact_records,
            )
            manifest = {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "stage": spec.stage,
                "key": spec.key,
                "spec": identity,
                "artifacts": artifact_records,
                "entry_fingerprint": entry_fingerprint,
                "published_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            _write_manifest(
                self.repo_root,
                temporary / "manifest.json",
                manifest,
            )
            _fsync_directory(self.repo_root, temporary)
            _require_directory_binding(
                self.repo_root,
                stage_root,
                stage_descriptor,
            )
            os.rename(
                temporary.name,
                entry.name,
                src_dir_fd=stage_descriptor,
                dst_dir_fd=stage_descriptor,
            )
            temporary = None
            os.fsync(stage_descriptor)
        finally:
            try:
                if temporary is not None:
                    try:
                        shutil.rmtree(temporary.name, dir_fd=stage_descriptor)
                    except FileNotFoundError:
                        pass
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    try:
                        os.close(descriptor)
                    finally:
                        os.close(stage_descriptor)

        result = self.lookup(spec)
        if not result.hit:
            raise CacheSafetyError(
                f"new cache entry failed verification: {result.diagnostic()}"
            )
        return result

    def invalidate(self, spec: StageCacheSpec) -> bool:
        entry = self.entry_path(spec)
        if not entry.exists() and not entry.is_symlink():
            return False
        stage_root = self.cache_root / spec.stage
        _ensure_safe_directory(self.repo_root, stage_root)
        lock_root = stage_root / ".locks"
        _ensure_safe_directory(self.repo_root, lock_root)
        descriptor = _open_lock(
            self.repo_root,
            lock_root / f"{spec.key}.lock",
        )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            if not entry.exists() and not entry.is_symlink():
                return False
            _remove_cache_entry(self.repo_root, entry)
            _fsync_directory(self.repo_root, stage_root)
            return True
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _verify_sources(self, spec: StageCacheSpec) -> CacheResult | None:
        for source in spec.sources:
            try:
                candidate, _ = _repo_path(self.repo_root, source.path)
                digest, size = _measure_file(self.repo_root, candidate)
            except FileNotFoundError:
                return self._miss(
                    spec,
                    "source_missing",
                    f"source file is missing: {source.path}",
                )
            except (CacheSafetyError, OSError, ValueError) as error:
                return self._miss(spec, _reason_for_error(error), str(error))
            if size != source.size_bytes:
                return self._miss(
                    spec,
                    "source_size_drift",
                    f"{source.path}: expected {source.size_bytes}, found {size}",
                )
            if digest != source.sha256:
                return self._miss(
                    spec,
                    "source_hash_drift",
                    f"{source.path}: SHA-256 changed",
                )
        return None

    def _validate_manifest(
        self,
        spec: StageCacheSpec,
        entry: Path,
        payload: Any,
    ) -> list[CachedArtifact]:
        if not isinstance(payload, dict):
            raise ValueError("cache manifest must be a JSON object")
        expected_manifest_fields = {
            "cache_schema_version",
            "stage",
            "key",
            "spec",
            "artifacts",
            "entry_fingerprint",
            "published_at",
        }
        if set(payload) != expected_manifest_fields:
            raise ValueError("cache manifest fields mismatch")
        if payload.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
            raise ValueError("cache manifest schema mismatch")
        if payload.get("stage") != spec.stage or payload.get("key") != spec.key:
            raise ValueError("cache manifest key or stage mismatch")
        if payload.get("spec") != spec.identity():
            raise ValueError("cache manifest specification mismatch")
        if not isinstance(payload.get("published_at"), str):
            raise ValueError("cache manifest publication time is malformed")
        records = payload.get("artifacts")
        if not isinstance(records, list):
            raise ValueError("cache manifest artifacts must be a list")
        expected = {output.name: output for output in spec.outputs}
        actual_names = [
            record.get("name") for record in records if isinstance(record, dict)
        ]
        if len(records) != len(expected) or set(actual_names) != set(expected):
            raise ValueError("cache manifest declared outputs mismatch")

        artifacts: list[CachedArtifact] = []
        canonical_records: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("cache manifest artifact record is malformed")
            if set(record) != {"name", "path", "sha256", "size_bytes"}:
                raise ValueError("cache manifest artifact fields mismatch")
            name = record.get("name")
            output = expected.get(name)
            if output is None or record.get("path") != output.path:
                raise CacheSafetyError("unsafe or undeclared cache artifact path")
            digest = record.get("sha256")
            size = record.get("size_bytes")
            if (
                not isinstance(digest, str)
                or not _SHA256.fullmatch(digest)
                or not isinstance(size, int)
                or isinstance(size, bool)
                or size < 0
            ):
                raise ValueError("cache manifest artifact fingerprint is malformed")
            artifact_path = entry / PurePosixPath(output.path)
            actual_digest, actual_size = _measure_file(
                self.repo_root,
                artifact_path,
            )
            if actual_size != size:
                raise ValueError(f"cached artifact size drift: {output.path}")
            if actual_digest != digest:
                raise ValueError(f"cached artifact hash drift: {output.path}")
            canonical = {
                "name": name,
                "path": output.path,
                "sha256": digest,
                "size_bytes": size,
            }
            canonical_records.append(canonical)
            artifacts.append(CachedArtifact(name, artifact_path, digest, size))
        canonical_records.sort(key=lambda item: item["name"])
        if payload.get("entry_fingerprint") != _entry_fingerprint(
            spec.key,
            spec.identity(),
            canonical_records,
        ):
            raise ValueError("cache manifest entry fingerprint mismatch")
        return sorted(artifacts, key=lambda item: item.name)

    @staticmethod
    def _miss(spec: StageCacheSpec, reason: str, detail: str) -> CacheResult:
        return CacheResult(False, reason, detail, spec.key)


def _validate_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")


def _require_unique(values: Sequence[str] | Any, label: str) -> None:
    materialized = tuple(values)
    if len(materialized) != len(set(materialized)):
        raise ValueError(f"duplicate {label}")


def _validate_relative_path(value: str, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"invalid {label}: {value!r}")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "." in relative.parts
        or relative.as_posix() != value
    ):
        raise ValueError(f"invalid {label}: {value!r}")
    return relative


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _repo_path(
    repo_root: Path,
    value: str | Path,
    *,
    allow_missing: bool = False,
) -> tuple[Path, Path]:
    path = Path(value).expanduser()
    if ".." in path.parts:
        raise CacheSafetyError(f"path traversal is not allowed: {path}")
    candidate = path if path.is_absolute() else repo_root / path
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(repo_root)
    except ValueError:
        root_info = repo_root.stat()
        alias_root: Path | None = None
        for ancestor in candidate.parents:
            try:
                ancestor_info = ancestor.stat()
            except OSError:
                continue
            if (
                stat.S_ISDIR(ancestor_info.st_mode)
                and ancestor_info.st_dev == root_info.st_dev
                and ancestor_info.st_ino == root_info.st_ino
            ):
                alias_root = ancestor
                break
        if alias_root is None:
            raise CacheSafetyError(f"path is outside the repository: {candidate}")
        relative = candidate.relative_to(alias_root)
        candidate = repo_root / relative
    if not relative.parts:
        raise CacheSafetyError("repository root is not a cache file path")
    if not allow_missing and not candidate.exists() and not candidate.is_symlink():
        raise FileNotFoundError(candidate)
    return candidate, relative


def _open_repo_directory(
    repo_root: Path,
    directory: Path,
    *,
    create: bool = False,
) -> int:
    directory = Path(os.path.abspath(directory))
    if directory == repo_root:
        relative = Path()
    else:
        directory, relative = _repo_path(
            repo_root,
            directory,
            allow_missing=create,
        )
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(repo_root, flags)
    try:
        for part in relative.parts:
            try:
                child = os.open(
                    part,
                    flags,
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
                try:
                    child = os.open(
                        part,
                        flags,
                        dir_fd=descriptor,
                    )
                except OSError as error:
                    raise CacheSafetyError(
                        f"unsafe symlink or non-directory component: {directory / part}"
                    ) from error
            except OSError as error:
                raise CacheSafetyError(
                    f"unsafe symlink or non-directory component: {directory / part}"
                ) from error
            os.close(descriptor)
            descriptor = child
        info = os.fstat(descriptor)
        if not stat.S_ISDIR(info.st_mode):
            raise CacheSafetyError(f"path is not a directory: {directory}")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _require_directory_binding(
    repo_root: Path,
    directory: Path,
    descriptor: int,
) -> None:
    expected = os.fstat(descriptor)
    try:
        current_descriptor = _open_repo_directory(repo_root, directory)
    except (OSError, CacheSafetyError) as error:
        raise CacheSafetyError(
            f"directory changed while being used: {directory}"
        ) from error
    try:
        current = os.fstat(current_descriptor)
    finally:
        os.close(current_descriptor)
    if expected.st_dev != current.st_dev or expected.st_ino != current.st_ino:
        raise CacheSafetyError(f"directory changed while being used: {directory}")


def _open_repo_regular_file(
    repo_root: Path,
    path: Path,
) -> tuple[Path, int, int]:
    candidate, _ = _repo_path(repo_root, path)
    parent_descriptor = _open_repo_directory(repo_root, candidate.parent)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(
            candidate.name,
            flags,
            dir_fd=parent_descriptor,
        )
    except OSError as error:
        os.close(parent_descriptor)
        if isinstance(error, FileNotFoundError):
            raise
        raise CacheSafetyError(
            f"cannot safely open file (symlink or path race): {candidate}"
        ) from error
    info = os.fstat(descriptor)
    try:
        path_info = os.stat(
            candidate.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError:
        os.close(descriptor)
        os.close(parent_descriptor)
        raise
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(path_info.st_mode)
        or info.st_dev != path_info.st_dev
        or info.st_ino != path_info.st_ino
    ):
        os.close(descriptor)
        os.close(parent_descriptor)
        raise CacheSafetyError(f"path is not a stable regular file: {candidate}")
    return candidate, descriptor, parent_descriptor


def _require_safe_tree_path(repo_root: Path, path: Path, *, kind: str) -> None:
    candidate, relative = _repo_path(
        repo_root,
        path,
        allow_missing=kind == "destination",
    )
    current = repo_root
    for index, part in enumerate(relative.parts):
        current /= part
        is_final = index == len(relative.parts) - 1
        try:
            info = current.lstat()
        except FileNotFoundError:
            if kind == "destination":
                continue
            raise
        if stat.S_ISLNK(info.st_mode):
            raise CacheSafetyError(f"unsafe symlink in repository path: {current}")
        if not is_final and not stat.S_ISDIR(info.st_mode):
            raise CacheSafetyError(f"path parent is not a directory: {current}")
        if is_final and kind == "file" and not stat.S_ISREG(info.st_mode):
            raise CacheSafetyError(f"path is not a regular file: {current}")
        if is_final and kind == "directory" and not stat.S_ISDIR(info.st_mode):
            raise CacheSafetyError(f"path is not a directory: {current}")
    if kind != "destination" and not candidate.exists():
        raise FileNotFoundError(candidate)


def _measure_file(repo_root: Path, path: Path) -> tuple[str, int]:
    candidate, descriptor, parent_descriptor = _open_repo_regular_file(
        repo_root,
        path,
    )
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        after = os.fstat(descriptor)
        _require_stable_open_file(
            repo_root,
            candidate,
            before,
            after,
            parent_descriptor,
        )
    finally:
        os.close(descriptor)
        os.close(parent_descriptor)
    return digest.hexdigest(), after.st_size


def _require_stable_open_file(
    repo_root: Path,
    path: Path,
    before: os.stat_result,
    after: os.stat_result,
    parent_descriptor: int,
) -> None:
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in fields):
        raise CacheSafetyError(f"file changed while being read: {path}")
    try:
        current = os.stat(
            path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        raise CacheSafetyError(f"file changed while being read: {path}") from None
    if (
        stat.S_ISLNK(current.st_mode)
        or current.st_dev != after.st_dev
        or current.st_ino != after.st_ino
    ):
        raise CacheSafetyError(f"file changed while being read: {path}")
    _require_directory_binding(
        repo_root,
        path.parent,
        parent_descriptor,
    )


def _copy_verified_file(
    repo_root: Path,
    source: Path,
    destination: Path,
    expected_hash: str | None = None,
    expected_size: int | None = None,
) -> tuple[str, int]:
    with ExitStack() as descriptors:
        (
            source,
            source_descriptor,
            source_parent_descriptor,
        ) = _open_repo_regular_file(repo_root, source)
        descriptors.callback(os.close, source_parent_descriptor)
        descriptors.callback(os.close, source_descriptor)
        destination, _ = _repo_path(repo_root, destination, allow_missing=True)
        destination_parent_descriptor = _open_repo_directory(
            repo_root,
            destination.parent,
            create=True,
        )
        descriptors.callback(os.close, destination_parent_descriptor)
        temporary_name = f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        output_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            output_flags |= os.O_NOFOLLOW
        temporary_descriptor = os.open(
            temporary_name,
            output_flags,
            0o600,
            dir_fd=destination_parent_descriptor,
        )
        descriptors.callback(os.close, temporary_descriptor)
        before = os.fstat(source_descriptor)
        digest = hashlib.sha256()
        size = 0
        try:
            with os.fdopen(source_descriptor, "rb", closefd=False) as input_stream:
                with os.fdopen(
                    temporary_descriptor,
                    "wb",
                    closefd=False,
                ) as output_stream:
                    for chunk in iter(lambda: input_stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                        size += len(chunk)
                        output_stream.write(chunk)
                    output_stream.flush()
                    os.fsync(output_stream.fileno())
            after = os.fstat(source_descriptor)
            _require_stable_open_file(
                repo_root,
                source,
                before,
                after,
                source_parent_descriptor,
            )
            actual_hash = digest.hexdigest()
            if expected_size is not None and size != expected_size:
                raise ValueError(f"cached artifact size drift: {source}")
            if expected_hash is not None and actual_hash != expected_hash:
                raise ValueError(f"cached artifact hash drift: {source}")
            _require_directory_binding(
                repo_root,
                destination.parent,
                destination_parent_descriptor,
            )
            try:
                destination_info = os.stat(
                    destination.name,
                    dir_fd=destination_parent_descriptor,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                if stat.S_ISLNK(destination_info.st_mode) or not stat.S_ISREG(
                    destination_info.st_mode
                ):
                    raise CacheSafetyError(f"unsafe restore destination: {destination}")
            os.replace(
                temporary_name,
                destination.name,
                src_dir_fd=destination_parent_descriptor,
                dst_dir_fd=destination_parent_descriptor,
            )
            os.fsync(destination_parent_descriptor)
            try:
                _require_directory_binding(
                    repo_root,
                    destination.parent,
                    destination_parent_descriptor,
                )
            except BaseException:
                try:
                    os.unlink(
                        destination.name,
                        dir_fd=destination_parent_descriptor,
                    )
                    os.fsync(destination_parent_descriptor)
                except FileNotFoundError:
                    pass
                raise
            return actual_hash, size
        finally:
            try:
                os.unlink(
                    temporary_name,
                    dir_fd=destination_parent_descriptor,
                )
            except FileNotFoundError:
                pass


def _read_json_manifest(repo_root: Path, path: Path) -> Any:
    try:
        candidate, descriptor, parent_descriptor = _open_repo_regular_file(
            repo_root,
            path,
        )
    except FileNotFoundError:
        raise ValueError("cache manifest is missing") from None
    try:
        before = os.fstat(descriptor)
        if before.st_size > MAX_MANIFEST_BYTES:
            raise ValueError("cache manifest exceeds safety limit")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read(MAX_MANIFEST_BYTES + 1)
        after = os.fstat(descriptor)
        _require_stable_open_file(
            repo_root,
            candidate,
            before,
            after,
            parent_descriptor,
        )
    finally:
        os.close(descriptor)
        os.close(parent_descriptor)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError("cache manifest exceeds safety limit")
    try:
        return json.loads(payload, object_pairs_hook=_unique_json_object)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateJsonKey,
        RecursionError,
    ) as error:
        raise ValueError("cache manifest is malformed") from error


def _write_manifest(
    repo_root: Path,
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path, _ = _repo_path(repo_root, path, allow_missing=True)
    parent_descriptor = _open_repo_directory(repo_root, path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(
            path.name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
    except BaseException:
        os.close(parent_descriptor)
        raise
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=False) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _require_directory_binding(repo_root, path.parent, parent_descriptor)
    finally:
        os.close(descriptor)
        os.close(parent_descriptor)


def _entry_fingerprint(
    key: str,
    spec: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> str:
    return hashlib.sha256(
        canonical_json_bytes(
            {
                "key": key,
                "spec": spec,
                "artifacts": list(artifacts),
            }
        )
    ).hexdigest()


def _ensure_safe_directory(repo_root: Path, path: Path) -> None:
    descriptor = _open_repo_directory(repo_root, path, create=True)
    os.close(descriptor)


def _remove_cache_entry(repo_root: Path, entry: Path) -> None:
    candidate, _ = _repo_path(repo_root, entry)
    parent_descriptor = _open_repo_directory(repo_root, candidate.parent)
    try:
        info = os.stat(
            candidate.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if stat.S_ISLNK(info.st_mode):
            os.unlink(candidate.name, dir_fd=parent_descriptor)
            return
        if not stat.S_ISDIR(info.st_mode):
            raise CacheSafetyError(f"cache entry is not a directory: {candidate}")
        if not shutil.rmtree.avoids_symlink_attacks:
            raise CacheSafetyError("platform lacks symlink-safe tree removal")
        shutil.rmtree(candidate.name, dir_fd=parent_descriptor)
    finally:
        os.close(parent_descriptor)


def _fsync_directory(repo_root: Path, path: Path) -> None:
    descriptor = _open_repo_directory(repo_root, path)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _open_lock(repo_root: Path, path: Path) -> int:
    path, _ = _repo_path(repo_root, path, allow_missing=True)
    parent_descriptor = _open_repo_directory(repo_root, path.parent)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(
            path.name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
    except OSError as error:
        os.close(parent_descriptor)
        raise CacheSafetyError(f"cannot safely open cache lock: {path}") from error
    info = os.fstat(descriptor)
    try:
        path_info = os.stat(
            path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as error:
        os.close(descriptor)
        os.close(parent_descriptor)
        raise CacheSafetyError(f"cache lock changed while opening: {path}") from error
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(path_info.st_mode)
        or info.st_dev != path_info.st_dev
        or info.st_ino != path_info.st_ino
    ):
        os.close(descriptor)
        os.close(parent_descriptor)
        raise CacheSafetyError(f"cache lock is unsafe: {path}")
    try:
        _require_directory_binding(repo_root, path.parent, parent_descriptor)
    except BaseException:
        os.close(descriptor)
        os.close(parent_descriptor)
        raise
    os.close(parent_descriptor)
    return descriptor


def _reason_for_error(error: BaseException) -> str:
    message = str(error).lower()
    if "manifest" in message and "missing" in message:
        return "manifest_missing"
    if "manifest" in message and "malformed" in message:
        return "manifest_malformed"
    if "manifest" in message and "schema" in message:
        return "manifest_schema_mismatch"
    if "manifest" in message:
        return "manifest_invalid"
    if "size drift" in message:
        return "artifact_size_drift"
    if "hash drift" in message:
        return "artifact_hash_drift"
    if (
        "symlink" in message
        or "outside the repository" in message
        or "unsafe" in message
        or "directory changed" in message
        or "path race" in message
        or "traversal" in message
    ):
        return "unsafe_path"
    if isinstance(error, FileNotFoundError):
        return "artifact_missing"
    return "entry_invalid"
