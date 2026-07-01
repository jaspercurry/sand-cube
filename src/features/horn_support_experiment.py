"""Experimental print-assist JMLC horn geometry.

This file intentionally started as a copy of ``src.features.horn`` so the
production horn builder can remain untouched while we explore printability
changes around the rolled-back mouth.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Compound,
    Cylinder,
    Face,
    Location,
    Mode,
    Part,
    Solid,
    Torus,
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_NurbsConvert,
)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Vec
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS


def _cylinder_z(
    *,
    diameter: float,
    depth: float,
    center: tuple[float, float, float],
) -> Part:
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    return Location(center) * cyl


def _primary_shape(shape):
    if hasattr(shape, "solids"):
        solids = shape.solids()
        if solids:
            return max(solids, key=lambda item: item.volume)
    if hasattr(shape, "bounding_box") and hasattr(shape, "volume"):
        return shape
    return max(shape, key=lambda item: item.volume)


def _target_area(
    *,
    s0: float,
    cutoff_hz: float,
    path_l: float,
    wavefront_t: float,
    sound_speed_mm_s: float,
) -> float:
    """JMLC spherical-wavefront expansion law."""
    m = 4 * math.pi * cutoff_hz / sound_speed_mm_s
    u = m * path_l / 2
    return s0 * (math.cosh(u) + wavefront_t * math.sinh(u)) ** 2


def _jmlc_points_for_cutoff(
    *,
    throat_d: float,
    mouth_inner_r: float,
    cutoff_hz: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
    sound_speed_mm_s: float = 344_000.0,
) -> tuple[list[tuple[float, float]], float]:
    """Derive Le Cleac'h wall points with the JMLC recurrence.

    Returned points are ``(radius, axial_z)`` samples in millimeters. The
    first point is the throat and the final point is interpolated to the
    requested mouth radius.
    """
    throat_r = throat_d / 2
    phi0 = math.radians(throat_angle_deg)
    if not 0 < phi0 < math.pi / 2:
        raise ValueError("throat_angle_deg must be between 0 and 90 degrees")

    r0 = throat_r / math.sin(phi0)
    s0 = 2 * math.pi * r0**2 * (1 - math.cos(phi0))
    l_samples = [0.0]
    phi = [phi0]
    xp = [r0 * (1 - math.cos(phi0))]
    yp = [throat_r]
    delta_alpha: list[float] = []

    max_steps = 8000
    while yp[-1] < mouth_inner_r and len(l_samples) < max_steps:
        i = len(l_samples)
        li = i * step
        target = _target_area(
            s0=s0,
            cutoff_hz=cutoff_hz,
            path_l=li,
            wavefront_t=wavefront_t,
            sound_speed_mm_s=sound_speed_mm_s,
        )

        projected = 2 * math.pi * (r0 + li) ** 2 * (1 - math.cos(phi0))
        for k in range(1, i):
            span = li - l_samples[k - 1]
            projected += (
                2
                * math.pi
                * span
                * (span * math.sin(phi[k - 1]) + yp[k - 1])
                * delta_alpha[k - 1]
            )

        remaining = target - projected
        local_r = step * math.sin(phi[i - 1]) + yp[i - 1]
        da = remaining / (2 * math.pi * local_r * step)
        next_phi = phi[i - 1] + da
        next_x = xp[i - 1] + step * math.cos(next_phi)
        next_y = yp[i - 1] + step * math.sin(next_phi)
        if not all(math.isfinite(v) for v in (da, next_phi, next_x, next_y)):
            raise ValueError("JMLC recurrence diverged")
        if next_y <= yp[-1]:
            raise ValueError("JMLC recurrence stopped expanding")

        delta_alpha.append(da)
        l_samples.append(li)
        phi.append(next_phi)
        xp.append(next_x)
        yp.append(next_y)

    if yp[-1] < mouth_inner_r:
        raise ValueError("JMLC recurrence did not reach the requested mouth")

    # Interpolate the last step to hit the mouth radius exactly.
    terminal_phi = phi[-1]
    if yp[-1] > mouth_inner_r:
        t = (mouth_inner_r - yp[-2]) / (yp[-1] - yp[-2])
        xp[-1] = xp[-2] + t * (xp[-1] - xp[-2])
        yp[-1] = mouth_inner_r
        terminal_phi = phi[-2] + t * (phi[-1] - phi[-2])

    z0 = xp[0]
    return [(r, z - z0) for r, z in zip(yp, xp)], math.degrees(terminal_phi)


def jmlc_cutoff_hz_for_exit_angle(
    *,
    throat_d: float,
    mouth_inner_r: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
) -> float:
    """Solve the cutoff that yields the requested wall angle at the mouth."""
    def angle_at(cutoff_hz: float) -> float | None:
        _points, terminal_angle = _jmlc_points_for_cutoff(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            cutoff_hz=cutoff_hz,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
            step=step,
        )
        return terminal_angle

    low = high = None
    low_angle = high_angle = None
    last_valid: tuple[float, float] | None = None
    for candidate in [250.0 + 5.0 * index for index in range(251)]:
        try:
            candidate_angle = angle_at(candidate)
        except ValueError:
            continue
        if candidate_angle is None:
            continue
        if candidate_angle < exit_angle_deg:
            last_valid = (candidate, candidate_angle)
            continue
        if last_valid is not None:
            low, low_angle = last_valid
            high, high_angle = candidate, candidate_angle
            break

    if (
        low is None
        or high is None
        or low_angle is None
        or high_angle is None
        or low_angle > exit_angle_deg
        or high_angle < exit_angle_deg
    ):
        raise ValueError(
            "Unable to bracket JMLC cutoff for the requested exit angle"
        )

    for _ in range(32):
        mid = (low + high) / 2
        try:
            mid_angle = angle_at(mid)
        except ValueError:
            high = mid
            continue
        if mid_angle is None:
            high = mid
            continue
        if mid_angle < exit_angle_deg:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def jmlc_profile_points(
    *,
    throat_d: float,
    mouth_inner_r: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
) -> tuple[list[tuple[float, float]], float]:
    """Return mathematically derived JMLC points and the solved cutoff."""
    cutoff_hz = jmlc_cutoff_hz_for_exit_angle(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
    )
    points, _terminal_angle = _jmlc_points_for_cutoff(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        cutoff_hz=cutoff_hz,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
    )
    return points, cutoff_hz


def jmlc_profile_metadata(
    *,
    throat_d: float,
    mouth_outer_d: float,
    wall_t: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
) -> dict[str, object]:
    """Small diagnostics payload for the generated JMLC profile."""
    mouth_inner_r = mouth_outer_d / 2 - wall_t
    points, cutoff_hz = jmlc_profile_points(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
    )
    return {
        "profile": "Le Cleac'h / JMLC recurrence",
        "solved_cutoff_hz": round(cutoff_hz, 1),
        "mouth_inner_d_mm": round(2 * mouth_inner_r, 3),
        "axial_length_mm": round(points[-1][1], 3),
        "exit_angle_deg": round(exit_angle_deg, 3),
        "sample_count": len(points),
    }


def _spline_edge(points: list[tuple[float, float]]):
    point_array = TColgp_Array1OfPnt(1, len(points))
    for index, (radius, z) in enumerate(points, 1):
        point_array.SetValue(index, gp_Pnt(radius, 0, z))
    curve = GeomAPI_PointsToBSpline(point_array).Curve()
    return BRepBuilderAPI_MakeEdge(curve).Edge()


def _line_edge(
    start: tuple[float, float],
    end: tuple[float, float],
):
    return BRepBuilderAPI_MakeEdge(
        gp_Pnt(start[0], 0, start[1]),
        gp_Pnt(end[0], 0, end[1]),
    ).Edge()


def _to_nurbs_solid(part: Part | Solid) -> Solid:
    """Convert one solid to NURBS, extracting it from OCCT's compound result."""
    converter = BRepBuilderAPI_NurbsConvert(part.wrapped, True)
    if not converter.IsDone():
        raise ValueError("Unable to convert horn wall to NURBS geometry")

    explorer = TopExp_Explorer(converter.Shape(), TopAbs_SOLID)
    solids: list[Solid] = []
    while explorer.More():
        solid = Solid.cast(TopoDS.Solid_s(explorer.Current()))
        if solid is not None:
            solids.append(solid)
        explorer.Next()

    if not solids:
        raise ValueError("NURBS conversion did not produce a solid")

    solid = max(solids, key=lambda item: item.volume)
    if not solid.is_valid:
        raise ValueError("NURBS-converted horn wall is not a valid solid")
    return solid


