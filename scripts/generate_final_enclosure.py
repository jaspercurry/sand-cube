"""Export the current Sand Cube enclosure STEP set."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.final_enclosure import OUT, export


def main() -> None:
    """Write enclosure-only, insert, rear-hardware, and full woofer assemblies."""
    data = export(OUT)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
