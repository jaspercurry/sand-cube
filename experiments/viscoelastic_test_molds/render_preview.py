"""Render quick visual checks of the viscoelastic test tooling."""

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

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from ocp_tessellate.tessellator import tessellate
from build123d import Pos

from generate_viscoelastic_test_molds import (
    OUT,
    _bottom_print_orientation,
    _top_print_orientation,
    build_coupon_tray,
    build_sphere_mold,
)


def _mesh(shape, cache_key: str) -> tuple[np.ndarray, np.ndarray]:
    result = tessellate(
        shape.wrapped,
        cache_key=cache_key,
        deviation=0.04,
        quality=1.0,
        angular_tolerance=0.08,
        compute_faces=True,
        compute_edges=False,
    )
    vertices = result["vertices"].reshape((-1, 3))
    triangles = result["triangles"].reshape((-1, 3))
    return vertices, vertices[triangles]


def _draw_shape(ax, shape, *, color: str, cache_key: str) -> np.ndarray:
    vertices, polygons = _mesh(shape, cache_key)
    normals = np.cross(
        polygons[:, 1] - polygons[:, 0],
        polygons[:, 2] - polygons[:, 0],
    )
    normals /= np.linalg.norm(normals, axis=1, keepdims=True).clip(1e-9)
    light = np.array([-0.25, -0.45, 0.86])
    light /= np.linalg.norm(light)
    # Some OpenCascade tessellations contain triangle windings opposite their
    # neighboring face. Absolute lighting avoids false dark wedges on planes.
    shade = 0.55 + 0.35 * np.abs(normals @ light).clip(0, 1)
    rgb = np.array(matplotlib.colors.to_rgb(color))
    facecolors = np.column_stack([rgb * shade[:, None], np.ones(len(shade))])
    ax.add_collection3d(
        Poly3DCollection(
            polygons,
            facecolors=facecolors,
            edgecolors="none",
            linewidths=0.0,
        )
    )
    return vertices


def _finish_axes(ax, vertices: np.ndarray, *, elev: float, azim: float) -> None:
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    centers = (mins + maxs) / 2
    radius = max((maxs - mins).max() / 2, 1.0)
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def main() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    bottom, top = build_sphere_mold()
    bottom_print = _bottom_print_orientation(bottom)
    top_print = _top_print_orientation(top)
    coupon = build_coupon_tray()

    fig = plt.figure(figsize=(12, 6.5), dpi=180)
    fig.patch.set_facecolor("#f3f0e9")

    mold_ax = fig.add_subplot(1, 2, 1, projection="3d")
    mold_ax.set_facecolor("#f3f0e9")
    mold_vertices = np.vstack(
        [
            _draw_shape(
                mold_ax,
                Pos(-28, 0, 0) * bottom_print,
                color="#4f8fc0",
                cache_key="viscoelastic-sphere-bottom-placed",
            ),
            _draw_shape(
                mold_ax,
                Pos(28, 0, 0) * top_print,
                color="#6da9d3",
                cache_key="viscoelastic-sphere-top-placed",
            ),
        ]
    )
    _finish_axes(mold_ax, mold_vertices, elev=28, azim=-48)
    mold_ax.set_title("25 mm sphere mold — print orientation", pad=12)

    coupon_ax = fig.add_subplot(1, 2, 2, projection="3d")
    coupon_ax.set_facecolor("#f3f0e9")
    coupon_vertices = _draw_shape(
        coupon_ax,
        coupon,
        color="#d6964b",
        cache_key="viscoelastic-coupon-tray",
    )
    _finish_axes(coupon_ax, coupon_vertices, elev=30, azim=-52)
    coupon_ax.set_title("40 × 12.5 mm coupon tray", pad=12)

    fig.tight_layout(pad=1.0, w_pad=0.2)
    path = OUT / "preview.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(path.resolve())
    return path


if __name__ == "__main__":
    main()
