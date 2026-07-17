# Canonical engineering report: folded-port micro-slit side-branch absorber

> **Status:** Rev. D design basis, 16 July 2026. This is the maintained project
> authority. The complete independently generated
> [Fable Rev. C report](FABLE_REV_C_REPORT.md) is preserved beside it, with
> provenance, as a valuable external analysis. Fable's equations and numerical
> claims were independently reproduced where possible; disagreements and
> unresolved validation gaps are recorded here rather than hidden.

## 1. Decision

Proceed with one removable D-shaped calibration absorber, but replace the
legacy 7.166 mm slots with the separately versioned Rev. D geometry:

| Item | Rev. D nominal |
|---|---:|
| Main bore | 40.000 mm uninterrupted ID |
| Common sealed cavity | 53.329815 cm³ |
| Slits | 4 racetracks at 30°, 120°, 210°, 300° |
| Finished slit gap | 0.400 mm |
| Finished slit tip-to-tip length | **9.066233 mm** |
| Physical passage depth | 5.000 mm |
| Total open area | 14.368627 mm² |
| Slit center within 30 mm body | z = 12.000 mm |
| Land to each end of the local boss | 4.466884 mm |
| Integrated route model target | **338.25 Hz** |
| Nominal model at 1.10 mm total inertial end correction | 337.18 Hz, Q 2.34, R/Z₀ 1.62 |
| End-correction bracket | 0.65–1.50 mm total |
| Predicted branch center over that bracket | 348.52–327.98 Hz |

The 9.066 mm length is a minimax choice over the stated inertial end-correction
range. It balances the two endpoint frequency errors around 338.25 Hz. It is
not a global optimum over width error, leakage, thermal effects, roughness,
nonlinearity, or three-dimensional entrances.

The old 7.166 mm CAD is preserved unchanged as Rev. C/history. In the checked
viscous model it is not a 334.7 Hz absorber: it predicts 325.78 Hz with no added
end correction, 309.26 Hz with the old 0.651 mm correction, 299.24 Hz at
1.10 mm, and 291.08 Hz at 1.50 mm.

## 2. Why the target changed from 334.5 to 338.25 Hz

Two port routes now exist and must not be mixed:

| Route | Physical centerline | 1-D bare first mode | Use |
|---|---:|---:|---|
| Pre-integration reference | 513.589 mm | about 334.5–334.75 Hz | Historical standalone calculations |
| Current enclosure-integrated route | 508.081579 mm | about 338.25–338.35 Hz | **Rev. D design input** |

The integrated D-squat service straight is centered 276.88155 mm from the
inlet. The Rev. D slit is moved from local body z=15 to z=12 to preserve boss
land, so its installed acoustic opening is approximately 273.88155 mm from the
inlet. The 1-D model places the pressure antinode near 255.31 mm, but normalized
pressure at the actual Rev. D opening is still 0.993. That small placement
offset is not worth rebuilding the folded route.

The reported 541.0 mm effective length belongs to the low-frequency port
inertance used for the approximately 39 Hz bass-reflex alignment. It is not the
midrange phase length and must not be inserted blindly into `c/(2L)`.

The printed untreated port remains authoritative. The measurement search band
should be broad enough for bend, inlet, radiation, and manufacturing effects;
roughly 325–345 Hz is a sensible first sweep window.

## 3. System context

| Quantity | Value |
|---|---:|
| Modeled net enclosure volume | 4.524 L |
| Bass-reflex tuning supplied before the integrated reroute | 39.12 Hz |
| Nominal enclosure envelope | 203 mm cube |
| Port ID / area | 40.0 mm / 1,256.64 mm² |
| Typical tube OD | 46 mm with 3 mm wall |
| Weight-bearing tower OD | 50 mm with 5 mm wall |
| Inlet flare mouth / length | 44.5 mm / 18 mm |
| Outlet flare mouth / length | 58.6 mm / 25 mm |
| Earlier route bends | 72.7°, 90°, 67°, 67°; R75 then R50/R50/R50 |
| Earlier total direction change | 296.7° |

The useful bass-reflex resonance near 39 Hz and the unwanted longitudinal port
mode near 338 Hz are different phenomena. The absorber is a side branch across
the port wall; it does not obstruct the bore and should have only small linear
flow at 39 Hz. High-level bass-driven slit jetting and noise remain experimental
risks, however.

## 4. Research basis

### 4.1 Hildebrandt (2024)

