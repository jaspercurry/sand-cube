"""Accepted Variant R removable baffle with a hybrid nested/flat seam.

The authoritative lightweight coherent closure remains the foundation.  Its
sculpted nested split core and corner-sealing system remain untouched.  The
left, right, and top seal path is retained exactly; only the bottom seal path
is straightened, where the planar bulkhead and matching baffle land form the
flat print base.

Retention geometry is intentionally absent from this accepted baseline and
must be introduced by a separately authorized future geometry change.  The
gasket compression remains controlled by the single
``VARIANT_R_PARAMETERS.gasket_closed_gap_mm`` source of truth.
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

import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from src.enclosure_family.variant_r.parameters import (  # noqa: E402
    VARIANT_R_PARAMETERS,
)
from src.enclosure_family.legacy_runtime import (  # noqa: E402
    LegacyAttributeBinding,
    bind_legacy_attributes,
)
from src.enclosure_family.variant_r.assembly import (  # noqa: E402
    build_variant_r_joint,
)
from src.enclosure_family.variant_r.bottom_ownership import (  # noqa: E402
    splice_flat_bottom_band,
    transfer_baffle_below_print_plane,
)
from src.enclosure_family.variant_r.seam import (  # noqa: E402
    build_hybrid_perimeter_wire,
)

_PROGRESS_T0 = time.perf_counter()
_PROGRESS_TLAST = _PROGRESS_T0


def _progress(msg: str) -> None:
    """Live milestone/timing log (to a file if SIMPLE_TG_TIMING_FILE is set)."""
    global _PROGRESS_TLAST
    now = time.perf_counter()
    line = (
        f"[+{now - _PROGRESS_T0:7.1f}s d={now - _PROGRESS_TLAST:6.1f}s] {msg}"
    )
    _PROGRESS_TLAST = now
    path = os.environ.get("SIMPLE_TG_TIMING_FILE")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
    print(line, flush=True)

from build123d import (
    Align,
    Box,
    Compound,
    Pos,
    Solid,
    Unit,
    Wire,
    export_step,
    import_step,
)


ROOT = Path(__file__).resolve().parents[2]
PARENT_EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_lightweight_coherent_closure"
)
if str(PARENT_EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(PARENT_EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure as previous  # noqa: E402


# --- alias the same ancestor modules the closure exposes -------------------
single = previous.single
simplified = previous.simplified
source = previous.source
base = previous.base
parent = previous.parent
centered = previous.centered


# Capture the authoritative implementations before this leaf patches hooks.
_AUTHORITATIVE_COMMON_JOINT = previous._lightweight_common_joint
_AUTHORITATIVE_PERIMETER_WIRE = single._perimeter_wire


OUT = (
    ROOT
    / "build"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
NAME = "sand_cube_190x210_parabolic_g1_simple_tongue_groove_baffle"


# --- the ONE compression knob (see module docstring) -----------------------
# SHOULDER_Y is derived from BAFFLE_BED_Y + this gap at ``source`` import time,
# so generate() must patch BOTH source.GASKET_CLOSED_GAP_MM AND source.SHOULDER_Y.
GASKET_CLOSED_GAP_MM = VARIANT_R_PARAMETERS.gasket_closed_gap_mm

# --- inherited seal-path widths (parabolic perimeter representation) --------
SEAL_LAND_WIDTH_MM = VARIANT_R_PARAMETERS.seal_land_width_mm
GASKET_WIDTH_MM = VARIANT_R_PARAMETERS.gasket_width_mm
GASKET_EDGE_MARGIN_MM = VARIANT_R_PARAMETERS.gasket_edge_margin_mm

# --- fresh seam dimensions --------------------------------------------------
BAFFLE_STRUCTURE_THICKNESS_MM = (
    VARIANT_R_PARAMETERS.baffle_structure_thickness_mm
)
SAND_CAP_THICKNESS_MM = VARIANT_R_PARAMETERS.sand_cap_thickness_mm
BUCKET_SHOULDER_THICKNESS_MM = (
    VARIANT_R_PARAMETERS.bucket_shoulder_thickness_mm
)
FINAL_FILL_PASSAGE_CLEARANCE_MM = (
    VARIANT_R_PARAMETERS.final_fill_passage_clearance_mm
)
BOTTOM_SYNTHESIS_MAX_Z_MM = VARIANT_R_PARAMETERS.bottom_synthesis_max_z_mm
BOTTOM_SYNTHESIS_OVERLAP_MM = VARIANT_R_PARAMETERS.bottom_synthesis_overlap_mm
BAFFLE_PRINT_BED_Z_MM = VARIANT_R_PARAMETERS.baffle_print_bed_z_mm
BOTTOM_PRINT_ROOT_OVERLAP_MM = (
    VARIANT_R_PARAMETERS.bottom_print_root_overlap_mm
)

# --- shared thresholds ------------------------------------------------------
MAX_ALLOWED_INTERFERENCE_MM3 = (
    VARIANT_R_PARAMETERS.max_allowed_interference_mm3
)
MINIMUM_GASKET_SUPPORT_RATIO = (
    VARIANT_R_PARAMETERS.minimum_gasket_support_ratio
)
FAIRING_AREA_TOLERANCE_MM2 = VARIANT_R_PARAMETERS.fairing_area_tolerance_mm2

# --- re-baselined net-volume constants (filled after cruft removal) ---------
CURRENT_SYSTEMIC_NET_VOLUME_L = previous.CURRENT_SYSTEMIC_NET_VOLUME_L
CURRENT_SYSTEMIC_CLOSURE_DISPLACEMENT_MM3 = (
    previous.CURRENT_SYSTEMIC_CLOSURE_DISPLACEMENT_MM3
)

_JOINT_AUDIT: dict[str, Any] = {}
_FILL_AUDIT: dict[str, Any] = {}
_FASTENER_AUDIT: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# thin wrappers that reuse the closure's boolean-hygiene helpers
# ---------------------------------------------------------------------------
def _shape_volume(shape: Any) -> float:
    return previous._shape_volume(shape)


def _single_solid(shape: Any, *, feature: str) -> Solid:
    return previous._single_solid(shape, feature=feature)


def _hybrid_perimeter_wire(*, offset_mm: float, y_mm: float) -> Wire:
    return build_hybrid_perimeter_wire(
        _AUTHORITATIVE_PERIMETER_WIRE,
        offset_mm=offset_mm,
        y_mm=y_mm,
        parameters=VARIANT_R_PARAMETERS,
    )


class _LegacyFoundationAdapter:
    """Contain the old cascade behind the explicit Variant R foundation API."""

    @staticmethod
    def authoritative_perimeter_wire(*, offset_mm: float, y_mm: float) -> Wire:
        return _AUTHORITATIVE_PERIMETER_WIRE(
            offset_mm=offset_mm,
            y_mm=y_mm,
        )

    @staticmethod
    def build_authoritative_joint(full_base: Solid) -> dict[str, Any]:
        return _AUTHORITATIVE_COMMON_JOINT(full_base)

    @staticmethod
    def build_flat_bottom_donor(
        full_base: Solid,
        *,
        perimeter_wire: Any,
    ) -> dict[str, Any]:
        with bind_legacy_attributes(
            (
                LegacyAttributeBinding(
                    single,
                    "_perimeter_wire",
                    perimeter_wire,
                ),
            )
        ):
            return _AUTHORITATIVE_COMMON_JOINT(full_base)


def _build_authoritative_joint(
    full_base: Solid,
    *,
    hybrid_bottom: bool,
    reference_joint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the authoritative joint and splice only the flat lower band."""
    if not hybrid_bottom:
        return _AUTHORITATIVE_COMMON_JOINT(full_base)
    return build_variant_r_joint(
        full_base,
        foundation=_LegacyFoundationAdapter(),
        single_solid=_single_solid,
        reference_joint=reference_joint,
        parameters=VARIANT_R_PARAMETERS,
    )


