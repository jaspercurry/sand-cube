"""Generate the serviceable 40 mm tower-cartridge variant.

The proven modular-header study remains untouched.  This isolated wrapper keeps
its enclosure, circular airway, header centerline, horn reference placement,
and fixed outlet height while replacing only the upper-tower assembly details:

* a D-shaped underside flange installed from inside the cabinet;
* three blind roof-island heat-set pockets with no projecting bosses;
* a continuous shallow RTV groove inside the fastener circle;
* matching lower-duct and removable-flare sockets around a seamless 40 mm bore;
* a conformal D-shaped roof brace around the service flange.
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
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    Compound,
    Pos,
    Unit,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = ROOT / "experiments" / "sand_cube_190x210_header_port"
sys.path.insert(0, str(SOURCE_EXPERIMENT))

import generate_sand_cube_190x210_header_port as header  # noqa: E402


base = header.base
OUT = ROOT / "build" / "sand_cube_190x210_serviceable_tower"
base.OUT = OUT
header.OUT = OUT
base.D = replace(
    base.D,
    name="sand_cube_190x210_serviceable_40mm_tower_cartridge",
)


# The interface values are deliberately plain FDM dimensions.  The radial
# clearances are diameter-independent and can be compensated in a slicer/test
# coupon without changing the acoustic 40 mm bore.
FLANGE_RADIUS = 40.0
FLANGE_THICKNESS = 5.5
FLANGE_REAR_LAND = 0.0
ROOF_ISLAND_RADIUS = 42.0
INSERT_DEPTH = 4.2
INSERT_DIAMETER = 4.8
CLEARANCE_DIAMETER = 4.5
LOWER_SOCKET_DEPTH = 4.5
UPPER_SOCKET_DEPTH = 10.0
LOWER_SOCKET_RADIAL_CLEARANCE = 0.30
UPPER_SOCKET_RADIAL_CLEARANCE = 0.25
LOWER_MALE_WALL = 1.75
UPPER_MALE_WALL = 2.55
LOWER_AXIAL_CLEARANCE = 0.40
UPPER_SEATING_GAP = 0.20
LOWER_SPIGOT_ROOT_OVERLAP = 0.20
RTV_GROOVE_DEPTH = 0.60
RTV_GROOVE_WIDTH = 0.80
D_CRADLE_CLEARANCE = 1.0
D_CRADLE_WIDTH = 8.0
INSTALLATION_SWEEP_MARGIN = 0.50

ROOF_INNER_Z = base.D.height / 2.0 - base.D.wall_stack_t
ROOF_GAP_MIN_Z = ROOF_INNER_Z + base.D.inner_skin_t
ROOF_GAP_MAX_Z = ROOF_GAP_MIN_Z + base.D.sand_gap_t
REAR_INNER_Y = base.D.center_y + base.D.depth / 2.0 - base.D.wall_stack_t
TOWER_X = base.D.port_x
TOWER_Y = base.D.upper_tower_y
LOWER_INTERFACE_Z = header.H.target_tower_z_mm
LOWER_SOCKET_MOUTH_Z = ROOF_INNER_Z - FLANGE_THICKNESS
LOWER_SOCKET_SHOULDER_Z = LOWER_SOCKET_MOUTH_Z + LOWER_SOCKET_DEPTH
LOWER_SOCKET_INNER_R = (
    base.D.port_rx + LOWER_MALE_WALL + LOWER_SOCKET_RADIAL_CLEARANCE
)
LOWER_RECEIVER_WALL = base.D.tower_outer_rx - LOWER_SOCKET_INNER_R
if LOWER_RECEIVER_WALL < 2.80:
    raise ValueError(
        "Lower tower receiver wall is too thin for the weight-bearing root: "
        f"{LOWER_RECEIVER_WALL:.3f} mm"
    )

FINAL_HEADER_VERTICAL_STRAIGHT = (
    header._header_route_metadata()["short_vertical_straights_mm"][-1]
)
FINAL_HEADER_VERTICAL_START_Z = (
    LOWER_INTERFACE_Z - FINAL_HEADER_VERTICAL_STRAIGHT
)
if (
    LOWER_SOCKET_MOUTH_Z - LOWER_SPIGOT_ROOT_OVERLAP
    < FINAL_HEADER_VERTICAL_START_Z + 0.10
):
    raise ValueError(
        "Recessed lower socket enters the final curved header segment: "
        f"spigot root z={LOWER_SOCKET_MOUTH_Z - LOWER_SPIGOT_ROOT_OVERLAP:.3f} "
        f"versus straight start z={FINAL_HEADER_VERTICAL_START_Z:.3f} mm"
    )

# Three points fully outside the 50 mm tower OD and the sealant groove.  The
# single front screw and two rear-side screws form a stable triangle without
# asking for material behind the tower, where the 2-3-2 rear wall is close.
FASTENER_XY = (
    (0.0, TOWER_Y - 34.0),
    (-32.0, TOWER_Y + 10.0),
    (32.0, TOWER_Y + 10.0),
)


def _fresh_solids(shape: Any) -> list[Any]:
    return [solid for solid in shape.solids()]


def _z_cylinder(*, diameter: float, z0: float, z1: float, x: float = TOWER_X, y: float = TOWER_Y) -> Any:
    return base._oriented_cylinder(
        diameter=diameter,
        depth=z1 - z0,
        axis="z",
        center=(x, y, (z0 + z1) / 2.0),
    )


def _d_blank(
    *,
    radius: float,
    z0: float,
    z1: float,
    rear_y: float,
) -> Any:
    disk = _z_cylinder(diameter=2.0 * radius, z0=z0, z1=z1)
    front_y = TOWER_Y - radius - 2.0
    clip = Pos(
        TOWER_X,
        (front_y + rear_y) / 2.0,
        (z0 + z1) / 2.0,
    ) * Box(
        2.0 * radius + 4.0,
        rear_y - front_y,
        z1 - z0 + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return base._require_single_solid(
        (disk & clip).clean().fix(),
        feature="rear-clipped D-shaped tower flange",
    )


def _flange_blank(*, clearance: float = 0.0) -> Any:
    return _d_blank(
        radius=FLANGE_RADIUS + clearance,
        z0=ROOF_INNER_Z - FLANGE_THICKNESS - clearance,
        z1=ROOF_INNER_Z + clearance,
        rear_y=REAR_INNER_Y - FLANGE_REAR_LAND,
    )


def _roof_island_fill() -> Any:
    """Fill only the existing 3 mm sand gap; the two skins stay unchanged."""
    return _d_blank(
        radius=ROOF_ISLAND_RADIUS,
        z0=ROOF_GAP_MIN_Z,
        z1=ROOF_GAP_MAX_Z,
        rear_y=REAR_INNER_Y,
    )


def _roof_insert_pockets() -> list[Any]:
    return [
        base._oriented_cylinder(
            diameter=INSERT_DIAMETER,
            depth=INSERT_DEPTH,
            axis="z",
            center=(x, y, ROOF_INNER_Z + INSERT_DEPTH / 2.0),
        )
        for x, y in FASTENER_XY
    ]


def _flange_clearance_holes() -> list[Any]:
    return [
        base._oriented_cylinder(
            diameter=CLEARANCE_DIAMETER,
            depth=FLANGE_THICKNESS + 2.0,
            axis="z",
            center=(x, y, ROOF_INNER_Z - FLANGE_THICKNESS / 2.0),
        )
        for x, y in FASTENER_XY
    ]


def _rtv_groove() -> Any:
    # The back of the tower is close to the rear wall.  A compact annular bead
    # immediately outside the 50 mm OD remains continuous and still fits on
    # the D land.  It is shallow enough to leave a broad compression face.
    inner_radius = base.D.tower_outer_rx + 0.20
    outer_radius = inner_radius + RTV_GROOVE_WIDTH
    outer = _z_cylinder(
        diameter=2.0 * outer_radius,
        z0=ROOF_INNER_Z - RTV_GROOVE_DEPTH,
        z1=ROOF_INNER_Z + 0.05,
    )
    inner = _z_cylinder(
        diameter=2.0 * inner_radius,
        z0=ROOF_INNER_Z - RTV_GROOVE_DEPTH - 0.1,
        z1=ROOF_INNER_Z + 0.1,
    )
    return (outer - inner).clean().fix()


def _roof_platforms() -> Compound:
    # No downward bosses: the island occupies only the sand gap between the
    # existing inner and outer skins, making this patch a true solid 7 mm roof.
    return Compound(children=_fresh_solids(_roof_island_fill()))


def _service_flange_keepout(*, clearance: float = 0.0) -> Any:
    """Full-height keepout so no retained rail can trap the rising flange."""
    brace_height = (
        base.RESTORED_FEATURE_VARIANT.vertical_brace_height
        + base.RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed
    )
    brace_center_z = (
        base.D.width / 2.0
        - base.D.wall_stack_t
        - base.RESTORED_FEATURE_VARIANT.vertical_brace_height / 2.0
        + base.RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed / 2.0
    )
    return _d_blank(
        radius=FLANGE_RADIUS + D_CRADLE_CLEARANCE + clearance,
        z0=brace_center_z - brace_height / 2.0 - 1.0,
        z1=brace_center_z + brace_height / 2.0 + 1.0,
        rear_y=REAR_INNER_Y + D_CRADLE_CLEARANCE + clearance,
    )


def _d_cradle() -> Any:
    """Constant-width D brace following the flange and roof-island boundary."""
    brace_height = (
        base.RESTORED_FEATURE_VARIANT.vertical_brace_height
        + base.RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed
    )
    brace_center_z = (
        base.D.width / 2.0
        - base.D.wall_stack_t
        - base.RESTORED_FEATURE_VARIANT.vertical_brace_height / 2.0
        + base.RESTORED_FEATURE_VARIANT.vertical_brace_skin_embed / 2.0
    )
    z0 = brace_center_z - brace_height / 2.0
    z1 = brace_center_z + brace_height / 2.0
    inner_radius = FLANGE_RADIUS + D_CRADLE_CLEARANCE
    outer_radius = inner_radius + D_CRADLE_WIDTH
    outer = _d_blank(
        radius=outer_radius,
        z0=z0,
        z1=z1,
        # The back of the brace becomes one smooth root inside the rear wall.
        rear_y=base.D.center_y + base.D.depth / 2.0,
    )
    inner = _d_blank(
        radius=inner_radius,
        z0=z0 - 0.2,
        z1=z1 + 0.2,
        rear_y=REAR_INNER_Y + D_CRADLE_CLEARANCE,
    )
    return base._require_single_solid(
        (outer - inner).clean().fix(),
        feature="constant-width D-shaped roof-island cradle",
    )


ORIGINAL_RESTORED_BRACES = base._restored_internal_braces


def _serviceable_braces(port_clearance: Any) -> Compound:
    """Retain the original network and add a conformal D-shaped roof cradle."""
    retained = ORIGINAL_RESTORED_BRACES(port_clearance)
    cradle = _d_cradle()
    result = Compound(
        children=[*_fresh_solids(retained), *_fresh_solids(cradle)]
    )

    # Final-position interference is insufficient for a removable cartridge.
    # Sweep an expanded D flange through the complete brace depth and reject
    # any overhang that would stop it from moving vertically into its seat.
    brace_bb = cradle.bounding_box()
    installation_sweep = _d_blank(
        radius=FLANGE_RADIUS + INSTALLATION_SWEEP_MARGIN,
        z0=brace_bb.min.Z - 1.0,
        z1=ROOF_INNER_Z,
        rear_y=REAR_INNER_Y + INSTALLATION_SWEEP_MARGIN,
    )
    trapped_volume = base._bounded_intersection_volume(result, installation_sweep)
    if trapped_volume > 0.001:
        raise ValueError(
            "Roof bracing traps the tower flange during installation by "
            f"{trapped_volume:.6f} mm3"
        )
    return result


def _internal_tube_with_male_spigot(
    port_airway: Any,
    port_outer: Any,
) -> tuple[Any, Any]:
    lower_z = -base.D.height / 2.0
    clip = Pos(
        0.0,
        base.D.center_y,
        (lower_z + LOWER_SOCKET_MOUTH_Z) / 2.0,
    ) * Box(
        300.0,
        300.0,
        LOWER_SOCKET_MOUTH_Z - lower_z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    enclosure_clip = base._outer_envelope() & clip
    lower_outer = base._primary_shape(port_outer & enclosure_clip)
    lower_airway = base._primary_shape(port_airway & enclosure_clip)
    lower_shell = (lower_outer - lower_airway).clean().fix()

    male_outer_r = base.D.port_rx + LOWER_MALE_WALL
    male_top = LOWER_SOCKET_SHOULDER_Z - LOWER_AXIAL_CLEARANCE
    male_outer = _z_cylinder(
        diameter=2.0 * male_outer_r,
        z0=LOWER_SOCKET_MOUTH_Z - LOWER_SPIGOT_ROOT_OVERLAP,
        z1=male_top,
    )
    male_air = _z_cylinder(
        diameter=base.D.port_width,
        z0=LOWER_SOCKET_MOUTH_Z - 0.25,
        z1=male_top + 0.2,
    )
    male_shell = (male_outer - male_air).clean().fix()
    tube = base._require_single_solid(
        lower_shell.fuse(male_shell).clean().fix(),
        feature="internal header with 40 mm-bore male tower spigot",
    )
    displacement = base._require_single_solid(
        lower_outer.fuse(male_outer).clean().fix(),
        feature="internal header and male-spigot displacement envelope",
    )
    return tube, displacement


def _upper_displacement(port_outer: Any) -> Any:
    roof_outer_z = base.D.height / 2.0
    clip = Pos(
        0.0,
        base.D.center_y,
        (LOWER_SOCKET_MOUTH_Z + roof_outer_z) / 2.0,
    ) * Box(
        300.0,
        300.0,
        roof_outer_z - LOWER_SOCKET_MOUTH_Z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    upper_outer = base._primary_shape(port_outer & base._outer_envelope() & clip)
    receiver_outer = _z_cylinder(
        diameter=2.0 * base.D.tower_outer_rx,
        z0=LOWER_SOCKET_MOUTH_Z,
        z1=roof_outer_z,
    )
    # The flange is a printed obstruction below the inner roof; fuse it to the
    # full port envelope so volume accounting sees one union, not nested parts.
    result = upper_outer.fuse(receiver_outer, _flange_blank()).clean().fix()
    for hole in _flange_clearance_holes():
        result = result - hole
    result = result - _rtv_groove()
    return base._require_single_solid(
        result.clean().fix(),
        feature="upper tower and D-flange displacement envelope",
    )


def _tower_parts(outlet_z: float) -> tuple[Any, Any, Any]:
    airway, outer = base._path_solids(outlet_z)
    outlet_throat_z = outlet_z - base.D.outlet_flare_l
    upper_socket_inner_r = (
        base.D.port_rx + UPPER_MALE_WALL + UPPER_SOCKET_RADIAL_CLEARANCE
    )

    cartridge_outer = _z_cylinder(
        diameter=2.0 * base.D.tower_outer_rx,
        z0=LOWER_SOCKET_MOUTH_Z,
        z1=outlet_throat_z,
    )
    cartridge_air = _z_cylinder(
        diameter=base.D.port_width,
        z0=LOWER_SOCKET_MOUTH_Z - 0.2,
        z1=outlet_throat_z + 0.2,
    )
    cartridge = (cartridge_outer - cartridge_air).clean().fix()
    cartridge = cartridge.fuse(_flange_blank()).clean().fix()

    lower_socket = _z_cylinder(
        diameter=2.0 * LOWER_SOCKET_INNER_R,
        z0=LOWER_SOCKET_MOUTH_Z - 0.2,
        z1=LOWER_SOCKET_SHOULDER_Z,
    )
    upper_socket = _z_cylinder(
        diameter=2.0 * upper_socket_inner_r,
        z0=outlet_throat_z - UPPER_SOCKET_DEPTH,
        z1=outlet_throat_z + 0.2,
    )
    # Re-cut the 40 mm airway after fusing the solid D flange.  The lower
    # counterbore is intentionally shorter than the flange, so it must not be
    # relied upon to open the final 1 mm of the acoustic passage.
    cartridge = cartridge - cartridge_air - lower_socket - upper_socket
    for hole in _flange_clearance_holes():
        cartridge = cartridge - hole
    cartridge = cartridge - _rtv_groove()
    cartridge = base._require_single_solid(
        cartridge.clean().fix(),
        feature="straight load-bearing tower cartridge with two female sockets",
    )

    flare_clip = Pos(
        0.0,
        base.D.center_y,
        (outlet_throat_z + outlet_z + 1.0) / 2.0,
    ) * Box(
        300.0,
        300.0,
        outlet_z - outlet_throat_z + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    flare_outer = base._primary_shape(outer & flare_clip)
    flare_air = base._primary_shape(airway & flare_clip)
    flare_shell = (flare_outer - flare_air).clean().fix()
    male_outer = _z_cylinder(
        diameter=2.0 * (base.D.port_rx + UPPER_MALE_WALL),
        z0=outlet_throat_z - UPPER_SOCKET_DEPTH + UPPER_SEATING_GAP,
        z1=outlet_throat_z + 0.25,
    )
    male_air = _z_cylinder(
        diameter=base.D.port_width,
        z0=outlet_throat_z - UPPER_SOCKET_DEPTH,
        z1=outlet_throat_z + 0.4,
    )
    flare_spigot = (male_outer - male_air).clean().fix()
    flare = base._require_single_solid(
        flare_shell.fuse(flare_spigot).clean().fix(),
        feature="removable outlet flare with 40 mm-bore male spigot",
    )

    tower = Compound(children=[cartridge, flare])
    return tower, airway, outer


# Override only the assembly-related hooks inherited by the header study.
base._internal_tower_mount_platforms = _roof_platforms
base._internal_tower_mount_insert_pockets = _roof_insert_pockets
base._internal_tower_mount_clearance_holes = _flange_clearance_holes
base._internal_tower_mount_saddle = _service_flange_keepout
base._restored_internal_braces = _serviceable_braces
base.build_internal_tube = _internal_tube_with_male_spigot
base._internal_tower_mount_displacement = _upper_displacement
base.build_tower = _tower_parts


def _separate_tower_parts(outlet_z: float) -> tuple[Any, Any]:
    tower, _airway, _outer = _tower_parts(outlet_z)
    solids = tower.solids()
    if len(solids) != 2:
        raise ValueError(f"Expected cartridge and flare, got {len(solids)} solids")
    return solids[0], solids[1]


def _export_separate_parts(diagnostics: dict[str, Any]) -> dict[str, Any]:
    outlet_z = float(diagnostics["port"]["lengths"]["outlet_z_mm"])
    cartridge, flare = _separate_tower_parts(outlet_z)
    parts = {
        "serviceable_40mm_tower_cartridge.step": cartridge,
        "serviceable_40mm_removable_flare.step": flare,
    }
    checks: dict[str, Any] = {}
    for filename, shape in parts.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        checks[filename] = {
            "source_solid_count": len(shape.solids()),
            "imported_solid_count": len(imported.solids()),
            "all_imported_solids_valid": all(
                solid.is_valid for solid in imported.solids()
            ),
        }
        if (
            checks[filename]["source_solid_count"]
            != checks[filename]["imported_solid_count"]
            or not checks[filename]["all_imported_solids_valid"]
        ):
            raise ValueError(f"STEP round-trip failed for {filename}")
    return checks


def _rewrite_diagnostics(diagnostics: dict[str, Any]) -> dict[str, Any]:
    diagnostics["name"] = base.D.name
    diagnostics["status"] = (
        "serviceable inside-installed 40 mm tower cartridge with a solid roof "
        "island, three blind fasteners, matching bore sockets, and removable flare"
    )
    diagnostics["isolation"] = {
        "experiment_dir": "experiments/sand_cube_190x210_serviceable_tower",
        "output_dir": "build/sand_cube_190x210_serviceable_tower",
        "header_port_variant_modified": False,
        "smooth_sweep_variant_modified": False,
    }
    diagnostics["enclosure"]["construction"] = (
        "The established 190 x 210 x 190 enclosure, centered black-hole face, "
        "GX16, fill blisters, solid floor, 2-3-2 walls, and port-relieved brace "
        "network are retained. Only the upper assembly changes: its local roof "
        "gap is filled into a solid 7 mm insert island, and the existing top rail "
        "flows into a constant-width D-shaped cradle around the hidden flange."
    )
    brace_data = diagnostics["enclosure"]["restored_original_features"][
        "internal_bracing"
    ]
    brace_data["tube_mounting_features_deferred"] = False
    brace_data["serviceable_tower_y_fork_added"] = False
    brace_data["serviceable_tower_conformal_d_cradle_added"] = True
    brace_data["design_intent"] = (
        "The original equal-height top and side brace network and all four "
        "conformal black-hole roots remain. Near the roof cartridge, the top "
        "rail flows into a smooth constant-width D-shaped cradle. Its inner and "
        "outer boundaries follow the flange and roof-island curvature, while a "
        "full-height installation keepout prevents any front or rear overhang."
    )
    diagnostics["serviceable_tower"] = {
        "installation_direction": "tower cartridge inserted from inside through roof",
        "visible_tower": {
            "airway_diameter_mm": base.D.port_width,
            "outside_diameter_mm": 2.0 * base.D.tower_outer_rx,
            "wall_thickness_mm": base.D.structural_tower_wall_t,
            "straight_above_enclosure": True,
        },
        "roof_island": {
            "local_total_thickness_mm": base.D.wall_stack_t,
            "fills_only_existing_sand_gap": True,
            "downward_insert_bosses": 0,
            "blind_insert_count": len(FASTENER_XY),
            "insert_pocket_diameter_mm": INSERT_DIAMETER,
            "insert_depth_mm": INSERT_DEPTH,
            "remaining_outer_cap_mm": base.D.wall_stack_t - INSERT_DEPTH,
            "fastener_centers_xy_mm": [list(xy) for xy in FASTENER_XY],
        },
        "d_flange": {
            "radius_mm": FLANGE_RADIUS,
            "thickness_mm": FLANGE_THICKNESS,
            "underside_is_flat_print_bed_face": True,
            "rear_clipped_to_acoustic_face": True,
            "clearance_hole_diameter_mm": CLEARANCE_DIAMETER,
            "rtv_groove_depth_mm": RTV_GROOVE_DEPTH,
            "rtv_groove_width_mm": RTV_GROOVE_WIDTH,
            "o_ring_required": False,
        },
        "modular_interfaces": {
            "count": 2,
            "locations": ["lower duct to tower", "tower to outlet flare"],
            "shared_acoustic_bore_diameter_mm": base.D.port_width,
            "lower_socket_depth_mm": LOWER_SOCKET_DEPTH,
            "upper_flare_socket_depth_mm": UPPER_SOCKET_DEPTH,
            "lower_receiver_projection_below_d_flange_mm": 0.0,
            "lower_receiver_fully_recessed_above_print_face": True,
            "lower_socket_mouth_z_mm": LOWER_SOCKET_MOUTH_Z,
            "lower_socket_shoulder_z_mm": LOWER_SOCKET_SHOULDER_Z,
            "lower_socket_entrance_chamfer_added": False,
            "lower_socket_shoulder_angle_deg": 90.0,
            "lower_spigot_outside_diameter_mm": 2.0
            * (base.D.port_rx + LOWER_MALE_WALL),
            "lower_socket_inside_diameter_mm": 2.0 * LOWER_SOCKET_INNER_R,
            "lower_receiver_minimum_wall_mm": LOWER_RECEIVER_WALL,
            "lower_receiver_material_area_retained_fraction": (
                base.D.tower_outer_rx**2 - LOWER_SOCKET_INNER_R**2
            )
            / (base.D.tower_outer_rx**2 - base.D.port_rx**2),
            "lower_receiver_bending_inertia_retained_fraction": (
                base.D.tower_outer_rx**4 - LOWER_SOCKET_INNER_R**4
            )
            / (base.D.tower_outer_rx**4 - base.D.port_rx**4),
            "final_header_vertical_straight_available_mm": (
                FINAL_HEADER_VERTICAL_STRAIGHT
            ),
            "straight_remaining_below_spigot_root_mm": (
                LOWER_SOCKET_MOUTH_Z
                - LOWER_SPIGOT_ROOT_OVERLAP
                - FINAL_HEADER_VERTICAL_START_Z
            ),
            "lower_radial_clearance_mm": LOWER_SOCKET_RADIAL_CLEARANCE,
            "upper_radial_clearance_mm": UPPER_SOCKET_RADIAL_CLEARANCE,
            "lower_male_wall_thickness_mm": LOWER_MALE_WALL,
            "upper_male_wall_thickness_mm": UPPER_MALE_WALL,
            "lower_nominal_axial_clearance_mm": LOWER_AXIAL_CLEARANCE,
            "upper_nominal_axial_seating_gap_mm": UPPER_SEATING_GAP,
            "lower_receiver_uses_internal_sealant": True,
            "inner_transition_has_diameter_step": False,
        },
        "top_brace": {
            "original_network_retained": True,
            "shape": "constant-width conformal D cradle",
            "inside_clearance_to_flange_mm": D_CRADLE_CLEARANCE,
            "cradle_width_mm": D_CRADLE_WIDTH,
            "inner_and_outer_boundaries_are_smooth": True,
            "inward_face_flush_with_original_ribs": True,
            "rear_root_fused_into_rear_wall": True,
            "vertical_installation_sweep_margin_mm": INSTALLATION_SWEEP_MARGIN,
            "front_or_rear_overhang_traps_flange": False,
            "rear_capture_groove_used": False,
            "retention": "three underside screws into blind solid-roof inserts",
        },
        "deferred": [
            "final print-process tolerance coupon",
            "snap features for the removable flare",
            "external tube ribs or constrained-layer damping",
            "final horn clamp redesign",
        ],
    }
    diagnostics["port"]["separate_printed_internal_tube"].update(
        {
            "core_shell_only": False,
            "join_collars_deferred": False,
            "lower_tower_spigot_added": True,
            "acoustic_bore_diameter_mm": base.D.port_width,
            "socket_join_is_above_internal_header_endpoint": True,
            "heat_set_insert_features_deferred": False,
        }
    )
    diagnostics["port"]["internally_mounted_upper_tower"] = {
        "enabled": True,
        "serviceable": True,
        "visible_profile": "straight 40 mm bore / 50 mm OD circle",
        "separate_outlet_flare": True,
        "underside_d_flange": True,
        "blind_roof_fasteners": len(FASTENER_XY),
        "downward_bosses": 0,
    }
    diagnostics["geometry"]["single_external_rising_support"] = True
    diagnostics["geometry"]["structural_mounts_deferred"] = False
    diagnostics["files"]["diagnostics"] = str(OUT / "diagnostics.json")
    diagnostics["files"]["exterior_viewer"] = str(OUT / "viewer" / "index.html")
    diagnostics["files"]["cutaway_viewer"] = str(
        OUT / "cutaway_viewer" / "index.html"
    )
    return diagnostics


def generate() -> dict[str, Any]:
    diagnostics = header.generate()
    diagnostics = _rewrite_diagnostics(diagnostics)
    diagnostics["serviceable_tower"]["separate_step_roundtrip"] = (
        _export_separate_parts(diagnostics)
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
