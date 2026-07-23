"""Generate the optional four-fin printability variant of the approved baffle."""

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
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
import math
import subprocess
import sys
from pathlib import Path

from build123d import (
    Align,
    Box,
    Edge,
    Face,
    Pos,
    Rot,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure as model  # noqa: E402


OUTPUT_ROOT = Path(
    "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
BASE_BAFFLE_STEP = ROOT / OUTPUT_ROOT / "centered_captive_nut_baffle.step"
BASE_BUCKET_STEP = ROOT / OUTPUT_ROOT / "centered_captive_nut_bucket.step"

FIN_ANGLES_DEG = (45.0, 135.0, 225.0, 315.0)
FIN_THICKNESS_MM = 1.60
FIN_INNER_RADIUS_MM = model.BRIDGE_INNER_RADIUS_MM
# Keep the fin crown inside the existing fairing skin while giving the boolean
# union a positive, printable overlap.  A deeper offset can land entirely in
# the hollow behind the thin fairing and leave the fin disconnected.
FIN_SKIN_EMBED_MM = 0.8
FIN_FUSE_TOLERANCE_MM = 0.02


def _shape_volume(shape) -> float:
    return model._shape_volume(shape)


def _bbox_deltas(reference, final) -> dict[str, float]:
    reference_box = reference.bounding_box()
    final_box = final.bounding_box()
    return {
        "min_x": final_box.min.X - reference_box.min.X,
        "max_x": final_box.max.X - reference_box.max.X,
        "min_y": final_box.min.Y - reference_box.min.Y,
        "max_y": final_box.max.Y - reference_box.max.Y,
        "min_z": final_box.min.Z - reference_box.min.Z,
        "max_z": final_box.max.Z - reference_box.max.Z,
    }


def _fuse_fin(shape: Solid, fin: Solid, *, feature: str) -> Solid:
    """Fuse through STEP face seams without changing nominal coordinates."""
    result = shape.fuse(fin, tol=FIN_FUSE_TOLERANCE_MM)
    if not hasattr(result, "clean"):
        raise ValueError(
            f"{feature} remained disconnected after tolerance-assisted fusion"
        )
    return model._single_solid(result.clean().fix(), feature=feature)


def _top_diagonal_fin() -> tuple[Solid, float, float]:
    """One open fin following the current acoustic-side inner wall."""
    inner_wall_source = model.parent.shell_source
    fairing_source = inner_wall_source.parent
    outer_surface = inner_wall_source._outer_fairing_surface()
    diagonal_parameter = fairing_source.ANGULAR_SAMPLE_COUNT / 8.0
    half_thickness = FIN_THICKNESS_MM / 2.0
    crown_points = []
    sample_count = 17
    for index in range(sample_count):
        v_parameter = (
            inner_wall_source.CONFORMAL_STOP_V
            * index
            / (sample_count - 1)
        )
        inner_point = inner_wall_source._exact_inward_offset_point(
            outer_surface,
            diagonal_parameter,
            v_parameter,
        )
        outer_point = outer_surface.Value(diagonal_parameter, v_parameter)
        outer_coordinates = (
            outer_point.X(),
            outer_point.Y(),
            outer_point.Z(),
        )
        embed_fraction = (
            FIN_SKIN_EMBED_MM / inner_wall_source.WALL_THICKNESS_MM
        )
        crown = tuple(
            float(inner_coordinate)
            + (float(outer_coordinate) - float(inner_coordinate))
            * embed_fraction
            for inner_coordinate, outer_coordinate in zip(
                inner_point,
                outer_coordinates,
            )
        )
        crown_points.append(
            (
                -half_thickness,
                crown[1],
                math.hypot(crown[0], crown[2]),
            )
        )

    outer_radius = crown_points[-1][2]
    inner_bed = (
        -half_thickness,
        model.source.BAFFLE_BED_Y,
        FIN_INNER_RADIUS_MM,
    )
    outer_bed = (
        -half_thickness,
        model.source.BAFFLE_BED_Y,
        outer_radius,
    )
    inner_collar_top = (
        -half_thickness,
        crown_points[0][1],
        FIN_INNER_RADIUS_MM,
    )
    edges = [
        Edge.make_line(inner_bed, outer_bed),
        Edge.make_line(outer_bed, crown_points[-1]),
        Edge.make_spline(
            crown_points,
            tangents=[
                Vector(crown_points[1]) - Vector(crown_points[0]),
                Vector(crown_points[-1]) - Vector(crown_points[-2]),
            ],
        ).reversed(),
        Edge.make_line(crown_points[0], inner_collar_top),
        Edge.make_line(inner_collar_top, inner_bed),
    ]
    wires = Wire.combine(edges)
    if len(wires) != 1 or not wires[0].is_closed:
        raise ValueError("The diagonal print-fin profile did not close")
    profile = Face(wires[0])
    if profile.area <= 0.01:
        raise ValueError("The diagonal print-fin profile has no area")
    fin = model._single_solid(
        Solid.extrude(
            profile,
            Vector(FIN_THICKNESS_MM, 0.0, 0.0),
        ).clean().fix(),
        feature="acoustic-inner-wall diagonal print fin",
    )
    collar_contact_height = model.source.BAFFLE_BED_Y - crown_points[0][1]
    return fin, outer_radius, collar_contact_height


def main() -> None:
    if not BASE_BAFFLE_STEP.is_file() or not BASE_BUCKET_STEP.is_file():
        raise FileNotFoundError("Build the approved captive-nut baffle first")

    base_baffle = model._single_solid(
        import_step(BASE_BAFFLE_STEP),
        feature="approved centered-slot baffle reference",
    )
    base_bucket = model._single_solid(
        import_step(BASE_BUCKET_STEP),
        feature="approved restored bucket reference",
    )
    base_bounds = base_baffle.bounding_box()
    y_min = base_bounds.min.Y
    y_max = model.source.BAFFLE_BED_Y
    top_fin, outer_radius, collar_contact_height = _top_diagonal_fin()

    keepout_parts = []
    for z_sign in (-1.0, 1.0):
        surface = model._fastener_surface(z_sign)
        nut_center = (
            surface
            + model._fastener_direction(z_sign) * model.NUT_AXIS_DISTANCE_MM
        )
        nut_access, _mouth, nominal_sweep, _seat, _rotation, _dot = (
            model._nut_loading_access(nut_center, z_sign=z_sign)
        )
        keepout_parts.extend((nut_access, nominal_sweep))

    driver_keepout = model.source._cylinder_between(
        Vector(0.0, y_min - 0.10, 0.0),
        Vector(0.0, y_max + 0.10, 0.0),
        diameter=2.0 * (FIN_INNER_RADIUS_MM - 0.10),
    )
    bed_probe = Pos(0.0, y_max - 0.125, 0.0) * Box(
        260.0,
        0.25,
        260.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    variant = base_baffle
    fin_audits: list[dict[str, float | int]] = []
    raw_fins = []
    for index, angle_deg in enumerate(FIN_ANGLES_DEG, start=1):
        fin = model._single_solid(
            (Rot(0.0, angle_deg, 0.0) * top_fin).clean().fix(),
            feature=f"diagonal conformal print fin {index}",
        )
        driver_overlap = _shape_volume(fin.intersect(driver_keepout))
        functional_overlap = sum(
            _shape_volume(fin.intersect(keepout)) for keepout in keepout_parts
        )
        bed_contact = _shape_volume(fin.intersect(bed_probe))
        if driver_overlap > 0.001:
            raise ValueError(f"Print fin {index} enters the driver opening")
        if functional_overlap > 0.001:
            raise ValueError(f"Print fin {index} enters a nut-loading keepout")
        if bed_contact <= 0.01:
            raise ValueError(
                f"Print fin {index} lacks a continuous printer-bed root"
            )
        baffle_overlap = _shape_volume(fin.intersect(base_baffle))
        if baffle_overlap <= 0.01:
            raise ValueError(
                f"Print fin {index} does not overlap the approved baffle skin"
            )
        print(
            f"Validated fin {index}; skin overlap "
            f"{baffle_overlap:.6f} mm3; fusing into the approved baffle"
        )
        raw_fins.append(fin)
        variant = _fuse_fin(
            variant,
            fin,
            feature=f"baffle with diagonal conformal print fin {index}",
        )
        print(f"Fused fin {index} into one valid baffle solid")
        fin_audits.append(
            {
                "index": index,
                "angle_deg": angle_deg,
                "candidate_volume_mm3": fin.volume,
                "bed_contact_mm3": bed_contact,
                "baffle_skin_overlap_mm3": baffle_overlap,
                "driver_keepout_overlap_mm3": driver_overlap,
                "nut_loading_keepout_overlap_mm3": functional_overlap,
            }
        )

    if len(variant.solids()) != 1 or not variant.is_valid:
        raise ValueError("The finned baffle is not one valid solid")

    exterior_deltas = _bbox_deltas(base_baffle, variant)
    if max(abs(value) for value in exterior_deltas.values()) > 1e-5:
        raise ValueError(f"Fins changed the baffle exterior bounds: {exterior_deltas}")

    bucket_overlap = _shape_volume(variant.intersect(base_bucket))
    if bucket_overlap > model.MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            f"The finned baffle intersects the restored bucket by {bucket_overlap} mm3"
        )

    original_bypass_depth = model.single.SCREW_BYPASS_DEPTH_MM
    model.single.SCREW_BYPASS_DEPTH_MM = model.SERVICE_BYPASS_DEPTH_MM
    try:
        gasket = model.single._single_face_band(
            model.GASKET_WIDTH_MM,
            model.source.BAFFLE_BED_Y,
            model.source.SHOULDER_Y,
            feature="current gasket reference for fin audit",
        )
    finally:
        model.single.SCREW_BYPASS_DEPTH_MM = original_bypass_depth
    fin_gasket_overlap = _shape_volume(
        model.Compound(children=raw_fins).intersect(gasket)
    )
    if fin_gasket_overlap > 0.001:
        raise ValueError(f"Print fins interrupt the gasket by {fin_gasket_overlap} mm3")

    added_volume_mm3 = variant.volume - base_baffle.volume
    if added_volume_mm3 <= 0.01:
        raise ValueError("The printability variant added no material")
    added_volume_l = added_volume_mm3 / 1_000_000.0

    step_path = job_output_path(
        OUTPUT_ROOT / "centered_captive_nut_baffle_finned_variant.step"
    )
    step_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(variant, step_path, unit=Unit.MM, write_pcurves=True)
    imported = import_step(step_path)
    roundtrip = {
        "source_solid_count": len(variant.solids()),
        "imported_solid_count": len(imported.solids()),
        "all_imported_solids_valid": all(
            solid.is_valid for solid in imported.solids()
        ),
    }
    if roundtrip != {
        "source_solid_count": 1,
        "imported_solid_count": 1,
        "all_imported_solids_valid": True,
    }:
        raise ValueError(f"Finned STEP round trip failed: {roundtrip}")

    viewer_path = job_output_path(OUTPUT_ROOT / "baffle_finned_viewer")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
            str(step_path),
            "--out",
            str(viewer_path),
        ],
        check=True,
    )
    model.centered._configure_viewer(viewer_path, cutaway=False)

    diagnostics = {
        "scope": "optional four-diagonal-fin printability baffle variant",
        "source_baffle_step": str(BASE_BAFFLE_STEP),
        "accepted_baffle_preserved": True,
        "fin_count": len(FIN_ANGLES_DEG),
        "fin_angles_deg": list(FIN_ANGLES_DEG),
        "fin_thickness_mm": FIN_THICKNESS_MM,
        "fin_inner_radius_mm": FIN_INNER_RADIUS_MM,
        "fin_outer_radius_mm": outer_radius,
        "fin_full_collar_contact_height_mm": collar_contact_height,
        "fin_skin_embed_mm": FIN_SKIN_EMBED_MM,
        "fin_fuse_tolerance_mm": FIN_FUSE_TOLERANCE_MM,
        "construction": (
            "four open bed-grown radial walls following the current diagonal "
            "acoustic-side conformal inner wall and embedded into that skin"
        ),
        "closed_ring_count": 0,
        "honeycomb_cell_count": 0,
        "floating_fin_end_count": 0,
        "added_material_volume_mm3": added_volume_mm3,
        "added_material_volume_l": added_volume_l,
        "added_volume_percent_of_current_net": (
            100.0 * added_volume_l / model.CURRENT_SYSTEMIC_NET_VOLUME_L
        ),
        "revised_estimated_net_volume_l": (
            model.CURRENT_SYSTEMIC_NET_VOLUME_L - added_volume_l
        ),
        "baffle_exterior_bounds_difference_mm": exterior_deltas,
        "bucket_overlap_mm3": bucket_overlap,
        "gasket_overlap_mm3": fin_gasket_overlap,
        "fins": fin_audits,
        "step_roundtrip": roundtrip,
    }
    diagnostics_path = job_output_path(
        OUTPUT_ROOT / "baffle_finned_variant_diagnostics.json"
    )
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
