"""Generate a self-contained OCP CAD Viewer page for a STEP file.

The normal OCP standalone server starts with a logo and waits for Python to push
model data over a websocket. This script bakes the tessellated STEP payload into
a static page so refresh/load timing cannot leave the viewer stuck on the logo.
"""

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

from cad_runner.outputs import job_output_path

import argparse
import os
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force ocp_vscode into local conversion mode so it does not need a running
# websocket viewer to provide config/status while generating the static page.
os.environ["OCP_VSCODE_PYTEST"] = "1"

import orjson
from build123d import import_step
from jinja2 import Environment, FileSystemLoader
from ocp_tessellate.utils import numpy_to_buffer_json
from ocp_vscode.config import AnalysisTool, Camera, Collapse, UiTab
from ocp_vscode.show import Progress, _tessellate
from ocp_vscode.standalone_defaults import DEFAULTS as STANDALONE_DEFAULTS


DEFAULT_STEP = ROOT / "build/final_system/final_sand_cube_horn_system.step"
DEFAULT_OUT = ROOT / "build/static_ocp_viewer"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _viewer_template_config() -> dict[str, Any]:
    config = dict(STANDALONE_DEFAULTS)
    config["glass"] = not config.pop("no_glass")
    config["tools"] = not config.pop("no_tools")
    config["ortho"] = not config.pop("perspective")
    config["grid"] = [True, False, False]
    config["axes"] = True
    config["axes0"] = True
    config["black_edges"] = True
    config["tree_width"] = 280
    config["treeWidth"] = 280
    config["collapse"] = "1"
    return config


def model_payload(step_path: Path) -> dict[str, Any]:
    shape = import_step(step_path)
    name = step_path.stem.replace("-", "_").replace(" ", "_")
    instances, shapes, config, count, _mapping, extracted_materials = _tessellate(
        shape,
        names=[name],
        progress=Progress(["-", "+", "*", "c"]),
        reset_camera=Camera.ISO,
        axes=True,
        axes0=True,
        grid=[True, False, False],
        black_edges=True,
        glass=False,
        tools=True,
        tree_width=280,
        collapse=Collapse.ROOT,
        analysis_tool=AnalysisTool.PROPERTIES,
        tab=UiTab.TREE,
        default_facecolor="#6ab7ff",
        default_thickedgecolor="#505050",
        default_vertexcolor="#505050",
    )
    if extracted_materials:
        shapes["materials"] = extracted_materials

    config.update(
        {
            "_splash": False,
            "reset_camera": Camera.ISO.value,
            "axes": True,
            "axes0": True,
            "grid": [True, False, False],
            "black_edges": True,
            "glass": False,
            "tools": True,
            "tree_width": 280,
            "collapse": Collapse.ROOT.value,
            "analysis_tool": AnalysisTool.PROPERTIES.value,
            "tab": UiTab.TREE.value,
            "theme": "browser",
        }
    )
    return {
        "type": "data",
        "data": numpy_to_buffer_json({"instances": instances, "shapes": shapes}),
        "config": config,
        "count": count,
    }


def render_viewer(payload: dict[str, Any], out_dir: Path) -> None:
    import ocp_vscode

    package_dir = Path(ocp_vscode.__file__).resolve().parent
    static_src = package_dir / "static"
    static_dst = out_dir / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)

    model_js = b"export const MODEL = " + orjson.dumps(
        payload,
        default=_json_default,
    ) + b";\n"
    (out_dir / "model-data.js").write_bytes(model_js)

    env = Environment(loader=FileSystemLoader(package_dir / "templates"))
    template = env.get_template("viewer.html")

    def render_html(asset_prefix: str) -> str:
        return template.render(
            standalone_scripts="",
            standalone_imports=(
                f'import {{ MODEL }} from "{asset_prefix}model-data.js";'
            ),
            standalone_comms="""
                const vscode = {
                    postMessage: (msg) => {
                        if (msg.command !== "status") {
                            console.debug("viewer message", msg);
                        }
                    }
                };
                const standaloneViewer = () => {
                    viewer = showViewer(MODEL.data, MODEL.config);
                    window.viewer = viewer;
                };
                window.showViewer = standaloneViewer;
            """,
            standalone_init='onload="showViewer()"',
            styleSrc=f"{asset_prefix}static/css/three-cad-viewer.css",
            scriptSrc=f"{asset_prefix}static/js/three-cad-viewer.esm.js",
            **_viewer_template_config(),
        )
    (out_dir / "index.html").write_text(render_html("./"))
    viewer_dir = out_dir / "viewer"
    viewer_dir.mkdir(exist_ok=True)
    (viewer_dir / "index.html").write_text(render_html("../"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a static OCP CAD Viewer page for a STEP file."
    )
    parser.add_argument(
        "step",
        nargs="?",
        type=Path,
        default=DEFAULT_STEP,
        help="STEP/STP file to render.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory for the static viewer.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    step_path = args.step.expanduser().resolve()
    if not step_path.exists():
        raise SystemExit(f"STEP file does not exist: {step_path}")
    out_dir = job_output_path(args.out.expanduser().resolve())
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = model_payload(step_path)
    render_viewer(payload, out_dir)
    print(f"Static OCP viewer: {out_dir / 'viewer' / 'index.html'}")
    print(f"Model data: {out_dir / 'model-data.js'}")


if __name__ == "__main__":
    main()
