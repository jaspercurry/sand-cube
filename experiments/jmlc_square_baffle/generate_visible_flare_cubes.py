"""Generate visible-flare JMLC square-cropped cube variants.

This is the corrected experiment direction: choose a parent horn mouth that is
small enough for the cube face to include the flared mouth region, then truncate
the rear where the profile reaches a 5.5 in driver hole.
"""

from __future__ import annotations


# This guard must remain before all native CAD/threaded-library imports.
from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys

_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
    and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Location,
    Mode,
    Part,
    Unit,
    export_step,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from explore_variants import (  # noqa: E402
    STEP_MM,
    _intersections_at_radius,
    _jmlc_points_for_cutoff,
    _solve_cutoff_hz,
)
from generate_rolled_cube import _revolved_air_tool  # noqa: E402
from params import p  # noqa: E402


OUT = ROOT / "build" / "jmlc_square_baffle" / "visible_flare_140"

EXIT_ANGLE_DEG = 140.0
DRIVER_HOLE_D = 5.5 * 25.4
MOUTH_INNER_DIAMETERS = (
    math.sqrt(2) * p.cube_outer,
    300.0,
    320.0,
    350.0,
)


@dataclass(frozen=True)
class VisibleFlareVariant:
    name: str
    mouth_inner_d: float


def _profile_for_mouth(mouth_inner_d: float) -> dict[str, object]:
    cutoff = _solve_cutoff_hz(
        mouth_inner_r=mouth_inner_d / 2,
        exit_angle_deg=EXIT_ANGLE_DEG,
    )
    points, terminal_angle = _jmlc_points_for_cutoff(
        throat_d=p.horn_throat_d,
        mouth_inner_r=mouth_inner_d / 2,
        cutoff_hz=cutoff,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=STEP_MM,
    )
    z_values = [z for _r, z in points]
    frontmost_z = max(z_values)
    mouth_z = points[-1][1]

    seat_intersections = _intersections_at_radius(points, DRIVER_HOLE_D / 2)
    if not seat_intersections:
        raise ValueError("Parent horn never reaches driver hole diameter")
    seat_z = seat_intersections[0]

    clipped_points = [
        (DRIVER_HOLE_D / 2, seat_z),
        *[(r, z) for r, z in points if DRIVER_HOLE_D / 2 < r < mouth_inner_d / 2],
        (mouth_inner_d / 2, mouth_z),
    ]
    normalized_points = [
        (r, z - frontmost_z)
        for r, z in clipped_points
    ]

    return {
        "mouth_inner_d_mm": mouth_inner_d,
        "mouth_outer_d_with_wall_mm": mouth_inner_d + 2 * p.horn_wall_t,
        "exit_angle_deg": EXIT_ANGLE_DEG,
        "seat_d_mm": DRIVER_HOLE_D,
        "seat_depth_from_frontmost_mm": frontmost_z - seat_z,
        "seat_depth_from_terminal_mouth_mm": mouth_z - seat_z,
        "terminal_mouth_z_from_frontmost_mm": mouth_z - frontmost_z,
        "rollback_mm": frontmost_z - mouth_z,
        "cutoff_hz": cutoff,
        "terminal_angle_deg": terminal_angle,
        "points": normalized_points,
    }


def build_variant(variant: VisibleFlareVariant) -> tuple[Part, dict[str, object]]:
    solved = _profile_for_mouth(variant.mouth_inner_d)
    profile = solved["points"]
    assert isinstance(profile, list)

    cube = Box(
        p.cube_outer,
        p.cube_outer,
        p.cube_outer,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
        mode=Mode.PRIVATE,
    )
    air_tool = _revolved_air_tool(
        profile,
        front_extension=12.0,
        rear_extension=p.cube_outer,
    )
    cut = cube - air_tool
    cut = max(cut.solids(), key=lambda solid: solid.volume)

    driver_hole = Cylinder(
        radius=DRIVER_HOLE_D / 2,
        height=p.cube_outer * 2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    cut -= driver_hole
    cut = max(cut.solids(), key=lambda solid: solid.volume).clean().fix()

    bb = cut.bounding_box()
    diagnostics = {
        "name": variant.name,
        **{k: v for k, v in solved.items() if k != "points"},
        "cube_outer_mm": p.cube_outer,
        "bounding_box_mm": [
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ],
        "volume_cm3": round(cut.volume / 1000, 3),
        "is_valid": cut.is_valid,
        "n_solids": len(cut.solids()),
        "n_faces": len(cut.faces()),
        "n_edges": len(cut.edges()),
    }
    return cut, diagnostics


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    variants = [
        VisibleFlareVariant(
            name=(
                "min_square"
                if math.isclose(mouth_d, math.sqrt(2) * p.cube_outer)
                else f"mouth_{mouth_d:.0f}"
            ),
            mouth_inner_d=mouth_d,
        )
        for mouth_d in MOUTH_INNER_DIAMETERS
    ]

    diagnostics: list[dict[str, object]] = []
    combined_parts: list[Part] = []
    spacing = p.cube_outer + 60.0
    offset0 = -spacing * (len(variants) - 1) / 2

    for index, variant in enumerate(variants):
        cube, data = build_variant(variant)
        if not data["is_valid"]:
            raise ValueError(f"Generated {variant.name} is not valid")
        export_step(
            cube,
            OUT / f"{variant.name}_visible_flare_cube.step",
            unit=Unit.MM,
        )
        diagnostics.append(data)

        placed = Location((offset0 + index * spacing, 0, 0)) * cube
        combined_parts.append(placed)

    export_step(
        Compound(combined_parts),
        OUT / "visible_flare_140_comparison.step",
        unit=Unit.MM,
    )
    (OUT / "visible_flare_140_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2)
    )
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