def _revolved_acoustic_void(
    profile: list[tuple[float, float]],
    *,
    radial_clearance: float = 0.0,
    throat_extend: float = 1.0,
) -> Solid:
    """Create the air volume that must be removed from the horn solid."""
    void_profile = [
        (radius + radial_clearance, z)
        for radius, z in profile
    ]
    throat_z = void_profile[0][1] - throat_extend
    mouth_z = void_profile[-1][1]

    wire_maker = BRepBuilderAPI_MakeWire()
    wire_maker.Add(_line_edge((0, throat_z), (void_profile[0][0], throat_z)))
    wire_maker.Add(_line_edge((void_profile[0][0], throat_z), void_profile[0]))
    wire_maker.Add(_spline_edge(void_profile))
    wire_maker.Add(_line_edge(void_profile[-1], (0, mouth_z)))
    wire_maker.Add(_line_edge((0, mouth_z), (0, throat_z)))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make horn acoustic void wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make horn acoustic void face")

    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve horn acoustic void")
    void = Solid.cast(revolved.Shape())
    if void is None or not void.is_valid:
        raise ValueError("Horn acoustic void is not a valid solid")
    return void


def _revolved_meridian_body(
    profile: list[tuple[float, float]],
    *,
    wall_t: float,
    throat_overlap: float = 0.0,
    mouth_round_r: float = 0.0,
) -> Solid:
    """Create the horn wall by thickening the revolved acoustic surface.

    This intentionally uses the earlier Onshape-friendly topology: revolve the
    exact sound-facing JMLC curve, thicken that face, then convert the resulting
    wall to NURBS before merging it with the native adapter.
    """
    surface_profile = profile
    if throat_overlap > 0:
        surface_profile = [
            (profile[0][0], profile[0][1] - throat_overlap),
            *profile,
        ]

    acoustic_revolve = BRepPrimAPI_MakeRevol(
        _spline_edge(surface_profile),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not acoustic_revolve.IsDone():
        raise ValueError("Unable to revolve horn acoustic surface")
    acoustic_face = Face.cast(acoustic_revolve.Shape())
    if acoustic_face is None or not acoustic_face.is_valid:
        raise ValueError("Revolved horn acoustic surface is not valid")

    body = Solid.thicken(acoustic_face, -wall_t)
    if body is None or not body.is_valid:
        raise ValueError("Thickened horn body is not a valid solid")

    if mouth_round_r > 0:
        fillet_r = min(mouth_round_r, wall_t * 0.375)
        mouth_z = profile[-1][1]
        mouth_radius = profile[-1][0]
        mouth_edges = [
            edge
            for edge in body.edges()
            if edge.length > math.tau * mouth_radius * 0.75
            and edge.bounding_box().max.Z > mouth_z - 0.25
        ]
        for candidate_r in (fillet_r, fillet_r * 0.75, fillet_r * 0.5):
            if not mouth_edges:
                break
            try:
                body = body.fillet(candidate_r, mouth_edges)
                break
            except ValueError:
                continue
        body = body.clean().fix()
        if body is None or not body.is_valid:
            raise ValueError("Filleted horn mouth is not a valid solid")

    return body


def _smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def _revolved_closed_profile(points: list[tuple[float, float]]) -> Solid:
    """Revolve a closed meridian polygon/spline into an axisymmetric solid."""
    wire_maker = BRepBuilderAPI_MakeWire()
    for start, end in zip(points, [*points[1:], points[0]]):
        wire_maker.Add(_line_edge(start, end))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make revolved closed profile wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make revolved closed profile face")
    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve closed profile")
    solid = Solid.cast(revolved.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Revolved closed profile is not a valid solid")
    return solid


def _revolved_between_profiles(
    inner_profile: list[tuple[float, float]],
    outer_profile: list[tuple[float, float]],
) -> Solid:
    """Revolve the filled area between two ordered radial/z profiles."""
    if len(inner_profile) < 2 or len(outer_profile) < 2:
        raise ValueError("Profiles need at least two points")
    wire_maker = BRepBuilderAPI_MakeWire()
    wire_maker.Add(_spline_edge(inner_profile))
    wire_maker.Add(_line_edge(inner_profile[-1], outer_profile[-1]))
    wire_maker.Add(_spline_edge(list(reversed(outer_profile))))
    wire_maker.Add(_line_edge(outer_profile[0], inner_profile[0]))
    if not wire_maker.IsDone():
        raise ValueError("Unable to make between-profiles wire")

    face_maker = BRepBuilderAPI_MakeFace(wire_maker.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make between-profiles face")
    revolved = BRepPrimAPI_MakeRevol(
        face_maker.Face(),
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.tau,
        True,
    )
    if not revolved.IsDone():
        raise ValueError("Unable to revolve between-profiles face")
    solid = Solid.cast(revolved.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Revolved between-profiles body is not valid")
    return solid


def _annular_cylinder(
    *,
    inner_radius: float,
    outer_radius: float,
    height: float,
    center_z: float,
) -> Part:
    if inner_radius <= 0 or outer_radius <= inner_radius:
        raise ValueError("Annular cylinder radii are invalid")
    outer = Cylinder(
        radius=outer_radius,
        height=height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    inner = Cylinder(
        radius=inner_radius,
        height=height + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    return Location((0, 0, center_z)) * (outer - inner)


def _outer_rollback_fairing(
    profile: list[tuple[float, float]],
    *,
    wall_t: float,
    fairing_start_before_apex_mm: float = 6.0,
    fairing_max_extra_t: float = 1.6,
    inner_clearance: float | None = None,
    max_outer_clearance: float = 0.35,
) -> Solid:
    """Add a subtle exterior thickening through the rolled-back mouth region.

    The inner boundary of this body intentionally overlaps the existing horn
    wall, while the exposed boundary grows gradually and stays inside the
    nominal mouth outer radius. It is a permanent exterior fairing only; the
    acoustic surface is not touched.
    """
    inner_boundary, outer_boundary = _rollback_fairing_boundary_profiles(
        profile,
        wall_t=wall_t,
        fairing_start_before_apex_mm=fairing_start_before_apex_mm,
        fairing_max_extra_t=fairing_max_extra_t,
        inner_clearance=inner_clearance,
        max_outer_clearance=max_outer_clearance,
    )
    return _revolved_between_profiles(inner_boundary, outer_boundary)


def _rollback_fairing_boundary_profiles(
    profile: list[tuple[float, float]],
    *,
    wall_t: float,
    fairing_start_before_apex_mm: float,
    fairing_max_extra_t: float,
    inner_clearance: float | None,
    max_outer_clearance: float,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Return the meridian boundaries used by the exterior rollback fairing."""
    apex_index = max(range(len(profile)), key=lambda index: profile[index][1])
    apex_r, _apex_z = profile[apex_index]
    start_r = max(profile[0][0], apex_r - fairing_start_before_apex_mm)
    fairing_profile = [point for point in profile if point[0] >= start_r]
    if len(fairing_profile) < 4:
        raise ValueError("Not enough rollback profile points for fairing")

    mouth_inner_r = profile[-1][0]
    max_outer_r = mouth_inner_r + wall_t - max_outer_clearance
    inner_offset = wall_t * 0.58 if inner_clearance is None else inner_clearance
    span = fairing_profile[-1][0] - fairing_profile[0][0]
    inner_boundary: list[tuple[float, float]] = []
    outer_boundary: list[tuple[float, float]] = []
    for radius, z in fairing_profile:
        t = 0.0 if span <= 0 else (radius - fairing_profile[0][0]) / span
        growth = fairing_max_extra_t * _smoothstep(t)
        inner_boundary.append((radius + inner_offset, z))
        outer_boundary.append((min(radius + wall_t + growth, max_outer_r), z))
    return inner_boundary, outer_boundary


def _lower_envelope_profile(
    polygon: list[tuple[float, float]],
    *,
    radial_min: float,
    radial_max: float,
    sample_count: int,
) -> list[tuple[float, float]]:
    """Sample the lower z-envelope of a closed meridian polygon."""
    if sample_count < 8:
        raise ValueError("Lower envelope needs at least eight samples")
    if radial_max <= radial_min:
        raise ValueError("Lower envelope radial bounds are invalid")

    profile: list[tuple[float, float]] = []
    edges = list(zip(polygon, [*polygon[1:], polygon[0]]))
    for index in range(sample_count):
        t = index / (sample_count - 1)
        radius = radial_min + (radial_max - radial_min) * t
        intersections: list[float] = []
        for (r1, z1), (r2, z2) in edges:
            if abs(r2 - r1) < 1e-9:
                if abs(radius - r1) < 1e-6:
                    intersections.extend([z1, z2])
                continue
            if (r1 <= radius <= r2) or (r2 <= radius <= r1):
                edge_t = (radius - r1) / (r2 - r1)
                intersections.append(z1 + (z2 - z1) * edge_t)
        if not intersections:
            raise ValueError(
                f"No rollback fairing envelope intersection at radius {radius:.3f}"
            )
        profile.append((radius, min(intersections)))
    return profile


def rollback_fairing_lower_envelope(
    profile: list[tuple[float, float]],
    *,
    wall_t: float,
    radial_min: float,
    radial_max: float,
    fairing_start_before_apex_mm: float = 10.0,
    fairing_max_extra_t: float = 1.2,
    inner_clearance: float | None = None,
    max_outer_clearance: float = 1.35,
    sample_count: int = 96,
) -> list[tuple[float, float]]:
    """Approximate the support-facing underside of the rolled-back fairing."""
    inner_boundary, outer_boundary = _rollback_fairing_boundary_profiles(
        profile,
        wall_t=wall_t,
        fairing_start_before_apex_mm=fairing_start_before_apex_mm,
        fairing_max_extra_t=fairing_max_extra_t,
        inner_clearance=inner_clearance,
        max_outer_clearance=max_outer_clearance,
    )
    return _lower_envelope_profile(
        [*inner_boundary, *reversed(outer_boundary)],
        radial_min=radial_min,
        radial_max=radial_max,
        sample_count=sample_count,
    )


def _inner_lip_print_landing(
    *,
    mouth_inner_r: float,
    mouth_z: float,
    lip_r: float,
    radial_inset: float = 0.48,
    radial_width: float = 1.24,
    vertical_drop: float = 1.42,
) -> Solid:
    """Create a hidden breakaway landing under the inner side of the lip."""
    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    bottom_z = mouth_z - vertical_drop
    top_z = mouth_z - 0.24
    chamfer = min(0.36, radial_width * 0.28)
    return _revolved_closed_profile(
        [
            (inner_r, top_z),
            (inner_r + chamfer, bottom_z),
            (outer_r, bottom_z),
            (outer_r + chamfer * 0.45, top_z - 0.52),
            (inner_r + radial_width * 0.42, top_z + 0.02),
        ]
    )


def build_inner_lip_petg_interface_cap(
    *,
    mouth_outer_d: float,
    wall_t: float,
    lip_r: float,
    mouth_z: float,
    radial_inset: float = 0.86,
    radial_width: float = 0.72,
    landing_vertical_drop: float = 1.42,
    interface_h: float = 0.20,
    interface_clearance: float = 0.0,
) -> Solid:
    """Build the breakaway interface stripe tucked below the hidden landing."""
    del lip_r
    mouth_inner_r = mouth_outer_d / 2 - wall_t
    landing_bottom_z = mouth_z - landing_vertical_drop
    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    return _annular_cylinder(
        inner_radius=inner_r,
        outer_radius=outer_r,
        height=interface_h,
        center_z=landing_bottom_z - interface_clearance - interface_h / 2,
    )


def build_contoured_lip_cradle(
    *,
    profile: list[tuple[float, float]],
    wall_t: float,
    radial_inset: float,
    radial_width: float,
    contact_profile: list[tuple[float, float]] | None = None,
    interface_h: float = 0.40,
    cradle_base_overlap_h: float = 0.20,
    fairing_start_before_apex_mm: float = 10.0,
    fairing_max_extra_t: float = 1.2,
    max_outer_clearance: float = 1.35,
    sample_count: int = 96,
    radial_band_count: int = 48,
    use_smooth_revolve: bool = False,
) -> tuple[Compound, Compound, dict[str, float]]:
    """Build a PLA saddle plus conformal support-material skin under the lip."""
    if interface_h <= 0 or cradle_base_overlap_h < 0:
        raise ValueError("Contoured cradle heights are invalid")
    mouth_inner_r = profile[-1][0]
    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    if contact_profile is None:
        contact_profile = rollback_fairing_lower_envelope(
            profile,
            wall_t=wall_t,
            radial_min=inner_r,
            radial_max=outer_r,
            fairing_start_before_apex_mm=fairing_start_before_apex_mm,
            fairing_max_extra_t=fairing_max_extra_t,
            max_outer_clearance=max_outer_clearance,
            sample_count=sample_count,
        )
    else:
        if len(contact_profile) < 8:
            raise ValueError("Contoured contact profile needs at least eight points")
        if contact_profile[0][0] > contact_profile[-1][0]:
            contact_profile = list(reversed(contact_profile))
    if radial_band_count < 4:
        raise ValueError("Contoured cradle needs at least four radial bands")

    def z_at_radius(radius: float) -> float:
        if radius <= contact_profile[0][0]:
            return contact_profile[0][1]
        if radius >= contact_profile[-1][0]:
            return contact_profile[-1][1]
        for (r1, z1), (r2, z2) in zip(contact_profile, contact_profile[1:]):
            if r1 <= radius <= r2:
                t = 0.0 if abs(r2 - r1) < 1e-9 else (radius - r1) / (r2 - r1)
                return z1 + (z2 - z1) * t
        raise ValueError(f"No contact-profile z at radius {radius:.3f}")

    band_edges = [
        inner_r + (outer_r - inner_r) * index / radial_band_count
        for index in range(radial_band_count + 1)
    ]
    contact_band_z = [
        min(z_at_radius(r1), z_at_radius(r2))
        for r1, r2 in zip(band_edges, band_edges[1:])
    ]
    interface_lower_z = [z - interface_h for z in contact_band_z]
    base_z = min(interface_lower_z) - cradle_base_overlap_h
    if use_smooth_revolve:
        smooth_contact_profile = [
            (
                inner_r + (outer_r - inner_r) * index / (radial_band_count - 1),
                z_at_radius(
                    inner_r
                    + (outer_r - inner_r) * index / (radial_band_count - 1)
                ),
            )
            for index in range(radial_band_count)
        ]
        interface_lower_profile = [
            (radius, z - interface_h) for radius, z in smooth_contact_profile
        ]
        base_profile = [(radius, base_z) for radius, _z in smooth_contact_profile]
        pla_cradle = Compound(
            children=[
                _revolved_between_profiles(
                    base_profile,
                    interface_lower_profile,
                )
            ]
        )
        interface_skin = Compound(
            children=[
                _revolved_between_profiles(
                    interface_lower_profile,
                    smooth_contact_profile,
                )
            ]
        )
        metadata = {
            "inner_radius_mm": inner_r,
            "outer_radius_mm": outer_r,
            "contact_z_min_mm": min(z for _radius, z in contact_profile),
            "contact_z_max_mm": max(z for _radius, z in contact_profile),
            "base_z_mm": base_z,
            "interface_h_mm": interface_h,
            "radial_band_count": radial_band_count,
            "smooth_revolved": 1.0,
        }
        return pla_cradle, interface_skin, metadata

    pla_bands: list[Solid] = []
    interface_bands: list[Solid] = []
    for r1, r2, contact_z, lower_z in zip(
        band_edges[:-1],
        band_edges[1:],
        contact_band_z,
        interface_lower_z,
        strict=True,
    ):
        pla_h = lower_z - base_z
        if pla_h <= 0:
            continue
        pla_bands.append(
            _annular_cylinder(
                inner_radius=r1,
                outer_radius=r2,
                height=pla_h,
                center_z=base_z + pla_h / 2,
            )
        )
        interface_bands.append(
            _annular_cylinder(
                inner_radius=r1,
                outer_radius=r2,
                height=interface_h,
                center_z=contact_z - interface_h / 2,
            )
        )
    # Fuse the staircase bands. Left as 48 separate hairline rings, the
    # slicer walks every ring with two overlapping minimum-width wall loops
    # and deposits ~5x the modeled volume of support filament.
    pla_cradle = _fused_compound(pla_bands, label="Contoured PLA cradle")
    interface_skin = _fused_compound(
        interface_bands, label="Contoured interface skin"
    )
    metadata = {
        "inner_radius_mm": inner_r,
        "outer_radius_mm": outer_r,
        "contact_z_min_mm": min(z for _radius, z in contact_profile),
        "contact_z_max_mm": max(z for _radius, z in contact_profile),
        "base_z_mm": base_z,
        "interface_h_mm": interface_h,
        "radial_band_count": radial_band_count,
    }
    return pla_cradle, interface_skin, metadata


def _fused_compound(parts: list[Part | Solid], *, label: str) -> Compound:
    """Union touching solids so slicers see one body instead of many slivers."""
    solids: list[Solid] = [solid for part in parts for solid in part.solids()]
    if not solids:
        raise ValueError(f"{label} produced no solids to fuse")
    shape = solids[0] if len(solids) == 1 else solids[0].fuse(*solids[1:])
    shape = shape.clean()
    fused = Compound(children=shape.solids())
    if fused is None or not fused.is_valid:
        raise ValueError(f"{label} did not fuse into a valid body")
    return fused


def _extruded_planar_polygon(
    points: list[tuple[float, float]],
    *,
    bottom_z: float,
    height: float,
) -> Solid:
    """Extrude one closed XY polygon into a vertical support solid."""
    if len(points) < 4:
        raise ValueError("A planar polygon needs at least four points")
    if height <= 0:
        raise ValueError("Extrusion height must be positive")

    polygon = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        polygon.Add(gp_Pnt(x, y, bottom_z))
    polygon.Close()
    if not polygon.IsDone():
        raise ValueError("Unable to make support polygon")

    face_maker = BRepBuilderAPI_MakeFace(polygon.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make support polygon face")

    prism = BRepPrimAPI_MakePrism(face_maker.Face(), gp_Vec(0, 0, height), True)
    if not prism.IsDone():
        raise ValueError("Unable to extrude support polygon")
    solid = Solid.cast(prism.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Extruded support polygon is not a valid solid")
    return solid


def _extruded_planar_ring(
    outer_points: list[tuple[float, float]],
    inner_points: list[tuple[float, float]],
    *,
    bottom_z: float,
    height: float,
) -> Solid:
    """Extrude a closed XY ring face into a vertical support solid."""
    if len(outer_points) < 4 or len(inner_points) < 4:
        raise ValueError("A planar ring needs at least four points per loop")
    if len(outer_points) != len(inner_points):
        raise ValueError("Outer and inner support loops must have equal samples")
    if height <= 0:
        raise ValueError("Extrusion height must be positive")

    def _wire(points: list[tuple[float, float]]):
        polygon = BRepBuilderAPI_MakePolygon()
        for x, y in points:
            polygon.Add(gp_Pnt(x, y, bottom_z))
        polygon.Close()
        if not polygon.IsDone():
            raise ValueError("Unable to make support ring loop")
        return polygon.Wire()

    face_maker = BRepBuilderAPI_MakeFace(_wire(outer_points))
    if not face_maker.IsDone():
        raise ValueError("Unable to make support ring outer face")
    face_maker.Add(_wire(list(reversed(inner_points))))
    if not face_maker.IsDone():
        raise ValueError("Unable to add support ring inner loop")

    prism = BRepPrimAPI_MakePrism(face_maker.Face(), gp_Vec(0, 0, height), True)
    if not prism.IsDone():
        raise ValueError("Unable to extrude support ring")
    solid = Solid.cast(prism.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Extruded support ring is not a valid solid")
    return solid


def _extruded_radial_profile(
    points: list[tuple[float, float]],
    *,
    theta: float,
    tangential_width: float,
) -> Solid:
    """Extrude one radial/Z profile into a thin tangential buttress rib."""
    if len(points) < 4:
        raise ValueError("A radial profile needs at least four points")
    if tangential_width <= 0:
        raise ValueError("Tangential rib width must be positive")

    radial_x = math.cos(theta)
    radial_y = math.sin(theta)
    tangent_x = -math.sin(theta)
    tangent_y = math.cos(theta)
    half_w = tangential_width / 2

    polygon = BRepBuilderAPI_MakePolygon()
    for radius, z in points:
        polygon.Add(
            gp_Pnt(
                radius * radial_x - tangent_x * half_w,
                radius * radial_y - tangent_y * half_w,
                z,
            )
        )
    polygon.Close()
    if not polygon.IsDone():
        raise ValueError("Unable to make radial rib polygon")

    face_maker = BRepBuilderAPI_MakeFace(polygon.Wire())
    if not face_maker.IsDone():
        raise ValueError("Unable to make radial rib face")

    prism = BRepPrimAPI_MakePrism(
        face_maker.Face(),
        gp_Vec(tangent_x * tangential_width, tangent_y * tangential_width, 0),
        True,
    )
    if not prism.IsDone():
        raise ValueError("Unable to extrude radial rib")
    solid = Solid.cast(prism.Shape())
    if solid is None or not solid.is_valid:
        raise ValueError("Extruded radial rib is not a valid solid")
    return solid


def build_lightweight_flared_lip_cradle(
    *,
    profile: list[tuple[float, float]],
    wall_t: float,
    radial_inset: float,
    radial_width: float,
    rib_base_inner_r: float,
    rib_base_outer_r: float,
    contact_profile: list[tuple[float, float]] | None = None,
    interface_h: float = 0.40,
    cap_h: float = 1.40,
    rib_count: int = 56,
    rib_angles: list[float] | None = None,
    rib_specs: list[tuple[float, float, float]] | None = None,
    rib_tangential_width: float = 1.00,
    rib_rise_h: float = 42.0,
    rib_top_overlap_h: float = 0.25,
    fairing_start_before_apex_mm: float = 10.0,
    fairing_max_extra_t: float = 1.2,
    max_outer_clearance: float = 1.35,
    sample_count: int = 96,
    radial_sample_count: int = 32,
) -> tuple[Compound, Compound, dict[str, float]]:
    """Build a continuous release saddle with open radial buttress ribs below."""
    if interface_h <= 0 or cap_h <= 0:
        raise ValueError("Lightweight cradle heights are invalid")
    if rib_specs is not None:
        rib_specs = list(rib_specs)
        if len(rib_specs) < 8:
            raise ValueError("Lightweight cradle needs at least eight rib specs")
        for _theta, base_inner_r, base_outer_r in rib_specs:
            if base_outer_r <= base_inner_r:
                raise ValueError("Rib spec base radii are invalid")
    elif rib_angles is not None:
        rib_angles = list(rib_angles)
        if len(rib_angles) < 8:
            raise ValueError("Lightweight cradle needs at least eight rib angles")
    elif rib_count < 12:
        raise ValueError("Lightweight cradle needs at least twelve ribs")
    if rib_base_outer_r <= rib_base_inner_r:
        raise ValueError("Rib base radii are invalid")
    if rib_tangential_width <= 0 or rib_rise_h <= 0:
        raise ValueError("Rib dimensions are invalid")
    if radial_sample_count < 8:
        raise ValueError("Lightweight cradle needs at least eight radial samples")

    mouth_inner_r = profile[-1][0]
    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    if contact_profile is None:
        contact_profile = rollback_fairing_lower_envelope(
            profile,
            wall_t=wall_t,
            radial_min=inner_r,
            radial_max=outer_r,
            fairing_start_before_apex_mm=fairing_start_before_apex_mm,
            fairing_max_extra_t=fairing_max_extra_t,
            max_outer_clearance=max_outer_clearance,
            sample_count=sample_count,
        )
    else:
        if len(contact_profile) < 8:
            raise ValueError("Lightweight contact profile needs at least eight points")
        if contact_profile[0][0] > contact_profile[-1][0]:
            contact_profile = list(reversed(contact_profile))

    def z_at_radius(radius: float) -> float:
        if radius <= contact_profile[0][0]:
            return contact_profile[0][1]
        if radius >= contact_profile[-1][0]:
            return contact_profile[-1][1]
        for (r1, z1), (r2, z2) in zip(contact_profile, contact_profile[1:]):
            if r1 <= radius <= r2:
                t = 0.0 if abs(r2 - r1) < 1e-9 else (radius - r1) / (r2 - r1)
                return z1 + (z2 - z1) * t
        raise ValueError(f"No contact-profile z at radius {radius:.3f}")

    contact = [
        (
            inner_r + (outer_r - inner_r) * index / (radial_sample_count - 1),
            z_at_radius(
                inner_r + (outer_r - inner_r) * index / (radial_sample_count - 1)
            ),
        )
        for index in range(radial_sample_count)
    ]
    interface_lower = [(radius, z - interface_h) for radius, z in contact]
    cap_lower = [(radius, z - interface_h - cap_h) for radius, z in contact]
    cap = _revolved_between_profiles(cap_lower, interface_lower)
    interface_skin = _revolved_between_profiles(interface_lower, contact)

    rib_bottom_z = min(z for _radius, z in cap_lower) - rib_rise_h
    top_profile = [
        (radius, z + min(rib_top_overlap_h, cap_h * 0.45))
        for radius, z in cap_lower
    ]
    if rib_specs is not None:
        rib_entries = rib_specs
    else:
        rib_thetas = (
            rib_angles
            if rib_angles is not None
            else [math.tau * index / rib_count for index in range(rib_count)]
        )
        rib_entries = [
            (theta, rib_base_inner_r, rib_base_outer_r) for theta in rib_thetas
        ]
    ribs = [
        _extruded_radial_profile(
            [
                (base_inner_r, rib_bottom_z),
                (base_outer_r, rib_bottom_z),
                *reversed(top_profile),
            ],
            theta=theta,
            tangential_width=rib_tangential_width,
        )
        for theta, base_inner_r, base_outer_r in rib_entries
    ]
    pla_cradle = Compound(children=[*cap.solids(), *ribs])
    interface = Compound(children=interface_skin.solids())
    rib_base_inner_min = min(base_inner_r for _theta, base_inner_r, _base_outer_r in rib_entries)
    rib_base_inner_max = max(base_inner_r for _theta, base_inner_r, _base_outer_r in rib_entries)
    rib_base_outer_min = min(base_outer_r for _theta, _base_inner_r, base_outer_r in rib_entries)
    rib_base_outer_max = max(base_outer_r for _theta, _base_inner_r, base_outer_r in rib_entries)
    metadata = {
        "inner_radius_mm": inner_r,
        "outer_radius_mm": outer_r,
        "contact_z_min_mm": min(z for _radius, z in contact_profile),
        "contact_z_max_mm": max(z for _radius, z in contact_profile),
        "interface_h_mm": interface_h,
        "cap_h_mm": cap_h,
        "rib_count": len(rib_entries),
        "rib_angles_are_explicit": 1.0 if rib_angles is not None else 0.0,
        "rib_specs_are_explicit": 1.0 if rib_specs is not None else 0.0,
        "rib_tangential_width_mm": rib_tangential_width,
        "rib_base_inner_radius_mm": rib_base_inner_r,
        "rib_base_outer_radius_mm": rib_base_outer_r,
        "rib_base_inner_radius_min_mm": rib_base_inner_min,
        "rib_base_inner_radius_max_mm": rib_base_inner_max,
        "rib_base_outer_radius_min_mm": rib_base_outer_min,
        "rib_base_outer_radius_max_mm": rib_base_outer_max,
        "rib_bottom_z_mm": rib_bottom_z,
        "rib_rise_h_mm": rib_rise_h,
        "radial_sample_count": radial_sample_count,
        "lightweight_ribbed": 1.0,
    }
    return pla_cradle, interface, metadata


def build_corrugated_inner_lip_support(
    *,
    mouth_outer_d: float,
    wall_t: float,
    lip_r: float,
    mouth_z: float,
    bottom_z: float,
    interface_h: float = 0.40,
    radial_inset: float = 0.60,
    radial_width: float = 1.25,
    landing_vertical_drop: float = 0.0,
    wall_thickness: float = 0.70,
    wave_amplitude: float = 0.22,
    wave_count: int = 72,
    samples_per_wave: int = 6,
    base_h: float = 1.20,
    base_inner_extra_r: float = 1.20,
    base_outer_extra_r: float = 0.12,
    top_landing_h: float = 1.20,
    top_inner_extra_r: float = 0.0,
    top_outer_extra_r: float = 0.0,
    hoop_h: float = 0.70,
    hoop_spacing: float = 18.0,
    include_intermediate_hoops: bool = True,
) -> Compound:
    """Build a continuous corrugated PLA support wall under the hidden lip."""
    del lip_r
    if wave_count < 8:
        raise ValueError("Corrugated support needs at least eight waves")
    if samples_per_wave < 4:
        raise ValueError("Corrugated support needs at least four samples per wave")
    if wall_thickness <= 0 or wave_amplitude < 0:
        raise ValueError("Corrugated support dimensions are invalid")

    mouth_inner_r = mouth_outer_d / 2 - wall_t
    landing_bottom_z = mouth_z - landing_vertical_drop
    top_z = landing_bottom_z - interface_h
    height = top_z - bottom_z
    if height <= 0:
        raise ValueError("Corrugated support top must be above bottom")

    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    top_inner_r = max(0.0, inner_r - top_inner_extra_r)
    top_outer_r = outer_r + top_outer_extra_r
    center_r = (inner_r + outer_r) / 2
    usable_half_width = radial_width / 2
    if wall_thickness / 2 + wave_amplitude >= usable_half_width:
        raise ValueError("Corrugation does not fit inside the support landing")

    sample_count = wave_count * samples_per_wave
    outer_points: list[tuple[float, float]] = []
    inner_points: list[tuple[float, float]] = []
    for index in range(sample_count):
        theta = math.tau * index / sample_count
        corrugation = wave_amplitude * math.sin(wave_count * theta)
        outer_radius = center_r + corrugation + wall_thickness / 2
        inner_radius = center_r + corrugation - wall_thickness / 2
        outer_points.append(
            (outer_radius * math.cos(theta), outer_radius * math.sin(theta))
        )
        inner_points.append(
            (inner_radius * math.cos(theta), inner_radius * math.sin(theta))
        )

    corrugated_wall = _extruded_planar_ring(
        outer_points,
        inner_points,
        bottom_z=bottom_z,
        height=height,
    )

    parts: list[Part | Solid] = [
        _annular_cylinder(
            inner_radius=max(0.0, inner_r - base_inner_extra_r),
            outer_radius=outer_r + base_outer_extra_r,
            height=base_h,
            center_z=bottom_z + base_h / 2,
        ),
        corrugated_wall,
        _annular_cylinder(
            inner_radius=top_inner_r,
            outer_radius=top_outer_r,
            height=top_landing_h,
            center_z=top_z - top_landing_h / 2,
        ),
    ]
    if include_intermediate_hoops:
        ring_z = bottom_z + base_h + hoop_spacing
        while ring_z < top_z - hoop_spacing * 0.55:
            parts.append(
                _annular_cylinder(
                    inner_radius=inner_r,
                    outer_radius=outer_r,
                    height=hoop_h,
                    center_z=ring_z,
                )
            )
            ring_z += hoop_spacing

    support = Compound(
        children=[solid for part in parts for solid in part.solids()]
    )
    if support is None or not support.is_valid:
        raise ValueError("Corrugated support wall is not valid")
    return support


def build_rear_flange_support_ring(
    *,
    flange_d: float,
    flange_t: float,
    rear_spigot_l: float,
    rear_spigot_od: float,
    inner_clearance: float = 0.55,
    outer_inset: float = 0.65,
    interface_h: float = 0.20,
    upper_clearance: float = 0.0,
    lower_clearance: float = 0.0,
) -> Part:
    """Build a removable PLA washer supporting the rear flange underside."""
    bottom_z = -flange_t - rear_spigot_l
    flange_bottom_z = -flange_t
    support_top_z = flange_bottom_z - upper_clearance - interface_h - lower_clearance
    height = support_top_z - bottom_z
    if height <= 0:
        raise ValueError("Rear flange support ring has no positive height")
    return _annular_cylinder(
        inner_radius=rear_spigot_od / 2 + inner_clearance,
        outer_radius=flange_d / 2 - outer_inset,
        height=height,
        center_z=bottom_z + height / 2,
    )


def build_rear_flange_petg_interface_ring(
    *,
    flange_d: float,
    flange_t: float,
    rear_spigot_l: float,
    rear_spigot_od: float,
    inner_clearance: float = 0.55,
    outer_inset: float = 0.65,
    interface_h: float = 0.20,
    upper_clearance: float = 0.0,
) -> Part:
    """Build the PETG breakaway washer below the rear flange."""
    del rear_spigot_l
    flange_bottom_z = -flange_t
    return _annular_cylinder(
        inner_radius=rear_spigot_od / 2 + inner_clearance,
        outer_radius=flange_d / 2 - outer_inset,
        height=interface_h,
        center_z=flange_bottom_z - upper_clearance - interface_h / 2,
    )


def build_sacrificial_inner_lip_support(
    *,
    mouth_outer_d: float,
    wall_t: float,
    lip_r: float,
    mouth_z: float,
    bottom_z: float,
    interface_h: float = 0.20,
    post_count: int = 72,
    post_d: float = 1.65,
    hoop_h: float = 0.86,
    hoop_spacing: float = 16.5,
    radial_inset: float = 0.48,
    radial_width: float = 1.24,
    post_center_radial_offset: float | None = None,
    top_landing_radial_width: float | None = None,
    top_landing_h: float | None = None,
    landing_vertical_drop: float = 1.42,
    base_inner_extra_r: float = 1.45,
    base_outer_extra_r: float = 0.10,
    base_h: float = 1.10,
) -> Compound:
    """Build the PLA body of the removable hidden inner-lip support cage."""
    del lip_r
    mouth_inner_r = mouth_outer_d / 2 - wall_t
    landing_bottom_z = mouth_z - landing_vertical_drop
    top_z = landing_bottom_z - interface_h
    inner_r = mouth_inner_r + radial_inset
    outer_r = inner_r + radial_width
    top_outer_r = inner_r + (
        radial_width
        if top_landing_radial_width is None
        else top_landing_radial_width
    )
    top_hoop_h = hoop_h if top_landing_h is None else top_landing_h
    center_r = (
        (inner_r + outer_r) / 2
        if post_center_radial_offset is None
        else inner_r + post_center_radial_offset
    )
    height = top_z - bottom_z
    if height <= 0:
        raise ValueError("Support cage top must be above bottom")

    parts: list[Part] = [
        _annular_cylinder(
            inner_radius=max(0.0, inner_r - base_inner_extra_r),
            outer_radius=outer_r + base_outer_extra_r,
            height=base_h,
            center_z=bottom_z + base_h / 2,
        ),
        _annular_cylinder(
            inner_radius=inner_r,
            outer_radius=top_outer_r,
            height=top_hoop_h,
            center_z=top_z - top_hoop_h / 2,
        )
    ]
    ring_z = bottom_z + base_h + hoop_spacing
    while ring_z < top_z - hoop_spacing * 0.55:
        parts.append(
            _annular_cylinder(
                inner_radius=inner_r,
                outer_radius=outer_r,
                height=hoop_h,
                center_z=ring_z,
            )
        )
        ring_z += hoop_spacing

    post_h = height
    post_center_z = bottom_z + post_h / 2
    post = Cylinder(
        radius=post_d / 2,
        height=post_h,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    for index in range(post_count):
        angle = math.tau * index / post_count
        parts.append(
            Location(
                (
                    center_r * math.cos(angle),
                    center_r * math.sin(angle),
                    post_center_z,
                )
            )
            * post
        )

    support = Compound(
        children=[solid for part in parts for solid in part.solids()]
    )
    if support is None or not support.is_valid:
        raise ValueError("Sacrificial support cage is not valid")
    return support


def build_jmlc_horn_with_print_assist(
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
    rear_spigot_l: float = 0.0,
    rear_spigot_od: float | None = None,
) -> Compound:
    """Build the experimental horn plus permanent print assists as solids."""
    print("  building copied baseline horn...", flush=True)
    horn = build_jmlc_horn(
        throat_d=throat_d,
        mouth_outer_d=mouth_outer_d,
        wall_t=wall_t,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
        lip_r=lip_r,
        flange_d=flange_d,
        flange_t=flange_t,
        bolt_clearance_d=bolt_clearance_d,
        bolt_3_bcd=bolt_3_bcd,
        bolt_2_bcd=bolt_2_bcd,
        rear_spigot_l=rear_spigot_l,
        rear_spigot_od=rear_spigot_od,
    )

    print("  deriving experimental mouth profile...", flush=True)
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

    print("  building hidden inner-lip landing...", flush=True)
    landing = _inner_lip_print_landing(
        mouth_inner_r=mouth_inner_r,
        mouth_z=mouth_z,
        lip_r=lip_r,
    )
    print("  packaging horn and permanent assist bodies...", flush=True)
    horn = Compound(children=[*horn.solids(), landing])
    if horn is None or not horn.is_valid:
        raise ValueError("Experimental print-assist horn is not valid")
    return horn


def build_jmlc_horn_print_assist_assembly(
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
    rear_spigot_l: float = 0.0,
    rear_spigot_od: float | None = None,
) -> tuple[Compound, Compound, Solid, Compound]:
    """Return the experimental horn, PLA cage, PETG cap, and assembly."""
    horn = build_jmlc_horn_with_print_assist(
        throat_d=throat_d,
        mouth_outer_d=mouth_outer_d,
        wall_t=wall_t,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
        lip_r=lip_r,
        flange_d=flange_d,
        flange_t=flange_t,
        bolt_clearance_d=bolt_clearance_d,
        bolt_3_bcd=bolt_3_bcd,
        bolt_2_bcd=bolt_2_bcd,
        rear_spigot_l=rear_spigot_l,
        rear_spigot_od=rear_spigot_od,
    )
    print("  deriving support-cage profile...", flush=True)
    profile, _cutoff_hz = jmlc_profile_points(
        throat_d=throat_d,
        mouth_inner_r=mouth_outer_d / 2 - wall_t,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
        step=step,
    )
    inner = [(radius, z - flange_t - rear_spigot_l) for radius, z in profile]
    print("  building sacrificial support cage...", flush=True)
    support = build_sacrificial_inner_lip_support(
        mouth_outer_d=mouth_outer_d,
        wall_t=wall_t,
        lip_r=lip_r,
        mouth_z=inner[-1][1],
        bottom_z=-flange_t - rear_spigot_l,
    )
    print("  building PETG breakaway cap...", flush=True)
    interface_cap = build_inner_lip_petg_interface_cap(
        mouth_outer_d=mouth_outer_d,
        wall_t=wall_t,
        lip_r=lip_r,
        mouth_z=inner[-1][1],
    )
    print("  packaging full print-assist assembly...", flush=True)
    assembly = Compound(
        children=[*horn.solids(), *support.solids(), *interface_cap.solids()]
    )
    return horn, support, interface_cap, assembly


def build_jmlc_horn(
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
    rear_spigot_l: float = 0.0,
    rear_spigot_od: float | None = None,
    convert_to_nurbs: bool = True,
) -> Part:
    """Build a printable 1 in Le Cleac'h horn with DE250 bolt patterns."""
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
    if convert_to_nurbs:
        horn_body = _to_nurbs_solid(horn_body)

    flange = Cylinder(
        radius=flange_d / 2,
        height=flange_t,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    flange = Location((0, 0, -flange_t / 2)) * flange
    collar_h = flange_t + max(4.0, wall_t * 1.5)
    collar_outer_r = throat_d / 2 + wall_t + 6.0
    throat_collar = Cylinder(
        radius=collar_outer_r,
        height=collar_h,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        mode=Mode.PRIVATE,
    )
    throat_collar = Location((0, 0, (-flange_t + collar_h) / 2)) * throat_collar
    adapter = _primary_shape((throat_collar + flange).clean().fix())
    if rear_spigot_l > 0:
        spigot_od = rear_spigot_od or (throat_d + 2 * wall_t)
        spigot = Cylinder(
            radius=spigot_od / 2,
            height=rear_spigot_l,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.PRIVATE,
        )
        spigot = Location((0, 0, -flange_t - rear_spigot_l / 2)) * spigot
        adapter = _primary_shape((adapter + spigot).clean().fix())
    adapter = _primary_shape(
        adapter
        - _revolved_acoustic_void(
            inner,
            # A positive clearance leaves a microscopic gap between the
            # adapter and thickened horn wall, so OpenCascade returns two
            # solids and the smaller adapter can be dropped downstream.
            # Exact tangency preserves the JMLC acoustic path and fuses as one
            # solid with this wall topology.
            radial_clearance=0.0,
            throat_extend=1.0,
        )
    )
    adapter = _primary_shape(adapter.clean().fix())

    horn = _primary_shape(horn_body.fuse(adapter))
    horn = _primary_shape(horn.clean().fix())
    if exit_angle_deg <= 90:
        lip = Torus(
            major_radius=mouth_outer_r - lip_r,
            minor_radius=lip_r,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.PRIVATE,
        )
        horn += Location((0, 0, mouth_z)) * lip
    horn = _primary_shape(horn.clean().fix())

    for index in range(3):
        angle = math.tau * index / 3 + math.pi / 2
        radius = bolt_3_bcd / 2
        horn = _primary_shape(
            horn
            - _cylinder_z(
                diameter=bolt_clearance_d,
                depth=flange_t + 2.0,
                center=(
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    -flange_t / 2,
                ),
            )
        )
        horn = _primary_shape(horn.clean().fix())

    for angle in (0.0, math.pi):
        radius = bolt_2_bcd / 2
        horn = _primary_shape(
            horn
            - _cylinder_z(
                diameter=bolt_clearance_d,
                depth=flange_t + 2.0,
                center=(
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    -flange_t / 2,
                ),
            )
        )
        horn = _primary_shape(horn.clean().fix())

    return horn


def horn_dimensions(part: Part) -> dict[str, object]:
    bb = part.bounding_box()
    return {
        "bounding_box_mm": (
            round(bb.size.X, 3),
            round(bb.size.Y, 3),
            round(bb.size.Z, 3),
        ),
        "volume_cm3": round(part.volume / 1000, 1),
        "is_valid": part.is_valid,
        "n_solids": len(part.solids()),
        "n_faces": len(part.faces()),
        "n_edges": len(part.edges()),
    }
