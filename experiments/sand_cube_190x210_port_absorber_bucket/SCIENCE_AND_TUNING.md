# Science and tuning of the bucket-style port absorber

## 1. Purpose and design status

This module is a side-branch Helmholtz absorber for the first longitudinal
resonance of the project's long bass-reflex port. It is not intended to absorb
the useful 39 Hz bass-reflex output. Its job is to draw energy from the much
higher-frequency pipe mode and dissipate that energy in the small drilled
passages.

The present part is an isolated, removable calibration module. It does not yet
replace a section of the production port. The earlier production geometry
remains unmodified, while this module and both of its mating sockets preserve an
exact 40.000 mm internal diameter. Direct connection to the earlier 39.243 mm-ID
port would create a small 0.379 mm radial step unless the adjoining tubes are
also changed to 40 mm ID.

The design deliberately does not depend on mesh, wool, felt, polyfill, or an
accurately printed microscopic slit. Its adjustable elements are geometry:

- number of holes;
- finished drill diameter;
- radial passage or neck length;
- chamber volume; and
- if measurements require it, a second core with a denser array of smaller
  holes.

## 2. Target frequency derived from this port

The provisional target is not copied from the 380 Hz example in the research
notes. It comes from the current project port.

The modeled physical centerline length is 491.369 mm. A first half-wave estimate
is therefore

\[
f_1 \approx \frac{c}{2L}
    = \frac{343}{2(0.491369)}
    \approx 349.0\ \text{Hz}.
\]

The project's segmented transfer-matrix model, including the inlet and outlet
flare approximations and the outlet radiation load, gives a bare first peak near
349.5 Hz. The absorber is provisionally calculated at 345 Hz to remain inside
the expected measurement range while allowing for end-correction and real-port
uncertainty.

The printed untreated port measurement should ultimately replace this
provisional target. The useful initial search region is approximately
315-365 Hz.

## 3. Helmholtz-resonator model

The chamber is represented by an acoustic compliance, and the air moving in the
small passages is represented by an acoustic mass.

For a chamber volume \(V\), total neck area \(S\), and effective neck length
\(L_{\mathrm{eff}}\), the resonance is

\[
f_H = \frac{c}{2\pi}
      \sqrt{\frac{S}{V L_{\mathrm{eff}}}}.
\]

For \(N\) identical drilled holes of diameter \(d\),

\[
S = N\frac{\pi d^2}{4}.
\]

The moving air does not stop exactly at the two physical faces of a hole. Air
outside both ends also participates. The model therefore uses

\[
L_{\mathrm{eff}} = t + \beta d,
\]

where:

- \(t\) is the physical radial passage length;
- \(d\) is the finished circular diameter; and
- \(\beta=0.85\) is the nominal combined two-sided end correction.

Substitution gives the equation used by the generator:

\[
f_H = \frac{c}{2\pi}
\sqrt{
\frac{N\pi d^2/4}
     {V(t+\beta d)}
}.
\]

Because \(d\) occurs in both the area and the end correction, the generator
solves this equation numerically rather than treating effective length as a
fixed guessed value.

The corresponding lumped acoustic properties are

\[
M_H = \frac{\rho L_{\mathrm{eff}}}{S},
\qquad
C_H = \frac{V}{\rho c^2},
\qquad
f_H = \frac{1}{2\pi\sqrt{M_H C_H}}.
\]

## 4. Current CAD solution

The default model has:

| Quantity | Current value |
|---|---:|
| Absorber body | 68 mm OD × 120 mm long |
| Connected length with two adapters | 146 mm |
| Main bore | 40.000 mm |
| Common chamber volume from CAD | 108.6887 cm³ |
| Hole arrangement | 4 rails × 6 holes |
| Total holes | 24 |
| Hole-band length | 50 mm |
| Printed diamond pilot span | 0.90 mm |
| Physical radial neck length | 8.00 mm |
| Solved finished diameter | 1.4588 mm |
| Effective length at that diameter | 9.2399 mm |
| Total finished opening area | 40.1110 mm² |
| Opening area relative to port area | 3.192% |
| Calculated absorber frequency | 345.0 Hz |

