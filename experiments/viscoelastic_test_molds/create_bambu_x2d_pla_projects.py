"""Package the test molds as ready-to-slice Bambu Studio X2D PLA projects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import struct
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile


HERE = Path(__file__).resolve().parent
OUT = HERE / "build"
TEMPLATE = Path(
    "/Users/jaspercurry/Downloads/"
    "JTS - Print Attempt 3 - PLA Matte Supports PETG Interface v5c.3mf"
)

PLATE_CENTER_X = 128.0
PLATE_CENTER_Y = 128.0
OBJECT_MODEL_PATH = "3D/Objects/object_1.model"

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PNS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", NS)
ET.register_namespace("p", PNS)


@dataclass(frozen=True)
class ProjectSpec:
    key: str
    title: str
    source_stl: Path
    filename: str
    process_profile: str
    layer_height: float
    wall_loops: int
    shell_layers: int
    infill: str
    outer_wall_speed: int
    inner_wall_speed: int
    top_surface_speed: int


PROJECTS = (
    ProjectSpec(
        key="sphere_mold",
        title="25 mm Sphere Mold - PLA - X2D",
        source_stl=OUT / "sphere_mold_two_piece_print_layout.stl",
        filename="25mm_sphere_mold_x2d_pla.3mf",
        process_profile="0.12mm High Quality @BBL X2D",
        layer_height=0.12,
        wall_loops=5,
        shell_layers=6,
        infill="30%",
        outer_wall_speed=60,
        inner_wall_speed=120,
        top_surface_speed=80,
    ),
    ProjectSpec(
        key="coupon_trays",
        title="40 x 12.5 mm Rebound Coupon Trays - PLA - X2D",
        source_stl=OUT / "coupon_tray_two_up_print_layout.stl",
        filename="40x12p5_coupon_trays_x2d_pla.3mf",
        process_profile="0.20mm Standard @BBL X2D",
        layer_height=0.20,
        wall_loops=4,
        shell_layers=5,
        infill="25%",
        outer_wall_speed=100,
        inner_wall_speed=180,
        top_surface_speed=100,
    ),
)


def _uuid(spec: ProjectSpec, seed: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"viscoelastic-test-molds/x2d-pla/{spec.key}/{seed}",
        )
    )


def _read_binary_stl(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path.name} is too small to be a binary STL")
    face_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + face_count * 50:
        raise ValueError(f"{path.name} is not the expected binary STL format")

    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[tuple[float, float, float], int] = {}
    triangles: list[tuple[int, int, int]] = []
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    offset = 84
    for _ in range(face_count):
        offset += 12
        triangle: list[int] = []
        for _vertex in range(3):
            point = tuple(
                round(value, 6)
                for value in struct.unpack_from("<fff", data, offset)
            )
            offset += 12
            index = vertex_index.get(point)
            if index is None:
                index = len(vertices)
                vertex_index[point] = index
                vertices.append(point)
                for axis, value in enumerate(point):
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
            triangle.append(index)
        triangles.append(tuple(triangle))
        offset += 2

    if abs(mins[2]) > 1e-4:
        raise ValueError(f"{path.name} is not positioned on the print bed")
    return {
        "vertices": vertices,
        "triangles": triangles,
        "face_count": face_count,
        "mins": mins,
        "maxs": maxs,
    }


def _translation(mesh: dict[str, object]) -> tuple[float, float]:
    tx = PLATE_CENTER_X - (mesh["mins"][0] + mesh["maxs"][0]) / 2
    ty = PLATE_CENTER_Y - (mesh["mins"][1] + mesh["maxs"][1]) / 2
    return tx, ty


def _object_model(spec: ProjectSpec, mesh: dict[str, object]) -> bytes:
    model = ET.Element(
        f"{{{NS}}}model",
        {
            "unit": "millimeter",
            f"{{{XML_NS}}}lang": "en-US",
            "requiredextensions": "p",
        },
    )
    ET.SubElement(
        model,
        f"{{{NS}}}metadata",
        {"name": "BambuStudio:3mfVersion"},
    ).text = "1"
    resources = ET.SubElement(model, f"{{{NS}}}resources")
    obj = ET.SubElement(
        resources,
        f"{{{NS}}}object",
        {
            "id": "1",
            f"{{{PNS}}}UUID": _uuid(spec, "object-mesh"),
            "type": "model",
        },
    )
    mesh_el = ET.SubElement(obj, f"{{{NS}}}mesh")
    vertices_el = ET.SubElement(mesh_el, f"{{{NS}}}vertices")
    for x, y, z in mesh["vertices"]:
        ET.SubElement(
            vertices_el,
            f"{{{NS}}}vertex",
            {"x": f"{x:.6f}", "y": f"{y:.6f}", "z": f"{z:.6f}"},
        )
    triangles_el = ET.SubElement(mesh_el, f"{{{NS}}}triangles")
    for v1, v2, v3 in mesh["triangles"]:
        ET.SubElement(
            triangles_el,
            f"{{{NS}}}triangle",
            {"v1": str(v1), "v2": str(v2), "v3": str(v3)},
        )
    ET.SubElement(model, f"{{{NS}}}build")
    return ET.tostring(model, encoding="utf-8", xml_declaration=True)


def _root_model(spec: ProjectSpec, mesh: dict[str, object]) -> bytes:
    tx, ty = _translation(mesh)
    model = ET.Element(
        f"{{{NS}}}model",
        {
            "unit": "millimeter",
            f"{{{XML_NS}}}lang": "en-US",
            "requiredextensions": "p",
        },
    )
    description = (
        "PLA-only Bambu Lab X2D 0.4 mm project. Parts are already bed-oriented; "
        "supports and prime tower are disabled. Open in Bambu Studio, confirm the "
        "loaded PLA and build plate, slice, and print."
    )
    for key, value in (
        ("Application", "BambuStudio-02.07.01.57"),
        ("BambuStudio:3mfVersion", "1"),
        ("CreationDate", str(date.today())),
        ("ModificationDate", str(date.today())),
        ("Title", spec.title),
        ("Description", description),
    ):
        ET.SubElement(model, f"{{{NS}}}metadata", {"name": key}).text = value

    resources = ET.SubElement(model, f"{{{NS}}}resources")
    obj = ET.SubElement(
        resources,
        f"{{{NS}}}object",
        {
            "id": "2",
            f"{{{PNS}}}UUID": _uuid(spec, "component-object"),
            "name": spec.title,
            "type": "model",
        },
    )
    components = ET.SubElement(obj, f"{{{NS}}}components")
    ET.SubElement(
        components,
        f"{{{NS}}}component",
        {
            f"{{{PNS}}}path": f"/{OBJECT_MODEL_PATH}",
            "objectid": "1",
            f"{{{PNS}}}UUID": _uuid(spec, "component"),
            "transform": "1 0 0 0 1 0 0 0 1 0 0 0",
        },
    )
    build = ET.SubElement(
        model,
        f"{{{NS}}}build",
        {f"{{{PNS}}}UUID": _uuid(spec, "build")},
    )
    ET.SubElement(
        build,
        f"{{{NS}}}item",
        {
            "objectid": "2",
            f"{{{PNS}}}UUID": _uuid(spec, "build-item"),
            "transform": f"1 0 0 0 1 0 0 0 1 {tx:g} {ty:g} 0",
            "printable": "1",
        },
    )
    return ET.tostring(model, encoding="utf-8", xml_declaration=True)


def _relationships() -> bytes:
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    root = ET.Element("Relationships", {"xmlns": rel_ns})
    ET.SubElement(
        root,
        "Relationship",
        {
            "Target": f"/{OBJECT_MODEL_PATH}",
            "Id": "rel-1",
            "Type": (
                "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
            ),
        },
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _project_settings(spec: ProjectSpec) -> bytes:
    with zipfile.ZipFile(TEMPLATE) as archive:
        settings = json.loads(archive.read("Metadata/project_settings.config"))
    end_gcode = settings.get("machine_end_gcode")
    if isinstance(end_gcode, str):
        settings["machine_end_gcode"] = re.sub(
            (
                r"\n; pull back filament to AMS\n"
                r"M620 S65279 B\n"
                r"; M620\.11 P1 L0 I65279 E-3\n"
                r"T65279\n"
                r"G150\.1 F8000\n"
                r"M621 S65279 B\n\n"
                r"M620 S65535 B\n"
                r"; M620\.11 P1 L0 I65535 E-4\n"
                r"T65535\n"
                r"G150\.1 F8000\n"
                r"M621 S65535 B\n"
            ),
            "\n; pull back filament to AMS\n",
            end_gcode,
        )

    settings.update(
        {
            "default_print_profile": spec.process_profile,
            "print_settings_id": spec.process_profile,
            "printer_settings_id": "Bambu Lab X2D 0.4 nozzle",
            "layer_height": str(spec.layer_height),
            "initial_layer_print_height": "0.2",
            "wall_loops": str(spec.wall_loops),
            "top_shell_layers": str(spec.shell_layers),
            "bottom_shell_layers": str(spec.shell_layers),
            "sparse_infill_density": spec.infill,
            "sparse_infill_pattern": "gyroid",
            "wall_generator": "classic",
            "seam_position": "back",
            "top_surface_pattern": "monotonicline",
            "enable_support": "0",
            "enable_prime_tower": "0",
            "brim_type": "no_brim",
            "brim_width": "0",
            "skirt_loops": "0",
            "outer_wall_speed": [str(spec.outer_wall_speed)] * 4,
            "inner_wall_speed": [str(spec.inner_wall_speed)] * 4,
            "sparse_infill_speed": ["150", "150", "120", "120"],
            "top_surface_speed": [str(spec.top_surface_speed)] * 4,
            "initial_layer_line_width": "0.55",
            "initial_layer_speed": ["30", "30", "30", "30"],
            "initial_layer_infill_speed": ["60", "60", "60", "60"],
            "eng_plate_temp": ["55"],
            "eng_plate_temp_initial_layer": ["55"],
            "hot_plate_temp": ["55"],
            "hot_plate_temp_initial_layer": ["55"],
            "textured_plate_temp": ["55"],
            "textured_plate_temp_initial_layer": ["55"],
            "cool_plate_temp": ["35"],
            "cool_plate_temp_initial_layer": ["35"],
            "nozzle_temperature": ["220", "220", "220", "220"],
            "nozzle_temperature_initial_layer": ["220", "220", "220", "220"],
            "filament_settings_id": [
                "Bambu PLA Basic @BBL X2D 0.4 nozzle"
            ],
            "filament_type": ["PLA"],
            "filament_ids": ["GFA00"],
            "default_filament_colour": ["#3b82b5"],
            "filament_colour": ["#3b82b5"],
            "filament_colour_type": ["2"],
            "filament_multi_colour": ["#3b82b5"],
            "filament_is_support": ["0"],
            "filament_soluble": ["0"],
            "filament_density": ["1.26"],
            "filament_flow_ratio": ["0.98", "0.98", "0.98", "0.98"],
            "filament_max_volumetric_speed": ["21", "40", "21", "30"],
            "filament_adhesiveness_category": ["100"],
            "filament_map": ["1"],
            "filament_map_mode": "Manual",
            "filament_nozzle_map": ["0"],
            "filament_volume_map": ["0"],
            "extruder_nozzle_count": ["1"],
            "extruder_nozzle_volume_type": ["Standard"],
            "physical_extruder_map": ["1", "0"],
            "single_extruder_multi_material": "0",
        }
    )
    return json.dumps(settings, indent=4).encode()


def _model_settings(spec: ProjectSpec, mesh: dict[str, object]) -> bytes:
    root = ET.Element("config")
    obj = ET.SubElement(root, "object", {"id": "2"})
    ET.SubElement(
        obj,
        "metadata",
        {"key": "name", "value": spec.filename},
    )
    ET.SubElement(obj, "metadata", {"key": "extruder", "value": "1"})
    ET.SubElement(
        obj,
        "metadata",
        {"face_count": str(mesh["face_count"])},
    )
    part = ET.SubElement(obj, "part", {"id": "1", "subtype": "normal_part"})
    for key, value in (
        ("name", spec.source_stl.name),
        ("extruder", "1"),
        ("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"),
        ("source_file", spec.filename),
        ("source_object_id", "0"),
        ("source_volume_id", "0"),
        ("source_offset_x", "0"),
        ("source_offset_y", "0"),
        ("source_offset_z", "0"),
    ):
        ET.SubElement(part, "metadata", {"key": key, "value": value})
    ET.SubElement(
        part,
        "mesh_stat",
        {
            "face_count": str(mesh["face_count"]),
            "edges_fixed": "0",
            "degenerate_facets": "0",
            "facets_removed": "0",
            "facets_reversed": "0",
            "backwards_edges": "0",
        },
    )

    plate = ET.SubElement(root, "plate")
    for key, value in (
        ("plater_id", "1"),
        ("plater_name", ""),
        ("locked", "false"),
        ("filament_map_mode", "Manual"),
        ("filament_maps", "1"),
        ("filament_volume_maps", "0"),
    ):
        ET.SubElement(plate, "metadata", {"key": key, "value": value})
    instance = ET.SubElement(plate, "model_instance")
    ET.SubElement(instance, "metadata", {"key": "object_id", "value": "2"})
    ET.SubElement(instance, "metadata", {"key": "instance_id", "value": "0"})
    ET.SubElement(instance, "metadata", {"key": "identify_id", "value": "82"})

    assemble = ET.SubElement(root, "assemble")
    ET.SubElement(
        assemble,
        "assemble_item",
        {
            "object_id": "2",
            "instance_id": "0",
            "transform": "1 0 0 0 1 0 0 0 1 0 0 0",
            "offset": "0 0 0",
        },
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _plate_json(spec: ProjectSpec, mesh: dict[str, object]) -> bytes:
    tx, ty = _translation(mesh)
    bbox = [
        tx + mesh["mins"][0],
        ty + mesh["mins"][1],
        tx + mesh["maxs"][0],
        ty + mesh["maxs"][1],
    ]
    return json.dumps(
        {
            "bbox_all": bbox,
            "bbox_objects": [
                {
                    "area": (
                        (mesh["maxs"][0] - mesh["mins"][0])
                        * (mesh["maxs"][1] - mesh["mins"][1])
                    ),
                    "bbox": bbox,
                    "id": 82,
                    "layer_height": spec.layer_height,
                    "name": spec.title,
                }
            ],
            "bed_type": "textured_plate",
            "filament_colors": ["#3b82b5"],
            "filament_ids": ["PLA Basic"],
            "first_extruder": 0,
            "is_seq_print": False,
            "nozzle_diameter": 0.4,
            "version": 2,
        },
        indent=4,
    ).encode()


def _slice_info() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="02.07.01.57"/>
  </header>
</config>
"""


