"""Generate a local HTML comparison viewer for electronics enclosure variants."""

from __future__ import annotations

import html
import json
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

from src.features.electronics import (
    DEFAULT_CONFIG,
    active_layout_variants,
    build_component_placeholders,
    build_printed_enclosure,
)


OUT = ROOT / "build" / "electronics_enclosure" / "viewer"
NOTES_PATH = (
    ROOT / "build" / "electronics_enclosure" / "electronics_enclosure_layouts.json"
)

PALETTE = {
    "enclosure": np.array([0.58, 0.60, 0.56]),
    "amp": np.array([0.15, 0.32, 0.58]),
    "pi_hat": np.array([0.10, 0.48, 0.35]),
    "buck": np.array([0.82, 0.48, 0.18]),
    "mic": np.array([0.72, 0.22, 0.30]),
}


def _shape_mesh(shape, cache_key: str) -> tuple[np.ndarray, np.ndarray]:
    mesh = tessellate(
        shape.wrapped,
        cache_key=cache_key,
        deviation=0.08,
        quality=0.75,
        angular_tolerance=0.12,
        compute_faces=True,
        compute_edges=False,
    )
    return mesh["vertices"].reshape((-1, 3)), mesh["triangles"].reshape((-1, 3))


def _set_axes_equal(ax, vertices: np.ndarray) -> None:
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    centers = (mins + maxs) / 2
    radius = (maxs - mins).max() / 2
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius * 0.08, centers[2] + radius * 1.08)


