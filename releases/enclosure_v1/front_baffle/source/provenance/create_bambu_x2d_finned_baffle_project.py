"""Package the finned baffle as a native Bambu Studio X2D PLA project."""

from __future__ import annotations


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
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import create_bambu_oss_horn_mount_project as bambu_template  # noqa: E402


OUTPUT_ROOT = Path(
    "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
SOURCE_3MF = (
    ROOT
    / OUTPUT_ROOT
    / "centered_captive_nut_baffle_finned_variant_bambu_pla.3mf"
)
PROJECT_NAME = (
    "centered_captive_nut_baffle_finned_variant_x2d_pla_matte_project.3mf"
)
DIAGNOSTICS_NAME = "baffle_finned_x2d_pla_matte_project_diagnostics.json"
TITLE = "Finned Front Baffle - X2D - PLA Matte"
OBJECT_NAME = "Finned Front Baffle - gasket face down"


def _mesh_from_generic_3mf(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        model_names = [
            name for name in archive.namelist() if name.lower().endswith(".model")
        ]
        if len(model_names) != 1:
            raise ValueError(f"Expected one generic 3MF model, found {model_names}")
        root = ET.fromstring(archive.read(model_names[0]))
    mesh_objects = [
        obj for obj in root.findall(".//{*}object") if obj.find("{*}mesh") is not None
    ]
    if len(mesh_objects) != 1:
        raise ValueError(f"Expected one mesh object, found {len(mesh_objects)}")
    mesh_element = mesh_objects[0].find("{*}mesh")
    vertices = [
        (
            float(vertex.attrib["x"]),
            float(vertex.attrib["y"]),
            float(vertex.attrib["z"]),
        )
        for vertex in mesh_element.findall("./{*}vertices/{*}vertex")
    ]
    indexed_triangles = [
        (
            int(triangle.attrib["v1"]),
            int(triangle.attrib["v2"]),
            int(triangle.attrib["v3"]),
        )
        for triangle in mesh_element.findall("./{*}triangles/{*}triangle")
    ]
    if not vertices or not indexed_triangles:
        raise ValueError("The generic 3MF contains no printable mesh")
    mins = [min(point[axis] for point in vertices) for axis in range(3)]
    maxs = [max(point[axis] for point in vertices) for axis in range(3)]
    bed_contact_area = 0.0
    bed_contact_triangles = 0
    for indices in indexed_triangles:
        triangle = [vertices[index] for index in indices]
        if not all(abs(point[2]) <= 1e-5 for point in triangle):
            continue
        a = tuple(triangle[1][axis] - triangle[0][axis] for axis in range(3))
        b = tuple(triangle[2][axis] - triangle[0][axis] for axis in range(3))
        cross = (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )
        bed_contact_area += 0.5 * math.sqrt(sum(value * value for value in cross))
        bed_contact_triangles += 1
    return {
        "vertices": vertices,
        "indexed_triangles": indexed_triangles,
        "triangles": [
            [vertices[index] for index in triangle]
            for triangle in indexed_triangles
        ],
        "mins": mins,
        "maxs": maxs,
        "face_count": len(indexed_triangles),
        "bed_contact_area": bed_contact_area,
        "bed_contact_triangles": bed_contact_triangles,
    }


def _root_model(mesh: dict[str, object]) -> bytes:
    root = ET.fromstring(bambu_template._root_model(mesh))
    metadata = {
        item.attrib.get("name"): item for item in root.findall("./{*}metadata")
    }
    metadata["Title"].text = TITLE
    metadata["Description"].text = (
        "Revised four-fin speaker front baffle, gasket and driver-collar service "
        "face on the X2D build plate. Native X2D 0.4 mm PLA Matte project; "
        "0.12 mm layers, six walls, seven top/bottom shells, zero sparse infill, "
        "modeled permanent fins, and supports disabled."
    )
    objects = root.findall("./{*}resources/{*}object")
    if len(objects) != 1:
        raise ValueError("Unexpected Bambu root object structure")
    objects[0].set("name", OBJECT_NAME)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _project_settings() -> bytes:
    settings = json.loads(bambu_template._project_settings())
    settings.update(
        {
            "default_print_profile": "0.12mm High Quality @BBL X2D",
            "print_settings_id": "0.12mm High Quality @BBL X2D",
            "printer_settings_id": "Bambu Lab X2D 0.4 nozzle",
            "layer_height": "0.12",
            "initial_layer_print_height": "0.2",
            "wall_generator": "arachne",
            "wall_loops": "6",
            "top_shell_layers": "7",
            "bottom_shell_layers": "7",
            "sparse_infill_density": "0%",
            "sparse_infill_pattern": "gyroid",
            "seam_position": "back",
            "top_surface_pattern": "monotonicline",
            "enable_support": "0",
            "enable_prime_tower": "0",
            "brim_type": "outer_only",
            "brim_width": "5",
            "brim_object_gap": "0.1",
            "skirt_loops": "0",
            "outer_wall_speed": ["60", "60", "60", "60"],
            "inner_wall_speed": ["120", "120", "120", "120"],
            "sparse_infill_speed": ["120", "120", "120", "120"],
            "top_surface_speed": ["80", "80", "80", "80"],
            "filament_settings_id": [
                "Bambu PLA Matte @BBL X2D 0.4 nozzle"
            ],
            "filament_type": ["PLA"],
            "filament_density": ["1.32"],
            "filament_flow_ratio": ["1.006", "0.98", "0.98", "0.98"],
            "filament_max_volumetric_speed": ["22", "40", "22", "25"],
            "textured_plate_temp": ["55"],
            "textured_plate_temp_initial_layer": ["55"],
            "nozzle_temperature": ["220", "220", "220", "220"],
            "nozzle_temperature_initial_layer": ["220", "220", "220", "220"],
        }
    )
    return json.dumps(settings, indent=4).encode()


def _model_settings(mesh: dict[str, object]) -> bytes:
    root = ET.fromstring(bambu_template._model_settings(mesh))
    object_element = root.find("./object")
    object_name = object_element.find("./metadata[@key='name']")
    object_name.set("value", PROJECT_NAME)
    part = object_element.find("./part")
    part.find("./metadata[@key='name']").set("value", OBJECT_NAME)
    part.find("./metadata[@key='source_file']").set("value", PROJECT_NAME)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _plate_json(mesh: dict[str, object]) -> bytes:
    plate = json.loads(bambu_template._plate_json(mesh))
    plate["bbox_objects"][0]["layer_height"] = 0.12
    plate["bbox_objects"][0]["name"] = OBJECT_NAME
    plate["filament_ids"] = ["PLA Matte"]
    plate["bed_type"] = "textured_plate"
    plate["nozzle_diameter"] = 0.4
    return json.dumps(plate, indent=4).encode()


def _validate_project(path: Path, mesh: dict[str, object]) -> dict[str, object]:
    required = {
        "3D/3dmodel.model",
        bambu_template.OBJECT_MODEL_PATH,
        "3D/_rels/3dmodel.model.rels",
        "Metadata/project_settings.config",
        "Metadata/model_settings.config",
        "Metadata/plate_1.json",
        "Metadata/slice_info.config",
    }
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"Native Bambu project is missing {missing}")
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
        project_settings = json.loads(
            archive.read("Metadata/project_settings.config")
        )
        plate = json.loads(archive.read("Metadata/plate_1.json"))
        object_root = ET.fromstring(
            archive.read(bambu_template.OBJECT_MODEL_PATH)
        )
    markers = {
        item.attrib.get("name"): item.text
        for item in root.findall("./{*}metadata")
    }
    object_markers = {
        item.attrib.get("name"): item.text
        for item in object_root.findall("./{*}metadata")
    }
    if markers.get("BambuStudio:3mfVersion") != "1":
        raise ValueError("Root BambuStudio 3MF marker is missing")
    if object_markers.get("BambuStudio:3mfVersion") != "1":
        raise ValueError("Object BambuStudio 3MF marker is missing")
    expected_settings = {
        "printer_settings_id": "Bambu Lab X2D 0.4 nozzle",
        "print_settings_id": "0.12mm High Quality @BBL X2D",
        "layer_height": "0.12",
        "wall_loops": "6",
        "top_shell_layers": "7",
        "bottom_shell_layers": "7",
        "sparse_infill_density": "0%",
        "enable_support": "0",
        "brim_width": "5",
    }
    mismatches = {
        key: {"expected": value, "actual": project_settings.get(key)}
        for key, value in expected_settings.items()
        if project_settings.get(key) != value
    }
    if mismatches:
        raise ValueError(f"Bambu project setting mismatch: {mismatches}")
    if project_settings.get("filament_settings_id") != [
        "Bambu PLA Matte @BBL X2D 0.4 nozzle"
    ]:
        raise ValueError("The Bambu PLA Matte filament profile is missing")
    if plate.get("bed_type") != "textured_plate":
        raise ValueError("The X2D textured build plate was not retained")
    size = [mesh["maxs"][axis] - mesh["mins"][axis] for axis in range(3)]
    if size[0] > 256.0 or size[1] > 256.0 or abs(mesh["mins"][2]) > 1e-5:
        raise ValueError(f"The baffle is not safely bed-oriented: {size}")
    return {
        "archive_entry_count": len(names),
        "required_native_entries_present": True,
        "root_bambu_3mf_version": markers["BambuStudio:3mfVersion"],
        "object_bambu_3mf_version": object_markers["BambuStudio:3mfVersion"],
        "project_settings_verified": expected_settings,
        "filament_settings_id": project_settings["filament_settings_id"],
        "bed_type": plate["bed_type"],
        "mesh_face_count": mesh["face_count"],
        "bbox_size_mm": size,
        "bed_contact_area_mm2": mesh["bed_contact_area"],
        "bed_contact_triangle_count": mesh["bed_contact_triangles"],
    }


def main() -> None:
    if not SOURCE_3MF.is_file():
        raise FileNotFoundError(f"Missing generic finned-baffle 3MF: {SOURCE_3MF}")
    if not bambu_template.TEMPLATE.is_file():
        raise FileNotFoundError(
            f"Missing native X2D Bambu Studio template: {bambu_template.TEMPLATE}"
        )
    mesh = _mesh_from_generic_3mf(SOURCE_3MF)
    output_path = job_output_path(OUTPUT_ROOT / PROJECT_NAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    skip = {
        "3D/3dmodel.model",
        "3D/_rels/3dmodel.model.rels",
        "Metadata/project_settings.config",
        "Metadata/model_settings.config",
        "Metadata/plate_1.json",
        "Metadata/layer_heights_profile.txt",
        "Metadata/cut_information.xml",
        "Metadata/slice_info.config",
        "Metadata/filament_sequence.json",
    }
    with zipfile.ZipFile(bambu_template.TEMPLATE) as template, zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as output:
        for info in template.infolist():
            if info.filename in skip:
                continue
            if info.filename.startswith("3D/Objects/"):
                continue
            if info.filename.startswith("Metadata/") and info.filename.endswith(
                ".png"
            ):
                continue
            output.writestr(info, template.read(info.filename))
        output.writestr("3D/3dmodel.model", _root_model(mesh))
        output.writestr(
            bambu_template.OBJECT_MODEL_PATH,
            bambu_template._object_model(mesh),
        )
        output.writestr(
            "3D/_rels/3dmodel.model.rels",
            bambu_template._relationships(),
        )
        output.writestr("Metadata/project_settings.config", _project_settings())
        output.writestr("Metadata/model_settings.config", _model_settings(mesh))
        output.writestr("Metadata/plate_1.json", _plate_json(mesh))
        output.writestr(
            "Metadata/cut_information.xml",
            bambu_template._cut_information(),
        )
        output.writestr(
            "Metadata/slice_info.config",
            bambu_template._slice_info(),
        )
        output.writestr(
            "Metadata/filament_sequence.json",
            bambu_template._filament_sequence(),
        )

    validation = _validate_project(output_path, mesh)
    diagnostics = {
        "scope": "native Bambu Studio X2D finned-baffle project",
        "source_generic_3mf": str(SOURCE_3MF),
        "native_template": str(bambu_template.TEMPLATE),
        "output_project": str(OUTPUT_ROOT / PROJECT_NAME),
        "bambu_studio_version": "02.07.01.57",
        "orientation": "gasket/collar service face on the build plate",
        "settings": {
            "printer": "Bambu Lab X2D 0.4 nozzle",
            "filament": "Bambu PLA Matte @BBL X2D 0.4 nozzle",
            "process": "0.12mm High Quality @BBL X2D",
            "layer_height_mm": 0.12,
            "first_layer_height_mm": 0.2,
            "wall_loops": 6,
            "top_bottom_shell_layers": 7,
            "sparse_infill_percent": 0,
            "supports": False,
            "brim": "5 mm outer brim",
            "plate": "textured plate",
        },
        "validation": validation,
    }
    diagnostics_path = job_output_path(OUTPUT_ROOT / DIAGNOSTICS_NAME)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
