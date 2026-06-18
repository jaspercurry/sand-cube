"""Package the experimental direct-rim-support horn as a Bambu Studio 3MF."""

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
OUT_DIR = ROOT / "build" / "experiments" / "jmlc_horn_support_experiment"
VERSION = "v21"
GEOMETRY_VERSION = "v20"
TEMPLATE = Path(
    "/Users/jaspercurry/Downloads/"
    "JTS - Print Attempt 3 - PLA Matte Supports PETG Interface v5c.3mf"
)
PROJECT_FILENAME = (
    f"jmlc_horn_220p0_accordion_support_{VERSION}_20wave_40rib_flare_016mm"
    "_variable_layers"
    "_dual_nozzle_pla_bambu_support_project.3mf"
)
OUT = OUT_DIR / PROJECT_FILENAME
PLATE_CENTER_X = 130.0
PLATE_CENTER_Y = 119.0

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PNS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BNS = "http://schemas.bambulab.com/package/2021"
XML_NS = "http://www.w3.org/XML/1998/namespace"
# Parts are packaged as separate component meshes with per-part extruder
# assignments instead of one merged painted mesh. Painting a merged mesh
# makes the slicer's multi-material segmentation bleed the support-filament
# color into the touching PLA volumes (~4x the modeled interface volume).
OBJECTS_MODEL_PATH = "3D/Objects/object_2.model"

ET.register_namespace("", NS)
ET.register_namespace("p", PNS)
ET.register_namespace("BambuStudio", BNS)


def _geometry_stl(stem: str) -> Path:
    return OUT_DIR / f"{stem}_{GEOMETRY_VERSION}_bed_oriented.stl"


PARTS = [
    {
        "name": "JMLC Horn 220.0 150 degree horn PLA",
        "source": _geometry_stl("experimental_jmlc_horn_print_assist"),
        "extruder": 1,
    },
    {
        "name": "JMLC Horn 220.0 accordion support wall PLA",
        "source": _geometry_stl("experimental_jmlc_horn_accordion_support_wall_pla"),
        "extruder": 1,
    },
    {
        "name": "JMLC Horn 220.0 40-rib 16mm inner flare cradle PLA",
        "source": _geometry_stl("experimental_jmlc_horn_inner_flare_cradle_pla"),
        "extruder": 1,
    },
    {
        "name": "JMLC Horn 220.0 corrugated-wall outer landing PLA",
        "source": _geometry_stl("experimental_jmlc_horn_outer_landing_cradle_pla"),
        "extruder": 1,
    },
    {
        "name": "JMLC Horn 220.0 inner flare Bambu support interface skin",
        "source": _geometry_stl(
            "experimental_jmlc_horn_inner_flare_bambu_support_interface"
        ),
        "extruder": 2,
        # The release skin must stay fully dense so the horn underside
        # lands on a continuous surface.
        "dense_infill": True,
    },
    {
        "name": "JMLC Horn 220.0 outer landing Bambu support interface skin",
        "source": _geometry_stl(
            "experimental_jmlc_horn_outer_landing_bambu_support_interface"
        ),
        "extruder": 2,
        # The release skin must stay fully dense so the horn underside
        # lands on a continuous surface.
        "dense_infill": True,
    },
    {
        "name": "JMLC Horn 220.0 rear flange support washer PLA",
        "source": _geometry_stl("experimental_jmlc_horn_rear_flange_support_ring_pla"),
        "extruder": 1,
    },
    {
        "name": "JMLC Horn 220.0 rear flange Bambu support interface skin",
        "source": _geometry_stl("experimental_jmlc_horn_rear_flange_interface_skin"),
        "extruder": 2,
        "dense_infill": True,
    },
]


def _uuid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"jmlc-direct-rim-support/{seed}"))


