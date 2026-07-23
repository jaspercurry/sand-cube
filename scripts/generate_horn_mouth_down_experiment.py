"""Export an experimental mouth-down JMLC horn with a shaped cradle."""

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
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build123d import Align, Cylinder, Location, Mode, Solid, export_stl
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeWire,
)
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.gp import gp_Ax1, gp_Dir, gp_Pln, gp_Pnt, gp_Vec
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

from params import p
from src.features.horn_support_experiment import (
    _cylinder_z,
    _line_edge,
    _primary_shape,
    _revolved_acoustic_void,
    _revolved_closed_profile,
    _revolved_meridian_body,
    _spline_edge,
    _to_nurbs_solid,
    build_jmlc_horn,
    horn_dimensions,
    jmlc_profile_metadata,
    jmlc_profile_points,
)


OUT = ROOT / "build" / "experiments" / "jmlc_horn_mouth_down_experiment"
VERSION = "v38"
TARGET_PRINTED_OUTER_D = 220.0
# Keep this calibrated value from the upright 220 mm work: it compensates for
# the rolled-back lip finishing slightly inside the construction mouth diameter.
EXPERIMENTAL_MOUTH_OUTER_D = 221.74
EXPERIMENTAL_EXIT_ANGLE_DEG = 150.0

# The cradle supports the rolled-back mouth band and reaches inward far enough
# to keep the visible mouth curve from starting as a long unsupported overhang.
CRADLE_INNER_R = 60.0
CRADLE_OUTER_R = 109.8
CRADLE_PROFILE_SAMPLES = 256
CRADLE_ANGULAR_SEGMENTS = 720
CRADLE_CONTACT_SEARCH_WINDOW = 0.18
CRADLE_MIN_TOP_Z = 2.0
INTERFACE_H = 0.40
INTERFACE_HORN_CLEARANCE = 0.04
INTERFACE_CRADLE_CLEARANCE = 0.04
EXPERIMENTAL_REAR_FLANGE_D = 96.0
REAR_FAIRING_MAX_DR_DZ = 0.65
REAR_FAIRING_START_DR_DZ = -0.15
REAR_FAIRING_WAIST_Z = 38.0
REAR_FAIRING_WAIST_CLEARANCE = 1.35
REAR_FAIRING_SMOOTH_BLEND_Z = 48.0
OUTER_BOLT_COUNTERBORE_D = 24.0
OUTER_BOLT_COUNTERBORE_FLOOR_T = 3.0
OUTER_BOLT_COUNTERBORE_TOP_Z = REAR_FAIRING_WAIST_Z
OUTER_BOLT_CUTAWAY_TAPER_START_Z = 8.0
OUTER_BOLT_CUTAWAY_TIP_OVERLAP = 0.05
STL_LINEAR_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.04


Triangle = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


