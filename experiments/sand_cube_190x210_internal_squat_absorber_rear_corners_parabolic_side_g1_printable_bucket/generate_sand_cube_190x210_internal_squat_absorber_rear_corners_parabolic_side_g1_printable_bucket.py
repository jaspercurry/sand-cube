"""Generate a rear-bed bucket and separate parabolic conformal front baffle.

The committed conformal full-system experiment remains unchanged.  This
isolated sibling reuses that complete feature pipeline, fills only the rear
sand gap, and then partitions the finished enclosure at the exact exterior G1
tangent boundary.  The hidden split slopes inward to the preserved driver
collar plane so both the collar and an inset perimeter can sit on the baffle's
print bed.
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

import copy
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from build123d import (
    Axis,
    Compound,
    Edge,
    GeomType,
    Pos,
    Solid,
    Unit,
    Wire,
    export_step,
    import_step,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_conformal_full_system"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_full_system as parent  # noqa: E402


base = parent.base
shell_source = parent.shell_source
cad = shell_source.cad
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_printable_bucket"
)
NAME = "sand_cube_190x210_parabolic_g1_printable_bucket"

PERIMETER_INSET_MM = 3.5
HIDDEN_FIT_CLEARANCE_MM = 0.30
ENVELOPE_FRONT_OVERTRAVEL_MM = 2.0
EXPLODED_BAFFLE_OFFSET_MM = 35.0

ORIGINAL_DETAIL_BASE = parent._full_detail_base
_SOLID_REAR_DIAGNOSTICS: dict[str, Any] = {}


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    solids = shape.solids()
    if len(solids) != 1 or not _is_valid(solids[0]):
        raise ValueError(
            f"{feature} did not produce one valid solid: {len(solids)}"
        )
    return solids[0]


def _rear_sand_gap() -> Solid:
    gaps = base._sand_void().solids()
    rear_candidates = [
        solid
        for solid in gaps
        if solid.bounding_box().min.Y
        > base.D.center_y + base.D.depth / 2.0 - base.D.wall_stack_t
    ]
    if len(rear_candidates) != 1:
        raise ValueError(
            f"Expected one isolated rear sand gap, found {len(rear_candidates)}"
        )
    return copy.copy(rear_candidates[0])


def _rear_service_cutters(
    *,
    include_gx16: bool,
    include_fill_ports: bool,
) -> list[Any]:
    cutters: list[Any] = []
    if include_gx16:
        cutters.append(
            base._rear_shifted(base._gx16_rear_cutout_corner(base.P))
        )
    if include_fill_ports:
        cutters.extend(
            base._sand_fill_rear_bore(fill_x)
            for fill_x in (-base.P.fill_port_x, base.P.fill_port_x)
        )
    return cutters


def _solid_rear_detail_base(
    port_clearance: Any,
    port_install_clearance: Any,
    *,
    include_gx16: bool = True,
    include_fill_ports: bool = True,
) -> Any:
    """Fill the rear gap after the complete detailed base is constructed."""
    detailed = ORIGINAL_DETAIL_BASE(
        port_clearance,
        port_install_clearance,
        include_gx16=include_gx16,
        include_fill_ports=include_fill_ports,
    )
    rear_gap = _rear_sand_gap()
    cutters = _rear_service_cutters(
        include_gx16=include_gx16,
        include_fill_ports=include_fill_ports,
    )
    expected_fill: Any = copy.copy(rear_gap)
    for cutter in cutters:
        expected_fill = expected_fill.cut(cutter)

    filled = _single_solid(
        detailed.fuse(rear_gap).clean().fix(),
        feature="full-detail enclosure after solid rear fill",
    )
    for cutter in cutters:
        filled = _single_solid(
            filled.cut(cutter).clean().fix(),
            feature="solid rear after restored service opening",
        )

    unfilled_target = expected_fill.cut(filled)
    unfilled_target_volume = _shape_volume(unfilled_target)
    if unfilled_target_volume > 0.05:
        raise ValueError(
            "Solid rear left an unintended cavity of "
            f"{unfilled_target_volume:.6f} mm3"
        )
    _SOLID_REAR_DIAGNOSTICS.clear()
    _SOLID_REAR_DIAGNOSTICS.update(
        {
            "nominal_rear_gap_volume_mm3": rear_gap.volume,
            "service_opening_adjusted_fill_volume_mm3": _shape_volume(
                expected_fill
            ),
            "actual_enclosure_material_added_mm3": (
                filled.volume - detailed.volume
            ),
            "unfilled_non_service_rear_gap_volume_mm3": (
                unfilled_target_volume
            ),
            "gx16_opening_preserved": include_gx16,
            "fill_passages_preserved": (
                2 if include_fill_ports else 0
            ),
        }
    )
    return filled


def _curve_wire(
    targets: list[tuple[float, float, float]],
    *,
    feature: str,
) -> Wire:
    poles = shell_source.legacy._periodic_interpolation_poles(targets)
    curve = shell_source.legacy._curve_from_poles(poles)
    maker = BRepBuilderAPI_MakeEdge(curve)
    if not maker.IsDone():
        raise ValueError(f"Unable to build {feature} edge")
    edge = Edge.cast(maker.Edge())
    if edge is None or not edge.is_closed:
        raise ValueError(f"{feature} is not a closed edge")
    return Wire([edge])


def _split_envelope(*, hidden_clearance_mm: float) -> Solid:
    """Closed front envelope with the exact exterior tangent seam."""
    if not 0.0 <= hidden_clearance_mm < PERIMETER_INSET_MM:
        raise ValueError("Hidden clearance must be smaller than the inset")
    seam_targets = shell_source.parent._minimum_energy_control_rings()[-1]
    front_targets = [
        (
            x,
            shell_source.FRONT_Y - ENVELOPE_FRONT_OVERTRAVEL_MM,
            z,
        )
        for x, _y, z in seam_targets
    ]
    bed_inset = PERIMETER_INSET_MM - hidden_clearance_mm
    bed_targets: list[tuple[float, float, float]] = []
    for x, _y, z in seam_targets:
        radius = math.hypot(x, z)
        scale = (radius - bed_inset) / radius
        bed_targets.append(
            (
                x * scale,
                shell_source.CAVITY_FRONT_Y,
                z * scale,
            )
        )

    builder = BRepOffsetAPI_ThruSections(True, False, 1e-7)
    builder.CheckCompatibility(True)
    for targets, feature in (
        (front_targets, "front overtravel split section"),
        (seam_targets, "exact G1 tangent seam"),
        (bed_targets, "inset baffle bed perimeter"),
    ):
        builder.AddWire(
            _curve_wire(targets, feature=feature).wrapped
        )
    builder.Build()
    if not builder.IsDone():
        raise ValueError("Unable to build the tapered baffle split envelope")
    envelope = Solid.cast(builder.Shape())
    if envelope is None:
        raise ValueError("Unable to cast the tapered split envelope")
    envelope = _single_solid(
        envelope.clean().fix(),
        feature="tapered baffle split envelope",
    )
    if envelope.volume <= 0.0:
        raise ValueError("Tapered baffle split envelope has no volume")
    return envelope


def _split_enclosure(full_base: Solid) -> dict[str, Any]:
    nominal_envelope = _split_envelope(hidden_clearance_mm=0.0)
    clearance_envelope = _split_envelope(
        hidden_clearance_mm=HIDDEN_FIT_CLEARANCE_MM
    )
    baffle = _single_solid(
        full_base.intersect(nominal_envelope).clean().fix(),
        feature="separate parabolic conformal front baffle",
    )
    bucket = _single_solid(
        full_base.cut(clearance_envelope).clean().fix(),
        feature="rear-bed printable enclosure bucket",
    )
    overlap_volume = _shape_volume(baffle.intersect(bucket))
    if overlap_volume > 0.01:
        raise ValueError(
            f"Bucket and baffle overlap by {overlap_volume:.6f} mm3"
        )
    # Sequentially subtracting both periodic split results from the source is
    # not a stable OCCT coverage test: the second complemented boolean can
    # reclassify the remaining source shell.  The robust allowance measurement
    # is the direct volume delta between otherwise identical zero-clearance and
    # fit-clearance bucket cuts.
    nominal_bucket = _single_solid(
        full_base.cut(nominal_envelope).clean().fix(),
        feature="zero-clearance reference bucket",
    )
    fit_gap_volume = max(0.0, nominal_bucket.volume - bucket.volume)
    if fit_gap_volume <= 0.0:
        raise ValueError("Hidden baffle clearance did not remove bucket material")

    target_fairing_area = parent._build_parabolic_conformal_geometry()[
        "outer_fairing_area_mm2"
    ]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_fairing_area) <= 1e-5
    ]
    if len(fairing_faces) != 1:
        raise ValueError(
            "The split changed the exact exterior fairing face: "
            f"found {len(fairing_faces)} matches"
        )
    large_radii = sorted(
        {
            round(edge.radius, 6)
            for edge in baffle.edges()
            if edge.geom_type == GeomType.CIRCLE and edge.radius > 50.0
        }
    )
    for required_radius in (65.25, 79.0, 87.0):
        if not any(
            abs(radius - required_radius) <= 1e-6
            for radius in large_radii
        ):
            raise ValueError(
                f"Separate baffle lost the R{required_radius:g} interface"
            )

    seam_depths = [
        target[1] for target in shell_source.parent._minimum_energy_control_rings()[-1]
    ]
    minimum_print_rise = (
        shell_source.CAVITY_FRONT_Y - max(seam_depths)
    )
    worst_overhang = math.degrees(
        math.atan2(PERIMETER_INSET_MM, minimum_print_rise)
    )
    return {
        "bucket": bucket,
        "baffle": baffle,
        "overlap_volume_mm3": overlap_volume,
        "fit_gap_volume_mm3": fit_gap_volume,
        "fairing_face_area_mm2": fairing_faces[0].area,
        "fairing_area_difference_mm2": (
            fairing_faces[0].area - target_fairing_area
        ),
        "large_circular_interface_radii_mm": large_radii,
        "minimum_print_rise_mm": minimum_print_rise,
        "worst_overhang_from_print_axis_deg": worst_overhang,
    }


def _print_oriented_bucket(bucket: Solid) -> Solid:
    rotated = bucket.rotate(Axis.X, -90.0)
    return copy.copy(rotated).moved(Pos(0.0, 0.0, 115.0))


def _print_oriented_baffle(baffle: Solid) -> Solid:
    rotated = baffle.rotate(Axis.X, -90.0)
    return copy.copy(rotated).moved(
        Pos(0.0, 0.0, shell_source.CAVITY_FRONT_Y)
    )


def _replace_base_in_assembly(
    assembly: Any,
    original_base: Solid,
    bucket: Solid,
    baffle: Solid,
) -> Compound:
    original_bbox = original_base.bounding_box()
    candidates = []
    retained = []
    for solid in assembly.solids():
        bbox = solid.bounding_box()
        if (
            abs(solid.volume - original_base.volume) <= 2.0
            and abs(bbox.size.X - original_bbox.size.X) <= 0.01
            and abs(bbox.size.Y - original_bbox.size.Y) <= 0.01
            and abs(bbox.size.Z - original_bbox.size.Z) <= 0.01
        ):
            candidates.append(solid)
        else:
            retained.append(copy.copy(solid))
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one full base in inherited assembly, found {len(candidates)}"
        )
    return Compound(
        children=[copy.copy(bucket), copy.copy(baffle), *retained]
    )


def _true_split_cutaway(
    bucket: Solid,
    baffle: Solid,
    inherited_cutaway: Any,
) -> Compound:
    bucket_half = shell_source._geometric_half_cutaway(bucket)
    baffle_half = shell_source._geometric_half_cutaway(baffle)
    return Compound(
        children=[
            *[copy.copy(face) for face in bucket_half.faces()],
            *[copy.copy(face) for face in baffle_half.faces()],
            *[copy.copy(solid) for solid in inherited_cutaway.solids()],
        ]
    )


def _export_and_check(exports: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        source_solids = shape.solids()
        imported_solids = imported.solids()
        source_faces = shape.faces()
        imported_faces = imported.faces()
        check = {
            "source_solid_count": len(source_solids),
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(source_solids) == len(imported_solids),
            "source_face_count": len(source_faces),
            "imported_face_count": len(imported_faces),
            "face_count_matches": len(source_faces) == len(imported_faces),
            "all_imported_solids_valid": all(
                _is_valid(solid) for solid in imported_solids
            ),
            "all_imported_faces_valid": all(
                _is_valid(face) for face in imported_faces
            ),
        }
        checks[filename] = check
        if not all(
            (
                check["solid_count_matches"],
                check["face_count_matches"],
                check["all_imported_solids_valid"],
                check["all_imported_faces_valid"],
            )
        ):
            raise ValueError(f"STEP round trip failed for {filename}: {check}")
    return checks


def _configure_viewer(viewer_dir: Path, *, cutaway: bool = False) -> None:
    cad._set_viewer_edge_mode(viewer_dir, face_only=False)
    model_data = viewer_dir / "model-data.js"
    payload = model_data.read_bytes()
    if cutaway:
        payload = payload.replace(
            b'"reset_camera":"iso"',
            (
                b'"reset_camera":"keep",'
                b'"position":[600.0,-350.0,350.0],'
                b'"target":[0.0,10.0,0.0],"zoom":1.0'
            ),
            1,
        )
        payload = payload.replace(
            b'"color":"#6ab7ff"',
            b'"color":"#e8b024"',
        )
        payload = payload.replace(
            b'"renderback":false',
            b'"renderback":true',
        )
    model_data.write_bytes(payload)


def _generate_viewers() -> None:
    for source_filename, viewer_name, cutaway in (
        ("printable_bucket_baffle_assembled.step", "viewer", False),
        ("printable_bucket_baffle_cutaway.step", "cutaway_viewer", True),
        ("printable_bucket_baffle_exploded.step", "exploded_viewer", False),
    ):
        viewer_dir = OUT / viewer_name
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source_filename),
                "--out",
                str(viewer_dir),
            ],
            check=True,
        )
        _configure_viewer(viewer_dir, cutaway=cutaway)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    for module in (
        parent,
        parent.source,
        parent.source.prior,
        parent.source.serviceable,
        parent.source.header,
        base,
    ):
        module.OUT = OUT
    base.D = replace(base.D, name=NAME)
    parent.NAME = NAME
    parent.OUT = OUT
    parent._GEOMETRY_CACHE = None
    parent._DETAIL_CUT_AUDITS.clear()
    parent._full_detail_base = _solid_rear_detail_base

    diagnostics = parent.generate()
    full_base_path = OUT / "sand_cube_190x210_single_oval_port_base.step"
    full_base = _single_solid(
        import_step(full_base_path),
        feature="round-tripped solid-rear full-detail enclosure",
    )
    split = _split_enclosure(full_base)
    bucket = split["bucket"]
    baffle = split["baffle"]

    assembled_shell = Compound(
        children=[copy.copy(bucket), copy.copy(baffle)]
    )
    exploded_shell = Compound(
        children=[
            copy.copy(bucket),
            copy.copy(baffle).moved(
                Pos(0.0, -EXPLODED_BAFFLE_OFFSET_MM, 0.0)
            ),
        ]
    )
    inherited_assembly = import_step(
        OUT / "sand_cube_190x210_single_oval_port_assembly.step"
    )
    split_full_assembly = _replace_base_in_assembly(
        inherited_assembly,
        full_base,
        bucket,
        baffle,
    )
    inherited_cutaway = import_step(
        OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
    )
    split_cutaway = _true_split_cutaway(
        bucket,
        baffle,
        inherited_cutaway,
    )
    bucket_print = _print_oriented_bucket(bucket)
    baffle_print = _print_oriented_baffle(baffle)

    exports = {
        "printable_bucket.step": bucket,
        "separate_front_baffle.step": baffle,
        "printable_bucket_print_orientation.step": bucket_print,
        "separate_front_baffle_print_orientation.step": baffle_print,
        "printable_bucket_baffle_assembled.step": assembled_shell,
        "printable_bucket_baffle_exploded.step": exploded_shell,
        "printable_bucket_baffle_full_system.step": split_full_assembly,
        "printable_bucket_baffle_cutaway.step": split_cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    baseline_net_l = diagnostics["volume_accounting"][
        "final_modeled_net_box_volume_l"
    ]
    port_length = diagnostics["port"]["lengths"][
        "physical_centerline_length_mm"
    ]
    tuning_hz = diagnostics["port"]["lengths"]["calculated_tuning_hz"]
    inherited_interferences = diagnostics["geometry"]["interference_mm3"]
    nonzero_inherited = {
        key: value
        for key, value in inherited_interferences.items()
        if abs(value) > 1e-6
    }
    if nonzero_inherited:
        raise ValueError(
            f"Inherited full-system interference returned: {nonzero_inherited}"
        )

    bucket_print_bbox = bucket_print.bounding_box()
    baffle_print_bbox = baffle_print.bounding_box()
    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete solid-rear printable bucket and separate conformal front "
        "baffle prototype"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_printable_bucket"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_printable_bucket"
        ),
        "committed_full_system_modified": False,
        "committed_bare_shell_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["printable_bucket_split"] = {
        "rear_wall": {
            "construction": "solid 7 mm wall, except preserved service holes",
            **_SOLID_REAR_DIAGNOSTICS,
            "side_and_roof_2_3_2_cavities_preserved": True,
        },
        "visible_seam": {
            "location": "exact G1 fairing-to-flat-wall tangent boundary",
            "exterior_seam_offset_mm": 0.0,
            "perimeter_inset_on_bed_mm": PERIMETER_INSET_MM,
            "hidden_fit_clearance_at_bed_mm": HIDDEN_FIT_CLEARANCE_MM,
            "hidden_fit_clearance_at_visible_seam_mm": 0.0,
            "fit_gap_volume_mm3": split["fit_gap_volume_mm3"],
            "bucket_to_baffle_interference_mm3": split[
                "overlap_volume_mm3"
            ],
        },
        "preserved_front": {
            "outer_fairing_face_area_mm2": split[
                "fairing_face_area_mm2"
            ],
            "outer_fairing_area_difference_mm2": split[
                "fairing_area_difference_mm2"
            ],
            "large_circular_interface_radii_mm": split[
                "large_circular_interface_radii_mm"
            ],
            "driver_collar_rear_plane_y_mm": (
                shell_source.CAVITY_FRONT_Y
            ),
            "black_hole_and_driver_insert_geometry_preserved": True,
            "conformal_inner_wall_preserved": True,
        },
        "print_orientation": {
            "bucket": "solid exterior rear face on Z=0 bed",
            "baffle": "driver collar and inset perimeter on Z=0 bed",
            "minimum_baffle_rise_at_pulled_corner_mm": split[
                "minimum_print_rise_mm"
            ],
            "worst_baffle_overhang_from_print_axis_deg": split[
                "worst_overhang_from_print_axis_deg"
            ],
            "bucket_print_bbox_min_z_mm": bucket_print_bbox.min.Z,
            "bucket_print_bbox_max_z_mm": bucket_print_bbox.max.Z,
            "baffle_print_bbox_min_z_mm": baffle_print_bbox.min.Z,
            "baffle_print_bbox_max_z_mm": baffle_print_bbox.max.Z,
            "supports_expected_for_split_shell_surfaces": False,
            "brim_recommended_for_3p5_mm_perimeter_land": True,
        },
        "assembly": {
            "bucket_solid_count": len(bucket.solids()),
            "baffle_solid_count": len(baffle.solids()),
            "assembled_shell_solid_count": len(assembled_shell.solids()),
            "split_full_system_solid_count": len(
                split_full_assembly.solids()
            ),
            "true_cutaway_face_count": len(split_cutaway.faces()),
        },
    }
    diagnostics["preserved_full_detail_contract"].update(
        {
            "dual_skin_2_3_2_walls": "side and roof only",
            "solid_rear_wall": True,
            "separate_front_baffle": True,
        }
    )
    diagnostics["manufacturing_effect"] = {
        "modeled_net_volume_l": baseline_net_l,
        "net_volume_change_from_committed_full_system_l": 0.0,
        "physical_port_length_mm": port_length,
        "port_length_change_mm": 0.0,
        "modeled_natural_tuning_hz": tuning_hz,
        "tuning_change_hz": 0.0,
        "inherited_zero_interference_check_count": len(
            inherited_interferences
        ),
        "new_bucket_baffle_interference_mm3": split[
            "overlap_volume_mm3"
        ],
        "rear_fill_is_outside_acoustic_domain": True,
    }
    diagnostics["geometry"]["printable_split_step_roundtrip"] = (
        step_roundtrip
    )
    diagnostics["files"].update(
        {
            **{filename: str(OUT / filename) for filename in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "index.html"),
            "cutaway_viewer": str(
                OUT / "cutaway_viewer" / "index.html"
            ),
            "exploded_viewer": str(
                OUT / "exploded_viewer" / "index.html"
            ),
        }
    )
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2)
    )
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
