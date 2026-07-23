# Source-lineage boundaries

This map intentionally links leaf owners instead of copying their code. The
enclosure source is not atomic yet: the current generators patch and import a
deep experiment chain. Moving a leaf by itself would break imports; copying
the chain would create a second, ambiguous source of truth.

## Removable-baffle and full-perimeter closure family

The active leaf is:

```text
simple_tongue_groove_baffle
  -> lightweight_coherent_closure
    -> systemic_joint_recessed_fasteners
      -> single_land_corner_fasteners
        -> simplified_printable_closure
          -> front_fill_perimeter_seal
            -> dual_captive_square_nut_printable
              -> forward_captive_square_nut
                -> centered_captive_nut
                  -> nested_seam_closure_concepts
                    -> hooked_gasketed_baffle
                      -> printable_bucket
                        -> conformal_full_system
```

`conformal_full_system` then combines the rear-corner enclosure/port lineage
with the conformal shell/front-profile lineage. This is why the working set
links the active leaf, the full-perimeter owner, and the nested-seam ancestor
but does not relocate them.

The future integral-front branch begins from the monolithic `full_base` before
`_lightweight_common_joint(full_base)` splits it. It must become a new owner,
not a mutation of the removable-baffle leaf.

## Bass-reflex tube lineage

```text
single_oval_port
  -> header_port
    -> serviceable_tower
      -> internal_squat_absorber
        -> internal_squat_absorber_flush
          -> internal_squat_absorber_rear_corners
```

The rear-corner generator is the present route owner. The whole chain remains
important because the leaf delegates geometry and service interfaces to its
ancestors.

## Resonator lineage

Rev D is independently versioned but imports the Rev C generator plus its
`model.py` and `duct.py`. Rev C remains the current enclosure-placement
reference; Rev D remains the latest acoustic/calibration reference. Neither
may silently replace the other.

## Horn lineage

`src/final_horn.py` is the stable public API. It calls
`src/features/horn.py`, which contains both the legacy JMLC recurrence and an
explicit reproduction of the 2007 Le Cleac'h workbook recurrence. Horn
parameters currently live in the shared root `params.py`; only the horn fields
are relevant to the future smaller horn.
