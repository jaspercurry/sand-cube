"""Rebuild the isolated, released Front Baffle V1 from its approved seed."""

from __future__ import annotations


# This guard must remain before every native CAD import.
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
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
from pathlib import Path

from build123d import (
    Edge,
    Face,
    Rot,
    Solid,
    Unit,
    Vector,
    Wire,
    export_step,
    import_step,
)


RELEASE_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_PATH = Path(__file__).resolve().with_name(
    "front_baffle_v1_parameters.json"
)
BASE_BAFFLE_STEP = (
    Path(__file__).resolve().parent
    / "inputs/front_baffle_v1_approved_pre_fin.step"
)
OUTPUT_ROOT = Path("build/releases/enclosure_v1/front_baffle")
OUTPUT_NAME = "front_baffle_v1_rebuilt.step"
DIAGNOSTICS_NAME = "front_baffle_v1_rebuild_diagnostics.json"


def _single_solid(shape, *, feature: str) -> Solid:
    solids = list(shape.solids()) if hasattr(shape, "solids") else []
    if len(solids) != 1:
        raise ValueError(f"{feature} is not one solid: {len(solids)}")
    solid = solids[0]
    if not solid.is_valid:
        raise ValueError(f"{feature} is invalid")
    return solid


def _bounds(shape: Solid) -> dict[str, float]:
    box = shape.bounding_box()
    return {
        "min_x": box.min.X,
        "max_x": box.max.X,
        "min_y": box.min.Y,
        "max_y": box.max.Y,
        "min_z": box.min.Z,
        "max_z": box.max.Z,
    }


def _bounds_delta(reference: Solid, final: Solid) -> dict[str, float]:
    before = _bounds(reference)
    after = _bounds(final)
    return {key: after[key] - before[key] for key in before}


def _top_fin(parameters: dict[str, object]) -> Solid:
    thickness = float(parameters["fin_thickness_mm"])
    half_thickness = thickness / 2.0
    inner_radius = float(parameters["fin_inner_radius_mm"])
    bed_y = float(parameters["baffle_bed_y_mm"])
    crown = [
        (
            float(point["x"]),
            float(point["y"]),
            float(point["radius"]),
        )
        for point in parameters["crown_points"]
    ]
    outer_radius = crown[-1][2]
    edges = [
        Edge.make_line(
            (-half_thickness, bed_y, inner_radius),
            (-half_thickness, bed_y, outer_radius),
        ),
        Edge.make_line((-half_thickness, bed_y, outer_radius), crown[-1]),
        Edge.make_spline(
            crown,
            tangents=[
                Vector(crown[1]) - Vector(crown[0]),
                Vector(crown[-1]) - Vector(crown[-2]),
            ],
        ).reversed(),
        Edge.make_line(
            crown[0],
            (-half_thickness, crown[0][1], inner_radius),
        ),
        Edge.make_line(
            (-half_thickness, crown[0][1], inner_radius),
            (-half_thickness, bed_y, inner_radius),
        ),
    ]
    wires = Wire.combine(edges)
    if len(wires) != 1 or not wires[0].is_closed:
        raise ValueError("The frozen V1 fin profile did not close")
    profile = Face(wires[0])
    if profile.area <= 0.01:
        raise ValueError("The frozen V1 fin profile has no area")
    return _single_solid(
        Solid.extrude(profile, Vector(thickness, 0.0, 0.0)).clean().fix(),
        feature="frozen V1 top fin",
    )


def main() -> None:
    if not BASE_BAFFLE_STEP.is_file():
        raise FileNotFoundError(BASE_BAFFLE_STEP)
    parameters = json.loads(PARAMETERS_PATH.read_text())
    base = _single_solid(
        import_step(BASE_BAFFLE_STEP),
        feature="approved pre-fin Front Baffle V1 seed",
    )
    top_fin = _top_fin(parameters)
    tolerance = float(parameters["fin_fuse_tolerance_mm"])
    variant = base
    for index, angle in enumerate(parameters["fin_angles_deg"], start=1):
        fin = _single_solid(
            (Rot(0.0, float(angle), 0.0) * top_fin).clean().fix(),
            feature=f"Front Baffle V1 fin {index}",
        )
        fused = variant.fuse(fin, tol=tolerance)
        variant = _single_solid(
            fused.clean().fix(),
            feature=f"Front Baffle V1 after fin {index}",
        )

    bounds_delta = _bounds_delta(base, variant)
    if max(abs(value) for value in bounds_delta.values()) > 1e-6:
        raise ValueError(f"A fin changed the approved exterior: {bounds_delta}")
    added_volume = variant.volume - base.volume
    expected_added = float(parameters["expected_added_material_volume_mm3"])
    if abs(added_volume - expected_added) > 0.01:
        raise ValueError(
            "The isolated rebuild no longer matches the approved fin volume: "
            f"expected {expected_added:.9f}, got {added_volume:.9f} mm3"
        )

    output_path = job_output_path(OUTPUT_ROOT / OUTPUT_NAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(variant, str(output_path), unit=Unit.MM)
    roundtrip = _single_solid(
        import_step(output_path),
        feature="round-tripped Front Baffle V1 release rebuild",
    )
    diagnostics = {
        "scope": "isolated Front Baffle V1 release rebuild",
        "release_root": str(RELEASE_ROOT),
        "approved_input": str(BASE_BAFFLE_STEP),
        "output": str(OUTPUT_ROOT / OUTPUT_NAME),
        "fin_count": len(parameters["fin_angles_deg"]),
        "fin_angles_deg": parameters["fin_angles_deg"],
        "fin_thickness_mm": parameters["fin_thickness_mm"],
        "added_material_volume_mm3": added_volume,
        "expected_added_material_volume_mm3": expected_added,
        "approved_exterior_bounds_delta_mm": bounds_delta,
        "source_solid_count": len(variant.solids()),
        "source_valid": variant.is_valid,
        "step_roundtrip_solid_count": len(roundtrip.solids()),
        "step_roundtrip_valid": roundtrip.is_valid,
        "final_bounds_mm": _bounds(roundtrip),
        "final_volume_mm3": roundtrip.volume,
    }
    diagnostics_path = job_output_path(OUTPUT_ROOT / DIAGNOSTICS_NAME)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
