# Custom FDM Support Learnings

These notes summarize the practical rules learned while developing custom
print-assist supports for the 220 mm JMLC horn on a Bambu X2D.

## Core Requirements

- Preserve the acoustic surface. Support geometry can touch or approach the
  outside/back side of the horn, but it must not modify the JMLC inner path.
- Use a continuous release interface where finish matters. Sparse point
  contacts are not enough under the rolled lip because the horn can sag between
  supports and leave visible/stringy underside defects.
- Keep the support interface hidden where possible. The best contact zone is
  tucked behind the rolled lip or on the rear flange underside.
- Treat the support as a printed part, not slicer-generated scaffolding. It
  must have printable first layers, stable load paths, and enough contact area
  to resist nozzle drag during the horn build.

## Material Interface

- PLA-to-PETG worked inconsistently for this geometry, especially where the
  support-material contact patch was small or broken into small islands.
- Bambu Support for PLA/PETG is the preferred interface material for the horn
  underside and rear flange support.
- A thin release layer is usually enough in principle, but the model should
  present it as a continuous solid skin so the slicer does not fragment it into
  sparse or hairline paths.
- Dense interface parts should be separate assigned volumes, not painted faces
  on a merged mesh. Separate volumes produced more predictable material usage
  and avoided support-filament bleeding into adjacent PLA regions.

## Geometry Rules

- The support top should be continuous under broad overhangs. Tree-like point
  supports may save material, but they are not appropriate where the visible
  horn surface depends on uniform underside support.
- The support body below the top skin does not need to be solid. Use ribs,
  corrugations, or open bays to reduce sacrificial material.
- A narrow bed footprint is useful for adhesion and removal, but the upper
  support can flare inward as it rises. This keeps the bed contact manageable
  while supporting the rolled-back lip.
- Avoid sudden horizontal ledges in the support itself. If the support flares
  inward, grow it gradually or carry the flare with ribs so the support does
  not need its own support.
- Pointed or teardrop-like openings are more FDM-friendly than semicircular
  arch cutouts because they avoid flat ceilings.
- Keep rib spacing near ordinary FDM bridge limits. Around the horn support,
  roughly 12-16 mm open span between ribs is a reasonable target when the cap
  is only a sacrificial support saddle.

## Current Preferred Pattern

For the next horn support iteration, use:

- A narrow corrugated outer wall at the original footprint.
- Coarser corrugations are usually preferable to many tiny waves. Around this
  horn, 20 waves keeps the wall continuous while avoiding the busy, stop-start
  look of a 40-wave wall.
- A 16 mm inward upper flare so the support reaches the forward/apex region of
  the rolled-back horn.
- Keep the coarser 20-wave outside wall, but use more hidden ribs under the
  inward support cap when the cap would otherwise bridge too far. Alternating
  trough- and peak-anchored ribs gives a 40-rib internal cradle without making
  the exterior corrugation busy again.
- Do not let the inward flare or peak-anchored ribs protrude outside the
  corrugated wall envelope.
- A continuous PLA cap/saddle below the support-material interface.
- A continuous 0.4 mm Bambu Support for PLA/PETG interface skin on top.
- Radial buttress ribs under the cap rather than a solid annular sheet.
- No intermediate horizontal hoops unless slicing or preview shows instability.

This pattern is intended to reduce the large solid sacrificial cradle while
preserving the one thing that matters most for print quality: a continuous,
well-supported interface under the horn.

## Slicing Checks

Before printing, verify:

- The sliced bounding box is still approximately 220 mm across the mouth.
- The support-material skin is assigned to the auxiliary nozzle.
- Prime tower is enabled for two-material reliability.
- The interface skin is dense/continuous, not sparse infill.
- The first layers of the throat/rear flange support are clean and brims do not
  merge into critical acoustic surfaces.
- Any slicer warning about floating cantilevers is understood. For these custom
  supports, Bambu Studio may warn because it sees separate modeled solids
  instead of native generated supports.

## Material Versus Time

Open support geometry can reduce modeled volume without reducing print time.
Many thin ribs create more wall loops, gap fills, and travel moves than a
simpler solid saddle. Treat lattice/ribbed supports as a reliability and
material strategy first, then verify the actual sliced time. If time is the
dominant constraint, compare against a simpler solid cradle in Bambu Studio
instead of assuming the open version will be faster.
