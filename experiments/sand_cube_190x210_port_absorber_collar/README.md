# Removable Helmholtz absorber collar

This isolated experiment develops a short four-chamber absorber collar for the
long circular bass-reflex port. It does not import, modify, or integrate with
the current enclosure or weight-bearing tower.

The full derivation, architecture comparison, tolerance table, and leakage
calculation are in [DESIGN_ANALYSIS.md](DESIGN_ANALYSIS.md).

## Why 345 Hz, not 380 Hz

The current port is 491.369 mm long. Its ideal physical half-wave estimate is
349.0 Hz. Reusing the project's 518.540 mm low-frequency inertance length gives
330.7 Hz, but that number is not a validated midrange phase length. The
generator's distributed plane-wave model, including the physical flares and
outlet radiation loading, predicts the first untreated peak close to this
range. The provisional absorber center is therefore 345 Hz; the printed bare
port measurement must set the final value.

Expected longitudinal bands from the current geometry are approximately:

- first: 330-350 Hz;
- second: 660-700 Hz;
- third: 990-1050 Hz.

The third band overlaps predicted enclosure axial modes and will be difficult
to attribute from an outlet measurement alone.

## First prototype

The coupon is 30 mm long and 100 mm outside diameter around the unchanged
39.243 mm bore. It matches the external tower's 5 mm host wall but thickens the
local liner outward to an 8 mm physical neck. Four sealed annular sectors each
provide about 25-26 cm3 of net acoustic volume. The exact cavity and solved
neck values are written to `diagnostics.json` after generation.

The neck openings are round, radial, and exactly flush with the bore. The main
airway is never reduced. The 8 mm neck permits a roughly 3.8 mm aperture,
which is more printable and has lower neck velocity than a hole through only a
3-5 mm wall.

The body prints upright with its integral chamber floor on the bed and the
cavities open upward. The lid prints flat. Apply captured woven polyester
acoustic mesh on the cavity side of each neck, then bond the lid along the
complete inner circumference, outer circumference, and every divider. Do not
use loose fibers near the airway.

The nominal end correction is:

```text
Leff = physical neck + 0.85r (duct side) + 0.85r (cavity side)
     = physical neck + 0.85d
```

This is only a starting estimate. The curved finite duct and sector cavity do
not have a directly transferable measured correction, so diagnostics also
show a beta range of 0.70-1.00 in `Leff = t + beta*d`.

## Placement

The ideal first-mode pressure antinode is near the port midpoint, inside the
curved upper return where a useful annular chamber will not fit. The removable
test collar instead occupies the lowest straight external-tower window,
nominally z=95-125 mm (centerline distance about 358 mm from the inlet).

The transfer model predicts that this position retains about 75% of the first
mode's maximum pressure and is almost exactly at a second-mode antinode. It
also displaces no enclosure air, remains accessible, and ends below the DE250
envelope.

## Broadband strategy

Start with all four chambers at the measured first mode. The thesis' preferred
absorber Q of about 0.75-1 is already deliberately broad, so blindly staggering
the first print reduces peak shunt admittance without evidence that the extra
coverage is needed.

The chambers remain independent so later measurements can compare:

- four identical chambers;
- a 2+2 split near 0.97 and 1.03 times the measured first mode; or
- a smaller dedicated second-mode chamber if the 660-700 Hz feature remains
  objectionable.

Use captured mesh or fabric to set resistance/Q. Do not try to obtain both
tuning and damping from sub-resolution printed slots.

## Build

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_collar/generate_port_absorber_collar.py
```

Useful calibration options include:

```sh
--target-frequency 345
--target-multipliers 0.97,0.97,1.03,1.03
--neck-diameter 3.80
--neck-length 8
--absorber-q 1
--collar-length 30
--maximum-outer-diameter 100
```

Outputs under `build/sand_cube_190x210_port_absorber_collar/` include separate
body and lid STEP files, an assembly, a housing cutaway, the complete intended
air domain, static viewers, `modeled_response.csv`, and detailed diagnostics.

## Measurement sequence

1. Measure the untreated outlet 5-10 mm from the mouth with a low-level sweep.
2. Add a temporary 20 mm outlet extension and repeat. A true first port mode
   near 345 Hz should move down roughly 3-4%; cabinet and panel modes should not.
3. Measure the collar first with all four undamped chambers at one frequency.
4. Correct center frequency with controlled aperture diameter or cavity-volume
   plugs. A reamed +/-0.05 mm hole is more meaningful than an as-printed nominal
   diameter.
5. Add captured mesh incrementally and fit the observed resistance/Q.
6. Compare identical and staggered chambers only if the measured residual is
   broad or unit-variable.
7. Recheck electrical impedance, bass tuning, 39 Hz output, decay, turbulence,
   distortion, and compression at increasing level.

## Technical basis and limitations

The collar follows Malte Hildebrandt's measured 3D-printed side-branch concept,
but its dimensions come from this project. The model uses cascaded plane-wave
duct matrices and shunt series-RLC Helmholtz branches. It excludes detailed
bend fields, driver electro-mechanics, thermoviscous loss, flexible printed
walls, and cabinet radiation, so its predicted attenuation is an ideal design
comparison rather than a guaranteed measured notch.

Primary references:

- [Hildebrandt, *Dämpfung stehender Wellen in Bassreflexrohren* (2024)](https://reposit.haw-hamburg.de/bitstream/20.500.12738/16061/1/BA_D%C3%A4mpfung_stehender_Wellen.pdf)
- [Ingard, *On the Theory and Design of Acoustic Resonators*](https://doi.org/10.1121/1.1907235)
- [Levine and Schwinger, *On the Radiation of Sound from an Unflanged Circular Pipe*](https://doi.org/10.1103/PhysRev.73.383)
- [Stinson, *The Propagation of Plane Sound Waves in Narrow and Wide Circular Tubes*](https://doi.org/10.1121/1.400379)
