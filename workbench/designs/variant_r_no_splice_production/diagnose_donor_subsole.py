"""Locate the refactored donor topology below the validated baffle sole."""

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

from build123d import import_step


ROOT = _CAD_SAFETY_ROOT
CANDIDATE = ROOT / "build/workbench/variant_r_no_splice_production/candidate"
DONOR = CANDIDATE / "continuous_donor_baffle.step"
OUTPUT = (
    ROOT
    / "build/workbench/variant_r_no_splice_production/"
    "donor-subsole-diagnostic.json"
)
SOLE_Z_MM = -91.495


def _bounds(shape) -> dict:
    bounds = shape.bounding_box()
    return {
        "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def main() -> None:
    donor = import_step(DONOR)
    vertices = sorted(
        (
            [vertex.X, vertex.Y, vertex.Z]
            for vertex in donor.vertices()
            if vertex.Z < SOLE_Z_MM - 1e-6
        ),
        key=lambda point: (point[2], point[1], point[0]),
    )
    faces = []
    for face in donor.faces():
        bounds = face.bounding_box()
        if bounds.min.Z < SOLE_Z_MM - 1e-6:
            center = face.center()
            faces.append(
                {
                    "geom_type": face.geom_type.name,
                    "area_mm2": face.area,
                    "center_mm": [center.X, center.Y, center.Z],
                    "bounds_mm": _bounds(face),
                }
            )
    faces.sort(
        key=lambda record: (
            record["bounds_mm"]["min"][2],
            record["center_mm"][1],
            record["center_mm"][0],
        )
    )
    result = {
        "input": str(DONOR.relative_to(ROOT)),
        "sole_z_mm": SOLE_Z_MM,
        "donor_bounds_mm": _bounds(donor),
        "subsole_vertex_count": len(vertices),
        "lowest_vertices_mm": vertices[:40],
        "subsole_face_count": len(faces),
        "subsole_faces": faces,
        "interpretation_boundary": (
            "This diagnostic locates existing donor topology only; the fit "
            "audit remains authority for preserved visible surfaces."
        ),
    }
    output = job_output_path(OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
