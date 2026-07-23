"""Export the final 8.5 in enclosure plus horn/bracket system assemblies."""

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

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import (
    Align,
    Box,
    BuildPart,
    Compound,
    Cylinder,
    Location,
    Mode,
    Pos,
    Rot,
    Unit,
    add,
    import_step,
)
from bd_warehouse.thread import IsoThread

from params import p
from src.cad_io import export_step
from src.features.bracket import build_binding_post_grommet, build_horn_bracket
from src.final_enclosure import build as build_final_enclosure
from src.final_enclosure import build_export_shapes
from src.final_horn import build as build_final_horn
from src.final_horn import place_above_enclosure


OUT = ROOT / "build" / "final_system"
MATERIAL_T = p.horn_bracket_t
GROMMET_WASHER_T = 2.0
HORN_CLEARANCE_ABOVE_TOP = 10.0
BINDING_POST_STEP = ROOT / "objects" / "Dayton Audio Binding Posts.stp"
BINDING_POST_PILOT_D = 6.35
BINDING_POST_TPU_BORE_D = 6.15
BINDING_POST_TPU_SLEEVE_OD = 8.4
BINDING_POST_CLEARANCE_D = 8.7


def _fresh_solids(shape) -> list:
    """Return copied solids so each exported compound owns its children."""
    return [copy.copy(solid) for solid in shape.solids()]


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _build_fill_plug(params):
    """Build the solid-core, flush-slotted sand-fill plug."""
    thread_l = params.fill_thread_length - 1.0
    head_t = params.fill_entry_depth
    head_d = params.fill_entry_d - 0.4
    slot_l = head_d * 0.82
    slot_w = 2.4
    slot_d = head_t + 0.25

    thread = IsoThread(
        major_diameter=params.fill_thread_major_d - 0.35,
        pitch=params.fill_thread_pitch,
        length=thread_l,
        external=True,
        end_finishes=("chamfer", "fade"),
        interference=0.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    with BuildPart() as plug:
        add(
            Cylinder(
                radius=params.fill_thread_core_d / 2,
                height=thread_l,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
        add(thread)
        add(
            Pos(0, 0, thread_l - head_t)
            * Cylinder(
                radius=head_d / 2,
                height=head_t,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.PRIVATE,
            )
        )
    slot = Pos(0, 0, thread_l - slot_d / 2) * Box(
        slot_l,
        slot_w,
        slot_d,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    return (plug.part - slot).clean().fix()


def _placed_fill_plugs(params):
    """Place two threaded plugs in the rear sand-fill ports."""
    half = params.cube_outer / 2
    plug = _build_fill_plug(params)
    thread_l = params.fill_thread_length - 1.0
    plug_y = half - thread_l
    return [
        Location((x, plug_y, params.fill_port_z)) * Rot(-90, 0, 0) * plug
        for x in (-params.fill_port_x, params.fill_port_x)
    ]


def _shape_from_export(
    enclosure_exports: dict[str, object],
    filename: str,
) -> object:
    return enclosure_exports[filename]


def _build_horn_stack(enclosure):
    """Build horn, bracket, grommets, and DE250 in the installed position."""
    standalone_horn = build_final_horn()
    horn = Rot(0, 0, -60) * standalone_horn
    placed_horn = place_above_enclosure(
        enclosure,
        horn,
        clearance=HORN_CLEARANCE_ABOVE_TOP,
    )

    horn_bb = placed_horn.bounding_box()
    enclosure_bb = enclosure.bounding_box()
    horn_center_x = (horn_bb.min.X + horn_bb.max.X) / 2
    horn_center_z = (horn_bb.min.Z + horn_bb.max.Z) / 2
    horn_driver_face_y = horn_bb.max.Y
    bracket_front_y = horn_driver_face_y - MATERIAL_T

    bracket = build_horn_bracket(
        enclosure_top_z=enclosure_bb.max.Z,
        horn_rear_y=bracket_front_y,
        horn_center_z=horn_center_z,
        material_t=MATERIAL_T,
        top_bolt_spacing=p.bracket_hole_spacing,
        top_bolt_y=p.bracket_hole_y,
        binding_post_spacing=p.binding_post_spacing,
        binding_post_y=p.binding_post_y,
        binding_post_grommet_hole_d=BINDING_POST_CLEARANCE_D,
        acoustic_hole_d=p.horn_bracket_throat_clearance_d,
        horn_bolt_d=p.horn_bolt_clearance_d,
        horn_bolt_3_bcd=p.horn_bolt_3_bcd,
        horn_bolt_2_bcd=p.horn_bolt_2_bcd,
    )

    grommet = build_binding_post_grommet(
        washer_t=GROMMET_WASHER_T,
        sleeve_od=BINDING_POST_TPU_SLEEVE_OD,
        bore_d=BINDING_POST_TPU_BORE_D,
        sleeve_l=p.outer_skin_t + p.void_t + p.inner_skin_t + MATERIAL_T,
    )
    bracket_top_z = enclosure_bb.max.Z + MATERIAL_T
    grommets = [
        Location((x, p.binding_post_y, bracket_top_z)) * grommet
        for x in (-p.binding_post_spacing / 2, p.binding_post_spacing / 2)
    ]
    binding_post_raw = import_step(BINDING_POST_STEP)
    head_solid = max(
        binding_post_raw.solids(),
        key=lambda solid: solid.bounding_box().size.X * solid.bounding_box().size.Y,
    )
    head_bottom_raw_z = head_solid.bounding_box().min.Z
    grommet_top_z = bracket_top_z + GROMMET_WASHER_T
    binding_post_z = grommet_top_z - head_bottom_raw_z
    binding_posts = [
        Location((x, p.binding_post_y, binding_post_z)) * binding_post_raw
        for x in (-p.binding_post_spacing / 2, p.binding_post_spacing / 2)
    ]

    comp_raw = import_step(ROOT / "objects" / "Compression DriverDE250.step")
    compression_driver = (
        Location((horn_center_x, horn_driver_face_y, horn_center_z))
        * (Rot(90, 0, 0) * comp_raw)
    )

    horn_stack = Compound(
        children=[
            *_fresh_solids(placed_horn),
            *_fresh_solids(bracket),
            *[_fresh_solids(grommet_part)[0] for grommet_part in grommets],
            *[
                solid
                for binding_post in binding_posts
                for solid in _fresh_solids(binding_post)
            ],
            *_fresh_solids(compression_driver),
        ]
    )

    notes = {
        "horn_front_flush_y_mm": round(placed_horn.bounding_box().min.Y, 3),
        "enclosure_front_y_mm": round(enclosure_bb.min.Y, 3),
        "horn_clearance_above_top_mm": round(
            horn_bb.min.Z - enclosure_bb.max.Z,
            3,
        ),
        "bracket_front_y_mm": round(bracket_front_y, 3),
        "compression_driver_face_y_mm": round(horn_driver_face_y, 3),
        "horn_center_x_mm": round(horn_center_x, 3),
        "horn_center_z_mm": round(horn_center_z, 3),
        "binding_post_source": str(BINDING_POST_STEP),
        "binding_post_head_bottom_raw_z_mm": round(head_bottom_raw_z, 3),
        "binding_post_head_seat_z_mm": round(grommet_top_z, 3),
        "binding_post_z_offset_mm": round(binding_post_z, 3),
        "binding_post_count": len(binding_posts),
        "binding_post_manufacturer_pilot_d_mm": BINDING_POST_PILOT_D,
        "binding_post_tpu_bore_d_mm": BINDING_POST_TPU_BORE_D,
        "binding_post_tpu_sleeve_od_mm": BINDING_POST_TPU_SLEEVE_OD,
        "binding_post_bracket_and_enclosure_clearance_d_mm": BINDING_POST_CLEARANCE_D,
    }
    return (
        standalone_horn,
        placed_horn,
        bracket,
        grommet,
        binding_posts,
        horn_stack,
        notes,
    )


def main() -> None:
    """Export final individual parts and the full system assembly."""
    OUT.mkdir(parents=True, exist_ok=True)

    enclosure_exports, enclosure_data = build_export_shapes()
    _enclosure_part, params, _ = build_final_enclosure()
    enclosure = _shape_from_export(
        enclosure_exports,
        "sand_cube_8_5_black_hole_final_enclosure.step",
    )
    enclosure_with_inserts = _shape_from_export(
        enclosure_exports,
        "sand_cube_8_5_black_hole_final_enclosure_with_heat_set_inserts.step",
    )
    enclosure_with_pr_gx16 = _shape_from_export(
        enclosure_exports,
        "sand_cube_8_5_black_hole_final_enclosure_with_inserts_pr_gx16.step",
    )
    complete_enclosure = _shape_from_export(
        enclosure_exports,
        "sand_cube_8_5_black_hole_final_complete_assembly.step",
    )
    fill_plugs = _placed_fill_plugs(params)

    (
        standalone_horn,
        placed_horn,
        bracket,
        grommet,
        binding_posts,
        horn_stack,
        stack_notes,
    ) = _build_horn_stack(enclosure)
    full_system = Compound(
        children=[
            *_fresh_solids(complete_enclosure),
            *[
                solid
                for fill_plug in fill_plugs
                for solid in _fresh_solids(fill_plug)
            ],
            *_fresh_solids(horn_stack),
        ]
    )
    diagnostic_assemblies = {
        "diag_01_enclosure_horn_stack": Compound(
            children=[
                *_fresh_solids(enclosure),
                *[
                    solid
                    for fill_plug in fill_plugs
                    for solid in _fresh_solids(fill_plug)
                ],
                *_fresh_solids(horn_stack),
            ]
        ),
        "diag_02_enclosure_inserts_horn_stack": Compound(
            children=[
                *_fresh_solids(enclosure_with_inserts),
                *[
                    solid
                    for fill_plug in fill_plugs
                    for solid in _fresh_solids(fill_plug)
                ],
                *_fresh_solids(horn_stack),
            ]
        ),
        "diag_03_enclosure_inserts_pr_gx16_horn_stack": Compound(
            children=[
                *_fresh_solids(enclosure_with_pr_gx16),
                *[
                    solid
                    for fill_plug in fill_plugs
                    for solid in _fresh_solids(fill_plug)
                ],
                *_fresh_solids(horn_stack),
            ]
        ),
        "diag_04_complete_enclosure_horn_stack": full_system,
    }

    files = {
        "horn_standalone": OUT / "final_jmlc_horn.step",
        "horn": OUT / "final_jmlc_horn_placed.step",
        "bracket": OUT / "final_horn_bracket_4mm_folded.step",
        "binding_post_grommet": OUT / "final_binding_post_tpu_grommet.step",
        "binding_posts_pair": OUT / "final_binding_posts_pair.step",
        "fill_plugs_pair": OUT / "final_sand_fill_plugs_pair.step",
        "horn_bracket_de250_stack": OUT / "final_horn_bracket_de250_stack.step",
        "full_system": OUT / "final_sand_cube_horn_system.step",
        **{
            name: OUT / f"{name}.step"
            for name in diagnostic_assemblies
        },
    }
    export_step(
        standalone_horn,
        files["horn_standalone"],
        unit=Unit.MM,
        write_pcurves=False,
    )
    export_step(placed_horn, files["horn"], unit=Unit.MM, write_pcurves=False)
    export_step(bracket, files["bracket"], unit=Unit.MM, write_pcurves=False)
    export_step(grommet, files["binding_post_grommet"], unit=Unit.MM)
    export_step(
        Compound(
            children=[
                solid
                for binding_post in binding_posts
                for solid in _fresh_solids(binding_post)
            ]
        ),
        files["binding_posts_pair"],
        unit=Unit.MM,
    )
    export_step(
        Compound(
            children=[
                solid
                for fill_plug in fill_plugs
                for solid in _fresh_solids(fill_plug)
            ]
        ),
        files["fill_plugs_pair"],
        unit=Unit.MM,
    )
    export_step(
        horn_stack,
        files["horn_bracket_de250_stack"],
        unit=Unit.MM,
        write_pcurves=False,
    )
    export_step(
        full_system,
        files["full_system"],
        unit=Unit.MM,
        write_pcurves=False,
    )
    for name, assembly in diagnostic_assemblies.items():
        export_step(
            assembly,
            files[name],
            unit=Unit.MM,
            write_pcurves=False,
        )

    notes = {
        "purpose": "Final 8.5 in Sand Cube with woofer/PR/GX16/inserts plus horn, bracket, and DE250.",
        "enclosure_source": "src.final_enclosure / sand_cube_8_5_black_hole final candidate",
        "horn_source": "src.final_horn / src.features.horn.build_jmlc_horn",
        "bracket_source": "src.features.bracket.build_horn_bracket",
        "files": {key: str(path) for key, path in files.items()},
        "interfaces": {
            "top_mount_holes": {
                "dedicated_screws": 2,
                "binding_posts_as_rear_clamps": 2,
                "front_screw_x_spacing_mm": p.bracket_hole_spacing,
                "front_screw_y_mm": p.bracket_hole_y - p.bracket_hole_spacing / 2,
                "binding_post_spacing_mm": p.binding_post_spacing,
                "binding_post_y_mm": p.binding_post_y,
                "bracket_and_enclosure_clearance_d_mm": BINDING_POST_CLEARANCE_D,
                "tpu_sleeve_od_mm": BINDING_POST_TPU_SLEEVE_OD,
                "tpu_bore_d_mm": BINDING_POST_TPU_BORE_D,
            },
            "horn_mount": {
                "active_pattern": "B&C DE250 3-bolt pattern",
                "bolt_3_bcd_mm": p.horn_bolt_3_bcd,
                "bolt_2_bcd_mm": p.horn_bolt_2_bcd,
                "hole_d_mm": p.horn_bolt_clearance_d,
                "acoustic_hole_d_mm": p.horn_bracket_throat_clearance_d,
                "printed_spigot_od_mm": p.horn_spigot_od,
                "printed_spigot_l_mm": p.horn_bracket_t,
            },
            **stack_notes,
        },
        "solid_counts": {
            "enclosure": len(enclosure.solids()),
            "enclosure_with_inserts": len(enclosure_with_inserts.solids()),
            "enclosure_with_pr_gx16": len(enclosure_with_pr_gx16.solids()),
            "complete_enclosure": len(complete_enclosure.solids()),
            "fill_plugs": sum(len(fill_plug.solids()) for fill_plug in fill_plugs),
            "horn_stack": len(horn_stack.solids()),
            "full_system": len(full_system.solids()),
            **{
                name: len(assembly.solids())
                for name, assembly in diagnostic_assemblies.items()
            },
        },
        "bounding_boxes": {
            "enclosure": _bbox(enclosure),
            "horn_standalone": _bbox(standalone_horn),
            "enclosure_with_inserts": _bbox(enclosure_with_inserts),
            "enclosure_with_pr_gx16": _bbox(enclosure_with_pr_gx16),
            "complete_enclosure": _bbox(complete_enclosure),
            "fill_plugs": _bbox(Compound(children=[
                solid
                for fill_plug in fill_plugs
                for solid in _fresh_solids(fill_plug)
            ])),
            "horn_stack": _bbox(horn_stack),
            "full_system": _bbox(full_system),
            **{
                name: _bbox(assembly)
                for name, assembly in diagnostic_assemblies.items()
            },
        },
        "enclosure_diagnostics": enclosure_data,
    }
    (OUT / "final_system_notes.json").write_text(json.dumps(notes, indent=2))
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