The inner core is printed upright. Its annular lower floor, locating lip, tube
wall, and four vertical drill rails are one support-free print. Each rail has a
deliberate 0.80 mm radial overlap into the core wall so it is attached by solid
volume rather than a tangent line. The outer part is a bucket: its annular top
closure and outer wall are one print, printed upside down with the closure on
the build plate.

The bucket is removed for drilling. Each diamond pilot is drilled radially from
the chamber side into the bore. Proud breakthrough burrs can be removed with
fine rolled sandpaper inside the tube. The bore-side edges should not be given
large or inconsistent chamfers because that changes the end correction.

The vertical line that can appear on a cylindrical STEP face is its parametric
surface seam, not a physical split or gap. The four rail centerlines are rotated
30 degrees away from that seam, at 30, 120, 210, and 300 degrees. This CAD seam
does not control the real FDM Z-seam; the slicer should place or paint its seam
between drill rails.

Two identical annular end adapters are printed flat on their 3 mm plates with
the sockets facing upward. One is flipped during assembly. Both retain the full
40 mm bore and provide 10 mm of tube engagement, a 3 mm socket wall, and 0.40 mm
diametral clearance:

| Mating tube | Socket ID |
|---|---:|
| 40 ID / 46 OD, 3 mm wall | 46.4 mm |
| 40 ID / 50 OD, 5 mm wall | 50.4 mm |

The present adapters are slip receptacles. Bond one adapter to the core's lower
floor and the other to the bucket's upper cap, using a temporary 40 mm mandrel
or mating tube to maintain concentricity during cure. This still lets the bucket
separate from the core for drilling. The tube joints can use removable sealant
during tuning. A gasketed screw, clamp, or bayonet retention system is not yet
modeled.
A short fit coupon should confirm the 0.40 mm diametral clearance on the chosen
printer; elephant foot should be removed or compensated at socket entries.

## 5. Placement and splitting into two modules

Side-branch absorption is location-sensitive because a resonator couples to
local acoustic pressure. The first modeled longitudinal mode has its pressure
antinode near the middle of the 491.369 mm path, at 245.684 mm from the inlet.
A single same-volume absorber is strongest there.

The current transfer-matrix model gives:

| Position | Path from inlet | Mode 1 pressure | Mode 2 pressure | Mode 3 pressure |
|---|---:|---:|---:|---:|
| One-third | 163.790 mm | 0.8653 | 0.8692 | 0.0884 |
| One-half | 245.684 mm | 1.0000 | 0.0387 | 0.9995 |
| Two-thirds | 327.579 mm | 0.8713 | 0.8533 | 0.0994 |

For the same total absorber volume and comparable Q, coupling scales roughly
with each module's share times normalized pressure squared. Two half-size
modules at one-third and two-thirds therefore give

\[
\frac{1}{2}(0.8653^2+0.8713^2)=0.75395,
\]

or about 75.4% of one same-total-volume module at the ideal center antinode.
That is a viable packaging trade, but not the strongest possible first-mode
placement. The hole-band center is 63 mm from either mating-tube shoulder, so
locate that center—not the end of the 146 mm loose assembly—at the desired path
coordinate. Both third-points are also strong-pressure locations for the second
mode; this does **not** make a 345 Hz absorber remove the modeled 698.5 Hz mode.
A separately tuned chamber or module is still required for that frequency.

Ideally, splitting the resonator keeps chamber volume and neck area in the same
ratio: approximately half the volume and half the holes at the same diameter
and radial neck length. Real end plates, skirts, and adapters do not scale
linearly, so the actual CAD volume must be recalculated. A validated 60 mm trial
body with four rails and three holes per rail has 49.761 cm³ of cavity volume;
its calculated 345 Hz drill diameter is 1.392 mm, rather than exactly matching
the full module's 1.459 mm drill.

## 6. Why one common chamber works

