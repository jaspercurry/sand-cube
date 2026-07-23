"""Export the revised finned baffle as a bed-oriented PLA 3MF."""

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

from collections import Counter
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from build123d import Mesher, Pos, Rot, Unit, import_step


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure as model  # noqa: E402


OUTPUT_ROOT = Path(
    "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
SOURCE_STEP = ROOT / OUTPUT_ROOT / "centered_captive_nut_baffle_finned_variant.step"
OUTPUT_NAME = "centered_captive_nut_baffle_finned_variant_bambu_pla.3mf"
DIAGNOSTICS_NAME = "baffle_finned_bambu_3mf_diagnostics.json"

LINEAR_DEFLECTION_MM = 0.02
ANGULAR_DEFLECTION_RAD = 0.06
MAX_MESH_VOLUME_ERROR_PERCENT = 2.0

PRINT_PROFILE = {
    "target": "Bambu Lab printer with 0.4 mm nozzle",
    "material": "PLA",
    "layer_height_mm": 0.12,
    "first_layer_height_mm": 0.20,
    "wall_generator": "Arachne",
    "wall_loops": 6,
    "top_shell_layers": 7,
    "bottom_shell_layers": 7,
    "sparse_infill_percent": 0,
    "supports": "off; four permanent conformal fins are modeled into the part",
    "brim_width_mm": 5.0,
    "seam": "place on the rear/inside face where practical",
    "orientation": "gasket and driver-collar service face flat on the bed",
    "notes": [
        "Select the exact Bambu printer, build plate, and loaded PLA in Bambu Studio.",
        "Use 0.08 mm layers only if the extra surface finish justifies the longer print.",
        "Inspect the sliced first layer and overhang preview before sending the print.",
        "Print settings are guidance metadata and are not a machine-locked preset.",
    ],
}


def _bbox(shape) -> dict[str, list[float]]:
    bounds = shape.bounding_box()
    return {
        "min": [bounds.min.X, bounds.min.Y, bounds.min.Z],
        "max": [bounds.max.X, bounds.max.Y, bounds.max.Z],
        "size": [bounds.size.X, bounds.size.Y, bounds.size.Z],
    }


def _mesh_diagnostics(path: Path) -> dict[str, object]:
    with ZipFile(path) as archive:
        names = archive.namelist()
        model_names = [name for name in names if name.lower().endswith(".model")]
        if len(model_names) != 1:
            raise ValueError(f"Expected one 3MF model document, found {model_names}")
        root = ET.fromstring(archive.read(model_names[0]))

    vertices = [
        (
            float(vertex.attrib["x"]),
            float(vertex.attrib["y"]),
            float(vertex.attrib["z"]),
        )
        for vertex in root.findall(".//{*}vertex")
    ]
    triangle_indices = [
        (
            int(triangle.attrib["v1"]),
            int(triangle.attrib["v2"]),
            int(triangle.attrib["v3"]),
        )
        for triangle in root.findall(".//{*}triangle")
    ]
    if not vertices or not triangle_indices:
        raise ValueError("The 3MF contains no printable mesh")

    edge_counts: Counter[tuple[int, int]] = Counter()
    signed_six_volume = 0.0
    degenerate_triangles = 0
    for v1, v2, v3 in triangle_indices:
        if len({v1, v2, v3}) != 3:
            degenerate_triangles += 1
        edge_counts.update(
            (
                tuple(sorted((v1, v2))),
                tuple(sorted((v2, v3))),
                tuple(sorted((v3, v1))),
            )
        )
        a = vertices[v1]
        b = vertices[v2]
        c = vertices[v3]
        signed_six_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )

    mesh_min = [min(point[axis] for point in vertices) for axis in range(3)]
    mesh_max = [max(point[axis] for point in vertices) for axis in range(3)]
    non_manifold_edge_count = sum(count != 2 for count in edge_counts.values())
    return {
        "archive_entries": len(names),
        "model_document": model_names[0],
        "unit": root.attrib.get("unit"),
        "object_count": len(root.findall(".//{*}object")),
        "mesh_object_count": len(root.findall(".//{*}object/{*}mesh")),
        "component_object_count": len(
            root.findall(".//{*}object/{*}components")
        ),
        "build_item_count": len(root.findall(".//{*}item")),
        "vertex_count": len(vertices),
        "triangle_count": len(triangle_indices),
        "degenerate_triangle_count": degenerate_triangles,
        "non_manifold_edge_count": non_manifold_edge_count,
        "watertight_two_triangle_edges": non_manifold_edge_count == 0,
        "bbox_mm": {
            "min": mesh_min,
            "max": mesh_max,
            "size": [mesh_max[i] - mesh_min[i] for i in range(3)],
        },
        "signed_mesh_volume_mm3": signed_six_volume / 6.0,
        "absolute_mesh_volume_mm3": abs(signed_six_volume) / 6.0,
    }


