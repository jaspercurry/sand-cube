"""Generate maximum black-hole baffle depth variants.

These are visual experiment blocks, not production enclosure geometry. Each is
a sharp-corner 8 in cube with the largest inscribed circular front depression
blending down to a 5.5 in driver hole.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Bezier,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Location,
    Mode,
    Part,
    Plane,
    Polyline,
    Unit,
    export_step,
    make_face,
    revolve,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


OUT = ROOT / "build" / "max_black_hole_baffle"

CUBE_SIDE = 8.0 * 25.4
DRIVER_HOLE_D = 5.5 * 25.4
DEPTHS_IN = (0.5, 1.0, 1.5, 2.0)


@dataclass(frozen=True)
class Variant:
    name: str
    depth_mm: float


def _black_hole_air_tool(
    *,
    outer_d: float,
    driver_hole_d: float,
    depth: float,
    block_depth: float,
) -> Part:
    """Return a revolved subtraction tool in +Z/-Z coordinates.

    The front face of the block is at z=0 and the driver seat is at z=-depth.
    """
    r_outer = outer_d / 2
    r_inner = driver_hole_d / 2
    rear_z = -block_depth - 2.0
    front_z = 4.0
    seat_z = -depth
    radial_span = r_outer - r_inner

    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                # Long first tangent keeps the outer face broad and smooth;
                # short final tangent dives into the driver-hole wall.
                Bezier(
                    (r_outer, 0.0),
                    (r_outer - radial_span * 0.65, 0.0),
                    (r_inner, seat_z + depth * 0.22),
                    (r_inner, seat_z),
                )
                Polyline(
                    (r_inner, seat_z),
                    (r_inner, rear_z),
                    (0.0, rear_z),
                    (0.0, front_z),
                    (r_outer, front_z),
                    (r_outer, 0.0),
                )
            make_face()
        assert sketch.sketch.area > 0, "Air-tool sketch must have positive area"
        revolve(axis=Axis.Z)

    return tool.part


def build_variant(variant: Variant) -> tuple[Part, dict[str, object]]:
    cube = Box(
        CUBE_SIDE,
        CUBE_SIDE,
        CUBE_SIDE,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
        mode=Mode.PRIVATE,
    )
    air_tool = _black_hole_air_tool(
        outer_d=CUBE_SIDE,
        driver_hole_d=DRIVER_HOLE_D,
        depth=variant.depth_mm,
        block_depth=CUBE_SIDE,
    )
    part = cube - air_tool
    part = max(part.solids(), key=lambda solid: solid.volume)

    driver_hole = Cylinder(
        radius=DRIVER_HOLE_D / 2,
        height=CUBE_SIDE * 2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    part -= driver_hole
    part = max(part.solids(), key=lambda solid: solid.volume).clean().fix()

    bb = part.bounding_box()
    diagnostics = {
        "name": variant.name,
        "cube_side_mm": CUBE_SIDE,
        "cube_side_in": CUBE_SIDE / 25.4,
        "front_circle_d_mm": CUBE_SIDE,
        "front_circle_d_in": CUBE_SIDE / 25.4,
        "driver_hole_d_mm": DRIVER_HOLE_D,
        "driver_hole_d_in": DRIVER_HOLE_D / 25.4,
        "recess_depth_mm": variant.depth_mm,
        "recess_depth_in": variant.depth_mm / 25.4,
        "radial_blend_span_mm": (CUBE_SIDE - DRIVER_HOLE_D) / 2,
        "bounding_box_mm": [
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ],
        "volume_cm3": round(part.volume / 1000, 3),
        "is_valid": part.is_valid,
        "n_solids": len(part.solids()),
        "n_faces": len(part.faces()),
        "n_edges": len(part.edges()),
    }
    return part, diagnostics


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    variants = [
        Variant(
            name=f"depth_{depth_in:.2f}in".replace(".", "_"),
            depth_mm=depth_in * 25.4,
        )
        for depth_in in DEPTHS_IN
    ]

    diagnostics: list[dict[str, object]] = []
    combined_parts: list[Part] = []
    spacing = CUBE_SIDE + 60.0
    offset0 = -spacing * (len(variants) - 1) / 2

    for index, variant in enumerate(variants):
        part, data = build_variant(variant)
        if not data["is_valid"]:
            raise ValueError(f"Generated {variant.name} is not valid")

        export_step(part, OUT / f"{variant.name}.step", unit=Unit.MM)
        diagnostics.append(data)
        combined_parts.append(Location((offset0 + index * spacing, 0, 0)) * part)

    export_step(
        Compound(combined_parts),
        OUT / "max_black_hole_comparison.step",
        unit=Unit.MM,
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
