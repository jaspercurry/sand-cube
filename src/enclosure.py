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
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Location,
    Mesher,
    Mode,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Rot,
    Unit,
    add,
    export_step,
    extrude,
    fillet,
)
from bd_warehouse.thread import IsoThread

from params import p
from src.features.baffle import black_hole_baffle
from src.features.horn import (
    build_jmlc_horn,
    horn_dimensions,
    jmlc_profile_metadata,
)


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
        mode=Mode.PRIVATE,
    )
    if axis == "x":
        cyl = Rot(0, 90, 0) * cyl
    elif axis == "y":
        cyl = Rot(90, 0, 0) * cyl
    elif axis != "z":
        raise ValueError(f"Unsupported axis: {axis}")
    return Location(center) * cyl


def _primary_shape(shape: Part) -> Part:
    """Drop tiny OpenCascade boolean crumbs and keep the main enclosure body."""
    if hasattr(shape, "bounding_box"):
        return shape
    return max(shape, key=lambda item: item.volume)


def _external_cube_edges(part: Part) -> list:
    """Find the 12 long outside cube edges and avoid circular feature edges."""
    half = p.cube_outer / 2
    edges = []
    for edge in part.edges():
        bb = edge.bounding_box()
        sizes = (bb.size.X, bb.size.Y, bb.size.Z)
        centers = (
            (bb.min.X + bb.max.X) / 2,
            (bb.min.Y + bb.max.Y) / 2,
            (bb.min.Z + bb.max.Z) / 2,
        )
        pinned_axes = sum(
            abs(abs(center) - half) < 0.01 and size < 0.01
            for center, size in zip(centers, sizes)
        )
        if pinned_axes >= 2 and max(sizes) > p.cube_outer * 0.65:
            edges.append(edge)
    return edges


def _bolt_circle_bores(
    *,
    radius: float,
    count: int,
    bore_depth: float,
    bore_open_y: float,
    bore_direction_y: int,
) -> Part:
    """Create blind M4 heat-set insert bores on an X/Z bolt circle."""
    bore_center_y = bore_open_y + bore_direction_y * bore_depth / 2
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
    return bores.part


def _hex_prism_y(
    *,
    across_flats: float,
    depth: float,
    center: tuple[float, float, float],
    rotation: float = 30.0,
) -> Part:
    """Hexagonal prism oriented on Y for a captive connector nut pocket."""
    with BuildPart() as hex_prism:
        with BuildSketch(Plane.XZ):
            RegularPolygon(
                radius=across_flats / 2,
                side_count=6,
                major_radius=False,
                rotation=rotation,
            )
        extrude(amount=depth / 2, both=True)
    return Location(center) * hex_prism.part


def _gx16_rear_cutout() -> Part:
    """GX16 bottom-right rear connector cutout with captive inner hex pocket."""
    half = p.cube_outer / 2
    panel_inner_y = half - p.gx16_flange_recess_depth - p.gx16_panel_land_t
    inner_face_y = half - p.rear_cap_t
    hex_depth = panel_inner_y - inner_face_y + 0.2
    hex_center_y = inner_face_y + hex_depth / 2 - 0.1
    hex_to_pr_angle = math.degrees(math.atan2(-p.gx16_z, -p.gx16_x))
    with BuildPart() as cutout:
        add(
            _oriented_cylinder(
                diameter=p.gx16_flange_recess_d,
                depth=p.gx16_flange_recess_depth,
                axis="y",
                center=(p.gx16_x, half - p.gx16_flange_recess_depth / 2, p.gx16_z),
            )
        )
        add(
            _oriented_cylinder(
                diameter=p.gx16_hole_d,
                depth=p.rear_cap_t + 2,
                axis="y",
                center=(p.gx16_x, half - p.rear_cap_t / 2, p.gx16_z),
            )
        )
        add(
            _hex_prism_y(
                across_flats=p.gx16_nut_across_flats,
                depth=hex_depth,
                center=(p.gx16_x, hex_center_y, p.gx16_z),
                rotation=hex_to_pr_angle - 30.0,
            )
        )
    return cutout.part


def _gx16_connector_island() -> Part:
    """Local solid rear-cap island around the GX16 inner nut pocket."""
    half = p.cube_outer / 2
    return Pos(p.gx16_x, half - p.rear_cap_t / 2, p.gx16_z) * Box(
        p.gx16_island_xy,
        p.rear_cap_t,
        p.gx16_island_xy,
    )


