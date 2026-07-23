"""Job-owned output staging helpers with no CAD imports."""

from __future__ import annotations

import os
from pathlib import Path


STAGE_ROOT_ENV = "CAD_JOB_STAGE_ROOT"
REPO_ROOT_ENV = "CAD_JOB_REPO_ROOT"


def job_output_path(path: str | Path) -> Path:
    """Map a repository output into the current job's staging tree.

    Outside a supervised worker this returns the original path, which keeps
    library imports and read-only use unsurprising. A supervised worker may
    only publish repository-owned paths.
    """
    candidate = Path(path)
    stage_value = os.environ.get(STAGE_ROOT_ENV)
    repo_value = os.environ.get(REPO_ROOT_ENV)
    if not stage_value or not repo_value:
        return candidate

    repo = Path(repo_value).resolve()
    stage = Path(stage_value).resolve()
    absolute = candidate if candidate.is_absolute() else repo / candidate
    absolute = absolute.resolve(strict=False)
    try:
        absolute.relative_to(stage)
        return absolute
    except ValueError:
        pass
    try:
        relative = absolute.relative_to(repo)
    except ValueError as exc:
        raise RuntimeError(
            f"CAD jobs may only stage repository-owned outputs: {absolute}"
        ) from exc
    return stage / relative
