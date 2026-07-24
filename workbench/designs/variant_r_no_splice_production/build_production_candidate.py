"""Build the active Variant R composer once for fast topology/visual evidence."""

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

import json
import sys
from pathlib import Path
from typing import Any

from build123d import Compound, import_step

from cad_runner.outputs import job_output_path
from src.enclosure_family.legacy_runtime import (
    LegacyAttributeBinding,
    bind_legacy_attributes,
)
from src.enclosure_family.variant_r.assembly import build_variant_r_joint
from src.enclosure_family.variant_r.export import publish_step_round_trip
from src.enclosure_family.variant_r.inputs import (
    authoritative_base_step,
    producer_attestation_path,
)
from src.enclosure_family.variant_r.provenance import verify_producer_attestation


ROOT = _CAD_SAFETY_ROOT
EXPERIMENT = (
    ROOT
    / "experiments"
    / "sand_cube_190x210_internal_squat_absorber_rear_corners_"
    "parabolic_side_g1_simple_tongue_groove_baffle"
)
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle as model  # noqa: E402
import validate_simple_tongue_groove_baffle as validator  # noqa: E402


OUT = ROOT / "build/workbench/variant_r_no_splice_production/candidate"


class _CapturingFoundation:
    """Delegate to production foundation while retaining its exact donor."""

    def __init__(self) -> None:
        self._delegate = model._LegacyFoundationAdapter()
        self.donor: dict[str, Any] | None = None

    def authoritative_perimeter_wire(
        self,
        *,
        offset_mm: float,
        y_mm: float,
    ) -> Any:
        return self._delegate.authoritative_perimeter_wire(
            offset_mm=offset_mm,
            y_mm=y_mm,
        )

    def build_authoritative_joint(self, full_base: Any) -> dict[str, Any]:
        return self._delegate.build_authoritative_joint(full_base)

    def build_flat_bottom_donor(
        self,
        full_base: Any,
        *,
        perimeter_wire: Any,
    ) -> dict[str, Any]:
        self.donor = dict(
            self._delegate.build_flat_bottom_donor(
                full_base,
                perimeter_wire=perimeter_wire,
            )
        )
        return self.donor


def _publish(filename: str, shape: Any, *, solids: int) -> dict[str, Any]:
    path = OUT / filename
    print(f"candidate: publishing {filename}", flush=True)
    record = publish_step_round_trip(
        path,
        shape,
        require_single_solid=solids == 1,
    )
    if (
        record["source_solid_count"] != solids
        or record["imported_solid_count"] != solids
    ):
        raise ValueError(f"{filename} failed {solids}-solid contract: {record}")
    return record


def main() -> None:
    base_path = authoritative_base_step(ROOT)
    attestation_path = producer_attestation_path(ROOT)
    base_attestation = verify_producer_attestation(
        repo_root=ROOT,
        base_step=base_path,
        attestation_path=attestation_path,
    )
    full_base = model._single_solid(
        import_step(base_path),
        feature="attested production Variant R base",
    )
    foundation = _CapturingFoundation()
    original_gap = model.source.GASKET_CLOSED_GAP_MM
    original_shoulder = model.source.SHOULDER_Y
    bindings = (
        LegacyAttributeBinding(
            model.source,
            "GASKET_CLOSED_GAP_MM",
            model.GASKET_CLOSED_GAP_MM,
        ),
        LegacyAttributeBinding(
            model.source,
            "SHOULDER_Y",
            model.source.BAFFLE_BED_Y + model.GASKET_CLOSED_GAP_MM,
        ),
    )
    with bind_legacy_attributes(bindings):
        common = build_variant_r_joint(
            full_base,
            foundation=foundation,
            single_solid=model._single_solid,
            parameters=model.VARIANT_R_PARAMETERS,
        )
    if foundation.donor is None:
        raise RuntimeError("production foundation did not expose its donor")

    bucket = common["bucket"]
    baffle = common["baffle"]
    gasket = common["gasket"]
    donor_bucket = foundation.donor["bucket"]
    donor_baffle = foundation.donor["baffle"]
    for name, shape in {
        "bucket": bucket,
        "baffle": baffle,
        "gasket": gasket,
        "donor_bucket": donor_bucket,
        "donor_baffle": donor_baffle,
    }.items():
        if len(shape.solids()) != 1 or not shape.is_valid:
            raise ValueError(f"{name} is not one valid solid")

    topology = {
        "bucket": validator._no_splice_topology_audit(
            bucket,
            part_name="bucket",
        ),
        "baffle": validator._no_splice_topology_audit(
            baffle,
            part_name="baffle",
        ),
    }
    contact = validator._baffle_print_contact_audit(baffle)
    outputs = {
        "production_candidate_bucket.step": (bucket, 1),
        "production_candidate_baffle.step": (baffle, 1),
        "production_candidate_gasket.step": (gasket, 1),
        "production_candidate_assembly.step": (
            Compound(children=[bucket, baffle, gasket]),
            3,
        ),
        "continuous_donor_bucket.step": (donor_bucket, 1),
        "continuous_donor_baffle.step": (donor_baffle, 1),
    }
    round_trip = {
        filename: _publish(filename, shape, solids=solids)
        for filename, (shape, solids) in outputs.items()
    }
    diagnostics = {
        "scope": "active production composer fast topology candidate",
        "base_attestation": {
            "cad_job_id": base_attestation["cad_job_id"],
            "sha256": base_attestation["authoritative_base_input"]["sha256"],
        },
        "construction": common["bottom_synthesis"],
        "topology": topology,
        "baffle_print_contact": contact,
        "joint_audit": dict(model.previous._JOINT_AUDIT),
        "source_single_valid_solids": {
            "bucket": True,
            "baffle": True,
            "gasket": True,
        },
        "assembly_source_solid_count": 3,
        "round_trip": round_trip,
        "legacy_state_restored": (
            model.source.GASKET_CLOSED_GAP_MM
            == original_gap
            and model.source.SHOULDER_Y == original_shoulder
        ),
    }
    output = job_output_path(OUT / "candidate_diagnostics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
