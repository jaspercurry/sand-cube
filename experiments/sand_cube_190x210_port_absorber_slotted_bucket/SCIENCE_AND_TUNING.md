# Science and tuning: post-finished slotted port absorber

## 1. What this part is doing

The useful bass-reflex resonance is approximately 39.12 Hz. The unwanted sound
is the port's first longitudinal pipe mode, predicted near 334.5-334.7 Hz by the
distributed model. The absorber is a side-branch Helmholtz resonator placed near
a pressure antinode of that pipe mode.

The supplied port dimensions are:

- physical mouth-to-mouth path: 513.6 mm;
- low-frequency effective inertance length: 541.0 mm;
- constant bore: 40 mm;
- inlet mouth: 44.5 mm;
- outlet mouth: 58.6 mm; and
- enclosure volume: 4.524 L.

The 541 mm value is useful for low-frequency bass-reflex tuning, but it is not a
fixed phase length for the midrange pipe mode. Using the physical distributed
path, flare transitions, and outlet radiation load gives a first bare peak near
334.5 Hz and a pressure maximum around 258 mm from the inlet mouth. The final
curved installation should be designed around that location after the untreated
port is measured.

This file describes the straight calibration module only.

## 2. Helmholtz equation

For chamber volume \(V\), combined opening area \(S\), and effective passage
length \(L_\mathrm{eff}\),

\[
f_H=\frac{c}{2\pi}\sqrt{\frac{S}{V L_\mathrm{eff}}}.
\]

The CAD chamber volume is

\[
V=108.6887\ \mathrm{cm^3}.
\]

There are four identical racetrack slots. For finished width \(b\) and total
tip-to-tip length \(h\), the opening area of one slot is

\[
A_s=b(h-b)+\frac{\pi b^2}{4},
\qquad S=4A_s.
\]

The exact racetrack perimeter is

\[
P_s=2(h-b)+\pi b,
\]

so its hydraulic diameter is

\[
D_h=\frac{4A_s}{P_s}.
\]

The provisional two-sided flush-opening correction is

\[
L_\mathrm{eff}=t+0.85D_h,
\]

where the physical radial passage is \(t=8\ \mathrm{mm}\). This correction is a
reasonable starting model, not a universal exact expression for a finite slot.
Real edge shape and the nearby bore and chamber walls matter, so the measured
center frequency remains authoritative.

Solving the equation at 334.7 Hz gives the default finished geometry:

\[
b=0.600\ \mathrm{mm},\qquad h=15.432\ \mathrm{mm}.
\]

Its combined opening area is 36.729 mm², approximately 2.92% of the 40 mm port
area. Its hydraulic diameter is 1.164 mm and its estimated effective passage
length is 8.990 mm.

## 3. Why width and length have different jobs

Both increasing width and increasing length add opening area and therefore tend
to raise the resonance frequency. They are not interchangeable, however.

The narrow gap controls how much of the moving air is near a wall. At 334.7 Hz,
the viscous boundary-layer thickness in air is approximately

\[
\delta_v=\sqrt{\frac{2\mu}{\rho\omega}}\approx0.120\ \mathrm{mm}.
\]

Consequently, a 0.6 mm gap has a larger boundary-layer fraction and greater
viscous resistance than a 0.7 or 0.8 mm gap. Slot length mainly supplies the
opening area needed to place the resonance after the width has been selected.

That leads to the tuning rule:

1. choose and establish finished width first, because it is the stronger Q and
   damping control;
2. tune frequency primarily by extending length; and
3. do not alternate arbitrary width and length changes, because the result will
   be hard to interpret.

## 4. Passage depth: more wetted area, but not free damping

Making the radial passage deeper does increase the wall area in contact with the
oscillating air. In the slit-resistance model used by Hildebrandt, the viscous
wall term has the trend

\[
R_\mathrm{wall}\propto\frac{l_0}{b^3},
\]

where \(l_0\) is physical passage depth and \(b\) is slit width. At otherwise
fixed geometry, a deeper passage therefore produces more wall resistance. The
cube on width is equally important: doubling the gap reduces this wall term by
approximately eight while quadrupling depth raises it by four. Depth alone does
not make a wide slit behave like an arbitrarily narrow one.

