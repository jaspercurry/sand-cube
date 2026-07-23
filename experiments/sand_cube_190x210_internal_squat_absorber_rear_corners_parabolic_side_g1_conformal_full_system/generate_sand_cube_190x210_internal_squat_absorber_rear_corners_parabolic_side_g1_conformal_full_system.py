"""Combine the parabolic conformal shell with the complete rear-corner system.

The committed enclosure-only sibling remains the authoritative source for the
front exterior, black-hole collar, and conformal inner wall.  This generator
replaces only the rear-corner baseline's initial enclosure shell, then reuses
its complete feature pipeline and diagnostics for every brace, opening,
mounting provision, port part, absorber, tower, horn, and hardware envelope.
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
    Align,
    Box,
    Compound,
    GeomType,
    Part,
    Pos,
    Unit,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners"
)
SHELL_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_inner_wall"
)
for module_dir in (SOURCE_EXPERIMENT, SHELL_EXPERIMENT):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners as source  # noqa: E402
import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_inner_wall as shell_source  # noqa: E402


base = source.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_full_system"
)
NAME = "sand_cube_190x210_rear_corners_parabolic_g1_conformal_full_system"

for module in (
    source,
    source.prior,
    source.serviceable,
    source.header,
    base,
):
    module.OUT = OUT

base.D = replace(base.D, name=NAME)

ORIGINAL_ACOUSTIC_DOMAIN = base._acoustic_domain
ORIGINAL_FRONT_BRACE_BLENDS = base._front_brace_blends
_GEOMETRY_CACHE: dict[str, Any] | None = None
_DETAIL_CUT_AUDITS: dict[str, Any] = {}


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _build_parabolic_conformal_geometry() -> dict[str, Any]:
    global _GEOMETRY_CACHE
    if _GEOMETRY_CACHE is not None:
        return _GEOMETRY_CACHE

    outer_cutter, outer_fairing_face, outer_fairing_topology = (
        shell_source.parent._g1_cutter()
    )
    outer_boundary_targets = [
        (
            shell_source.legacy._outer_radius(
                math.tau
                * index
                / shell_source.parent.ANGULAR_SAMPLE_COUNT
            )
            * math.cos(
                math.tau
                * index
                / shell_source.parent.ANGULAR_SAMPLE_COUNT
            ),
            shell_source.FRONT_Y,
            shell_source.legacy._outer_radius(
                math.tau
                * index
                / shell_source.parent.ANGULAR_SAMPLE_COUNT
            )
            * math.sin(
                math.tau
                * index
                / shell_source.parent.ANGULAR_SAMPLE_COUNT
            ),
        )
        for index in range(shell_source.parent.ANGULAR_SAMPLE_COUNT)
    ]
    outer_boundary_poles = shell_source.legacy._periodic_interpolation_poles(
        outer_boundary_targets
    )
    body, body_topology = shell_source.legacy._outer_body(
        outer_boundary_poles
    )
    sculpted_outer = base._require_single_solid(
        (body - outer_cutter).clean().fix(),
        feature="full-system preferred parabolic G1 outer envelope",
    )
    old_enclosure = shell_source.legacy._aesthetic_shell(sculpted_outer)
    conformal_cutter, inner_face, inner_topology = (
        shell_source._conformal_cavity_cutter()
    )
    cavity = base._rectangular_cavity()
    sand_void = base._sand_void()

    outer_bbox = sculpted_outer.bounding_box()
    front_clip_min_y = outer_bbox.min.Y - 1.0
    front_clip_max_y = (
        shell_source.CAVITY_FRONT_Y + shell_source.CAVITY_OVERLAP_MM
    )
    front_clip = Pos(
        0.0,
        (front_clip_min_y + front_clip_max_y) / 2.0,
        0.0,
    ) * Box(
        outer_bbox.size.X + 2.0,
        front_clip_max_y - front_clip_min_y,
        outer_bbox.size.Z + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    front_blank = base._require_single_solid(
        (sculpted_outer & front_clip).clean().fix(),
        feature="full-system solid preferred-front reconstruction blank",
    )
    front_blank = base._require_single_solid(
        (
            front_blank
            - sand_void
            - cavity
            - base._black_hole_visible_tool()
        ).clean().fix(),
        feature="full-system front blank with original recess and cavity",
    )
    restored_shell = base._require_single_solid(
        (old_enclosure + front_blank - sand_void).clean().fix(),
        feature="full-system preferred shell before conformal recavity",
    )
    enclosure = base._require_single_solid(
        (
            shell_source._subtract_periodic_cutter(
                restored_shell,
                conformal_cutter,
            )
            - sand_void
        ).clean().fix(),
        feature="full-system parabolic G1 conformal bare shell",
    )
    if shell_source._triangle_seam_faces(enclosure):
        raise ValueError("Bare-shell triangular seams returned in full system")

    # Put the blind tower inserts and rear fill passages into the simple solid
    # blank before it is hollowed.  Late cuts at the rounded rear edge can make
    # OpenCascade re-heal the unrelated periodic front surface; native blank
    # features keep the exact baseline locations without that global rewrite.
    native_wall_cutters = [
        *base._internal_tower_mount_insert_pockets(),
        base._sand_fill_rear_bore(-base.P.fill_port_x),
        base._sand_fill_rear_bore(base.P.fill_port_x),
    ]
    native_cut_outer = sculpted_outer.cut(*native_wall_cutters)
    native_cut_solids = native_cut_outer.solids()
    if len(native_cut_solids) != 1 or not _is_valid(native_cut_solids[0]):
        raise ValueError(
            "Native tower/fill wall features did not leave one valid blank"
        )
    detailed_outer_blank = native_cut_solids[0]
    residual_native_cutter_volume = sum(
        _shape_volume(detailed_outer_blank & cutter)
        for cutter in native_wall_cutters
    )
    if residual_native_cutter_volume > 0.05:
        raise ValueError(
            "Native tower/fill wall cutters left "
            f"{residual_native_cutter_volume:.6f} mm3 behind"
        )
    detailed_old_enclosure = shell_source.legacy._aesthetic_shell(
        detailed_outer_blank
    )
    detailed_pre_conformal_shell = base._require_single_solid(
        (
            detailed_old_enclosure
            + front_blank
            - sand_void
        ).clean().fix(),
        feature="pre-conformal shell with native tower/fill wall features",
    )

    conformal_domain = base._require_single_solid(
        (cavity + conformal_cutter).clean().fix(),
        feature="parabolic conformal gross acoustic domain",
    )
    legacy_domain = ORIGINAL_ACOUSTIC_DOMAIN()
    collar = shell_source._collar_signature(enclosure)
    if not _is_valid(enclosure) or not _is_valid(conformal_domain):
        raise ValueError("Parabolic conformal shell or acoustic domain is invalid")

    _GEOMETRY_CACHE = {
        "enclosure": enclosure,
        "detailed_pre_conformal_shell": detailed_pre_conformal_shell,
        "conformal_cutter": conformal_cutter,
        "sculpted_outer": sculpted_outer,
        "conformal_domain": conformal_domain,
        "legacy_domain": legacy_domain,
        "collar": collar,
        "outer_fairing_area_mm2": outer_fairing_face.area,
        "outer_fairing_topology": outer_fairing_topology,
        "inner_topology": inner_topology,
        "inner_face_area_mm2": inner_face.area,
        "body_topology": body_topology,
        "native_wall_cutter_residual_mm3": (
            residual_native_cutter_volume
        ),
    }
    return _GEOMETRY_CACHE


def _conformal_acoustic_domain() -> Part:
    return copy.copy(
        _build_parabolic_conformal_geometry()["conformal_domain"]
    )


def _conformal_front_brace_blends() -> Compound:
    """Attach four symmetric roots at the conformal wall's rear land."""
    wall_embed_mm = 1.0
    allowed = Pos(0.0, -wall_embed_mm, 0.0) * base._rectangular_cavity()
    clipped: list[Any] = []
    for brace in ORIGINAL_FRONT_BRACE_BLENDS().solids():
        clipped.extend((brace & allowed).solids())
    if len(clipped) != 4 or not all(_is_valid(solid) for solid in clipped):
        raise ValueError(
            "Conformal front-brace clipping did not preserve four valid roots"
        )
    volumes = [solid.volume for solid in clipped]
    if max(volumes) - min(volumes) > 0.01:
        raise ValueError("Conformal front-brace roots lost four-way symmetry")
    return Compound(children=clipped)


