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
from OCP.GeomAPI import (
    GeomAPI_Interpolate,
    GeomAPI_PointsToBSpline,
    GeomAPI_ProjectPointOnCurve,
)
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Vec
from OCP.TColgp import TColgp_Array1OfPnt, TColgp_HArray1OfPnt
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


def _le_cleach_2007_step_mm(*, cutoff_hz: float, throat_d: float) -> float:
    """Return the 4000-row increment used by Le Cleac'h's 2007 workbook."""
    estimated_length = (
        11600.0
        / 2.275 ** (math.log(cutoff_hz / 20.0) / math.log(2.0))
        / 1.1375 ** (math.log(throat_d / 380.0) / math.log(2.0))
    )
    return estimated_length / 4000.0


def _le_cleach_2007_points_for_cutoff(
    *,
    throat_d: float,
    mouth_inner_r: float,
    cutoff_hz: float,
    wavefront_t: float,
    throat_angle_deg: float,
    sound_speed_mm_s: float = 344_000.0,
) -> tuple[list[tuple[float, float]], float, float]:
    """Reproduce the original 2007 JMLC spreadsheet recurrence.

    ``throat_angle_deg`` is the half-angle; the workbook's driver-exit-angle
    input is twice this value.  The equations below correspond to workbook
    cells B24:H4028 in ``pavillon_JMLC.xls``.
    """
    throat_r = throat_d / 2.0
    phi0 = math.radians(throat_angle_deg)
    if not 0.0 < phi0 < math.pi / 2.0:
        raise ValueError("throat_angle_deg must be between 0 and 90 degrees")
    if cutoff_hz <= 0.0 or mouth_inner_r <= throat_r:
        raise ValueError("JMLC cutoff and mouth radius must be positive")

    step = _le_cleach_2007_step_mm(
        cutoff_hz=cutoff_hz,
        throat_d=throat_d,
    )
    wavefront_r0 = throat_r / math.sin(phi0)
    cap_h = wavefront_r0 - math.sqrt(wavefront_r0**2 - throat_r**2)
    s0 = math.pi * (throat_r**2 + cap_h**2)
    m = 4.0 * math.pi * cutoff_hz / (sound_speed_mm_s / 1000.0)

    area = [s0]
    radius = [throat_r]
    axial = [0.0]
    compensator_length = [0.0]
    cumulative_compensator = [0.0]

    for index in range(1, 8001):
        path_l = index * step
        u = m * path_l / 2000.0
        target_area = s0 * (
            math.cosh(u) + wavefront_t * math.sinh(u)
        ) ** 2

        if index == 1:
            next_compensator = math.sqrt(target_area / math.pi) - math.sqrt(
                area[-1] / math.pi
            )
        elif index == 2:
            next_compensator = (
                math.sqrt(target_area / math.pi)
                - math.sqrt(area[-1] / math.pi)
                - compensator_length[-1]
            )
        else:
            peripheral_area = target_area - (
                2.0 * math.sqrt(area[-1]) - math.sqrt(area[-2])
            ) ** 2
            estimated_radius = (
                3.0 * radius[-1] - 3.0 * radius[-2] + radius[-3]
            )
            next_compensator = peripheral_area / (
                2.0 * math.pi * estimated_radius
            )

        next_cumulative = cumulative_compensator[-1] + next_compensator
        wall_angle = next_cumulative / step
        next_axial = axial[-1] + math.cos(wall_angle) * step
        next_radius = radius[-1] + math.sin(wall_angle) * step
        if not all(
            math.isfinite(value)
            for value in (
                target_area,
                next_compensator,
                wall_angle,
                next_axial,
                next_radius,
            )
        ):
            raise ValueError("Le Cleac'h 2007 recurrence diverged")
        if next_radius <= radius[-1]:
            raise ValueError("Le Cleac'h 2007 recurrence stopped expanding")

        area.append(target_area)
        compensator_length.append(next_compensator)
        cumulative_compensator.append(next_cumulative)
        axial.append(next_axial)
        radius.append(next_radius)

        if next_radius >= mouth_inner_r:
            fraction = (mouth_inner_r - radius[-2]) / (
                radius[-1] - radius[-2]
            )
            mouth_axial = axial[-2] + fraction * (axial[-1] - axial[-2])
            previous_angle = cumulative_compensator[-2] / step
            terminal_angle = previous_angle + fraction * (
                wall_angle - previous_angle
            )
            points = list(zip(radius[:-1], axial[:-1]))
            points.append((mouth_inner_r, mouth_axial))
            return points, math.degrees(terminal_angle), step

    raise ValueError("Le Cleac'h 2007 recurrence did not reach the mouth")


