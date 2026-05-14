"""Build the Sand Cube enclosure."""

from __future__ import annotations

from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Cylinder,
    GridLocations,
    Location,
    Mesher,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Pos,
    Rot,
    Unit,
    add,
    export_step,
)

from params import p
from src.features.baffle import black_hole_baffle
from src.features.bracing import bonded_collar, reinforcement_ring


def _oriented_cylinder(
    *,
    diameter: float,
    depth: float,
    axis: str,
    center: tuple[float, float, float],
) -> Part:
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    if axis == "x":
        cyl = Rot(0, 90, 0) * cyl
    elif axis == "y":
        cyl = Rot(90, 0, 0) * cyl
    elif axis != "z":
        raise ValueError(f"Unsupported axis: {axis}")
    return Location(center) * cyl


def _face_posts(*, z_rotation: float, center: tuple[float, float, float]) -> Part:
    full_h = p.outer_skin_t + p.void_t + p.inner_skin_t
    with BuildPart() as posts:
        with GridLocations(p.bracing_grid_pitch, p.bracing_grid_pitch, 3, 3):
            Cylinder(
                radius=p.bracing_post_d / 2,
                height=full_h,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
    return Location(center) * Rot(0, 0, z_rotation) * posts.part


def _bolt_circle_collars(
    *,
    radius: float,
    count: int,
    center_y: float,
    face_sign: int,
) -> Part:
    full_h = p.outer_skin_t + p.void_t + p.inner_skin_t
    with BuildPart() as collars:
        for index in range(count):
            angle = math.tau * index / count + (math.tau / 8 if count == 4 else 0)
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            add(
                Pos(x, center_y, z)
                * Rot(90, 0, 0)
                * bonded_collar(
                    full_h=full_h,
                    collar_od=p.boss_od,
                    insert_bore_d=p.insert_bore_d,
                    insert_bore_depth=p.insert_bore_depth,
                )
            )
    return collars.part


def build() -> Part:
    """Create the first complete CAD pass for the enclosure."""
    shell_span = p.cube_outer - 2 * p.outer_skin_t
    inner_outer = p.cube_outer - 2 * (p.outer_skin_t + p.void_t)
    cavity = inner_outer - 2 * p.inner_skin_t
    half = p.cube_outer / 2
    inner_face_y = inner_outer / 2
    through = p.cube_outer + 10

    outer_solid = Box(p.cube_outer, p.cube_outer, p.cube_outer)
    sand_void = Box(shell_span, shell_span, shell_span)
    inner_solid = Box(inner_outer, inner_outer, inner_outer)
    acoustic_cavity = Box(cavity, cavity, cavity)

    enclosure = (outer_solid - sand_void) + (inner_solid - acoustic_cavity)

    # Driver front face is -Y; PR rear face is +Y.
    enclosure -= Pos(0, -half - 0.2, 0) * Rot(90, 0, 0) * black_hole_baffle(
        face_thickness=p.outer_skin_t,
        driver_cutout_dia=p.driver_cutout_dia,
        blend_radius=p.baffle_blend_r,
        blend_depth=p.baffle_blend_depth,
        tangent_in=p.baffle_tangent_in,
        tangent_out=p.baffle_tangent_out,
    )
    enclosure -= _oriented_cylinder(
        diameter=p.driver_cutout_dia,
        depth=through,
        axis="y",
        center=(0, -half, 0),
    )
    enclosure -= _oriented_cylinder(
        diameter=p.pr_cutout_dia,
        depth=through,
        axis="y",
        center=(0, half, 0),
    )

    enclosure += Pos(0, -inner_face_y - p.ring_t, 0) * Rot(90, 0, 0) * reinforcement_ring(
        cutout_dia=p.driver_cutout_dia,
        ring_width=p.ring_width,
        ring_t=p.ring_t,
    )
    enclosure += Pos(0, inner_face_y, 0) * Rot(90, 0, 0) * reinforcement_ring(
        cutout_dia=p.pr_cutout_dia,
        ring_width=p.ring_width,
        ring_t=p.ring_t,
    )

    enclosure += _bolt_circle_collars(
        radius=p.driver_bolt_circle_r,
        count=p.driver_screw_count,
        center_y=-half + (p.outer_skin_t + p.void_t + p.inner_skin_t),
        face_sign=-1,
    )
    enclosure += _bolt_circle_collars(
        radius=p.pr_bolt_circle_r,
        count=p.pr_screw_count,
        center_y=half,
        face_sign=1,
    )

    return enclosure


def diagnostics(part: Part) -> dict[str, object]:
    """Return basic geometry checks."""
    bb = part.bounding_box()
    volume_mm3 = part.volume
    petg_density_g_per_mm3 = 1.27e-3
    mass_g = volume_mm3 * petg_density_g_per_mm3
    cavity_side = p.cube_outer - 2 * (p.outer_skin_t + p.void_t + p.inner_skin_t)
    cavity_l = cavity_side**3 / 1_000_000

    return {
        "bounding_box_mm": [
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ],
        "volume_cm3": round(volume_mm3 / 1000, 1),
        "petg_mass_g": round(mass_g, 1),
        "nominal_cavity_l": round(cavity_l, 2),
        "is_valid": part.is_valid,
        "n_solids": len(part.solids()),
        "n_faces": len(part.faces()),
        "n_edges": len(part.edges()),
        "checks": {
            "outer_dim_x_ok": math.isclose(bb.size.X, p.cube_outer, abs_tol=0.01),
            "outer_dim_y_ok": math.isclose(bb.size.Y, p.cube_outer, abs_tol=0.01),
            "outer_dim_z_ok": math.isclose(bb.size.Z, p.cube_outer, abs_tol=0.01),
            "valid": part.is_valid,
        },
    }


def export_3mf(part: Part, path: Path) -> None:
    """Export 3MF through build123d's Mesher API."""
    mesher = Mesher(unit=Unit.MM)
    mesher.add_shape(part, linear_deflection=0.05, angular_deflection=0.1)
    mesher.add_meta_data(
        name_space="sand-cube",
        name="params",
        value=json.dumps(p.__dict__, sort_keys=True),
        metadata_type="str",
        must_preserve=False,
    )
    mesher.write(str(path))


def main() -> None:
    part = build()
    data = diagnostics(part)
    assert data["is_valid"], "Generated enclosure is not a valid part"

    out = Path("build")
    out.mkdir(exist_ok=True)
    export_step(part, out / "sand_cube.step", unit=Unit.MM)
    export_3mf(part, out / "sand_cube.3mf")
    (out / "diagnostics.json").write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