def _cut_information() -> bytes:
    return b"""<?xml version="1.0" encoding="utf-8"?>
<objects>
 <object id="2">
  <cut_id id="0" check_sum="1" connectors_cnt="0"/>
 </object>
</objects>
"""


def _filament_sequence() -> bytes:
    return b'{"plate_1":{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}'


def _package_project(spec: ProjectSpec) -> dict[str, object]:
    mesh = _read_binary_stl(spec.source_stl)
    path = OUT / spec.filename
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
    with zipfile.ZipFile(TEMPLATE) as template, zipfile.ZipFile(
        path,
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
        output.writestr("3D/3dmodel.model", _root_model(spec, mesh))
        output.writestr(OBJECT_MODEL_PATH, _object_model(spec, mesh))
        output.writestr("3D/_rels/3dmodel.model.rels", _relationships())
        output.writestr(
            "Metadata/project_settings.config",
            _project_settings(spec),
        )
        output.writestr(
            "Metadata/model_settings.config",
            _model_settings(spec, mesh),
        )
        output.writestr("Metadata/plate_1.json", _plate_json(spec, mesh))
        output.writestr("Metadata/cut_information.xml", _cut_information())
        output.writestr("Metadata/slice_info.config", _slice_info())
        output.writestr("Metadata/filament_sequence.json", _filament_sequence())

    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"Corrupt member in {path.name}: {bad_member}")

    return {
        "project": str(path.resolve()),
        "source_stl": str(spec.source_stl.resolve()),
        "process_profile": spec.process_profile,
        "printer": "Bambu Lab X2D 0.4 nozzle",
        "filament": "Bambu PLA Basic",
        "supports": False,
        "prime_tower": False,
        "layer_height_mm": spec.layer_height,
        "wall_loops": spec.wall_loops,
        "top_bottom_shell_layers": spec.shell_layers,
        "infill": f"{spec.infill} gyroid",
        "bbox_mm": {
            "x": round(mesh["maxs"][0] - mesh["mins"][0], 3),
            "y": round(mesh["maxs"][1] - mesh["mins"][1], 3),
            "z": round(mesh["maxs"][2] - mesh["mins"][2], 3),
        },
        "face_count": mesh["face_count"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing Bambu Studio template: {TEMPLATE}")
    for spec in PROJECTS:
        if not spec.source_stl.exists():
            raise FileNotFoundError(f"Missing generated STL: {spec.source_stl}")

    project_diagnostics = [_package_project(spec) for spec in PROJECTS]
    print_package = OUT / "viscoelastic_test_molds_x2d_pla_print_package.zip"
    with zipfile.ZipFile(
        print_package,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for spec in PROJECTS:
            archive.write(
                OUT / spec.filename,
                arcname=f"Bambu_X2D_PLA/{spec.filename}",
            )
        archive.write(
            OUT / "sphere_mold_two_piece_print_layout.stl",
            arcname="STL/sphere_mold_two_piece_print_layout.stl",
        )
        archive.write(
            OUT / "coupon_tray_two_up_print_layout.stl",
            arcname="STL/coupon_tray_two_up_print_layout.stl",
        )
        archive.write(HERE / "README.md", arcname="README.md")
    with zipfile.ZipFile(print_package) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"Corrupt print-package member: {bad_member}")

    diagnostics = {
        "projects": project_diagnostics,
        "print_package": str(print_package.resolve()),
    }
    diagnostics_path = OUT / "bambu_x2d_pla_projects_diagnostics.json"
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
