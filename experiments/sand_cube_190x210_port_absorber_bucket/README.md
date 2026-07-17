# Removable bucket-style port absorber

This isolated experiment replaces the earlier short, wide collar with a long,
slim, support-free architecture:

- a vertical inner core with an exact 40.000 mm bore, an integral chamber
  floor, four vertical neck rails rotated 30 degrees away from the cylindrical
  surface seam, a deliberate 0.80 mm solid rail-to-core overlap, and 24 small
  diamond pilot passages;
- an outer bucket with its upper annular closure printed integrally.  The bucket
  is printed inverted with that closure on the build plate, then lowered over
  the drilled inner core; and
- one annular socket-adapter design printed twice, with one copy flipped during
  assembly to receive a 40 mm-ID tube at each end.

See [SCIENCE_AND_TUNING.md](SCIENCE_AND_TUNING.md) for the derivation, formulas,
geometry-only damping analysis, drill-bit ladder, and measurement procedure.

The absorber body is 68 mm outside diameter and 120 mm long.  The connected
assembly is 146 mm long including a 13 mm adapter at each end.  It uses one
common annular chamber so the removable bucket does not have to seal four long
divider ribs.  At one shared tuning frequency this is acoustically equivalent
to identical parallel chambers.  Independent chambers remain a later option
only if measurements justify staggered tuning.

## Hole calibration

The print-ready core has 0.90 mm diamond pilots.  Ream them from the chamber
side with the bucket removed.  The nominal diameter is solved from the actual
CAD cavity volume, 24 parallel holes, an 8 mm physical neck, and a provisional
345 Hz target.  `diagnostics.json` includes predicted frequency for nearby
0.05 mm drill sizes and comparable 16-, 24-, 32-, 64-, and 96-hole families.

Begin below the target using an undersized bit, assemble the bucket with a
temporary airtight seal, measure, then enlarge all active holes equally.  A
hole can be removed from the active total by plugging it from the chamber side
before the bucket is reinstalled.  Remove only breakthrough burrs inside the
bore; do not deliberately countersink the airway-side edges.

No mesh, wool, felt, or polyfill is part of this model.  The TMM response uses
Q=1 as a comparison case only.  The real Q produced by the drilled geometry
must be inferred from the measured peak and decay.  The diagnostic resistance
estimate intentionally reports that 24 holes may remain relatively high-Q
before contraction and edge losses.  It also compares denser 32-, 64-, and
96-hole families so a second inner core can add geometric damping without
changing the bucket.

## Sealing and printing

The bucket rim seats on the integral lower floor and is centered by a printed
lip.  Its integral upper skirt slips over the continuous inner core.  Use a
thin removable face seal at the lower rim and a circumferential gasket or
removable sealant at the upper skirt during tuning.  Pressure-decay test the
assembled cavity before acoustic measurements.

Both primary parts are support-free:

- print the inner core upright on its integral floor;
- print the bucket inverted, annular cap on the build plate and open rim up; and
- print two identical socket adapters flat on their annular plates, sockets up.

The generated `port_absorber_bucket_print_layout.step` shows all four physical
pieces in those orientations.

The adapters preserve a 40 mm through-bore and provide 10 mm-deep female
sockets with 0.40 mm diametral clearance.  Use the 46.4 mm socket-ID version for
40 ID / 46 OD tube with a 3 mm wall, or the 50.4 mm socket-ID version for 40 ID /
50 OD tube with a 5 mm wall.  These are slip receptacles; adhesive, removable
sealant, a gasket, or a later mechanical lock still has to provide the final
seal and retention.

For the simplest serviceable build, bond the lower adapter to the core floor
and the upper adapter to the bucket cap while a straight 40 mm mandrel holds
them concentric. The bucket can still be removed from the core for drilling;
only the adjoining tube joints need a temporary seal during tuning.

The clearance is a CAD starting value, not a printer guarantee. Print a short
fit coupon and compensate for elephant foot at the socket entry before printing
the full module.

The vertical line sometimes visible in a STEP viewer is the parametric seam of
a cylindrical face, not a physical joint.  The actual FDM Z-seam is selected in
the slicer; place it away from the four drilled rails if desired.

## Placement and a split pair

The first modeled port mode has its pressure antinode near the middle of the
491.37 mm acoustic path.  A single absorber is strongest there.  Two modules
using half the total absorber volume and neck area at one-third and two-thirds
of the path retain approximately 75.4% of the ideal centered first-mode
pressure-squared coupling.  That makes the split layout viable when packaging
matters, though not quite as strong as one centered module.

Maintaining the same tuning requires maintaining total neck area divided by
chamber volume in each half.  Simply shortening the current body does not do
that exactly because floors, caps, skirts, and adapters do not scale.  A
verified 60 mm trial body with 4 rails × 3 holes has 49.761 cm³ of actual cavity
volume and solves to a 1.392 mm drill at 345 Hz; it is a starting geometry, not
an instruction to cut the existing model in half.  Both one-third positions
also have strong pressure for the second pipe mode, but a 345 Hz absorber does
not absorb the roughly 699 Hz mode unless a chamber is tuned separately for it.

## Build

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_bucket/generate_port_absorber_bucket.py
```

Useful geometry-only variants:

```sh
--holes-per-rail 8
--hole-pitch 7
--rail-count 4
--rail-angle-offset 30
--ream-diameter 1.50
--neck-length 8
--length 120
--outer-diameter 68
--target-frequency 345
```

A denser geometry-only resistance study can use, for example, eight rails with
twelve holes per rail, approximately 4.5 mm pitch, and a smaller pilot span.
Its required drill size is recalculated from that version's actual cavity
volume.

```sh
--rail-count 8 --holes-per-rail 12 --hole-pitch 4.5 --pilot-span 0.50
```

Outputs are written under
`build/sand_cube_190x210_port_absorber_bucket/`.  They include print-ready and
nominal-reamed core STEP files, the outer bucket, assembled/cutaway/exploded
views, a four-piece print layout, 46 OD and 50 OD socket adapters, connected
assemblies for both tube sizes, the intended air domain, modeled response,
diagnostics, and static viewers.
