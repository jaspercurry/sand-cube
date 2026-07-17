"""Generate the independently versioned Rev D D-squat port absorber.

Rev D preserves the 30 mm-tall, 40 mm-bore, removable-bucket packaging of the
earlier D-squat study.  It replaces the legacy lumped slot sizing with the
repository's checked parallel-plate viscous model and deliberately treats slit
end correction as an uncertainty range rather than a known constant.

All CAD dimensions are millimetres; acoustic calculations use SI units.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Pos,
    Rot,
    Unit,
    export_step,
    import_step,
)

from experiments.sand_cube_190x210_port_absorber_slotted_d_squat import (
    duct as duct_model,
)
from experiments.sand_cube_190x210_port_absorber_slotted_d_squat import (
    generate_port_absorber_slotted_d_squat as base,
)
from experiments.sand_cube_190x210_port_absorber_slotted_d_squat import (
    model as slit_model,
)


OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_slotted_d_squat_rev_d"


@dataclass(frozen=True)
class Design(base.Design):
    name: str = "sand_cube_190x210_port_absorber_slotted_d_squat_rev_d_v1"

    # The integrated internal route currently measures 508.082 mm in CAD.  Its
    # bare first mode is 338.25 Hz in the same 1-D model.  The pre-integration
    # 513.589 mm route remains documented as the 334.5 Hz baseline.
    main_port_physical_length_mm: float = 508.0815787648397
    target_absorber_frequency_hz: float = 338.25

    # The slot sits at the center of its local boss, not the 30 mm body.  This
    # gives equal axial land above and below the longer Rev D slit while leaving
    # the original 6 mm high common manifold above all four bosses untouched.
    slot_center_z: float = 12.0
    minimum_slot_land_mm: float = 2.0

    # The installed service straight is centered at path 276.882 mm.  Moving
    # the slot from local z=15 to z=12 puts its opening at path 273.882 mm while
    # the connector/body envelope stays fixed.
    coupling_path_mm: float = 273.8815502462105
    integrated_body_center_path_mm: float = 276.8815502462105

    # Exposed uncertainty range for the *total* inertial correction at 0.4 mm.
    # Other witness widths scale the range by gap width.
    inertial_end_low_at_nominal_mm: float = 0.65
    inertial_end_high_at_nominal_mm: float = 1.50
    inertial_end_mid_at_nominal_mm: float = 1.10
    resistive_end_per_side_width_factor: float = 0.425
    reference_duct_attenuation_np_per_m: float = 0.10


D = Design()


def _branch(
    *, width_mm: float, length_mm: float, volume_cm3: float, end_total_mm: float,
    design: Design,
) -> slit_model.SlitBranch:
    return slit_model.SlitBranch(
        slot_count=design.rail_count,
        width_mm=width_mm,
        overall_length_mm=length_mm,
        physical_depth_mm=design.neck_physical_length,
        cavity_volume_cm3=volume_cm3,
        inertial_end_total_mm=end_total_mm,
        resistive_end_per_side_width_factor=(
            design.resistive_end_per_side_width_factor
        ),
    )


def _scaled_end_bounds(width_mm: float, design: Design) -> tuple[float, float]:
    scale = width_mm / design.nominal_finished_slot_width
    return (
        design.inertial_end_low_at_nominal_mm * scale,
        design.inertial_end_high_at_nominal_mm * scale,
    )


def _minimax_slot_length_mm(
    *, width_mm: float, volume_cm3: float, design: Design,
) -> float:
    """Balance endpoint frequency errors over the stated end range."""
    end_low, end_high = _scaled_end_bounds(width_mm, design)
    low = max(width_mm * 1.01, 1.0)
    high = 30.0
    for _ in range(100):
        middle = (low + high) / 2.0
        endpoint_average = sum(
            slit_model.resonance_frequency_hz(
                _branch(
                    width_mm=width_mm,
                    length_mm=middle,
                    volume_cm3=volume_cm3,
                    end_total_mm=end_total,
                    design=design,
                )
            )
            for end_total in (end_low, end_high)
        ) / 2.0
        if endpoint_average < design.target_absorber_frequency_hz:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _witness_tools(
    *, target_lengths: dict[float, float], design: Design,
) -> list[Any]:
    shift_z = design.slot_center_z - design.overall_length / 2.0
    return [
        Pos(0, 0, shift_z) * tool
        for tool in base.acoustic._witness_tools(
            target_lengths=target_lengths,
            design=design,
        )
    ]


def _calibration_coupon(nominal_length_mm: float, design: Design) -> Any:
    """Exact-section coupon with one full-length nominal Rev D pilot path."""
    height = design.coupon_height
    floor = base.acoustic.bucket_base._shell(
        design.outer_r,
        design.bore_r,
        design.coupon_floor_t,
    )
    core = base.acoustic.bucket_base._shell(
        design.core_outer_r,
        design.bore_r,
        height,
    )
    coupon = (floor + core).clean().fix()
    rail_height = height - 2.0 * design.coupon_floor_t
    for index in range(design.rail_count):
        angle = design.rail_angle_offset_deg + 360.0 * index / design.rail_count
        rail = Box(
            design.rail_radial_depth,
            design.rail_tangential_width,
            rail_height,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        rail = (
            Rot(0, 0, angle)
            * Pos(
                design.core_outer_r - design.rail_core_overlap,
                0,
                design.coupon_floor_t,
            )
            * rail
        )
        coupon = (coupon + rail).clean().fix()
        test_length = (
            nominal_length_mm if index == 0 else design.pilot_slot_length
        )
        test_tool = base.acoustic._radial_racetrack_tool(
            angle_deg=angle,
            z=height / 2.0,
            width=design.coupon_slot_widths[index],
            overall_length=test_length,
            design=design,
        )
        coupon = (coupon - test_tool).clean().fix()
    return coupon


def _build_geometry(design: Design) -> dict[str, Any]:
    blank = base._core_blank(design)
    bucket = base._bucket(design)
    cavity = base._cavity_bulk(design)
    cavity_solids = list(cavity.solids())
    if len(cavity_solids) != 1:
        raise ValueError(f"Expected one common D cavity, got {len(cavity_solids)}")
    volume_cm3 = cavity_solids[0].volume / 1000.0

    target_lengths = {
        width: _minimax_slot_length_mm(
            width_mm=width,
            volume_cm3=volume_cm3,
            design=design,
        )
        for width in design.witness_slot_widths
    }
    nominal_length = target_lengths[design.nominal_finished_slot_width]
    slot_low = design.slot_center_z - nominal_length / 2.0
    slot_high = design.slot_center_z + nominal_length / 2.0
    lower_land = slot_low - design.slot_boss_z_min
    upper_land = design.slot_boss_z_max - slot_high
    if min(lower_land, upper_land) < design.minimum_slot_land_mm:
        raise ValueError("Rev D slot lacks required land inside its local boss")

    pilot_tools = base.acoustic._slot_tools(
        width=design.pilot_slot_width,
        overall_length=design.pilot_slot_length,
        design=design,
        z=design.slot_center_z,
    )
    nominal_tools = base.acoustic._slot_tools(
        width=design.nominal_finished_slot_width,
        overall_length=nominal_length,
        design=design,
        z=design.slot_center_z,
    )
    witness_tools = _witness_tools(
        target_lengths=target_lengths,
        design=design,
    )
    marked_blank = base.acoustic._subtract_tools(blank, witness_tools)
    core_pilot = base.acoustic._subtract_tools(marked_blank, pilot_tools)
    core_nominal = base.acoustic._subtract_tools(marked_blank, nominal_tools)
    if not core_pilot.is_valid or not core_nominal.is_valid:
        raise ValueError("Rev D pilot or nominal core is invalid")

    airway = Cylinder(
        design.bore_r,
        design.overall_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pilot_air_domain = (airway + cavity).clean().fix()
    nominal_air_domain = (airway + cavity).clean().fix()
    for tool in pilot_tools:
        pilot_air_domain = (pilot_air_domain + tool).clean().fix()
    for tool in nominal_tools:
        nominal_air_domain = (nominal_air_domain + tool).clean().fix()

    adapters: dict[str, Any] = {}
    connected: dict[str, Any] = {}
    installed: dict[str, tuple[Any, Any]] = {}
    for tube_wall_t in design.adapter_tube_wall_variants:
        key = f"{tube_wall_t:g}mm_wall"
        adapter = base._tube_socket_adapter(tube_wall_t, design)
        bottom = Rot(180, 0, 0) * adapter
        top = Pos(0, 0, design.overall_length) * adapter
        adapters[key] = adapter
        installed[key] = (bottom, top)
        connected[key] = Compound(children=[core_nominal, bucket, bottom, top])

    default_key = "3mm_wall"
    bottom_adapter, top_adapter = installed[default_key]
    connected_parts = [core_nominal, bucket, bottom_adapter, top_adapter]
    connected_fused = Compound(children=connected_parts)
    total_z_min = -(design.adapter_plate_t + design.adapter_socket_depth)
    total_height = design.overall_length + 2.0 * (
        design.adapter_plate_t + design.adapter_socket_depth
    )
    keep = Pos(0, 0, total_z_min) * Box(
        2.5 * design.d_outer_arc_radius,
        1.25 * design.d_outer_arc_radius,
        total_height,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    cutaway_solids: list[Any] = []
    for part in connected_parts:
        cutaway_solids.extend(list((part & keep).solids()))
    cutaway = Compound(children=cutaway_solids)

    exploded = Compound(
        children=[
            Pos(-60, 0, 0) * core_pilot,
            Pos(60, 0, 0) * bucket,
            Pos(-60, 0, -22) * adapters[default_key],
            Pos(60, 0, 43) * adapters[default_key],
        ]
    )
    coupon = _calibration_coupon(nominal_length, design)
    inverted_bucket = Rot(180, 0, 0) * bucket
    bucket_min_z = inverted_bucket.bounding_box().min.Z
    print_layout = Compound(
        children=[
            Pos(-105, 0, 0) * core_pilot,
            Pos(-10, 0, -bucket_min_z) * inverted_bucket,
            Pos(80, -38, 0) * adapters[default_key],
            Pos(80, 38, 0) * adapters[default_key],
            Pos(145, 0, 0) * coupon,
        ]
    )

    extended_airway = Pos(0, 0, total_z_min) * Cylinder(
        design.bore_r,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return {
        "blank": blank,
        "core_pilot": core_pilot,
        "core_nominal": core_nominal,
        "bucket": bucket,
        "cavity_bulk": cavity,
        "cavity_volume_cm3": volume_cm3,
        "airway": airway,
        "extended_airway": extended_airway,
        "pilot_tools": pilot_tools,
        "nominal_tools": nominal_tools,
        "pilot_air_domain": pilot_air_domain,
        "nominal_air_domain": nominal_air_domain,
        "nominal_slot_length_mm": nominal_length,
        "target_lengths_by_width_mm": target_lengths,
        "slot_lands_mm": {"lower": lower_land, "upper": upper_land},
        "adapters": adapters,
        "connected": connected,
        "default_adapter_key": default_key,
        "assembly_pilot": Compound(children=[core_pilot, bucket]),
        "assembly_nominal": Compound(children=[core_nominal, bucket]),
        "connected_fused": connected_fused,
        "cutaway": cutaway,
        "exploded": exploded,
        "coupon": coupon,
        "print_layout": print_layout,
    }


def _step_roundtrip(exports: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        source_solids = list(shape.solids())
        imported_solids = list(imported.solids())
        row = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(source_solids) == len(imported_solids),
            "all_imported_solids_valid": all(
                solid.is_valid for solid in imported_solids
            ),
        }
        results[filename] = row
        if not row["solid_count_matches"] or not row["all_imported_solids_valid"]:
            raise ValueError(f"STEP round-trip failed for {filename}")
    return results


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    design = base._solve_arc_radius(D)
    base._validate_design(design)
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_geometry(design)
    volume_cm3 = geometry["cavity_volume_cm3"]
    nominal_length = geometry["nominal_slot_length_mm"]

    nominal_branch = _branch(
        width_mm=design.nominal_finished_slot_width,
        length_mm=nominal_length,
        volume_cm3=volume_cm3,
        end_total_mm=design.inertial_end_mid_at_nominal_mm,
        design=design,
    )
    pilot_branch = _branch(
        width_mm=design.pilot_slot_width,
        length_mm=design.pilot_slot_length,
        volume_cm3=volume_cm3,
        end_total_mm=(
            design.inertial_end_mid_at_nominal_mm
            * design.pilot_slot_width
            / design.nominal_finished_slot_width
        ),
        design=design,
    )
    nominal_properties = slit_model.evaluate(
        nominal_branch,
        reference_hz=design.target_absorber_frequency_hz,
    )
    pilot_properties = slit_model.evaluate(
        pilot_branch,
        reference_hz=design.target_absorber_frequency_hz,
    )

    end_cases: dict[str, dict[str, float]] = {}
    for end_total in (
        design.inertial_end_low_at_nominal_mm,
        design.inertial_end_mid_at_nominal_mm,
        design.inertial_end_high_at_nominal_mm,
    ):
        branch = _branch(
            width_mm=design.nominal_finished_slot_width,
            length_mm=nominal_length,
            volume_cm3=volume_cm3,
            end_total_mm=end_total,
            design=design,
        )
        evaluated = slit_model.evaluate(
            branch,
            reference_hz=design.target_absorber_frequency_hz,
        )
        end_cases[f"{end_total:g}_mm"] = {
            "resonance_hz": evaluated["resonance_frequency_hz"],
            "q": evaluated["resonance_q_from_reactance_slope"],
            "resistance_over_z0": evaluated["resistance_over_duct_impedance"],
        }

    port = duct_model.Port(
        length_mm=design.main_port_physical_length_mm,
        attenuation_np_per_m=design.reference_duct_attenuation_np_per_m,
    )
    duct_summary, duct_rows, pressure_rows = duct_model.summarize(
        nominal_branch,
        branch_path_mm=design.coupling_path_mm,
        port=port,
    )

    prefix = "port_absorber_d_squat_rev_d"
    nominal_token = f"{design.nominal_finished_slot_width:.2f}".replace(".", "p")
    exports = {
        f"{prefix}_inner_core_pilot.step": geometry["core_pilot"],
        f"{prefix}_inner_core_{nominal_token}_finished_reference.step": (
            geometry["core_nominal"]
        ),
        f"{prefix}_outer_bucket.step": geometry["bucket"],
        f"{prefix}_socket_adapter_40id_46od.step": geometry["adapters"]["3mm_wall"],
        f"{prefix}_socket_adapter_40id_50od.step": geometry["adapters"]["5mm_wall"],
        f"{prefix}_assembly_finished_reference.step": geometry["assembly_nominal"],
        f"{prefix}_connected_46od_tubes.step": geometry["connected"]["3mm_wall"],
        f"{prefix}_connected_50od_tubes.step": geometry["connected"]["5mm_wall"],
        f"{prefix}_cutaway.step": geometry["cutaway"],
        f"{prefix}_exploded.step": geometry["exploded"],
        f"{prefix}_print_layout.step": geometry["print_layout"],
        f"{prefix}_air_domain_finished.step": geometry["nominal_air_domain"],
        f"{prefix}_calibration_coupon.step": geometry["coupon"],
    }
    roundtrip = _step_roundtrip(exports)

    diagnostics = base._diagnostics(
        geometry,
        design,
        nominal_properties,
        pilot_properties,
        {"status": "superseded by verified branch and duct model below"},
        {"status": "superseded by verified branch and duct model below"},
        roundtrip,
    )
    diagnostics["status"] = (
        "Rev D thermoviscous-minimax calibration geometry; not production-validated"
    )
    diagnostics["acoustic_target"].update(
        {
            "model_target_hz": design.target_absorber_frequency_hz,
            "provisional_pressure_antinode_mm_from_inlet": (
                duct_summary["bare_pressure_antinode_path_mm"]
            ),
            "placement_target_path_mm_from_inlet": design.coupling_path_mm,
            "integrated_body_center_path_mm_from_inlet": (
                design.integrated_body_center_path_mm
            ),
            "placement_tolerance_interpretation": (
                "With the existing integrated body position, the Rev D slit is "
                "3 mm toward the inlet from the body center.  Its modeled "
                "pressure coupling remains about 0.993; measure the bare port "
                "before treating 338.25 Hz as authoritative."
            ),
        }
    )
    diagnostics["slot_layout"] = {
        "slot_center_z_mm": design.slot_center_z,
        "boss_z_min_mm": design.slot_boss_z_min,
        "boss_z_max_mm": design.slot_boss_z_max,
        "axial_lands_mm": geometry["slot_lands_mm"],
        "neck_air_volume_total_mm3": (
            nominal_branch.total_area_m2
            * 1e6
            * design.neck_physical_length
        ),
    }
    diagnostics["verified_acoustic_model"] = {
        "nominal_mid_end_case": nominal_properties,
        "end_correction_cases": end_cases,
        "reference_duct_case": duct_summary,
        "model_limitations": [
            "Parallel-plate viscous density; no thermal bulk-modulus correction.",
            "End correction is swept and remains the dominant linear uncertainty.",
            "One-dimensional duct uses bend centerline length only.",
            "Reference 0.1 Np/m loss is hypothetical; dB values are not predictions.",
            "No leakage, wall compliance, 3-D entrance flow, or nonlinear jetting.",
        ],
    }
    diagnostics["manufacturing_caveats"] = [
        "The 0.30 mm printed pilots are sacrificial guides, not trusted dimensions.",
        "Measure the finished 0.40 mm gap with feeler gauges at several heights.",
        "Coupon rail 1 carries a full 8.87 mm-class slot; other rails screen gap width.",
        "The removable bucket needs a real gasket and positive external retention.",
        "The socket plates are fit interfaces, not yet a validated structural tower joint.",
    ]
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=False) + "\n"
    )
    _write_csv(OUT / "verified_duct_response.csv", duct_rows)
    _write_csv(OUT / "verified_pressure_profile.csv", pressure_rows)

    for source, viewer_name in (
        (f"{prefix}_connected_46od_tubes.step", "viewer"),
        (f"{prefix}_cutaway.step", "cutaway_viewer"),
        (f"{prefix}_exploded.step", "exploded_viewer"),
        (f"{prefix}_print_layout.step", "print_layout_viewer"),
    ):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source),
                "--out",
                str(OUT / viewer_name),
            ],
            check=True,
        )

    print(f"Rev D assembly: {OUT / f'{prefix}_assembly_finished_reference.step'}")
    print(f"Rev D cutaway: {OUT / f'{prefix}_cutaway.step'}")
    print(f"Diagnostics: {OUT / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
