"""Render lightweight PNG previews of the current CAD model."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from ocp_tessellate.tessellator import tessellate

from src.enclosure import build


def _set_axes_equal(ax, vertices: np.ndarray) -> None:
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    centers = (mins + maxs) / 2
    radius = (maxs - mins).max() / 2
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)


def render(path: Path, *, elev: float, azim: float, title: str) -> None:
    part = build()
    mesh = tessellate(
        part.wrapped,
        cache_key=f"sand-cube-{title}",
        deviation=0.03,
        quality=1.0,
        angular_tolerance=0.08,
        compute_faces=True,
        compute_edges=False,
    )

    vertices = mesh["vertices"].reshape((-1, 3))
    triangles = mesh["triangles"].reshape((-1, 3))
    polys = vertices[triangles]

    face_normals = np.cross(polys[:, 1] - polys[:, 0], polys[:, 2] - polys[:, 0])
    face_normals /= np.linalg.norm(face_normals, axis=1, keepdims=True).clip(1e-9)
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    shade = (face_normals @ light).clip(0, 1)
    shade = 0.46 + 0.34 * shade

    base = np.array([0.08, 0.09, 0.1])
    facecolors = np.column_stack([base * shade[:, None] + 0.04, np.ones(len(shade))])

    fig = plt.figure(figsize=(9, 9), dpi=180)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(
            polys,
            facecolors=facecolors,
            edgecolors="none",
            linewidths=0.0,
            antialiased=True,
        )
    )
    _set_axes_equal(ax, vertices)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, pad=18, fontsize=13)
    fig.patch.set_facecolor("#f4f1ea")
    ax.set_facecolor("#f4f1ea")
    plt.tight_layout(pad=0.25)
    path.parent.mkdir(exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def main() -> None:
    render(Path("build/preview_iso.png"), elev=24, azim=-38, title="Sand Cube - ISO Preview")
    render(Path("build/preview_front.png"), elev=0, azim=-90, title="Sand Cube - Front Preview")
    render(Path("build/preview_rear.png"), elev=0, azim=90, title="Sand Cube - Rear Preview")


if __name__ == "__main__":
    main()
