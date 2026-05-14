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
    Location,
    Mesher,
    Part,
    Pos,
    Rot,
    Unit,
    add,
    export_step,
)

from params import p
from src.features.baffle import black_hole_baffle
from src.features.bracing import reinforcement_ring


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


def _bolt_circle_bosses_and_bores(
    *,
    radius: float,
    count: int,
    boss_center_y: float,
    bore_open_y: float,
    bore_direction_y: int,
) -> tuple[Part, Part]:
    """Create bolt-circle bosses plus blind M4 insert bores.

    The bosses are solid until their matching bore tools are subtracted. This
    lets us choose which side the insert is installed from, which matters for a
    rear-mounted driver: its insert holes open from the cabinet interior, not
    from the visible front face.
    """
    full_h = p.outer_skin_t + p.void_t + p.inner_skin_t
    bore_depth = p.insert_bore_depth + 0.4
    bore_center_y = bore_open_y + bore_direction_y * bore_depth / 2

    with BuildPart() as bosses:
        for index in range(count):
            angle = math.tau * index / count + (math.tau / 8 if count == 4 else 0)
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            add(
                _oriented_cylinder(
                    diameter=p.boss_od,
                    depth=full_h,
                    axis="y",
                    center=(x, boss_center_y, z),
                )
            )

    with BuildPart() as bores:
        for index in range(count):
            angle = math.tau * index / count + (math.tau / 8 if count == 4 else 0)
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            add(
                _oriented_cylinder(
                    diameter=p.insert_bore_d,
                    depth=bore_depth,
                    axis="y",
                    center=(x, bore_center_y, z),
                )
            )
    return bosses.part, bores.part


def build() -> Part:
    """Create the first complete CAD pass for the enclosure."""
    shell_span = p.cube_outer - 2 * p.outer_skin_t
    inner_outer = p.cube_outer - 2 * (p.outer_skin_t + p.void_t)
    cavity = inner_outer - 2 * p.inner_skin_t
    half = p.cube_outer / 2
    inner_face_y = inner_outer / 2
    front_inner_y = -inner_face_y
    rear_inner_y = inner_face_y
    sandwich_t = p.outer_skin_t + p.void_t + p.inner_skin_t
    through = p.cube_outer + 10

    outer_solid = Box(p.cube_outer, p.cube_outer, p.cube_outer)
    sand_void = Box(shell_span, shell_span, shell_span)
    inner_solid = Box(inner_outer, inner_outer, inner_outer)
    acoustic_cavity = Box(cavity, cavity, cavity)

    enclosure = (outer_solid - sand_void) + (inner_solid - acoustic_cavity)

    # Driver is rear-mounted: the reinforcement ring sits inside the acoustic
    # cavity on the back side of the front baffle.
    enclosure += Pos(0, front_inner_y + p.ring_t, 0) * Rot(90, 0, 0) * reinforcement_ring(
        cutout_dia=p.driver_cutout_dia,
        ring_width=p.ring_width,
        ring_t=p.ring_t,
    )
    enclosure += Pos(0, rear_inner_y, 0) * Rot(90, 0, 0) * reinforcement_ring(
        cutout_dia=p.pr_cutout_dia,
        ring_width=p.ring_width,
        ring_t=p.ring_t,
    )

    driver_bosses, driver_insert_bores = _bolt_circle_bosses_and_bores(
        radius=p.driver_bolt_circle_r,
        count=p.driver_screw_count,
        boss_center_y=-half + sandwich_t / 2,
        bore_open_y=front_inner_y,
        bore_direction_y=-1,
    )
    pr_bosses, pr_insert_bores = _bolt_circle_bosses_and_bores(
        radius=p.pr_bolt_circle_r,
        count=p.pr_screw_count,
        boss_center_y=half - sandwich_t / 2,
        bore_open_y=half,
        bore_direction_y=-1,
    )
    enclosure += driver_bosses + pr_bosses

    # Driver front face is -Y; PR rear face is +Y. Cut after adding hidden
    # rear-mount structure so the visible recess carves the front surface clean.
    enclosure -= Pos(0, -half - 0.2, 0) * Rot(90, 0, 0) * black_hole_baffle(
        face_thickness=sandwich_t,
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
    enclosure -= driver_insert_bores + pr_insert_bores

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
