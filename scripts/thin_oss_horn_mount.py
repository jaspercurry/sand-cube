"""Create a 4 mm shoulder relief on the OSS horn mount.

The source is a mesh-only STL. The horn-facing face is kept fixed at Y=134 mm.
Inside the upper horn-interface envelope, rear-side vertices are clamped to
Y=130 mm, producing a flat 4 mm pocket/relief instead of scaling the original
8 mm wall into a tapered-looking surface.
"""

from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "/Users/jaspercurry/Downloads/Open-Source Speaker V1.0/"
    "OSS V1.0 - Horn Mount.stl"
)
OUT_DIR = ROOT / "build" / "experiments" / "horn_mount_fit"
OUT_STL = OUT_DIR / "OSS V1.0 - Horn Mount - 4mm Shoulder Relief.stl"
OUT_JSON = OUT_DIR / "oss_horn_mount_4mm_shoulder_relief_diagnostics.json"

FRONT_Y = 134.0
TARGET_REAR_Y = 130.0
INTERFACE_Z_MIN = 198.0
INTERFACE_Z_MAX = 238.0
INTERFACE_X_ABS_MAX = 46.1


Triangle = list[list[float]]


def _read_binary_stl(path: Path) -> list[Triangle]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")
    tri_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + tri_count * 50
    if expected != len(data):
        raise ValueError(f"{path} does not look like a binary STL")
    triangles: list[Triangle] = []
    offset = 84
    for _index in range(tri_count):
        offset += 12
        tri: Triangle = []
        for _vertex in range(3):
            tri.append(list(struct.unpack_from("<fff", data, offset)))
            offset += 12
        triangles.append(tri)
        offset += 2
    return triangles


def _normal(tri: Triangle) -> tuple[float, float, float] | None:
    ax = [tri[1][index] - tri[0][index] for index in range(3)]
    bx = [tri[2][index] - tri[0][index] for index in range(3)]
    vector = (
        ax[1] * bx[2] - ax[2] * bx[1],
        ax[2] * bx[0] - ax[0] * bx[2],
        ax[0] * bx[1] - ax[1] * bx[0],
    )
    length = math.sqrt(sum(value * value for value in vector))
    if length < 1e-12:
        return None
    return tuple(value / length for value in vector)


def _write_binary_stl(
    path: Path,
    *,
    header_text: str,
    triangles: list[Triangle],
) -> int:
    valid: list[tuple[tuple[float, float, float], Triangle]] = []
    for tri in triangles:
        normal = _normal(tri)
        if normal is not None:
            valid.append((normal, tri))

    header = header_text.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with path.open("wb") as output:
        output.write(header)
        output.write(struct.pack("<I", len(valid)))
        for normal, tri in valid:
            output.write(struct.pack("<fff", *normal))
            for vertex in tri:
                output.write(struct.pack("<fff", *(float(value) for value in vertex)))
            output.write(struct.pack("<H", 0))
    return len(triangles) - len(valid)


def _shoulder_vertex(vertex: list[float]) -> list[float]:
    x, y, z = vertex
    in_interface_zone = (
        abs(x) <= INTERFACE_X_ABS_MAX
        and INTERFACE_Z_MIN <= z <= INTERFACE_Z_MAX
        and y < TARGET_REAR_Y
    )
    if not in_interface_zone:
        return vertex.copy()
    return [x, TARGET_REAR_Y, z]


def _bounds(triangles: list[Triangle]) -> dict[str, list[float]]:
    points = [vertex for tri in triangles for vertex in tri]
    mins = [min(vertex[index] for vertex in points) for index in range(3)]
    maxs = [max(vertex[index] for vertex in points) for index in range(3)]
    return {
        "min": [round(value, 3) for value in mins],
        "max": [round(value, 3) for value in maxs],
        "size": [round(maxs[index] - mins[index], 3) for index in range(3)],
    }


def _region_bounds(triangles: list[Triangle]) -> dict[str, list[float]]:
    points = [
        vertex
        for tri in triangles
        for vertex in tri
        if abs(vertex[0]) <= INTERFACE_X_ABS_MAX
        and INTERFACE_Z_MIN <= vertex[2] <= INTERFACE_Z_MAX
    ]
    mins = [min(vertex[index] for vertex in points) for index in range(3)]
    maxs = [max(vertex[index] for vertex in points) for index in range(3)]
    return {
        "min": [round(value, 3) for value in mins],
        "max": [round(value, 3) for value in maxs],
        "size": [round(maxs[index] - mins[index], 3) for index in range(3)],
    }


def _edge_valence(triangles: list[Triangle]) -> dict[str, int | dict[str, int]]:
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = (
        Counter()
    )
    for tri in triangles:
        rounded = [tuple(round(coord, 5) for coord in vertex) for vertex in tri]
        for a, b in ((rounded[0], rounded[1]), (rounded[1], rounded[2]), (rounded[2], rounded[0])):
            edges[tuple(sorted((a, b)))] += 1
    counts = Counter(edges.values())
    return {
        "valence_counts": {str(key): value for key, value in sorted(counts.items())},
        "non_2_edges": sum(1 for value in edges.values() if value != 2),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    triangles = _read_binary_stl(SOURCE)
    modified = [[_shoulder_vertex(vertex) for vertex in tri] for tri in triangles]
    degenerate_removed = _write_binary_stl(
        OUT_STL,
        header_text="OSS V1.0 Horn Mount with 4mm shoulder relief",
        triangles=modified,
    )
    # Re-read the written file so diagnostics match exactly what the slicer sees.
    written = _read_binary_stl(OUT_STL)
    diagnostics = {
        "source": str(SOURCE),
        "output": str(OUT_STL.resolve()),
        "operation": (
            "Clamped rear-side vertices in the upper horn-interface zone to "
            "Y=130 mm while keeping the horn-facing Y=134 mm face fixed. "
            "This creates a flat 4 mm relief with a deliberate shoulder "
            "instead of a scaled/tapered rear surface."
        ),
        "interface_zone": {
            "x_abs_max_mm": INTERFACE_X_ABS_MAX,
            "z_min_mm": INTERFACE_Z_MIN,
            "z_max_mm": INTERFACE_Z_MAX,
            "front_y_mm": FRONT_Y,
            "target_rear_y_mm": TARGET_REAR_Y,
            "target_thickness_mm": FRONT_Y - TARGET_REAR_Y,
        },
        "original_bounds": _bounds(triangles),
        "modified_bounds": _bounds(written),
        "original_interface_region_bounds": _region_bounds(triangles),
        "modified_interface_region_bounds": _region_bounds(written),
        "triangle_count": len(written),
        "degenerate_triangles_removed": degenerate_removed,
        "mesh_edge_audit": _edge_valence(written),
    }
    OUT_JSON.write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
