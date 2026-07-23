# Deferred integral-front / bottom-hatch contract

## Status and baseline

This pass inventories and freezes the correct external-package reference only.
It does not fuse the front, remove the seam, add a hatch, rebuild geometry, or
promote a model.

The baseline is the latest surviving full-perimeter nested-seam pair from the
`lightweight_coherent_closure` experiment:

- `centered_captive_nut_bucket.step`;
- `centered_captive_nut_baffle.step`; and
- `centered_captive_nut_assembled.step` as the installed reference.

Unlike the later front-hatch hybrid, this pair retains the sculpted nested seam
and original bottom-corner treatment around the complete perimeter. It does not
transfer a flat print base to the baffle.

## Future requested behavior

Create an independent integral-front enclosure variant whose exterior is the
same as the installed baseline pair, but whose front baffle is permanent and
monolithic with the enclosure. Eliminate the visible joint and remove obsolete
internal removable-baffle machinery. Only after that monolithic package is
validated should one or more bottom-hatch concepts be added.

## External invariants

- Preserve the complete installed exterior surface and silhouette, including
  all four sculpted corners and the entire bottom-corner treatment.
- Preserve the parabolic-G1 front fairing, driver recess and opening, edge
  radii, superellipse sides, rear roll, fill openings/blisters, and nominal
  190 x 210 x 190 mm package.
- The front seam must disappear in the integral version; no exterior groove,
  step, gasket gap, or ghost split may remain.
- Do not borrow the later flat-bottom baffle or hybrid L/R/T-plus-flat-bottom
  seam for this variant.

## Construction rule

Do not merely Boolean-union the exported bucket and baffle. The installed pair
has an intentional gasket/clearance gap and zero hard-part overlap, so a naïve
union may remain disconnected or preserve the wrong internal voids.

Build the integral front semantically from the parameterized pre-split
`full_base`/monocoque geometry, or from an equally explicit source
construction. Remove the nested split, gasket, removable-baffle fasteners, nut
loading slots, and service-joint cavities only after proving which features are
obsolete. Use the baseline STEP pair solely as exact exterior and section
references.

## Future deterministic checks

- One valid connected enclosure solid before the bottom hatch is cut.
- Installed exterior symmetric difference against the baseline assembly is
  zero or within a declared kernel tolerance everywhere outside the future
  bottom-hatch band.
- Exterior bounds and named front-fairing surface measurements are unchanged.
- No remaining external seam or internal gasket/joint void.
- Driver opening, mounting land, fill passages, sand containment, and wall
  thickness remain valid.
- Recalculate net acoustic volume after removing joint hardware/voids and after
  adding the hatch.
- The bottom hatch must preserve the external bottom/corner envelope, seal the
  sand and acoustic volumes independently, and have a real installation and
  fastener path.
- Re-anchor the current port/tube and any floor-mounted structure before
  removing the solid floor region they depend upon.
- Validate bottom-down printability. The approximately 176 mm interior ceiling
  bridge and the current port/floor anchoring are explicit design gates, not
  downstream details.

## Review views

- One isometric showing the complete preserved external package.
- One section through a bottom front corner showing the former front seam, the
  new monolithic wall, the future hatch boundary, and sand/acoustic seals.

## Resume gate and blockers

- Do not start the hatch until the current front-baffle enclosure work has been
  finalized independently.
- Establish and validate the seam-free integral-front baseline before branching
  into alternative hatch designs.
- The hatch position, size, sealing architecture, fastener scheme, print
  support strategy, and port re-anchoring remain open design questions.
