"""Generate the preferred parabolic G1 face with a conformal inner wall.

The parent experiment's exterior fairing, perimeter, and 15 mm pullback are
reused without modification.  This sibling replaces only the old flat inner
front seam with a seven-millimeter inward normal offset of that fairing.  The
new acoustic-domain cutter overlaps both the existing black-hole relief and
the rectangular cavity so their former coplanar R1/square corner seams cannot
leave the four 0.214602 mm2 triangular faces.
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
from pathlib import Path
from typing import Any

import numpy as np
from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Face,
    GeomType,
    Pos,
    Shell,
    Solid,
    Unit,
    Wire,
    export_step,
    import_step,
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Sewing,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.Geom import Geom_BSplineCurve, Geom_BSplineSurface
from OCP.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal
from OCP.gp import gp_Pnt, gp_Vec


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_fairing"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_fairing as parent  # noqa: E402


legacy = parent.parent
cad = parent.cad
base = parent.base
OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_inner_wall"
)

NAME = "sand_cube_190x210_parabolic_side_g1_conformal_inner_wall_preview"
FRONT_Y = parent.FRONT_Y
WALL_THICKNESS_MM = base.D.wall_stack_t
CAVITY_FRONT_Y = FRONT_Y + base.BLACK_HOLE_SEAT_DEPTH
CAVITY_OVERLAP_MM = 0.25
TRANSITION_FRONT_MARGIN_MM = 0.25
TRANSITION_SECTION_INSET_MM = 0.05
CONFORMAL_STOP_V = 0.65
CONFORMAL_TANGENT_GUIDE_V = 0.67

# The exact normal offset is not polynomial.  A dense periodic cubic in U and
# a degree-12 Bezier in V reproduce it to approximately 0.015 mm while keeping
# a clean, closed, single-face periodic topology for robust booleans and STEP.
INNER_U_SAMPLE_COUNT = 1024
INNER_V_DEGREE = 12
INNER_V_SAMPLE_COUNT = INNER_V_DEGREE + 1
INNER_U_DEGREE = 3

TRIANGLE_AREA_MM2 = 1.0 - math.pi / 4.0


def _is_valid(shape: Any) -> bool:
    value = getattr(shape, "is_valid")
    return value() if callable(value) else bool(value)


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    if hasattr(shape, "solids"):
        return sum(solid.volume for solid in shape.solids())
    return sum(item.volume for item in shape)


def _complement(solid: Solid) -> Solid:
    """Return OCCT's oriented complement of a finite cutter solid."""
    return Solid.cast(solid.wrapped.Reversed())


def _overlap_volume(target: Solid, cutter: Solid) -> float:
    """Measure overlap robustly when a periodic cutter is fully nested."""
    remainder = target & _complement(cutter)
    return max(0.0, target.volume - _shape_volume(remainder))


def _subtract_periodic_cutter(target: Solid, cutter: Solid) -> Solid:
    """Cut with a complemented-common operation for periodic NURBS solids."""
    result = target & _complement(cutter)
    return base._require_single_solid(
        result,
        feature="periodic conformal cavity subtraction",
    )


def _outer_fairing_surface() -> Geom_BSplineSurface:
    control_targets = parent._minimum_energy_control_rings()
    control_poles = [
        legacy._periodic_interpolation_poles(ring)
        for ring in control_targets
    ]
    return legacy._surface_from_poles(
        control_poles,
        v_degree=parent.V_DEGREE,
    )


def _exact_inward_offset_point(
    surface: Geom_BSplineSurface,
    u_parameter: float,
    v_parameter: float,
) -> np.ndarray:
    point = gp_Pnt()
    u_tangent = gp_Vec()
    v_tangent = gp_Vec()
    surface.D1(
        u_parameter,
        v_parameter,
        point,
        u_tangent,
        v_tangent,
    )
    normal = u_tangent.Crossed(v_tangent)
    if normal.Magnitude() <= 1e-12:
        raise ValueError("Degenerate normal on the parent G1 fairing")
    normal.Normalize()
    return np.asarray(
        (
            point.X() + WALL_THICKNESS_MM * normal.X(),
            point.Y() + WALL_THICKNESS_MM * normal.Y(),
            point.Z() + WALL_THICKNESS_MM * normal.Z(),
        ),
        dtype=float,
    )