def _read_binary_stl(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")
    tri_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + tri_count * 50
    if expected != len(data):
        raise ValueError(f"{path} does not look like a binary STL")

    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[tuple[float, float, float], int] = {}
    triangles: list[tuple[int, int, int]] = []
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    offset = 84
    for _ in range(tri_count):
        offset += 12
        tri: list[int] = []
        for _vertex in range(3):
            point = struct.unpack_from("<fff", data, offset)
            offset += 12
            key = tuple(round(value, 6) for value in point)
            index = vertex_index.get(key)
            if index is None:
                index = len(vertices)
                vertex_index[key] = index
                vertices.append(key)
                for axis, value in enumerate(key):
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
            tri.append(index)
        triangles.append(tuple(tri))
        offset += 2

    return {
        "vertices": vertices,
        "triangles": triangles,
        "mins": mins,
        "maxs": maxs,
        "face_count": tri_count,
    }


def _objects_model(meshes: list[dict[str, object]]) -> bytes:
    """Write the production-extension sub-model holding one mesh per part."""
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
    for index, mesh in enumerate(meshes, 1):
        obj = ET.SubElement(
            resources,
            f"{{{NS}}}object",
            {
                "id": str(index),
                f"{{{PNS}}}UUID": _uuid(f"part-mesh/{VERSION}/{index}"),
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


def _component_object() -> ET.Element:
    obj = ET.Element(
        f"{{{NS}}}object",
        {
            "id": "2",
            f"{{{PNS}}}UUID": _uuid(f"mesh/component-assembly-{VERSION}-dual-nozzle"),
            "name": f"JMLC Horn 220.0 accordion support 20wave 40rib flare {VERSION} dual nozzle",
            "type": "model",
        },
    )
    components = ET.SubElement(obj, f"{{{NS}}}components")
    for index in range(1, len(PARTS) + 1):
        ET.SubElement(
            components,
            f"{{{NS}}}component",
            {
                f"{{{PNS}}}path": f"/{OBJECTS_MODEL_PATH}",
                "objectid": str(index),
                f"{{{PNS}}}UUID": _uuid(f"component/{VERSION}/{index}"),
                "transform": "1 0 0 0 1 0 0 0 1 0 0 0",
            },
        )
    return obj


def _root_model() -> bytes:
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
        ("Title", "JMLC Horn 220.0 accordion support 20wave 40rib flare"),
        (
            "Description",
            "Experimental 220 mm JMLC horn generated from the Le Cleac'h "
            "recurrence with a 150 degree rolled-back exit angle, "
            "a narrow-footprint 20-wave accordion PLA support wall, a 16 mm inward "
            "peak/trough ribbed flared cradle with continuous top cap, a matching Bambu "
            "Support for PLA/PETG release skin following the analytic JMLC "
            "rolled-wall underside, and a rear-flange PLA support washer topped with a "
            f"Bambu Support for PLA/PETG interface ring. {VERSION.upper()} prints PLA from "
            "nozzle 1 and support filament from nozzle 2 on the X2D. V21 keeps "
            "0.16 mm layers for the steeper body and bakes in finer variable "
            "layers through the rolled lip and top crest.",
        ),
    ]:
        ET.SubElement(model, f"{{{NS}}}metadata", {"name": key}).text = value

    resources = ET.SubElement(model, f"{{{NS}}}resources")
    build = ET.SubElement(
        model,
        f"{{{NS}}}build",
        {f"{{{PNS}}}UUID": _uuid("build")},
    )
    resources.append(_component_object())
    ET.SubElement(
        build,
        f"{{{NS}}}item",
        {
            "objectid": "2",
            f"{{{PNS}}}UUID": _uuid(f"build/painted-assembly-{VERSION}-dual-nozzle"),
            "transform": (
                f"1 0 0 0 1 0 0 0 1 {PLATE_CENTER_X:g} {PLATE_CENTER_Y:g} 0"
            ),
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
            "Target": f"/{OBJECTS_MODEL_PATH}",
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
            "default_print_profile": (
                "Variable Layer JMLC Horn 220 V21 20wave 40rib Flare Dual Nozzle PLA Support @BBL X2D"
            ),
            "layer_height": "0.16",
            "initial_layer_print_height": "0.2",
            "enable_support": "0",
            "enable_prime_tower": "1",
            "prime_tower_width": "18",
            "prime_tower_brim_width": "0",
            "prime_tower_rib_width": "4",
            "wipe_tower_x": ["22"],
            "wipe_tower_y": ["212"],
            "brim_type": "outer_and_inner",
            "brim_object_gap": "0.05",
            "brim_width": "5",
            # Force solid shells where volumes of different filaments touch.
            # Without this the flange/horn faces resting on the support
            # interface skins are classified internal and print sparse.
            "interface_shells": "1",
            "eng_plate_temp": ["55", "60"],
            "eng_plate_temp_initial_layer": ["55", "60"],
            "initial_layer_flow_ratio": "1.03",
            "initial_layer_infill_speed": ["60", "60", "60", "60"],
            "initial_layer_line_width": "0.55",
            "initial_layer_speed": ["30", "30", "30", "30"],
            "filament_tower_interface_purge_volume": ["20", "20"],
            "filament_adhesiveness_category": ["100", "705"],
            "filament_density": ["1.32", "1.19"],
            "filament_flow_ratio": [
                "1.006",
                "1.006",
                "1.006",
                "1.006",
                "1",
                "1",
                "1",
                "1",
            ],
            "filament_ids": ["GFA00", "GFS05"],
            "filament_is_support": ["0", "1"],
            "filament_max_volumetric_speed": [
                "22",
                "40",
                "22",
                "25",
                "6",
                "6",
                "6",
                "6",
            ],
            "filament_settings_id": [
                "Bambu PLA Matte @BBL X2D 0.4 nozzle",
                "Bambu Support For PLA/PETG @BBL X2D 0.4 nozzle",
            ],
            "filament_soluble": ["0", "0"],
            "filament_tower_interface_print_temp": ["220", "210"],
            "filament_type": ["PLA", "PLA"],
            "hot_plate_temp": ["55", "60"],
            "hot_plate_temp_initial_layer": ["55", "60"],
            "nozzle_temperature": [
                "220",
                "220",
                "220",
                "220",
                "210",
                "210",
                "210",
                "210",
            ],
            "nozzle_temperature_initial_layer": [
                "220",
                "220",
                "220",
                "220",
                "210",
                "210",
                "210",
                "210",
            ],
            "textured_plate_temp": ["55", "60"],
            "textured_plate_temp_initial_layer": ["55", "60"],
            "extruder_nozzle_count": ["1", "1"],
            "extruder_nozzle_volume_type": ["Standard", "Standard"],
            # Filament -> logical extruder. PLA on extruder/nozzle 1,
            # support filament on extruder/nozzle 2.
            "filament_map": ["1", "2"],
            "filament_map_mode": "Manual",
            # Nozzle index inside each extruder; the X2D heads carry one
            # nozzle each, so this is always 0 (see the stock presets).
            "filament_nozzle_map": ["0", "0"],
            "filament_volume_map": ["0", "0"],
            # Machine constant from the Bambu X2D/H2D dual-extruder
            # profile (logical 1 -> physical 1, logical 2 -> physical 0).
            # Overriding it with invalid ids makes Studio fall back to a
            # single-nozzle mapping.
            "physical_extruder_map": ["1", "0"],
            "single_extruder_multi_material": "0",
            "wall_loops": "8",
            "sparse_infill_density": "15%",
            "sparse_infill_pattern": "gyroid",
        }
    )
    return json.dumps(settings, indent=4).encode()


def _object_config(meshes: list[dict[str, object]]) -> ET.Element:
    obj = ET.Element("object", {"id": "2"})
    ET.SubElement(
        obj,
        "metadata",
        {
            "key": "name",
            "value": f"JMLC Horn 220.0 accordion support 20wave 40rib flare {VERSION} dual nozzle.3mf",
        },
    )
    ET.SubElement(obj, "metadata", {"key": "extruder", "value": "1"})
    ET.SubElement(
        obj,
        "metadata",
        {"face_count": str(sum(int(mesh["face_count"]) for mesh in meshes))},
    )
    for index, (part, mesh) in enumerate(zip(PARTS, meshes, strict=True), 1):
        part_el = ET.SubElement(
            obj, "part", {"id": str(index), "subtype": "normal_part"}
        )
        entries = [
            ("name", str(part["name"])),
            ("extruder", str(part["extruder"])),
            ("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"),
            ("source_file", PROJECT_FILENAME),
            ("source_object_id", "0"),
            ("source_volume_id", str(index - 1)),
            ("source_offset_x", "0"),
            ("source_offset_y", "0"),
            ("source_offset_z", "0"),
        ]
        if part.get("dense_infill"):
            entries.insert(2, ("sparse_infill_density", "100%"))
        for key, value in entries:
            ET.SubElement(part_el, "metadata", {"key": key, "value": value})
        ET.SubElement(
            part_el,
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
    return obj


def _model_settings(meshes: list[dict[str, object]]) -> bytes:
    root = ET.Element("config")
    root.append(_object_config(meshes))

    plate = ET.SubElement(root, "plate")
    for key, value in [
        ("plater_id", "1"),
        ("plater_name", ""),
        ("locked", "false"),
        ("filament_map_mode", "Manual"),
        ("filament_maps", "1 2"),
        ("filament_volume_maps", "0 0"),
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


def _plate_json(meshes: list[dict[str, object]]) -> bytes:
    min_x = min(mesh["mins"][0] for mesh in meshes)
    min_y = min(mesh["mins"][1] for mesh in meshes)
    max_x = max(mesh["maxs"][0] for mesh in meshes)
    max_y = max(mesh["maxs"][1] for mesh in meshes)
    bbox_all = [
        PLATE_CENTER_X + min_x,
        PLATE_CENTER_Y + min_y,
        PLATE_CENTER_X + max_x,
        PLATE_CENTER_Y + max_y,
    ]
    bbox_objects = [
        {
            "area": (max_x - min_x) * (max_y - min_y),
            "bbox": bbox_all,
            "id": 82,
            "layer_height": 0.16,
            "name": f"JMLC Horn 220.0 accordion support 20wave 40rib flare {VERSION} dual nozzle",
        }
    ]
    return json.dumps(
        {
            "bbox_all": bbox_all,
            "bbox_objects": bbox_objects,
            "bed_type": "textured_plate",
            "filament_colors": ["#000000", "#FFFFFF"],
            "filament_ids": ["PLA Matte", "Support for PLA/PETG"],
            "first_extruder": 0,
            "is_seq_print": False,
            "nozzle_diameter": 0.4,
            "version": 2,
        },
        indent=4,
    ).encode()


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge1 <= edge0:
        return 1.0 if value >= edge1 else 0.0
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _target_layer_height(z: float, model_height: float) -> float:
    """Geometry-aware variable layer profile for the visible horn crest."""
    if z < 76.0:
        return 0.16
    if z < 86.0:
        return _lerp(0.16, 0.12, _smoothstep(76.0, 86.0, z))
    if z < 96.0:
        return _lerp(0.12, 0.10, _smoothstep(86.0, 96.0, z))
    return _lerp(0.10, 0.08, _smoothstep(96.0, model_height, z))


def _layer_heights_profile(meshes: list[dict[str, object]]) -> bytes:
    model_height = max(float(mesh["maxs"][2]) for mesh in meshes)
    pairs: list[tuple[float, float]] = [
        (0.0, 0.20),
        (0.20, 0.20),
        (0.20, _target_layer_height(0.20, model_height)),
    ]

    z = 0.20
    while z < model_height - 1e-6:
        height = _target_layer_height(z, model_height)
        z = min(model_height, z + height)
        pairs.append((z, _target_layer_height(z, model_height)))

    payload = "object_id=1|" + ";".join(
        f"{z:.6f};{height:.6f}" for z, height in pairs
    )
    payload += "\n"
    return payload.encode()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing Bambu template: {TEMPLATE}")
    meshes = [_read_binary_stl(Path(part["source"])) for part in PARTS]

    skip = {
        "3D/3dmodel.model",
        "3D/_rels/3dmodel.model.rels",
        "Metadata/project_settings.config",
        "Metadata/model_settings.config",
        "Metadata/plate_1.json",
        "Metadata/layer_heights_profile.txt",
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
        output.writestr("3D/3dmodel.model", _root_model())
        output.writestr(OBJECTS_MODEL_PATH, _objects_model(meshes))
        output.writestr("3D/_rels/3dmodel.model.rels", _relationships())
        output.writestr("Metadata/project_settings.config", _project_settings())
        output.writestr("Metadata/model_settings.config", _model_settings(meshes))
        output.writestr("Metadata/plate_1.json", _plate_json(meshes))
        output.writestr(
            "Metadata/layer_heights_profile.txt",
            _layer_heights_profile(meshes),
        )

    summary = {
        "path": str(OUT.resolve()),
        "geometry_version": GEOMETRY_VERSION,
        "layer_height_profile": "0.16 mm body, ramping to 0.08 mm at top crest",
        "parts": [
            {
                "name": part["name"],
                "extruder": part["extruder"],
                "source": str(Path(part["source"]).resolve()),
                "bbox": {
                    "min": [round(value, 3) for value in mesh["mins"]],
                    "max": [round(value, 3) for value in mesh["maxs"]],
                },
                "faces": mesh["face_count"],
            }
            for part, mesh in zip(PARTS, meshes, strict=True)
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
