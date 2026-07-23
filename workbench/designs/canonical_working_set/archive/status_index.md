# Practical model-status index

## Active working surface

| Catalog record | Role |
|---|---|
| `development-190x210-tongue-groove` | Current removable-baffle development model; not accepted final geometry |
| `exp-190x210-simple-tongue-groove` | Active leaf experiment for the removable-front variant |
| `exp-190x210-lightweight-coherent-closure` | Supporting full-perimeter owner and integral-front external baseline |
| `exp-190x210-rear-corners` | Supporting tube route owner, deferred |
| `exp-190x210-port-absorber-d-squat` | Rev C placement/mechanical study, deferred |
| `exp-190x210-port-absorber-d-squat-rev-d` | Latest acoustic/calibration study, deferred |
| `final-jmlc-horn` | Stable current large horn used only as the future smaller-horn source reference |

## Supporting dependency chain — keep in place

- `exp-190x210-conformal-full-system`
- `exp-190x210-printable-bucket`
- `exp-190x210-simplified-printable-closure`
- `exp-190x210-single-land-fasteners`
- `exp-190x210-systemic-recessed-fasteners`
- the single-oval, header, serviceable-tower, internal-absorber, and
  rear-flush tube ancestors

These are not part of the day-to-day design surface, but active sources import
them.

## Historical closure variants — provenance only

- centered captive-nut closure;
- corner-fill curved-gasket closure;
- dual captive square-nut printable closure;
- forward captive square-nut closure;
- front-fill perimeter-seal closure;
- hooked gasketed baffle; and
- nested-seam closure concepts.

The catalog marks these historical. Some still sit inside the active import
chain, especially the nested-seam source, so “historical” is not permission to
delete them.

## Frozen or rejected references

- `releases/enclosure_v1/front_baffle/` is a frozen release and superseded as
  the new removable-baffle development baseline.
- `front_component_removed_candidate_viewer` deleted wanted seating geometry.
- `deleted_face_plate_candidate_viewer` failed gasket and sand-cap requirements
  and did not remove the real inherited hunks.
- `clean_corner_hunks_candidate_viewer` is retained because its bucket is the
  current visual/geometry target, but it remains an unpromoted STEP-derived
  reference with incorrect bottom ownership.

## Other studies

All remaining cataloged front-profile, enclosure-wall, port, absorber,
materials, compact-system, and legacy 200/203 mm models remain available for
research or regeneration but are outside this 190 × 210 working set. Consult
`.cad-project/models.toml` rather than guessing from directory names.