def _periodic_interpolation_poles(
    target_rings: np.ndarray,
) -> list[np.ndarray]:
    """Solve every dense periodic cubic ring in one factorization."""
    ring_count, sample_count, coordinate_count = target_rings.shape
    if sample_count != INNER_U_SAMPLE_COUNT or coordinate_count != 3:
        raise ValueError("Unexpected dense offset target dimensions")
    matrix = np.zeros((sample_count, sample_count), dtype=float)
    for row in range(sample_count):
        matrix[row, row] = 1.0
        matrix[row, (row + 1) % sample_count] = 4.0
        matrix[row, (row + 2) % sample_count] = 1.0
    right_hand_side = np.transpose(
        target_rings,
        (1, 0, 2),
    ).reshape(sample_count, ring_count * 3)
    solution = np.linalg.solve(matrix, 6.0 * right_hand_side)
    pole_array = solution.reshape(sample_count, ring_count, 3)
    return [pole_array[:, index, :] for index in range(ring_count)]


def _u_basis() -> tuple[TColStd_Array1OfReal, TColStd_Array1OfInteger]:
    knots = TColStd_Array1OfReal(1, INNER_U_SAMPLE_COUNT + 1)
    multiplicities = TColStd_Array1OfInteger(1, INNER_U_SAMPLE_COUNT + 1)
    for index in range(INNER_U_SAMPLE_COUNT + 1):
        knots.SetValue(index + 1, float(index))
        multiplicities.SetValue(index + 1, 1)
    return knots, multiplicities


def _v_basis(degree: int) -> tuple[
    TColStd_Array1OfReal,
    TColStd_Array1OfInteger,
]:
    knots = TColStd_Array1OfReal(1, 2)
    knots.SetValue(1, 0.0)
    knots.SetValue(2, 1.0)
    multiplicities = TColStd_Array1OfInteger(1, 2)
    multiplicities.SetValue(1, degree + 1)
    multiplicities.SetValue(2, degree + 1)
    return knots, multiplicities


def _surface_from_poles(
    pole_rings: list[np.ndarray],
    *,
    v_degree: int,
) -> Geom_BSplineSurface:
    poles = TColgp_Array2OfPnt(
        1,
        INNER_U_SAMPLE_COUNT,
        1,
        len(pole_rings),
    )
    for v_index, ring in enumerate(pole_rings, 1):
        for u_index, point in enumerate(ring, 1):
            poles.SetValue(u_index, v_index, gp_Pnt(*point))
    u_knots, u_multiplicities = _u_basis()
    v_knots, v_multiplicities = _v_basis(v_degree)
    return Geom_BSplineSurface(
        poles,
        u_knots,
        v_knots,
        u_multiplicities,
        v_multiplicities,
        INNER_U_DEGREE,
        v_degree,
        True,
        False,
    )


def _curve_from_poles(poles: np.ndarray) -> Geom_BSplineCurve:
    pole_array = TColgp_Array1OfPnt(1, INNER_U_SAMPLE_COUNT)
    for index, point in enumerate(poles, 1):
        pole_array.SetValue(index, gp_Pnt(*point))
    knots, multiplicities = _u_basis()
    return Geom_BSplineCurve(
        pole_array,
        knots,
        multiplicities,
        INNER_U_DEGREE,
        True,
    )


def _face_from_surface(
    surface: Geom_BSplineSurface,
    *,
    feature: str,
    v_max: float | None = None,
) -> Face:
    if v_max is None:
        maker = BRepBuilderAPI_MakeFace(surface, 1e-7)
    else:
        u_min, u_max, v_min, _surface_v_max = surface.Bounds()
        maker = BRepBuilderAPI_MakeFace(
            surface,
            u_min,
            u_max,
            v_min,
            v_max,
            1e-7,
        )
    if not maker.IsDone():
        raise ValueError(f"Unable to make {feature} face")
    face = Face.cast(maker.Face())
    if face is None or face.area <= 0.0 or not _is_valid(face):
        raise ValueError(f"{feature} face is empty or invalid")
    return face


def _face_from_curve(curve: Geom_BSplineCurve, *, feature: str) -> Face:
    edge_maker = BRepBuilderAPI_MakeEdge(curve)
    if not edge_maker.IsDone():
        raise ValueError(f"Unable to make {feature} edge")
    edge = legacy.Edge.cast(edge_maker.Edge())
    if edge is None:
        raise ValueError(f"Unable to cast {feature} edge")
    face = Face(Wire([edge]))
    if face.area <= 0.0 or not _is_valid(face):
        raise ValueError(f"{feature} face is empty or invalid")
    return face


