# 200 mm Sand Cube — 38 Hz Twin-Inlet / Single-Spine Draft

This is the third isolated port experiment. It does not modify either the
straight 43 Hz tower or the single-U 38 Hz folded-reflex concept.

## Topology

- One central rounded 40 x 30 mm spine rises through the enclosure top.
- Only that single spine supports the centered B&C DE250 half-cup.
- Two equal 20 x 30 mm internal branches merge into the bottom of the spine.
- The two 600 mm² branches are acoustically parallel, so their combined area
  equals the 1,200 mm² common spine.
- Each internal branch uses a large lower J bend and a swept upper 90-degree
  elbow terminating in a forward-facing flared mouth.
- There are two internal inlets and one external upward outlet.
- The base owns the complete in-box duct as a monocoque structure. The separate
  tower part begins above the gasket and contains only the single external spine
  and B&C cradle.

The forward mouths are the first draft of the requested 180/270-degree intake
idea. They avoid the 11 mm ceiling clearance of the upward-facing inlet in the
single-U variant. A later pass could turn each mouth into a three-sided hood,
but the current geometry makes the flow direction and clearance easy to judge.

## First generated result

- Calculated Helmholtz tuning: 38.0 Hz.
- Final modeled net box volume: 4.746 L.
- Path from either inlet to the outlet: 501 mm.
- Each separate inlet branch: 234 mm; shared central section: 242 mm plus the
  25 mm outlet flare.
- Visible outlet height above the enclosure: 108 mm / 4.26 in.
- Predicted small-signal F3: 49.1 Hz.
- The base, tower, airway, and gasket each re-import as one valid solid.
- The airway and tower do not intersect the enclosure or residual sand void.
- The lower 180-degree returns have 14 mm airway inside radii; the upper
  90-degree elbows have 10 mm airway inside radii.

The revised duct clears the provisional woofer. The relocated rear GX16 remains
a layout item: its bounding box overlaps at most 1.11 cm³ of the in-box port
envelope, so its actual solid clearance must be resolved before production.

## Wall integration

- Rear wall: 2 mm outer skin, 3 mm sand gap, 2 mm inner skin.
- Floor: 2 mm outer skin, 3 mm sand gap, 2 mm inner skin.
- The airway is tangent to the acoustic cavity at both the rear wall and floor.
- The 3.2 mm duct wall replaces the local 2 mm inner skin, extends 1.2 mm into
  the sand gap, and retains 1.8 mm clearance to the outer skin.
- Only point-like cylindrical bridges are added in the rear and floor gaps; no
  closed sand-trapping ribs are introduced.

## Generate

```bash
.venv/bin/python experiments/sand_cube_200_twin_inlet_port/generate_sand_cube_200_twin_inlet_port.py
```

Outputs are written under `build/sand_cube_200_twin_inlet_port/`, including
separate STEP files for the base, tower, acoustic airway, gasket, exterior
assembly, hardware check, and cutaway plus exterior and cutaway web viewers.