Four separate chambers, each with one quarter of the total volume and one
quarter of the total neck area, are equivalent to one chamber with the combined
volume and combined area when every chamber is tuned identically. The parallel
acoustic admittances add.

The common chamber avoids the difficult requirement to seal four long divider
ribs against a removable sliding bucket. It still produces one Helmholtz
resonance. It does not produce four independently staggered resonances.

If measurements eventually justify staggered frequencies, the outer chamber
will need genuine airtight divisions. That should be a later, measurement-led
version rather than a complication in the first calibration module.

## 7. The easiest frequency adjustment: drill diameter

For fixed hole count, chamber volume, and physical neck length, increasing drill
diameter raises the absorber frequency. It increases area faster than it
increases end correction.

The exact ratio between two drilled diameters is

\[
\frac{f_2}{f_1}
=
\frac{d_2}{d_1}
\sqrt{\frac{t+\beta d_1}{t+\beta d_2}}.
\]

Near the current 1.46 mm solution, a 1% diameter change produces approximately
a 0.93% frequency change. A 0.05 mm drill step therefore moves the predicted
center by roughly 11 Hz.

The actual-CAD drill ladder is:

| Finished diameter | Predicted frequency |
|---:|---:|
| 1.25 mm | 298.5 Hz |
| 1.30 mm | 309.7 Hz |
| 1.35 mm | 320.9 Hz |
| 1.40 mm | 332.0 Hz |
| 1.45 mm | 343.1 Hz |
| 1.459 mm | 345.0 Hz |
| 1.50 mm | 354.1 Hz |
| 1.55 mm | 365.1 Hz |
| 1.60 mm | 376.0 Hz |
| 1.65 mm | 386.8 Hz |

This makes a 1.45, 1.50, 1.55, and 1.60 mm metric PCB-drill sequence a practical
calibration set. Begin undersized because enlarging a hole is easy and reducing
it is not.

A drill bit gives much more repeatable diameter than an as-printed circular
horizontal tunnel. It is still worth using the same pin vise or low-speed drill,
the same technique, and minimal runout for every hole. A short printed test
coupon can reveal whether a nominal bit consistently cuts slightly oversize in
the chosen filament.

## 8. Passage length: what “shorter” and “taller” mean

The acoustically relevant passage length is radial: the distance from the bore
surface through the tube wall and raised neck rail to the chamber. In the
current model this is 8 mm.

Changing the axial height of a rail or spreading the same holes over a taller
region does not directly change Helmholtz tuning. Axial height matters only if
it changes hole count, chamber volume, or the port-mode pressure sampled by the
hole band.

At the current 1.4588 mm diameter and fixed chamber volume, changing only radial
passage length gives:

| Physical passage length | Predicted frequency |
|---:|---:|
| 6 mm | 389.7 Hz |
| 7 mm | 365.3 Hz |
| 8 mm | 345.0 Hz |
| 9 mm | 327.7 Hz |
| 10 mm | 312.8 Hz |

Therefore:

- a shorter radial passage raises frequency;
- a longer radial passage lowers frequency;
- a larger drill raises frequency; and
- a smaller drill lowers frequency.

Drill diameter is the easiest adjustment on one printed core. Passage length is
best changed by printing another inexpensive core with a different rail depth.
Counterboring the chamber side to shorten an existing neck is possible, but it
also changes the cavity-side mouth geometry and end correction, so a modeled
core variant is preferable.

## 9. Chamber-volume adjustment

With neck geometry fixed,

\[
f_H \propto \frac{1}{\sqrt{V}}.
\]

Increasing chamber volume lowers frequency; inserting a solid displacement
piece raises frequency. With the current holes and neck length:

| Chamber volume | Predicted frequency |
|---:|---:|
| 100 cm³ | 359.7 Hz |
| 105 cm³ | 351.0 Hz |
| 108.6887 cm³ | 345.0 Hz |
| 110 cm³ | 342.9 Hz |
| 115 cm³ | 335.4 Hz |
| 120 cm³ | 328.3 Hz |
| 125 cm³ | 321.7 Hz |