Malte Hildebrandt's bachelor thesis, *Dämpfung stehender Wellen in
Bassreflexrohren*, HAW Hamburg, is the closest physical precedent. The project
used a 3D-printed port with four approximately 50 × 0.2 mm longitudinal slits,
a 2 mm wall/neck, and about 123 cm³ total absorber volume. It reported a 653 Hz
simulated mode, about 675 Hz measured without enclosure foam, desired Q near
0.75–1, estimated as-built Q near 3.25, and about 19 dB reduction in the bare
case.

Primary source:

- [HAW repository record](https://reposit.haw-hamburg.de/handle/20.500.12738/16061)
- [German thesis PDF](https://reposit.haw-hamburg.de/bitstream/20.500.12738/16061/1/BA_D%C3%A4mpfung_stehender_Wellen.pdf)

The thesis establishes that the general class of printed slit-fed side-branch
absorber is viable. It does not quantitatively validate our impedance model.
Putting the thesis dimensions into our present parallel-plate calculation gives
about 299 kPa·s/m³ and `ωM/R = 1.16` at 653 Hz, versus the approximately
85 kPa·s/m³ and Q 3.25 comparison reported in the supplied analysis. This
factor-of-about-3.5 mismatch must be resolved before calling either result a
cross-validation.

### 4.2 Aulitto et al. (2021, 2022)

The end correction of a slit is not one universal multiple of hydraulic
diameter. It depends on shear number, porosity, edge geometry, neighboring
walls, and whether the relevant correction is inertial or resistive.

- Aulitto, Hirschberg, and Lopez Arteaga, “Influence of geometry on acoustic
  end-corrections of slits in microslit absorbers,” JASA 149(5), 2021,
  [DOI 10.1121/10.0004826](https://doi.org/10.1121/10.0004826).
- Aulitto, Hirschberg, Lopez Arteaga, and Buijssen, “Effect of slit length on
  linear and non-linear acoustic transfer impedance of a micro-slit plate,”
  *Acta Acustica* 6, 2022,
  [DOI 10.1051/aacus/2021059](https://doi.org/10.1051/aacus/2021059).

These papers support exposing end corrections as uncertain inputs and treating
nonlinearity as level-dependent. They do not make the present curved 40 mm
duct, irregular D cavity, and finite racetrack tips equivalent to their test
specimens.

### 4.3 Fable Rev. C: what reproduced and what did not

The supplied Fable report correctly identified the missing viscous dynamic
density of the slit. At 334.7 Hz for a 0.4 mm parallel-plate gap, our independent
implementation gives

\[
\rho_\mathrm{eff}/\rho = 1.192593 - j0.566127,
\]

matching the report's approximately 19% added oscillating mass. The checked
low-frequency limits also reproduce `Re(ρ_eff)/ρ → 6/5` and the Poiseuille
resistance exactly; the high-frequency density approaches bulk air.

The report also correctly redirected attention from a geometry-only Q of 3.62
to the actual complex slit impedance. For the old geometry and its old
0.651 mm end assumption, we obtain Q 2.03 and `R/Z₀ = 2.04`.

The following Fable claims are not promoted to canonical facts:

- “292–309 Hz before any end-correction argument” conflates viscous mass with
  end correction. Viscous mass with zero added end length gives 325.78 Hz; the
  292–309 range requires added inertance.
- Its exact −25 to −27 dB plateau was generated by scripts that were not
  supplied. Our 1-D result varies strongly with assumed bare-port loss and
  source/load definition.
- Its “width 0.35–0.50 mm all works” conclusion is too relaxed as a tuning
  statement. At fixed Rev. D length and the same end-factor rule, 0.35, 0.40,
  0.45, and 0.50 mm predict approximately 318.3, 337.2, 354.6, and 370.9 Hz.
- Placement remains consequential, although the current installed position is
  close enough to the antinode to retain 99.3% normalized pressure amplitude.
- The low-frequency slit-velocity/Strouhal table is an order-of-magnitude
  screen based on an approximate pressure gradient, not a nonlinear safety
  prediction.

The Fable report materially improved the design direction. Its strongest
contribution was the correct viscous mass/resistance framework; its strongest
overreach was treating conditional 1-D attenuation and tolerance flatness as
hardware-robust conclusions.

## 5. Governing model

### 5.1 Racetrack geometry

For gap width `w` and tip-to-tip length `h`, one racetrack opening has

\[
A_s = w(h-w)+\frac{\pi w^2}{4},
\]

\[
P_s = 2(h-w)+\pi w,
\qquad
D_h=\frac{4A_s}{P_s}.
\]

With `N=4`, total area is `S=N A_s`. For Rev. D, `S=14.368627 mm²`, about
1.143% of the 40 mm bore area.

### 5.2 Exact viscous parallel-plate density used here

For the `exp(+jωt)` convention,

\[
\rho_\mathrm{eff}(\omega)
=\frac{\rho}{1-\tanh(\beta)/\beta},
\qquad
\beta=\frac{w}{2}\sqrt{\frac{j\omega}{\nu}},
\qquad
\nu=\mu/\rho.
\]

The distributed neck impedance is

\[
Z_\mathrm{dist}
=j\omega\rho_\mathrm{eff}\frac{t}{S}.
\]

The implementation adds explicit, independently sweepable inertial and
resistive end terms. It does not hide them inside the physical depth.

The cavity compliance is

\[
C=\frac{V}{\rho c^2},
\]

and the branch impedance is

\[
Z_b(\omega)=Z_\mathrm{neck}(\omega)+\frac{1}{j\omega C}.
\]

Resonance is the root of `Im(Z_b)=0`. The generalized series-resonance Q is

\[
Q=\frac{\omega_0}{2R(\omega_0)}
\left.\frac{dX}{d\omega}\right|_{\omega_0}.
\]

The slope-Q for the old reference case is 2.0288; an independent numerical
half-power calculation gives 2.0472, a 0.9% difference.

### 5.3 What is not in the branch model

This is a linear viscous model, not a complete “full thermoviscous” solution.
It omits thermal bulk-modulus/compliance correction, finite-racetrack-tip
sidewalls beyond the area/perimeter geometry, 3-D entrance flow, local backing
inertance, leakage, wall compliance, roughness, taper, and nonlinear separation.
The current minimum radial cavity backing is 3.313 mm and deserves future 3-D
checking.

## 6. Width, length, depth, viscosity, Q, and volume

### Width

Width is the most sensitive manufactured variable. In the narrow parallel-
plate limit,

\[
R\sim\frac{12\mu t}{Nhw^3},
\]

so a small gap change strongly alters resistance, Q, and frequency. At the
338.25 Hz target, the viscous boundary-layer thickness is 0.11894 mm and
`w/δv = 3.363` for a 0.4 mm gap. The layers interact substantially.

Do not interpret the target as “0.4 mm nominal from the slicer.” The finished
gap must be post-processed and measured. A practical first acceptance band is
0.40 ± 0.02 mm if achievable; ±0.05 mm is useful for experimentation but is not
acoustically precise.

### Length

At fixed width and depth, more length gives more open area and raises the
branch center. Length is therefore the safest one-way trim after width is
established. Rev. D prints 0.30 × 4.00 mm sacrificial pilots and includes
witness lengths derived from the same viscous model:

| Finished gap | End-minimax tip-to-tip length |
|---:|---:|
| 0.400 mm | 9.066 mm |
| 0.500 mm | 7.509 mm |
| 0.600 mm | 6.460 mm |

These are alternative width/length pairs, not a suggested sequence of widening
the same 9.066 mm slot.

### Depth

The 5 mm passage increases both distributed mass and viscous resistance. It is
not free damping, but it makes the design less dependent on a separate mesh or
porous fill. The `t/w=12.5` aspect is mechanically convenient and remains the
chosen compromise. Changing depth requires re-solving area and volume.

### Chamber volume

For a simple Helmholtz scaling, `f ∝ sqrt(S/(V L_eff))`; larger volume lowers
frequency. Chamber shape is flexible only while it remains compact, rigid,
airtight, and well connected to every slit. The present D body preserves one
53.3298 cm³ air solid and a minimum 3.313 mm radial backing path.

The Rev. D decision keeps volume fixed and changes slit length because that
preserves the validated package and gives a one-way manual trim. Geometric
displacement plugs remain a reversible option for raising frequency, but are
not required for the first article.

### Q and duct loading

Low Q means wider bandwidth but not automatically stronger absorption. If
resistance is too small the duct mode can split into shoulders; if too large the
branch accepts too little flow. `R/Z₀` is therefore a more useful coupling check
than intrinsic Q alone. Rev. D's nominal `R/Z₀≈1.62` is promising, but the
resistive end prescription is empirical and the Hildebrandt mismatch prevents
claiming a validated optimum.

## 7. Four auditable models

The repository now contains four independent-purpose scripts:

1. `model.py` — racetrack geometry, complex parallel-plate density, neck and
   cavity impedance, resonance, Q, and length/volume solvers.
2. `duct.py` — 1-D transfer matrix for the physical path, linear inlet/outlet
   flares, low-`ka` radiation load, optional distributed attenuation, pressure
   profile, and side-branch shunt.
3. `verify.py` — asymptotic checks, Poiseuille check, passivity, determinant
   checks, Q cross-check, segment convergence, Hildebrandt comparison, and
   verification plots.
4. `robust.py` — width, length/end, volume/end, placement, assumed duct loss,
   and low-frequency screening sweeps with CSV/PNG output.

Example commands from the repository root:

```sh
python3 experiments/sand_cube_190x210_port_absorber_slotted_d_squat/model.py \
  --width-mm 0.4 --length-mm 9.066233 --depth-mm 5 \
  --volume-cm3 53.329815 --end-total-mm 1.1

.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_d_squat/duct.py \
  --width-mm 0.4 --length-mm 9.066233 --depth-mm 5 \
  --volume-cm3 53.329815 --end-total-mm 1.1 \
  --port-length-mm 508.081579 --branch-path-mm 273.88155 \
  --attenuation-np-m 0.1 --output-dir /tmp/rev-d-duct

MPLCONFIGDIR=/tmp/mpl .venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_d_squat/verify.py \
  --output-dir build/sand_cube_190x210_port_absorber_slotted_d_squat/modeling/verification

MPLCONFIGDIR=/tmp/mpl .venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_d_squat/robust.py \
  --output-dir build/sand_cube_190x210_port_absorber_slotted_d_squat/modeling/robustness
```

### Verification status

- all programmed assertions pass;
- parallel-plate low- and high-frequency limits pass;
- computed low-frequency resistance matches the Poiseuille expression;
- branch resistance remains positive from 20–2000 Hz;
- lossless segment and shunt determinants are unity;
- 80, 260, and 840 segment installed-route models converge to 338.35–338.40 Hz
  and a 255.31 mm antinode;
- the Hildebrandt quantitative mismatch remains explicitly unresolved.

### Conditional duct result

With a hypothetical distributed attenuation of 0.1 Np/m, chosen only to give a
bare-port Q around 27, the installed-route model gives:

| Comparison | Value |
|---|---:|
| Bare peak | 338.25 Hz in the detailed 260-segment run |
| Rev. D treated level at the bare peak | about −21.2 dB |
| Rev. D worst treated peak vs bare maximum | about −17.6 dB |
| Legacy geometry worst treated peak vs bare maximum | about −14.9 dB |

These are not hardware predictions. The fixed 1 Pa inlet, radiation load,
phenomenological line attenuation, omitted bend scattering, and unresolved
branch resistance all affect the numbers. The relative conclusion—Rev. D is a
better-centered starting geometry than the legacy 7.166 mm part—is stronger
than the absolute dB claim.

## 8. Rev. D CAD and manufacturing decision

Rev. D is a new folder and build namespace. No previous variant is deleted or
overwritten.

The body remains 74.967 × 76.934 × 30.000 mm with a 40 mm bore. A 3 mm base
tube wall and four local bosses create the 5 mm passages. The removable bucket
provides one common cavity. Separate socket adapters accept 40 ID / 46 OD and
40 ID / 50 OD host tubes.

The 9.066 mm slot could not remain centered at body z=15: it would leave only
1.565 mm upper boss land and violate the 2 mm rule. Moving all pilots, final
tools, and witness marks to z=12 centers them in the boss and leaves 4.467 mm
at both ends without enlarging the body or reducing the 6 mm common manifold
above the bosses.

Generated checks confirm:

- no body or connected-assembly material intrudes into the 40 mm airway;
- core and bucket do not intersect;
- the cavity is one connected air solid;
- all four finished slots intersect both bore and cavity;
- every exported STEP round-trips with matching valid-solid counts; and
- the support-free core, inverted bucket, adapters, and coupon remain separate.

Remaining mechanical caveats:

- the 0.30 mm pilots are guides, not trusted printed dimensions;
- the bucket still requires a real gasket and positive retention;
- the round socket plates are fit references, not a validated weight-bearing
  tower joint;
- the 50 mm-OD socket has limited plate overhang;
- the lower D rebate and both socket IDs need material/profile-specific fit
  coupons; and
- a future integration pass must import Rev. D in place of Rev. C and update
  the slot-center path rather than assuming the body midpoint is the opening.

## 9. Practical finishing and tuning

1. Print the curved coupon using the exact material, nozzle, orientation, seam,
   and slicer profile planned for the part. Coupon rail 1 includes a full
   9.066 mm-class slit; the other rails screen gap widths/orientations.
2. Inspect the sliced pilots. A missing or partly fused 0.30 mm negative feature
   is acceptable only if it leaves a controllable guide.
3. Open the gap uniformly from the chamber side. A jeweler's/piercing saw near
   the desired kerf, or abrasive film on a thin steel shim, is more plausible
   than side-milling with a fragile 0.4 mm drill/end mill.
4. Use measured feeler leaves as go/no-go references. A narrowed leaf is needed
   to check the full depth; an entrance-only corner check can miss taper or an
   hourglass profile.
5. Establish all four gaps before extending length. Record go/no-go width at
   multiple axial positions and both faces.
6. Start short and extend toward the 9.066 mm witness. Longer area raises the
   branch center. Remove small, symmetric increments from all four openings.
7. Deburr without adding a deliberate chamfer. Edge condition is not assumed
   irrelevant; it is simply less controllable than gap and length.
8. Leak-test the assembled chamber before interpreting any acoustic result.

## 10. Measurement plan

Use a calibrated microphone, fixed source level, fixed microphone position near
the outlet, and response plus decay/ringing:

1. Bare integrated port: locate the real first mode and bare Q.
2. Rev. D module installed with slits sealed: isolate the module body's effect
   on the duct.
3. Rev. D active at the printed/pilot state.
4. Finish width to the measured target and repeat.
5. Extend all four lengths symmetrically and repeat until the worst residual
   peak/decay is minimized—not merely the deepest point notch.
6. Repeat at several drive levels around the unwanted mode.
7. Run a loud 35–45 Hz test for hiss, buzz, compression, or changed reflex
   output. The present bass-frequency jet estimate is not a pass/fail model.
8. Recheck the low-frequency port alignment and useful output.

Before cutting, archive for every step: measured slit widths, tip-to-tip
lengths, temperature, sealed cavity volume/configuration, microphone geometry,
drive level, frequency response, and decay.

## 11. Highest-value unresolved questions

1. What finite rectangular/racetrack thermoviscous correction replaces the
   infinite parallel-plate approximation for this 9.066 × 0.400 × 5.000 mm
   passage?
2. What inertial and resistive end corrections apply to the actual curved duct,
   low porosity, rounded tips, irregular common cavity, and 3.313 mm minimum
   backing?
3. Why does the same model disagree with the Hildebrandt resistance/Q
   comparison by about 3.5×?
4. What bare Q and source impedance does the printed folded port actually have?
5. At realistic port velocities, do the four narrow slits hiss or become
   amplitude-dependent at 39 Hz or near 338 Hz?
6. Is the 53.33 cm³ cavity sufficient once leakage, wall compliance, and 3-D
   flow are included?
7. Would a second staggered chamber improve measured residual shoulders enough
   to justify the added printing and sealing complexity? Do not divide the
   cavity until one measured resonator establishes the real defect.

## 12. Local files

- Preserved external report: `FABLE_REV_C_REPORT.md`
- Historical Rev. C design: `README.md` and
  `generate_port_absorber_slotted_d_squat.py`
- Four models: `model.py`, `duct.py`, `verify.py`, `robust.py`
- Model outputs: `../../build/sand_cube_190x210_port_absorber_slotted_d_squat/modeling/`
- Rev. D source:
  `../sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/`
- Rev. D generated CAD:
  `../../build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/`

## Bottom line

Fable was directionally right that viscous dynamic density changes both tuning
and damping, and that the old Q=3.62 calculation was not sufficient. Reproducing
the calculation showed that the old 7.166 mm geometry is tuned too low, while
the exact amount depends strongly on uncertain end corrections. The updated
Rev. D part keeps the printable 5 mm-deep, mesh-free, one-cavity architecture,
but sizes the openings for the actual 508.08 mm integrated route and preserves
enough boss land to manufacture them safely.

Rev. D is the right first measurement article. It is not a validated production
absorber until bare-port measurement, slit metrology, leak testing, drive-level
tests, and the unresolved thesis/model normalization are closed.