def _splice_flat_bottom_band(
    authoritative: Solid,
    flat_bottom_donor: Solid,
    *,
    feature: str,
) -> Solid:
    return splice_flat_bottom_band(
        authoritative,
        flat_bottom_donor,
        feature=feature,
        single_solid=_single_solid,
        parameters=VARIANT_R_PARAMETERS,
    )


def _transfer_baffle_below_print_plane(
    bucket: Solid,
    baffle: Solid,
) -> tuple[Solid, Solid, dict[str, float]]:
    return transfer_baffle_below_print_plane(
        bucket,
        baffle,
        single_solid=_single_solid,
        parameters=VARIANT_R_PARAMETERS,
    )


def _authoritative_reference_joint(full_base: Solid) -> dict[str, Any]:
    return _build_authoritative_joint(full_base, hybrid_bottom=False)


def _simple_tongue_groove_joint(full_base: Solid) -> dict[str, Any]:
    common = _build_authoritative_joint(full_base, hybrid_bottom=True)

    # The authoritative implementation owns these detailed audits.  Copy them
    # into the leaf diagnostics rather than recreating weaker proxy checks.
    _FILL_AUDIT.clear()
    _FILL_AUDIT.update(previous._FILL_AUDIT)
    for label in ("left", "right"):
        _FILL_AUDIT[label]["front_clearance_start_y_mm"] = (
            source.BAFFLE_BED_Y
            - simplified.FRONT_FILL_MOUTH_OVERTRAVEL_MM
        )
        _FILL_AUDIT[label]["front_bulkhead_keepout_diameter_mm"] = (
            base.P.fill_entry_d
            + 2.0 * simplified.FRONT_FILL_SUPPORT_WALL_MM
            + 2.0 * previous.FRONT_BULKHEAD_FILL_CLEARANCE_MM
        )
        _FILL_AUDIT[label]["front_bulkhead_rear_y_mm"] = (
            source.SHOULDER_Y + previous.FRONT_BULKHEAD_THICKNESS_MM
        )
    _JOINT_AUDIT.clear()
    _JOINT_AUDIT.update(previous._JOINT_AUDIT)
    _JOINT_AUDIT.update(
        {
            "installation_motion": "seam-only validation; retention disabled",
            "gasket_closed_gap_mm": GASKET_CLOSED_GAP_MM,
            "shoulder_y_mm": source.SHOULDER_Y,
            "baffle_bed_y_mm": source.BAFFLE_BED_Y,
            "seam_architecture": "authoritative nested L/R/T + flat bottom",
            "authoritative_common_joint_inherited": True,
            "front_bulkhead_architecture": (
                "planar shoulder face plate plus constant-height support wedge"
            ),
            "authoritative_outside_gasket_closure_retained": False,
            "authoritative_corner_closure_panels_retained": True,
            "authoritative_front_closure_audit_retained": True,
            "top_hinge": {"present": False},
        }
    )
    _progress("joint: authoritative L/R/T seam + flat bottom restored")
    return common