Volume inserts are reversible, but drill diameter is simpler and easier to
calculate. Volume should be treated as a secondary coarse adjustment or as a
way to recover from an accidentally high drilled frequency.

## 10. Hole count and patching

At fixed diameter and effective length,

\[
f_H \propto \sqrt{N}.
\]

Plugging one of 24 equal holes changes frequency approximately by

\[
\frac{f_{23}}{f_{24}}\approx\sqrt{\frac{23}{24}}=0.979,
\]

or about 7 Hz near 345 Hz. This is a useful reversible trim. The bucket is
removed, and a hole is sealed from the chamber side without touching the smooth
port bore.

For the cleanest circumferential loading, opposite pairs or equal changes on all
four rails are preferable, but those produce larger frequency steps. A single
plug is acceptable as a calibration step because the chamber is common and the
hole dimensions are very small compared with the acoustic wavelength.

If holes have mixed diameters, their acoustic masses combine in parallel:

\[
\frac{1}{M_{\mathrm{eq}}}
=
\sum_i \frac{1}{M_i}
=
\sum_i \frac{S_i}{\rho L_{\mathrm{eff},i}}.
\]

The generator currently keeps every active hole equal because it is easier to
manufacture, calculate, and audit.

## 11. Damping and absorber Q without mesh or filling

Frequency and damping are related but not identical. The resonator quality
factor is

\[
Q_H = \frac{\omega_H M_H}{R_H},
\]

where \(R_H\) is the total acoustic resistance of the holes, their edges, and
the chamber. More resistance lowers Q and broadens the absorber. Too little
resistance produces a very narrow notch and response shoulders. Too much
resistance prevents useful air motion and weakens the absorber.

At 345 Hz, the viscous boundary-layer thickness in air is approximately

\[
\delta_v = \sqrt{\frac{2\mu}{\rho\omega}}
          \approx 0.118\ \text{mm}.
\]

The radius of a 1.459 mm hole is about 6.2 boundary-layer thicknesses. Wall drag
is significant but does not occupy most of the hole. Using more, smaller holes
at the same tuned acoustic mass increases wetted perimeter and resistance.

A high-Womersley boundary estimate for \(N\) identical circular holes is

\[
R_v \approx
\frac{16t}{N\pi d^3}
\sqrt{\frac{\omega\rho\mu}{2}}.
\]

This is a comparison model, not a final Q prediction. It excludes detailed
entrance contraction, FDM roughness, imperfect circularity, and nonlinear loss
at higher sound level. Those effects generally add resistance and lower the
measured Q.

For the current common volume and 8 mm passage length, geometry families tuned
to the same 345 Hz target are approximately:

| Holes | Solved diameter | Boundary-only Q estimate |
|---:|---:|---:|
| 16 | 1.816 mm | 9.20 |
| 24 | 1.459 mm | 7.15 |
| 32 | 1.251 mm | 6.02 |
| 64 | 0.869 mm | 4.03 |
| 96 | 0.704 mm | 3.21 |

The default 24-hole core is deliberately the easy-to-drill calibration version.
It may remain relatively high-Q. The generator also supports eight rails,
twelve holes per rail, 4.5 mm axial pitch, and 0.50 mm diamond pilots. That
actual geometry must be regenerated because the additional rail volume changes
the cavity and therefore the solved drill diameter.

The 96-hole version is more work to drill, but it is a completely geometric
route toward the neighborhood of the German prototype's predicted as-built
Q≈3.25. It does not require a resistive fabric.

## 12. Why the drilled-hole version was chosen over the slit

The slit remains acoustically attractive because it provides much more wall
perimeter and viscous resistance for a given open area. The German thesis used
four 50 × 0.2 mm slots, totaling 40 mm². Its calculation suggested a slot width
near 0.13 mm for Q≈1, but the 0.2 mm printable choice was predicted at Q≈3.25.

That result shows both the advantage and weakness of the slit. Slit resistance
contains terms that vary approximately with the inverse square and inverse cube
of width. A width error of only a few hundredths of a millimeter can therefore
change damping dramatically, while also changing tuning area.

