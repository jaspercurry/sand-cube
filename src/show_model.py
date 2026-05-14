"""Send the Sand Cube model to OCP CAD Viewer."""

from __future__ import annotations

from ocp_vscode import Camera, show

from src.enclosure import build


def main() -> None:
    part = build()
    show(
        part,
        names=["sand_cube"],
        reset_camera=Camera.ISO,
        axes=True,
        black_edges=True,
    )


if __name__ == "__main__":
    main()