def _bbox_from_mesh(triangles: list[Triangle]) -> dict[str, list[float]]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for _normal, p1, p2, p3 in triangles:
        for point in (p1, p2, p3):
            for axis, value in enumerate(point):
                mins[axis] = min(mins[axis], value)
                maxs[axis] = max(maxs[axis], value)
    return {
        "min": [round(value, 3) for value in mins],
        "max": [round(value, 3) for value in maxs],
        "size": [round(maxs[i] - mins[i], 3) for i in range(3)],
    }


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {
        "min": [round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
        "max": [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
        "size": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
    }


def _z_shifted(shape, z_shift: float):
    return Location((0, 0, z_shift)) * shape


def _extruded_xy_polygon(
    points: list[tuple[float, float]],
    *,
    bottom_z: float,
    height: float,
) -> Solid:
    if len(points) < 4:
        raise ValueError("A planar cut polygon needs at least four points")
    if height <= 0:
        raise ValueError("A planar cut polygon needs positive height")

    polygon = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        polygon.Add(gp_Pnt(x, y, bottom_z))
    polygon.Close()
    if not polygon.IsDone():
        raise ValueError("Unable to create planar cut polygon")

    face_maker = BRepBuilderAPI_MakeFace(polygon.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to create planar cut face")

    prism = BRepPrimAPI_MakePrism(face_maker.Face(), gp_Vec(0, 0, height), True)
    if not prism.IsDone():
        raise ValueError("Unable to extrude planar cut")
    solid = Solid.cast(prism.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Extruded planar cut is not a valid solid")
    return solid


def _capsule_points(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    radius: float,
    arc_segments: int = 24,
) -> list[tuple[float, float]]:
    """Return a rounded slot footprint around a line segment in the XY plane."""
    if radius <= 0:
        raise ValueError("Capsule radius must be positive")
    if arc_segments < 6:
        raise ValueError("Capsule arc needs enough segments")

    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy)
    if length <= 1e-6:
        raise ValueError("Capsule start and end must differ")

    direction = math.atan2(dy, dx)
    points: list[tuple[float, float]] = []
    for index in range(arc_segments + 1):
        theta = direction + math.pi / 2 - math.pi * index / arc_segments
        points.append((ex + radius * math.cos(theta), ey + radius * math.sin(theta)))
    for index in range(arc_segments + 1):
        theta = direction - math.pi / 2 - math.pi * index / arc_segments
        points.append((sx + radius * math.cos(theta), sy + radius * math.sin(theta)))
    return points


def _spline_edge_3d(points: list[tuple[float, float, float]]):
    point_array = TColgp_Array1OfPnt(1, len(points))
    for index, (x, y, z) in enumerate(points, 1):
        point_array.SetValue(index, gp_Pnt(x, y, z))
    curve = GeomAPI_PointsToBSpline(point_array).Curve()
    return BRepBuilderAPI_MakeEdge(curve).Edge()


def _line_edge_3d(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
):
    return BRepBuilderAPI_MakeEdge(
        gp_Pnt(*start),
        gp_Pnt(*end),
    ).Edge()


def _tapered_cutter_z(
    *,
    center_xy: tuple[float, float],
    bottom_z: float,
    taper_start_z: float,
    top_z: float,
    full_radius: float,
    tip_radius: float,
    samples: int = 28,
) -> Solid:
    """Create a vertical variable-radius cutter around a local Z axis."""
    if not bottom_z < taper_start_z < top_z:
        raise ValueError("Tapered cutter Z stations must be strictly ordered")
    if not 0 < tip_radius < full_radius:
        raise ValueError("Tapered cutter tip radius must be smaller than full radius")
    if samples < 8:
        raise ValueError("Tapered cutter needs enough samples")

    cx, cy = center_xy
    axis_bottom = (cx, cy, bottom_z)
    axis_top = (cx, cy, top_z)
    outer_bottom = (cx + full_radius, cy, bottom_z)
    outer_taper_start = (cx + full_radius, cy, taper_start_z)
    outer_top = (cx + tip_radius, cy, top_z)

    taper_points: list[tuple[float, float, float]] = []
    for index in range(samples):
        u = index / (samples - 1)
        smooth = 3 * u**2 - 2 * u**3
        z = taper_start_z + (top_z - taper_start_z) * u
        radius = full_radius + (tip_radius - full_radius) * smooth
        taper_points.append((cx + radius, cy, z))

    wire_maker = BRepBuilderAPI_MakeWire()
    for start, end in (
        (axis_bottom, outer_bottom),
        (outer_bottom, outer_taper_start),
    ):
        wire_maker.Add(_line_edge_3d(start, end))
    wire_maker.Add(_spline_edge_3d(taper_points))
    for start, end in (
        (outer_top, axis_top),
        (axis_top, axis_bottom),
    ):
        wire_maker.Add(_line_edge_3d(start, end))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make tapered cutter profile wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make tapered cutter profile face")
    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(cx, cy, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve tapered cutter")
    solid = Solid.cast(revolved.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Tapered cutter did not produce a valid solid")
    return solid


def _read_binary_stl_triangles(path: Path) -> list[Triangle]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + triangle_count * 50
    if expected != len(data):
        raise ValueError(f"{path} does not look like a binary STL")

    triangles: list[Triangle] = []
    offset = 84
    for _index in range(triangle_count):
        normal = struct.unpack_from("<fff", data, offset)
        offset += 12
        vertices = []
        for _vertex in range(3):
            vertices.append(struct.unpack_from("<fff", data, offset))
            offset += 12
        offset += 2
        triangles.append((normal, vertices[0], vertices[1], vertices[2]))
    return triangles


def _triangle_normal(
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    p3: tuple[float, float, float],
) -> tuple[float, float, float]:
    ax, ay, az = (p2[i] - p1[i] for i in range(3))
    bx, by, bz = (p3[i] - p1[i] for i in range(3))
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length <= 1e-12:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def _write_binary_stl_triangles(path: Path, triangles: list[Triangle]) -> None:
    header = f"{path.stem} generated by generate_horn_mouth_down_experiment".encode()
    header = header[:80].ljust(80, b" ")
    with path.open("wb") as fh:
        fh.write(header)
        fh.write(struct.pack("<I", len(triangles)))
        for _normal, p1, p2, p3 in triangles:
            normal = _triangle_normal(p1, p2, p3)
            fh.write(struct.pack("<fff", *normal))
            fh.write(struct.pack("<fff", *p1))
            fh.write(struct.pack("<fff", *p2))
            fh.write(struct.pack("<fff", *p3))
            fh.write(struct.pack("<H", 0))


def _revolved_band_triangles(
    lower_profile: list[tuple[float, float]],
    upper_profile: list[tuple[float, float]],
    *,
    angular_segments: int,
) -> list[Triangle]:
    """Make a closed annular solid mesh between two radial/z profiles."""
    if len(lower_profile) != len(upper_profile):
        raise ValueError("Lower and upper profiles must have the same sample count")
    if len(lower_profile) < 2:
        raise ValueError("Revolved band profiles need at least two samples")
    if angular_segments < 24:
        raise ValueError("Revolved band needs enough angular segments")

    def point(
        profile: list[tuple[float, float]],
        index: int,
        segment: int,
    ) -> tuple[float, float, float]:
        radius, z = profile[index]
        theta = math.tau * segment / angular_segments
        return (radius * math.cos(theta), radius * math.sin(theta), z)

    triangles: list[Triangle] = []
    last = len(lower_profile) - 1
    for segment in range(angular_segments):
        next_segment = (segment + 1) % angular_segments

        for index in range(last):
            top_00 = point(upper_profile, index, segment)
            top_10 = point(upper_profile, index + 1, segment)
            top_11 = point(upper_profile, index + 1, next_segment)
            top_01 = point(upper_profile, index, next_segment)
            triangles.append(((0, 0, 0), top_00, top_10, top_11))
            triangles.append(((0, 0, 0), top_00, top_11, top_01))

            bot_00 = point(lower_profile, index, segment)
            bot_10 = point(lower_profile, index + 1, segment)
            bot_11 = point(lower_profile, index + 1, next_segment)
            bot_01 = point(lower_profile, index, next_segment)
            triangles.append(((0, 0, 0), bot_00, bot_11, bot_10))
            triangles.append(((0, 0, 0), bot_00, bot_01, bot_11))

        inner_bot_0 = point(lower_profile, 0, segment)
        inner_bot_1 = point(lower_profile, 0, next_segment)
        inner_top_0 = point(upper_profile, 0, segment)
        inner_top_1 = point(upper_profile, 0, next_segment)
        triangles.append(((0, 0, 0), inner_bot_0, inner_top_1, inner_bot_1))
        triangles.append(((0, 0, 0), inner_bot_0, inner_top_0, inner_top_1))

        outer_bot_0 = point(lower_profile, last, segment)
        outer_bot_1 = point(lower_profile, last, next_segment)
        outer_top_0 = point(upper_profile, last, segment)
        outer_top_1 = point(upper_profile, last, next_segment)
        triangles.append(((0, 0, 0), outer_bot_0, outer_bot_1, outer_top_1))
        triangles.append(((0, 0, 0), outer_bot_0, outer_top_1, outer_top_0))

    return triangles


def _write_revolved_band_stl(
    path: Path,
    lower_profile: list[tuple[float, float]],
    upper_profile: list[tuple[float, float]],
) -> list[Triangle]:
    triangles = _revolved_band_triangles(
        lower_profile,
        upper_profile,
        angular_segments=CRADLE_ANGULAR_SEGMENTS,
    )
    _write_binary_stl_triangles(path, triangles)
    return triangles


def _radius_at_z(profile: list[tuple[float, float]], z: float) -> float:
    """Interpolate an ordered radial/z profile by z."""
    ordered = sorted(profile, key=lambda point: point[1])
    if z <= ordered[0][1]:
        return ordered[0][0]
    if z >= ordered[-1][1]:
        return ordered[-1][0]
    for (r1, z1), (r2, z2) in zip(ordered, ordered[1:]):
        if z1 <= z <= z2:
            if abs(z2 - z1) < 1e-9:
                return max(r1, r2)
            t = (z - z1) / (z2 - z1)
            return r1 + (r2 - r1) * t
    raise ValueError(f"No profile radius at z={z:.3f}")


def _dr_dz_at_z(profile: list[tuple[float, float]], z: float) -> float:
    """Estimate local radial slope for an ordered radial/z profile."""
    ordered = sorted(profile, key=lambda point: point[1])
    low_z = ordered[0][1]
    high_z = ordered[-1][1]
    eps = min(0.25, max((high_z - low_z) / 800, 0.05))
    z1 = max(low_z, z - eps)
    z2 = min(high_z, z + eps)
    if z2 <= z1:
        raise ValueError(f"No profile slope at z={z:.3f}")
    return (_radius_at_z(profile, z2) - _radius_at_z(profile, z1)) / (z2 - z1)


def _cad_section_outer_radius_profile(
    shape,
    *,
    z_min: float,
    z_max: float,
    sample_count: int,
    curve_samples_per_edge: int = 1800,
) -> list[tuple[float, float]]:
    """Sample the positive-X exterior radius of an exact axial CAD section."""
    if sample_count < 8:
        raise ValueError("Outer section profile needs at least eight samples")
    if z_max <= z_min:
        raise ValueError("Outer section z range is invalid")

    section = BRepAlgoAPI_Section(
        shape.wrapped,
        gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)),
        False,
    )
    section.Approximation(True)
    section.Build()
    if not section.IsDone():
        raise ValueError("Unable to section horn body for rear fairing")

    points: list[tuple[float, float]] = []
    explorer = TopExp_Explorer(section.Shape(), TopAbs_EDGE)
    z_pad = 0.85
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        curve = BRepAdaptor_Curve(edge)
        first = curve.FirstParameter()
        last = curve.LastParameter()
        if not (math.isfinite(first) and math.isfinite(last)):
            explorer.Next()
            continue
        for index in range(curve_samples_per_edge + 1):
            u = first + (last - first) * index / curve_samples_per_edge
            point = curve.Value(u)
            x = point.X()
            z = point.Z()
            if x >= 0 and z_min - z_pad <= z <= z_max + z_pad:
                points.append((x, z))
        explorer.Next()
    if not points:
        raise ValueError("CAD section did not produce horn exterior samples")

    profile: list[tuple[float, float]] = []
    for index in range(sample_count):
        z = z_min + (z_max - z_min) * index / (sample_count - 1)
        window = 0.04
        nearby: list[float] = []
        while window <= 0.55:
            candidate = [x for x, point_z in points if abs(point_z - z) <= window]
            if candidate:
                nearby = candidate
                if max(candidate) - min(candidate) > 1.0 or window >= 0.25:
                    break
            window *= 1.7
        if not nearby:
            raise ValueError(f"No horn exterior section samples at z={z:.3f}")
        profile.append((max(nearby), z))
    return profile


def _hermite_radius(
    *,
    start_z: float,
    start_r: float,
    start_dr_dz: float,
    end_z: float,
    end_r: float,
    end_dr_dz: float,
    z: float,
) -> float:
    """Cubic Hermite radius interpolation by axial position."""
    span = end_z - start_z
    if span <= 0:
        raise ValueError("Hermite fairing span must be positive")
    t = (z - start_z) / span
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    return (
        h00 * start_r
        + h10 * span * start_dr_dz
        + h01 * end_r
        + h11 * span * end_dr_dz
    )


def _hermite_dr_dz(
    *,
    start_z: float,
    start_r: float,
    start_dr_dz: float,
    end_z: float,
    end_r: float,
    end_dr_dz: float,
    z: float,
) -> float:
    """Derivative of cubic Hermite radius interpolation."""
    span = end_z - start_z
    if span <= 0:
        raise ValueError("Hermite fairing span must be positive")
    t = (z - start_z) / span
    dh00 = 6 * t**2 - 6 * t
    dh10 = 3 * t**2 - 4 * t + 1
    dh01 = -6 * t**2 + 6 * t
    dh11 = 3 * t**2 - 2 * t
    dr_dt = (
        dh00 * start_r
        + dh10 * span * start_dr_dz
        + dh01 * end_r
        + dh11 * span * end_dr_dz
    )
    return dr_dt / span


def _revolved_rear_adapter_profile(
    *,
    rear_axis_z: float,
    spigot_r: float,
    flange_r: float,
    fairing_profile: list[tuple[float, float]],
) -> Solid:
    """Revolve the rear adapter with a true spline exterior fairing."""
    if len(fairing_profile) < 4:
        raise ValueError("Rear fairing needs enough points for a spline")
    start_r, start_z = fairing_profile[0]
    end_r, end_z = fairing_profile[-1]
    if abs(start_r - flange_r) > 1e-6:
        raise ValueError("Rear fairing must start at the flange radius")

    p0 = (0.0, rear_axis_z)
    p1 = (spigot_r, rear_axis_z)
    p2 = (spigot_r, start_z)
    p3 = fairing_profile[0]
    p4 = fairing_profile[-1]
    p5 = (0.0, end_z)

    wire_maker = BRepBuilderAPI_MakeWire()
    for start, end in ((p0, p1), (p1, p2), (p2, p3)):
        wire_maker.Add(_line_edge(start, end))
    wire_maker.Add(_spline_edge(fairing_profile))
    for start, end in ((p4, p5), (p5, p0)):
        wire_maker.Add(_line_edge(start, end))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make rear adapter profile wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make rear adapter profile face")
    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve rear adapter profile")
    solid = Solid.cast(revolved.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Rear adapter profile did not produce a valid solid")
    return solid


def _rear_fairing_join(
    profile: list[tuple[float, float]],
    *,
    flange_r: float,
    wall_t: float,
    max_dr_dz: float,
) -> tuple[float, float]:
    """Find where the printable rear fairing blends into the horn wall."""
    max_z = max(z for _r, z in profile)

    def margin(z: float) -> float:
        return flange_r - max_dr_dz * z - (_radius_at_z(profile, z) + wall_t)

    if margin(0.0) <= 0:
        raise ValueError("Rear fairing flange radius is smaller than throat body")
    high = 0.0
    for index in range(1, 400):
        z = max_z * index / 399
        if margin(z) <= 0:
            high = z
            break
    if high <= 0:
        raise ValueError("Rear fairing never intersects the horn exterior")

    low = 0.0
    for _ in range(48):
        mid = (low + high) / 2
        if margin(mid) > 0:
            low = mid
        else:
            high = mid
    join_z = (low + high) / 2
    join_r = _radius_at_z(profile, join_z) + wall_t
    return join_z, join_r


def build_jmlc_horn_with_printable_rear_fairing(
    *,
    throat_d: float,
    mouth_outer_d: float,
    wall_t: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
    lip_r: float,
    flange_d: float,
    flange_t: float,
    bolt_clearance_d: float,
    bolt_3_bcd: float,
    bolt_2_bcd: float,
    rear_spigot_l: float,
    rear_spigot_od: float,
    max_fairing_dr_dz: float,
    nut_counterbore_d: float,
    nut_counterbore_floor_t: float,
    nut_counterbore_top_z: float,
    nut_cutaway_taper_start_z: float,
    nut_cutaway_tip_overlap: float,
) -> tuple[object, dict[str, float]]:
    """Build the JMLC horn with a printable exterior rear adapter fairing."""
    mouth_outer_r = mouth_outer_d / 2
    mouth_inner_r = mouth_outer_r - wall_t
    profile, _cutoff_hz = jmlc_profile_points(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
    )
    inner = [(radius, z - flange_t - rear_spigot_l) for radius, z in profile]
    mouth_z = inner[-1][1]

    horn_body = _revolved_meridian_body(
        inner,
        wall_t=wall_t,
        throat_overlap=0.0,
        mouth_round_r=lip_r,
    )
    horn_body = _to_nurbs_solid(horn_body)

    flange_r = flange_d / 2
    spigot_r = rear_spigot_od / 2
    fairing_start_z = -flange_t
    waist_z = REAR_FAIRING_WAIST_Z
    blend_z = REAR_FAIRING_SMOOTH_BLEND_Z
    if not fairing_start_z < waist_z < blend_z:
        raise ValueError("Rear fairing start, waist, and blend must be ordered")

    horn_outer_profile = _cad_section_outer_radius_profile(
        horn_body,
        z_min=fairing_start_z,
        z_max=blend_z,
        sample_count=360,
    )
    waist_r = (
        _radius_at_z(horn_outer_profile, waist_z)
        + REAR_FAIRING_WAIST_CLEARANCE
    )
    blend_r = _radius_at_z(horn_outer_profile, blend_z)
    blend_dr_dz = _dr_dz_at_z(horn_outer_profile, blend_z)
    if abs(blend_dr_dz) > max_fairing_dr_dz:
        raise ValueError("Rear fairing blend tangent violates overhang limit")

    def fairing_radius_at(z: float) -> float:
        if z <= waist_z:
            return _hermite_radius(
                start_z=fairing_start_z,
                start_r=flange_r,
                start_dr_dz=REAR_FAIRING_START_DR_DZ,
                end_z=waist_z,
                end_r=waist_r,
                end_dr_dz=0.0,
                z=z,
            )
        return _hermite_radius(
            start_z=waist_z,
            start_r=waist_r,
            start_dr_dz=0.0,
            end_z=blend_z,
            end_r=blend_r,
            end_dr_dz=blend_dr_dz,
            z=z,
        )

    def fairing_dr_dz_at(z: float) -> float:
        if z <= waist_z:
            return _hermite_dr_dz(
                start_z=fairing_start_z,
                start_r=flange_r,
                start_dr_dz=REAR_FAIRING_START_DR_DZ,
                end_z=waist_z,
                end_r=waist_r,
                end_dr_dz=0.0,
                z=z,
            )
        return _hermite_dr_dz(
            start_z=waist_z,
            start_r=waist_r,
            start_dr_dz=0.0,
            end_z=blend_z,
            end_r=blend_r,
            end_dr_dz=blend_dr_dz,
            z=z,
        )

    fairing_samples = 112
    fairing_profile = []
    for index in range(fairing_samples):
        u = index / (fairing_samples - 1)
        if u <= 0.55:
            local_u = u / 0.55
            z = fairing_start_z + (waist_z - fairing_start_z) * local_u
        else:
            local_u = (u - 0.55) / 0.45
            z = waist_z + (blend_z - waist_z) * local_u
        fairing_profile.append((fairing_radius_at(z), z))
    fairing_profile[0] = (flange_r, fairing_start_z)
    fairing_profile[min(
        range(len(fairing_profile)),
        key=lambda item: abs(fairing_profile[item][1] - waist_z),
    )] = (waist_r, waist_z)
    fairing_profile[-1] = (blend_r, blend_z)
    fairing_slopes = [
        fairing_dr_dz_at(
            fairing_start_z + (blend_z - fairing_start_z) * sample / 480
        )
        for sample in range(481)
    ]
    max_abs_fairing_dr_dz = max(abs(slope) for slope in fairing_slopes)
    if max_abs_fairing_dr_dz > max_fairing_dr_dz:
        raise ValueError("Rear fairing curve violates overhang limit")
    for index in range(1, 240):
        z = fairing_start_z + (blend_z - fairing_start_z) * index / 240
        fairing_r = fairing_radius_at(z)
        horn_r = _radius_at_z(horn_outer_profile, z)
        if fairing_r < horn_r - 0.02:
            raise ValueError("Rear fairing curve cuts inside the horn wall")
    min_fairing_r, min_fairing_z = min(
        ((radius, z) for radius, z in fairing_profile),
        key=lambda point: point[0],
    )

    adapter = _primary_shape(
        _revolved_rear_adapter_profile(
            rear_axis_z=-flange_t - rear_spigot_l,
            spigot_r=spigot_r,
            flange_r=flange_r,
            fairing_profile=fairing_profile,
        )
        .clean()
        .fix()
    )
    adapter = _primary_shape(
        adapter
        - _revolved_acoustic_void(
            inner,
            radial_clearance=0.0,
            throat_extend=1.0,
        )
    )
    adapter = _primary_shape(adapter.clean().fix())

    horn = _primary_shape(horn_body.fuse(adapter))
    horn = _primary_shape(horn.clean().fix())
    if exit_angle_deg <= 90:
        from build123d import Torus

        lip = Torus(
            major_radius=mouth_outer_r - lip_r,
            minor_radius=lip_r,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.PRIVATE,
        )
        horn += Location((0, 0, mouth_z)) * lip
    horn = _primary_shape(horn.clean().fix())

    del bolt_3_bcd
    nut_counterbore_bottom_z = -flange_t + nut_counterbore_floor_t
    if nut_counterbore_bottom_z >= 0:
        raise ValueError("Nut counterbore floor must leave material in the flange")
    if nut_counterbore_d <= bolt_clearance_d:
        raise ValueError("Nut counterbore diameter must exceed bolt clearance")
    if nut_counterbore_top_z <= nut_counterbore_bottom_z + 6.0:
        raise ValueError("Nut counterbore top is too low for tool access")
    if nut_counterbore_top_z > waist_z:
        raise ValueError("Nut counterbore must not extend past the rear fairing waist")
    if not nut_counterbore_bottom_z < nut_cutaway_taper_start_z < nut_counterbore_top_z:
        raise ValueError("Nut cutaway taper start must sit inside the cutaway height")
    radius = bolt_2_bcd / 2
    counterbore_r = nut_counterbore_d / 2
    counterbore_floor_r = fairing_radius_at(nut_counterbore_bottom_z)
    counterbore_top_outer_r = fairing_radius_at(nut_counterbore_top_z)
    counterbore_tip_r = (
        radius - counterbore_top_outer_r + nut_cutaway_tip_overlap
    )
    if not 0 < counterbore_tip_r < counterbore_r:
        raise ValueError(
            "Nut cutaway tapered tip radius is invalid: "
            f"tip_r={counterbore_tip_r:.3f} mm, full_r={counterbore_r:.3f} mm"
        )
    side_open_breakout = radius + counterbore_r - counterbore_floor_r
    side_open_breakout_top = radius + counterbore_tip_r - counterbore_top_outer_r
    top_intrusion_depth = counterbore_top_outer_r - (radius - counterbore_tip_r)
    if side_open_breakout < 1.0:
        raise ValueError(
            "Side-open nut counterbore does not break through the rear "
            f"flange far enough: breakout={side_open_breakout:.3f} mm, "
            f"floor_r={counterbore_floor_r:.3f} mm, "
            f"counterbore_d={nut_counterbore_d:.3f} mm"
        )
    counterbore_inner_reach_r = radius - counterbore_r
    if counterbore_inner_reach_r <= spigot_r + 4.0:
        raise ValueError(
            "Side-open nut counterbore reaches too close to the rear spigot: "
            f"inner_reach={counterbore_inner_reach_r:.3f} mm, "
            f"minimum={spigot_r + 4.0:.3f} mm"
        )
    shaft_bottom_z = -flange_t - rear_spigot_l - 1.0
    shaft_top_z = nut_counterbore_top_z + 1.0
    shaft_depth = shaft_top_z - shaft_bottom_z
    shaft_center_z = (shaft_top_z + shaft_bottom_z) / 2
    for angle in (0.0, math.pi):
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        horn = _primary_shape(
            horn
            - _cylinder_z(
                diameter=bolt_clearance_d,
                depth=shaft_depth,
                center=(x, y, shaft_center_z),
            )
        )
        horn = _primary_shape(horn.clean().fix())
        nut_cutaway = _tapered_cutter_z(
            center_xy=(x, y),
            bottom_z=nut_counterbore_bottom_z,
            taper_start_z=nut_cutaway_taper_start_z,
            top_z=nut_counterbore_top_z,
            full_radius=counterbore_r,
            tip_radius=counterbore_tip_r,
        )
        horn = _primary_shape(
            horn - nut_cutaway
        )
        horn = _primary_shape(horn.clean().fix())

    return horn, {
        "rear_flange_d_mm": flange_d,
        "rear_fairing_start_z_mm": round(fairing_start_z, 3),
        "rear_fairing_start_r_mm": round(flange_r, 3),
        "rear_fairing_start_dr_dz": REAR_FAIRING_START_DR_DZ,
        "rear_fairing_waist_z_mm": round(waist_z, 3),
        "rear_fairing_waist_r_mm": round(waist_r, 3),
        "rear_fairing_waist_clearance_mm": REAR_FAIRING_WAIST_CLEARANCE,
        "rear_fairing_blend_end_z_mm": round(blend_z, 3),
        "rear_fairing_blend_end_r_mm": round(blend_r, 3),
        "rear_fairing_blend_end_dr_dz": round(blend_dr_dz, 4),
        "rear_fairing_blend_source": "measured CAD section of thickened horn body",
        "rear_fairing_minimum_z_mm": round(min_fairing_z, 3),
        "rear_fairing_minimum_r_mm": round(min_fairing_r, 3),
        "rear_fairing_max_abs_dr_dz": round(max_abs_fairing_dr_dz, 4),
        "rear_fairing_dr_dz_limit": max_fairing_dr_dz,
        "rear_fairing_max_angle_from_vertical_deg": round(
            math.degrees(math.atan(max_abs_fairing_dr_dz)),
            2,
        ),
        "active_mount_holes": "two opposing outer holes only",
        "outer_bolt_bcd_mm": bolt_2_bcd,
        "bolt_clearance_d_mm": bolt_clearance_d,
        "nut_counterbore_d_mm": nut_counterbore_d,
        "nut_counterbore_floor_t_mm": nut_counterbore_floor_t,
        "nut_counterbore_open_cut_height_mm": round(
            nut_counterbore_top_z - nut_counterbore_bottom_z, 3
        ),
        "nut_cutaway_taper_start_z_mm": nut_cutaway_taper_start_z,
        "nut_cutaway_full_radius_mm": counterbore_r,
        "nut_cutaway_tip_radius_mm": round(counterbore_tip_r, 3),
        "nut_cutaway_tip_overlap_mm": nut_cutaway_tip_overlap,
        "nut_cutaway_top_intrusion_depth_mm": round(top_intrusion_depth, 3),
        "nut_counterbore_floor_outer_r_mm": round(counterbore_floor_r, 3),
        "nut_counterbore_top_outer_r_mm": round(counterbore_top_outer_r, 3),
        "nut_counterbore_side_open_breakout_mm": round(side_open_breakout, 3),
        "nut_counterbore_side_open_breakout_top_mm": round(
            side_open_breakout_top, 3
        ),
        "nut_counterbore_inner_reach_r_mm": round(counterbore_inner_reach_r, 3),
        "nut_counterbore_bottom_z_mm": round(nut_counterbore_bottom_z, 3),
        "nut_counterbore_top_z_mm": round(nut_counterbore_top_z, 3),
        "nut_counterbore_shape": (
            "single side-open cutaway with a full lower circular nut relief "
            "and a smooth taper to a small rounded nose at the waist"
        ),
    }


def _flip_upright_horn_to_mouth_down(
    source: Path,
    output: Path,
    *,
    min_top_z: float,
) -> dict[str, list[float]]:
    """Flip an already-bed-oriented upright horn STL mouth-down."""
    triangles = _read_binary_stl_triangles(source)
    source_bbox = _bbox_from_mesh(triangles)
    max_z = source_bbox["max"][2]
    flipped: list[Triangle] = []
    for normal, p1, p2, p3 in triangles:
        del normal
        transformed = []
        for x, y, z in (p1, p2, p3):
            transformed.append((x, -y, max_z - z + min_top_z))
        # A 180 degree rotation preserves handedness, so keep vertex order.
        flipped.append(((0.0, 0.0, 0.0), transformed[0], transformed[1], transformed[2]))
    _write_binary_stl_triangles(output, flipped)
    return _bbox_from_mesh(flipped)


def _stl_lower_envelope_profile(
    path: Path,
    *,
    radial_min: float,
    radial_max: float,
    sample_count: int,
    search_window: float,
) -> list[tuple[float, float]]:
    """Sample the lowest mesh vertex around each radius."""
    if sample_count < 8:
        raise ValueError("Contact profile needs at least eight samples")
    if radial_max <= radial_min:
        raise ValueError("Contact profile radial bounds are invalid")

    radial_pad = max(search_window * 2.5, 0.25)
    vertices: list[tuple[float, float]] = []
    for _normal, p1, p2, p3 in _read_binary_stl_triangles(path):
        for x, y, z in (p1, p2, p3):
            radius = math.hypot(x, y)
            if radial_min - radial_pad <= radius <= radial_max + radial_pad:
                vertices.append((radius, z))
    if not vertices:
        raise ValueError("No STL vertices found in cradle contact band")

    profile: list[tuple[float, float]] = []
    for index in range(sample_count):
        t = index / (sample_count - 1)
        radius = radial_min + (radial_max - radial_min) * t
        window = search_window
        nearby: list[float] = []
        while not nearby and window <= 0.75:
            nearby = [z for point_r, z in vertices if abs(point_r - radius) <= window]
            window *= 1.6
        if not nearby:
            raise ValueError(f"No STL lower-envelope samples at radius {radius:.3f}")
        profile.append((radius, min(nearby)))
    return profile


def _cad_section_lower_envelope_profile(
    shape,
    *,
    radial_min: float,
    radial_max: float,
    sample_count: int,
    curve_samples_per_edge: int = 220,
) -> list[tuple[float, float]]:
    """Sample the lower radial envelope from an exact axial CAD section."""
    if sample_count < 8:
        raise ValueError("Contact profile needs at least eight samples")
    if radial_max <= radial_min:
        raise ValueError("Contact profile radial bounds are invalid")
    section = BRepAlgoAPI_Section(
        shape.wrapped,
        gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)),
        False,
    )
    section.Approximation(True)
    section.Build()
    if not section.IsDone():
        raise ValueError("Unable to section mouth-down horn for cradle profile")

    points: list[tuple[float, float]] = []
    explorer = TopExp_Explorer(section.Shape(), TopAbs_EDGE)
    radial_pad = 0.75
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        curve = BRepAdaptor_Curve(edge)
        first = curve.FirstParameter()
        last = curve.LastParameter()
        if not (math.isfinite(first) and math.isfinite(last)):
            explorer.Next()
            continue
        for index in range(curve_samples_per_edge + 1):
            u = first + (last - first) * index / curve_samples_per_edge
            point = curve.Value(u)
            radius = abs(point.X())
            if radial_min - radial_pad <= radius <= radial_max + radial_pad:
                points.append((radius, point.Z()))
        explorer.Next()
    if not points:
        raise ValueError("CAD section did not produce points in cradle band")

    profile: list[tuple[float, float]] = []
    for index in range(sample_count):
        t = index / (sample_count - 1)
        radius = radial_min + (radial_max - radial_min) * t
        window = 0.04
        nearby: list[float] = []
        while not nearby and window <= 0.45:
            nearby = [z for point_r, z in points if abs(point_r - radius) <= window]
            window *= 1.7
        if not nearby:
            raise ValueError(f"No CAD section lower-envelope sample at {radius:.3f}")
        profile.append((radius, min(nearby)))
    return profile


def _export_stl_only(shape, stem: str, *, stl_tolerance: float = STL_LINEAR_TOLERANCE) -> Path:
    path = OUT / f"{stem}.stl"
    print(f"exporting {path.name}...", flush=True)
    export_stl(
        shape,
        path,
        tolerance=stl_tolerance,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    return path


def _volume_cm3_from_mesh(path: Path) -> float:
    # Signed tetrahedron volume. Binary STL vertex order is outward for our
    # generated meshes, but use abs() so transformed meshes report positively.
    volume = 0.0
    for _normal, p1, p2, p3 in _read_binary_stl_triangles(path):
        volume += (
            p1[0] * (p2[1] * p3[2] - p2[2] * p3[1])
            - p1[1] * (p2[0] * p3[2] - p2[2] * p3[0])
            + p1[2] * (p2[0] * p3[1] - p2[1] * p3[0])
        )
    return round(abs(volume) / 6000.0, 2)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("building 220 mm JMLC horn with printable rear fairing...", flush=True)
    horn, rear_fairing_metadata = build_jmlc_horn_with_printable_rear_fairing(
        throat_d=p.horn_throat_d,
        mouth_outer_d=EXPERIMENTAL_MOUTH_OUTER_D,
        wall_t=p.horn_wall_t,
        exit_angle_deg=EXPERIMENTAL_EXIT_ANGLE_DEG,
        wavefront_t=p.horn_wavefront_t,
        throat_angle_deg=p.horn_throat_angle_deg,
        step=p.horn_profile_step,
        lip_r=p.horn_lip_r,
        flange_d=EXPERIMENTAL_REAR_FLANGE_D,
        flange_t=p.horn_flange_t,
        bolt_clearance_d=p.horn_bolt_clearance_d,
        bolt_3_bcd=p.horn_bolt_3_bcd,
        bolt_2_bcd=p.horn_bolt_2_bcd,
        rear_spigot_l=p.horn_bracket_t,
        rear_spigot_od=p.horn_spigot_od,
        max_fairing_dr_dz=REAR_FAIRING_MAX_DR_DZ,
        nut_counterbore_d=OUTER_BOLT_COUNTERBORE_D,
        nut_counterbore_floor_t=OUTER_BOLT_COUNTERBORE_FLOOR_T,
        nut_counterbore_top_z=OUTER_BOLT_COUNTERBORE_TOP_Z,
        nut_cutaway_taper_start_z=OUTER_BOLT_CUTAWAY_TAPER_START_Z,
        nut_cutaway_tip_overlap=OUTER_BOLT_CUTAWAY_TIP_OVERLAP,
    )

    mouth_down_stl = OUT / f"experimental_jmlc_horn_mouth_down_horn_{VERSION}_bed_oriented.stl"
    horn_bb = horn.bounding_box()
    mouth_down_horn = Location(
        (0, 0, CRADLE_MIN_TOP_Z + horn_bb.max.Z),
        (180, 0, 0),
    ) * horn
    print("exporting mouth-down horn STL...", flush=True)
    export_stl(
        mouth_down_horn,
        mouth_down_stl,
        tolerance=STL_LINEAR_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    mouth_down_bbox = _bbox(mouth_down_horn)

    print("sampling final horn STL lower envelope for slicer-visible cradle/interface...", flush=True)
    contact_profile = _stl_lower_envelope_profile(
        mouth_down_stl,
        radial_min=CRADLE_INNER_R,
        radial_max=CRADLE_OUTER_R,
        sample_count=CRADLE_PROFILE_SAMPLES,
        search_window=CRADLE_CONTACT_SEARCH_WINDOW,
    )
    contact_profile = [
        (radius, z - INTERFACE_HORN_CLEARANCE)
        for radius, z in contact_profile
    ]
    interface_lower_profile = [
        (radius, max(0.2, z - INTERFACE_H)) for radius, z in contact_profile
    ]
    cradle_top_profile = [
        (radius, max(0.0, z - INTERFACE_CRADLE_CLEARANCE))
        for radius, z in interface_lower_profile
    ]
    bed_profile = [(radius, 0.0) for radius, _z in contact_profile]

    print("writing shaped annular PLA cradle and support-material interface STLs...", flush=True)
    cradle_path = OUT / (
        f"experimental_jmlc_horn_mouth_down_female_cradle_pla_{VERSION}"
        "_bed_oriented.stl"
    )
    interface_path = OUT / (
        f"experimental_jmlc_horn_mouth_down_barrier_interface_{VERSION}"
        "_bed_oriented.stl"
    )
    cradle_mesh = _write_revolved_band_stl(
        cradle_path,
        bed_profile,
        cradle_top_profile,
    )
    interface_mesh = _write_revolved_band_stl(
        interface_path,
        interface_lower_profile,
        contact_profile,
    )
    output_paths = {
        "horn_mouth_down": {"bed_oriented_stl": str(mouth_down_stl.resolve())},
        "female_cradle_pla": {"bed_oriented_stl": str(cradle_path.resolve())},
        "barrier_interface_skin": {"bed_oriented_stl": str(interface_path.resolve())},
    }

    print("writing diagnostics...", flush=True)
    diagnostics = {
        "version": VERSION,
        "target_printed_outer_d_mm": TARGET_PRINTED_OUTER_D,
        "construction_mouth_outer_d_mm": EXPERIMENTAL_MOUTH_OUTER_D,
        "exit_angle_deg": EXPERIMENTAL_EXIT_ANGLE_DEG,
        "orientation": "mouth-down on shaped annular PLA cradle with support-material interface skin",
        "cradle_profile_source": (
            "high-resolution final horn STL lower envelope; this is used because "
            "Bambu collapses a perfectly coincident internal CAD-section barrier "
            "during multi-volume slicing"
        ),
        "cradle_radial_band_mm": [CRADLE_INNER_R, CRADLE_OUTER_R],
        "cradle_min_top_z_mm": CRADLE_MIN_TOP_Z,
        "interface_h_mm": INTERFACE_H,
        "interface_horn_clearance_mm": INTERFACE_HORN_CLEARANCE,
        "interface_cradle_clearance_mm": INTERFACE_CRADLE_CLEARANCE,
        "mouth_down_horn_bbox": mouth_down_bbox,
        "mouth_down_horn": horn_dimensions(mouth_down_horn),
        "mouth_down_horn_volume_cm3_mesh": _volume_cm3_from_mesh(mouth_down_stl),
        "rear_fairing": rear_fairing_metadata,
        "cradle": {
            "bounding_box_mm": _bbox_from_mesh(cradle_mesh)["size"],
            "bbox": _bbox_from_mesh(cradle_mesh),
            "face_count": len(cradle_mesh),
            "stl_volume_cm3": _volume_cm3_from_mesh(cradle_path),
        },
        "barrier_interface_skin": {
            "bounding_box_mm": _bbox_from_mesh(interface_mesh)["size"],
            "bbox": _bbox_from_mesh(interface_mesh),
            "face_count": len(interface_mesh),
            "stl_volume_cm3": _volume_cm3_from_mesh(interface_path),
        },
        "contact_profile_z_range_mm": [
            round(min(z for _r, z in contact_profile), 3),
            round(max(z for _r, z in contact_profile), 3),
        ],
        "paths": output_paths,
        "jmlc_profile": jmlc_profile_metadata(
            throat_d=p.horn_throat_d,
            mouth_outer_d=EXPERIMENTAL_MOUTH_OUTER_D,
            wall_t=p.horn_wall_t,
            exit_angle_deg=EXPERIMENTAL_EXIT_ANGLE_DEG,
            wavefront_t=p.horn_wavefront_t,
            throat_angle_deg=p.horn_throat_angle_deg,
            step=p.horn_profile_step,
        ),
    }
    diagnostics_path = OUT / f"diagnostics_{VERSION}_mouth_down.json"
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
