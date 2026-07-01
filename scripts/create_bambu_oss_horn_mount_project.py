"""Package the shoulder-relieved OSS horn mount as a PLA-only Bambu project."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import struct
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "experiments" / "horn_mount_fit"
SOURCE_STL = OUT_DIR / "OSS V1.0 - Horn Mount - 4mm Shoulder Relief.stl"
BED_STL = OUT_DIR / "OSS V1.0 - Horn Mount - 4mm Shoulder Relief - bed oriented.stl"
PROJECT_FILENAME = "oss_horn_mount_4mm_shoulder_relief_x2d_pla_project.3mf"
OUT = OUT_DIR / PROJECT_FILENAME
DIAGNOSTICS = (
    OUT_DIR / "oss_horn_mount_4mm_shoulder_relief_x2d_pla_project_diagnostics.json"
)
TEMPLATE = Path(
    "/Users/jaspercurry/Downloads/"
    "JTS - Print Attempt 3 - PLA Matte Supports PETG Interface v5c.3mf"
)

# Original mount coordinates are X = width, Y = fore/aft thickness, Z = height.
# Put the horn-facing Y=max face on the print bed so the holes print vertically
# through the part and the broadest face provides bed adhesion.
ORIGINAL_FRONT_Y = 134.0
ORIGINAL_MIN_Z = 110.0
PLATE_CENTER_X = 128.0
PLATE_CENTER_Y = 128.0
OBJECT_MODEL_PATH = "3D/Objects/object_1.model"

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PNS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BNS = "http://schemas.bambulab.com/package/2021"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", NS)
ET.register_namespace("p", PNS)
ET.register_namespace("BambuStudio", BNS)


def _uuid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"oss-horn-mount-4mm/{seed}"))


def _normal(tri: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    ax = [tri[1][index] - tri[0][index] for index in range(3)]
    bx = [tri[2][index] - tri[0][index] for index in range(3)]
    cross = (
        ax[1] * bx[2] - ax[2] * bx[1],
        ax[2] * bx[0] - ax[0] * bx[2],
        ax[0] * bx[1] - ax[1] * bx[0],
    )
    length = sum(value * value for value in cross) ** 0.5
    if length < 1e-12:
        return (0.0, 0.0, 0.0)
    return tuple(value / length for value in cross)


def _read_and_orient_stl(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")
    tri_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + tri_count * 50
    if expected != len(data):
        raise ValueError(f"{path} does not look like a binary STL")

    triangles: list[list[tuple[float, float, float]]] = []
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[tuple[float, float, float], int] = {}
    indexed_triangles: list[tuple[int, int, int]] = []
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    bed_contact_area = 0.0
    bed_contact_triangles = 0

    offset = 84
    for _index in range(tri_count):
        offset += 12
        tri: list[tuple[float, float, float]] = []
        indexed: list[int] = []
        for _vertex in range(3):
            x, y, z = struct.unpack_from("<fff", data, offset)
            offset += 12
            point = (
                round(x, 6),
                round(z - ORIGINAL_MIN_Z, 6),
                round(ORIGINAL_FRONT_Y - y, 6),
            )
            tri.append(point)
            existing = vertex_index.get(point)
            if existing is None:
                existing = len(vertices)
                vertex_index[point] = existing
                vertices.append(point)
                for axis, value in enumerate(point):
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
            indexed.append(existing)
        triangles.append(tri)
        indexed_triangles.append(tuple(indexed))
        if all(abs(point[2]) < 1e-5 for point in tri):
            ax = [tri[1][index] - tri[0][index] for index in range(3)]
            bx = [tri[2][index] - tri[0][index] for index in range(3)]
            cross = (
                ax[1] * bx[2] - ax[2] * bx[1],
                ax[2] * bx[0] - ax[0] * bx[2],
                ax[0] * bx[1] - ax[1] * bx[0],
            )
            bed_contact_area += 0.5 * sum(value * value for value in cross) ** 0.5
            bed_contact_triangles += 1
        offset += 2

    return {
        "triangles": triangles,
        "vertices": vertices,
        "indexed_triangles": indexed_triangles,
        "mins": mins,
        "maxs": maxs,
        "face_count": tri_count,
        "bed_contact_area": bed_contact_area,
        "bed_contact_triangles": bed_contact_triangles,
    }


def _write_bed_stl(path: Path, mesh: dict[str, object]) -> None:
    triangles = mesh["triangles"]
    with path.open("wb") as output:
        output.write(b"OSS horn mount 4mm shoulder relief bed oriented".ljust(80, b" "))
        output.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            output.write(struct.pack("<fff", *_normal(tri)))
            for vertex in tri:
                output.write(struct.pack("<fff", *vertex))
            output.write(struct.pack("<H", 0))


def _object_model(mesh: dict[str, object]) -> bytes:
    model = ET.Element(
        f"{{{NS}}}model",
        {
            "unit": "millimeter",
            f"{{{XML_NS}}}lang": "en-US",
            "requiredextensions": "p",
        },
    )
    ET.SubElement(model, f"{{{NS}}}metadata", {"name": "BambuStudio:3mfVersion"}).text = "1"
    resources = ET.SubElement(model, f"{{{NS}}}resources")
    obj = ET.SubElement(
        resources,
        f"{{{NS}}}object",
        {
            "id": "1",
            f"{{{PNS}}}UUID": _uuid("object-mesh"),
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
    for v1, v2, v3 in mesh["indexed_triangles"]:
        ET.SubElement(
            triangles_el,
            f"{{{NS}}}triangle",
            {"v1": str(v1), "v2": str(v2), "v3": str(v3)},
        )
    ET.SubElement(model, f"{{{NS}}}build")
    return ET.tostring(model, encoding="utf-8", xml_declaration=True)


def _root_model(mesh: dict[str, object]) -> bytes:
    min_x, min_y, _min_z = mesh["mins"]
    max_x, max_y, _max_z = mesh["maxs"]
    tx = PLATE_CENTER_X - (min_x + max_x) / 2
    ty = PLATE_CENTER_Y - (min_y + max_y) / 2

    model = ET.Element(
        f"{{{NS}}}model",
        {
            "unit": "millimeter",
            f"{{{XML_NS}}}lang": "en-US",
            "requiredextensions": "p",
        },
    )
    for key, value in [
        ("Application", "BambuStudio-02.07.01.57"),
        ("BambuStudio:3mfVersion", "1"),
        ("CreationDate", str(date.today())),
        ("ModificationDate", str(date.today())),
        ("Title", "OSS V1.0 Horn Mount - 4 mm Shoulder Relief - PLA"),
        (
            "Description",
            "OSS horn mount with a deliberate 4 mm shoulder relief for "
            "the printed horn spigot. "
            "Bed-oriented with the horn-facing side down; PLA-only X2D "
            "project, no supports, no prime tower.",
        ),
    ]:
        ET.SubElement(model, f"{{{NS}}}metadata", {"name": key}).text = value

    resources = ET.SubElement(model, f"{{{NS}}}resources")
    obj = ET.SubElement(
        resources,
        f"{{{NS}}}object",
        {
            "id": "2",
            f"{{{PNS}}}UUID": _uuid("component-object"),
            "name": "OSS V1.0 Horn Mount 4mm Shoulder PLA",
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
            f"{{{PNS}}}UUID": _uuid("component"),
            "transform": "1 0 0 0 1 0 0 0 1 0 0 0",
        },
    )
    build = ET.SubElement(
        model,
        f"{{{NS}}}build",
        {f"{{{PNS}}}UUID": _uuid("build")},
    )
    ET.SubElement(
        build,
        f"{{{NS}}}item",
        {
            "objectid": "2",
            f"{{{PNS}}}UUID": _uuid("build-item"),
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
            "Type": "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel",
        },
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _project_settings() -> bytes:
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
            "default_print_profile": "0.20mm OSS Horn Mount PLA @BBL X2D",
            "print_settings_id": "0.20mm Standard @BBL X2D",
            "printer_settings_id": "Bambu Lab X2D 0.4 nozzle",
            "layer_height": "0.2",
            "initial_layer_print_height": "0.2",
            "wall_loops": "4",
            "top_shell_layers": "5",
            "bottom_shell_layers": "5",
            "sparse_infill_density": "25%",
            "sparse_infill_pattern": "gyroid",
            "enable_support": "0",
            "enable_prime_tower": "0",
            "brim_type": "no_brim",
            "brim_width": "0",
            "brim_object_gap": "0.1",
            "initial_layer_line_width": "0.55",
            "initial_layer_speed": ["30", "30", "30", "30"],
            "initial_layer_infill_speed": ["60", "60", "60", "60"],
            "outer_wall_speed": ["120", "120", "50", "50"],
            "inner_wall_speed": ["200", "200", "150", "150"],
            "sparse_infill_speed": ["180", "180", "150", "150"],
            "top_surface_speed": ["120", "120", "80", "80"],
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
            "filament_settings_id": ["Bambu PLA Matte @BBL X2D 0.4 nozzle"],
            "filament_type": ["PLA"],
            "filament_ids": ["GFA00"],
            "default_filament_colour": ["#1d1d1d"],
            "filament_colour": ["#1d1d1d"],
            "filament_colour_type": ["2"],
            "filament_multi_colour": ["#1d1d1d"],
            "filament_is_support": ["0"],
            "filament_soluble": ["0"],
            "filament_density": ["1.32"],
            "filament_flow_ratio": ["1.006", "0.98", "0.98", "0.98"],
            "filament_max_volumetric_speed": ["22", "40", "22", "25"],
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


def _model_settings(mesh: dict[str, object]) -> bytes:
    root = ET.Element("config")
    obj = ET.SubElement(root, "object", {"id": "2"})
    ET.SubElement(
        obj,
        "metadata",
        {"key": "name", "value": "OSS V1.0 Horn Mount 4mm Shoulder PLA.3mf"},
    )
    ET.SubElement(obj, "metadata", {"key": "extruder", "value": "1"})
    ET.SubElement(obj, "metadata", {"face_count": str(mesh["face_count"])})
    part = ET.SubElement(obj, "part", {"id": "1", "subtype": "normal_part"})
    for key, value in [
        ("name", "OSS V1.0 Horn Mount - 4mm Shoulder Relief.stl"),
        ("extruder", "1"),
        ("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"),
        ("source_file", PROJECT_FILENAME),
        ("source_object_id", "0"),
        ("source_volume_id", "0"),
        ("source_offset_x", "0"),
        ("source_offset_y", "0"),
        ("source_offset_z", "0"),
    ]:
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
    for key, value in [
        ("plater_id", "1"),
        ("plater_name", ""),
        ("locked", "false"),
        ("filament_map_mode", "Manual"),
        ("filament_maps", "1"),
        ("filament_volume_maps", "0"),
    ]:
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


def _plate_json(mesh: dict[str, object]) -> bytes:
    min_x, min_y, _min_z = mesh["mins"]
    max_x, max_y, _max_z = mesh["maxs"]
    tx = PLATE_CENTER_X - (min_x + max_x) / 2
    ty = PLATE_CENTER_Y - (min_y + max_y) / 2
    bbox = [tx + min_x, ty + min_y, tx + max_x, ty + max_y]
    return json.dumps(
        {
            "bbox_all": bbox,
            "bbox_objects": [
                {
                    "area": (max_x - min_x) * (max_y - min_y),
                    "bbox": bbox,
                    "id": 82,
                    "layer_height": 0.2,
                    "name": "OSS V1.0 Horn Mount 4mm Shoulder PLA",
                }
            ],
            "bed_type": "textured_plate",
            "filament_colors": ["#1d1d1d"],
            "filament_ids": ["PLA Matte"],
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_STL.exists():
        raise FileNotFoundError(f"Missing shoulder-relieved mount STL: {SOURCE_STL}")
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing Bambu template: {TEMPLATE}")

    mesh = _read_and_orient_stl(SOURCE_STL)
    _write_bed_stl(BED_STL, mesh)

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
        OUT, "w", compression=zipfile.ZIP_DEFLATED
    ) as output:
        for info in template.infolist():
            if info.filename in skip:
                continue
            if info.filename.startswith("3D/Objects/"):
                continue
            if info.filename.startswith("Metadata/") and info.filename.endswith(".png"):
                continue
            output.writestr(info, template.read(info.filename))
        output.writestr("3D/3dmodel.model", _root_model(mesh))
        output.writestr(OBJECT_MODEL_PATH, _object_model(mesh))
        output.writestr("3D/_rels/3dmodel.model.rels", _relationships())
        output.writestr("Metadata/project_settings.config", _project_settings())
        output.writestr("Metadata/model_settings.config", _model_settings(mesh))
        output.writestr("Metadata/plate_1.json", _plate_json(mesh))
        output.writestr("Metadata/cut_information.xml", _cut_information())
        output.writestr("Metadata/slice_info.config", _slice_info())
        output.writestr("Metadata/filament_sequence.json", _filament_sequence())

    diagnostics = {
        "source_stl": str(SOURCE_STL.resolve()),
        "bed_oriented_stl": str(BED_STL.resolve()),
        "project_3mf": str(OUT.resolve()),
        "orientation": (
            "x' = x, y' = z - 110, z' = 134 - y; horn-facing face on bed"
        ),
        "bbox_mm": {
            "min": [round(value, 3) for value in mesh["mins"]],
            "max": [round(value, 3) for value in mesh["maxs"]],
            "size": [
                round(mesh["maxs"][index] - mesh["mins"][index], 3)
                for index in range(3)
            ],
        },
        "bed_contact": {
            "area_mm2": round(float(mesh["bed_contact_area"]), 1),
            "triangle_count": int(mesh["bed_contact_triangles"]),
        },
        "settings": {
            "printer": "Bambu Lab X2D, 0.4 mm nozzle",
            "filament": "Bambu PLA Matte @BBL X2D 0.4 nozzle",
            "layer_height_mm": 0.2,
            "wall_loops": 4,
            "infill": "25% gyroid",
            "top_bottom_shell_layers": 5,
            "supports": False,
            "prime_tower": False,
            "brim": "none",
            "nozzle_temperature_c": 220,
            "textured_plate_temperature_c": 55,
        },
    }
    DIAGNOSTICS.write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
