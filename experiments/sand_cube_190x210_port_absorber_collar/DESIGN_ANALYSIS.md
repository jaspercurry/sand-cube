# Project-specific absorber-collar analysis

## Result in one sentence

Use a removable four-sector Helmholtz collar provisionally tuned to 345 Hz at
the lowest accessible part of the straight external tower, begin with all four
chambers identical and damped toward Q=0.75-1, and let the untreated-port
measurement set the final aperture diameters.

The 380 Hz value in the background documents is not used.

## 1. Current port and the unwanted modes

The current round-port experiment gives:

| Quantity | Value |
|---|---:|
| Main bore diameter | 39.2428 mm |
| Main bore area | 1,209.51 mm2 |
| Physical centerline length | 491.369 mm |
| Reported low-frequency effective length | 518.540 mm |
| Net enclosure volume | 4.57012 L |
| Bass-reflex tuning | 39.00 Hz |

The 39 Hz box/port resonance and the unwanted midrange pipe resonances are
different physical modes. The 39 Hz calculation reduces the port air to a
lumped inertance. A longitudinal mode requires distributed acoustic mass and
compliance along the duct.

The simplest open-open estimate is:

```text
f_n = n c / (2 L)
```

With c=343 m/s and the physical centerline, this gives 349.0, 698.0, 1047.1,
and 1396.1 Hz. Reusing the 518.540 mm low-frequency inertance length gives
330.7, 661.5, 992.2, and 1322.9 Hz. The latter is a useful lower bracket, not a
phase-accurate prediction.

The generator also cascades plane-wave transfer matrices for the physical
inlet flare, constant-area path, and outlet flare:

```text
             [ cos(kl)       j Zc sin(kl) ]
T_segment =  [                              ]
             [ j sin(kl)/Zc      cos(kl)   ]

Zc = rho c / S
```

It terminates the mouth with a low-ka unflanged radiation approximation. That
model predicts untreated peaks near 350.5, 700.0, 1048, and 1394 Hz. A variant
including a finite inlet spreading mass predicts about 344, 681, and 1019 Hz.
Both exclude driver electro-mechanics, detailed bend fields, thermoviscous
propagation, and flexible printed walls.

The defensible pre-measurement conclusion is therefore:

- search approximately 315-365 Hz for the first port mode;
- use 345 Hz as the mechanical prototype center;
- expect a second port feature around 0.66-0.70 kHz; and
- do not assume a 0.99-1.05 kHz feature is only the port.

The enclosure's first simple axial estimates are about 933 Hz in depth and
974 Hz in width/height, overlapping the third port band. Printed-wall radiation
can further confuse that region. The circular duct's first transverse cutoff
is around 5.1 kHz, so a 1D longitudinal model is appropriate for the bands of
interest even though the bends still perturb it.

## 2. Absorber equations

Each chamber is represented as a series acoustic RLC branch connected in shunt
to the main duct:

```text
Z_H = R_H + j (omega M_H - 1/(omega C_H))
Y_total = sum(1/Z_H,i)

M_H = rho Leff / A
C_H = V / (rho c^2)
f_H = c/(2 pi) sqrt(A/(V Leff))
```

The shunt transfer matrix is:

```text
      [ 1   0 ]
T_H = [       ]
      [ Y   1 ]
```

For a series resonator:

```text
Q = omega_H M_H / R_H = sqrt(M_H/C_H) / R_H
R_H = sqrt(M_H/C_H) / Q
```

The final relation is important: Q is in the denominator. The thesis prints
one equation with Q inverted, but its later numerical examples use the inverse
relationship above.

Four identical chambers have four admittances in parallel. If their volumes,
areas, and losses are equal, their center frequency remains unchanged while
their total shunt strength increases.

## 3. Neck length and end correction

The physical neck is 8.0 mm long and grows only outward from the unchanged
39.243 mm bore. For a small circular aperture in a locally planar wall, the
first estimate is:

```text
Leff = t + delta_duct + delta_cavity
delta_duct = 0.85 r
delta_cavity = 0.85 r
Leff = t + 0.85 d
```

The actual opening is flush in a curved finite duct and enters a sector-shaped
cavity rather than two infinite half-spaces. No transferable correction for
that exact geometry was found in the thesis. The generator therefore carries:

