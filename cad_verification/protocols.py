"""Narrow integration boundaries for CAD kernels and artifact storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .model import ActualValue, ArtifactObservation, Requirement, Scalar


@dataclass(frozen=True)
class Measurement:
    """A kernel-independent measurement returned by an adapter."""

    actual: ActualValue
    diagnostic: str
    evidence_refs: tuple[str, ...] = ()


class MeasurementAdapter(Protocol):
    """Later integrations implement this without entering the core model."""

    def measure(
        self,
        requirement: Requirement,
        *,
        context: Mapping[str, Scalar],
    ) -> Measurement:
        """Return an actual value; orchestration remains outside the core."""


class ArtifactProbe(Protocol):
    """Observe an artifact without coupling validation to a filesystem."""

    def inspect(self, path: str) -> ArtifactObservation:
        """Return existence and current hash/size metadata for ``path``."""
