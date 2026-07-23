"""One coordinated native job for synthetic geometry-check fixtures."""

from __future__ import annotations

# ruff: noqa: E402

from pathlib import Path as _CadSafetyPath
import sys as _cad_safety_sys


_CAD_SAFETY_ROOT = next(
    parent
    for parent in _CadSafetyPath(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file()
)
if str(_CAD_SAFETY_ROOT) not in _cad_safety_sys.path:
    _cad_safety_sys.path.insert(0, str(_CAD_SAFETY_ROOT))
from cad_runner.entrypoint import ensure_coordinated as _ensure_cad_coordinated


_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Edge,
    Face,
    GeomType,
    Location,
    Plane,
    Wire,
)

from cad_geometry_checks import BooleanOutcome, DiagnosticStatus
from cad_geometry_checks.native import (
    compare_protected_material,
    compare_protected_surfaces,
    measure_difference,
    measure_edge_continuity,
    measure_intersection,
    measure_normal_change,
    measure_print_bed_contact,
    measure_volume,
    normalize_shapes,
    normalize_solids,
    sample_edge_signatures,
    summarize_topology,
)
from cad_runner.outputs import job_output_path


OUTPUT = Path("build/cad-geometry-checks/native-fixtures.json")
LINEAR_TOLERANCE_MM = 1e-5
AREA_TOLERANCE_MM2 = 1e-4
VOLUME_TOLERANCE_MM3 = 1e-4