```text
Leff = t + beta d,  beta = 0.85 nominal, 0.70-1.00 sensitivity range
```

The neck radius is about 10% of the main-port radius, so local planarity is a
reasonable starting assumption, but measurement is still required.

## 4. Provisional dimensions

The generated default is:

| Feature | Nominal value |
|---|---:|
| Collar outside diameter | 100.0 mm |
| Axial length | 30.0 mm |
| Unchanged main bore | 39.2428 mm |
| Existing tower wall | 5.0 mm |
| Local physical neck/liner | 8.0 mm |
| Outer wall | 3.0 mm |
| Integral chamber floor | 3.0 mm |
| Bonded lid | 3.0 mm |
| Radial dividers | 2.4 mm |
| Chamber count | 4 |
| Gross volume per chamber | 26.141 cm3 |
| Damping displacement allowance | 0.250 cm3 |
| Net acoustic volume per chamber | 25.891 cm3 |
| Target per chamber | 345.0 Hz |
| Solved round neck diameter | 3.853 mm |
| Neck area per chamber | 11.659 mm2 |
| Effective neck length | 11.275 mm |
| Total neck area / main port area | 3.86% |

For each chamber at c=343 m/s and rho=1.204 kg/m3:

```text
M_H = 1164.3 Pa s2/m3
C_H = 1.8278e-10 m5/N
R_H(Q=1) = 2.524 MPa s/m3
R_H(Q=0.75) = 3.365 MPa s/m3
```

The numerical values in `diagnostics.json` come from the actual CAD cavity
volumes rather than an ideal annular-volume approximation.

## 5. Why four equal chambers first

| Architecture | Benefit | Drawback | Decision |
|---|---|---|---|
| One shared annular cavity | Maximum volume, few dividers | One leak or print defect compromises everything; no tuning experiments | Rejected for prototype |
| Four identical sectors | Maximum first-mode shunt strength; inspectable and fault-isolated | Requires a bonded divider seal | Selected |
| Four blindly staggered sectors | Broader nominal frequency coverage | Less admittance at the measured peak; may create shoulders | Defer until measurement |
| Two axial collars | Can address even and odd modes at their own antinodes | More volume, joints, flow openings, and mechanical complexity | Only if one location cannot solve measured modes |
| Membrane chambers | Potentially compact | Printed stiffness and boundary conditions make tuning unreliable | Rejected |

The thesis' coupled simulation favored absorber Q around 0.75-1. An isolated
resonator at Q=1 is already broad; the coupled notch width is not simply the
isolated resonator's -3 dB width. Staggering before measuring the untreated
port would trade away useful peak coupling based on an assumed problem.

The four sectors preserve the option to test a 2+2 split near 0.97f1 and
1.03f1. If the second mode remains objectionable, a separate smaller chamber
near f2 is preferable to giving a full 26 cm3 sector an unnecessarily large
opening.

## 6. Placement

The first-mode pressure maximum is near the acoustic midpoint, around 246 mm
from the inlet in the current TMM. That location lies in the curved upper
return with poor radial clearance.

The collar is instead centered 358.26 mm from the inlet, corresponding to
global z=110 mm and a z=95-125 mm span on the straight external tower. The
calculated pressure ratios relative to each mode's own maximum are:

| Mode | Bare modeled peak | Pressure at collar |
|---|---:|---:|
| First | 350.5 Hz | 0.752 (-2.47 dB) |
| Second | 700.0 Hz | 0.991 (-0.08 dB) |
| Third | 1048 Hz | 0.546 (-5.26 dB) |

This is a useful compromise: strong first-mode coupling, almost ideal
second-mode coupling, a straight printable host, access for testing, no
enclosure displacement, and clearance below the DE250 envelope.

## 7. Predicted effect and what not to overclaim

With four ideal Q=1 branches at 345 Hz, the lossless TMM predicts about 32 dB
reduction at its untreated first peak and about 19 dB at its untreated second
peak. It also shifts the residual response maxima because a resonant shunt
splits and reshapes the duct response.

Those are design-model numbers, not promised measurements. The model does not
include real duct loss, neck nonlinearity, mesh repeatability, bend scattering,
driver coupling, wall vibration, or cabinet radiation. Hildebrandt measured
about 19 dB attributable suppression in the cleaner configuration, which is a
better reality check than the ideal 32 dB result.

