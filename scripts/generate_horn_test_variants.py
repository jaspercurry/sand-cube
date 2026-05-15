"""Generate clearly named STEP variants for debugging horn import topology.

These files are intentionally written under ``build/test_variants``. They are
not production geometry; they isolate one modeling choice at a time so we can
compare Onshape import behavior against local OpenCascade validity checks.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

from build123d import Align, Cylinder, Location, Mode, Solid, export_step
from OCP.BOPAlgo import BOPAlgo_CheckerSI
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCP.GC import GC_MakeArcOfCircle
from OCP.GeomAbs import (
    GeomAbs_BSplineCurve,
    GeomAbs_BSplineSurface,
    GeomAbs_Circle,
    GeomAbs_Cylinder,
    GeomAbs_Line,
    GeomAbs_Plane,
    GeomAbs_SurfaceOfRevolution,
    GeomAbs_Torus,
)
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt
from OCP.STEPControl import STEPControl_Reader
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_SHELL, TopAbs_SOLID
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from params import p
from src.features.horn import (
    _cylinder_z,
    _primary_shape,
    _revolved_meridian_body,
    build_jmlc_horn,
    horn_dimensions,
    jmlc_profile_points,
)


OUT = Path("build/test_variants")

SURFACE_NAMES = {
    GeomAbs_Plane: "Plane",
    GeomAbs_Cylinder: "Cylinder",
    GeomAbs_Torus: "Torus",
    GeomAbs_BSplineSurface: "BSplineSurface",
    GeomAbs_SurfaceOfRevolution: "SurfaceOfRevolution",
}

CURVE_NAMES = {
    GeomAbs_Line: "Line",
    GeomAbs_Circle: "Circle",
    GeomAbs_BSplineCurve: "BSplineCurve",
}


def _line_edge(start: tuple[float, float], end: tuple[float, float]):
    return BRepBuilderAPI_MakeEdge(
        gp_Pnt(start[0], 0, start[1]),
        gp_Pnt(end[0], 0, end[1]),
    ).Edge()


def _arc_edge(
    start: tuple[float, float],
    mid: tuple[float, float],
    end: tuple[float, float],
):
    arc = GC_MakeArcOfCircle(
        gp_Pnt(start[0], 0, start[1]),
        gp_Pnt(mid[0], 0, mid[1]),
        gp_Pnt(end[0], 0, end[1]),
    ).Value()
    return BRepBuilderAPI_MakeEdge(arc).Edge()


def _spline_edge(points: list[tuple[float, float]]):
    point_array = TColgp_Array1OfPnt(1, len(points))
    for index, (radius, z) in enumerate(points, 1):
        point_array.SetValue(index, gp_Pnt(radius, 0, z))
    curve = GeomAPI_PointsToBSpline(point_array).Curve()
    return BRepBuilderAPI_MakeEdge(curve).Edge()


def _split_revolved_meridian_body(
    profile: list[tuple[float, float]],
    *,
    split_index: int,
    wall_t: float,
    throat_overlap: float,
    mouth_round_r: float,
) -> Solid:
    """Revolve one meridian, but split each long spline at the rollback apex.

    This preserves the exact same sample points and profile, but gives STEP
    importers shorter faces instead of one high-degree revolved spline spanning
    the forward-and-back rollback region.
    """
    outer = [(radius + wall_t, z) for radius, z in profile]
    cap_r = min(mouth_round_r, wall_t / 2)
    throat_inner = (profile[0][0], profile[0][1] - throat_overlap)
    throat_outer = (outer[0][0], outer[0][1] - throat_overlap)
    cap_mid = (
        (profile[-1][0] + outer[-1][0]) / 2,
        profile[-1][1] - cap_r,
    )

    wire_maker = BRepBuilderAPI_MakeWire()
    wire_maker.Add(_line_edge(throat_inner, profile[0]))
    wire_maker.Add(_spline_edge(profile[: split_index + 1]))
    wire_maker.Add(_spline_edge(profile[split_index:]))
    wire_maker.Add(_arc_edge(profile[-1], cap_mid, outer[-1]))
    wire_maker.Add(_spline_edge(list(reversed(outer[split_index:]))))
    wire_maker.Add(_spline_edge(list(reversed(outer[: split_index + 1]))))
    wire_maker.Add(_line_edge(outer[0], throat_outer))
    wire_maker.Add(_line_edge(throat_outer, throat_inner))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make split horn meridian wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make split horn meridian face")
    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve split horn meridian face")
    body = Solid.cast(revolved.Shape())
    if body is None or not body.is_valid:
        raise ValueError("Split revolved horn body is not a valid solid")
    return body


def _profile(*, exit_angle_deg: float | None = None):
    mouth_inner_r = p.horn_mouth_outer_d / 2 - p.horn_wall_t
    return jmlc_profile_points(
        throat_d=p.horn_throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=p.horn_exit_angle_deg
        if exit_angle_deg is None
        else exit_angle_deg,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=p.horn_profile_step,
    )[0]


def _body_current(
    profile: list[tuple[float, float]],
    *,
    mouth_round_r: float | None = None,
):
    return _revolved_meridian_body(
        profile,
        wall_t=p.horn_wall_t,
        throat_overlap=min(1.0, p.horn_flange_t * 0.2),
        mouth_round_r=p.horn_lip_r if mouth_round_r is None else mouth_round_r,
    )


def _add_flange_and_cuts(
    body,
    profile: list[tuple[float, float]],
    *,
    bolt_holes: bool,
):
    length = max(z for _radius, z in profile)
    flange = Cylinder(
        radius=p.horn_flange_d / 2,
        height=p.horn_flange_t,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    flange = Location((0, 0, -p.horn_flange_t / 2)) * flange
    horn = _primary_shape((body + flange).clean().fix())
    horn -= _cylinder_z(
        diameter=p.horn_throat_d + 0.2,
        depth=length + p.horn_flange_t + 4.0,
        center=(0, 0, (length - p.horn_flange_t) / 2),
    )
    horn = _primary_shape(horn.clean().fix())
    if not bolt_holes:
        return horn

    for index in range(3):
        angle = math.tau * index / 3 + math.pi / 2
        radius = p.horn_bolt_3_bcd / 2
        horn -= _cylinder_z(
            diameter=p.horn_bolt_clearance_d,
            depth=p.horn_flange_t + 2.0,
            center=(
                radius * math.cos(angle),
                radius * math.sin(angle),
                -p.horn_flange_t / 2,
            ),
        )
        horn = _primary_shape(horn.clean().fix())

    for angle in (0.0, math.pi):
        radius = p.horn_bolt_2_bcd / 2
        horn -= _cylinder_z(
            diameter=p.horn_bolt_clearance_d,
            depth=p.horn_flange_t + 2.0,
            center=(
                radius * math.cos(angle),
                radius * math.sin(angle),
                -p.horn_flange_t / 2,
            ),
        )
        horn = _primary_shape(horn.clean().fix())
    return horn


def _read_step_shape(path: Path):
    reader = STEPControl_Reader()
    status = reader.ReadFile(str(path))
    transferred = reader.TransferRoots()
    return reader.OneShape(), str(status), transferred


def _count(shape, kind) -> int:
    explorer = TopExp_Explorer(shape, kind)
    total = 0
    while explorer.More():
        total += 1
        explorer.Next()
    return total


def _audit_step(path: Path) -> dict[str, object]:
    shape, read_status, transferred = _read_step_shape(path)
    checker = BOPAlgo_CheckerSI()
    checker.AddArgument(shape)
    checker.SetLevelOfCheck(9)
    checker.Perform()

    edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(
        shape,
        TopAbs_EDGE,
        TopAbs_FACE,
        edge_face_map,
    )
    edge_face_counts = [
        edge_face_map.FindFromIndex(index).Extent()
        for index in range(1, edge_face_map.Extent() + 1)
    ]
    edge_use_histogram = Counter(edge_face_counts)

    face_type_histogram: Counter[str] = Counter()
    face_areas = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, props)
        surface = BRepAdaptor_Surface(face, True)
        face_type = SURFACE_NAMES.get(surface.GetType(), str(surface.GetType()))
        face_type_histogram[face_type] += 1
        face_areas.append(round(props.Mass(), 6))
        explorer.Next()

    edge_lengths = []
    edge_tolerances = []
    edge_type_histogram: Counter[str] = Counter()
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        props = GProp_GProps()
        BRepGProp.LinearProperties_s(edge, props)
        curve = BRepAdaptor_Curve(edge)
        edge_type = CURVE_NAMES.get(curve.GetType(), str(curve.GetType()))
        edge_type_histogram[edge_type] += 1
        edge_lengths.append(props.Mass())
        edge_tolerances.append(BRep_Tool.Tolerance_s(edge))
        explorer.Next()

    return {
        "step_file": str(path),
        "read_status": read_status,
        "transferred_roots": transferred,
        "valid": BRepCheck_Analyzer(shape, True).IsValid(),
        "self_interference_errors": checker.HasErrors(),
        "counts": {
            "solids": _count(shape, TopAbs_SOLID),
            "shells": _count(shape, TopAbs_SHELL),
            "faces": _count(shape, TopAbs_FACE),
            "edges": _count(shape, TopAbs_EDGE),
        },
        "face_type_histogram": dict(sorted(face_type_histogram.items())),
        "edge_type_histogram": dict(sorted(edge_type_histogram.items())),
        "edge_face_use_histogram": {
            str(key): value for key, value in sorted(edge_use_histogram.items())
        },
        "boundary_edge_count": sum(1 for count in edge_face_counts if count == 1),
        "non_manifold_edge_count": sum(
            1 for count in edge_face_counts if count > 2
        ),
        "shortest_edge_mm": round(min(edge_lengths), 6),
        "edges_under_1mm": sum(1 for length in edge_lengths if length < 1.0),
        "edges_under_3mm": sum(1 for length in edge_lengths if length < 3.0),
        "max_edge_tolerance_mm": max(edge_tolerances),
        "smallest_face_area_mm2": min(face_areas),
    }


def _variant(name: str, description: str, part) -> dict[str, object]:
    path = OUT / f"{name}.step"
    export_step(part, str(path))
    audit = _audit_step(path)
    return {
        "name": name,
        "description": description,
        "path": str(path.resolve()),
        "build123d": horn_dimensions(part),
        "audit": audit,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    current = _profile()
    current_split_index = max(range(len(current)), key=lambda i: current[i][1])
    no_rollback = _profile(exit_angle_deg=90.0)
    no_rollback_split_index = max(
        range(len(no_rollback)),
        key=lambda i: no_rollback[i][1],
    )

    current_body = _body_current(current)
    flat_body = _body_current(current, mouth_round_r=0.0)
    split_body = _split_revolved_meridian_body(
        current,
        split_index=current_split_index,
        wall_t=p.horn_wall_t,
        throat_overlap=min(1.0, p.horn_flange_t * 0.2),
        mouth_round_r=p.horn_lip_r,
    )
    no_rollback_body = _split_revolved_meridian_body(
        no_rollback,
        split_index=no_rollback_split_index,
        wall_t=p.horn_wall_t,
        throat_overlap=min(1.0, p.horn_flange_t * 0.2),
        mouth_round_r=p.horn_lip_r,
    )

    variants = [
        _variant(
            "test_variant_01_current_full_model",
            "Production horn exactly as src/enclosure.py exports it now.",
            build_jmlc_horn(
                throat_d=p.horn_throat_d,
                mouth_outer_d=p.horn_mouth_outer_d,
                wall_t=p.horn_wall_t,
                exit_angle_deg=p.horn_exit_angle_deg,
                wavefront_t=p.horn_wavefront_t,
                throat_angle_deg=p.horn_throat_angle_deg,
                step=p.horn_profile_step,
                lip_r=p.horn_lip_r,
                flange_d=p.horn_flange_d,
                flange_t=p.horn_flange_t,
                bolt_clearance_d=p.horn_bolt_clearance_d,
                bolt_3_bcd=p.horn_bolt_3_bcd,
                bolt_2_bcd=p.horn_bolt_2_bcd,
            ),
        ),
        _variant(
            "test_variant_02_body_only_current_rounded_mouth",
            "Horn wall only: 140 degree rollback, rounded mouth, no flange, no cuts.",
            current_body,
        ),
        _variant(
            "test_variant_03_body_only_flat_mouth",
            "Horn wall only: 140 degree rollback, flat mouth bridge instead of rounded return.",
            flat_body,
        ),
        _variant(
            "test_variant_04_full_no_bolt_holes",
            "Current rounded body plus flange and throat cut, but no bolt-hole booleans.",
            _add_flange_and_cuts(current_body, current, bolt_holes=False),
        ),
        _variant(
            "test_variant_05_full_flat_mouth_no_bolt_holes",
            "Flat-mouth body plus flange and throat cut, but no bolt-hole booleans.",
            _add_flange_and_cuts(flat_body, current, bolt_holes=False),
        ),
        _variant(
            "test_variant_06_body_split_at_rollback_apex",
            "Horn wall only, same 140 degree profile, but inner/outer splines split at max-depth apex.",
            split_body,
        ),
        _variant(
            "test_variant_07_full_split_at_rollback_no_bolt_holes",
            "Split-at-apex body plus flange and throat cut, but no bolt-hole booleans.",
            _add_flange_and_cuts(split_body, current, bolt_holes=False),
        ),
        _variant(
            "test_variant_08_no_rollback_90deg_body_only",
            "Control: same mouth and throat, but 90 degree non-rollback body with split meridian.",
            no_rollback_body,
        ),
    ]

    summary = {
        "purpose": (
            "Import these STEP files into Onshape one at a time to isolate "
            "which horn topology feature triggers Imported parts contained "
            "faults."
        ),
        "rollback_apex": {
            "index": current_split_index,
            "radius_mm": round(current[current_split_index][0], 3),
            "z_mm": round(current[current_split_index][1], 3),
        },
        "variants": variants,
    }
    (OUT / "test_variant_audit.json").write_text(json.dumps(summary, indent=2))

    readme_lines = [
        "# Horn STEP Test Variants",
        "",
        "Import these files into Onshape one at a time. They are diagnostic",
        "variants, not production exports.",
        "",
        "| File | What It Isolates |",
        "|---|---|",
    ]
    for item in variants:
        readme_lines.append(
            f"| `{Path(item['path']).name}` | {item['description']} |"
        )
    readme_lines.extend(
        [
            "",
            "Also see `test_variant_audit.json` for local OpenCascade validity,",
            "self-interference, edge-use, and face/edge type checks.",
            "",
            "Suggested Onshape import order:",
            "",
            "1. `test_variant_02_body_only_current_rounded_mouth.step`",
            "2. `test_variant_03_body_only_flat_mouth.step`",
            "3. `test_variant_06_body_split_at_rollback_apex.step`",
            "4. `test_variant_04_full_no_bolt_holes.step`",
            "5. `test_variant_07_full_split_at_rollback_no_bolt_holes.step`",
            "6. `test_variant_01_current_full_model.step`",
            "",
            "If the body-only file fails, the issue is the revolved horn wall.",
            "If body-only passes but full/no-bolts fails, the issue is the",
            "flange/throat boolean. If only the current full model fails, the",
            "bolt-hole booleans or their interaction with the flange are suspect.",
        ]
    )
    (OUT / "README.md").write_text("\n".join(readme_lines) + "\n")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
