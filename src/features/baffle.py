"""Front baffle geometry."""

from __future__ import annotations

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Part,
    Plane,
    Polyline,
    Spline,
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
                Spline(
                    (r_outer, z_top),
                    (r_inner, z_blend),
                    tangents=((-1, 0), (0, 1)),
                    tangent_scalars=(tangent_in, tangent_out),
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
