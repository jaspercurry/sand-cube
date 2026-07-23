"""Authoritative joint-coupon contract and native-free provenance helpers."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Iterable

from cad_verification import (
    CheckKind,
    CheckSpec,
    DesignContract,
    Expectation,
    Fingerprint,
    ModelIdentity,
    Requirement,
    Tolerance,
    Unit,
    VerificationProfile,
)
from workbench.designs.joint_coupon.parameters import (
    CouponParameters,
    expected_volumes,
)


ROOT = Path(__file__).resolve().parents[3]
DESIGN_ROOT = Path(__file__).resolve().parent
SOURCE_PATHS = (
    DESIGN_ROOT / "parameters.py",
    DESIGN_ROOT / "model.py",
    DESIGN_ROOT / "verification.py",
    DESIGN_ROOT / "build.py",
    DESIGN_ROOT / "packet.py",
)
INPUT_PATHS = (DESIGN_ROOT / "params.json",)


def _requirement(
    requirement_id: str,
    description: str,
    kind: CheckKind,
    adapter: str,
    expected: bool | int | float,
    unit: Unit,
    tolerance: float,
    profile: VerificationProfile,
) -> Requirement:
    return Requirement(
        requirement_id=requirement_id,
        description=description,
        check=CheckSpec(kind, adapter),
        expectation=Expectation.exactly(expected),
        unit=unit,
        tolerance=Tolerance(tolerance),
        cost_profile=profile,
    )


def design_contract(params: CouponParameters) -> DesignContract:
    """Return the one contract shared by fast, fit, and release evidence."""

    volumes = expected_volumes(params)
    assembly_height = params.lower_thickness + params.closed_gap + params.upper_thickness
    vertical_clearance = (
        params.upper_underside_z
        + params.groove_depth
        - (params.lower_thickness + params.tongue_height)
    )
    requirements = (
        _requirement("JC-STRUCT-PARAMETERS-FINITE", "Every coupon parameter is finite and positive where required.", CheckKind.STRUCTURAL, "analytic.parameters_finite", True, Unit.BOOLEAN, 0.0, VerificationProfile.FAST),
        _requirement("JC-STRUCT-LAYOUT-FEASIBLE", "Tongue, groove, gasket, and fastener layout fits within the coupon plates.", CheckKind.STRUCTURAL, "analytic.layout_feasible", True, Unit.BOOLEAN, 0.0, VerificationProfile.FAST),
        _requirement("JC-DIM-NOMINAL-LENGTH", "Nominal assembly length is available before native CAD.", CheckKind.DIMENSION, "analytic.assembly_length", params.length, Unit.MILLIMETER, 1e-6, VerificationProfile.FAST),
        _requirement("JC-DIM-NOMINAL-DEPTH", "Nominal assembly depth is available before native CAD.", CheckKind.DIMENSION, "analytic.assembly_depth", params.depth, Unit.MILLIMETER, 1e-6, VerificationProfile.FAST),
        _requirement("JC-DIM-NOMINAL-HEIGHT", "Nominal closed height includes the plate gap.", CheckKind.DIMENSION, "analytic.assembly_height", assembly_height, Unit.MILLIMETER, 1e-6, VerificationProfile.FAST),
        _requirement("JC-DIM-ANALYTIC-LOWER-VOLUME", "Analytic lower volume is finite and positive.", CheckKind.DIMENSION, "analytic.lower_volume", volumes["lower"], Unit.CUBIC_MILLIMETER, 1e-4, VerificationProfile.FAST),
        _requirement("JC-DIM-ANALYTIC-UPPER-VOLUME", "Analytic upper volume is finite and positive.", CheckKind.DIMENSION, "analytic.upper_volume", volumes["upper"], Unit.CUBIC_MILLIMETER, 1e-4, VerificationProfile.FAST),
        _requirement("JC-DIM-ANALYTIC-GASKET-VOLUME", "Analytic compressed gasket volume is finite and positive.", CheckKind.DIMENSION, "analytic.gasket_volume", volumes["gasket_each"], Unit.CUBIC_MILLIMETER, 1e-5, VerificationProfile.FAST),
        _requirement("JC-STRUCT-LOWER-VALID", "Lower rigid coupon is valid.", CheckKind.STRUCTURAL, "kernel.lower_valid", True, Unit.BOOLEAN, 0.0, VerificationProfile.FIT),
        _requirement("JC-STRUCT-UPPER-VALID", "Upper rigid coupon is valid.", CheckKind.STRUCTURAL, "kernel.upper_valid", True, Unit.BOOLEAN, 0.0, VerificationProfile.FIT),
        _requirement("JC-STRUCT-LOWER-SOLID-COUNT", "Lower coupon remains one printable solid.", CheckKind.STRUCTURAL, "kernel.lower_solid_count", 1, Unit.COUNT, 0.0, VerificationProfile.FIT),
        _requirement("JC-STRUCT-UPPER-SOLID-COUNT", "Upper coupon remains one printable solid.", CheckKind.STRUCTURAL, "kernel.upper_solid_count", 1, Unit.COUNT, 0.0, VerificationProfile.FIT),
        _requirement("JC-DIM-ASSEMBLY-LENGTH", "Built assembly length matches the parameter input.", CheckKind.DIMENSION, "kernel.assembly_length", params.length, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-DIM-ASSEMBLY-DEPTH", "Built assembly depth matches the parameter input.", CheckKind.DIMENSION, "kernel.assembly_depth", params.depth, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-DIM-ASSEMBLY-HEIGHT", "Built assembly height includes the intended plate gap.", CheckKind.DIMENSION, "kernel.assembly_height", assembly_height, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-DIM-LOWER-VOLUME", "Built lower volume matches its analytic expectation.", CheckKind.DIMENSION, "kernel.lower_volume", volumes["lower"], Unit.CUBIC_MILLIMETER, 1e-4, VerificationProfile.FIT),
        _requirement("JC-DIM-UPPER-VOLUME", "Built upper volume matches its analytic expectation.", CheckKind.DIMENSION, "kernel.upper_volume", volumes["upper"], Unit.CUBIC_MILLIMETER, 1e-4, VerificationProfile.FIT),
        _requirement("JC-DIM-GASKET-LEFT-VOLUME", "Built left gasket reference matches its analytic expectation.", CheckKind.DIMENSION, "kernel.left_gasket_volume", volumes["gasket_each"], Unit.CUBIC_MILLIMETER, 1e-5, VerificationProfile.FIT),
        _requirement("JC-DIM-GASKET-RIGHT-VOLUME", "Built right gasket reference matches its analytic expectation.", CheckKind.DIMENSION, "kernel.right_gasket_volume", volumes["gasket_each"], Unit.CUBIC_MILLIMETER, 1e-5, VerificationProfile.FIT),
        _requirement("JC-CLEAR-SIDE", "Tongue-to-groove side clearance is preserved per side.", CheckKind.CLEARANCE, "kernel.side_clearance", params.groove_side_clearance, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-CLEAR-END", "Tongue-to-groove end clearance is preserved per end.", CheckKind.CLEARANCE, "kernel.end_clearance", params.groove_end_clearance, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-FIT-GASKET-COMPRESSION", "Gasket compression at closure matches the input contract.", CheckKind.FIT, "kernel.gasket_compression", params.gasket_compression, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-INTERFERENCE-RIGID", "Closed rigid parts have no positive-volume interference.", CheckKind.INTERFERENCE, "kernel.rigid_interference", 0.0, Unit.CUBIC_MILLIMETER, 1e-7, VerificationProfile.FIT),
        _requirement("JC-INTERFERENCE-GASKET", "Compressed gasket references do not penetrate rigid parts.", CheckKind.INTERFERENCE, "kernel.gasket_interference", 0.0, Unit.CUBIC_MILLIMETER, 1e-7, VerificationProfile.FIT),
        _requirement("JC-SECTION-VERTICAL-CLEARANCE", "The mid-plane tongue-to-groove ceiling clearance is preserved.", CheckKind.SECTION, "kernel.joint_section_clearance", vertical_clearance, Unit.MILLIMETER, 1e-6, VerificationProfile.FIT),
        _requirement("JC-ROUNDTRIP-VALID", "The assembly STEP round-trips as valid geometry.", CheckKind.ROUND_TRIP, "artifact.assembly_valid", True, Unit.BOOLEAN, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-SOLID-COUNT", "The assembly STEP retains both rigid solids.", CheckKind.ROUND_TRIP, "artifact.assembly_solid_count", 2, Unit.COUNT, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-VOLUME", "The assembly STEP retains total rigid volume.", CheckKind.ROUND_TRIP, "artifact.assembly_volume", volumes["lower"] + volumes["upper"], Unit.CUBIC_MILLIMETER, 1e-3, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-LOWER-SOLID-COUNT", "The lower STEP remains one solid.", CheckKind.ROUND_TRIP, "artifact.lower_solid_count", 1, Unit.COUNT, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-LOWER-VOLUME", "The lower STEP retains rigid volume.", CheckKind.ROUND_TRIP, "artifact.lower_volume", volumes["lower"], Unit.CUBIC_MILLIMETER, 1e-3, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-UPPER-SOLID-COUNT", "The upper STEP remains one solid.", CheckKind.ROUND_TRIP, "artifact.upper_solid_count", 1, Unit.COUNT, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-ROUNDTRIP-UPPER-VOLUME", "The upper STEP retains rigid volume.", CheckKind.ROUND_TRIP, "artifact.upper_volume", volumes["upper"], Unit.CUBIC_MILLIMETER, 1e-3, VerificationProfile.RELEASE),
        _requirement("JC-ARTIFACT-SIDECAR", "The topology sidecar is hash-bound to the assembly STEP.", CheckKind.ARTIFACT_INTEGRITY, "artifact.sidecar_hash_binding", True, Unit.BOOLEAN, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-VIS-VIEWER", "A read-only Viewer link exposes the exact assembly STEP.", CheckKind.VISUAL_REVIEW, "review.viewer_ready", True, Unit.BOOLEAN, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-VIS-SNAPSHOT-ISO", "The agent inspected an isometric Snapshot of the exact STEP and sidecar.", CheckKind.VISUAL_REVIEW, "review.snapshot_isometric", True, Unit.BOOLEAN, 0.0, VerificationProfile.RELEASE),
        _requirement("JC-VIS-SNAPSHOT-SECTION", "The agent inspected a joint-section Snapshot of the exact STEP and sidecar.", CheckKind.VISUAL_REVIEW, "review.snapshot_section", True, Unit.BOOLEAN, 0.0, VerificationProfile.RELEASE),
    )
    return DesignContract(
        contract_id="contract.joint-coupon",
        title="Cataloged joint-coupon staged verification",
        model=ModelIdentity(
            model_id="joint-coupon",
            name="Workbench gasket and joint coupon",
            variant="cataloged-workbench-proof",
            source="workbench/designs/joint_coupon/model.py",
            entrypoint="workbench/designs/joint_coupon/build.py",
        ),
        requirements=requirements,
    )


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprints(paths: Iterable[Path]) -> tuple[Fingerprint, ...]:
    return tuple(
        Fingerprint(str(path.resolve().relative_to(ROOT)), sha256_file(path))
        for path in paths
    )


def source_fingerprints() -> tuple[Fingerprint, ...]:
    return fingerprints(SOURCE_PATHS)


def input_fingerprints() -> tuple[Fingerprint, ...]:
    return fingerprints(INPUT_PATHS)