def le_cleach_2007_cutoff_hz_for_exit_angle(
    *,
    throat_d: float,
    mouth_inner_r: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
) -> float:
    """Solve cutoff so the exact 2007 recurrence reaches the exit angle."""

    def angle_at(cutoff_hz: float) -> float:
        _points, terminal_angle, _step = _le_cleach_2007_points_for_cutoff(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            cutoff_hz=cutoff_hz,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
        )
        return terminal_angle

    low = high = None
    last_valid: tuple[float, float] | None = None
    for candidate_index in range(351):
        candidate = 250.0 + 5.0 * candidate_index
        try:
            candidate_angle = angle_at(candidate)
        except ValueError:
            continue
        if candidate_angle < exit_angle_deg:
            last_valid = (candidate, candidate_angle)
            continue
        if last_valid is not None:
            low = last_valid[0]
            high = candidate
            break
    if low is None or high is None:
        raise ValueError(
            "Unable to bracket the exact Le Cleac'h 2007 cutoff for the exit angle"
        )

    for _ in range(44):
        mid = (low + high) / 2.0
        if angle_at(mid) < exit_angle_deg:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def le_cleach_2007_profile_points(
    *,
    throat_d: float,
    mouth_inner_r: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
) -> tuple[list[tuple[float, float]], float, float]:
    """Return exact 2007-workbook points, solved cutoff, and row increment."""
    cutoff_hz = le_cleach_2007_cutoff_hz_for_exit_angle(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        exit_angle_deg=exit_angle_deg,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
    )
    points, _terminal_angle, row_step = _le_cleach_2007_points_for_cutoff(
        throat_d=throat_d,
        mouth_inner_r=mouth_inner_r,
        cutoff_hz=cutoff_hz,
        wavefront_t=wavefront_t,
        throat_angle_deg=throat_angle_deg,
    )
    return points, cutoff_hz, row_step


