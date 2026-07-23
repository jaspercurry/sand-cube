"""Send Sand Cube geometry or exported STEP files to OCP CAD Viewer."""

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

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ShapeList = list[tuple[str, object]]
ShapeBuilder = Callable[[], ShapeList]


@dataclass(frozen=True)
class ViewerTarget:
    """A named OCP CAD Viewer target."""

    description: str
    build: ShapeBuilder


def _final_enclosure() -> ShapeList:
    from src.final_enclosure import build as build_final_enclosure

    part, _params, _data = build_final_enclosure()
    return [("final_enclosure", part)]


def _final_enclosure_exports() -> ShapeList:
    from src.final_enclosure import build_export_shapes

    shapes, _data = build_export_shapes()
    return [(Path(filename).stem, shape) for filename, shape in shapes.items()]


def _final_horn() -> ShapeList:
    from src.final_horn import build as build_final_horn

    return [("final_jmlc_horn", build_final_horn())]


def _legacy_enclosure() -> ShapeList:
    from src.enclosure import build as build_legacy_enclosure

    return [("legacy_203mm_sand_cube", build_legacy_enclosure())]


def _electronics_open_lid() -> ShapeList:
    """Show the focused electronics enclosure with the lid as a separate body."""
    from build123d import Location

    from src.features.electronics import (
        DEFAULT_CONFIG,
        active_layout_variants,
        build_component_placeholders,
        build_thin_plate_printed_parts,
    )

    variant = active_layout_variants()[0]
    base, lid, _printed, _notes = build_thin_plate_printed_parts(
        variant,
        DEFAULT_CONFIG,
    )
    placeholders, _placement_notes = build_component_placeholders(
        variant,
        DEFAULT_CONFIG,
    )
    placeholder_names = [
        f"{placement.spec}_clearance"
        for placement in variant.placements
        if placement.spec in {"amp", "pi_hat", "buck", "mic"}
    ]
    shapes: ShapeList = [
        ("electronics_base_with_standoffs", base),
        ("electronics_lid_lifted_for_inspection", Location((0, 0, 24.0)) * lid),
    ]
    shapes.extend(zip(placeholder_names, placeholders, strict=True))
    return shapes


def _horn_support_experiment() -> ShapeList:
    from build123d import import_stl
    from scripts.generate_horn_support_experiment import OUT, VERSION

    stl_stems = [
        ("horn_pla", "experimental_jmlc_horn_print_assist"),
        ("accordion_wall_pla", "experimental_jmlc_horn_accordion_support_wall_pla"),
        ("inner_flare_cradle_pla", "experimental_jmlc_horn_inner_flare_cradle_pla"),
        ("outer_landing_pla", "experimental_jmlc_horn_outer_landing_cradle_pla"),
        (
            "inner_flare_support_interface",
            "experimental_jmlc_horn_inner_flare_bambu_support_interface",
        ),
        (
            "outer_landing_support_interface",
            "experimental_jmlc_horn_outer_landing_bambu_support_interface",
        ),
        (
            "rear_flange_support_pla",
            "experimental_jmlc_horn_rear_flange_support_ring_pla",
        ),
        (
            "rear_flange_support_interface",
            "experimental_jmlc_horn_rear_flange_interface_skin",
        ),
    ]
    shapes: ShapeList = []
    for name, stem in stl_stems:
        path = OUT / f"{stem}_{VERSION}_bed_oriented.stl"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing generated horn support experiment STL: {path}"
            )
        shapes.append((name, import_stl(path)))
    return shapes


def _horn_mouth_down_experiment() -> ShapeList:
    from build123d import import_stl
    from scripts.generate_horn_mouth_down_experiment import OUT, VERSION

    stl_stems = [
        ("horn_pla_mouth_down", "experimental_jmlc_horn_mouth_down_horn"),
        (
            "female_cradle_pla",
            "experimental_jmlc_horn_mouth_down_female_cradle_pla",
        ),
        (
            "support_barrier_interface",
            "experimental_jmlc_horn_mouth_down_barrier_interface",
        ),
    ]
    shapes: ShapeList = []
    for name, stem in stl_stems:
        path = OUT / f"{stem}_{VERSION}_bed_oriented.stl"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing generated mouth-down horn experiment STL: {path}"
            )
        shapes.append((name, import_stl(path)))
    return shapes

GEOMETRY_TARGETS: dict[str, ViewerTarget] = {
    "electronics-open-lid": ViewerTarget(
        "Show the focused electronics enclosure with the lid lifted as its own body.",
        _electronics_open_lid,
    ),
    "final-enclosure": ViewerTarget(
        "Build and show the current final 8.5 in enclosure.",
        _final_enclosure,
    ),
    "final-enclosure-exports": ViewerTarget(
        "Build and show the four standard enclosure export bodies.",
        _final_enclosure_exports,
    ),
    "final-horn": ViewerTarget(
        "Build and show the current standalone B&C DE250 JMLC horn.",
        _final_horn,
    ),
    "legacy-enclosure": ViewerTarget(
        "Build and show the archived 203 mm enclosure.",
        _legacy_enclosure,
    ),
    "horn-support-experiment": ViewerTarget(
        "Import and show the current generated JMLC horn support experiment.",
        _horn_support_experiment,
    ),
    "horn-mouth-down-experiment": ViewerTarget(
        "Import and show the current generated mouth-down JMLC horn cradle experiment.",
        _horn_mouth_down_experiment,
    ),
}


