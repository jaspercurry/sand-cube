# Compact reduced-volume slotted port absorber

This is a **separate** packaging experiment. It does not replace or overwrite
`sand_cube_190x210_port_absorber_slotted_bucket`.

The part keeps the German paper's visually slim annular arrangement: a port
tube forms the inner chamber wall, four axial slits open directly through that
wall, and a removable outer sleeve closes the common annular cavity. The body is
shortened and the chamber volume is deliberately reduced to test how little
packaging is needed in this installation.

## Nominal package

| Quantity | Value |
|---|---:|
| Bore | 40 mm |
| Core wall / physical passage | 5 mm |
| Core OD | 50 mm |
| Outer body | 65 mm OD × 80 mm tall |
| Outer sleeve wall | 3 mm |
| Finished slot count | 4 |
| Intended finished gap | 0.40 mm |
| Calculated finished length per slot | 7.166 mm |
| Total finished opening area | 11.329 mm² |
| Printed pilot | 0.30 mm × 4.0 mm |
| CAD chamber volume | 53.330 cm³ |
| Absorber target | 334.7 Hz |
| Printed-pilot prediction | 219.4 Hz |
| Smooth-wall Q trend before edge losses | 3.62 |

These values are calculated from the final CAD solids; they are not copied from
the German paper. The generated `diagnostics.json` remains the machine-readable
source of record.

## Important volume comparison

The German prototype did not actually use a tiny acoustic volume. It reported
about 123 cm³, spread along a relatively long and narrow annulus. The established
68 × 120 mm project variant contains roughly 109–117 cm³ depending on passage
depth. This compact version is expected to contain only about 53 cm³.

That smaller volume can still be tuned to 334.7 Hz by shortening the slots to
7.166 mm each, but equal center frequency does not imply equal absorption
strength. The compact part has less acoustic compliance and is expected to
couple less strongly to the port mode. It is an intentionally conservative
packaging test that should be compared against the full-volume version with the
same microphone position and drive level.

## Manufacturing and tuning

- Print the core and bucket vertically.
- The 5 mm structural core wall is also the complete acoustic passage; there is
  no additional projecting neck rail.
- A 0.30 mm printed pilot may close partly on a stock 0.4 mm nozzle. The pilot is
  a tooling starter, not a calibrated finished gap.
- Establish every slot at the same measured 0.40 mm width first.
- Begin at the 4 mm pilot length, assemble and measure, then extend the slots
  toward the witness marks in equal increments.
- Keep the bucket airtight and removable during tuning.

The equations, Q limitations, and measurement method remain those in the parent
[science and tuning guide](../sand_cube_190x210_port_absorber_slotted_bucket/SCIENCE_AND_TUNING.md).

## Build

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_bucket_compact/generate_port_absorber_slotted_bucket_compact.py
```

Outputs are written only to
`build/sand_cube_190x210_port_absorber_slotted_bucket_compact/`.