def _box(
    length: float = 10.0,
    width: float = 10.0,
    height: float = 10.0,
    *,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    shape = Box(length, width, height, align=Align.MIN)
    return shape.moved(Location(location)) if location != (0.0, 0.0, 0.0) else shape


def _close(actual: float | None, expected: float, tolerance: float) -> None:
    assert actual is not None
    assert abs(actual - expected) <= tolerance, (actual, expected, tolerance)


def _holed_face() -> Face:
    return Face(
        Wire.make_rect(10.0, 10.0),
        [Wire.make_rect(4.0, 4.0)],
    )


def main() -> None:
    cases: dict[str, object] = {}

    base = _box()
    disjoint = _box(location=(11.0, 0.0, 0.0))
    touching = _box(location=(10.0, 0.0, 0.0))
    overlapping = _box(location=(9.0, 0.0, 0.0))

    disjoint_result = measure_intersection(base, disjoint)
    touching_result = measure_intersection(base, touching)
    overlap_result = measure_intersection(base, overlapping)
    missing_result = measure_intersection(
        base,
        overlapping,
        operation=lambda _left, _right: None,
    )
    explicit_empty_result = measure_intersection(
        base,
        overlapping,
        operation=lambda _left, _right: Compound(children=[]),
    )
    assert disjoint_result.outcome is BooleanOutcome.BOUNDING_BOX_DISJOINT
    assert touching_result.outcome is BooleanOutcome.ZERO_VOLUME_CONTACT
    assert overlap_result.outcome is BooleanOutcome.POSITIVE_VOLUME
    assert missing_result.outcome is BooleanOutcome.NO_RETURNED_SHAPE
    assert explicit_empty_result.outcome is BooleanOutcome.EMPTY_SHAPE
    mixed_left = [_box(), _box()]
    mixed_positive_calls = 0

    def mixed_positive_operation(left, right):
        nonlocal mixed_positive_calls
        mixed_positive_calls += 1
        return (
            None
            if mixed_positive_calls == 1
            else left.intersect(right, tolerance=1e-7, include_touched=True)
        )

    mixed_positive = measure_intersection(
        mixed_left,
        _box(),
        operation=mixed_positive_operation,
    )
    mixed_empty_calls = 0

    def mixed_empty_operation(_left, _right):
        nonlocal mixed_empty_calls
        mixed_empty_calls += 1
        return None if mixed_empty_calls == 1 else Compound(children=[])

    mixed_empty = measure_intersection(
        mixed_left,
        _box(),
        operation=mixed_empty_operation,
    )
    assert mixed_positive.outcome is BooleanOutcome.NO_RETURNED_SHAPE
    assert mixed_positive.volume_mm3 is None
    assert mixed_empty.outcome is BooleanOutcome.NO_RETURNED_SHAPE
    assert mixed_empty.volume_mm3 is None
    _close(overlap_result.volume_mm3, 100.0, VOLUME_TOLERANCE_MM3)
    cases["intersection_outcomes"] = {
        "disjoint": disjoint_result.outcome.value,
        "touching": touching_result.outcome.value,
        "overlap_mm3": overlap_result.volume_mm3,
        "missing": missing_result.outcome.value,
        "empty": explicit_empty_result.outcome.value,
        "mixed_missing_positive": mixed_positive.outcome.value,
        "mixed_missing_empty": mixed_empty.outcome.value,
    }

    first = _box()
    second = _box(location=(20.0, 0.0, 0.0))
    listed = [first, second]
    compound = Compound(children=[_box(), _box(location=(20.0, 0.0, 0.0))])
    assert normalize_shapes(None).diagnostic.status is DiagnosticStatus.INDETERMINATE
    assert normalize_solids(first).count == 1
    assert normalize_solids(listed).count == 2
    assert normalize_solids(compound).count == 2
    assert normalize_solids(Compound(children=[])).diagnostic.status is DiagnosticStatus.EMPTY
    _close(measure_volume(listed).value, 2000.0, VOLUME_TOLERANCE_MM3)
    _close(measure_volume(compound).value, 2000.0, VOLUME_TOLERANCE_MM3)
    covering_tool = _box(30.0, 10.0, 10.0)
    list_overlap = measure_intersection(compound, covering_tool)
    _close(list_overlap.volume_mm3, 2000.0, VOLUME_TOLERANCE_MM3)
    duplicate_volume = measure_volume([_box(), _box()])
    overlapping_volume = measure_volume([_box(), _box(location=(5.0, 0.0, 0.0))])
    duplicate_overlap = measure_intersection([_box(), _box()], _box())
    _close(duplicate_volume.value, 1000.0, VOLUME_TOLERANCE_MM3)
    _close(overlapping_volume.value, 1500.0, VOLUME_TOLERANCE_MM3)
    _close(duplicate_overlap.volume_mm3, 1000.0, VOLUME_TOLERANCE_MM3)
    cases["normalization"] = {
        "single": 1,
        "list": 2,
        "compound": 2,
        "list_compound_intersection_mm3": list_overlap.volume_mm3,
        "duplicate_union_mm3": duplicate_volume.value,
        "overlapping_union_mm3": overlapping_volume.value,
        "duplicate_intersection_union_mm3": duplicate_overlap.volume_mm3,
    }

    difference = measure_difference(base, overlapping)
    _close(difference.value, 900.0, VOLUME_TOLERANCE_MM3)
    cases["difference_remaining_mm3"] = difference.value

    full_contact = measure_print_bed_contact(_box(10.0, 8.0, 2.0))
    off_bed = measure_print_bed_contact(
        _box(10.0, 8.0, 2.0, location=(0.0, 0.0, 2.0))
    )
    nub = _box(1.0, 1.0, 1.0)
    upper = _box(10.0, 8.0, 2.0, location=(-4.5, -3.5, 1.0))
    tiny_nub = measure_print_bed_contact(Compound(children=[nub, upper]))
    vertical_plane = Plane(
        origin=(0.0, 0.0, 4.0),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, -1.0, 0.0),
    )
    vertical_contact = measure_print_bed_contact(
        Face.make_rect(10.0, 8.0, vertical_plane)
    )
    spline_bottom = Face.make_surface_from_array_of_points(
        [
            [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0)],
            [(0.0, 5.0, 0.0), (5.0, 5.0, 0.0), (10.0, 5.0, 0.0)],
            [(0.0, 10.0, 0.0), (5.0, 10.0, 0.0), (10.0, 10.0, 0.0)],
        ],
        min_deg=2,
        max_deg=3,
    )
    spline_contact = measure_print_bed_contact(spline_bottom)
    assert str(spline_bottom.geom_type).lower().endswith("bspline")
    assert spline_bottom.is_planar is not None
    _close(full_contact.area_mm2, 80.0, AREA_TOLERANCE_MM2)
    _close(full_contact.width_mm, 8.0, LINEAR_TOLERANCE_MM)
    assert off_bed.area_mm2 == 0.0
    _close(tiny_nub.area_mm2, 1.0, AREA_TOLERANCE_MM2)
    _close(tiny_nub.width_mm, 1.0, LINEAR_TOLERANCE_MM)
    assert vertical_contact.area_mm2 == 0.0
    _close(spline_contact.area_mm2, 100.0, AREA_TOLERANCE_MM2)
    _close(spline_contact.width_mm, 10.0, LINEAR_TOLERANCE_MM)
    cases["print_bed"] = {
        "full": [full_contact.area_mm2, full_contact.width_mm],
        "off_bed": [off_bed.area_mm2, off_bed.width_mm],
        "tiny_nub": [tiny_nub.area_mm2, tiny_nub.width_mm],
        "vertical": [vertical_contact.area_mm2, vertical_contact.width_mm],
        "planar_bspline": [spline_contact.area_mm2, spline_contact.width_mm],
    }

    fused = _box(1.0, 1.0, 1.0).fuse(
        _box(1.0, 1.0, 1.0, location=(1.0, 0.0, 0.0))
    ).clean()
    ordinary = _box(2.0, 1.0, 1.0)
    fused_topology = summarize_topology(fused)
    ordinary_topology = summarize_topology(ordinary)
    open_face_topology = summarize_topology(
        Face.make_rect(2.0, 1.0, Plane.XY)
    )
    closed_cylinder = Cylinder(5.0, 10.0, align=Align.MIN)
    closed_cylinder_topology = summarize_topology(closed_cylinder)
    cylindrical_face = next(
        face
        for face in closed_cylinder.faces()
        if face.geom_type is GeomType.CYLINDER
    )
    open_cylinder_topology = summarize_topology(cylindrical_face)
    assert fused_topology.solid_count == ordinary_topology.solid_count == 1
    assert fused_topology.face_count == ordinary_topology.face_count == 6
    assert fused_topology.edge_count == ordinary_topology.edge_count == 12
    assert fused_topology.boundary_edge_count == 0
    assert fused_topology.manifold_edge_count == 12
    assert open_face_topology.boundary_edge_count == 4
    assert closed_cylinder_topology.boundary_edge_count == 0
    assert closed_cylinder_topology.non_manifold_edge_count == 0
    assert open_cylinder_topology.boundary_edge_count == 2
    assert open_cylinder_topology.manifold_edge_count == 1
    fused_signatures = sample_edge_signatures(fused)
    ordinary_signatures = sample_edge_signatures(ordinary)
    assert fused_signatures.signatures == ordinary_signatures.signatures
    assert {
        signature.geometry_type
        for signature in ordinary_signatures.signatures
    } == {"LINE"}
    cases["topology_and_edge_signatures"] = {
        "fused_faces_edges": [
            fused_topology.face_count,
            fused_topology.edge_count,
        ],
        "closed_manifold_edges": fused_topology.manifold_edge_count,
        "open_boundary_edges": open_face_topology.boundary_edge_count,
        "closed_cylinder_boundary_edges": (
            closed_cylinder_topology.boundary_edge_count
        ),
        "open_cylinder_boundary_manifold_edges": [
            open_cylinder_topology.boundary_edge_count,
            open_cylinder_topology.manifold_edge_count,
        ],
        "signature_count": len(fused_signatures.signatures),
    }

    first_edge = Edge.make_line((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    tangent_edge = Edge.make_line((1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
    sharp_edge = Edge.make_line((1.0, 0.0, 0.0), (1.0, 1.0, 0.0))
    tangent_continuity = measure_edge_continuity(first_edge, tangent_edge)
    sharp_continuity = measure_edge_continuity(first_edge, sharp_edge)
    assert tangent_continuity.continuous is True
    assert sharp_continuity.continuous is False
    _close(tangent_continuity.angle_change_deg, 0.0, 1e-7)
    _close(sharp_continuity.angle_change_deg, 90.0, 1e-7)

    first_face = Face.make_rect(2.0, 2.0, Plane.XY)
    coplanar_face = Face.make_rect(
        2.0,
        2.0,
        Plane(origin=(0.0, 2.0, 0.0)),
    )
    upright_face = Face.make_rect(
        2.0,
        2.0,
        Plane(
            origin=(0.0, 1.0, 1.0),
            x_dir=(1.0, 0.0, 0.0),
            z_dir=(0.0, -1.0, 0.0),
        ),
    )
    opposite_face = Face.make_rect(
        2.0,
        2.0,
        Plane(
            origin=(0.0, 0.0, 0.0),
            x_dir=(1.0, 0.0, 0.0),
            z_dir=(0.0, 0.0, -1.0),
        ),
    )
    shared_edge = Edge.make_line((-1.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    coplanar_normals = measure_normal_change(
        first_face,
        coplanar_face,
        shared_edge,
    )
    sharp_normals = measure_normal_change(
        first_face,
        upright_face,
        shared_edge,
    )
    opposite_normals = measure_normal_change(
        first_face,
        opposite_face,
        shared_edge,
    )
    assert coplanar_normals.continuous is True
    assert sharp_normals.continuous is False
    assert opposite_normals.continuous is True
    _close(coplanar_normals.angle_change_deg, 0.0, 1e-7)
    _close(sharp_normals.angle_change_deg, 90.0, 1e-7)
    _close(opposite_normals.angle_change_deg, 0.0, 1e-7)
    cases["continuity"] = {
        "tangent_edge_deg": tangent_continuity.angle_change_deg,
        "sharp_edge_deg": sharp_continuity.angle_change_deg,
        "coplanar_normal_deg": coplanar_normals.angle_change_deg,
        "sharp_normal_deg": sharp_normals.angle_change_deg,
        "opposite_unoriented_normal_deg": opposite_normals.angle_change_deg,
    }

    reference = _box()
    identical = _box()
    additive = Compound(
        children=[
            _box(),
            _box(2.0, 2.0, 2.0, location=(20.0, 0.0, 0.0)),
        ]
    )
    removed = _box(5.0, 10.0, 10.0)
    empty = Compound(children=[])
    translated = _box(location=(1.0, 0.0, 0.0))
    material_cases = {
        "identical": compare_protected_material(reference, identical),
        "additive": compare_protected_material(reference, additive),
        "removed": compare_protected_material(reference, removed),
        "empty_candidate": compare_protected_material(reference, empty),
        "both_empty": compare_protected_material(empty, empty),
        "translated": compare_protected_material(reference, translated),
    }
    expected_material = {
        "identical": (0.0, 0.0),
        "additive": (0.0, 8.0),
        "removed": (500.0, 0.0),
        "empty_candidate": (1000.0, 0.0),
        "both_empty": (0.0, 0.0),
        "translated": (100.0, 100.0),
    }
    for name, result in material_cases.items():
        assert result.diagnostic.status is DiagnosticStatus.SUCCESS
        _close(
            result.removed_volume_mm3,
            expected_material[name][0],
            VOLUME_TOLERANCE_MM3,
        )
        _close(
            result.added_volume_mm3,
            expected_material[name][1],
            VOLUME_TOLERANCE_MM3,
        )

    identical_surfaces = compare_protected_surfaces(reference, identical)
    additive_surfaces = compare_protected_surfaces(reference, additive)
    removed_surfaces = compare_protected_surfaces(reference, removed)
    empty_surfaces = compare_protected_surfaces(empty, empty)
    translated_surfaces = compare_protected_surfaces(reference, translated)
    identical_holed_surfaces = compare_protected_surfaces(
        _holed_face(),
        _holed_face(),
    )
    filled_hole_surfaces = compare_protected_surfaces(
        _holed_face(),
        Face(Wire.make_rect(10.0, 10.0)),
    )
    _close(identical_surfaces.reference_to_candidate_max_mm, 0.0, LINEAR_TOLERANCE_MM)
    _close(identical_surfaces.candidate_to_reference_max_mm, 0.0, LINEAR_TOLERANCE_MM)
    assert additive_surfaces.candidate_to_reference_max_mm > 0.0
    assert removed_surfaces.reference_to_candidate_max_mm > 0.0
    assert empty_surfaces.diagnostic.status is DiagnosticStatus.SUCCESS
    assert translated_surfaces.reference_to_candidate_max_mm > 0.0
    assert translated_surfaces.candidate_to_reference_max_mm > 0.0
    _close(
        identical_holed_surfaces.reference_to_candidate_max_mm,
        0.0,
        LINEAR_TOLERANCE_MM,
    )
    _close(
        identical_holed_surfaces.candidate_to_reference_max_mm,
        0.0,
        LINEAR_TOLERANCE_MM,
    )
    assert filled_hole_surfaces.candidate_to_reference_max_mm > 0.0
    cases["protected_comparison"] = {
        name: [
            result.removed_volume_mm3,
            result.added_volume_mm3,
        ]
        for name, result in material_cases.items()
    }
    cases["protected_surfaces"] = {
        "identical": [
            identical_surfaces.reference_to_candidate_max_mm,
            identical_surfaces.candidate_to_reference_max_mm,
        ],
        "additive_reverse_mm": additive_surfaces.candidate_to_reference_max_mm,
        "removed_forward_mm": removed_surfaces.reference_to_candidate_max_mm,
        "empty_status": empty_surfaces.diagnostic.status.value,
        "translated": [
            translated_surfaces.reference_to_candidate_max_mm,
            translated_surfaces.candidate_to_reference_max_mm,
        ],
        "identical_holed": [
            identical_holed_surfaces.reference_to_candidate_max_mm,
            identical_holed_surfaces.candidate_to_reference_max_mm,
        ],
        "filled_hole_reverse_mm": (
            filled_hole_surfaces.candidate_to_reference_max_mm
        ),
    }

    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "status": "passed",
                "case_groups": cases,
                "case_group_count": len(cases),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"native geometry fixtures passed: {len(cases)} case groups")


if __name__ == "__main__":
    main()