def _audited_direct_cut(
    base_shape: Any,
    cutter: Any,
    *,
    feature: str,
) -> Part:
    """Cut one simple hardware tool and audit the actual resulting volume."""
    before_volume = base_shape.volume
    before_bbox = base_shape.bounding_box()
    raw_cut = base_shape.cut(cutter)
    raw_solids = raw_cut.solids()
    if len(raw_solids) == 1 and _is_valid(raw_solids[0]):
        result = raw_solids[0]
    else:
        result = base._require_single_solid(
            raw_cut.clean(),
            feature=feature,
        )
    removed_volume = before_volume - result.volume
    cutter_volume = _shape_volume(cutter)
    residual_cutter_volume = _shape_volume(result & cutter)
    after_bbox = result.bounding_box()
    bbox_growth = max(
        before_bbox.min.X - after_bbox.min.X,
        before_bbox.min.Y - after_bbox.min.Y,
        before_bbox.min.Z - after_bbox.min.Z,
        after_bbox.max.X - before_bbox.max.X,
        after_bbox.max.Y - before_bbox.max.Y,
        after_bbox.max.Z - before_bbox.max.Z,
    )
    if residual_cutter_volume > 0.05 or bbox_growth > 0.001:
        raise ValueError(
            f"{feature} left {residual_cutter_volume:.6f} mm3 in the "
            f"cutter or grew the bounding box by {bbox_growth:.6f} mm"
        )
    _DETAIL_CUT_AUDITS[feature] = {
        "signed_whole_body_volume_delta_mm3": removed_volume,
        "cutter_volume_mm3": cutter_volume,
        "residual_cutter_volume_mm3": residual_cutter_volume,
        "bounding_box_growth_mm": bbox_growth,
    }
    return result