The same model moves the low-frequency coupled peak from about 39.28 to
39.25 Hz, a -0.03 Hz relative shift. The exact driver/port system still needs
an impedance and nearfield check, and 39 Hz output must be compared as well as
the frequency.

External placement displaces no box air. If this 100x30 mm envelope were put
inside around the existing 49.243 mm tower, its added gross envelope would
remove about 178.5 cm3 from the 4.570 L enclosure. Ignoring side-branch
compliance, that alone would move 39.00 Hz to roughly 39.78 Hz. An internal
version therefore requires complete volume and tuning recalculation.

## 8. Tolerances

For small changes:

```text
df/f ~= dc/c + dd/d - 0.5 dV/V - 0.5 dLeff/Leff
```

Because Leff also contains diameter-dependent end correction, the generator
recalculates rather than using only this differential approximation.

| Change from nominal | Predicted fH |
|---|---:|
| Neck diameter -0.15 mm | 333.46 Hz |
| Neck diameter +0.15 mm | 356.42 Hz |
| Physical neck -0.20 mm | 348.10 Hz |
| Physical neck +0.20 mm | 341.98 Hz |
| Cavity volume -5% | 353.96 Hz |
| Cavity volume +5% | 336.69 Hz |
| Speed of sound 340.3 m/s | 342.28 Hz |
| Speed of sound 349.0 m/s | 351.03 Hz |
| End beta=0.70 | 354.20 Hz |
| End beta=1.00 | 336.48 Hz |

Diameter and end correction dominate. Print the opening slightly undersize and
finish it with a measured drill or reamer. A controlled +/-0.05 mm aperture is
more useful than false precision in the CAD nominal.

## 9. Leakage and damping

Treat a cavity leak resistance as parallel with cavity compliance. Keeping the
compliance error near resonance below roughly 5% requires:

```text
omega R_leak C_H > 20
```

For one generated chamber this gives R_leak greater than about 50.5 MPa s/m3,
or a plugged-neck pressure-decay time:

```text
tau = R_leak C_H > 9.23 ms
```

The practical target is at least 50 ms for margin. Test each chamber before
installing it. A leak with its own inertance can also create an unintended
second resonance, so a visibly closed seam is not enough evidence.

Use a captured woven polyester acoustic mesh or another repeatable resistive
fabric on the cavity side of each neck. Bond its perimeter so no fiber can
reach the main airway. Do not loosely stuff the whole chamber: bulk fill alters
effective volume/compliance as well as resistance. The acoustic resistance
must be inferred from the measured collar Q; cloth type and layer count are
calibration variables.

## 10. Measurement-driven finalization

1. Measure the untreated mouth 5-10 mm away with a low-level 20-2000 Hz sweep.
2. Add a temporary 20 mm outlet extension. A 345 Hz pipe mode should fall by
   approximately 3-4%, while a cabinet or panel mode should not track length.
3. Measure electrical impedance and port nearfield together to confirm 39 Hz.
4. Fit the distributed model to measured f1, f2, and their widths.
5. Test four undamped equal chambers first to establish the real collar center.
6. Correct frequency by measured aperture diameter or cavity-volume plugs.
7. Add captured mesh incrementally and fit R_H/Q from the response and decay.
8. Test 2+2 staggering only if the untreated or residual band is broad.
9. Recheck box tuning, 39 Hz level, resonance decay, and electrical impedance.
10. Increase level in steps to expose neck turbulence, nonlinear resistance,
    distortion, compression, or resonance shift.

## References

- [Malte Hildebrandt, *Dämpfung stehender Wellen in Bassreflexrohren* (2024)](https://reposit.haw-hamburg.de/bitstream/20.500.12738/16061/1/BA_D%C3%A4mpfung_stehender_Wellen.pdf)
- [U. Ingard, *On the Theory and Design of Acoustic Resonators*](https://doi.org/10.1121/1.1907235)
- [H. Levine and J. Schwinger, *On the Radiation of Sound from an Unflanged Circular Pipe*](https://doi.org/10.1103/PhysRev.73.383)
- [M. R. Stinson, *The Propagation of Plane Sound Waves in Narrow and Wide Circular Tubes*](https://doi.org/10.1121/1.400379)
