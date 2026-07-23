"""Build and publish the exact-edge Variant R joint without either Z splice."""

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

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from build123d import Compound, GeomType, Unit, import_step
from src.cad_io import export_step


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


SOURCE_BASE_STEP = (
    ROOT
    / "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure/"
    "sand_cube_190x210_single_oval_port_base.step"
)
OUT = ROOT / "build/workbench/variant_r_underside_seam_refinement/candidate"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _shape_volume(shape: Any) -> float:
    if shape is None:
        return 0.0
    return sum(solid.volume for solid in shape.solids())


def _print_contact(shape: Any) -> dict[str, Any]:
    tolerance = 0.01
    bed_z = min(vertex.Z for vertex in shape.vertices())
    contacts = []
    for face in shape.faces():
        bounds = face.bounding_box()
        if (
            face.geom_type == GeomType.PLANE
            and bounds.size.Z <= tolerance
            and abs(bounds.min.Z - bed_z) <= tolerance
            and abs(bounds.max.Z - bed_z) <= tolerance
        ):
            contacts.append(
                {
                    "area_mm2": face.area,
                    "x_span_mm": bounds.size.X,
                    "y_span_mm": bounds.size.Y,
                    "center_mm": [
                        face.center().X,
                        face.center().Y,
                        face.center().Z,
                    ],
                }
            )
    contacts.sort(key=lambda item: item["area_mm2"], reverse=True)
    return {
        "bed_z_mm": bed_z,
        "planar_contact_face_count": len(contacts),
        "total_planar_contact_area_mm2": sum(
            item["area_mm2"] for item in contacts
        ),
        "contacts": contacts,
    }


def _topology(shape: Any) -> dict[str, Any]:
    bounds = shape.bounding_box()
    return {
        "solid_count": len(shape.solids()),
        "valid": shape.is_valid,
        "volume_mm3": shape.volume,
        "face_count": len(shape.faces()),
        "edge_count": len(shape.edges()),
        "vertex_count": len(shape.vertices()),
        "bounds_mm": {
            "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
            "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
            "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
        },
        "print_contact": _print_contact(shape),
    }


def _export_and_round_trip(filename: str, shape: Any) -> dict[str, Any]:
    published = job_output_path(OUT / filename)
    published.parent.mkdir(parents=True, exist_ok=True)
    print(f"exporting {filename}", flush=True)
    # Use the repository wrapper so OCCT receives a shallow object made from
    # the actual solids rather than an algebra/construction tree.
    export_step(shape, published, unit=Unit.MM, write_pcurves=True)
    imported = import_step(published)
    result = {
        "path": str((OUT / filename).relative_to(ROOT)),
        "sha256": _sha256(published),
        "source_solid_count": len(shape.solids()),
        "imported_solid_count": len(imported.solids()),
        "all_imported_solids_valid": all(
            solid.is_valid for solid in imported.solids()
        ),
        "imported_face_count": len(imported.faces()),
        "imported_edge_count": len(imported.edges()),
        "step_write_pcurves": True,
        "repository_safe_stream_export": True,
    }
    if (
        result["source_solid_count"] != result["imported_solid_count"]
        or not result["all_imported_solids_valid"]
    ):
        raise ValueError(f"{filename} failed STEP round trip: {result}")
    return result


def main() -> None:
    if not SOURCE_BASE_STEP.is_file():
        raise FileNotFoundError(SOURCE_BASE_STEP)
    full_base = model._single_solid(
        import_step(SOURCE_BASE_STEP),
        feature="regenerated authoritative full-detail enclosure base",
    )
    print("candidate: authoritative base loaded", flush=True)

    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    original_perimeter = model.single._perimeter_wire
    model.source.GASKET_CLOSED_GAP_MM = model.GASKET_CLOSED_GAP_MM
    model.source.SHOULDER_Y = (
        model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM
    )
    model.single._perimeter_wire = model._hybrid_perimeter_wire
    try:
        candidate = model._AUTHORITATIVE_COMMON_JOINT(full_base)
    finally:
        model.single._perimeter_wire = original_perimeter
        model.source.GASKET_CLOSED_GAP_MM = original_gap
        model.source.SHOULDER_Y = original_shoulder
    print("candidate: exact-edge unspliced joint built", flush=True)

    restored = (
        model.single._perimeter_wire is original_perimeter
        and model.source.GASKET_CLOSED_GAP_MM == original_gap
        and model.source.SHOULDER_Y == original_shoulder
    )
    bucket = candidate["bucket"]
    baffle = candidate["baffle"]
    gasket = candidate["gasket"]
    if (
        len(bucket.solids()) != 1
        or len(baffle.solids()) != 1
        or not bucket.is_valid
        or not baffle.is_valid
    ):
        raise ValueError("Unspliced candidate parts are not single valid solids")
    overlap = _shape_volume(bucket.intersect(baffle))
    if overlap > model.MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(f"Unspliced candidate overlap is {overlap:.6f} mm3")

    outputs = {
        "unspliced_exact_edge_bucket.step": bucket,
        "unspliced_exact_edge_baffle.step": baffle,
        "unspliced_exact_edge_assembly.step": Compound(
            children=[bucket, baffle]
        ),
    }
    round_trip = {
        filename: _export_and_round_trip(filename, shape)
        for filename, shape in outputs.items()
    }
    diagnostics = {
        "scope": "focused exact-edge no-Z-splice candidate",
        "source_base_step": str(SOURCE_BASE_STEP.relative_to(ROOT)),
        "construction": (
            "model._AUTHORITATIVE_COMMON_JOINT with only "
            "model._hybrid_perimeter_wire patched; no -80 mm splice and no "
            "-91.5 mm baffle-to-bucket transfer"
        ),
        "bucket": _topology(bucket),
        "baffle": _topology(baffle),
        "gasket": _topology(gasket),
        "bucket_baffle_overlap_mm3": overlap,
        "gasket_bucket_overlap_mm3": _shape_volume(gasket.intersect(bucket)),
        "gasket_baffle_overlap_mm3": _shape_volume(gasket.intersect(baffle)),
        "ancestor_state_restored": restored,
        "joint_audit": dict(model.previous._JOINT_AUDIT),
        "round_trip": round_trip,
    }
    diagnostics_path = job_output_path(OUT / "diagnostics.json")
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
