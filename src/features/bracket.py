"""Sheet-metal horn bracket for the Sand Cube top mount."""

from __future__ import annotations

import math

from build123d import (
    Align,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    RectangleRounded,
    make_face,
    add,
    extrude,
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
    if axis == "y":
        from build123d import Rot

        cyl = Rot(90, 0, 0) * cyl
    elif axis != "z":
        raise ValueError(f"Unsupported axis: {axis}")
    return Location(center) * cyl


def _vertical_plate_outline(
    *,
    bottom_z: float,
    horn_center_z: float,
    material_t: float,
    head_radius: float,
    neck_bottom_w: float,
    neck_top_w: float,
) -> Part:
    _ = neck_top_w
    with BuildPart() as plate:
        with BuildSketch(Plane.XZ):
            center = (0.0, horn_center_z)
            right_bottom = (neck_bottom_w / 2, bottom_z)
            v_x = right_bottom[0] - center[0]
            v_z = right_bottom[1] - center[1]
            d2 = v_x * v_x + v_z * v_z
            if d2 <= head_radius * head_radius:
                raise ValueError("Vertical bracket neck point must be outside head circle")
            base_x = center[0] + head_radius * head_radius / d2 * v_x
            base_z = center[1] + head_radius * head_radius / d2 * v_z
            tangent_scale = head_radius * math.sqrt(d2 - head_radius * head_radius) / d2
            right_tangent = (
                base_x + tangent_scale * -v_z,
                base_z + tangent_scale * v_x,
            )
            left_tangent = (-right_tangent[0], right_tangent[1])
            right_angle = math.degrees(
                math.atan2(right_tangent[1] - horn_center_z, right_tangent[0])
            )
            left_angle = math.degrees(
                math.atan2(left_tangent[1] - horn_center_z, left_tangent[0])
            )
            if left_angle <= right_angle:
                left_angle += 360.0
            with BuildLine():
                Polyline(
                    (-neck_bottom_w / 2, bottom_z),
                    (neck_bottom_w / 2, bottom_z),
                    right_tangent,
                )
                CenterArc(
                    center,
                    head_radius,
                    start_angle=right_angle,
                    arc_size=left_angle - right_angle,
                )
                Polyline(
                    left_tangent,
                    (-neck_bottom_w / 2, bottom_z),
                )
            make_face()
        extrude(amount=material_t)
    return plate.part


def _rounded_base_plate(
    *,
    width: float,
    front_y: float,
    back_y: float,
    corner_r: float,
    top_z: float,
    material_t: float,
) -> Part:
    """Flat top foot: a simple rounded rectangle of constant sheet thickness."""
    length = back_y - front_y
    center_y = (front_y + back_y) / 2
    with BuildPart() as base:
        with BuildSketch(Plane.XY):
            RectangleRounded(width, length, corner_r)
        extrude(amount=material_t)
    return Pos(0, center_y, top_z) * base.part


def _bend_band(
    *,
    horn_rear_y: float,
    top_z: float,
    material_t: float,
    inside_r: float,
    width: float,
    vertical_overlap: float = 6.0,
) -> Part:
    """Constant-thickness 90-degree sheet-metal bend at the bracket foot.

    The sketch is a quarter annulus in the YZ plane with a short straight
    continuation into the upright. Extruding it along X avoids pretending a
    sharp fillet is a manufacturable bend.
    """
    center_y = horn_rear_y + material_t + inside_r
    center_z = top_z + material_t + inside_r
    outer_r = inside_r + material_t

    with BuildPart() as bend:
        with BuildSketch(Plane.YZ):
            with BuildLine():
                Polyline(
                    (horn_rear_y, center_z + vertical_overlap),
                    (horn_rear_y, center_z),
                )
                CenterArc(
                    (center_y, center_z),
                    outer_r,
                    start_angle=180.0,
                    arc_size=90.0,
                )
                Polyline(
                    (center_y, top_z),
                    (center_y, top_z + material_t),
                )
                CenterArc(
                    (center_y, center_z),
                    inside_r,
                    start_angle=270.0,
                    arc_size=-90.0,
                )
                Polyline(
                    (horn_rear_y + material_t, center_z),
                    (horn_rear_y + material_t, center_z + vertical_overlap),
                    (horn_rear_y, center_z + vertical_overlap),
                )
            make_face()
        extrude(amount=width)
    return Pos(-width / 2, 0, 0) * bend.part


def build_horn_bracket(
    *,
    enclosure_top_z: float,
    horn_rear_y: float,
    horn_center_z: float,
    material_t: float = 4.0,
    bend_inside_r: float = 8.0,
    base_front_y: float | None = None,
    base_back_y: float = 86.0,
    base_w: float = 72.0,
    base_corner_r: float = 7.0,
    bend_w: float = 58.0,
    top_bolt_spacing: float = 50.0,
    top_bolt_y: float = 36.0,
    top_bolt_d: float = 5.5,
    binding_post_spacing: float = 19.05,
    binding_post_y: float = 72.0,
    binding_post_grommet_hole_d: float = 6.8,
    horn_head_d: float = 112.0,
    acoustic_hole_d: float = 42.0,
    horn_bolt_d: float = 6.6,
    horn_bolt_3_bcd: float = 57.0,
    horn_bolt_2_bcd: float = 76.0,
) -> Part:
    """Build a folded 90-degree bracket in installed world coordinates.

    The vertical face is intended to be sandwiched between the printed horn
    flange and the B&C DE250 compression-driver face. The top foot is a simple
    rounded rectangle with two dedicated screws plus two insulated binding-post
    pass-throughs that double as the rear clamp points.
    """
    bend_center_y = horn_rear_y + material_t + bend_inside_r
    bend_center_z = enclosure_top_z + material_t + bend_inside_r
    if base_front_y is None:
        base_front_y = bend_center_y

    head_radius = horn_head_d / 2
    join_overlap = 0.15
    bend_vertical_overlap = 6.0

    base = _rounded_base_plate(
        width=base_w,
        front_y=base_front_y - join_overlap,
        back_y=base_back_y,
        corner_r=base_corner_r,
        top_z=enclosure_top_z,
        material_t=material_t,
    )
    bend = _bend_band(
        horn_rear_y=horn_rear_y,
        top_z=enclosure_top_z,
        material_t=material_t,
        inside_r=bend_inside_r,
        width=bend_w,
        vertical_overlap=bend_vertical_overlap,
    )
    # BuildSketch(Plane.XZ) extrudes along -Y in this context. Offset the
    # upright by one material thickness so the finished sheet occupies
    # horn_rear_y..horn_rear_y + material_t, matching the bend and cutouts.
    vertical = Location((0, horn_rear_y + material_t, 0)) * _vertical_plate_outline(
        bottom_z=bend_center_z + bend_vertical_overlap - join_overlap,
        horn_center_z=horn_center_z,
        material_t=material_t,
        head_radius=head_radius,
        neck_bottom_w=58.0,
        neck_top_w=42.0,
    )

    bracket = base.fuse(bend, vertical, glue=True, tol=0.01).clean().fix()

    with BuildPart() as cutouts:
        # Base screw holes into the reinforced top island.
        half_spacing = top_bolt_spacing / 2
        for x in (-half_spacing, half_spacing):
            add(
                _oriented_cylinder(
                    diameter=top_bolt_d,
                    depth=material_t + 2.0,
                    axis="z",
                    center=(
                        x,
                        top_bolt_y - half_spacing,
                        enclosure_top_z + material_t / 2,
                    ),
                )
            )

        # Binding posts double as the rear bracket clamp points. These are
        # oversized for TPU insulating sleeves, not bare metal posts.
        for x in (-binding_post_spacing / 2, binding_post_spacing / 2):
            add(
                _oriented_cylinder(
                    diameter=binding_post_grommet_hole_d,
                    depth=material_t + 2.0,
                    axis="z",
                    center=(x, binding_post_y, enclosure_top_z + material_t / 2),
                )
            )

        # Acoustic throat clearance and both DE250 bolt patterns. The horn is
        # rotated -60 degrees in the assembly, so these angles match the holes
        # in the placed printed horn flange.
        add(
            _oriented_cylinder(
                diameter=acoustic_hole_d,
                depth=material_t * 3,
                axis="y",
                center=(0, horn_rear_y + material_t / 2, horn_center_z),
            ),
        )
        bolt_r = horn_bolt_3_bcd / 2
        for angle_deg in (30.0, 150.0, 270.0):
            angle = math.radians(angle_deg)
            add(
                _oriented_cylinder(
                    diameter=horn_bolt_d,
                    depth=material_t * 3,
                    axis="y",
                    center=(
                        bolt_r * math.cos(angle),
                        horn_rear_y + material_t / 2,
                        horn_center_z + bolt_r * math.sin(angle),
                    ),
                ),
            )
        bolt_r = horn_bolt_2_bcd / 2
        for angle_deg in (-60.0, 120.0):
            angle = math.radians(angle_deg)
            add(
                _oriented_cylinder(
                    diameter=horn_bolt_d,
                    depth=material_t * 3,
                    axis="y",
                    center=(
                        bolt_r * math.cos(angle),
                        horn_rear_y + material_t / 2,
                        horn_center_z + bolt_r * math.sin(angle),
                    ),
                ),
            )

    bracket = bracket - cutouts.part
    return bracket.clean().fix()


def build_binding_post_grommet(
    *,
    washer_d: float = 13.0,
    washer_t: float = 2.0,
    sleeve_od: float = 6.2,
    bore_d: float = 4.3,
    sleeve_l: float = 22.0,
) -> Part:
    """TPU insulating/sealing sleeve for a binding post through metal + shell.

    Local coordinates put the washer underside at ``z = 0``. The sleeve extends
    downward through the bracket and printed top island.
    """
    with BuildPart() as grommet:
        add(
            Cylinder(
                radius=washer_d / 2,
                height=washer_t,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
        add(
            Pos(0, 0, -sleeve_l)
            * Cylinder(
                radius=sleeve_od / 2,
                height=sleeve_l,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
    bore = Pos(0, 0, -sleeve_l - 1.0) * Cylinder(
        radius=bore_d / 2,
        height=sleeve_l + washer_t + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    return (grommet.part - bore).clean().fix()
