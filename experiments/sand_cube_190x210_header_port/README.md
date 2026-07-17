# 190 x 190 x 210 mm modular-header 40 mm port study

This is an isolated successor to the smooth 39.243 mm circular-port variant.
The prior experiment and its generated output remain unchanged. This pass
keeps the same enclosure, centered black-hole front, supplied woofer, GX16,
fill blisters, bracing, JMLC horn, and DE250 reference placement while changing
only the core port architecture.

The acoustic bore is a constant 40 mm circle from the inlet throat through the
visible tower. The 1,256.64 mm2 area is 3.896% larger than the saved smooth
variant. The in-box tube has a 3 mm wall; the visible straight tower retains
the existing 5 mm structural wall for packaging reference. Port join collars,
mounting tabs, heat-set platforms, and the final horn load path are deliberately
excluded from this geometry study.

The in-box centerline is assembled from ordinary header-like modules:

- 72.7 degree R75 plan elbow
- 26.275 mm straight
- 90 degree R50 rise elbow
- 2.811 mm vertical straight
- 67 degree R50 offset elbow
- 3.397 mm diagonal straight
- 67 degree R50 return elbow
- 2.811 mm vertical straight

Every bend is a true constant-radius circular arc and every transition is
tangent. There are no splines, flattened sections, oval rotations, or changing
airway profiles. The two 67 degree elbows are rotated in a shared vertical
plane to return the side rise to the centered tower, demonstrating the same
placement freedom used when fabricating an exhaust header from elbows and
short straight coupons.

The module route is 325.935 mm long and changes direction by 296.7 degrees in
total. The broad floor-plan bend is 1.875 bore diameters at centerline; the
three R50 bends are 1.25 diameters. The latter are acceptable prototype
geometry, but they are the highest-loss parts of the route and should be the
first radii enlarged if later packaging permits. No empirical bend-loss or
"extra acoustic length per elbow" correction is assumed; final compression,
noise, and impedance tuning must be measured on a print.

Growing the bore revealed a tiny woofer-wall conflict in the inherited inlet
position. The inlet remains 0.5 mm farther left, while its flare grows from
15 to 18 mm toward the front. This moves the visible mouth forward exactly
3 mm but holds the 40 mm throat at y=-10.25 mm, so the floor route does not
move toward the woofer. The floor heading changes from 75 to 72.7 degrees and
its straight grows to 26.275 mm to recover the tuning length while placing the
rise close to the rear-right corner. The finished port has zero modeled overlap
with the woofer, GX16, enclosure, or airway. Nominal rise clearance is 0.979 mm
to the right acoustic wall and 0.961 mm to the rear acoustic wall. Including
the 0.30 mm installation allowance leaves 0.679 and 0.661 mm.

Exact OpenCascade volume accounting gives 4.55109 L net air volume after the
woofer, cabinet features, connector allowance, and complete 0.58192 L in-box
port envelope. Relative to the saved smooth variant, the larger header port
consumes another 0.01903 L (19.0 mL) of net volume. The total physical
centerline including both flares and the straight tower is 513.589 mm; the
modeled effective acoustic length is 541.011 mm.

The outlet solves to 38.99944 Hz in the modeled 4.551 L box. Its top is
z=253.654 mm, exactly 3 mm lower than the preceding header draft and about
1.35 mm below the current DE250 body top. It remains 10.541 mm higher than the
saved smooth-port design because the 40 mm bore needs more length. The larger
bore buys 3.896% more area and correspondingly lower velocity for a given
volume flow, while adding 22.22 mm total physical length versus that smooth
variant.

The small-signal model predicts a natural F3 near 50 Hz and about 5.78 dB of
DSP at 39 Hz for the flat moderate-volume goal. At 25 W without boost, modeled
port velocity is 10.92 m/s at 39 Hz; the fully boosted 25 W reference case is
21.21 m/s. Retain the planned 28-30 Hz fourth-order high-pass and dynamic bass
limiter. These figures are comparative model outputs, not substitutes for
impedance, near-field, compression, and noise measurements on the printed
prototype.

Run:

```sh
MPLCONFIGDIR=/private/tmp/cad-mpl UV_CACHE_DIR=/private/tmp/cad-uv-cache \
  uv run python experiments/sand_cube_190x210_header_port/generate_sand_cube_190x210_header_port.py
```

Generated STEP files, diagnostics, and static viewers are written under
`build/sand_cube_190x210_header_port/`.
