# 140° rollback variant contract

## Baseline

- Enclosure and support context:
  `experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py`.
- Existing exact-profile horn artifact:
  `build/sand_cube_190x210_single_oval_port/sand_cube_190x210_single_oval_port_horn.step`.
- Exact recurrence and solid construction:
  `src/features/horn.py`, using `profile_method="le_cleach_2007"`.
- The active package is 190 mm wide, 190 mm high, and 210 mm deep. Its front
  face is the requested 190 mm square.

## Requested change

Create a standalone, parameterized Le Cléac'h horn candidate with:

- a 190.000 mm maximum physical rolled envelope;
- the exact Le Cléac'h 2007 spreadsheet recurrence;
- the existing exact-profile acoustic axial length retained for now;
- an explicit target-length solver so a later length revision requires changing
  one parameter rather than hand-pinning a new wavefront factor.

## Reversible assumptions

- “Keep the length as is” means retain the exact-profile horn used by the
  190-by-190-by-210 bass-reflex study: 82.38213681735276 mm acoustic axial
  length.
- Retain the B&C DE250 acoustic and horn-side mounting inputs from that study:
  25.4 mm modeled throat, 8 degree throat half-angle, 140 degree terminal
  rollback, 3.2 mm wall, 8 mm flange, 4 mm by 38 mm rear spigot, and only the
  two-hole 76 mm BCD pattern.
- Keep the already calibrated 192.5299283 mm profile mouth input that produces
  the 190.000 mm physical rolled envelope. Do not uniformly scale the horn.
- Driver, port-tower, and horn placement are intentionally deferred. This
  checkpoint proves the standalone horn and exposes the axial-length input; it
  does not freeze the compression-driver setback.

## Invariants and checks

- One valid solid before and after STEP round-trip.
- Maximum physical X/Y envelope: 190.000 mm within 0.01 mm.
- Acoustic axial length: target within 0.001 mm.
- Acoustic mouth inner diameter: 186.130 mm within 0.001 mm.
- Throat diameter: 25.400 mm and no smaller than the official 25.0 mm DE250
  exit.
- Exact recurrence terminal angle and CAD spline terminal tangent: 140 degrees
  within 0.001 degree.
- CAD spline throat tangent: 8 degrees within 0.001 degree.
- Maximum sampled recurrence-to-CAD meridian deviation below 0.003 mm.
- Two flange bolt holes only, on 76 mm BCD.
- STEP audit: one solid, no boundary or non-manifold edges, and no
  `OFFSET_SURFACE` entities.
- Catalog check passes after registering the horn family.

## Visual question

Does the standalone 190 mm rolled-back horn read as the intended symmetric
Le Cléac'h form, with a continuous throat/flange transition and no visible
surface discontinuity at the rolled mouth? Use one isometric Snapshot overview
and, only if needed, one meridian-focused direct render.

## Promotion comparison

Compare every regenerated family output against this accepted candidate for
physical envelope, acoustic length, cutoff, wavefront factor, throat/mouth
dimensions, solid topology, and the inspected isometric appearance.
