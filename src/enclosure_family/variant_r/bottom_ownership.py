"""Variant R lower-band splice and accepted print-edge material ownership."""

from __future__ import annotations

from collections.abc import Callable

from build123d import Align, Box, Pos, Solid

from .parameters import VARIANT_R_PARAMETERS, VariantRParameters


SingleSolid = Callable[..., Solid]


def _clip_for_pair(
    left: Solid,
    right: Solid,
    z_min_mm: float,
    z_max_mm: float,
) -> Solid:
    left_bounds = left.bounding_box()
    right_bounds = right.bounding_box()
    min_x = min(left_bounds.min.X, right_bounds.min.X) - 1.0
    max_x = max(left_bounds.max.X, right_bounds.max.X) + 1.0
    min_y = min(left_bounds.min.Y, right_bounds.min.Y) - 1.0
    max_y = max(left_bounds.max.Y, right_bounds.max.Y) + 1.0
    return Pos(
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (z_min_mm + z_max_mm) / 2.0,
    ) * Box(
        max_x - min_x,
        max_y - min_y,
        z_max_mm - z_min_mm,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )


def splice_flat_bottom_band(
    authoritative: Solid,
    flat_bottom_donor: Solid,
    *,
    feature: str,
    single_solid: SingleSolid,
    parameters: VariantRParameters = VARIANT_R_PARAMETERS,
) -> Solid:
    """Join the accepted authoritative upper solid to the donor lower band."""

    reference_bounds = authoritative.bounding_box()
    donor_bounds = flat_bottom_donor.bounding_box()
    min_z = min(reference_bounds.min.Z, donor_bounds.min.Z) - 1.0
    max_z = max(reference_bounds.max.Z, donor_bounds.max.Z) + 1.0
    half_overlap = parameters.bottom_synthesis_overlap_mm / 2.0
    upper_clip = _clip_for_pair(
        authoritative,
        flat_bottom_donor,
        parameters.bottom_synthesis_max_z_mm - half_overlap,
        max_z,
    )
    lower_clip = _clip_for_pair(
        authoritative,
        flat_bottom_donor,
        min_z,
        parameters.bottom_synthesis_max_z_mm + half_overlap,
    )
    upper_parts = [
        solid.clean().fix()
        for solid in (authoritative & upper_clip).solids()
        if solid.volume > 1e-6
    ]
    lower_parts = [
        solid.clean().fix()
        for solid in (flat_bottom_donor & lower_clip).solids()
        if solid.volume > 1e-6
    ]
    if (
        not upper_parts
        or not lower_parts
        or not all(solid.is_valid for solid in [*upper_parts, *lower_parts])
    ):
        raise ValueError(
            f"{feature} did not produce valid splice pieces: "
            f"upper={len(upper_parts)}, lower={len(lower_parts)}"
        )
    return single_solid(
        upper_parts[0]
        .fuse(*upper_parts[1:], *lower_parts)
        .clean()
        .fix(),
        feature=feature,
    )


def transfer_baffle_below_print_plane(
    bucket: Solid,
    baffle: Solid,
    *,
    single_solid: SingleSolid,
    parameters: VariantRParameters = VARIANT_R_PARAMETERS,
) -> tuple[Solid, Solid, dict[str, float]]:
    """Preserve the accepted imperfect lower print-edge material relationship."""

    bucket_bounds = bucket.bounding_box()
    baffle_bounds = baffle.bounding_box()
    min_z = min(bucket_bounds.min.Z, baffle_bounds.min.Z) - 1.0
    max_z = max(bucket_bounds.max.Z, baffle_bounds.max.Z) + 1.0
    lower_clip = _clip_for_pair(
        bucket,
        baffle,
        min_z,
        parameters.baffle_print_bed_z_mm,
    )
    upper_clip = _clip_for_pair(
        bucket,
        baffle,
        parameters.baffle_print_bed_z_mm,
        max_z,
    )
    transfer = single_solid(
        (baffle & lower_clip).clean().fix(),
        feature="baffle remnants below the print plane",
    )
    printable_baffle = single_solid(
        (baffle & upper_clip).clean().fix(),
        feature="baffle terminating on the planar print contact",
    )
    lower_seam_root_depth = (
        parameters.gasket_closed_gap_mm
        + parameters.bottom_print_root_overlap_mm
    )
    rearward_transfer = Pos(0.0, lower_seam_root_depth, 0.0) * transfer
    receiving_bucket = single_solid(
        bucket.fuse(rearward_transfer).clean().fix(),
        feature="bucket with overlapping lower print-edge root",
    )
    receiving_bucket = single_solid(
        receiving_bucket.fuse(transfer).clean().fix(),
        feature="bucket with complementary lower print-edge material",
    )
    return receiving_bucket, printable_baffle, {
        "bed_z_mm": parameters.baffle_print_bed_z_mm,
        "transferred_volume_mm3": transfer.volume,
        "lower_seam_root_depth_mm": lower_seam_root_depth,
        "lower_seam_root_overlap_mm": (
            parameters.bottom_print_root_overlap_mm
        ),
        "original_baffle_volume_mm3": baffle.volume,
        "printable_baffle_volume_mm3": printable_baffle.volume,
        "receiving_bucket_volume_mm3": receiving_bucket.volume,
    }
