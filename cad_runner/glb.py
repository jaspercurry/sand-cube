"""Bounded, native-free readers for Text-to-CAD GLB provenance."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import struct
from typing import Any


MAX_GLB_BYTES = 64 * 1024 * 1024
GLB_JSON_CHUNK = 0x4E4F534A
GLB_BIN_CHUNK = 0x004E4942
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GlbStepIdentity:
    step_hash: str
    entry_kind: str


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _contains_step_hash(value: Any) -> bool:
    if isinstance(value, dict):
        return "stepHash" in value or any(
            _contains_step_hash(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_step_hash(item) for item in value)
    return False


def _bounded_regular_file(path: Path, maximum_bytes: int) -> bytes:
    """Read one stable regular file without following a final symlink."""

    candidate = path.expanduser()
    try:
        before_path = candidate.lstat()
    except FileNotFoundError:
        raise ValueError(f"sidecar does not exist: {candidate}") from None
    if stat.S_ISLNK(before_path.st_mode):
        raise ValueError(f"sidecar must not be a symlink: {candidate}")
    if not stat.S_ISREG(before_path.st_mode):
        raise ValueError(f"sidecar is not a regular file: {candidate}")
    if before_path.st_size > maximum_bytes:
        raise ValueError(
            f"sidecar exceeds the {maximum_bytes}-byte safety cap: {candidate}"
        )

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(candidate, flags)
    except OSError as error:
        raise ValueError(f"cannot safely open sidecar: {candidate}") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"sidecar is not a regular file: {candidate}")
        if before.st_size > maximum_bytes:
            raise ValueError(
                f"sidecar exceeds the {maximum_bytes}-byte safety cap: {candidate}"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read(maximum_bytes + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    if len(payload) > maximum_bytes:
        raise ValueError(
            f"sidecar exceeds the {maximum_bytes}-byte safety cap: {candidate}"
        )
    stable_fields = (
        "st_dev",
        "st_ino",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
        raise ValueError(f"sidecar changed while it was being read: {candidate}")
    try:
        after_path = candidate.lstat()
    except FileNotFoundError:
        raise ValueError(
            f"sidecar changed while it was being read: {candidate}"
        ) from None
    if (
        stat.S_ISLNK(after_path.st_mode)
        or after_path.st_dev != after.st_dev
        or after_path.st_ino != after.st_ino
    ):
        raise ValueError(f"sidecar changed while it was being read: {candidate}")
    return payload


def glb_step_identity(
    path: str | Path,
    *,
    maximum_bytes: int | None = None,
) -> GlbStepIdentity:
    """Read canonical STEP provenance from a bounded Text-to-CAD GLB."""

    candidate = Path(path)
    maximum_bytes = MAX_GLB_BYTES if maximum_bytes is None else maximum_bytes
    if maximum_bytes < 1:
        raise ValueError("maximum GLB size must be positive")
    payload = _bounded_regular_file(candidate, maximum_bytes)
    if len(payload) < 12 or payload[:4] != b"glTF":
        raise ValueError(f"sidecar is not a GLB file: {candidate}")
    version, declared_size = struct.unpack_from("<II", payload, 4)
    if version != 2 or declared_size != len(payload) or declared_size % 4:
        raise ValueError(f"sidecar has an invalid GLB header: {candidate}")

    offset = 12

    def read_chunk(expected_type: int, label: str) -> bytes:
        nonlocal offset
        if offset + 8 > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk header: {candidate}")
        chunk_size, chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        if chunk_type != expected_type:
            raise ValueError(f"sidecar {label} chunk has the wrong type: {candidate}")
        if chunk_size % 4:
            raise ValueError(f"sidecar has an unaligned GLB chunk: {candidate}")
        end = offset + chunk_size
        if end > len(payload):
            raise ValueError(f"sidecar has a truncated GLB chunk: {candidate}")
        chunk = payload[offset:end]
        offset = end
        return chunk

    json_chunk = read_chunk(GLB_JSON_CHUNK, "JSON")
    binary = read_chunk(GLB_BIN_CHUNK, "BIN")
    if offset != len(payload):
        raise ValueError(
            "sidecar must contain one JSON chunk followed by one BIN chunk: "
            f"{candidate}"
        )

    try:
        document = json.loads(
            json_chunk.rstrip(b" \t\r\n\0").decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"sidecar JSON chunk is malformed: {candidate}") from error
    if not isinstance(document, dict):
        raise ValueError(f"sidecar JSON chunk must be an object: {candidate}")
    try:
        contains_noncanonical_hash = _contains_step_hash(document)
    except RecursionError as error:
        raise ValueError(
            f"sidecar JSON structure is too deeply nested: {candidate}"
        ) from error
    if contains_noncanonical_hash:
        raise ValueError(
            "sidecar contains stepHash outside the canonical index metadata: "
            f"{candidate}"
        )
    extensions = document.get("extensions")
    extension = (
        extensions.get("STEP_topology") if isinstance(extensions, dict) else None
    )
    if not isinstance(extension, dict):
        raise ValueError(f"sidecar lacks the STEP_topology extension: {candidate}")
    index_view = extension.get("indexView")
    extension_kind = extension.get("entryKind")
    if (
        extension.get("schemaVersion") != 2
        or extension.get("encoding") != "utf-8"
        or not isinstance(index_view, int)
        or isinstance(index_view, bool)
        or extension_kind not in {"part", "assembly"}
    ):
        raise ValueError(
            f"sidecar STEP_topology extension is not canonical: {candidate}"
        )
    views = document.get("bufferViews")
    buffers = document.get("buffers")
    if (
        not isinstance(views, list)
        or not 0 <= index_view < len(views)
        or not isinstance(buffers, list)
        or len(buffers) != 1
        or not isinstance(buffers[0], dict)
    ):
        raise ValueError(f"sidecar index buffer metadata is malformed: {candidate}")
    view = views[index_view]
    if (
        not isinstance(view, dict)
        or not isinstance(view.get("buffer"), int)
        or isinstance(view.get("buffer"), bool)
        or view.get("buffer") != 0
    ):
        raise ValueError(f"sidecar indexView does not reference buffer 0: {candidate}")
    byte_offset = view.get("byteOffset", 0)
    byte_length = view.get("byteLength")
    declared_buffer_length = buffers[0].get("byteLength")
    if (
        not isinstance(byte_offset, int)
        or isinstance(byte_offset, bool)
        or not isinstance(byte_length, int)
        or isinstance(byte_length, bool)
        or not isinstance(declared_buffer_length, int)
        or isinstance(declared_buffer_length, bool)
        or byte_offset < 0
        or byte_length <= 0
        or declared_buffer_length < 0
        or declared_buffer_length > len(binary)
        or len(binary) - declared_buffer_length > 3
        or byte_offset + byte_length > declared_buffer_length
    ):
        raise ValueError(f"sidecar indexView bounds are invalid: {candidate}")
    try:
        metadata = json.loads(
            binary[byte_offset : byte_offset + byte_length].decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"sidecar index metadata is malformed: {candidate}") from error
    if (
        not isinstance(metadata, dict)
        or metadata.get("schemaVersion") != 2
        or metadata.get("profile") != "index"
        or metadata.get("sourceKind") != "step"
        or metadata.get("entryKind") not in {"part", "assembly"}
    ):
        raise ValueError(f"sidecar index metadata schema is not canonical: {candidate}")
    metadata_kind = metadata["entryKind"]
    if metadata_kind != extension_kind:
        raise ValueError(f"sidecar entryKind values do not agree: {candidate}")
    step_hash = metadata.get("stepHash")
    nested_values = (item for key, item in metadata.items() if key != "stepHash")
    try:
        contains_nested_hash = any(_contains_step_hash(item) for item in nested_values)
    except RecursionError as error:
        raise ValueError(
            f"sidecar index metadata is too deeply nested: {candidate}"
        ) from error
    if (
        not isinstance(step_hash, str)
        or not SHA256_PATTERN.fullmatch(step_hash)
        or contains_nested_hash
    ):
        raise ValueError(
            "sidecar must contain exactly one lowercase stepHash at the canonical "
            f"index metadata location: {candidate}"
        )
    return GlbStepIdentity(step_hash, metadata_kind)


def glb_step_hash(path: str | Path, *, maximum_bytes: int | None = None) -> str:
    """Read the one canonical STEP hash from a bounded Text-to-CAD GLB."""

    return glb_step_identity(path, maximum_bytes=maximum_bytes).step_hash