def le_cleach_2007_profile_for_axial_length(
    *,
    throat_d: float,
    mouth_inner_r: float,
    target_axial_length_mm: float,
    exit_angle_deg: float,
    throat_angle_deg: float,
    wavefront_t_bounds: tuple[float, float] = (0.05, 4.0),
    axial_tolerance_mm: float = 1e-7,
    max_iterations: int = 48,
) -> tuple[list[tuple[float, float]], float, float, float]:
    """Solve the exact 2007 profile from a requested acoustic axial length.

    The spreadsheet recurrence treats the wavefront factor ``T`` as an input.
    For a fixed throat, mouth, throat tangent, and terminal rollback, this
    helper solves ``T`` so the resulting meridian reaches the requested axial
    length.  It returns the profile points, solved cutoff, workbook row step,
    and solved wavefront factor.
    """
    if target_axial_length_mm <= 0.0:
        raise ValueError("target_axial_length_mm must be positive")
    if axial_tolerance_mm <= 0.0:
        raise ValueError("axial_tolerance_mm must be positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least one")

    lower_t, upper_t = wavefront_t_bounds
    if lower_t <= 0.0 or upper_t <= lower_t:
        raise ValueError(
            "wavefront_t_bounds must be positive and strictly increasing"
        )

    def evaluate(
        wavefront_t: float,
    ) -> tuple[
        float,
        list[tuple[float, float]],
        float,
        float,
    ]:
        points, cutoff_hz, row_step = le_cleach_2007_profile_points(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=exit_angle_deg,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
        )
        residual = points[-1][1] - target_axial_length_mm
        return residual, points, cutoff_hz, row_step

    # The exact recurrence has finite valid regions for some parameter sets.
    # Start with the requested bounds, then use a small logarithmic scan only
    # when an endpoint is invalid or the endpoints do not bracket the target.
    samples: list[
        tuple[
            float,
            float,
            list[tuple[float, float]],
            float,
            float,
        ]
    ] = []

    def add_sample(wavefront_t: float) -> None:
        try:
            residual, points, cutoff_hz, row_step = evaluate(wavefront_t)
        except (OverflowError, ValueError):
            return
        samples.append(
            (wavefront_t, residual, points, cutoff_hz, row_step)
        )

    add_sample(lower_t)
    add_sample(upper_t)

    def bracketed_pair():
        ordered = sorted(samples, key=lambda item: item[0])
        for left, right in zip(ordered, ordered[1:]):
            if left[1] == 0.0:
                return left, left
            if right[1] == 0.0:
                return right, right
            if left[1] * right[1] < 0.0:
                return left, right
        return None

    bracket = bracketed_pair()
    if bracket is None:
        log_lower = math.log(lower_t)
        log_span = math.log(upper_t) - log_lower
        for index in range(1, 24):
            candidate = math.exp(log_lower + log_span * index / 24.0)
            add_sample(candidate)
        bracket = bracketed_pair()

    if bracket is None:
        lengths = sorted(
            target_axial_length_mm + sample[1] for sample in samples
        )
        if lengths:
            available = f"{lengths[0]:.6f} to {lengths[-1]:.6f} mm"
        else:
            available = "no valid profiles"
        raise ValueError(
            "Unable to bracket the requested Le Cleac'h axial length; "
            f"valid sampled lengths were {available}"
        )

    left, right = bracket
    if left is right:
        return left[2], left[3], left[4], left[0]

    best = min((left, right), key=lambda item: abs(item[1]))
    for _ in range(max_iterations):
        middle_t = (left[0] + right[0]) / 2.0
        residual, points, cutoff_hz, row_step = evaluate(middle_t)
        middle = (
            middle_t,
            residual,
            points,
            cutoff_hz,
            row_step,
        )
        if abs(middle[1]) < abs(best[1]):
            best = middle
        if abs(middle[1]) <= axial_tolerance_mm:
            return middle[2], middle[3], middle[4], middle[0]
        if left[1] * middle[1] <= 0.0:
            right = middle
        else:
            left = middle

    if abs(best[1]) > axial_tolerance_mm:
        raise ValueError(
            "Le Cleac'h axial-length solve did not converge: "
            f"{best[1]:.9f} mm residual"
        )
    return best[2], best[3], best[4], best[0]