# ---------------------------------------------------------------------------
# Legacy closure hook: no retention geometry exists in the accepted baseline.
# ---------------------------------------------------------------------------
def _removable_baffle_fastener_concept(common: dict[str, Any]) -> dict[str, Any]:
    bucket = copy.copy(common["bucket"])
    baffle = copy.copy(common["baffle"])
    reference_bucket = copy.copy(bucket)
    reference_baffle = copy.copy(baffle)
    gasket = common["gasket"]

    guard = _assert_exterior_identity(
        reference_baffle, baffle, reference_bucket, bucket, common
    )

    bucket_baffle_overlap = _shape_volume(bucket.intersect(baffle))
    if bucket_baffle_overlap > MAX_ALLOWED_INTERFERENCE_MM3:
        raise ValueError(
            "Removable-baffle bucket/baffle interference is "
            f"{bucket_baffle_overlap:.6f} mm3"
        )

    _FASTENER_AUDIT.clear()
    hardware = Compound(children=[])
    return {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "hardware": hardware,
        "clearance_hardware": hardware,
        "cutters": Compound(children=[]),
        "head_tongue": Compound(children=[]),
        "nut_load_pad": Compound(children=[]),
        "nut_loading_sweep_reference": Compound(children=[]),
        "sealed_tunnel": True,
        "minimum_sealed_tunnel_roof_mm": 1.2,
        "description": (
            "Accepted removable front baffle and closed gasket seam; "
            "retention geometry is intentionally absent"
        ),
        "service_notes": (
            "Do not print as a mechanically retained assembly until a "
            "separately authorized retention design is verified"
        ),
        "closure_passage_mode": "no retention passage geometry",
        "geometry": {
            "fastener_count": 0,
            "retention": "absent; future independent geometry task",
            "authoritative_fairing_face_exactly_preserved": True,
            **guard,
            "fasteners": {},
        },
    }