def main() -> None:
    if not SOURCE_STEP.is_file():
        raise FileNotFoundError("Build the revised finned baffle STEP first")

    source = model._single_solid(
        import_step(SOURCE_STEP),
        feature="revised finned baffle for 3MF export",
    )
    # Rotating -90 degrees about X maps the baffle's rear service face to the
    # printer XY plane while making all of the baffle geometry grow in +Z.
    oriented = model._single_solid(
        (Rot(-90.0, 0.0, 0.0) * source).clean().fix(),
        feature="bed-oriented revised finned baffle",
    )
    oriented = model._single_solid(
        (Pos(0.0, 0.0, -oriented.bounding_box().min.Z) * oriented).clean().fix(),
        feature="bed-zeroed revised finned baffle",
    )
    oriented_bounds = _bbox(oriented)
    if abs(oriented_bounds["min"][2]) > 1e-6:
        raise ValueError("The 3MF baffle does not start on Z=0")
    if oriented_bounds["size"][0] > 256.0 or oriented_bounds["size"][1] > 256.0:
        raise ValueError(f"The oriented baffle exceeds a 256 mm bed: {oriented_bounds}")

    output_path = job_output_path(OUTPUT_ROOT / OUTPUT_NAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mesher = Mesher(unit=Unit.MM)
    mesher.add_shape(
        oriented,
        linear_deflection=LINEAR_DEFLECTION_MM,
        angular_deflection=ANGULAR_DEFLECTION_RAD,
        part_number="Finned front baffle - PLA - gasket face down",
    )
    mesher.add_meta_data(
        name_space="sand-cube-baffle",
        name="print_profile",
        value=json.dumps(PRINT_PROFILE, sort_keys=True),
        metadata_type="str",
        must_preserve=False,
    )
    mesher.add_meta_data(
        name_space="sand-cube-baffle",
        name="source_step",
        value=SOURCE_STEP.name,
        metadata_type="str",
        must_preserve=False,
    )
    mesher.write(str(output_path))

    mesh = _mesh_diagnostics(output_path)
    if mesh["unit"] not in ("millimeter", "millimetre"):
        raise ValueError(f"Unexpected 3MF unit: {mesh['unit']}")
    if mesh["mesh_object_count"] != 1 or mesh["build_item_count"] != 1:
        raise ValueError(
            "The 3MF is not one printable mesh/build item: "
            f"mesh_objects={mesh['mesh_object_count']}, "
            f"build_items={mesh['build_item_count']}"
        )
    if mesh["degenerate_triangle_count"] != 0:
        raise ValueError("The 3MF contains degenerate triangles")
    if not mesh["watertight_two_triangle_edges"]:
        raise ValueError("The 3MF mesh is not watertight")
    if abs(mesh["bbox_mm"]["min"][2]) > 1e-5:
        raise ValueError("The 3MF mesh is not seated on the build plate")
    volume_error = abs(mesh["absolute_mesh_volume_mm3"] - source.volume)
    volume_error_percent = 100.0 * volume_error / source.volume
    if volume_error_percent > MAX_MESH_VOLUME_ERROR_PERCENT:
        raise ValueError(
            "The 3MF mesh volume differs by "
            f"{volume_error_percent:.4f}%: source={source.volume:.6f} mm3, "
            f"mesh={mesh['absolute_mesh_volume_mm3']:.6f} mm3, "
            f"signed={mesh['signed_mesh_volume_mm3']:.6f} mm3, "
            f"triangles={mesh['triangle_count']}, "
            f"non_manifold_edges={mesh['non_manifold_edge_count']}"
        )
    mesh_size_error = max(
        abs(mesh["bbox_mm"]["size"][axis] - oriented_bounds["size"][axis])
        for axis in range(3)
    )
    if mesh_size_error > 0.05:
        raise ValueError(f"The 3MF mesh bounds differ by {mesh_size_error:.6f} mm")

    diagnostics = {
        "scope": "Bambu-compatible PLA 3MF for the revised finned baffle",
        "source_step": str(SOURCE_STEP),
        "output_3mf": str(OUTPUT_ROOT / OUTPUT_NAME),
        "orientation": "gasket/collar service face on Z=0; baffle grows in +Z",
        "source_solid_count": len(source.solids()),
        "source_valid": source.is_valid,
        "source_volume_mm3": source.volume,
        "oriented_bbox_mm": oriented_bounds,
        "mesh_linear_deflection_mm": LINEAR_DEFLECTION_MM,
        "mesh_angular_deflection_rad": ANGULAR_DEFLECTION_RAD,
        "mesh_max_bbox_error_mm": mesh_size_error,
        "mesh_volume_error_mm3": volume_error,
        "mesh_volume_error_percent": volume_error_percent,
        "maximum_mesh_volume_error_percent": MAX_MESH_VOLUME_ERROR_PERCENT,
        "mesh": mesh,
        "recommended_print_profile": PRINT_PROFILE,
    }
    diagnostics_path = job_output_path(OUTPUT_ROOT / DIAGNOSTICS_NAME)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