The drilled design accepts less resistance in its easiest version in exchange
for:

- a diameter established by a physical cutting tool;
- additive, auditable total area;
- easy enlargement in known increments;
- external access before the bucket is installed; and
- inexpensive replacement of only the inner core.

If the 24-, 32-, or denser-hole experiments cannot provide enough damping at a
reasonable drilling workload, a post-machined slit core is still a valid next
experiment. It should be cut with a tool of known kerf rather than left at an
as-printed microscopic width.

## 13. Recommended measurement and tuning sequence

1. Assemble the bucket with every pilot sealed from the chamber side. Measure
   the untreated port 5-10 mm from the outlet with a repeatable low-level sweep.
2. Confirm that the suspect peak is a port mode. A temporary 20 mm outlet
   extension should move a first longitudinal port mode down by roughly 3-4%,
   while a cabinet or panel resonance should not track the extension.
3. Select a first drill size below the frequency predicted for the measured
   peak. For a peak around 345-355 Hz, 1.45 or 1.50 mm is a safe first step.
4. Drill every active hole with the same bit and method. Remove only proud bore
   burrs.
5. Reassemble the bucket with a repeatable airtight temporary seal. A pressure
   decay test should exceed approximately 50 ms before relying on acoustic
   results.
6. Repeat the port near-field sweep and inspect the waterfall or spectrogram.
   The absorber should reduce both peak height and decay time.
7. If the absorber center is below the port mode, enlarge the holes one bit
   step. If it is above the port mode, plug one or more holes, add a volume
   insert, lengthen the neck in a new core, or reprint the inexpensive core.
8. When a high-Q absorber splits the response into shoulders, the tuning center
   is approximately the geometric mean

   \[
   f_c \approx \sqrt{f_- f_+}.
   \]

   Use this together with the notch and decay plot rather than judging only one
   response point.
9. Once frequency is correct, decide whether damping is sufficient. If narrow
   shoulders and long decay remain, move to a denser, smaller-hole core. If the
   suppression is already broad and clean, do not add complexity.
10. Recheck 39 Hz electrical impedance, port output, compression, turbulence,
    and distortion at increasing level. The present lumped model predicts only
    about a -0.04 Hz change in the low-frequency peak, but the printed system is
    the authority.

## 14. Direction-of-change summary

| Change | Resonance frequency | Geometric damping tendency |
|---|---|---|
| Larger drill diameter | Higher | Lower wall influence |
| Smaller drill diameter | Lower | Higher wall influence |
| More holes at the same diameter | Higher | Lower equivalent resistance because holes are parallel |
| More holes, with diameter reduced to retune | Held near target | Higher resistance and lower Q |
| Shorter radial passage at fixed diameter | Higher | Changes resistance and mass together |
| Longer radial passage at fixed diameter | Lower | Changes resistance and mass together |
| Larger chamber volume | Lower | Stronger acoustic compliance |
| Smaller chamber volume or solid insert | Higher | Weaker acoustic compliance |
| Taller axial hole band with the same holes | Nearly unchanged | Samples a wider axial pressure region |

## 15. Generator controls

The default model is generated with:

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_bucket/generate_port_absorber_bucket.py
```

Useful geometry controls include:

```text
--target-frequency
--ream-diameter
--neck-length
--rail-count
--rail-angle-offset
--holes-per-rail
--hole-pitch
--pilot-span
--length
--outer-diameter
```

The source of record is `generate_port_absorber_bucket.py`. Generated STEP
files, viewers, response data, and `diagnostics.json` are written under
`build/sand_cube_190x210_port_absorber_bucket/`.

## References

- Malte Hildebrandt, *Dämpfung stehender Wellen in Bassreflexrohren*, HAW
  Hamburg, 2024.
- U. Ingard, “On the Theory and Design of Acoustic Resonators,” *Journal of the
  Acoustical Society of America*, 1953.
- M. R. Stinson, “The Propagation of Plane Sound Waves in Narrow and Wide
  Circular Tubes,” *Journal of the Acoustical Society of America*, 1991.
