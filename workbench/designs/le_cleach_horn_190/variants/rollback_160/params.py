"""Parameters for the separate 160-degree rollback comparison."""

from __future__ import annotations

from dataclasses import replace

from workbench.designs.le_cleach_horn_190.variants.rollback_140.params import (
    PARAMS_140,
)


# This input is calibrated independently because the rolled-back wall reaches
# its maximum physical radius before the acoustic terminal point. It is not a
# uniform scale factor and does not alter the frozen 82.382 mm axial length.
PROFILE_MOUTH_OUTER_D_INPUT_160 = 191.138682846249

PARAMS_160 = replace(
    PARAMS_140,
    exit_angle_deg=160.0,
    profile_mouth_outer_d_input=PROFILE_MOUTH_OUTER_D_INPUT_160,
)
