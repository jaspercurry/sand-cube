"""Generate a square-cropped JMLC front-face cube concept.

This is intentionally isolated from the production enclosure. It creates a
simple 203 mm cube with a front face cut from a much larger 140 degree JMLC
parent horn. The parent horn is sized so its rollback is 0.75 in, then the
deep end is cut where the profile diameter is 5.5 in.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from build123d import Align, Box, Cylinder, Mode, Part, Solid, Unit, export_step
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
)
from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt
from OCP.TColgp import TColgp_Array1OfPnt

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
from params import p  # noqa: E402


OUT = ROOT / "build" / "jmlc_square_baffle" / "rolled_cube_140"

EXIT_ANGLE_DEG = 140.0
ROLLBACK_MM = 0.75 * 25.4
DRIVER_HOLE_D = 5.5 * 25.4


def _line_edge(start: tuple[float, float], end: tuple[float, float]):
    return BRepBuilderAPI_MakeEdge(
        gp_Pnt(start[0], 0, start[1]),
        gp_Pnt(end[0], 0, end[1]),
    ).Edge()


def _spline_edge(points: list[tuple[float, float]]):
    point_array = TColgp_Array1OfPnt(1, len(points))
    for index, (radius, z) in enumerate(points, 1):
        point_array.SetValue(index, gp_Pnt(radius, 0, z))
    curve = GeomAPI_PointsToBSpline(point_array).Curve()
    return BRepBuilderAPI_MakeEdge(curve).Edge()


def _solve_parent_profile() -> dict[str, object]:
    def profile_for_mouth(mouth_inner_d: float):
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
        return {
            "cutoff_hz": cutoff,
            "terminal_angle_deg": terminal_angle,
            "points": points,
            "rollback_mm": max(z_values) - points[-1][1],
            "frontmost_z_mm": max(z_values),
            "mouth_z_mm": points[-1][1],
        }

    low = math.sqrt(2) * p.cube_outer
    high = 800.0
    for _ in range(52):
        mid = (low + high) / 2
        if profile_for_mouth(mid)["rollback_mm"] < ROLLBACK_MM:
            low = mid
        else:
            high = mid

    mouth_inner_d = (low + high) / 2
    solved = profile_for_mouth(mouth_inner_d)
    points = solved["points"]
    assert isinstance(points, list)

    seat_intersections = _intersections_at_radius(points, DRIVER_HOLE_D / 2)
    if not seat_intersections:
        raise ValueError("Solved parent horn never reaches driver hole diameter")
    seat_z = seat_intersections[0]
    frontmost_z = float(solved["frontmost_z_mm"])

    clipped_points = [
        (DRIVER_HOLE_D / 2, seat_z),
        *[(r, z) for r, z in points if DRIVER_HOLE_D / 2 < r < mouth_inner_d / 2],
        (mouth_inner_d / 2, float(solved["mouth_z_mm"])),
    ]
    normalized_points = [
        (r, z - frontmost_z)
        for r, z in clipped_points
    ]

    return {
        "mouth_inner_d_mm": mouth_inner_d,
        "mouth_outer_d_with_wall_mm": mouth_inner_d + 2 * p.horn_wall_t,
        "seat_d_mm": DRIVER_HOLE_D,
        "seat_depth_from_frontmost_mm": frontmost_z - seat_z,
        "seat_depth_from_terminal_mouth_mm": float(solved["mouth_z_mm"]) - seat_z,
        "frontmost_z_mm": frontmost_z,
        "terminal_mouth_z_from_frontmost_mm": float(solved["mouth_z_mm"])
        - frontmost_z,
        "rollback_mm": float(solved["rollback_mm"]),
        "cutoff_hz": float(solved["cutoff_hz"]),
        "terminal_angle_deg": float(solved["terminal_angle_deg"]),
        "points": normalized_points,
    }


def _revolved_air_tool(
    profile: list[tuple[float, float]],
    *,
    front_extension: float,
    rear_extension: float,
) -> Solid:
    """Build a revolved air volume around Z from outside front to rear seat."""
    cube_corner_r = math.sqrt(2) * p.cube_outer / 2
    outside_r = max(profile[-1][0] + 20.0, cube_corner_r + 30.0)
    front_z = front_extension
    seat_z = profile[0][1]
    rear_z = seat_z - rear_extension

    wire_maker = BRepBuilderAPI_MakeWire()
    wire_maker.Add(_line_edge((0, front_z), (outside_r, front_z)))
    wire_maker.Add(_line_edge((outside_r, front_z), profile[-1]))
    wire_maker.Add(_spline_edge(list(reversed(profile))))
    wire_maker.Add(_line_edge(profile[0], (profile[0][0], rear_z)))
    wire_maker.Add(_line_edge((profile[0][0], rear_z), (0, rear_z)))
    wire_maker.Add(_line_edge((0, rear_z), (0, front_z)))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make rolled cube air-tool wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make rolled cube air-tool face")

    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve rolled cube air tool")

    solid = Solid.cast(revolved.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Rolled cube air tool is not a valid solid")
    return solid


def build_cube() -> tuple[Part, dict[str, object]]:
    solved = _solve_parent_profile()
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

    # Continue the 5.5 in driver opening through the back of this visual block.
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
    cube, diagnostics = build_cube()
    if not diagnostics["is_valid"]:
        raise ValueError("Generated rolled cube is not valid")
    export_step(cube, OUT / "rolled_jmlc_front_cube.step", unit=Unit.MM)
    (OUT / "rolled_jmlc_front_cube_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2)
    )
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