Depth also increases the acoustic mass of the air in the passage. Since

\[
f_H\propto\sqrt{\frac{S}{V L_\mathrm{eff}}},
\]

increasing depth while leaving opening area and chamber volume unchanged lowers
the Helmholtz frequency. Holding the same frequency and chamber volume requires
opening area to rise roughly in proportion to the new effective passage length.
That generally means longer or wider slots, and it changes wall loss, entrance
loss, and end correction at the same time.

There is a second subtlety: Q compares stored acoustic energy with energy lost
per cycle. A deeper passage can raise both inertial energy and viscous loss, so
four times the depth does **not** imply one quarter the Q. Once the physical
length dominates the end correction, the added mass and distributed wall loss
can grow at similar rates. Depth is therefore a useful design variable, but it
is not a free damping control.

Our 8 mm passage is four times the German prototype's 2 mm physical neck. It
gives useful post-machining access and makes the slot a deliberate, repeatable
channel, but it also requires substantially more opening area than a 2 mm neck
would require at the same chamber volume and frequency. Exact comparisons must
include total slot area and length, end corrections, and entrance losses—not
just the wetted area.

### What the German paper actually says about its 2 mm depth

The paper gives a direct construction reason, not an acoustic optimum. In
Section 4.2, Hildebrandt says the existing **2 mm port-wall thickness was used
as the Helmholtz neck length to simplify the construction**. The available
annular chamber was constrained to about 123 cm³ by a 65 mm maximum outside
diameter, and the final opening was divided into four 50 mm × 0.2 mm slits.

The paper does not report a depth sweep or claim that 2 mm gives the best Q. A
reasonable mechanical inference from its geometry is that a deeper inward neck
would obstruct the port, while a thicker wall or outward neck would consume the
already limited chamber volume or outside-diameter allowance. Reusing the wall
as a flush neck avoided all three problems.

