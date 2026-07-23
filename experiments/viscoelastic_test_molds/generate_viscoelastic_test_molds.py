"""Generate FDM tooling for simple viscoelastic rebound comparisons.

Outputs:

* a two-piece mold for a nominal 25 mm cast polyurethane ball;
* a circular tray for a 40 mm diameter x 12.5 mm test coupon;
* individual print-oriented STL files and editable STEP files;
* combined print layouts and a JSON geometry report.

All dimensions are millimeters.
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

import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Pos,
    Rot,
    Sphere,
    Unit,
    export_step,
    export_stl,
)


HERE = Path(__file__).resolve().parent
OUT = HERE / "build"

STL_LINEAR_TOLERANCE = 0.03
STL_ANGULAR_TOLERANCE = 0.08


@dataclass(frozen=True)
class MoldDimensions:
    """Parameters intended to be easy to tune for a specific printer."""

    ball_diameter: float = 25.0
    sphere_block_width: float = 48.0
    sphere_outer_skin: float = 5.0

    registration_pin_diameter: float = 4.0
    registration_pin_length: float = 3.0
    registration_hole_diameter: float = 4.4
    registration_hole_depth: float = 3.4
    registration_pin_offset: float = 18.5

    funnel_stem_diameter: float = 6.18
    funnel_socket_diameter: float = 6.6
    funnel_socket_depth: float = 3.0
    pour_gate_diameter: float = 4.0
    vent_diameter: float = 1.2
    vent_offset: float = 5.0

    coupon_diameter: float = 40.0
    coupon_depth: float = 12.5
    coupon_wall: float = 3.0
    coupon_floor: float = 3.0

    print_layout_gap: float = 8.0

    @property
    def sphere_radius(self) -> float:
        return self.ball_diameter / 2

    @property
    def sphere_half_height(self) -> float:
        return self.sphere_radius + self.sphere_outer_skin

    @property
    def coupon_outer_diameter(self) -> float:
        return self.coupon_diameter + 2 * self.coupon_wall


D = MoldDimensions()


def _cylinder(
    diameter: float,
    height: float,
    *,
    z: float = 0.0,
    x: float = 0.0,
    y: float = 0.0,
):
    return Pos(x, y, z) * Cylinder(
        radius=diameter / 2,
        height=height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def build_sphere_mold() -> tuple[Any, Any]:
    """Return bottom and top mold halves in their assembled positions.

    The equator is the z=0 parting plane. Four pins are integral to the bottom
    half; clearance holes are in the top half. Both exported STL halves are
    later oriented with their outside flat faces on the print bed.
    """

    half_h = D.sphere_half_height
    cavity = Sphere(D.sphere_radius)

    bottom = Pos(0, 0, -half_h) * Box(
        D.sphere_block_width,
        D.sphere_block_width,
        half_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    top = Box(
        D.sphere_block_width,
        D.sphere_block_width,
        half_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bottom = (bottom - cavity).clean()
    top = (top - cavity).clean()

    pin_xy = (-D.registration_pin_offset, D.registration_pin_offset)
    for x in pin_xy:
        for y in pin_xy:
            pin = _cylinder(
                D.registration_pin_diameter,
                D.registration_pin_length,
                x=x,
                y=y,
            )
            bottom = (bottom + pin).clean()

            hole = _cylinder(
                D.registration_hole_diameter,
                D.registration_hole_depth + 0.1,
                z=-0.1,
                x=x,
                y=y,
            )
            top = (top - hole).clean()

    # A 6.18 mm funnel stem would be unreliable in a nominal 6.2 mm printed
    # bore. The 6.6 mm socket gives 0.21 mm radial clearance. A short 4 mm gate
    # limits the cured sprue without restricting 1,800-2,000 cP VytaFlex.
    socket_z = half_h - D.funnel_socket_depth
    socket = _cylinder(
        D.funnel_socket_diameter,
        D.funnel_socket_depth + 0.2,
        z=socket_z,
    )
    gate = _cylinder(
        D.pour_gate_diameter,
        half_h - D.sphere_radius + 0.4,
        z=D.sphere_radius - 0.2,
    )
    top = (top - socket - gate).clean()

    # Two high-point witness vents let air escape even if the funnel stem
    # seals its socket. Seeing rubber at both vents confirms a complete fill.
    vent_start = math.sqrt(
        D.sphere_radius**2 - D.vent_offset**2
    ) - 0.2
    for x in (-D.vent_offset, D.vent_offset):
        vent = _cylinder(
            D.vent_diameter,
            half_h - vent_start + 0.2,
            z=vent_start,
            x=x,
        )
        top = (top - vent).clean()

    return bottom, top


def build_coupon_tray():
    """Return a tray whose open cavity is the finished coupon envelope."""

    height = D.coupon_floor + D.coupon_depth
    tray = _cylinder(D.coupon_outer_diameter, height)
    cavity = _cylinder(
        D.coupon_diameter,
        D.coupon_depth + 0.2,
        z=D.coupon_floor,
    )
    return (tray - cavity).clean()


def _bottom_print_orientation(shape):
    return Pos(0, 0, D.sphere_half_height) * shape


def _top_print_orientation(shape):
    # Rotate the assembled upper half so its flat outside face is on the bed
    # and its hemispherical cavity opens upward without support material.
    return Pos(0, 0, D.sphere_half_height) * Rot(180, 0, 0) * shape


def _bbox(shape) -> dict[str, float]:
    box = shape.bounding_box()
    return {
        "x_mm": round(box.size.X, 4),
        "y_mm": round(box.size.Y, 4),
        "z_mm": round(box.size.Z, 4),
        "min_z_mm": round(box.min.Z, 4),
        "max_z_mm": round(box.max.Z, 4),
    }


def _validate_single_solid(name: str, shape) -> None:
    solid_count = len(shape.solids())
    if solid_count != 1:
        raise ValueError(f"{name} must contain one solid, found {solid_count}")
    if not shape.is_valid:
        raise ValueError(f"{name} is not a valid solid")
    if shape.volume <= 0:
        raise ValueError(f"{name} has non-positive volume")


def _export_pair(shape, stem: str) -> dict[str, str]:
    step_path = OUT / f"{stem}.step"
    stl_path = OUT / f"{stem}.stl"
    export_step(shape, step_path, unit=Unit.MM, write_pcurves=False)
    export_stl(
        shape,
        stl_path,
        tolerance=STL_LINEAR_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    return {
        "step": str(step_path.resolve()),
        "stl": str(stl_path.resolve()),
    }


def _binary_stl_diagnostics(path: Path) -> dict[str, Any]:
    """Read back a binary STL and report its mesh envelope and volume."""

    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path.name} is too small to be a binary STL")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + triangle_count * 50:
        raise ValueError(f"{path.name} is not the expected binary STL format")

    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    signed_volume_mm3 = 0.0
    offset = 84
    for _ in range(triangle_count):
        offset += 12  # stored normal
        p1 = struct.unpack_from("<fff", data, offset)
        p2 = struct.unpack_from("<fff", data, offset + 12)
        p3 = struct.unpack_from("<fff", data, offset + 24)
        offset += 38  # three vertices plus attribute-byte count
        for point in (p1, p2, p3):
            for axis in range(3):
                mins[axis] = min(mins[axis], point[axis])
                maxs[axis] = max(maxs[axis], point[axis])
        signed_volume_mm3 += (
            p1[0] * (p2[1] * p3[2] - p2[2] * p3[1])
            - p1[1] * (p2[0] * p3[2] - p2[2] * p3[0])
            + p1[2] * (p2[0] * p3[1] - p2[1] * p3[0])
        ) / 6

    return {
        "triangle_count": triangle_count,
        "volume_cm3": round(abs(signed_volume_mm3) / 1000, 3),
        "bbox_mm": {
            "x": round(maxs[0] - mins[0], 4),
            "y": round(maxs[1] - mins[1], 4),
            "z": round(maxs[2] - mins[2], 4),
            "min_z": round(mins[2], 4),
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    bottom, top = build_sphere_mold()
    coupon = build_coupon_tray()
    bottom_print = _bottom_print_orientation(bottom)
    top_print = _top_print_orientation(top)

    for name, shape in (
        ("sphere_mold_bottom", bottom),
        ("sphere_mold_top", top),
        ("sphere_mold_bottom_print", bottom_print),
        ("sphere_mold_top_print", top_print),
        ("coupon_tray", coupon),
    ):
        _validate_single_solid(name, shape)

    assembled_interference_mm3 = (bottom & top).volume
    if assembled_interference_mm3 > 1e-5:
        raise ValueError(
            "Closed sphere mold halves interfere by "
            f"{assembled_interference_mm3:.6f} mm^3"
        )

    bed_offset = (D.sphere_block_width + D.print_layout_gap) / 2
    sphere_print_layout = Compound(
        children=[
            Pos(-bed_offset, 0, 0) * bottom_print,
            Pos(bed_offset, 0, 0) * top_print,
        ]
    )
    coupon_offset = (D.coupon_outer_diameter + D.print_layout_gap) / 2
    coupon_two_up = Compound(
        children=[
            Pos(-coupon_offset, 0, 0) * coupon,
            Pos(coupon_offset, 0, 0) * coupon,
        ]
    )
    assembled = Compound(children=[bottom, top])

    exports: dict[str, dict[str, str]] = {}
    exports["sphere_mold_bottom_print"] = _export_pair(
        bottom_print, "sphere_mold_bottom_print"
    )
    exports["sphere_mold_top_print"] = _export_pair(
        top_print, "sphere_mold_top_print"
    )
    exports["coupon_tray"] = _export_pair(coupon, "coupon_tray_40x12p5")

    assembly_path = OUT / "sphere_mold_assembled.step"
    sphere_layout_path = OUT / "sphere_mold_two_piece_print_layout.stl"
    coupon_layout_path = OUT / "coupon_tray_two_up_print_layout.stl"
    export_step(assembled, assembly_path, unit=Unit.MM, write_pcurves=False)
    export_stl(
        sphere_print_layout,
        sphere_layout_path,
        tolerance=STL_LINEAR_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    export_stl(
        coupon_two_up,
        coupon_layout_path,
        tolerance=STL_LINEAR_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )

    mesh_paths_and_expected_volumes = {
        OUT / "sphere_mold_bottom_print.stl": bottom_print.volume,
        OUT / "sphere_mold_top_print.stl": top_print.volume,
        sphere_layout_path: bottom_print.volume + top_print.volume,
        OUT / "coupon_tray_40x12p5.stl": coupon.volume,
        coupon_layout_path: 2 * coupon.volume,
    }
    mesh_diagnostics = {
        path.name: _binary_stl_diagnostics(path)
        for path in mesh_paths_and_expected_volumes
    }
    for path, expected_volume_mm3 in mesh_paths_and_expected_volumes.items():
        mesh_volume_mm3 = mesh_diagnostics[path.name]["volume_cm3"] * 1000
        relative_error = abs(mesh_volume_mm3 - expected_volume_mm3) / (
            expected_volume_mm3
        )
        if relative_error > 0.001:
            raise ValueError(
                f"{path.name} mesh volume differs from CAD by "
                f"{relative_error:.2%}"
            )

    sphere_volume_ml = 4 / 3 * math.pi * D.sphere_radius**3 / 1000
    coupon_volume_ml = (
        math.pi * (D.coupon_diameter / 2) ** 2 * D.coupon_depth / 1000
    )
    diagnostics = {
        "dimensions": asdict(D),
        "derived": {
            "nominal_ball_volume_ml": round(sphere_volume_ml, 3),
            "coupon_volume_ml": round(coupon_volume_ml, 3),
            "funnel_radial_clearance_mm": round(
                (D.funnel_socket_diameter - D.funnel_stem_diameter) / 2, 3
            ),
            "registration_radial_clearance_mm": round(
                (D.registration_hole_diameter - D.registration_pin_diameter) / 2,
                3,
            ),
        },
        "geometry": {
            "sphere_mold_bottom": {
                "valid": bottom.is_valid,
                "solid_count": len(bottom.solids()),
                "volume_cm3": round(bottom.volume / 1000, 3),
                "bbox": _bbox(bottom),
            },
            "sphere_mold_top": {
                "valid": top.is_valid,
                "solid_count": len(top.solids()),
                "volume_cm3": round(top.volume / 1000, 3),
                "bbox": _bbox(top),
            },
            "assembled_interference_mm3": round(assembled_interference_mm3, 8),
            "coupon_tray": {
                "valid": coupon.is_valid,
                "solid_count": len(coupon.solids()),
                "volume_cm3": round(coupon.volume / 1000, 3),
                "bbox": _bbox(coupon),
            },
            "sphere_print_layout": {
                "solid_count": len(sphere_print_layout.solids()),
                "bbox": _bbox(sphere_print_layout),
            },
            "coupon_two_up": {
                "solid_count": len(coupon_two_up.solids()),
                "bbox": _bbox(coupon_two_up),
            },
        },
        "exported_meshes": mesh_diagnostics,
        "exports": {
            **exports,
            "sphere_mold_assembled_step": str(assembly_path.resolve()),
            "sphere_mold_two_piece_print_layout_stl": str(
                sphere_layout_path.resolve()
            ),
            "coupon_tray_two_up_print_layout_stl": str(
                coupon_layout_path.resolve()
            ),
        },
    }
    report_path = OUT / "diagnostics.json"
    report_path.write_text(json.dumps(diagnostics, indent=2) + "\n")

    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
