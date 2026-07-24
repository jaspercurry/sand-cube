"""Explicit, serialized compatibility binding for the inherited CAD cascade."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class LegacyAttributeBinding:
    """One intentionally temporary attribute replacement."""

    owner: Any
    name: str
    value: Any


_LEGACY_BINDING_LOCK = RLock()


@contextmanager
def bind_legacy_attributes(
    bindings: Sequence[LegacyAttributeBinding],
) -> Iterator[None]:
    """Apply visible legacy bindings for one call and restore them exactly."""

    with _LEGACY_BINDING_LOCK:
        originals = tuple(
            (binding.owner, binding.name, getattr(binding.owner, binding.name))
            for binding in bindings
        )
        try:
            for binding in bindings:
                setattr(binding.owner, binding.name, binding.value)
            yield
        finally:
            for owner, name, original in reversed(originals):
                setattr(owner, name, original)
            unrestored = [
                f"{type(owner).__name__}.{name}"
                for owner, name, original in originals
                if getattr(owner, name) is not original
            ]
            if unrestored:
                raise RuntimeError(
                    "Legacy runtime attributes were not restored: "
                    + ", ".join(unrestored)
                )