Source: Malte Hildebrandt, *Dämpfung stehender Wellen in Bassreflexrohren durch
den Einsatz von Helmholtzabsorbern*, Section 4.2, especially PDF pages 36–38
([official thesis PDF](https://reposit.haw-hamburg.de/bitstream/20.500.12738/16061/1/BA_D%C3%A4mpfung_stehender_Wellen.pdf)).

## 5. Geometry-only Q estimate

A smooth-wall high-frequency boundary approximation can be written in terms of
the slot perimeter and area. For four parallel slots,

\[
R_v\approx
\frac{tP_s}{4A_s^2}
\sqrt{\frac{\omega\rho\mu}{2}}.
\]

With acoustic mass

\[
M=\frac{\rho L_\mathrm{eff}}{4A_s},
\]

the comparison value is

\[
Q\approx\frac{\omega M}{R_v}.
\]

For the 0.6 mm × 15.432 mm nominal geometry this gives approximately \(Q=5.47\)
before entrance contraction, edge loss, FDM texture, tool marks, leakage, and
level-dependent nonlinear loss. This is a trend estimate, not a predicted
measured Q. The actual part may be substantially more damped.

At the same 334.7 Hz target, the comparison is:

| Gap | Length per slot | Total opening area | Boundary-layer overlap* | Geometry-only Q trend |
|---:|---:|---:|---:|---:|
| 0.20 mm | 42.630 mm | 34.070 mm² | 1.20 | 1.74 |
| 0.30 mm | 29.025 mm | 34.753 mm² | 0.80 | 2.65 |
| 0.40 mm | 22.227 mm | 35.426 mm² | 0.60 | 3.58 |
| 0.50 mm | 18.150 mm | 36.085 mm² | 0.48 | 4.52 |
| 0.60 mm | 15.432 mm | 36.729 mm² | 0.40 | 5.47 |
| 0.70 mm | 13.491 mm | 37.354 mm² | 0.34 | 6.43 |
| 0.80 mm | 12.035 mm | 37.963 mm² | 0.30 | 7.38 |

\*Boundary-layer overlap is \(\delta_v/(b/2)\) at 334.7 Hz. Values near or
above one mean the viscous layers from opposite walls strongly overlap. It is a
useful physical indicator, not a direct efficiency or Q measurement.

The 0.6 mm choice is a compromise between stronger viscous damping and a gap
that can be finished and gauged without relying on a microscopic printed slit.
It is the current cautious reference, not a claim of acoustic optimality. A
post-finished 0.4 mm core is a sensible stronger-damping experiment; 0.2 mm is
the aggressive low-Q case, requires almost 43 mm per slot, and will be much more
sensitive to burrs, contamination, width error, and level-dependent flow.

The nominal bandwidth values \(f_H/Q\) from this comparison would be about 193
Hz at 0.2 mm, 94 Hz at 0.4 mm, and 45 Hz at 0.8 mm. These are resonator-only
trend numbers, not predictions of the final port attenuation bandwidth.

## 6. Why the printed pilot is 0.5 mm × 11 mm

The stock 0.4 mm X2D setup may print a 0.5 mm vertical opening, but the actual
gap can vary with filament, flow, seam behavior, cooling, and surface texture.
The print-ready slot is therefore not treated as the calibrated acoustic neck.
It is material intentionally left for finishing.

The 0.5 mm × 11 mm pilots predict approximately 260.2 Hz. After opening only the
width to 0.6 mm while leaving the length at 11 mm, the prediction is about
282.3 Hz. That leaves ample one-way tuning range below 334.7 Hz.

At a constant 0.6 mm finished width:

| Slot length per slot | Predicted frequency |
|---:|---:|
| 11.0 mm | 282.3 Hz |
| 12.0 mm | 294.9 Hz |
| 13.0 mm | 307.0 Hz |
| 14.0 mm | 318.7 Hz |
| 15.0 mm | 330.0 Hz |
| 15.432 mm | 334.7 Hz |
| 15.932 mm | 340.1 Hz |

Near the target, extending every slot by 0.5 mm changes the model by about
5.4 Hz. Extending only one of four slots by 0.5 mm is approximately a quarter of
that change, making endpoint-by-endpoint adjustment a useful fine control.

## 7. Tooling interpretation

The removable bucket exposes the chamber side of all four rails. The intended
slot is radial through the 8 mm passage and axial along the tube.

Suitable finishing approaches include:

- a known-thickness abrasive shim or feeler-gauge strip;
- a guided straight-flute micro cutter;
- a micro end mill in a rigid guide; or
- another tool whose finished kerf has first been measured on the coupon.

A twist drill used sideways is not automatically a diameter-accurate milling
tool. It can flex, grab, melt plastic, or cut wider than its nominal diameter.
If it is used, the coupon should establish the real kerf and a guide should
limit depth and endpoint travel.

The witness marks show the intended physical slot tips. A round cutter's center
must stop one cutter radius inside the corresponding mark. Deburr proud material
inside the bore with fine rolled abrasive, but avoid deliberate countersinks or
large chamfers because they change the entrance loss and end correction.

## 8. Measurement sequence

1. Print and measure the coupon with the intended production settings.
2. Print the full inner core only after confirming a usable pilot opening.
3. Finish all four gaps to the same measured 0.60 mm width while retaining the
   initial 11 mm length.
4. Assemble the bucket and sockets with removable airtight seals.
5. Pressure-decay test the chamber; repair leakage before acoustic conclusions.
6. Measure the untreated port and record its resonance frequency and bandwidth.
7. Install the absorber and measure from the same microphone location and drive
   level.
8. Extend all four slots in equal small steps until the attenuation notch is
   close to the measured port resonance.
9. Use one endpoint or one slot at a time for the final fine adjustment.
10. If the center is correct but attenuation is too narrow or weak, change width
    only in a new core or by a deliberately measured enlargement, recognizing
    that widening raises frequency and reduces viscous resistance at the same
    time.

## 9. Model limitations

The calculation is sufficient to define a safe starting geometry, but it does
not replace measurement. Important unmodeled or approximate effects include:

- finite-slot end correction in the curved 40 mm bore;
- contraction and separation at the slot mouths;
- printed and post-machined surface roughness;
- leakage at the removable bucket and tube sockets;
- sound-pressure-dependent nonlinear loss;
- temperature and humidity; and
- the final curved installation's exact pressure distribution.

The source of record is `generate_port_absorber_slotted_bucket.py`. Generated
STEP files, diagnostic JSON, response CSV files, and viewers are written to
`build/sand_cube_190x210_port_absorber_slotted_bucket/`.
