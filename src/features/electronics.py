"""First-pass electronics enclosure layouts for the amp/Pi/buck/mic stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from build123d import (
    Align,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Cylinder,
    Location,
    Mode,
    Part,
    Plane,
    Pos,
    Polyline,
    Rot,
    add,
    extrude,
    loft,
    make_face,
)


Orientation = Literal[
    "floor",
    "front_wall",
    "rear_wall",
    "top_compartment",
    "amp_envelope",
]


@dataclass(frozen=True)
class BoardSpec:
    name: str
    size_x: float
    size_y: float
    size_z: float
    mount_points: tuple[tuple[float, float], ...] = ()
    mount_hole_d: float = 0.0
    post_od: float = 8.0
    post_h: float = 6.0
    bore_d: float = 3.2


@dataclass(frozen=True)
class DiskSpec:
    name: str
    diameter: float
    thickness: float


@dataclass(frozen=True)
class Placement:
    spec: str
    x: float
    y: float
    z: float = 0.0
    orientation: Orientation = "floor"
    note: str = ""


@dataclass(frozen=True)
class LayoutVariant:
    name: str
    description: str
    outer_size: tuple[float, float, float]
    placements: tuple[Placement, ...]
    shelf: tuple[float, float, float, float] | None = None
    top_mic: TopMicCompartment | None = None
    separate_mic: bool = False
    wall_mount: bool = False
    vertical_buck: bool = False
    mic_on_front: bool = False


@dataclass(frozen=True)
class TopMicCompartment:
    center_x: float = 0.0
    center_y: float = 0.0
    outer_d: float = 114.0
    inner_d: float = 104.0
    outer_h: float = 17.0
    floor_t: float = 2.0
    cable_pass_d: float = 14.0


@dataclass(frozen=True)
class PrintedConfig:
    wall_t: float = 3.0
    floor_t: float = 3.0
    roof_t: float = 3.0
    front_wall_t: float = 3.0
    vent_d: float = 6.0
    vent_pitch: float = 14.0
    vent_edge_margin: float = 17.0
    shelf_t: float = 3.0
    shelf_support_d: float = 8.0
    buck_bracket_t: float = 3.0
    buck_bracket_margin: float = 5.0


AMP_WIRE_EXIT_CLEARANCE = 18.0
AMP_MOUNT_LONG_CTC = 101.7
AMP_MOUNT_NARROW_CTC = 88.0
BUCK_WIRE_CLEARANCE = 18.0
BUCK_REAR_MOUNT_BODY_H = 58.0
BUCK_REAR_MOUNT_BODY_DEPTH = 21.0
BUCK_MOUNT_HOLE_CTC = 53.67
BUCK_REAR_PIN_D = 5.8
BUCK_REAR_PIN_DEPTH = 4.0
BUCK_REAR_PIN_CENTER_Z_FROM_BOTTOM = 29.0
BUCK_REAR_WIRE_NOTCH_W = 17.0
BUCK_REAR_WIRE_SLOT_H = 3.0
BUCK_REAR_WIRE_SLOT_EXTRA_DEPTH = 5.0
BUCK_REAR_WIRE_CHAMFER_DEPTH = 6.0
BUCK_REAR_WIRE_CHAMFER_H = 6.0
GX14_HOLE_W = 14.8
GX14_HOLE_H = 15.8
GX14_COLLAR_OD = 18.06
GX14_RECESS_W = 19.0
GX14_RECESS_H = 19.8
GX14_RECESS_DEPTH = 1.2
GX14_CENTER_Z = 37.0
LID_RECEIVER_OD = 10.0
LID_RECEIVER_ENGAGEMENT_H = 2.0
LID_RECEIVER_TAPER_H = 8.0
LID_RECEIVER_PILOT_D = 2.5
PI5_PORT_EDGE_MIDLINE_FROM_BOTTOM = 28.0
PI5_REAR_PORT_WINDOW_H = 25.0
PI5_REAR_PORT_WINDOW_CENTER_Z_FROM_BOARD_BOTTOM = 8.0
PI5_REAR_PORT_BAYS = (
    ("left_usb_stack", 47.0, 15.5),
    ("middle_usb_stack", 29.1, 15.5),
    ("right_ethernet", 10.2, 17.0),
)
PI_POWER_INPUT_HOLE_W = 10.83
PI_POWER_INPUT_HOLE_H = 11.3
PI_POWER_INPUT_CENTER_Z = 43.0
WALL_VENT_SLOT_LEN = 12.0
WALL_VENT_SLOT_H = 4.0
WALL_VENT_MARGIN = 24.0
WALL_VENT_Z_CENTERS = (16.0, 31.0, 46.0)
BOTTOM_VENT_SLOT_X = 12.0
BOTTOM_VENT_SLOT_Y = 5.0
BOTTOM_VENT_MARGIN = 20.0
BOTTOM_VENT_STANDOFF_CLEARANCE = 8.0
PI_ADJUST_SLOT_W = 3.4
PI_ADJUST_SLOT_LEN = 24.0
PI_ADJUST_SLOT_KEEPAWAY = 4.0


AMP = BoardSpec(
    name="amp",
    # Active thin-plate layout rotates the amp 90 degrees so the long heatsink
    # runs front-to-back, perpendicular to the rear service face.
    size_x=94.0,
    size_y=108.0,
    size_z=36.0,
    mount_points=(
        (-AMP_MOUNT_NARROW_CTC / 2, -AMP_MOUNT_LONG_CTC / 2),
        (AMP_MOUNT_NARROW_CTC / 2, -AMP_MOUNT_LONG_CTC / 2),
        (-AMP_MOUNT_NARROW_CTC / 2, AMP_MOUNT_LONG_CTC / 2),
        (AMP_MOUNT_NARROW_CTC / 2, AMP_MOUNT_LONG_CTC / 2),
    ),
    mount_hole_d=3.0,
    post_od=8.5,
    post_h=3.0,
    bore_d=3.2,
)

PI_HAT = BoardSpec(
    name="pi_hat",
    # Fit-test envelope for the Pi board/ports. The HAT can overhang the amp
    # input side above the amp, so it no longer drives the enclosure width.
    size_x=56.0,
    size_y=90.0,
    size_z=42.0,
    # Pi USB/Ethernet ports are on the short 56 mm edge. In this enclosure that
    # short edge faces the rear panel, so the official 58 x 49 mm mount pattern
    # is rotated: 49 mm across X, 58 mm front-to-back in Y.
    mount_points=(
        (-24.5, -29.0),
        (24.5, -29.0),
        (-24.5, 29.0),
        (24.5, 29.0),
    ),
    mount_hole_d=2.75,
    post_od=7.0,
    post_h=6.0,
    bore_d=2.7,
)

BUCK = BoardSpec(
    name="buck",
    size_x=62.0,
    size_y=60.0 + BUCK_WIRE_CLEARANCE,
    size_z=21.0,
    mount_points=(
        (-BUCK_MOUNT_HOLE_CTC / 2, 0.0),
        (BUCK_MOUNT_HOLE_CTC / 2, 0.0),
    ),
    mount_hole_d=6.0,
    post_od=10.0,
    post_h=5.0,
    bore_d=3.4,
)

MIC = DiskSpec(name="mic", diameter=100.0, thickness=9.0)

BOARD_SPECS = {spec.name: spec for spec in (AMP, PI_HAT, BUCK)}
DISK_SPECS = {MIC.name: MIC}

DEFAULT_CONFIG = PrintedConfig()


def layout_variants() -> tuple[LayoutVariant, ...]:
    """Return the current first-pass layout study variants."""
    return (
        LayoutVariant(
            name="thin_plate_inline_separate_mic",
            description=(
                "Compact low-profile hidden plate sized for a 256 mm square bed: "
                "rotated amp and Pi are tucked tightly together, the buck converter "
                "mounts vertically on the rear exterior, and the mic stays external."
            ),
            outer_size=(166.0, 124.0, 60.0),
            placements=(
                Placement(
                    "amp",
                    28.0,
                    0.0,
                    note=(
                        "Amp rotated 90 degrees; from the rear, it sits on the "
                        "left side, with a small sidewall gap and equal front/back "
                        "clearance inside the enclosure."
                    ),
                ),
                Placement(
                    "pi_hat",
                    -49.0,
                    11.0,
                    note=(
                        "Pi USB/Ethernet face the rear panel on the rear-view "
                        "right side; no fixed posts, only adjustment slots for "
                        "removable feet."
                    ),
                ),
                Placement(
                    "buck",
                    8.0,
                    72.5,
                    0.0,
                    orientation="rear_wall",
                    note=(
                        "Buck stands vertically on the rear outside wall between "
                        "the Pi openings and GX connectors; wires bend down 90 "
                        "degrees and enter through a bottom-edge notch."
                    ),
                ),
            ),
            separate_mic=True,
        ),
        LayoutVariant(
            name="thin_plate_rear_service_channel",
            description=(
                "Slightly larger hidden plate with the electronics pulled forward "
                "to preserve a rear wiring/service channel for USB, power, and "
                "speaker leads."
            ),
            outer_size=(326.0, 158.0, 58.0),
            placements=(
                Placement(
                    "buck",
                    -122.0,
                    -24.0,
                    note="Buck flat with extra rear cable room.",
                ),
                Placement(
                    "amp",
                    -16.0,
                    -20.0,
                    note="Amp flat and forward of the rear service channel.",
                ),
                Placement(
                    "pi_hat",
                    98.0,
                    20.0,
                    note="Pi/HAT rear ports sit near the open back edge.",
                ),
            ),
            separate_mic=True,
            wall_mount=True,
        ),
        LayoutVariant(
            name="thin_plate_staggered_separate_mic",
            description=(
                "Still low-profile, but less wide: amp and Pi/HAT are staggered "
                "front-to-back, while the buck remains flat in the remaining "
                "corner space."
            ),
            outer_size=(252.0, 188.0, 58.0),
            placements=(
                Placement(
                    "amp",
                    -54.0,
                    -18.0,
                    note="Amp flat on the left/front half of the plate.",
                ),
                Placement(
                    "pi_hat",
                    54.0,
                    26.0,
                    note="Pi/HAT flat on the right/rear half for port access.",
                ),
                Placement(
                    "buck",
                    44.0,
                    -54.0,
                    note="Buck flat in the front-right corner.",
                ),
            ),
            separate_mic=True,
            wall_mount=True,
        ),
        LayoutVariant(
            name="flat_low",
            description=(
                "Lowest height: all electronics lie on the floor, including the "
                "100 mm mic disk. Big footprint, easiest airflow and wiring."
            ),
            outer_size=(238.0, 230.0, 58.0),
            placements=(
                Placement("amp", -54.0, -53.0, note="Amp flat on floor."),
                Placement("pi_hat", 58.0, -61.0, note="Pi/HAT flat on floor."),
                Placement("buck", 58.0, 46.0, note="Buck flat on floor."),
                Placement("mic", -56.0, 58.0, note="Mic disk flat on floor."),
            ),
        ),
        LayoutVariant(
            name="balanced_side_by_side",
            description=(
                "Lower footprint than flat: amp and Pi are side by side, buck "
                "stands vertically near the open rear, mic is on the front face."
            ),
            outer_size=(224.0, 154.0, 118.0),
            placements=(
                Placement("amp", -54.0, -14.0, note="Amp flat on floor."),
                Placement("pi_hat", 54.0, -14.0, note="Pi/HAT flat on floor."),
                Placement(
                    "buck",
                    0.0,
                    56.0,
                    12.0,
                    orientation="rear_wall",
                    note="Buck vertical on a printed rear bracket.",
                ),
                Placement(
                    "mic",
                    0.0,
                    -77.0,
                    58.0,
                    orientation="front_wall",
                    note="Mic disk parked on outside of the front wall.",
                ),
            ),
            vertical_buck=True,
            mic_on_front=True,
        ),
        LayoutVariant(
            name="compact_stack",
            description=(
                "Smallest footprint and closest to cube-like: amp below, Pi/HAT "
                "on a raised shelf, vertical buck at the rear, mic on the front."
            ),
            outer_size=(138.0, 144.0, 124.0),
            placements=(
                Placement("amp", 0.0, -10.0, note="Amp flat on floor."),
                Placement(
                    "pi_hat",
                    0.0,
                    -12.0,
                    51.0,
                    note="Pi/HAT on the raised shelf.",
                ),
                Placement(
                    "buck",
                    0.0,
                    59.0,
                    15.0,
                    orientation="rear_wall",
                    note="Buck vertical on a printed rear bracket.",
                ),
                Placement(
                    "mic",
                    0.0,
                    -72.0,
                    61.0,
                    orientation="front_wall",
                    note="Mic disk parked on outside of the front wall.",
                ),
            ),
            shelf=(100.0, 96.0, 48.0, 0.0),
            vertical_buck=True,
            mic_on_front=True,
        ),
        LayoutVariant(
            name="pi_under_amp_top_mic_compact",
            description=(
                "Compact vertical stack: Pi/HAT sits on the floor, amp is above "
                "it on a shelf, buck is reserved inside a low amp-envelope pocket, "
                "and the mic gets a horizontal top tray."
            ),
            outer_size=(138.0, 148.0, 129.0),
            placements=(
                Placement("pi_hat", 0.0, -16.0, note="Pi/HAT flat on floor."),
                Placement(
                    "amp",
                    0.0,
                    -10.0,
                    56.0,
                    note="Amp above Pi/HAT on raised shelf.",
                ),
                Placement(
                    "buck",
                    20.0,
                    18.0,
                    68.0,
                    orientation="amp_envelope",
                    note="Buck reserved in low-height area inside the amp footprint.",
                ),
                Placement(
                    "mic",
                    0.0,
                    -8.0,
                    114.0,
                    orientation="top_compartment",
                    note="Mic board horizontal in raised top compartment.",
                ),
            ),
            shelf=(120.0, 122.0, 53.0, 0.0),
            top_mic=TopMicCompartment(center_y=-8.0),
        ),
        LayoutVariant(
            name="pi_under_amp_top_mic_wide",
            description=(
                "Same Pi-under-amp stack with more side clearance around the shelf "
                "supports and buck pocket; slightly wider and shallower."
            ),
            outer_size=(150.0, 136.0, 129.0),
            placements=(
                Placement("pi_hat", 0.0, -12.0, note="Pi/HAT flat on floor."),
                Placement(
                    "amp",
                    0.0,
                    -8.0,
                    56.0,
                    note="Amp above Pi/HAT on raised shelf.",
                ),
                Placement(
                    "buck",
                    27.0,
                    20.0,
                    68.0,
                    orientation="amp_envelope",
                    note="Buck reserved in low-height area inside the amp footprint.",
                ),
                Placement(
                    "mic",
                    0.0,
                    -6.0,
                    114.0,
                    orientation="top_compartment",
                    note="Mic board horizontal in raised top compartment.",
                ),
            ),
            shelf=(126.0, 118.0, 53.0, 0.0),
            top_mic=TopMicCompartment(center_y=-6.0),
        ),
        LayoutVariant(
            name="pi_under_amp_top_mic_narrow_deep",
            description=(
                "Narrower, deeper Pi-under-amp stack with extra rear wiring depth "
                "and the same horizontal top mic compartment."
            ),
            outer_size=(128.0, 166.0, 133.0),
            placements=(
                Placement("pi_hat", 0.0, -24.0, note="Pi/HAT flat on floor."),
                Placement(
                    "amp",
                    0.0,
                    -16.0,
                    58.0,
                    note="Amp above Pi/HAT on raised shelf.",
                ),
                Placement(
                    "buck",
                    18.0,
                    30.0,
                    70.0,
                    orientation="amp_envelope",
                    note="Buck reserved in low-height area inside the amp footprint.",
                ),
                Placement(
                    "mic",
                    0.0,
                    -8.0,
                    118.0,
                    orientation="top_compartment",
                    note="Mic board horizontal in raised top compartment.",
                ),
            ),
            shelf=(116.0, 126.0, 55.0, 0.0),
            top_mic=TopMicCompartment(center_y=-8.0),
        ),
    )


def active_layout_variants() -> tuple[LayoutVariant, ...]:
    """Return variants that should be exported in the current focused study."""
    return tuple(
        variant
        for variant in layout_variants()
        if variant.name == "thin_plate_inline_separate_mic"
    )


def archived_layout_variants() -> tuple[LayoutVariant, ...]:
    """Return earlier broad layout concepts retained for reference."""
    active_names = {variant.name for variant in active_layout_variants()}
    return tuple(
        variant for variant in layout_variants() if variant.name not in active_names
    )


def _oriented_cylinder(
    *,
    diameter: float,
    depth: float,
    axis: Literal["x", "y", "z"],
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


def _rear_panel_obround_cutout(
    *,
    width: float,
    height: float,
    depth: float,
    center: tuple[float, float, float],
) -> Part:
    """Vertical relief slot through the rear wall, with short printable bridges."""
    if height < width:
        raise ValueError("Rear panel obround height must be >= width")
    straight_h = height - width
    x, y, z = center
    with BuildPart() as cutout:
        add(
            Location((x, y, z - straight_h / 2))
            * _oriented_cylinder(
                diameter=width,
                depth=depth,
                axis="y",
                center=(0, 0, 0),
            )
        )
        add(
            Location((x, y, z + straight_h / 2))
            * _oriented_cylinder(
                diameter=width,
                depth=depth,
                axis="y",
                center=(0, 0, 0),
            )
        )
        if straight_h > 0:
            add(
                Location((x, y, z))
                * Box(
                    width,
                    depth,
                    straight_h,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    mode=Mode.PRIVATE,
                )
            )
    return cutout.part.clean().fix()


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _main_box_height(variant: LayoutVariant) -> float:
    if variant.top_mic is None:
        return variant.outer_size[2]
    return variant.outer_size[2] - variant.top_mic.outer_h


def _rect_post(
    *,
    x: float,
    y: float,
    z: float,
    od: float,
    h: float,
    bore_d: float,
) -> Part:
    post = Cylinder(
        radius=od / 2,
        height=h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    bore = Pos(0, 0, -0.2) * Cylinder(
        radius=bore_d / 2,
        height=h + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    return Location((x, y, z)) * (post - bore).clean().fix()


def _peg(
    *,
    x: float,
    y: float,
    z: float,
    od: float,
    h: float,
) -> Part:
    return Location((x, y, z)) * Cylinder(
        radius=od / 2,
        height=h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )


def _board_placeholder(spec: BoardSpec, placement: Placement, floor_z: float) -> Part:
    if placement.orientation == "floor":
        bottom_z = floor_z + spec.post_h + placement.z
        if spec.name == "amp":
            return _amp_clearance_placeholder(spec, placement, bottom_z)
        return Location((placement.x, placement.y, bottom_z)) * Box(
            spec.size_x,
            spec.size_y,
            spec.size_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )

    if placement.orientation == "amp_envelope":
        bottom_z = floor_z + placement.z + spec.post_h
        return Location((placement.x, placement.y, bottom_z)) * Box(
            spec.size_x,
            spec.size_y,
            spec.size_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )

    if spec.name != "buck":
        raise ValueError("Only the buck converter currently has a vertical layout")

    if placement.orientation == "rear_wall":
        return Location((placement.x, placement.y, placement.z)) * Box(
            spec.size_x,
            BUCK_REAR_MOUNT_BODY_DEPTH,
            BUCK_REAR_MOUNT_BODY_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )

    return Location((placement.x, placement.y, floor_z + placement.z)) * Box(
        spec.size_x,
        spec.size_z,
        spec.size_y,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )


def _board_clearance_size(
    spec: BoardSpec,
    placement: Placement,
) -> list[float]:
    if spec.name == "buck" and placement.orientation == "rear_wall":
        return [
            spec.size_x,
            BUCK_REAR_MOUNT_BODY_DEPTH,
            BUCK_REAR_MOUNT_BODY_H,
        ]
    return [spec.size_x, spec.size_y, spec.size_z]


def _amp_clearance_placeholder(
    spec: BoardSpec,
    placement: Placement,
    bottom_z: float,
) -> Part:
    board_t = 5.0
    heatsink_w = 23.0
    heatsink_d = spec.size_y
    heatsink_h = min(spec.size_z - board_t, 34.0 - board_t)
    output_side_to_heatsink = 38.0
    heatsink_x = (
        placement.x
        - spec.size_x / 2
        + output_side_to_heatsink
        + heatsink_w / 2
    )
    heatsink_y = placement.y
    with BuildPart() as amp:
        add(
            Location((placement.x, placement.y, bottom_z))
            * Box(
                spec.size_x,
                spec.size_y,
                board_t,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
        add(
            Location((heatsink_x, heatsink_y, bottom_z + board_t))
            * Box(
                heatsink_w,
                heatsink_d,
                heatsink_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
    return amp.part.clean().fix()


def _disk_placeholder(
    spec: DiskSpec,
    placement: Placement,
    floor_z: float,
) -> Part:
    if placement.orientation == "floor":
        return Location((placement.x, placement.y, floor_z)) * Cylinder(
            radius=spec.diameter / 2,
            height=spec.thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )

    if placement.orientation == "top_compartment":
        return Location((placement.x, placement.y, placement.z)) * Cylinder(
            radius=spec.diameter / 2,
            height=spec.thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )

    if placement.orientation == "front_wall":
        return _oriented_cylinder(
            diameter=spec.diameter,
            depth=spec.thickness,
            axis="y",
            center=(placement.x, placement.y, placement.z),
        )

    raise ValueError(f"Unsupported disk orientation: {placement.orientation}")


def _vent_cutouts(
    *,
    width: float,
    depth: float,
    height: float,
    config: PrintedConfig,
    keepouts: tuple[tuple[float, float, float], ...] = (),
) -> tuple[Part, int]:
    x_min = -width / 2 + config.vent_edge_margin
    x_max = width / 2 - config.vent_edge_margin
    y_min = -depth / 2 + config.vent_edge_margin
    y_max = depth / 2 - config.vent_edge_margin
    holes: list[Part] = []
    row = 0
    y = y_min
    while y <= y_max + 0.001:
        offset = (config.vent_pitch / 2) if row % 2 else 0.0
        x = x_min + offset
        while x <= x_max + 0.001:
            in_keepout = any(
                (x - cx) ** 2 + (y - cy) ** 2
                < (radius + config.vent_d / 2 + 2.0) ** 2
                for cx, cy, radius in keepouts
            )
            if not in_keepout:
                holes.append(
                    Location((x, y, height - config.roof_t - 0.2))
                    * Cylinder(
                        radius=config.vent_d / 2,
                        height=config.roof_t + 0.4,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.PRIVATE,
                    )
                )
            x += config.vent_pitch
        row += 1
        y += config.vent_pitch
    with BuildPart() as cutouts:
        for hole in holes:
            add(hole)
    return cutouts.part, len(holes)


def _open_back_shell(variant: LayoutVariant, config: PrintedConfig) -> tuple[Part, int]:
    width, depth, _overall_height = variant.outer_size
    height = _main_box_height(variant)
    keepouts = ()
    if variant.top_mic is not None:
        keepouts = (
            (
                variant.top_mic.center_x,
                variant.top_mic.center_y,
                variant.top_mic.outer_d / 2,
            ),
        )
    outer = Box(
        width,
        depth,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    inner_h = height - config.floor_t - config.roof_t
    inner_cut_y_min = -depth / 2 + config.front_wall_t
    inner_cut_y_max = depth / 2 + 2.0
    inner = Location(
        (
            0,
            (inner_cut_y_min + inner_cut_y_max) / 2,
            config.floor_t,
        )
    ) * Box(
        width - 2 * config.wall_t,
        inner_cut_y_max - inner_cut_y_min,
        inner_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    vents, vent_count = _vent_cutouts(
        width=width,
        depth=depth,
        height=height,
        config=config,
        keepouts=keepouts,
    )
    return (outer - inner - vents).clean().fix(), vent_count


def _top_mic_compartment_parts(
    variant: LayoutVariant,
    config: PrintedConfig,
) -> tuple[list[Part], list[Part]]:
    if variant.top_mic is None:
        return [], []

    top_mic = variant.top_mic
    base_h = _main_box_height(variant)
    outer = Location((top_mic.center_x, top_mic.center_y, base_h)) * Cylinder(
        radius=top_mic.outer_d / 2,
        height=top_mic.outer_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    inner = Location(
        (
            top_mic.center_x,
            top_mic.center_y,
            base_h + top_mic.floor_t,
        )
    ) * Cylinder(
        radius=top_mic.inner_d / 2,
        height=top_mic.outer_h - top_mic.floor_t + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    cable_pass = Location(
        (
            top_mic.center_x,
            top_mic.center_y,
            base_h - config.roof_t - 0.3,
        )
    ) * Cylinder(
        radius=top_mic.cable_pass_d / 2,
        height=config.roof_t + top_mic.floor_t + 0.6,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    return [(outer - inner).clean().fix()], [cable_pass]


def _wall_mount_cutouts(variant: LayoutVariant) -> list[Part]:
    if not variant.wall_mount:
        return []

    width, depth, _overall_height = variant.outer_size
    height = _main_box_height(variant)
    inset = 14.0
    hole_d = 6.4
    return [
        Location((x, y, -0.2))
        * Cylinder(
            radius=hole_d / 2,
            height=height + 0.4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )
        for x in (-width / 2 + inset, width / 2 - inset)
        for y in (-depth / 2 + inset, depth / 2 - inset)
    ]


def _rear_panel_cutouts(
    variant: LayoutVariant,
    config: PrintedConfig,
    *,
    base_h: float,
) -> tuple[list[Part], dict[str, object]]:
    width, depth, _height = variant.outer_size
    _ = width
    rear_y = depth / 2
    pi = next(
        (placement for placement in variant.placements if placement.spec == "pi_hat"),
        None,
    )
    cutouts: list[Part] = []
    notes: dict[str, object] = {}

    if pi is not None:
        pi_cutouts, pi_notes = _pi_rear_port_bay_cutouts(
            pi=pi,
            rear_y=rear_y,
            config=config,
        )
        cutouts.extend(pi_cutouts)
        power_cutout, power_note = _pi_power_input_cutout(
            pi=pi,
            rear_y=rear_y,
            config=config,
        )
        cutouts.append(power_cutout)
        pi_notes["power_input_hole"] = power_note
        notes["pi_rear_io_window"] = pi_notes

    buck = next(
        (
            placement
            for placement in variant.placements
            if placement.spec == "buck" and placement.orientation == "rear_wall"
        ),
        None,
    )
    gx14_centers, gx14_spacing_notes = _gx14_center_positions(
        variant=variant,
        config=config,
        buck=buck,
    )
    for x, z in gx14_centers:
        cutouts.append(
            _rear_panel_obround_cutout(
                width=GX14_HOLE_W,
                height=GX14_HOLE_H,
                depth=config.wall_t + 1.0,
                center=(x, rear_y - config.wall_t / 2, z),
            )
        )
        cutouts.append(
            _rear_panel_obround_cutout(
                width=GX14_RECESS_W,
                height=GX14_RECESS_H,
                depth=GX14_RECESS_DEPTH + 0.2,
                center=(x, rear_y - GX14_RECESS_DEPTH / 2, z),
            )
        )
    notes["gx14_outputs"] = {
        "count": 2,
        "connector": "GX14-4 assumed",
        "center_xz_mm": [[x, z] for x, z in gx14_centers],
        "through_hole_size_xz_mm": [GX14_HOLE_W, GX14_HOLE_H],
        "measured_collar_od_mm": GX14_COLLAR_OD,
        "flange_recess_size_xz_mm": [GX14_RECESS_W, GX14_RECESS_H],
        "flange_recess_depth_mm": GX14_RECESS_DEPTH,
        "spacing": gx14_spacing_notes,
        "assumption": (
            "Two 4-pin aviation-style outputs for four amp channels total. "
            "Rear-wall FDM holes are intentionally relieved vertically because "
            "printed circular holes can come out slightly undersized/oval. "
            "Centers are tight and biased toward the rear-view left edge to "
            "clear the amp heat sink on the inside."
        ),
    }

    if buck is not None:
        buck_notch = _rear_bottom_wire_slot(
            center_x=buck.x,
            rear_y=rear_y,
            wall_t=config.wall_t,
        )
        cutouts.append(buck_notch)
        notes["buck_bottom_wire_entry"] = {
            "center_x_mm": round(buck.x, 3),
            "width_mm": BUCK_REAR_WIRE_NOTCH_W,
            "slot_height_mm": BUCK_REAR_WIRE_SLOT_H,
            "through_depth_mm": config.wall_t + BUCK_REAR_WIRE_SLOT_EXTRA_DEPTH,
            "internal_chamfer_mm": [
                BUCK_REAR_WIRE_CHAMFER_DEPTH,
                BUCK_REAR_WIRE_CHAMFER_H,
            ],
            "assumption": (
                "Rear-mounted buck converter wires bend down 90 degrees and enter "
                "through this full-depth rear-wall bottom slot."
            ),
        }
    notes["rear_panel_h_mm"] = base_h
    return cutouts, notes


def _gx14_center_positions(
    *,
    variant: LayoutVariant,
    config: PrintedConfig,
    buck: Placement | None,
) -> tuple[tuple[tuple[float, float], tuple[float, float]], dict[str, object]]:
    """Pack the two GX14 recesses between the buck body and rear-view left wall."""
    width, _depth, _height = variant.outer_size
    inner_side_x = width / 2 - config.wall_t
    if buck is None:
        buck_edge_x = 39.0
    else:
        buck_edge_x = buck.x + BUCK.size_x / 2

    usable_w = inner_side_x - buck_edge_x
    equal_gap = max(0.0, (usable_w - 2 * GX14_RECESS_W) / 3)
    near_buck_x = buck_edge_x + equal_gap + GX14_RECESS_W / 2
    near_wall_x = near_buck_x + GX14_RECESS_W + equal_gap
    centers = (
        (round(near_wall_x, 3), GX14_CENTER_Z),
        (round(near_buck_x, 3), GX14_CENTER_Z),
    )
    notes = {
        "strategy": (
            "Centers are equally packed between the rear-mounted buck body and "
            "the rear-view left inner sidewall using the collar recess size."
        ),
        "buck_edge_x_mm": round(buck_edge_x, 3),
        "inner_sidewall_x_mm": round(inner_side_x, 3),
        "usable_lane_w_mm": round(usable_w, 3),
        "equal_gap_mm": round(equal_gap, 3),
        "center_spacing_mm": round(abs(centers[0][0] - centers[1][0]), 3),
    }
    return centers, notes


def _rear_bottom_wire_slot(*, center_x: float, rear_y: float, wall_t: float) -> Part:
    """Rectangular rear-wall through-slot for buck wiring at the bottom edge."""
    slot_depth = wall_t + BUCK_REAR_WIRE_SLOT_EXTRA_DEPTH
    slot = Location(
        (center_x, rear_y - wall_t / 2, BUCK_REAR_WIRE_SLOT_H / 2)
    ) * Box(
        BUCK_REAR_WIRE_NOTCH_W,
        slot_depth,
        BUCK_REAR_WIRE_SLOT_H,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    chamfer = _rear_bottom_wire_slot_chamfer(
        center_x=center_x,
        rear_y=rear_y,
        wall_t=wall_t,
    )
    with BuildPart() as wire_slot:
        add(slot)
        add(chamfer)
    return wire_slot.part.clean().fix()


def _rear_bottom_wire_slot_chamfer(
    *,
    center_x: float,
    rear_y: float,
    wall_t: float,
) -> Part:
    """45 degree-ish relief at the internal top edge of the buck wire slot."""
    inside_y = rear_y - wall_t
    chamfer_w = BUCK_REAR_WIRE_NOTCH_W + 1.0
    with BuildPart() as chamfer:
        with BuildSketch(Plane.YZ):
            with BuildLine():
                Polyline(
                    (inside_y, BUCK_REAR_WIRE_SLOT_H),
                    (inside_y, BUCK_REAR_WIRE_SLOT_H + BUCK_REAR_WIRE_CHAMFER_H),
                    (
                        inside_y + BUCK_REAR_WIRE_CHAMFER_DEPTH,
                        BUCK_REAR_WIRE_SLOT_H,
                    ),
                    (inside_y, BUCK_REAR_WIRE_SLOT_H),
                )
            make_face()
        extrude(amount=chamfer_w)
    return Pos(center_x - chamfer_w / 2, 0, 0) * chamfer.part.clean().fix()


def _pi_rear_port_bay_cutouts(
    *,
    pi: Placement,
    rear_y: float,
    config: PrintedConfig,
) -> tuple[list[Part], dict[str, object]]:
    """Three smaller Pi 5 rear port openings instead of one long bridge."""
    center_z = (
        config.floor_t
        + PI_HAT.post_h
        + PI5_REAR_PORT_WINDOW_CENTER_Z_FROM_BOARD_BOTTOM
    )
    cutouts: list[Part] = []
    bays: list[dict[str, object]] = []
    for name, edge_center_from_bottom, bay_w in PI5_REAR_PORT_BAYS:
        x_offset = PI5_PORT_EDGE_MIDLINE_FROM_BOTTOM - edge_center_from_bottom
        center_x = pi.x + x_offset
        cutouts.append(
            Location((center_x, rear_y - config.wall_t / 2, center_z))
            * Box(
                bay_w,
                config.wall_t + 1.0,
                PI5_REAR_PORT_WINDOW_H,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.PRIVATE,
            )
        )
        bays.append(
            {
                "name": name,
                "center_xyz_mm": [
                    round(center_x, 3),
                    round(rear_y, 3),
                    round(center_z, 3),
                ],
                "size_xyz_mm": [
                    bay_w,
                    config.wall_t + 1.0,
                    PI5_REAR_PORT_WINDOW_H,
                ],
                "pi5_port_edge_center_from_bottom_mm": edge_center_from_bottom,
            }
        )

    gaps: list[float] = []
    for left, right in zip(bays, bays[1:]):
        left_x = left["center_xyz_mm"][0]
        right_x = right["center_xyz_mm"][0]
        left_w = left["size_xyz_mm"][0]
        right_w = right["size_xyz_mm"][0]
        gaps.append(round(abs(right_x - left_x) - (left_w + right_w) / 2, 3))

    notes = {
        "style": "three Pi 5 port bays with print-supporting vertical piers",
        "bays": bays,
        "bay_gap_mm": gaps,
        "source_mapping": (
            "Uses Raspberry Pi 5 mechanical drawing port-edge callouts at "
            "47.0, 29.1, and 10.2 mm from the port-edge bottom, with the Pi "
            "openings kept on the rear-view right side."
        ),
        "height_basis": (
            "The official Raspberry Pi 5 drawing does not directly dimension the "
            "USB-A stack face height, but the scaled side elevation keeps the "
            "rear connector bodies around a 16 mm vertical envelope. The current "
            "25 mm window drops the lower edge 5 mm from the earlier tight bay "
            "for removable-foot fit testing."
        ),
        "assumption": (
            "Fit-study bay openings for USB/Ethernet access with the Pi port edge "
            "facing the rear panel. Validate with the real Pi/HAT stack and cable "
            "moldings before a production print."
        ),
    }
    return cutouts, notes


def _pi_power_input_cutout(
    *,
    pi: Placement,
    rear_y: float,
    config: PrintedConfig,
) -> tuple[Part, dict[str, object]]:
    """Circular rear-panel power input hole centered over the Pi port group."""
    bay_edges: list[tuple[float, float]] = []
    for _name, edge_center_from_bottom, bay_w in PI5_REAR_PORT_BAYS:
        x_offset = PI5_PORT_EDGE_MIDLINE_FROM_BOTTOM - edge_center_from_bottom
        center_x = pi.x + x_offset
        bay_edges.append((center_x - bay_w / 2, center_x + bay_w / 2))
    min_x = min(edge[0] for edge in bay_edges)
    max_x = max(edge[1] for edge in bay_edges)
    center_x = (min_x + max_x) / 2
    center = (
        center_x,
        rear_y - config.wall_t / 2,
        PI_POWER_INPUT_CENTER_Z,
    )
    cutout = _rear_panel_obround_cutout(
        width=PI_POWER_INPUT_HOLE_W,
        height=PI_POWER_INPUT_HOLE_H,
        depth=config.wall_t + 1.0,
        center=center,
    )
    note = {
        "nominal_diameter_mm": PI_POWER_INPUT_HOLE_W,
        "through_hole_size_xz_mm": [PI_POWER_INPUT_HOLE_W, PI_POWER_INPUT_HOLE_H],
        "center_xyz_mm": [round(value, 3) for value in center],
        "basis": (
            "Centered over the combined Pi USB/Ethernet rear cutout group, with "
            "vertical relief for FDM hole ovaling."
        ),
    }
    return cutout, note


def _thin_plate_auxiliary_vent_cutouts(
    variant: LayoutVariant,
    config: PrintedConfig,
    *,
    base_h: float,
) -> tuple[list[Part], dict[str, object]]:
    """Fast rectangular airflow slots on the front, side, and bottom faces."""
    width, depth, _total_h = variant.outer_size
    front_y = -depth / 2
    side_x_abs = width / 2
    z_centers = tuple(
        z for z in WALL_VENT_Z_CENTERS if z - WALL_VENT_SLOT_H / 2 > config.floor_t
    )

    front_slots: list[Part] = []
    x = -width / 2 + WALL_VENT_MARGIN + WALL_VENT_SLOT_LEN / 2
    while x <= width / 2 - WALL_VENT_MARGIN - WALL_VENT_SLOT_LEN / 2 + 0.001:
        for z in z_centers:
            front_slots.append(
                Location((x, front_y + config.wall_t / 2, z))
                * Box(
                    WALL_VENT_SLOT_LEN,
                    config.wall_t + 0.8,
                    WALL_VENT_SLOT_H,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    mode=Mode.PRIVATE,
                )
            )
        x += WALL_VENT_SLOT_LEN + 12.0

    side_slots: list[Part] = []
    y = -depth / 2 + WALL_VENT_MARGIN + WALL_VENT_SLOT_LEN / 2
    while y <= depth / 2 - WALL_VENT_MARGIN - WALL_VENT_SLOT_LEN / 2 + 0.001:
        for sx in (-side_x_abs, side_x_abs):
            for z in z_centers:
                side_slots.append(
                    Location((sx - (config.wall_t / 2 if sx > 0 else -config.wall_t / 2), y, z))
                    * Box(
                        config.wall_t + 0.8,
                        WALL_VENT_SLOT_LEN,
                        WALL_VENT_SLOT_H,
                        align=(Align.CENTER, Align.CENTER, Align.CENTER),
                        mode=Mode.PRIVATE,
                    )
                )
        y += WALL_VENT_SLOT_LEN + 10.0

    standoff_keepouts = _thin_plate_floor_standoff_keepouts(variant)
    bottom_slots: list[Part] = []
    y = -depth / 2 + BOTTOM_VENT_MARGIN + BOTTOM_VENT_SLOT_Y / 2
    while y <= depth / 2 - BOTTOM_VENT_MARGIN - BOTTOM_VENT_SLOT_Y / 2 + 0.001:
        x = -width / 2 + BOTTOM_VENT_MARGIN + BOTTOM_VENT_SLOT_X / 2
        while x <= width / 2 - BOTTOM_VENT_MARGIN - BOTTOM_VENT_SLOT_X / 2 + 0.001:
            if not _slot_intersects_keepout(
                slot_center=(x, y),
                slot_size=(BOTTOM_VENT_SLOT_X, BOTTOM_VENT_SLOT_Y),
                keepouts=standoff_keepouts,
                clearance=BOTTOM_VENT_STANDOFF_CLEARANCE,
            ):
                bottom_slots.append(
                    Location((x, y, config.floor_t / 2))
                    * Box(
                        BOTTOM_VENT_SLOT_X,
                        BOTTOM_VENT_SLOT_Y,
                        config.floor_t + 0.8,
                        align=(Align.CENTER, Align.CENTER, Align.CENTER),
                        mode=Mode.PRIVATE,
                    )
                )
            x += BOTTOM_VENT_SLOT_X + 14.0
        y += BOTTOM_VENT_SLOT_Y + 18.0

    notes = {
        "style": "rectangular fast-print airflow slots",
        "front_slot_count": len(front_slots),
        "side_slot_count": len(side_slots),
        "bottom_slot_count": len(bottom_slots),
        "front_side_slot_size_mm": [WALL_VENT_SLOT_LEN, WALL_VENT_SLOT_H],
        "bottom_slot_size_mm": [BOTTOM_VENT_SLOT_X, BOTTOM_VENT_SLOT_Y],
        "bottom_standoff_keepout_clearance_mm": BOTTOM_VENT_STANDOFF_CLEARANCE,
        "note": (
            "Bottom slots are skipped around floor-mounted amp/Pi standoffs so "
            "the posts still land on solid plastic."
        ),
    }
    return [*front_slots, *side_slots, *bottom_slots], notes


def _thin_plate_floor_standoff_keepouts(
    variant: LayoutVariant,
) -> tuple[tuple[float, float, float], ...]:
    keepouts: list[tuple[float, float, float]] = []
    for placement in variant.placements:
        if placement.orientation != "floor" or placement.spec not in BOARD_SPECS:
            continue
        if placement.spec == "pi_hat":
            for dx, dy in PI_HAT.mount_points:
                keepouts.append(
                    (
                        placement.x + dx,
                        placement.y + dy,
                        PI_ADJUST_SLOT_LEN / 2 + PI_ADJUST_SLOT_KEEPAWAY,
                    )
                )
            continue
        spec = BOARD_SPECS[placement.spec]
        for dx, dy in spec.mount_points:
            keepouts.append((placement.x + dx, placement.y + dy, spec.post_od / 2))
    return tuple(keepouts)


def _slot_intersects_keepout(
    *,
    slot_center: tuple[float, float],
    slot_size: tuple[float, float],
    keepouts: tuple[tuple[float, float, float], ...],
    clearance: float,
) -> bool:
    sx, sy = slot_center
    slot_w, slot_d = slot_size
    for kx, ky, radius in keepouts:
        if (
            abs(kx - sx) <= slot_w / 2 + radius + clearance
            and abs(ky - sy) <= slot_d / 2 + radius + clearance
        ):
            return True
    return False


def _pi_floor_adjustment_slot_cutouts(
    variant: LayoutVariant,
    config: PrintedConfig,
) -> tuple[list[Part], dict[str, object] | None]:
    pi = next(
        (placement for placement in variant.placements if placement.spec == "pi_hat"),
        None,
    )
    if pi is None:
        return [], None
    cutouts = [
        _floor_obround_slot(
            center=(
                pi.x + dx,
                pi.y + dy,
                config.floor_t / 2,
            ),
            slot_w=PI_ADJUST_SLOT_W,
            slot_len=PI_ADJUST_SLOT_LEN,
            depth=config.floor_t + 0.8,
        )
        for dx, dy in PI_HAT.mount_points
    ]
    notes = {
        "count": len(cutouts),
        "slot_size_xy_mm": [PI_ADJUST_SLOT_W, PI_ADJUST_SLOT_LEN],
        "positions_xy_mm": [
            [round(pi.x + dx, 3), round(pi.y + dy, 3)]
            for dx, dy in PI_HAT.mount_points
        ],
        "purpose": (
            "Through-floor screw slots for separate/removable Pi feet. Slots run "
            "front-to-back so the Pi port face can slide into the rear USB/Ethernet "
            "cutouts during fit tuning."
        ),
    }
    return cutouts, notes


def _floor_obround_slot(
    *,
    center: tuple[float, float, float],
    slot_w: float,
    slot_len: float,
    depth: float,
) -> Part:
    x, y, z = center
    straight_len = max(0.0, slot_len - slot_w)
    with BuildPart() as slot:
        add(
            Location((x, y - straight_len / 2, z))
            * Cylinder(
                radius=slot_w / 2,
                height=depth,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.PRIVATE,
            )
        )
        add(
            Location((x, y + straight_len / 2, z))
            * Cylinder(
                radius=slot_w / 2,
                height=depth,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.PRIVATE,
            )
        )
        if straight_len > 0:
            add(
                Location((x, y, z))
                * Box(
                    slot_w,
                    straight_len,
                    depth,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    mode=Mode.PRIVATE,
                )
            )
    return slot.part.clean().fix()


def _lid_screw_positions(variant: LayoutVariant) -> tuple[tuple[float, float], ...]:
    width, depth, _height = variant.outer_size
    inset = 5.0
    return tuple(
        (x, y)
        for x in (-width / 2 + inset, width / 2 - inset)
        for y in (-depth / 2 + inset, depth / 2 - inset)
    )


def _lid_screw_bosses(
    variant: LayoutVariant,
    *,
    base_h: float,
) -> tuple[list[Part], dict[str, object]]:
    bosses = [
        _corner_lid_receiver(
            x=x,
            y=y,
            base_h=base_h,
            od=LID_RECEIVER_OD,
            engagement_h=LID_RECEIVER_ENGAGEMENT_H,
            taper_h=LID_RECEIVER_TAPER_H,
        )
        for x, y in _lid_screw_positions(variant)
    ]
    notes = {
        "count": len(bosses),
        "boss_od_mm": LID_RECEIVER_OD,
        "screw_engagement_h_mm": LID_RECEIVER_ENGAGEMENT_H,
        "wall_grown_ramp_h_mm": LID_RECEIVER_TAPER_H,
        "receiver_start_z_mm": base_h
        - LID_RECEIVER_ENGAGEMENT_H
        - LID_RECEIVER_TAPER_H,
        "pilot_start_z_mm": base_h - LID_RECEIVER_ENGAGEMENT_H,
        "self_tap_pilot_d_mm": LID_RECEIVER_PILOT_D,
        "positions_xy_mm": [
            [round(x, 3), round(y, 3)] for x, y in _lid_screw_positions(variant)
        ],
    }
    return bosses, notes


def _corner_lid_receiver(
    *,
    x: float,
    y: float,
    base_h: float,
    od: float,
    engagement_h: float,
    taper_h: float,
) -> Part:
    top_z = base_h - engagement_h
    root_z = top_z - taper_h
    sx = 1 if x >= 0 else -1
    sy = 1 if y >= 0 else -1
    wall_t = DEFAULT_CONFIG.wall_t
    top_r = od / 2
    root_r = 2.1
    mid_r = 3.5
    root_x = x + sx * (top_r - wall_t)
    root_y = y + sy * (top_r - wall_t)
    mid_x = (root_x + x) / 2
    mid_y = (root_y + y) / 2

    with BuildPart() as receiver:
        with BuildSketch(Plane.XY.offset(root_z)):
            add(Pos(root_x, root_y) * Circle(root_r, mode=Mode.PRIVATE))
        with BuildSketch(Plane.XY.offset(root_z + taper_h * 0.55)):
            add(Pos(mid_x, mid_y) * Circle(mid_r, mode=Mode.PRIVATE))
        with BuildSketch(Plane.XY.offset(top_z)):
            add(Pos(x, y) * Circle(top_r, mode=Mode.PRIVATE))
        loft()
        add(
            Location((x, y, top_z))
            * Cylinder(
                radius=top_r,
                height=engagement_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
    return receiver.part.clean().fix()


def _lid_screw_pilot_cutouts(
    variant: LayoutVariant,
    *,
    base_h: float,
) -> list[Part]:
    start_z = base_h - LID_RECEIVER_ENGAGEMENT_H
    return [
        Location((x, y, start_z - 0.2))
        * Cylinder(
            radius=LID_RECEIVER_PILOT_D / 2,
            height=LID_RECEIVER_ENGAGEMENT_H + 0.4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )
        for x, y in _lid_screw_positions(variant)
    ]


def _build_thin_plate_base(
    variant: LayoutVariant,
    config: PrintedConfig,
) -> tuple[Part, dict[str, object]]:
    width, depth, total_h = variant.outer_size
    lid_t = config.roof_t
    base_h = total_h - lid_t
    outer = Box(
        width,
        depth,
        base_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    inner = Pos(0, 0, config.floor_t) * Box(
        width - 2 * config.wall_t,
        depth - 2 * config.wall_t,
        base_h - config.floor_t + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    rear_cutouts, rear_notes = _rear_panel_cutouts(
        variant,
        config,
        base_h=base_h,
    )
    auxiliary_vents, auxiliary_vent_notes = _thin_plate_auxiliary_vent_cutouts(
        variant,
        config,
        base_h=base_h,
    )
    pi_slots, pi_slot_notes = _pi_floor_adjustment_slot_cutouts(variant, config)
    with BuildPart() as cuts:
        add(inner)
        for cutout in rear_cutouts:
            add(cutout)
        for cutout in auxiliary_vents:
            add(cutout)
        for cutout in pi_slots:
            add(cutout)
    base = (outer - cuts.part).clean().fix()
    bosses, screw_notes = _lid_screw_bosses(variant, base_h=base_h)
    with BuildPart() as detailed_base:
        add(base)
        for boss in bosses:
            add(boss)
    base = detailed_base.part.clean().fix()
    pilot_cutouts = _lid_screw_pilot_cutouts(variant, base_h=base_h)
    with BuildPart() as lid_screw_cuts:
        for cutout in pilot_cutouts:
            add(cutout)
    base = (base - lid_screw_cuts.part).clean().fix()
    notes = {
        "base_h_mm": base_h,
        "rear_panel": rear_notes,
        "auxiliary_vents": auxiliary_vent_notes,
        "pi_adjustment_slots": pi_slot_notes,
        "lid_screw_bosses": screw_notes,
    }
    return base, notes


def _build_thin_plate_lid(
    variant: LayoutVariant,
    config: PrintedConfig,
) -> tuple[Part, dict[str, object]]:
    width, depth, total_h = variant.outer_size
    lid_t = config.roof_t
    base_h = total_h - lid_t
    slab = Location((0, 0, base_h)) * Box(
        width,
        depth,
        lid_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    vents, vent_count = _vent_cutouts(
        width=width,
        depth=depth,
        height=total_h,
        config=config,
    )
    through_d = 3.3
    head_recess_d = 7.2
    head_recess_depth = 1.6
    with BuildPart() as cutouts:
        add(vents)
        for x, y in _lid_screw_positions(variant):
            add(
                Location((x, y, base_h - 0.2))
                * Cylinder(
                    radius=through_d / 2,
                    height=lid_t + 0.4,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            )
            add(
                Location((x, y, total_h - head_recess_depth))
                * Cylinder(
                    radius=head_recess_d / 2,
                    height=head_recess_depth + 0.2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            )
    lid = (slab - cutouts.part).clean().fix()
    notes = {
        "lid_t_mm": lid_t,
        "vent_hole_count": vent_count,
        "cheese_head_screw_clearance": {
            "through_d_mm": through_d,
            "head_recess_d_mm": head_recess_d,
            "head_recess_depth_mm": head_recess_depth,
            "positions_xy_mm": [
                [round(x, 3), round(y, 3)] for x, y in _lid_screw_positions(variant)
            ],
        },
    }
    return lid, notes


def build_thin_plate_printed_parts(
    variant: LayoutVariant,
    config: PrintedConfig = DEFAULT_CONFIG,
) -> tuple[Part, Part, Compound, dict[str, object]]:
    """Build the focused thin plate as separate base and screw-on lid."""
    base, base_notes = _build_thin_plate_base(variant, config)
    lid, lid_notes = _build_thin_plate_lid(variant, config)
    features = _component_mount_features(variant, config)
    with BuildPart() as detailed_base:
        add(base)
        for feature in features:
            add(feature)
    base = detailed_base.part.clean().fix()
    assembly = Compound(children=[base, lid])
    notes = {
        "base": base_notes,
        "lid": lid_notes,
        "component_standoffs": {
            "purpose": "Self-tapping screw pilot pegs that lift boards for airflow.",
            "count": len(features),
            "rear_buck_pin": {
                "diameter_mm": BUCK_REAR_PIN_D,
                "depth_mm": BUCK_REAR_PIN_DEPTH,
                "center_z_from_buck_bottom_mm": BUCK_REAR_PIN_CENTER_Z_FROM_BOTTOM,
            },
        },
        "printed_bounding_box": _bbox(assembly),
    }
    return base, lid, assembly, notes


def _component_mount_features(
    variant: LayoutVariant,
    config: PrintedConfig,
) -> list[Part]:
    floor_z = config.floor_t
    features: list[Part] = []
    for placement in variant.placements:
        if placement.spec not in BOARD_SPECS:
            continue
        if placement.spec == "pi_hat":
            continue
        spec = BOARD_SPECS[placement.spec]
        if placement.orientation == "floor":
            features.extend(
                _horizontal_mounts(
                    spec=spec,
                    placement=placement,
                    floor_z=floor_z + placement.z,
                )
            )
        elif placement.spec == "buck" and placement.orientation == "rear_wall":
            features.extend(
                _vertical_buck_mount(
                    placement=placement,
                    config=config,
                    floor_z=floor_z,
                )
            )
        elif placement.spec == "buck" and placement.orientation == "amp_envelope":
            features.extend(
                _raised_buck_mount(
                    placement=placement,
                    floor_z=floor_z,
                )
            )
    return features


def _horizontal_mounts(
    *,
    spec: BoardSpec,
    placement: Placement,
    floor_z: float,
) -> list[Part]:
    features: list[Part] = []
    for dx, dy in spec.mount_points:
        x = placement.x + dx
        y = placement.y + dy
        if spec.name == "buck":
            features.append(
                _peg(
                    x=x,
                    y=y,
                    z=floor_z,
                    od=max(4.8, spec.mount_hole_d - 0.5),
                    h=spec.post_h,
                )
            )
        else:
            features.append(
                _rect_post(
                    x=x,
                    y=y,
                    z=floor_z,
                    od=spec.post_od,
                    h=spec.post_h,
                    bore_d=spec.bore_d,
                )
            )
    return features


def _vertical_buck_mount(
    *,
    placement: Placement,
    config: PrintedConfig,
    floor_z: float,
) -> list[Part]:
    _ = floor_z
    spec = BUCK
    _ = config
    rear_face_y = placement.y - BUCK_REAR_MOUNT_BODY_DEPTH / 2
    pin_depth = BUCK_REAR_PIN_DEPTH
    pin_center_y = rear_face_y + pin_depth / 2
    pin_center_z = placement.z + BUCK_REAR_PIN_CENTER_Z_FROM_BOTTOM
    pins = [
        _oriented_cylinder(
            diameter=BUCK_REAR_PIN_D,
            depth=pin_depth,
            axis="y",
            center=(
                placement.x + dx,
                pin_center_y,
                pin_center_z,
            ),
        )
        for dx, _dy in spec.mount_points
    ]
    return pins


def _raised_buck_mount(
    *,
    placement: Placement,
    floor_z: float,
) -> list[Part]:
    spec = BUCK
    shelf_t = 3.0
    shelf_z = floor_z + placement.z
    shelf_w = spec.size_x + 10.0
    shelf_d = spec.size_y + 10.0
    shelf = Location((placement.x, placement.y, shelf_z)) * Box(
        shelf_w,
        shelf_d,
        shelf_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    leg_od = 6.0
    leg_inset = 6.0
    legs = [
        Location((placement.x + x, placement.y + y, floor_z))
        * Cylinder(
            radius=leg_od / 2,
            height=placement.z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )
        for x in (-shelf_w / 2 + leg_inset, shelf_w / 2 - leg_inset)
        for y in (-shelf_d / 2 + leg_inset, shelf_d / 2 - leg_inset)
    ]
    pegs = [
        _peg(
            x=placement.x + dx,
            y=placement.y + dy,
            z=shelf_z + shelf_t,
            od=max(4.8, spec.mount_hole_d - 0.5),
            h=spec.post_h,
        )
        for dx, dy in spec.mount_points
    ]
    return [shelf, *legs, *pegs]


def _shelf_features(
    variant: LayoutVariant,
    config: PrintedConfig,
    floor_z: float,
) -> list[Part]:
    if variant.shelf is None:
        return []

    shelf_w, shelf_d, shelf_z, shelf_y = variant.shelf
    shelf = Location((0, shelf_y, floor_z + shelf_z)) * Box(
        shelf_w,
        shelf_d,
        config.shelf_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    support_h = shelf_z
    supports = [
        Location((x, y, floor_z))
        * Cylinder(
            radius=config.shelf_support_d / 2,
            height=support_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.PRIVATE,
        )
        for x in (-shelf_w / 2 + 8.0, shelf_w / 2 - 8.0)
        for y in (shelf_y - shelf_d / 2 + 8.0, shelf_y + shelf_d / 2 - 8.0)
    ]
    return [shelf, *supports]


def build_printed_enclosure(
    variant: LayoutVariant,
    config: PrintedConfig = DEFAULT_CONFIG,
) -> tuple[Part | Compound, dict[str, object]]:
    """Build the printed enclosure body, standoffs, shelf, and brackets."""
    if variant.name == "thin_plate_inline_separate_mic":
        _base, _lid, printed, thin_notes = build_thin_plate_printed_parts(
            variant,
            config,
        )
        diagnostics = {
            "variant": variant.name,
            "outer_size_mm": list(variant.outer_size),
            "external_footprint_area_mm2": round(
                variant.outer_size[0] * variant.outer_size[1],
                3,
            ),
            "external_volume_mm3": round(
                variant.outer_size[0] * variant.outer_size[1] * variant.outer_size[2],
                3,
            ),
            "rear": "closed panel with service cutouts",
            "vent_hole_count": thin_notes["lid"]["vent_hole_count"],
            "wall_t_mm": config.wall_t,
            "floor_t_mm": config.floor_t,
            "roof_t_mm": config.roof_t,
            "separate_mic": variant.separate_mic,
            "removable_lid": thin_notes["lid"],
            "base": thin_notes["base"],
            "component_standoffs": thin_notes["component_standoffs"],
            "bounding_box": _bbox(printed),
        }
        return printed, diagnostics

    shell, vent_count = _open_back_shell(variant, config)
    floor_z = config.floor_t
    features: list[Part] = []
    for placement in variant.placements:
        if placement.spec not in BOARD_SPECS:
            continue
        spec = BOARD_SPECS[placement.spec]
        if placement.orientation == "floor":
            features.extend(
                _horizontal_mounts(
                    spec=spec,
                    placement=placement,
                    floor_z=floor_z + placement.z,
                )
            )
        elif placement.spec == "buck" and placement.orientation == "rear_wall":
            features.extend(
                _vertical_buck_mount(
                    placement=placement,
                    config=config,
                    floor_z=floor_z,
                )
            )

    features.extend(_shelf_features(variant, config, floor_z))
    top_features, cutouts = _top_mic_compartment_parts(variant, config)
    cutouts.extend(_wall_mount_cutouts(variant))
    with BuildPart() as printed:
        add(shell)
        for feature in features:
            add(feature)
        for feature in top_features:
            add(feature)
    part = printed.part.clean().fix()
    if cutouts:
        with BuildPart() as cutout_builder:
            for cutout in cutouts:
                add(cutout)
        part = (part - cutout_builder.part).clean().fix()

    top_mic_notes = None
    if variant.top_mic is not None:
        top_mic_notes = {
            "center_xy_mm": [variant.top_mic.center_x, variant.top_mic.center_y],
            "outer_d_mm": variant.top_mic.outer_d,
            "inner_d_mm": variant.top_mic.inner_d,
            "outer_h_mm": variant.top_mic.outer_h,
            "floor_t_mm": variant.top_mic.floor_t,
            "cable_pass_d_mm": variant.top_mic.cable_pass_d,
            "main_box_h_mm": _main_box_height(variant),
        }
    diagnostics = {
        "variant": variant.name,
        "outer_size_mm": list(variant.outer_size),
        "external_footprint_area_mm2": round(
            variant.outer_size[0] * variant.outer_size[1],
            3,
        ),
        "external_volume_mm3": round(
            variant.outer_size[0] * variant.outer_size[1] * variant.outer_size[2],
            3,
        ),
        "rear": "open",
        "vent_hole_count": vent_count,
        "wall_t_mm": config.wall_t,
        "floor_t_mm": config.floor_t,
        "roof_t_mm": config.roof_t,
        "top_mic_compartment": top_mic_notes,
        "separate_mic": variant.separate_mic,
        "wall_mount_holes": (
            {
                "count": 4,
                "diameter_mm": 6.4,
                "corner_inset_mm": 14.0,
            }
            if variant.wall_mount
            else None
        ),
        "bounding_box": _bbox(part),
    }
    return part, diagnostics


def build_component_placeholders(
    variant: LayoutVariant,
    config: PrintedConfig = DEFAULT_CONFIG,
) -> tuple[list[Part], dict[str, object]]:
    """Build rough clearance solids for the electronics in a layout variant."""
    floor_z = config.floor_t
    parts: list[Part] = []
    placements: dict[str, object] = {}
    for placement in variant.placements:
        if placement.spec in BOARD_SPECS:
            spec = BOARD_SPECS[placement.spec]
            part = _board_placeholder(spec, placement, floor_z)
            parts.append(part)
            placements[placement.spec] = {
                "orientation": placement.orientation,
                "center_xyz_mm": [placement.x, placement.y, placement.z],
                "clearance_size_mm": _board_clearance_size(spec, placement),
                "mount_points_local_xy_mm": [
                    list(point) for point in spec.mount_points
                ],
                "mount_hole_d_mm": spec.mount_hole_d,
                "note": placement.note,
                "bounding_box": _bbox(part),
            }
        elif placement.spec in DISK_SPECS:
            spec = DISK_SPECS[placement.spec]
            part = _disk_placeholder(spec, placement, floor_z)
            parts.append(part)
            placements[placement.spec] = {
                "orientation": placement.orientation,
                "center_xyz_mm": [placement.x, placement.y, placement.z],
                "diameter_mm": spec.diameter,
                "thickness_mm": spec.thickness,
                "note": placement.note,
                "bounding_box": _bbox(part),
            }
        else:
            raise ValueError(f"Unknown component spec: {placement.spec}")
    return parts, placements


def build_layout_assembly(
    variant: LayoutVariant,
    config: PrintedConfig = DEFAULT_CONFIG,
) -> tuple[Compound, dict[str, object]]:
    """Build an assembly of printed geometry plus rough component placeholders."""
    enclosure, enclosure_notes = build_printed_enclosure(variant, config)
    placeholders, placement_notes = build_component_placeholders(variant, config)
    assembly = Compound(children=[enclosure, *placeholders])
    notes = {
        **enclosure_notes,
        "description": variant.description,
        "placements": placement_notes,
        "assembly_bounding_box": _bbox(assembly),
    }
    return assembly, notes


def build_separate_mic_puck() -> tuple[Part, Compound, dict[str, object]]:
    """Build a detached low-profile horizontal mic puck concept."""
    outer_d = 114.0
    inner_d = 104.0
    height = 14.0
    floor_t = 2.0
    cable_notch_w = 16.0
    cable_notch_d = 14.0

    outer = Cylinder(
        radius=outer_d / 2,
        height=height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    inner = Pos(0, 0, floor_t) * Cylinder(
        radius=inner_d / 2,
        height=height - floor_t + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    cable_notch = Pos(0, outer_d / 2 - cable_notch_d / 2, floor_t) * Box(
        cable_notch_w,
        cable_notch_d + 0.6,
        height - floor_t + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    printed = (outer - inner - cable_notch).clean().fix()
    mic_disk = Pos(0, 0, floor_t) * Cylinder(
        radius=MIC.diameter / 2,
        height=MIC.thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.PRIVATE,
    )
    assembly = Compound(children=[printed, mic_disk])
    notes = {
        "description": (
            "Separate low-profile mic puck concept. The mic board remains "
            "horizontal for beamforming while the electronics plate can be hidden."
        ),
        "printed_outer_d_mm": outer_d,
        "printed_h_mm": height,
        "mic_clearance_d_mm": inner_d,
        "mic_board_d_mm": MIC.diameter,
        "mic_board_h_mm": MIC.thickness,
        "cable_notch_mm": [cable_notch_w, cable_notch_d],
        "printed_bounding_box": _bbox(printed),
        "assembly_bounding_box": _bbox(assembly),
    }
    return printed, assembly, notes


def researched_sources() -> dict[str, object]:
    """Return sourced dimensions used in this rough electronics model."""
    return {
        "raspberry_pi_5_mechanical_drawing": {
            "source": (
                "https://datasheets.raspberrypi.com/rpi5/"
                "raspberry-pi-5-mechanical-drawing.pdf"
            ),
            "board_size_mm": [85.0, 56.0],
            "mounting_hole_rectangle_mm": [58.0, 49.0],
            "mounting_hole_d_mm": 2.7,
            "noted_connector_edge_dimensions_mm": {
                "usb_ethernet_side_y_callouts": [10.2, 29.1, 47.0, 56.0],
                "bottom_edge_callouts": [11.2, 25.8, 39.2],
            },
            "rear_cutout_bay_mapping_mm": {
                "port_edge_midline_from_bottom": PI5_PORT_EDGE_MIDLINE_FROM_BOTTOM,
                "bay_centers_from_port_edge_bottom": {
                    name: center
                    for name, center, _width in PI5_REAR_PORT_BAYS
                },
            },
            "note": (
                "Official one-page mechanical drawing. Port cutout is still a "
                "fit-study bayed service window until the real Pi/HAT stack "
                "and cable moldings are test fit."
            ),
        },
        "raspberry_pi_5_product_brief": {
            "source": (
                "https://datasheets.raspberrypi.com/rpi5/"
                "raspberry-pi-5-product-brief.pdf"
            ),
            "board_size_mm": [85.0, 56.0],
            "mounting_hole_rectangle_mm": [58.0, 49.0],
            "mounting_hole_d_mm": 2.7,
            "note": (
                "Product brief physical specification shows 85 x 56 mm board, "
                "58 x 49 mm mount rectangle, and approx 2.7 mm holes."
            ),
        },
        "raspberry_pi_hat_mechanical": {
            "source": (
                "https://github.com/raspberrypi/hats/blob/master/"
                "hat-board-mechanical.pdf"
            ),
            "hat_board_size_mm": [65.0, 56.5],
            "mounting_hole_rectangle_mm": [58.0, 49.0],
            "mounting_hole_d_mm": 2.75,
            "corner_radius_mm": 3.0,
            "note": (
                "Official HAT drawing calls out 4x M2.5 holes drilled to "
                "2.75 mm +/- 0.05."
            ),
        },
        "user_supplied_clearances": {
            "amp_mm": {
                "mount_hole_rectangle": [AMP_MOUNT_LONG_CTC, AMP_MOUNT_NARROW_CTC],
                "mount_hole_d": 3.0,
                "measured_long_axis_hole_edges": {
                    "outer_to_outer_mm": 104.7,
                    "derived_center_to_center_mm": AMP_MOUNT_LONG_CTC,
                    "assumed_hole_d_mm": 3.0,
                },
                "actual": [108.0, 94.0, 36.0],
                "active_rotated_floor_footprint": [AMP.size_x, AMP.size_y],
                "active_post_height": AMP.post_h,
                "wire_exit_clearance_assumed": AMP_WIRE_EXIT_CLEARANCE,
            },
            "pi_with_hat_clearance_original_mm": [90.0, 90.0, 42.0],
            "pi_active_service_envelope_mm": [PI_HAT.size_x, PI_HAT.size_y, PI_HAT.size_z],
            "pi_mounting": "Fixed posts removed; four through-floor adjustment slots are used for removable feet.",
            "buck_mm": {
                "overall_width": 62.0,
                "body_length_plus_wire_clearance": 60.0 + BUCK_WIRE_CLEARANCE,
                "height": 21.0,
                "rear_mount_vertical_body_height": BUCK_REAR_MOUNT_BODY_H,
                "rear_mount_body_depth": BUCK_REAR_MOUNT_BODY_DEPTH,
                "rear_pin_d": BUCK_REAR_PIN_D,
                "rear_pin_depth": BUCK_REAR_PIN_DEPTH,
                "rear_pin_center_z_from_bottom": BUCK_REAR_PIN_CENTER_Z_FROM_BOTTOM,
                "hole_center_to_center": BUCK_MOUNT_HOLE_CTC,
                "hole_d": 6.0,
                "measured_hole_edge_distances": {
                    "outer_to_outer_mm": 59.5,
                    "inner_to_inner_mm": 47.84,
                    "derived_hole_d_mm": round((59.5 - 47.84) / 2, 3),
                },
                "bottom_wire_notch": [
                    BUCK_REAR_WIRE_NOTCH_W,
                    BUCK_REAR_WIRE_SLOT_H,
                ],
            },
            "mic_mm": {"diameter": 100.0, "height": 9.0},
        },
    }
