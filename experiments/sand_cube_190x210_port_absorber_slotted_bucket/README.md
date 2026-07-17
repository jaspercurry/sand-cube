# Post-finished slotted port absorber

This is the straight cylindrical calibration version of the 40 mm-ID port
absorber. It keeps the removable, support-free bucket construction but replaces
the 24 drilled holes with four vertical racetrack slots.

The print-ready slots are intentionally undersized. The intended workflow is:

1. print a narrow, short pilot;
2. remove the outer bucket;
3. finish all four gaps to one measured width;
4. assemble with removable airtight seals and measure at the port mouth; and
5. extend the slots equally until the absorber is centered on the measured pipe
   resonance.

No mesh, wool, polyfill, or tuned damping insert is used.

## Default geometry

| Quantity | Value |
|---|---:|
| Through-bore | 40.000 mm |
| Body | 68 mm OD × 120 mm |
| Connected length with adapters | 146 mm |
| Common chamber volume from CAD | 108.689 cm³ |
| Slot count | 4 |
| Physical radial passage | 8.000 mm |
| Printed pilot per slot | 0.50 mm × 11.00 mm |
| Intended finished width | 0.60 mm |
| Calculated finished length per slot | 15.432 mm |
| Provisional target | 334.7 Hz |
| Printed-pilot prediction | 260.2 Hz |

The pilot is deliberately predicted below the target. Both widening a slot and
lengthening it raise the Helmholtz frequency; neither operation is reversible.

The cylinder's mathematical STEP seam is not a split. All four slot rails are
rotated 30 degrees away from it. In Bambu Studio, paint the real FDM Z-seam
between the rails.

## Width and depth trade-off

A 0.7 mm slot is the safer direct-print choice with a stock 0.4 mm nozzle. Once
post-finishing is accepted, a 0.6 mm final gap becomes attractive: it is still
large enough to gauge and tool, but its greater perimeter-to-area ratio gives
more viscous loss than the 0.7 or 0.8 mm alternatives.

Calculated alternatives using the actual CAD chamber are:

| Finished gap | Required length per slot | Smooth-wall Q trend estimate* |
|---:|---:|---:|
| 0.20 mm | 42.630 mm | 1.74 |
| 0.30 mm | 29.025 mm | 2.65 |
| 0.40 mm | 22.227 mm | 3.58 |
| 0.50 mm | 18.150 mm | 4.52 |
| **0.60 mm** | **15.432 mm** | **5.47** |
| 0.70 mm | 13.491 mm | 6.43 |
| 0.80 mm | 12.035 mm | 7.38 |

\*These Q values compare geometry only. Entrance loss, FDM texture, tool marks,
leakage, sound level, and nonlinear flow can materially lower the measured Q.

At the target frequency, the viscous boundary layer is approximately 0.12 mm
thick. A 0.2 mm slit has strongly overlapping boundary layers and is an
aggressive damping geometry; 0.4 mm is a practical stronger-damping candidate;
0.6 mm is the current cautious post-finished reference; and 0.8 mm is easier to
make but is expected to be substantially narrower-band.

The physical passage depth is 8 mm. A deeper passage does provide more wetted
wall and more viscous drag, but it also adds acoustic mass and lowers the
Helmholtz frequency unless opening area is increased or chamber volume is
reduced. It can raise resistance and stored inertial energy together, so more
depth does not automatically mean a proportionally lower Q.

The German prototype used a much shallower 2 mm passage because that was its
existing port-wall thickness. The paper explicitly says the wall was reused as
the absorber neck to simplify construction; it does not present 2 mm as an
acoustically optimized depth. Its chamber was outside-diameter constrained, so
a deeper neck would also have complicated the flush geometry or consumed bore,
chamber, or radial space. See the detailed comparison and source in
[SCIENCE_AND_TUNING.md](SCIENCE_AND_TUNING.md#4-passage-depth-more-wetted-area-but-not-free-damping).

## Witness notches

Each rail has three pairs of shallow blind notches on its chamber-facing edge.
They do not penetrate the passage.

- closest pair to the slot center: physical tips for a 0.8 mm finished slot;
- middle pair: physical tips for a 0.7 mm finished slot; and
- farthest pair: physical tips for the intended 0.6 mm finished slot.

The marks indicate the final physical slot tips. When using a round cutter, stop
its center one cutter radius before a mark. An abrasive shim may be extended
until its cutting edge reaches the mark.

The marks are reference positions, not an instruction to cut directly to the
final length before measuring. Begin at 11 mm and approach the target in steps.

## Calibration coupon

`port_absorber_slotted_calibration_coupon.step` duplicates the final core's
5 mm wall, 8 mm radial passage, 6 mm rail, and vertical print orientation. Its
four 11 mm slots are:

| Angle from CAD X axis | Nominal gap |
|---:|---:|
| 30° | 0.40 mm |
| 120° | 0.50 mm |
| 210° | 0.60 mm |
| 300° | 0.70 mm |

Print the coupon with the same filament, layer height, flow calibration, wall
settings, seam strategy, and plate preparation as the real core. Inspect the
sliced preview first. Determine which openings remain continuous, then practice
the finishing method and verify the result with a feeler gauge, gauge strip,
microscope, or known tool shank.

## Printing and assembly

All parts are support-free in their exported print orientations:

- inner core: integral annular floor on the build plate, axis vertical;
- outer bucket: inverted, integral annular cap on the build plate;
- two socket adapters: annular plates on the build plate, sockets upward; and
- coupon: annular floor on the build plate.

The two separately printed adapters avoid a large unsupported annular shoulder
on either tall part. Print two identical copies, then flip one during assembly.

- Use the 46.4 mm socket-ID adapter for 40 ID / 46 OD tube.
- Use the 50.4 mm socket-ID adapter for 40 ID / 50 OD tube.

Both provide 10 mm engagement and 0.40 mm diametral starting clearance. Print a
short fit test before relying on that clearance. Use a 40 mm mandrel or mating
tube while bonding adapters so the airway remains concentric.

The bucket must be airtight during measurements but removable during tuning.
Use a thin temporary face seal at its lower rim and a removable circumferential
seal at the upper skirt. Pressure-decay test the chamber before acoustic tests.

## Build

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_bucket/generate_port_absorber_slotted_bucket.py
```

Useful overrides include:

```sh
--pilot-width 0.50
--pilot-length 11
--finished-width 0.60
--target-frequency 334.7
--neck-length 8
--length 120
--outer-diameter 68
```

Outputs are written under
`build/sand_cube_190x210_port_absorber_slotted_bucket/`. The print-ready file is
`port_absorber_slotted_inner_core_pilot.step`; the 0.6 mm finished core is a CAD
reference, not the part to print first.

See [SCIENCE_AND_TUNING.md](SCIENCE_AND_TUNING.md) for the equations, assumptions,
and measurement sequence.