def _bernstein_matrix(degree: int) -> np.ndarray:
    sample_parameters = np.linspace(0.0, 1.0, degree + 1)
    return np.asarray(
        [
            [
                math.comb(degree, index)
                * parameter**index
                * (1.0 - parameter) ** (degree - index)
                for index in range(degree + 1)
            ]
            for parameter in sample_parameters
        ],
        dtype=float,
    )


def _conformal_inner_surface() -> tuple[
    Geom_BSplineSurface,
    list[np.ndarray],
    dict[str, Any],
]:
    outer_surface = _outer_fairing_surface()
    v_parameters = np.linspace(0.0, 1.0, INNER_V_SAMPLE_COUNT)
    bernstein = _bernstein_matrix(INNER_V_DEGREE)
    control_targets = np.empty(
        (INNER_V_SAMPLE_COUNT, INNER_U_SAMPLE_COUNT, 3),
        dtype=float,
    )
    for u_index in range(INNER_U_SAMPLE_COUNT):
        outer_u = (
            parent.ANGULAR_SAMPLE_COUNT
            * u_index
            / INNER_U_SAMPLE_COUNT
        )
        offset_samples = np.asarray(
            [
                _exact_inward_offset_point(
                    outer_surface,
                    outer_u,
                    float(v_parameter),
                )
                for v_parameter in v_parameters
            ],
            dtype=float,
        )
        control_targets[:, u_index, :] = np.linalg.solve(
            bernstein,
            offset_samples,
        )
    control_poles = _periodic_interpolation_poles(control_targets)
    inner_surface = _surface_from_poles(
        control_poles,
        v_degree=INNER_V_DEGREE,
    )

    maximum_point_error = 0.0
    minimum_wall = math.inf
    maximum_wall = 0.0
    for u_index in range(2 * INNER_U_SAMPLE_COUNT):
        inner_u = u_index / 2.0
        outer_u = (
            parent.ANGULAR_SAMPLE_COUNT
            * inner_u
            / INNER_U_SAMPLE_COUNT
        )
        for v_parameter in np.linspace(0.0, 1.0, 33):
            exact_offset = _exact_inward_offset_point(
                outer_surface,
                outer_u,
                float(v_parameter),
            )
            approximated = inner_surface.Value(
                inner_u,
                float(v_parameter),
            )
            approximated_array = np.asarray(
                (approximated.X(), approximated.Y(), approximated.Z()),
                dtype=float,
            )
            maximum_point_error = max(
                maximum_point_error,
                float(np.linalg.norm(exact_offset - approximated_array)),
            )
            outer_point = outer_surface.Value(
                outer_u,
                float(v_parameter),
            )
            wall = float(
                np.linalg.norm(
                    approximated_array
                    - np.asarray(
                        (outer_point.X(), outer_point.Y(), outer_point.Z()),
                        dtype=float,
                    )
                )
            )
            minimum_wall = min(minimum_wall, wall)
            maximum_wall = max(maximum_wall, wall)
    return inner_surface, control_poles, {
        "construction": "dense approximation of exact inward normal offset",
        "target_wall_thickness_mm": WALL_THICKNESS_MM,
        "u_sample_count": INNER_U_SAMPLE_COUNT,
        "v_degree": INNER_V_DEGREE,
        "maximum_offset_surface_error_mm": maximum_point_error,
        "minimum_sampled_wall_thickness_mm": minimum_wall,
        "maximum_sampled_wall_thickness_mm": maximum_wall,
        "surface_continuity": str(inner_surface.Continuity()),
    }