def jmlc_profile_metadata(
    *,
    throat_d: float,
    mouth_outer_d: float,
    wall_t: float,
    exit_angle_deg: float,
    wavefront_t: float,
    throat_angle_deg: float,
    step: float,
    profile_method: str = "legacy_recurrence",
) -> dict[str, object]:
    """Small diagnostics payload for the generated JMLC profile."""
    mouth_inner_r = mouth_outer_d / 2 - wall_t
    if profile_method == "le_cleach_2007":
        points, cutoff_hz, row_step = le_cleach_2007_profile_points(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=exit_angle_deg,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
        )
    elif profile_method == "legacy_recurrence":
        points, cutoff_hz = jmlc_profile_points(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=exit_angle_deg,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
            step=step,
        )
        row_step = step
    else:
        raise ValueError(f"Unknown JMLC profile method: {profile_method}")
    endpoint_data: dict[str, float] = {}
    if profile_method == "le_cleach_2007":
        _verified_points, recurrence_terminal_angle, _verified_step = (
            _le_cleach_2007_points_for_cutoff(
                throat_d=throat_d,
                mouth_inner_r=mouth_inner_r,
                cutoff_hz=cutoff_hz,
                wavefront_t=wavefront_t,
                throat_angle_deg=throat_angle_deg,
            )
        )
        curve = _spline_curve(
            points,
            start_angle_deg=throat_angle_deg,
            end_angle_deg=exit_angle_deg,
        )
        start_point = gp_Pnt()
        start_tangent = gp_Vec()
        end_point = gp_Pnt()
        end_tangent = gp_Vec()
        curve.D1(curve.FirstParameter(), start_point, start_tangent)
        curve.D1(curve.LastParameter(), end_point, end_tangent)

        def wall_angle(vector: gp_Vec) -> float:
            angle = math.degrees(math.atan2(vector.X(), vector.Z()))
            return angle + 360.0 if angle < 0.0 else angle

        endpoint_data = {
            "recurrence_terminal_angle_deg": recurrence_terminal_angle,
            "cad_spline_throat_tangent_deg": wall_angle(start_tangent),
            "cad_spline_terminal_tangent_deg": wall_angle(end_tangent),
            "cad_spline_constraint_point_count": len(
                _cad_spline_constraint_points(
                    points,
                    maximum=_cad_spline_constraint_limit(exit_angle_deg),
                )
            ),
            "cad_spline_max_profile_deviation_mm": (
                _maximum_profile_deviation_mm(points, curve)
            ),
        }

    return {
        "profile": (
            "Le Cleac'h 2007 spreadsheet recurrence"
            if profile_method == "le_cleach_2007"
            else "Le Cleac'h / JMLC legacy recurrence"
        ),
        "profile_method": profile_method,
        "solved_cutoff_hz": round(cutoff_hz, 1),
        "solved_cutoff_hz_exact": cutoff_hz,
        "mouth_inner_d_mm": round(2 * mouth_inner_r, 3),
        "axial_length_mm": round(points[-1][1], 3),
        "axial_length_mm_exact": points[-1][1],
        "exit_angle_deg": round(exit_angle_deg, 3),
        "calculation_step_mm": round(row_step, 6),
        "sample_count": len(points),
        **endpoint_data,
    }


def _spline_curve(
    points: list[tuple[float, float]],
    *,
    start_angle_deg: float | None = None,
    end_angle_deg: float | None = None,
):
    if (start_angle_deg is None) != (end_angle_deg is None):
        raise ValueError("Both horn spline endpoint angles must be supplied")

    if start_angle_deg is not None and end_angle_deg is not None:
        # The workbook recurrence remains at its full 4000-row resolution.
        # Constraining all reached rows produces a needlessly huge NURBS that
        # some STEP tessellators skip. The sharper curvature above 150 degrees
        # needs a denser, still bounded sample to retain the same measured
        # meridian accuracy as the 140-degree production profile.
        cad_points = _cad_spline_constraint_points(
            points,
            maximum=_cad_spline_constraint_limit(end_angle_deg),
        )
        point_array = TColgp_HArray1OfPnt(1, len(cad_points))
        for index, (radius, z) in enumerate(cad_points, 1):
            point_array.SetValue(index, gp_Pnt(radius, 0, z))
        interpolator = GeomAPI_Interpolate(point_array, False, 1e-7)

        def tangent(angle_deg: float) -> gp_Vec:
            angle = math.radians(angle_deg)
            # Le Cleac'h's wall angle is measured from the horn axis: the
            # meridian therefore advances by (dr, dz) = (sin(a), cos(a)).
            return gp_Vec(math.sin(angle), 0.0, math.cos(angle))

        interpolator.Load(
            tangent(start_angle_deg),
            tangent(end_angle_deg),
            True,
        )
        interpolator.Perform()
        if not interpolator.IsDone():
            raise ValueError("Unable to interpolate the tangent-constrained horn")
        return interpolator.Curve()

    point_array = TColgp_Array1OfPnt(1, len(points))
    for index, (radius, z) in enumerate(points, 1):
        point_array.SetValue(index, gp_Pnt(radius, 0, z))
    return GeomAPI_PointsToBSpline(point_array).Curve()


