"""Public API for the current Sand Cube enclosure.

The black-hole enclosure was developed in ``experiments/`` because the baffle
profile went through several visual and manufacturing iterations. The functions
here are the stable import surface for scripts and assemblies that need the
validated final candidate. The final API now points at the 200 mm / 7 mm wall
variant; the legacy 8.5 in variant remains buildable from the experiment module.
"""

from __future__ import annotations

from pathlib import Path

from build123d import Compound, Part

from experiments.sand_cube_8_5_black_hole.generate_contoured_inner_variants import (
    OUT,
    build_final_enclosure,
    build_final_export_shapes,
    export_final_enclosure_set,
)


def build() -> tuple[Part, object, dict[str, object]]:
    """Build the final enclosure and return ``(part, params, data)``."""
    return build_final_enclosure()


def build_export_shapes() -> tuple[dict[str, Compound | Part], dict[str, object]]:
    """Build the four standard final enclosure/hardware export shapes."""
    return build_final_export_shapes()


def export(out: Path = OUT) -> dict[str, object]:
    """Export the final enclosure STEP set."""
    return export_final_enclosure_set(out)