def _sand_fill_port_cutout(*, x: float, z: float) -> Part:
    """Rear coarse threaded fill port that breaks into the top sand void."""
    half = p.cube_outer / 2
    port_depth = p.rear_cap_t + 0.8
    thread_center_y = half - p.fill_thread_length / 2 + 0.2
    port_center_y = half - port_depth / 2
    thread = IsoThread(
        major_diameter=p.fill_thread_major_d,
        pitch=p.fill_thread_pitch,
        length=p.fill_thread_length,
        external=False,
        end_finishes=("square", "fade"),
        interference=0.35,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    with BuildPart() as cutout:
        add(
            _oriented_cylinder(
                diameter=p.fill_entry_d,
                depth=p.fill_entry_depth,
                axis="y",
                center=(x, half - p.fill_entry_depth / 2, z),
            )
        )
        add(
            _oriented_cylinder(
                diameter=p.fill_thread_core_d,
                depth=port_depth,
                axis="y",
                center=(x, port_center_y, z),
            )
        )
        add(Location((x, thread_center_y, z)) * Rot(90, 0, 0) * thread)
    return cutout.part


def _skin_bridge_posts() -> Part:
    """Point-like bridges through the four sand-filled side/top/bottom voids."""
    half = p.cube_outer / 2
    void_center = half - p.outer_skin_t - p.void_t / 2
    grid = (-60.0, 0.0, 60.0)

    def in_top_island(x: float, y: float) -> bool:
        return (
            abs(x - p.top_island_x) <= p.top_island_w / 2
            and abs(y - p.top_island_y) <= p.top_island_d / 2
        )

    with BuildPart() as posts:
        for y in grid:
            for z in grid:
                for side in (-1, 1):
                    add(
                        _oriented_cylinder(
                            diameter=p.bracing_post_d,
                            depth=p.void_t,
                            axis="x",
                            center=(side * void_center, y, z),
                        )
                    )
        for x in grid:
            for y in grid:
                for side in (-1, 1):
                    if side > 0 and in_top_island(x, y):
                        continue
                    add(
                        _oriented_cylinder(
                            diameter=p.bracing_post_d,
                            depth=p.void_t,
                            axis="z",
                            center=(x, y, side * void_center),
                        )
                    )
    return posts.part


def _top_reinforcement_island() -> Part:
    """Hidden solid top island for horn bracket bolts and tweeter terminals."""
    half = p.cube_outer / 2
    top_stack_t = p.outer_skin_t + p.void_t + p.inner_skin_t
    return Pos(p.top_island_x, p.top_island_y, half - top_stack_t / 2) * Box(
        p.top_island_w,
        p.top_island_d,
        top_stack_t,
    )


def _top_binding_post_cutouts() -> Part:
    """Two BPA-38G binding post holes through the hidden top island."""
    half = p.cube_outer / 2
    top_stack_t = p.outer_skin_t + p.void_t + p.inner_skin_t
    inner_top_z = half - top_stack_t
    with BuildPart() as cutouts:
        for x in (-p.binding_post_spacing / 2, p.binding_post_spacing / 2):
            add(
                _oriented_cylinder(
                    diameter=p.binding_post_recess_d,
                    depth=p.binding_post_recess_depth,
                    axis="z",
                    center=(x, p.binding_post_y, half - p.binding_post_recess_depth / 2),
                )
            )
            add(
                _oriented_cylinder(
                    diameter=p.binding_post_hole_d,
                    depth=top_stack_t + 2.0,
                    axis="z",
                    center=(x, p.binding_post_y, half - top_stack_t / 2),
                )
            )
            add(
                _oriented_cylinder(
                    diameter=p.binding_post_washer_recess_d,
                    depth=p.binding_post_washer_recess_depth,
                    axis="z",
                    center=(
                        x,
                        p.binding_post_y,
                        inner_top_z + p.binding_post_washer_recess_depth / 2,
                    ),
                )
            )
    return cutouts.part


def _top_bracket_cutouts() -> Part:
    """50 x 50 mm M5 bracket holes with internal washer counterbores."""
    half = p.cube_outer / 2
    top_stack_t = p.outer_skin_t + p.void_t + p.inner_skin_t
    inner_top_z = half - top_stack_t
    spacing = p.bracket_hole_spacing / 2
    with BuildPart() as cutouts:
        for x in (-spacing, spacing):
            for y in (
                p.bracket_hole_y - spacing,
                p.bracket_hole_y + spacing,
            ):
                add(
                    _oriented_cylinder(
                        diameter=p.bracket_hole_d,
                        depth=top_stack_t + 2.0,
                        axis="z",
                        center=(x, y, half - top_stack_t / 2),
                    )
                )
                add(
                    _oriented_cylinder(
                        diameter=p.bracket_washer_recess_d,
                        depth=p.bracket_washer_recess_depth,
                        axis="z",
                        center=(
                            x,
                            y,
                            inner_top_z + p.bracket_washer_recess_depth / 2,
                        ),
                    )
                )
    return cutouts.part


def build_fill_plug() -> Part:
    """Printable coarse-thread sand-fill plug for the rear fill ports."""
    thread = IsoThread(
        major_diameter=p.fill_thread_major_d - 0.35,
        pitch=p.fill_thread_pitch,
        length=p.fill_thread_length - 1.0,
        external=True,
        end_finishes=("chamfer", "fade"),
        interference=0.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    with BuildPart() as plug:
        add(thread)
        add(
            Pos(0, 0, p.fill_thread_length - 1.0)
            * Cylinder(
                radius=p.fill_boss_od / 2,
                height=5.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
    return plug.part


def build_horn() -> Part:
    """Build the separate B&C DE250 Le Cleac'h horn."""
    return build_jmlc_horn(
        throat_d=p.horn_throat_d,
        mouth_outer_d=p.horn_mouth_outer_d,
        wall_t=p.horn_wall_t,
        exit_angle_deg=p.horn_exit_angle_deg,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=p.horn_profile_step,
        lip_r=p.horn_lip_r,
        flange_d=p.horn_flange_d,
        flange_t=p.horn_flange_t,
        bolt_clearance_d=p.horn_bolt_clearance_d,
        bolt_3_bcd=p.horn_bolt_3_bcd,
        bolt_2_bcd=p.horn_bolt_2_bcd,
    )


def build() -> Part:
    """Create the first complete CAD pass for the enclosure."""
    shell_span = p.cube_outer - 2 * p.outer_skin_t
    cavity = p.cube_outer - 2 * (p.outer_skin_t + p.void_t + p.inner_skin_t)
    half = p.cube_outer / 2
    front_inner_y = -half + p.front_cap_t
    rear_inner_y = half - p.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    cavity_center_y = (front_inner_y + rear_inner_y) / 2
    front_mount_y = front_inner_y
    sandwich_t = p.front_cap_t
    through = p.cube_outer + 10

    outer_solid = Box(p.cube_outer, p.cube_outer, p.cube_outer)
    acoustic_cavity = Pos(0, cavity_center_y, 0) * Box(cavity, cavity_y, cavity)

    enclosure = outer_solid - acoustic_cavity
    for x in (-1, 1):
        enclosure -= Pos(
            x * (half - p.outer_skin_t - p.void_t / 2),
            cavity_center_y,
            0,
        ) * Box(
            p.void_t,
            cavity_y,
            shell_span,
        )
    for z in (-1, 1):
        enclosure -= Pos(
            0,
            cavity_center_y,
            z * (half - p.outer_skin_t - p.void_t / 2),
        ) * Box(
            shell_span,
            cavity_y,
            p.void_t,
        )
    enclosure = _primary_shape(enclosure)
    enclosure += _skin_bridge_posts()
    enclosure = _primary_shape(enclosure)
    enclosure += _gx16_connector_island()
    enclosure = _primary_shape(enclosure)
    enclosure += _top_reinforcement_island()
    enclosure = _primary_shape(enclosure)

    # The front and rear are solid end caps. The driver is inserted through the
    # rear PR/service opening and fastens into shallow heat-set inserts opened
    # from the cavity side of the solid front face.

    driver_insert_bores = _bolt_circle_bores(
        radius=p.driver_bolt_circle_r,
        count=p.driver_screw_count,
        bore_depth=p.driver_insert_bore_depth,
        bore_open_y=front_mount_y,
        bore_direction_y=-1,
    )
    pr_insert_bores = _bolt_circle_bores(
        radius=p.pr_bolt_circle_r,
        count=p.pr_screw_count,
        bore_depth=p.pr_insert_bore_depth,
        bore_open_y=half - p.pr_recess_depth,
        bore_direction_y=-1,
    )

    # Driver front face is -Y; PR rear face is +Y. Cut after adding hidden
    # rear-mount structure so the visible recess carves the front surface clean.
    enclosure -= Pos(0, -half, 0) * Rot(-90, 0, 0) * black_hole_baffle(
        face_thickness=sandwich_t,
        driver_cutout_dia=p.driver_cutout_dia,
        blend_radius=p.baffle_blend_r,
        blend_depth=p.baffle_blend_depth,
        tangent_in=p.baffle_tangent_in,
        tangent_out=p.baffle_tangent_out,
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= _oriented_cylinder(
        diameter=p.driver_cutout_dia,
        depth=through,
        axis="y",
        center=(0, -half, 0),
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= _oriented_cylinder(
        diameter=p.pr_recess_dia,
        depth=p.pr_recess_depth,
        axis="y",
        center=(0, half - p.pr_recess_depth / 2, 0),
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= _oriented_cylinder(
        diameter=p.pr_service_cutout_dia,
        depth=through,
        axis="y",
        center=(0, half, 0),
    )
    enclosure = _primary_shape(enclosure)
    enclosure -= driver_insert_bores
    enclosure = _primary_shape(enclosure)
    enclosure -= pr_insert_bores
    enclosure = _primary_shape(enclosure)
    enclosure -= _gx16_rear_cutout()
    enclosure = _primary_shape(enclosure)
    for fill_x in (-p.fill_port_x, p.fill_port_x):
        enclosure -= _sand_fill_port_cutout(x=fill_x, z=p.fill_port_z)
        enclosure = _primary_shape(enclosure)
    enclosure -= _top_binding_post_cutouts()
    enclosure = _primary_shape(enclosure)
    enclosure -= _top_bracket_cutouts()
    enclosure = _primary_shape(enclosure)

    if p.edge_fillet_r > 0:
        enclosure = fillet(_external_cube_edges(enclosure), radius=p.edge_fillet_r)
        enclosure = _primary_shape(enclosure)

    return enclosure


def diagnostics(part: Part) -> dict[str, object]:
    """Return basic geometry checks."""
    bb = part.bounding_box()
    volume_mm3 = part.volume
    petg_density_g_per_mm3 = 1.27e-3
    mass_g = volume_mm3 * petg_density_g_per_mm3
    cavity_side = p.cube_outer - 2 * (p.outer_skin_t + p.void_t + p.inner_skin_t)
    front_inner_y = -p.cube_outer / 2 + p.front_cap_t
    rear_inner_y = p.cube_outer / 2 - p.rear_cap_t
    cavity_y = rear_inner_y - front_inner_y
    cavity_l = cavity_side * cavity_y * cavity_side / 1_000_000

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
    plug = build_fill_plug()
    horn = build_horn()
    data = diagnostics(part)
    assert data["is_valid"], "Generated enclosure is not a valid part"
    horn_data = horn_dimensions(horn)
    horn_data.update(
        jmlc_profile_metadata(
            throat_d=p.horn_throat_d,
            mouth_outer_d=p.horn_mouth_outer_d,
            wall_t=p.horn_wall_t,
            exit_angle_deg=p.horn_exit_angle_deg,
            wavefront_t=p.horn_wavefront_t,
            throat_angle_deg=p.horn_throat_angle_deg,
            step=p.horn_profile_step,
        )
    )
    assert horn_data["is_valid"], "Generated horn is not a valid part"

    out = Path("build")
    out.mkdir(exist_ok=True)
    export_step(part, out / "sand_cube.step", unit=Unit.MM)
    export_step(plug, out / "sand_fill_plug.step", unit=Unit.MM)
    export_step(horn, out / "jmlc_horn.step", unit=Unit.MM)
    export_3mf(part, out / "sand_cube.3mf")
    export_3mf(plug, out / "sand_fill_plug.3mf")
    export_3mf(horn, out / "jmlc_horn.3mf")
    (out / "diagnostics.json").write_text(json.dumps(data, indent=2))
    (out / "horn_diagnostics.json").write_text(json.dumps(horn_data, indent=2))
    print(json.dumps({"enclosure": data, "horn": horn_data}, indent=2))


if __name__ == "__main__":
    main()