def _cad_spline_constraint_limit(exit_angle_deg: float) -> int:
    """Bound CAD spline density while resolving sharper rolled-back lips."""
    return 801 if exit_angle_deg > 150.0 else 401


def _cad_spline_constraint_points(
    points: list[tuple[float, float]],
    *,
    maximum: int = 401,
) -> list[tuple[float, float]]:
    if len(points) <= maximum:
        return points
    stride = math.ceil((len(points) - 1) / (maximum - 1))
    constrained = points[::stride]
    if constrained[-1] != points[-1]:
        constrained = [*constrained, points[-1]]
    return constrained


def _maximum_profile_deviation_mm(
    points: list[tuple[float, float]],
    curve,
) -> float:
    maximum = 0.0
    for radius, z in points:
        projection = GeomAPI_ProjectPointOnCurve(gp_Pnt(radius, 0.0, z), curve)
        maximum = max(maximum, projection.LowerDistance())
    return maximum


def _spline_edge(
    points: list[tuple[float, float]],
    *,
    start_angle_deg: float | None = None,
    end_angle_deg: float | None = None,
):
    curve = _spline_curve(
        points,
        start_angle_deg=start_angle_deg,
        end_angle_deg=end_angle_deg,
    )
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
    start_angle_deg: float | None = None,
    end_angle_deg: float | None = None,
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
    wire_maker.Add(
        _spline_edge(
            void_profile,
            start_angle_deg=start_angle_deg,
            end_angle_deg=end_angle_deg,
        )
    )
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
    start_angle_deg: float | None = None,
    end_angle_deg: float | None = None,
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
        _spline_edge(
            surface_profile,
            start_angle_deg=start_angle_deg,
            end_angle_deg=end_angle_deg,
        ),
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
    profile_method: str = "legacy_recurrence",
    include_three_bolt_pattern: bool = True,
    include_two_bolt_pattern: bool = True,
) -> Part:
    """Build a printable 1 in Le Cleac'h horn with DE250 bolt patterns."""
    mouth_outer_r = mouth_outer_d / 2
    mouth_inner_r = mouth_outer_r - wall_t
    if profile_method == "le_cleach_2007":
        profile, _cutoff_hz, _row_step = le_cleach_2007_profile_points(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=exit_angle_deg,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
        )
    elif profile_method == "legacy_recurrence":
        profile, _cutoff_hz = jmlc_profile_points(
            throat_d=throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=exit_angle_deg,
            wavefront_t=wavefront_t,
            throat_angle_deg=throat_angle_deg,
            step=step,
        )
    else:
        raise ValueError(f"Unknown JMLC profile method: {profile_method}")
    inner = [(radius, z - flange_t - rear_spigot_l) for radius, z in profile]
    mouth_z = inner[-1][1]
    horn_body = _revolved_meridian_body(
        inner,
        wall_t=wall_t,
        throat_overlap=0.0,
        mouth_round_r=lip_r,
        start_angle_deg=(
            throat_angle_deg if profile_method == "le_cleach_2007" else None
        ),
        end_angle_deg=(
            exit_angle_deg if profile_method == "le_cleach_2007" else None
        ),
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
            start_angle_deg=(
                throat_angle_deg
                if profile_method == "le_cleach_2007"
                else None
            ),
            end_angle_deg=(
                exit_angle_deg if profile_method == "le_cleach_2007" else None
            ),
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

    if include_three_bolt_pattern:
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

    if include_two_bolt_pattern:
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
