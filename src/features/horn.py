"""Le Cleac'h / JMLC horn geometry for the B&C DE250."""

from __future__ import annotations

import math

from build123d import (
    Align,
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
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_NurbsConvert,
)
from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt
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
    if hasattr(shape, "bounding_box"):
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
