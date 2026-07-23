"""Measure nearby sole planes on the published exact-edge donor baffle."""

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
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
from pathlib import Path

from build123d import Align, Box, GeomType, Pos, import_step


ROOT = Path(__file__).resolve().parents[3]
INPUT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/candidate/"
    "unspliced_exact_edge_baffle.step"
)
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/"
    "sole_plane_sweep.json"
)
PLANES_MM = (
    -91.49,
    -91.495,
    -91.5,
    -91.505,
    -91.51,
    -91.52,
    -91.55,
    -91.60,
)


def _measure(shape, plane_z: float) -> dict:
    bounds = shape.bounding_box()
    clip = Pos(
        (bounds.min.X + bounds.max.X) / 2.0,
        (bounds.min.Y + bounds.max.Y) / 2.0,
        (plane_z + bounds.max.Z + 1.0) / 2.0,
    ) * Box(
        bounds.size.X + 2.0,
        bounds.size.Y + 2.0,
        bounds.max.Z + 1.0 - plane_z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    trimmed = (shape & clip).clean().fix()
    solids = [solid for solid in trimmed.solids() if solid.volume > 1e-6]
    if len(solids) != 1 or not solids[0].is_valid:
        return {
            "plane_z_mm": plane_z,
            "valid_single_solid": False,
            "solid_count": len(solids),
        }
    solid = solids[0]
    bed_z = min(vertex.Z for vertex in solid.vertices())
    contacts = []
    for face in solid.faces():
        face_bounds = face.bounding_box()
        if (
            face.geom_type == GeomType.PLANE
            and face_bounds.size.Z <= 0.01
            and abs(face_bounds.min.Z - bed_z) <= 0.01
            and abs(face_bounds.max.Z - bed_z) <= 0.01
        ):
            contacts.append(
                {
                    "area_mm2": face.area,
                    "x_span_mm": face_bounds.size.X,
                    "y_span_mm": face_bounds.size.Y,
                }
            )
    contacts.sort(key=lambda item: item["area_mm2"], reverse=True)
    return {
        "plane_z_mm": plane_z,
        "valid_single_solid": True,
        "bed_z_mm": bed_z,
        "removed_volume_mm3": shape.volume - solid.volume,
        "contact_face_count": len(contacts),
        "largest_contact": contacts[0] if contacts else None,
    }


def main() -> None:
    if not INPUT.is_file():
        raise FileNotFoundError(INPUT)
    baffle = import_step(INPUT)
    results = [_measure(baffle, plane_z) for plane_z in PLANES_MM]
    output = {
        "input": str(INPUT.relative_to(ROOT)),
        "input_min_z_mm": min(vertex.Z for vertex in baffle.vertices()),
        "required_min_width_mm": 187.020979,
        "required_min_area_mm2": 2277.950023,
        "results": results,
    }
    path = job_output_path(OUTPUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