def _full_detail_base(
    port_clearance: Part,
    port_install_clearance: Part,
    *,
    include_gx16: bool = True,
    include_fill_ports: bool = True,
) -> Part:
    """Apply the complete baseline feature pipeline to the saved bare shell."""
    geometry = _build_parabolic_conformal_geometry()
    result: Any = copy.copy(geometry["detailed_pre_conformal_shell"])

    if include_gx16:
        result = result.fuse(
            base._rear_shifted(base._gx16_connector_island(base.P))
        ).clean().fix()
    if include_fill_ports:
        for fill_x in (-base.P.fill_port_x, base.P.fill_port_x):
            result = result.fuse(
                base._sand_fill_blister_shell(fill_x)
            ).clean().fix()
    result = base._require_single_solid(
        result,
        feature="conformal shell with GX16 island and sand-fill blisters",
    )

    tower_insert_pockets = base._internal_tower_mount_insert_pockets()
    platforms = base._internal_tower_mount_platforms()
    for pocket in tower_insert_pockets:
        platforms -= pocket
    for platform in platforms.solids():
        result = result.fuse(platform).clean().fix()
    result = base._require_single_solid(
        result,
        feature="conformal shell with upper-tower mounting platforms",
    )

    floor_top_z = -base.D.height / 2.0 + base.D.wall_stack_t
    clearance_clip = Pos(
        0.0,
        10.0,
        (floor_top_z + 0.01 + base.D.height / 2.0) / 2.0,
    ) * Box(
        base.D.width + 2.0,
        base.D.depth + 2.0,
        base.D.height / 2.0 - floor_top_z - 0.01,
    )
    in_box_install_clearance = base._primary_shape(
        port_install_clearance & base._outer_envelope() & clearance_clip
    )
    result -= in_box_install_clearance
    result = base._require_single_solid(
        result.clean().fix(),
        feature="conformal base with floor-tangent removable tube opening",
    )

    front_y = -base.D.depth / 2.0 + 10.0
    driver_seat_y = front_y + base.BLACK_HOLE_SEAT_DEPTH
    for index in range(base.P.driver_screw_count):
        angle = math.tau * index / base.P.driver_screw_count + math.pi / 4.0
        result -= base._oriented_cylinder(
            diameter=base.P.insert_bore_d,
            depth=base.P.driver_insert_bore_depth,
            axis="y",
            center=(
                base.P.driver_bolt_circle_r * math.cos(angle),
                driver_seat_y - base.P.driver_insert_bore_depth / 2.0,
                base.P.driver_bolt_circle_r * math.sin(angle)
                + base.BLACK_HOLE_CENTER_Z,
            ),
        )
    result = base._require_single_solid(
        result.clean().fix(),
        feature="conformal base after original driver insert bores",
    )
    # Keep the authoritative cut order while the inner wall has its original
    # simple topology.  The conformal inner surface is applied once, below,
    # after every unrelated rear/top hardware feature is finished.
    tube_insert_pockets = base._tube_mount_insert_pockets()
    for index, pocket in enumerate(tube_insert_pockets):
        result = base._cut_single_solid(
            result,
            pocket,
            feature=f"conformal base after tube insert pocket {index + 1}",
        )
    if include_gx16:
        result = _audited_direct_cut(
            result,
            base._rear_shifted(base._gx16_rear_cutout_corner(base.P)),
            feature="conformal GX16-cut base",
        )
    result = base._require_single_solid(
        (
            shell_source._subtract_periodic_cutter(
                result,
                geometry["conformal_cutter"],
            )
            - base._sand_void()
        ).clean().fix(),
        feature="finished conformal inner wall after full detailing",
    )

    # Add the brace network after the conformal cavity exists so the internal
    # rails remain in the acoustic volume.  Trim every brace with the same
    # installation envelope and insert tools used by the baseline before
    # fusing it to the finished wall.
    braces = base._restored_internal_braces(port_clearance)
    for brace_solid in braces.solids():
        brace_parts = list(
            (brace_solid - in_box_install_clearance).solids()
        )
        for pocket in tube_insert_pockets:
            next_parts: list[Any] = []
            for brace_part in brace_parts:
                next_parts.extend((brace_part - pocket).solids())
            brace_parts = next_parts
        for brace_part in brace_parts:
            result = result.fuse(brace_part).clean().fix()
    result = base._require_single_solid(
        result,
        feature="conformal shell with complete relieved brace network",
    )
    return base._require_single_solid(
        result.clean().fix(),
        feature="finished parabolic conformal full-detail monocoque base",
    )