STEP_TARGETS: dict[str, Path] = {
    "compact-enclosure-step": ROOT
    / "build/compact_6in/compact_6in_one_piece_enclosure.step",
    "compact-horn-step": ROOT / "build/compact_6in/compact_6in_f110m_jmlc_horn.step",
    "compact-horn-fit-step": ROOT
    / "build/compact_6in/compact_6in_horn_f110m_fit_stack.step",
    "compact-system-step": ROOT / "build/compact_6in/compact_6in_system_preview.step",
    "final-enclosure-step": ROOT
    / "build/sand_cube_8_5_black_hole/contoured_inner"
    / "sand_cube_8_5_black_hole_final_enclosure.step",
    "final-complete-step": ROOT
    / "build/sand_cube_8_5_black_hole/contoured_inner"
    / "sand_cube_8_5_black_hole_final_complete_assembly.step",
    "final-system-step": ROOT / "build/final_system/final_sand_cube_horn_system.step",
    "horn-stack-step": ROOT / "build/final_system/final_horn_bracket_de250_stack.step",
    "placed-horn-step": ROOT / "build/final_system/final_jmlc_horn_placed.step",
}


def _display_name(path: Path) -> str:
    return path.stem.replace("-", "_").replace(" ", "_")


def _import_step_file(path: Path) -> ShapeList:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"STEP file does not exist: {resolved}")
    from build123d import import_step

    return [(_display_name(resolved), import_step(resolved))]


def _latest_step_file() -> Path:
    files = sorted(
        (path for path in (ROOT / "build").rglob("*.step") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
    )
    if not files:
        raise FileNotFoundError(
            "No STEP files found under build/. Run a generate script first."
        )
    return files[-1]


def _print_targets() -> None:
    print("Build123d geometry targets:")
    for name, target in sorted(GEOMETRY_TARGETS.items()):
        print(f"  {name:<25} {target.description}")
    print()
    print("Exported STEP targets:")
    for name, path in sorted(STEP_TARGETS.items()):
        status = "exists" if path.exists() else "missing"
        print(f"  {name:<25} {path.relative_to(ROOT)} [{status}]")


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    target_names = sorted([*GEOMETRY_TARGETS, *STEP_TARGETS])
    parser = argparse.ArgumentParser(
        description=(
            "Show Sand Cube build123d geometry or imported STEP files in "
            "OCP CAD Viewer."
        )
    )
    parser.add_argument(
        "step_path",
        nargs="?",
        type=Path,
        help="Optional STEP/STP file to import and show.",
    )
    parser.add_argument(
        "-t",
        "--target",
        choices=target_names,
        default="final-enclosure",
        help="Named geometry or exported STEP target to show.",
    )
    parser.add_argument(
        "--step",
        type=Path,
        help="STEP/STP file to import and show. Overrides --target.",
    )
    parser.add_argument(
        "--latest-step",
        action="store_true",
        help="Import and show the most recently modified STEP file under build/.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available viewer targets and exit.",
    )
    parser.add_argument(
        "--tool",
        choices=("off", "select", "properties", "distance"),
        default="properties",
        help="Initial OCP analysis tool.",
    )
    parser.add_argument(
        "--tab",
        choices=("tree", "clip", "zebra", "material", "studio"),
        default=None,
        help="Initial OCP UI tab. Use 'clip' for section-plane inspection.",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Show the OCP grid.",
    )
    parser.add_argument(
        "--no-axes",
        action="store_true",
        help="Hide viewer axes.",
    )
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="Start with model transparency enabled.",
    )
    parser.add_argument(
        "--plain-edges",
        action="store_true",
        help="Do not force black model edges.",
    )
    args = parser.parse_args(argv)

    selected_modes = sum(
        bool(value)
        for value in (args.step_path, args.step, args.latest_step)
    )
    if selected_modes > 1:
        parser.error("Use only one of positional STEP path, --step, or --latest-step.")
    return args


def _resolve_shapes(args: argparse.Namespace) -> ShapeList:
    if args.latest_step:
        latest = _latest_step_file()
        print(f"Importing latest STEP: {latest.relative_to(ROOT)}")
        return _import_step_file(latest)
    if args.step is not None:
        return _import_step_file(args.step)
    if args.step_path is not None:
        return _import_step_file(args.step_path)
    if args.target in STEP_TARGETS:
        return _import_step_file(STEP_TARGETS[args.target])
    return GEOMETRY_TARGETS[args.target].build()


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.list:
        _print_targets()
        return

    try:
        shapes = _resolve_shapes(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    from ocp_vscode import AnalysisTool, Camera, UiTab, show

    names = [name for name, _shape in shapes]
    cad_objects = [shape for _name, shape in shapes]
    show(
        *cad_objects,
        names=names,
        reset_camera=Camera.ISO,
        axes=not args.no_axes,
        axes0=not args.no_axes,
        grid=args.grid,
        transparent=args.transparent,
        black_edges=not args.plain_edges,
        analysis_tool=AnalysisTool(args.tool),
        tab=UiTab(args.tab) if args.tab is not None else None,
    )


if __name__ == "__main__":
    main()
