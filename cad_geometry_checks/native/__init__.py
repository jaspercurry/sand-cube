"""Explicit boundary for native-object geometry measurements.

Importing this module does not itself initialize Build123d or OCP.  Constructing
real CAD objects and calling these functions must happen inside ``cad_runner``.
"""

from .measurements import (
    compare_protected_material,
    compare_protected_surfaces,
    measure_difference,
    measure_edge_continuity,
    measure_intersection,
    measure_normal_change,
    measure_print_bed_contact,
    measure_volume,
    normalize_shapes,
    normalize_solids,
    sample_edge_signatures,
    summarize_topology,
)


__all__ = [
    "compare_protected_material",
    "compare_protected_surfaces",
    "measure_difference",
    "measure_edge_continuity",
    "measure_intersection",
    "measure_normal_change",
    "measure_print_bed_contact",
    "measure_volume",
    "normalize_shapes",
    "normalize_solids",
    "sample_edge_signatures",
    "summarize_topology",
]
