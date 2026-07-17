# 190 x 190 x 210 mm all-circular 39 Hz port study

This is an isolated fourth Sand Cube bass-alignment experiment. It leaves the
straight, single-U, and twin-inlet variants unchanged.

The enclosure is 190 mm wide, 210 mm deep, and 190 mm high. The side, roof,
and rear panels use a concentric rounded 2-3-2 mm skin / sand / skin stack.
The bottom is an untouched solid 7 mm plate and the contoured front keeps the
solid construction needed by the black-hole recess. The rounded wall layers
follow R8 / R6 / R3 / R1 surfaces from the exterior through to the acoustic
face, so the sand gap does not break through the exterior edge radii.

The acoustic airway is circular everywhere. Its constant-area bore is
39.243 mm in diameter (1,209.5 mm2), preserving the area of the earlier
44 x 35 mm oval while reducing wetted perimeter and eliminating section roll.
The low circular inlet is centered at (-61, -27, -62.763) mm and faces the
front of the acoustic cavity. It has 48.817 mm of axial breathing room to the
driver-seat plane, or 1.244 equivalent diameters, plus 1.463 mm lateral print
clearance to the left acoustic wall. A 15 mm circular flare feeds the constant
bore.

The route uses three controlled pieces: a 100.826 mm circular-plan sweep with
a 77.871 mm centerline radius and 74.186-degree turn, one rotated 70 mm-radius
quarter bend, and a 106.474 mm degree-eight upper drift. The first two curves
meet at an exact common tangent; the drift stays in one vertical plane, rises
monotonically, and never crosses or reverses relative to the centerline. The
round lower tube has a 3 mm wall and sits tangent on top of the inner floor at
z=-88 mm. No port-shaped channel or relief is cut into the floor.

The visible riser is the same circular acoustic profile from the roof to the
outlet. Only the printed wall changes: it thickens from 3 to 5 mm between
z=84 and 87.5 mm, entirely below the inner roof, then remains a constant
49.243 mm outer diameter above the enclosure. The riser centerline is at
y=82.5 mm. Its structural wall stays 0.879 mm ahead of the rear acoustic face
(0.579 mm including installation clearance), so it does not enter the rear
2-3-2 wall. The 58.583 mm circular outlet flare is also concentric with this
straight column.

The lower duct is a separate printable part with four integral mounting ears.
Two fasten downward into 4.8 x 5.0 mm blind insert pockets in the solid floor,
leaving a full 2 mm exterior layer. The rear-right return occupies the material
where a nominal right-side fastener would land, so the other two ears form one
broad left-side wing and fasten rearward into two separated pockets in the
cross-brace. All holes and tabs are relieved by the actual airway solid before
fusion, so no fastener intrudes into the acoustic passage. The nominal 0.30 mm
assembly clearance is clipped above the floor tangent; it never becomes a
floor channel.

The rising tower is installed from inside and is the sole visible
cabinet-to-horn support. There is no exterior mounting flange or secondary
horn stay. A 4 mm plate molded into the tower bears against the underside of
the roof, and a second 4 mm plate bears against the inner rear wall. The plates
form one rigid hidden L saddle. Two upward and two rearward screws pass through
the saddle into four 14 mm solid platforms bridging the 2-3-2 wall stack. The
platforms contain 4.8 x 6.5 mm blind pockets for heat-set inserts or
thread-forming plastic screws.

The rear retains the GX16 connector island, captive-nut pocket, and the pair of
sand-fill entries with their supported curved internal blisters. The redundant
floor bracing is removed: there is no bottom longitudinal rail, and the former
transverse window frame is now a top-and-side U frame. The top and both side
longitudinal rails still project exactly 10 mm into the cavity and meet the U
frame flush. Four identical constant-height front buttresses follow the exact
black-hole surface and fuse directly into its collar. The recess is completed
before those roots are added, so no later subtraction reopens a gap at any of
the four structural joints. A rear horizontal cross-brace remains as the
second cradle for the long internal duct.

The front restores the larger 200 mm design's black-hole driver recess. Its
16.93 mm visible depth is unchanged, while its outer diameter is reduced from
183 to 174 mm around the centered woofer. The contour reaches the tangent line
where the 8 mm cabinet edge radius begins.

The horn is regenerated from Jean-Michel Le Cleac'h's exact 2007 spreadsheet
recurrence rather than uniformly scaled. Holding the 25.4 mm throat,
8-degree throat half-angle, 140-degree terminal rollback, and mouth fixed while
solving for a 10.000 mm shorter acoustic axis gives T=0.49437398987356584,
a 1002.006 Hz profile cutoff, and an 82.382 mm acoustic axial length. The
finished rolled envelope is 190.000 mm and the acoustic mouth is 186.130 mm.
B&C specifies the DE250-8 exit as 25.0 mm, so the horn's 25.4 mm throat is not
an acoustic constriction.

The prior front-flush horn constraint is intentionally released for this
structural pass. The provisional horn envelope projects 4.0 mm ahead of the
cabinet front, its lowest edge remains 5.0 mm above the roof, and the measured
DE250-to-riser clearance is 1.357 mm. Final horn placement can be adjusted in a
later pass without changing the circular port architecture. The mount retains
only the horizontal 2 x M6 on 76 mm BCD pattern and uses three 10 mm round
spokes that wrap around the DE250 with the specified 2 mm nominal envelope gap.

The exact modeled net air volume is 4.570 L after the supplied woofer,
bracing, blisters, GX16 allowance, and complete 0.561 L in-box port envelope
are included. The final centerline is about 491.37 mm and its effective
acoustic length is about 518.54 mm. The outlet height is set for a 39.00 Hz
natural alignment. The modeled response still needs about 5.75 dB of DSP at
39 Hz for the flat moderate-volume goal, so a dynamic limiter and 28-30 Hz
fourth-order high-pass remain part of the design. Final EQ and any small port
trim must come from impedance and near-field measurements of a printed unit.

Run:

```sh
.venv/bin/python experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py
```

Generated STEP files, diagnostics, and static viewers are written under
`build/sand_cube_190x210_single_oval_port/`. The cutaway export includes the
enclosure, both tube pieces, woofer, GX16 connector, horn, and DE250. A
standalone exact horn STEP is exported as
`sand_cube_190x210_single_oval_port_horn.step`.