def _conformal_cavity_cutter() -> tuple[Solid, Face, dict[str, Any]]:
    inner_surface, _control_poles, diagnostics = _conformal_inner_surface()
    inner_face = _face_from_surface(
        inner_surface,
        feature="conformal inner G1 wall",
        v_max=CONFORMAL_STOP_V,
    )
    boundaries = [edge for edge in inner_face.edges() if edge.is_closed]
    if len(boundaries) != 2:
        raise ValueError(
            f"Expected two conformal inner boundaries, found {len(boundaries)}"
        )
    circular_edge = min(boundaries, key=lambda edge: edge.length)
    outer_edge = max(boundaries, key=lambda edge: edge.length)
    cavity = base._rectangular_cavity()
    cavity_front_faces = [
        face
        for face in cavity.faces()
        if abs(face.center().Y - CAVITY_FRONT_Y) <= 1e-6
    ]
    if not cavity_front_faces:
        raise ValueError("Unable to find the rectangular cavity front section")
    cavity_front_face = max(cavity_front_faces, key=lambda face: face.area)
    section_scale = (
        base.D.width / 2.0
        - WALL_THICKNESS_MM
        - TRANSITION_SECTION_INSET_MM
    ) / (base.D.width / 2.0 - WALL_THICKNESS_MM)
    centered_section = cavity_front_face.moved(
        Pos(0.0, -cavity_front_face.center().Y, 0.0)
    )
    transition_face = centered_section.scale(section_scale).moved(
        Pos(
            0.0,
            CAVITY_FRONT_Y - TRANSITION_FRONT_MARGIN_MM,
            0.0,
        )
    )
    rear_face = centered_section.moved(
        Pos(0.0, CAVITY_FRONT_Y + CAVITY_OVERLAP_MM, 0.0)
    )

    # The first version closed the circular boundary of the conformal wall
    # with a flat disk at the black-hole crest.  That disk made the acoustic
    # cutter pass straight through the parent driver's internal collar.  Use
    # the parent's exact revolved collar boundary instead, extending only its
    # cylindrical back wall by the deliberate cavity overlap.  The visible
    # recess, collar thickness, and driver opening therefore remain the exact
    # parent geometry while the conformal surface begins at the same R87 crest.
    relief = base._black_hole_inner_relief()
    revolved_faces = [
        face for face in relief.faces() if face.geom_type == GeomType.REVOLUTION
    ]
    cylindrical_faces = [
        face for face in relief.faces() if face.geom_type == GeomType.CYLINDER
    ]
    if len(revolved_faces) != 1 or len(cylindrical_faces) != 1:
        raise ValueError(
            "Unable to isolate the parent collar's revolved and cylindrical "
            "boundary faces"
        )
    collar_revolution = copy.copy(revolved_faces[0])
    parent_cylinder = cylindrical_faces[0]
    parent_cylinder_bbox = parent_cylinder.bounding_box()
    collar_radius = parent_cylinder_bbox.size.X / 2.0
    collar_start_y = parent_cylinder_bbox.min.Y
    collar_rear_y = CAVITY_FRONT_Y + CAVITY_OVERLAP_MM
    collar_length = collar_rear_y - collar_start_y
    collar_extension = Pos(0.0, collar_start_y, 0.0) * Cylinder(
        collar_radius,
        collar_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).rotate(Axis.X, -90.0)
    extended_cylinder_faces = [
        face
        for face in collar_extension.faces()
        if face.geom_type == GeomType.CYLINDER
    ]
    if len(extended_cylinder_faces) != 1:
        raise ValueError("Unable to construct the extended parent collar wall")
    collar_cylinder = extended_cylinder_faces[0]
    collar_rear_disks = [
        face
        for face in collar_extension.faces()
        if face.geom_type == GeomType.PLANE
        and abs(face.center().Y - collar_rear_y) <= 1e-6
    ]
    if len(collar_rear_disks) != 1:
        raise ValueError("Unable to isolate the parent collar rear disk")
    rear_annulus_result = rear_face - collar_rear_disks[0]
    rear_annulus_faces = rear_annulus_result.faces()
    if len(rear_annulus_faces) != 1:
        raise ValueError("Unable to construct the annular rear cutter cap")
    rear_annulus = rear_annulus_faces[0]

    guide_edge_maker = BRepBuilderAPI_MakeEdge(
        inner_surface.VIso(CONFORMAL_TANGENT_GUIDE_V)
    )
    if not guide_edge_maker.IsDone():
        raise ValueError("Unable to build conformal tangent guide")
    guide_edge = legacy.Edge.cast(guide_edge_maker.Edge())
    if guide_edge is None or not guide_edge.is_closed:
        raise ValueError("Conformal tangent guide is not a closed edge")

    transition_builder = BRepOffsetAPI_ThruSections(False, True, 1e-7)
    transition_builder.CheckCompatibility(True)
    transition_builder.AddWire(Wire([copy.copy(outer_edge)]).wrapped)
    transition_builder.AddWire(Wire([guide_edge]).wrapped)
    transition_builder.AddWire(transition_face.outer_wire().wrapped)
    transition_builder.AddWire(rear_face.outer_wire().wrapped)
    transition_builder.Build()
    if not transition_builder.IsDone():
        raise ValueError("Unable to build the hidden conformal cavity transition")
    transition_shell = Shell.cast(transition_builder.Shape())
    if transition_shell is None or not _is_valid(transition_shell):
        raise ValueError("Hidden conformal cavity transition is invalid")

    cutter_faces = [
        inner_face,
        *transition_shell.faces(),
        collar_revolution,
        collar_cylinder,
        rear_annulus,
    ]
    sewing = BRepBuilderAPI_Sewing(1e-4)
    for face in cutter_faces:
        sewing.Add(face.wrapped)
    sewing.Perform()
    cutter_shell = Shell.cast(sewing.SewedShape())
    if cutter_shell is None:
        raise ValueError("Unable to sew the conformal and parent collar faces")
    if sewing.NbFreeEdges() != 0:
        free_edge_bounds = []
        for edge_index in range(1, sewing.NbFreeEdges() + 1):
            free_edge = legacy.Edge.cast(sewing.FreeEdge(edge_index))
            free_bbox = free_edge.bounding_box()
            free_edge_bounds.append(
                {
                    "length": free_edge.length,
                    "min": tuple(free_bbox.min),
                    "max": tuple(free_bbox.max),
                }
            )
        raise ValueError(
            "Conformal collar cutter shell remains open after sewing: "
            f"{sewing.NbFreeEdges()} free edges, "
            f"{sewing.NbContigousEdges()} contiguous edges, "
            f"{sewing.NbMultipleEdges()} multiple edges; "
            f"bounds={free_edge_bounds}"
        )
    cutter = Solid(cutter_shell).clean().fix()
    cutter = base._require_single_solid(
        cutter,
        feature="closed conformal inner acoustic-domain cutter",
    )
    if not _is_valid(cutter) or cutter.volume <= 0.0:
        raise ValueError("Conformal inner cutter is invalid")
    return cutter, inner_face, {
        **diagnostics,
        "inner_face_area_mm2": inner_face.area,
        "cutter_volume_mm3": cutter.volume,
        "cavity_overlap_mm": CAVITY_OVERLAP_MM,
        "hidden_transition_face_count": len(transition_shell.faces()),
        "hidden_transition_target": "existing R1 rectangular cavity section",
        "conformal_stop_parameter": CONFORMAL_STOP_V,
        "conformal_tangent_guide_parameter": CONFORMAL_TANGENT_GUIDE_V,
        "transition_front_margin_mm": TRANSITION_FRONT_MARGIN_MM,
        "transition_section_inset_mm": TRANSITION_SECTION_INSET_MM,
        "preserved_parent_collar_radius_mm": collar_radius,
        "preserved_parent_collar_start_y_mm": collar_start_y,
        "preserved_parent_collar_rear_y_mm": collar_rear_y,
    }


