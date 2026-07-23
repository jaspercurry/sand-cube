"""Generate a separate reduced-volume, German-style compact slot absorber.

This wrapper intentionally leaves the established 68 x 120 mm slotted-bucket
experiment and its build outputs untouched.  It reuses that audited geometry
implementation with a shorter 65 x 80 mm annular body, a 5 mm wall-depth neck,
and slot dimensions recalculated from the compact cavity's actual CAD volume.
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

import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.sand_cube_190x210_port_absorber_slotted_bucket import (
    generate_port_absorber_slotted_bucket as base,
)


OUT = ROOT / "build" / "sand_cube_190x210_port_absorber_slotted_bucket_compact"

D = replace(
    base.D,
    name="sand_cube_190x210_port_absorber_slotted_bucket_compact_v1",
    overall_length=80.0,
    maximum_outer_d=65.0,
    neck_physical_length=5.0,
    # The inherited drilled-hole validation is not acoustically active in the
    # slot variant; one centered placeholder prevents it imposing a tall band.
    holes_per_rail=1,
    pilot_slot_width=0.30,
    pilot_slot_length=4.0,
    nominal_finished_slot_width=0.40,
    witness_slot_widths=(0.40, 0.50, 0.60),
    coupon_slot_widths=(0.30, 0.40, 0.50, 0.60),
)


def main() -> None:
    base.OUT = OUT
    base.D = D
    base.main()


if __name__ == "__main__":
    main()
