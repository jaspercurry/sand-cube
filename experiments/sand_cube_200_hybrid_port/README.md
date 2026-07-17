# 200 mm Sand Cube — 38 Hz Folded Reflex Concept

This experiment is the first three-dimensional pass at **direction one**: a
conventional 38 Hz bass-reflex duct with one internal U-turn and an upward
outlet behind the B&C DE250. It is separate from, and does not modify, the
validated 43 Hz straight circular tower experiment.

## Concept geometry

- The constant-area throat is a rounded 80 x 15 mm rectangle (1,200 mm²).
- One smooth 180-degree turn sits near the bottom of the acoustic cavity.
- The inlet is high inside the box; the return leg exits vertically through a
  sealed rectangular receiver in the top wall.
- The visible outlet and its 3.2 mm shell remain narrower than the 136 mm-wide
  compression-driver cradle.
- The existing open-top DE250 half-cup is molded into the front of the rising
  leg, retaining the full front mounting face and both B&C bolt patterns.
- The actual outlet height is solved from the exact OpenCascade-measured net
  air volume after the enclosure, hardware, and complete in-box duct envelope
  are subtracted.

This is packaging CAD, not final production CAD. In particular, the lower U
cannot be inserted through the current top opening as a single piece. A rear
service panel, a sealed split duct, or an enclosure-integrated lower return is
the next mechanical choice. Main-woofer interference is measured and reported
without moving the driver in this pass.

## Generate

From the repository root:

```bash
.venv/bin/python experiments/sand_cube_200_hybrid_port/generate_sand_cube_200_hybrid_port.py
```

Outputs are written to `build/sand_cube_200_hybrid_port/`. The exterior viewer
is under `viewer/viewer/index.html`; the more useful sectioned acoustic-path
view is under `cutaway_viewer/viewer/index.html`.

The generator also exports separate base, tower, airway, gasket, complete
assembly, hardware-check, and cutaway STEP files plus `diagnostics.json`.

## What the 38 Hz model does and does not prove

The length is a conventional Helmholtz/inertance solution, not a transmission
line quarter-wave alignment. The calculation includes the exact net box
volume, smooth inlet/outlet area changes, approximate end corrections, and the
centerline length of the U-turn. It does not predict the extra loss and small
tuning shift caused by a printed bend, layer texture, leakage, or a final
removable joint. The first physical prototype still needs an impedance sweep;
the parametric outlet leg can then be shortened toward 40 Hz if needed.