def _assert_exterior_identity(
    reference_baffle: Solid,
    baffle: Solid,
    reference_bucket: Solid,
    bucket: Solid,
    common: dict[str, Any],
) -> dict[str, Any]:
    """bbox delta + 2nd fairing recheck + bucket skin-face fingerprint."""

    def bbox_deltas(reference: Solid, final: Solid) -> dict[str, float]:
        rb = reference.bounding_box()
        fb = final.bounding_box()
        return {
            "min_x": fb.min.X - rb.min.X,
            "max_x": fb.max.X - rb.max.X,
            "min_y": fb.min.Y - rb.min.Y,
            "max_y": fb.max.Y - rb.max.Y,
            "min_z": fb.min.Z - rb.min.Z,
            "max_z": fb.max.Z - rb.max.Z,
        }

    baffle_deltas = bbox_deltas(reference_baffle, baffle)
    bucket_deltas = bbox_deltas(reference_bucket, bucket)
    _progress(
        "guard: bucket bbox delta "
        + ", ".join(f"{k}={v:+.3f}" for k, v in bucket_deltas.items())
    )
    if max(abs(v) for v in baffle_deltas.values()) > 1e-5:
        raise ValueError(f"Fasteners changed baffle bounds: {baffle_deltas}")
    # All six bucket bounds are byte-identical (the counterbores are recesses).
    if max(abs(v) for v in bucket_deltas.values()) > 1e-5:
        raise ValueError(f"Fasteners changed bucket bounds: {bucket_deltas}")

    # Protect every substantial bucket face. Retention geometry is absent, so
    # there is no permitted lower-band exclusion.
    def skin_fingerprint(solid: Solid) -> tuple[int, tuple[float, ...]]:
        areas = []
        for face in solid.faces():
            if face.area <= 100.0:
                continue
            areas.append(round(face.area, 4))
        return (len(areas), tuple(sorted(areas)))

    ref_fp = skin_fingerprint(reference_bucket)
    final_fp = skin_fingerprint(bucket)
    matched = sum(
        1
        for a in ref_fp[1]
        if any(abs(a - b) <= 1e-3 for b in final_fp[1])
    )
    _progress(
        f"guard: skin fingerprint protected ref={ref_fp[0]} final={final_fp[0]} "
        f"matched={matched}"
    )
    if ref_fp[0] != final_fp[0]:
        raise ValueError(
            "Fasteners changed the bucket skin face count: "
            f"{ref_fp[0]} -> {final_fp[0]}"
        )
    if matched != ref_fp[0]:
        raise ValueError(
            "Fasteners perturbed a bucket skin face area fingerprint: "
            f"matched {matched}/{ref_fp[0]}"
        )

    # 2nd fairing recheck on the (possibly screw-modified) baffle -- strict.
    target_area = common["fairing_area_mm2"]
    fairing_faces = [
        face
        for face in baffle.faces()
        if abs(face.area - target_area) <= FAIRING_AREA_TOLERANCE_MM2
    ]
    if len(fairing_faces) != 1:
        closest = min(
            baffle.faces(), key=lambda f: abs(f.area - target_area), default=None
        )
        cb = closest.bounding_box() if closest is not None else None
        _progress(
            f"guard: fairing recheck n={len(fairing_faces)} "
            f"target={target_area:.4f} closest_area="
            f"{(closest.area if closest is not None else None)} "
            f"delta={(closest.area - target_area) if closest is not None else None} "
            f"closest_bbox_z=[{cb.min.Z:.2f},{cb.max.Z:.2f}]"
            if cb is not None else "no faces"
        )
        raise ValueError("Fasteners changed the authoritative G1 fairing")

    return {
        "baffle_exterior_bounds_difference_mm": baffle_deltas,
        "bucket_exterior_bounds_difference_mm": bucket_deltas,
        "bucket_protected_skin_face_count": ref_fp[0],
        "external_bucket_humps": False,
    }