def _triangle_seam_faces(shape: Any) -> list[Face]:
    return [
        face
        for face in shape.faces()
        if abs(face.area - TRIANGLE_AREA_MM2) <= 1e-6
        and abs(face.center().Y - CAVITY_FRONT_Y) <= 1e-6
    ]


def _collar_signature(shape: Any) -> dict[str, float]:
    candidates: list[tuple[Face, list[float]]] = []
    for face in shape.faces():
        if (
            face.geom_type != GeomType.PLANE
            or abs(face.center().Y - CAVITY_FRONT_Y) > 1e-6
        ):
            continue
        radii = sorted(
            edge.radius
            for edge in face.edges()
            if edge.geom_type == GeomType.CIRCLE
        )
        if len(radii) == 2 and radii[-1] > 50.0:
            candidates.append((face, radii))
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one driver collar annulus, found {len(candidates)}"
        )
    face, radii = candidates[0]
    return {
        "rear_face_y_mm": face.center().Y,
        "rear_face_area_mm2": face.area,
        "through_opening_radius_mm": radii[0],
        "outer_radius_mm": radii[1],
        "radial_width_mm": radii[1] - radii[0],
    }


def _geometric_half_cutaway(shape: Any) -> Compound:
    """Return an actual X<=0 face cut, independent of viewer clipping state."""
    bbox = shape.bounding_box()
    margin = 2.0
    clip = Pos(
        (bbox.min.X - margin) / 2.0,
        (bbox.min.Y + bbox.max.Y) / 2.0,
        (bbox.min.Z + bbox.max.Z) / 2.0,
    ) * Box(
        -bbox.min.X + margin,
        bbox.size.Y + 2.0 * margin,
        bbox.size.Z + 2.0 * margin,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    fragments: list[Face] = []
    for face in shape.faces():
        clipped = face & clip
        if clipped is None:
            continue
        fragments.extend(
            fragment
            for fragment in clipped.faces()
            if fragment.area > 1e-8
        )
    if not fragments or not all(_is_valid(face) for face in fragments):
        raise ValueError("Geometric face cutaway is empty or invalid")
    cutaway = Compound(children=fragments)
    if cutaway.bounding_box().max.X > 1e-6 or not _is_valid(cutaway):
        raise ValueError("Geometric face cutaway escaped its X<=0 half-space")
    return cutaway


def _export_and_check(exports: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for filename, shape in exports.items():
        path = OUT / filename
        export_step(shape, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        imported_solids = imported.solids()
        imported_faces = imported.faces()
        source_count = len(shape.solids())
        source_face_count = len(shape.faces())
        checks[filename] = {
            "source_solid_count": source_count,
            "imported_solid_count": len(imported_solids),
            "solid_count_matches": len(imported_solids) == source_count,
            "all_imported_solids_valid": all(
                _is_valid(solid) for solid in imported_solids
            ),
            "source_face_count": source_face_count,
            "imported_face_count": len(imported_faces),
            "face_count_matches": len(imported_faces) == source_face_count,
            "all_imported_faces_valid": all(
                _is_valid(face) for face in imported_faces
            ),
        }
        if (
            not checks[filename]["solid_count_matches"]
            or not checks[filename]["all_imported_solids_valid"]
            or not checks[filename]["face_count_matches"]
            or not checks[filename]["all_imported_faces_valid"]
        ):
            raise ValueError(f"STEP round-trip failed for {filename}")
    return checks


def _generate_viewers() -> None:
    for source, viewer_name, face_only in (
        ("parabolic_g1_conformal_inner_enclosure.step", "viewer", True),
        (
            "parabolic_g1_conformal_inner_enclosure_cutaway.step",
            "cutaway_viewer",
            False,
        ),
    ):
        viewer_dir = OUT / viewer_name
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_static_ocp_viewer.py"),
                str(OUT / source),
                "--out",
                str(viewer_dir),
            ],
            check=True,
        )
        cad._set_viewer_edge_mode(viewer_dir, face_only=face_only)
        if viewer_name == "cutaway_viewer":
            model_data = viewer_dir / "model-data.js"
            payload = model_data.read_bytes()
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
            if (
                b'"reset_camera":"keep"' not in payload
                or b'"position":[600.0,-350.0,350.0]' not in payload
                or b'"renderback":false' in payload
            ):
                raise ValueError("Unable to configure the geometric cutaway viewer")
            model_data.write_bytes(payload)


def generate() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    outer_cutter, outer_fairing_face, outer_fairing_topology = (
        parent._g1_cutter()
    )
    outer_boundary_targets = [
        (
            legacy._outer_radius(
                math.tau * index / parent.ANGULAR_SAMPLE_COUNT
            )
            * math.cos(math.tau * index / parent.ANGULAR_SAMPLE_COUNT),
            FRONT_Y,
            legacy._outer_radius(
                math.tau * index / parent.ANGULAR_SAMPLE_COUNT
            )
            * math.sin(math.tau * index / parent.ANGULAR_SAMPLE_COUNT),
        )
        for index in range(parent.ANGULAR_SAMPLE_COUNT)
    ]
    outer_boundary_poles = legacy._periodic_interpolation_poles(
        outer_boundary_targets
    )
    body, body_topology = legacy._outer_body(outer_boundary_poles)
    sculpted_outer = base._require_single_solid(
        (body - outer_cutter).clean().fix(),
        feature="unchanged preferred parabolic G1 outer envelope",
    )
    old_enclosure = legacy._aesthetic_shell(sculpted_outer)
    old_triangle_faces = _triangle_seam_faces(old_enclosure)
    if len(old_triangle_faces) != 4:
        raise ValueError(
            f"Expected four parent triangle seams, found {len(old_triangle_faces)}"
        )

    conformal_cutter, inner_face, inner_topology = (
        _conformal_cavity_cutter()
    )
    cavity = base._rectangular_cavity()
    relief = base._black_hole_inner_relief()
    sand_void = base._sand_void()

    outer_bbox = sculpted_outer.bounding_box()
    front_clip_min_y = outer_bbox.min.Y - 1.0
    front_clip_max_y = CAVITY_FRONT_Y + CAVITY_OVERLAP_MM
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
        feature="solid preferred-front reconstruction blank",
    )
    front_blank = base._require_single_solid(
        (
            front_blank
            - sand_void
            - cavity
            - base._black_hole_visible_tool()
        ).clean().fix(),
        feature=(
            "front reconstruction with preserved sand, rear cavity, and "
            "visible recess"
        ),
    )
    restored_shell = base._require_single_solid(
        (old_enclosure + front_blank - sand_void).clean().fix(),
        feature="preferred enclosure with front acoustic region restored",
    )

    enclosure = base._require_single_solid(
        (
            _subtract_periodic_cutter(
                restored_shell,
                conformal_cutter,
            )
            - sand_void
        ).clean().fix(),
        feature="parabolic G1 enclosure with conformal inner front wall",
    )
    remaining_triangle_faces = _triangle_seam_faces(enclosure)
    if remaining_triangle_faces:
        raise ValueError("Triangular inner seam faces remain after the fix")
    if not _is_valid(enclosure):
        raise ValueError("Conformal-inner enclosure is invalid")

    parent_collar = _collar_signature(old_enclosure)
    preserved_collar = _collar_signature(enclosure)
    for dimension in (
        "rear_face_y_mm",
        "rear_face_area_mm2",
        "through_opening_radius_mm",
        "outer_radius_mm",
        "radial_width_mm",
    ):
        if abs(parent_collar[dimension] - preserved_collar[dimension]) > 1e-6:
            raise ValueError(
                f"Driver collar changed at {dimension}: "
                f"{parent_collar[dimension]:.9f} -> "
                f"{preserved_collar[dimension]:.9f}"
            )
    cutaway = _geometric_half_cutaway(enclosure)

    acoustic_volume_change_l = (
        old_enclosure.volume - enclosure.volume
    ) / 1_000_000.0
    baseline_net_volume_l = 4.398
    estimated_net_volume_l = baseline_net_volume_l + acoustic_volume_change_l
    baseline_tuning_hz = 39.21
    estimated_tuning_hz = baseline_tuning_hz * math.sqrt(
        baseline_net_volume_l / estimated_net_volume_l
    )
    restored_front_material_mm3 = max(
        0.0,
        restored_shell.volume - old_enclosure.volume,
    )
    conformal_cutter_removal_mm3 = max(
        0.0,
        restored_shell.volume - enclosure.volume,
    )
    cavity_front_face = max(
        (
            face
            for face in cavity.faces()
            if abs(face.center().Y - CAVITY_FRONT_Y) <= 1e-6
        ),
        key=lambda face: face.area,
    )
    cavity_overlap_mm3 = cavity_front_face.area * CAVITY_OVERLAP_MM
    preserved_sand_void_material_mm3 = _shape_volume(enclosure & sand_void)
    if preserved_sand_void_material_mm3 > 1e-6:
        raise ValueError(
            "Corrected enclosure fills part of the preserved sand void: "
            f"{preserved_sand_void_material_mm3:.9f} mm3"
        )

    exports = {
        "parabolic_g1_conformal_inner_enclosure.step": enclosure,
        "parabolic_g1_conformal_inner_enclosure_cutaway.step": cutaway,
    }
    step_roundtrip = _export_and_check(exports)
    _generate_viewers()

    measurement = legacy._finished_measurement(sculpted_outer)
    diagnostics = {
        "name": NAME,
        "status": "enclosure-only conformal-inner-wall correction",
        "isolation": {
            "preferred_parent_experiment_modified": False,
            "authoritative_rear_corner_variant_modified": False,
            "shared_upstream_generators_modified": False,
        },
        "exterior": {
            "construction": "bit-for-bit reuse of preferred parent outer cutter",
            "fairing_face_area_mm2": outer_fairing_face.area,
            "corner_pullback_mm": measurement["finished_corner_pullback_mm"],
            "edge_midpoint_pullback_mm": measurement[
                "edge_midpoint_pullback_mm"
            ],
            "black_hole_crest_y_mm": measurement["black_hole_crest_y_mm"],
            "body_topology": body_topology,
            "fairing_topology": outer_fairing_topology,
        },
        "inner_wall": {
            **inner_topology,
            "inner_face_area_mm2": inner_face.area,
            "driver_relief_front_y_mm": relief.bounding_box().min.Y,
            "cavity_front_y_mm": CAVITY_FRONT_Y,
        },
        "preserved_black_hole_and_driver_collar": {
            "construction": (
                "exact parent visible recess plus exact parent revolved and "
                "cylindrical collar boundary"
            ),
            "parent_signature": parent_collar,
            "corrected_signature": preserved_collar,
            "signature_maximum_difference_mm_or_mm2": max(
                abs(parent_collar[key] - preserved_collar[key])
                for key in parent_collar
            ),
            "through_opening_diameter_mm": (
                2.0 * preserved_collar["through_opening_radius_mm"]
            ),
            "collar_outer_diameter_mm": (
                2.0 * preserved_collar["outer_radius_mm"]
            ),
            "collar_axial_length_mm": (
                CAVITY_FRONT_Y
                - inner_topology["preserved_parent_collar_start_y_mm"]
            ),
            "crest_diameter_mm": base.BLACK_HOLE_OUTER_D,
            "crest_to_collar_rear_depth_mm": (
                preserved_collar["rear_face_y_mm"]
                - measurement["black_hole_crest_y_mm"]
            ),
        },
        "triangle_seam_correction": {
            "parent_triangle_face_count": len(old_triangle_faces),
            "parent_triangle_area_each_mm2": TRIANGLE_AREA_MM2,
            "remaining_triangle_face_count": len(remaining_triangle_faces),
            "root_cause": (
                "square-clipped inner relief and R1 rounded cavity only "
                "touched at a coplanar seam"
            ),
        },
        "clearance_and_interference": {
            "positive_overlap_with_cavity_mm3": cavity_overlap_mm3,
            "legacy_inner_relief_replaced_in_front_zone": True,
            "restored_front_material_before_recavity_mm3": (
                restored_front_material_mm3
            ),
            "conformal_cutter_material_removal_mm3": (
                conformal_cutter_removal_mm3
            ),
            "material_remaining_inside_preserved_sand_void_mm3": (
                preserved_sand_void_material_mm3
            ),
            "minimum_hidden_transition_inset_mm": (
                TRANSITION_SECTION_INSET_MM
            ),
        },
        "acoustic_effect": {
            "modeled_acoustic_volume_change_l": acoustic_volume_change_l,
            "baseline_modeled_net_volume_l": baseline_net_volume_l,
            "estimated_corrected_net_volume_l": estimated_net_volume_l,
            "baseline_port_physical_length_mm": 526.4,
            "corrected_port_physical_length_mm": 526.4,
            "baseline_modeled_natural_tuning_hz": baseline_tuning_hz,
            "estimated_corrected_natural_tuning_hz": estimated_tuning_hz,
            "estimated_tuning_change_hz": (
                estimated_tuning_hz - baseline_tuning_hz
            ),
            "estimate_basis": (
                "unchanged port and omitted internal assemblies; Helmholtz "
                "frequency scaled by sqrt(baseline volume / corrected volume)"
            ),
        },
        "printability": {
            "target_front_transition_wall_mm": WALL_THICKNESS_MM,
            "minimum_sampled_front_transition_wall_mm": inner_topology[
                "minimum_sampled_wall_thickness_mm"
            ],
            "new_undercuts": False,
            "support_assessment": (
                "continuous conformal inner surface with no coplanar seam"
            ),
        },
        "geometry": {
            "conformal_cutter_valid": _is_valid(conformal_cutter),
            "enclosure_valid": _is_valid(enclosure),
            "enclosure_solid_count": len(enclosure.solids()),
            "cutaway_valid": _is_valid(cutaway),
            "cutaway_face_count": len(cutaway.faces()),
            "cutaway_method": (
                "actual X<=0 geometric face intersection exported as its own "
                "round-trip-validated STEP"
            ),
            "step_roundtrip": step_roundtrip,
        },
        "omitted_from_preview": [
            "woofer",
            "internal port and absorber",
            "serviceable tower and flare",
            "horn and compression driver",
            "GX16 and fill hardware",
            "internal brace network",
        ],
        "files": {
            **{filename: str(OUT / filename) for filename in exports},
            "diagnostics": str(OUT / "diagnostics.json"),
            "exterior_viewer": str(OUT / "viewer" / "index.html"),
            "cutaway_viewer": str(OUT / "cutaway_viewer" / "index.html"),
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    print(json.dumps(generate(), indent=2))


if __name__ == "__main__":
    main()
