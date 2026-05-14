"""Front baffle geometry."""

from __future__ import annotations

from build123d import (
    Axis,
    Bezier,
    BuildLine,
    BuildPart,
    BuildSketch,
    Part,
    Plane,
    Polyline,
    make_face,
    revolve,
)


def black_hole_baffle(
    *,
    face_thickness: float,
    driver_cutout_dia: float,
    blend_radius: float,
    blend_depth: float,
    tangent_in: float = 1.6,
    tangent_out: float = 1.0,
) -> Part:
    """Return a revolved subtraction tool for the recessed driver baffle."""
    r_outer = driver_cutout_dia / 2 + blend_radius
    r_inner = driver_cutout_dia / 2
    z_top = 0.0
    z_blend = blend_depth
    z_floor = max(face_thickness, blend_depth) + 0.5

    with BuildPart() as recess:
        with BuildSketch(Plane.XZ) as sketch:
            with BuildLine():
                Bezier(
                    (r_outer, z_top),
                    (r_outer - blend_radius * tangent_in, z_top),
                    (r_inner, z_blend * (1 - tangent_out)),
                    (r_inner, z_blend),
                )
                Polyline(
                    (r_inner, z_blend),
                    (r_inner, z_floor),
                    (0, z_floor),
                    (0, z_top),
                    (r_outer, z_top),
                )
            make_face()
        assert sketch.sketch.area > 0, "Recess sketch must have positive area"
        revolve(axis=Axis.Z)

    return recess.part
