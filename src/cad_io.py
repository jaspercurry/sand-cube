"""Repository-safe CAD interchange helpers.

Build123d 0.11 moved to OCCT 7.9 and its XDE STEP writer fails when asked to
write some macOS paths containing spaces. Exporting the same document to a
binary stream succeeds, so 0.11+ uses that route and Python writes the bytes.
"""

from __future__ import annotations

from io import BytesIO
import importlib.metadata
from os import PathLike
from pathlib import Path
from typing import Any, BinaryIO

from build123d import Compound, export_step as _build123d_export_step


def _build123d_minor() -> tuple[int, int]:
    release = importlib.metadata.version("build123d").split("+", 1)[0]
    numbers = release.split(".")
    return int(numbers[0]), int(numbers[1])


def export_step(
    shape: Any,
    file_path: PathLike[str] | str | bytes | BinaryIO,
    *args: Any,
    **kwargs: Any,
) -> bool:
    """Export STEP reliably across the repository's Build123d versions."""
    if _build123d_minor() < (0, 11) or hasattr(file_path, "write"):
        return _build123d_export_step(shape, file_path, *args, **kwargs)

    # Algebra operations can retain construction trees under Parts and
    # Compounds. OCCT 7.9's XDE writer may serialize only those trees and omit
    # the final solids. Rebuild a shallow export object from the actual solids.
    solids = list(shape.solids())
    if len(solids) == 1:
        export_shape = solids[0]
    elif solids:
        export_shape = Compound(children=solids)
    else:
        export_shape = shape

    stream = BytesIO()
    success = _build123d_export_step(export_shape, stream, *args, **kwargs)
    if success:
        data = stream.getvalue()
        if solids and len(data) < 1024:
            raise RuntimeError(
                "Build123d reported STEP export success but produced an empty "
                f"or truncated {len(data)}-byte stream"
            )
        Path(file_path).write_bytes(data)
    return success