def _lit_facecolors(polys: np.ndarray, base: np.ndarray, alpha: float) -> np.ndarray:
    normals = np.cross(polys[:, 1] - polys[:, 0], polys[:, 2] - polys[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True).clip(1e-9)
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    shade = (normals @ light).clip(0, 1)
    shade = 0.52 + 0.36 * shade
    return np.column_stack([base * shade[:, None] + 0.05, np.full(len(shade), alpha)])


def _render_variant_image(
    variant_name: str,
    parts: list[tuple[str, object]],
    path: Path,
    *,
    elev: float,
    azim: float,
) -> None:
    meshes = []
    all_vertices = []
    for index, (label, shape) in enumerate(parts):
        vertices, triangles = _shape_mesh(shape, f"{variant_name}-{path.stem}-{index}")
        if len(vertices) == 0 or len(triangles) == 0:
            continue
        meshes.append((label, vertices, triangles))
        all_vertices.append(vertices)

    if not all_vertices:
        raise RuntimeError(f"No renderable mesh data for {variant_name}")

    vertices_for_axes = np.vstack(all_vertices)
    fig = plt.figure(figsize=(7.2, 5.6), dpi=170)
    ax = fig.add_subplot(111, projection="3d")
    for label, vertices, triangles in meshes:
        polys = vertices[triangles]
        base = PALETTE.get(label, np.array([0.24, 0.24, 0.24]))
        alpha = 0.26 if label == "enclosure" else 0.94
        collection = Poly3DCollection(
            polys,
            facecolors=_lit_facecolors(polys, base, alpha),
            edgecolors="none",
            linewidths=0.0,
            antialiased=True,
        )
        ax.add_collection3d(collection)

    _set_axes_equal(ax, vertices_for_axes)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.patch.set_facecolor("#f6f5ef")
    ax.set_facecolor("#f6f5ef")
    plt.tight_layout(pad=0.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def _variant_parts(variant) -> list[tuple[str, object]]:
    enclosure, _notes = build_printed_enclosure(variant, DEFAULT_CONFIG)
    placeholders, placements = build_component_placeholders(variant, DEFAULT_CONFIG)
    parts: list[tuple[str, object]] = [("enclosure", enclosure)]
    for placement_name, shape in zip(placements, placeholders, strict=True):
        parts.append((placement_name, shape))
    return parts


def _load_notes() -> dict[str, object]:
    if NOTES_PATH.exists():
        return json.loads(NOTES_PATH.read_text())
    return {}


def _variant_card(name: str, notes: dict[str, object]) -> str:
    size = notes.get("outer_size_mm", ["?", "?", "?"])
    footprint = notes.get("external_footprint_area_mm2", "?")
    description = notes.get("description", "")
    top_mic = notes.get("top_mic_compartment")
    separate_mic = notes.get("separate_mic")
    if separate_mic:
        badge = "separate mic"
    elif top_mic:
        badge = "top mic pod"
    else:
        badge = "baseline"
    return f"""
      <article class="card">
        <header>
          <div>
            <h2>{html.escape(name.replace("_", " "))}</h2>
            <p>{html.escape(description)}</p>
          </div>
          <span>{html.escape(badge)}</span>
        </header>
        <div class="meta">
          <strong>{size[0]} x {size[1]} x {size[2]} mm</strong>
          <span>{footprint} mm² footprint</span>
        </div>
        <div class="views">
          <figure>
            <img src="{name}_iso.png" alt="{html.escape(name)} ISO view">
            <figcaption>ISO</figcaption>
          </figure>
          <figure>
            <img src="{name}_top.png" alt="{html.escape(name)} top view">
            <figcaption>Top</figcaption>
          </figure>
        </div>
      </article>
    """


def _write_html(notes: dict[str, object]) -> None:
    variants = notes.get("variants", {})
    recommendation = notes.get("recommendation", {})
    cards = "\n".join(
        _variant_card(name, variants.get(name, {}))
        for name in variants
    )
    best = recommendation.get("best_first_print", "")
    why = recommendation.get("why", "")
    (OUT / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Electronics Enclosure Options</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      background: #f6f5ef;
      color: #1f2428;
    }}
    body {{
      margin: 0;
      padding: 28px;
    }}
    main {{
      max-width: 1500px;
      margin: 0 auto;
    }}
    .topbar {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 22px;
    }}
    h1 {{
      margin: 0;
      font-size: 28px;
      font-weight: 720;
      letter-spacing: 0;
    }}
    .topbar p {{
      margin: 7px 0 0;
      max-width: 760px;
      color: #5c646b;
      line-height: 1.45;
    }}
    .legend {{
      display: grid;
      grid-template-columns: repeat(5, max-content);
      gap: 10px 14px;
      align-items: center;
      font-size: 13px;
      color: #4b5258;
    }}
    .legend i {{
      display: inline-block;
      width: 13px;
      height: 13px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: -2px;
    }}
    .callout {{
      margin: 0 0 22px;
      padding: 12px 14px;
      border-left: 4px solid #276f54;
      background: #edf4ef;
      color: #24362e;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 18px;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #dfe2dc;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 12px 30px rgb(31 36 40 / 8%);
    }}
    .card-feature {{
      border-color: #cfded4;
      box-shadow: 0 14px 32px rgb(39 111 84 / 12%);
    }}
    .card header {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      padding: 16px 16px 10px;
      border-bottom: 1px solid #eceee8;
    }}
    .card h2 {{
      margin: 0 0 6px;
      font-size: 18px;
      text-transform: capitalize;
      letter-spacing: 0;
    }}
    .card p {{
      margin: 0;
      color: #596167;
      line-height: 1.35;
      font-size: 13px;
    }}
    .card header span {{
      white-space: nowrap;
      align-self: flex-start;
      border-radius: 999px;
      background: #f0eee4;
      color: #5c5542;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 650;
    }}
    .meta {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      padding: 11px 16px;
      color: #3f474c;
      font-size: 13px;
      border-bottom: 1px solid #eceee8;
    }}
    .views {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0;
    }}
    figure {{
      margin: 0;
      background: #f6f5ef;
      border-right: 1px solid #eceee8;
      position: relative;
    }}
    figure:last-child {{
      border-right: 0;
    }}
    img {{
      display: block;
      width: 100%;
      aspect-ratio: 1.18;
      object-fit: contain;
    }}
    figcaption {{
      position: absolute;
      left: 10px;
      bottom: 9px;
      padding: 3px 7px;
      background: rgb(255 255 255 / 82%);
      border: 1px solid #e5e3d9;
      border-radius: 5px;
      font-size: 11px;
      font-weight: 700;
      color: #4f565c;
    }}
    @media (max-width: 760px) {{
      body {{
        padding: 16px;
      }}
      .topbar {{
        display: block;
      }}
      .legend {{
        grid-template-columns: repeat(2, max-content);
        margin-top: 14px;
      }}
      .grid {{
        grid-template-columns: 1fr;
      }}
      .views {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="topbar">
      <div>
        <h1>Electronics Enclosure Options</h1>
        <p>Generated from the build123d layout study. Cards show each variant as
        an assembly preview plus a top view for footprint and mic orientation.</p>
      </div>
      <div class="legend" aria-label="Color legend">
        <span><i style="background:#93998f"></i>enclosure</span>
        <span><i style="background:#265292"></i>amp</span>
        <span><i style="background:#1a7a59"></i>Pi/HAT</span>
        <span><i style="background:#d17a2e"></i>buck</span>
        <span><i style="background:#b8384d"></i>mic</span>
      </div>
    </section>
    <p class="callout"><strong>Recommended:</strong> {html.escape(best)}
    · {html.escape(why)}</p>
    <section class="grid">
      {cards}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for variant in active_layout_variants():
        parts = _variant_parts(variant)
        _render_variant_image(
            variant.name,
            parts,
            OUT / f"{variant.name}_iso.png",
            elev=25,
            azim=-42,
        )
        _render_variant_image(
            variant.name,
            parts,
            OUT / f"{variant.name}_top.png",
            elev=90,
            azim=-90,
        )

    notes = _load_notes()
    _write_html(notes)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
