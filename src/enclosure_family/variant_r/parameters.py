"""Native-CAD-free parameters and verification policies for Variant R."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class VariantRParameters:
    """Accepted removable-baffle dimensions in design-coordinate millimetres."""

    gasket_closed_gap_mm: float = 1.0
    path_half_size_mm: float = 88.125
    path_bottom_corner_tangency_mm: float = 73.0
    screw_bypass_depth_mm: float = 4.0
    seal_land_width_mm: float = 6.75
    gasket_width_mm: float = 5.0
    baffle_structure_thickness_mm: float = 3.0
    sand_cap_thickness_mm: float = 3.0
    bucket_shoulder_thickness_mm: float = 3.0
    final_fill_passage_clearance_mm: float = 0.05
    bottom_synthesis_max_z_mm: float = -80.0
    bottom_synthesis_overlap_mm: float = 0.20
    bottom_print_root_overlap_mm: float = 0.20
    max_allowed_interference_mm3: float = 0.01
    minimum_gasket_support_ratio: float = 0.985
    fairing_area_tolerance_mm2: float = 1e-5

    def __post_init__(self) -> None:
        positive = (
            self.gasket_closed_gap_mm,
            self.path_half_size_mm,
            self.path_bottom_corner_tangency_mm,
            self.screw_bypass_depth_mm,
            self.seal_land_width_mm,
            self.gasket_width_mm,
            self.baffle_structure_thickness_mm,
            self.sand_cap_thickness_mm,
            self.bucket_shoulder_thickness_mm,
            self.final_fill_passage_clearance_mm,
            self.bottom_synthesis_overlap_mm,
            self.bottom_print_root_overlap_mm,
            self.max_allowed_interference_mm3,
            self.fairing_area_tolerance_mm2,
        )
        if min(positive) <= 0.0:
            raise ValueError("Variant R dimensions and tolerances must be positive")
        if self.gasket_width_mm >= self.seal_land_width_mm:
            raise ValueError("gasket must fit inside the seal land")
        if not 0.0 < self.minimum_gasket_support_ratio <= 1.0:
            raise ValueError("gasket support ratio must be in (0, 1]")

    @property
    def gasket_edge_margin_mm(self) -> float:
        return (self.seal_land_width_mm - self.gasket_width_mm) / 2.0

    @property
    def baffle_print_bed_z_mm(self) -> float:
        return -(self.path_half_size_mm + self.seal_land_width_mm / 2.0)


VARIANT_R_PARAMETERS: Final = VariantRParameters()
