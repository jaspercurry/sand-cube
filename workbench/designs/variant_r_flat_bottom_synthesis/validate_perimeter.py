"""Focused proof that the hybrid wire changes only the bottom-center policy."""

from __future__ import annotations

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
from cad_runner.outputs import job_output_path

_ensure_cad_coordinated(__name__, __file__, _CAD_SAFETY_ROOT)

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402


OUT = (
    ROOT
    / "build"
    / "workbench"
    / "variant_r_flat_bottom_synthesis"
    / "perimeter"
)
DIAGNOSTICS_PATH = OUT / "diagnostics.json"


def _near(actual: float, expected: float, tolerance: float = 1e-6) -> bool:
    return abs(actual - expected) <= tolerance


def _edge_signature(edge) -> tuple:
    """Orientation-neutral geometric signature for separately built edges."""
    bounds = edge.bounding_box()
    samples = tuple(
        tuple(round(value, 7) for value in edge.position_at(fraction).to_tuple())
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)
    )
    canonical_samples = min(samples, tuple(reversed(samples)))
    return (
        str(edge.geom_type),
        round(edge.length, 7),
        tuple(
            round(value, 7)
            for value in (
                bounds.min.X,
                bounds.min.Y,
                bounds.min.Z,
                bounds.max.X,
                bounds.max.Y,
                bounds.max.Z,
            )
        ),
        canonical_samples,
    )


def _validate_case(label: str, offset_mm: float, y_mm: float) -> dict:
    authoritative = model._AUTHORITATIVE_PERIMETER_WIRE(
        offset_mm=offset_mm,
        y_mm=y_mm,
    )
    candidate = model._hybrid_perimeter_wire(
        offset_mm=offset_mm,
        y_mm=y_mm,
    )
    authoritative_edges = authoritative.edges()
    candidate_edges = candidate.edges()
    h = model.single.PATH_HALF_SIZE_MM + offset_mm
    bc = model.single.PATH_BOTTOM_CORNER_TANGENCY_MM
    bypass_depth = model.single.SCREW_BYPASS_DEPTH_MM

    retained = []
    removed = []
    for edge in authoritative_edges:
        bounds = edge.bounding_box()
        is_bottom_center_detour = (
            bounds.min.X >= -bc - 1e-6
            and bounds.max.X <= bc + 1e-6
            and bounds.min.Z >= -h - 1e-6
            and bounds.max.Z <= -h + bypass_depth + 1e-6
        )
        (removed if is_bottom_center_detour else retained).append(edge)

    retained_signatures = [_edge_signature(edge) for edge in retained]
    candidate_signatures = [_edge_signature(edge) for edge in candidate_edges]
    retained_match_counts = [
        sum(
            candidate_signature == retained_signature
            for candidate_signature in candidate_signatures
        )
        for retained_signature in retained_signatures
    ]
    unmatched_candidate_edges = [
        candidate_edge
        for candidate_edge, candidate_signature in zip(
            candidate_edges,
            candidate_signatures,
            strict=True,
        )
        if candidate_signature not in retained_signatures
    ]

    if (
        not authoritative.is_closed
        or not candidate.is_closed
        or len(authoritative_edges) != 14
        or len(removed) != 4
        or len(retained) != 10
        or len(candidate_edges) != 11
        or retained_match_counts != [1] * 10
        or len(unmatched_candidate_edges) != 1
    ):
        raise ValueError(
            f"{label} did not preserve the authoritative perimeter topology: "
            f"authoritative={len(authoritative_edges)}, removed={len(removed)}, "
            f"retained={len(retained)}, candidate={len(candidate_edges)}, "
            f"matches={retained_match_counts}, "
            f"unmatched={len(unmatched_candidate_edges)}"
        )

    flat = unmatched_candidate_edges[0]
    bounds = flat.bounding_box()
    if not (
        _near(bounds.min.X, -bc)
        and _near(bounds.max.X, bc)
        and _near(bounds.min.Y, y_mm)
        and _near(bounds.max.Y, y_mm)
        and _near(bounds.min.Z, -h)
        and _near(bounds.max.Z, -h)
        and _near(flat.length, 2.0 * bc)
    ):
        raise ValueError(
            f"{label} flat edge misses authoritative tangencies: "
            f"length={flat.length}, bounds={bounds}"
        )

    return {
        "offset_mm": offset_mm,
        "y_mm": y_mm,
        "authoritative_edge_count": len(authoritative_edges),
        "removed_bottom_detour_edge_count": len(removed),
        "retained_authoritative_edge_count": len(retained),
        "retained_edge_geometry_match_counts": retained_match_counts,
        "edge_signature_rounding_mm": 1e-7,
        "candidate_edge_count": len(candidate_edges),
        "new_flat_edge_count": len(unmatched_candidate_edges),
        "flat_edge_length_mm": flat.length,
        "flat_edge_x_span_mm": [bounds.min.X, bounds.max.X],
        "flat_edge_z_mm": bounds.min.Z,
        "authoritative_closed": authoritative.is_closed,
        "candidate_closed": candidate.is_closed,
    }


def main() -> None:
    half_land = model.SEAL_LAND_WIDTH_MM / 2.0
    half_gasket = model.GASKET_WIDTH_MM / 2.0
    cases = [
        ("nominal", 0.0, model.source.BAFFLE_BED_Y),
        ("land_inner", -half_land, model.source.BAFFLE_BED_Y),
        ("land_outer", half_land, model.source.SHOULDER_Y),
        ("gasket_inner", -half_gasket, model.source.BAFFLE_BED_Y),
        ("gasket_outer", half_gasket, model.source.SHOULDER_Y),
    ]
    diagnostics = {
        label: _validate_case(label, offset_mm, y_mm)
        for label, offset_mm, y_mm in cases
    }
    published = job_output_path(DIAGNOSTICS_PATH)
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