def _large_circular_edge_radii(shape: Any) -> list[float]:
    radii = {
        round(edge.radius, 6)
        for edge in shape.edges()
        if edge.geom_type == GeomType.CIRCLE and edge.radius > 50.0
    }
    return sorted(radii)


def _export_named_references(full_base: Any) -> dict[str, Any]:
    exports = {
        "parabolic_g1_conformal_bare_shell_reference.step": (
            _build_parabolic_conformal_geometry()["enclosure"]
        ),
        "parabolic_g1_conformal_full_detail_base.step": full_base,
    }
    checks: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        source_solids = len(shape.solids())
        imported_solids = imported.solids()
        checks[filename] = {
            "source_solid_count": source_solids,
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(imported_solids) == source_solids,
            "all_imported_solids_valid": all(
                _is_valid(solid) for solid in imported_solids
            ),
        }
        if (
            not checks[filename]["solid_count_matches"]
            or not checks[filename]["all_imported_solids_valid"]
        ):
            raise ValueError(f"Named STEP round-trip failed for {filename}")
    return checks


def _replace_with_true_half_cutaway(full_base: Any) -> dict[str, Any]:
    """Add the conformal half-shell faces to the inherited internal cutaway."""
    cutaway_path = OUT / "sand_cube_190x210_single_oval_port_cutaway.step"
    inherited_cutaway = import_step(cutaway_path)
    half_shell = shell_source._geometric_half_cutaway(full_base)
    true_cutaway = Compound(
        children=[
            *[copy.copy(face) for face in half_shell.faces()],
            *[copy.copy(solid) for solid in inherited_cutaway.solids()],
        ]
    )
    export_step(
        true_cutaway,
        cutaway_path,
        unit=Unit.MM,
        write_pcurves=True,
    )
    imported = import_step(cutaway_path)
    source_solid_count = len(true_cutaway.solids())
    imported_solids = imported.solids()
    source_face_count = len(true_cutaway.faces())
    imported_face_count = len(imported.faces())
    checks = {
        "method": (
            "actual X<=0 conformal enclosure face intersection plus the "
            "complete inherited internal/hardware cutaway"
        ),
        "half_shell_face_count": len(half_shell.faces()),
        "source_solid_count": source_solid_count,
        "imported_solid_count": len(imported_solids),
        "solid_count_matches": len(imported_solids) == source_solid_count,
        "source_face_count": source_face_count,
        "imported_face_count": imported_face_count,
        "face_count_matches": imported_face_count == source_face_count,
        "all_imported_solids_valid": all(
            _is_valid(solid) for solid in imported_solids
        ),
        "all_imported_faces_valid": all(
            _is_valid(face) for face in imported.faces()
        ),
    }
    if not all(
        (
            checks["solid_count_matches"],
            checks["face_count_matches"],
            checks["all_imported_solids_valid"],
            checks["all_imported_faces_valid"],
            checks["half_shell_face_count"] > 0,
        )
    ):
        raise ValueError(f"True half-cutaway STEP round-trip failed: {checks}")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
            str(cutaway_path),
            "--out",
            str(OUT / "cutaway_viewer"),
        ],
        check=True,
    )
    return checks


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    geometry = _build_parabolic_conformal_geometry()
    base.build_base = _full_detail_base
    base._acoustic_domain = _conformal_acoustic_domain
    base._front_brace_blends = _conformal_front_brace_blends

    diagnostics = source.generate()
    full_base_path = OUT / "sand_cube_190x210_single_oval_port_base.step"
    full_base = import_step(full_base_path)
    if len(full_base.solids()) != 1 or not _is_valid(full_base):
        raise ValueError("Round-tripped conformal full-detail base is invalid")
    true_cutaway_roundtrip = _replace_with_true_half_cutaway(full_base)

    fairing_faces = [
        face
        for face in full_base.faces()
        if abs(face.area - geometry["outer_fairing_area_mm2"]) <= 1e-5
    ]
    if len(fairing_faces) != 1:
        raise ValueError(
            "Full-detail features changed or split the preferred outer fairing: "
            f"found {len(fairing_faces)} matching faces"
        )
    if shell_source._triangle_seam_faces(full_base):
        raise ValueError("Triangular front seam faces returned after detailing")

    radii = _large_circular_edge_radii(full_base)
    for required_radius in (65.25, 79.0, 87.0):
        if not any(abs(radius - required_radius) <= 1e-6 for radius in radii):
            raise ValueError(
                f"Full-detail base lost the R{required_radius:g} collar interface"
            )

    named_roundtrip = _export_named_references(full_base)
    gross_volume_change_l = (
        geometry["conformal_domain"].volume
        - geometry["legacy_domain"].volume
    ) / 1_000_000.0
    front_bbox = full_base.bounding_box()
    collar = geometry["collar"]

    diagnostics["name"] = NAME
    diagnostics["status"] = (
        "complete rear-corner port, absorber, tower, horn, hardware, and "
        "brace system with the preserved parabolic G1 conformal front"
    )
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_conformal_full_system"
        ),
        "output_dir": (
            "build/"
            "sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_conformal_full_system"
        ),
        "committed_bare_shell_modified": False,
        "authoritative_rear_corner_variant_modified": False,
        "shared_upstream_generators_modified": False,
    }
    diagnostics["parabolic_conformal_front"] = {
        "construction": (
            "exact committed exterior, collar, and conformal wall geometry; "
            "native rear/top wall features are formed before hollowing, and "
            "the authoritative assembly pipeline follows"
        ),
        "outer_fairing_face_count_after_detailing": len(fairing_faces),
        "outer_fairing_face_area_mm2": fairing_faces[0].area,
        "outer_fairing_area_difference_mm2": (
            fairing_faces[0].area - geometry["outer_fairing_area_mm2"]
        ),
        "corner_pullback_mm": 15.0,
        "edge_midpoint_pullback_mm": 8.0,
        "crest_diameter_mm": base.BLACK_HOLE_OUTER_D,
        "through_opening_diameter_mm": (
            2.0 * collar["through_opening_radius_mm"]
        ),
        "collar_outer_diameter_mm": 2.0 * collar["outer_radius_mm"],
        "collar_radial_width_mm": collar["radial_width_mm"],
        "collar_rear_face_y_mm": collar["rear_face_y_mm"],
        "large_circular_interface_radii_mm": radii,
        "remaining_triangle_seam_face_count": len(
            shell_source._triangle_seam_faces(full_base)
        ),
        "target_wall_thickness_mm": shell_source.WALL_THICKNESS_MM,
        "minimum_sampled_wall_thickness_mm": geometry["inner_topology"][
            "minimum_sampled_wall_thickness_mm"
        ],
        "maximum_sampled_wall_thickness_mm": geometry["inner_topology"][
            "maximum_sampled_wall_thickness_mm"
        ],
        "gross_acoustic_domain_change_l": gross_volume_change_l,
        "legacy_gross_acoustic_domain_l": (
            geometry["legacy_domain"].volume / 1_000_000.0
        ),
        "conformal_gross_acoustic_domain_l": (
            geometry["conformal_domain"].volume / 1_000_000.0
        ),
        "full_base_frontmost_y_mm": front_bbox.min.Y,
    }
    diagnostics["preserved_full_detail_contract"] = {
        "solid_bottom_floor": True,
        "dual_skin_2_3_2_walls": True,
        "driver_insert_bores": base.P.driver_screw_count,
        "front_collar_buttresses": 4,
        "internal_brace_network": True,
        "roof_harmonic_tube_opening_and_saddle": True,
        "gx16_island_cutout_and_hardware": True,
        "sand_fill_ports_and_internal_blisters": 2,
        "removable_internal_port_and_mounting_tabs": True,
        "rear_flush_d_squat_absorber": True,
        "serviceable_exterior_tower_and_flare": True,
        "horn_de250_and_support_geometry": True,
        "true_geometric_half_shell_cutaway": True,
        "detail_cut_audits": _DETAIL_CUT_AUDITS,
    }
    diagnostics["geometry"]["named_reference_step_roundtrip"] = (
        named_roundtrip
    )
    diagnostics["geometry"]["true_half_cutaway_step_roundtrip"] = (
        true_cutaway_roundtrip
    )
    diagnostics["geometry"]["step_roundtrip"][
        "sand_cube_190x210_single_oval_port_cutaway.step"
    ] = true_cutaway_roundtrip
    diagnostics["files"].update(
        {
            "parabolic_g1_conformal_bare_shell_reference.step": str(
                OUT / "parabolic_g1_conformal_bare_shell_reference.step"
            ),
            "parabolic_g1_conformal_full_detail_base.step": str(
                OUT / "parabolic_g1_conformal_full_detail_base.step"
            ),
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "index.html"),
            "cutaway_viewer": str(OUT / "cutaway_viewer" / "index.html"),
        }
    )
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