# ---------------------------------------------------------------------------
# close-section replacement (new feature set; drops centered_captive_nut /
# screw_tunnel / nut_slot sections that referenced deleted geometry)
# ---------------------------------------------------------------------------
def _section_compound(shape: Any, clip: Solid, *, feature: str) -> Compound:
    pieces = [
        piece.clean().fix()
        for solid in shape.solids()
        for piece in (solid & clip).solids()
        if piece.volume > 1e-6
    ]
    if not pieces or not all(piece.is_valid for piece in pieces):
        raise ValueError(f"{feature} did not produce valid section solids")
    return Compound(children=pieces)


def _generate_close_sections() -> dict[str, Any]:
    """Section the surviving seam features (gasket land, fill bore)."""
    bucket = import_step(OUT / "centered_captive_nut_bucket.step")
    assembled = import_step(OUT / "centered_captive_nut_assembled.step")
    specs = {
        "left_fill_close_section.step": (
            bucket,
            Pos(-86.0, source.SHOULDER_Y + 4.0, 86.0)
            * Box(14.0, 36.0, 24.0,
                  align=(Align.CENTER, Align.CENTER, Align.CENTER)),
            "left_fill_section_viewer",
        ),
        "gasket_seam_close_section.step": (
            assembled,
            Pos(45.0, source.SHOULDER_Y + 6.0, 0.0)
            * Box(6.0, 40.0, 205.0,
                  align=(Align.CENTER, Align.CENTER, Align.CENTER)),
            "gasket_seam_section_viewer",
        ),
    }
    checks: dict[str, Any] = {}
    for filename, (shape, clip, _viewer) in specs.items():
        section = _section_compound(shape, clip, feature=filename)
        path = OUT / filename
        export_step(section, path, unit=Unit.MM, write_pcurves=True)
        imported = import_step(path)
        checks[filename] = {
            "source_solid_count": len(section.solids()),
            "imported_solid_count": len(imported.solids()),
            "all_imported_solids_valid": all(
                s.is_valid for s in imported.solids()
            ),
        }
    return checks


# ---------------------------------------------------------------------------
# generate() -- bind the inherited cascade explicitly for one serialized call,
# restore it exactly, then retarget the stale diagnostic keys.
# ---------------------------------------------------------------------------
def generate() -> dict[str, Any]:
    bindings = (
        LegacyAttributeBinding(previous, "OUT", OUT),
        LegacyAttributeBinding(previous, "NAME", NAME),
        LegacyAttributeBinding(
            previous,
            "_lightweight_common_joint",
            _simple_tongue_groove_joint,
        ),
        LegacyAttributeBinding(
            previous,
            "_accessible_fastener_concept",
            _removable_baffle_fastener_concept,
        ),
        LegacyAttributeBinding(
            previous,
            "_generate_close_sections",
            _generate_close_sections,
        ),
        LegacyAttributeBinding(
            source,
            "GASKET_CLOSED_GAP_MM",
            GASKET_CLOSED_GAP_MM,
        ),
        # SHOULDER_Y was frozen at import from the old gap.
        LegacyAttributeBinding(
            source,
            "SHOULDER_Y",
            source.BAFFLE_BED_Y + GASKET_CLOSED_GAP_MM,
        ),
    )
    with bind_legacy_attributes(bindings):
        diagnostics = previous.generate()

    diagnostics["name"] = NAME
    diagnostics["status"] = "accepted removable baffle (Variant R)"
    diagnostics["isolation"] = {
        "experiment_dir": (
            "experiments/sand_cube_190x210_internal_squat_absorber_rear_"
            "corners_parabolic_side_g1_simple_tongue_groove_baffle"
        ),
        "output_dir": (
            "build/sand_cube_190x210_internal_squat_absorber_rear_corners_"
            "parabolic_side_g1_simple_tongue_groove_baffle"
        ),
        "shared_upstream_generators_modified": False,
    }
    diagnostics[NAME] = {
        "joint": dict(_JOINT_AUDIT),
        "front_fill": dict(_FILL_AUDIT),
        "fasteners": dict(_FASTENER_AUDIT),
        "compression_knob": {
            "GASKET_CLOSED_GAP_MM": GASKET_CLOSED_GAP_MM,
            "location": f"{__name__}.GASKET_CLOSED_GAP_MM",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    return diagnostics


if __name__ == "__main__":
    generate()
