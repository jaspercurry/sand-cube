# D-shaped ultra-squat slotted port absorber — preserved Rev. C geometry

> **Historical variant:** this 7.166 mm design is preserved for comparison and
> has not been overwritten. The checked viscous model shows it tunes below the
> current integrated-route mode. The current design authority is the
> [canonical engineering report](DEEP_RESEARCH_BRIEF.md), and the updated CAD is
> the separate
> [Rev. D variant](../sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/README.md).

This is a third, completely separate packaging experiment. It does not replace
the 68 × 120 mm cylindrical absorber or the 65 × 80 mm compact cylinder.

The 40 mm airway is moved close to a flat wall-facing side. The sealed chamber
bulges away from the speaker wall in a sturdy D-shaped body, allowing the same
approximately 53.33 cm³ chamber volume as the compact cylinder to fit in a body
only about 30 mm tall.

## Design intent

- preserve the uninterrupted 40 mm circular bore;
- preserve a 5 mm acoustic passage using local slot bosses on a 3 mm base wall;
- preserve four vertical, post-finished slots and a removable bucket;
- give every slot direct access to one connected common cavity;
- preserve the compact cylinder's chamber volume and 334.7 Hz target;
- minimize axial height by spending footprint away from the speaker wall; and
- keep the tube and both socket choices inside the flat wall tangent plane.

The generator solves the D arc radius from the target chamber volume, then
solves the slot length from the actual final CAD volume. Exact generated values
are recorded in `diagnostics.json`.

## Generated geometry

| Quantity | Value |
|---|---:|
| Body footprint | 74.967 × 76.934 mm |
| Absorber body height | 30.000 mm |
| Connected height including both 10 mm sockets | 56.000 mm |
| Solved outer-arc radius | 38.467 mm |
| Common chamber volume | 53.3298 cm³ |
| Bore | 40.000 mm |
| Base tube wall | 3.000 mm |
| Local slot passage depth | 5.000 mm |
| Finished slots | 4 × 0.400 × 7.166 mm |
| Printed pilots | 4 × 0.300 × 4.000 mm |
| Predicted finished center | 334.7 Hz |
| Smooth-wall Q trend before edge losses | 3.62 |
| Minimum local cavity behind any slot | 3.313 mm |

The final slot is centered axially. Its upper tip has approximately 2.42 mm of
solid local boss before that boss ends; the common chamber remains unobstructed
above it. This is the minimum accepted neck land in this study and must not be
consumed by tuning. If a longer slot becomes necessary, increase body height
rather than cutting beyond the boss.

## Manufacturing architecture

- The core prints vertically with the D-shaped lower floor on the bed.
- Four local neck bosses grow continuously from that floor, so their 2 mm
  projection beyond the 3 mm base tube wall needs no support.
- The bucket prints inverted with its D-shaped top closure on the bed.
- The flat side is vertical and requires no support.
- The two round tube adapters print separately with their plates on the bed.
- The lower D-shaped rim seats 0.5 mm into a matching locating rebate and uses
  a thin removable gasket during tuning.
- There is no collar, skirt, or locating ring inside the acoustic chamber.
- The upper seal is an external face gasket beneath the socket-adapter plate,
  spanning the small assembly clearance between the core and bucket top.

The D-shaped rebate provides translation and rotation alignment without using
chamber volume. It is still a packaging-study interface rather than a finalized
clamp. For production, add positive screws, a bayonet, or an external clamp
after the installation orientation is known. Do not rely on a friction fit to
seal a 53 cm³ resonator.

The very short body leaves less axial room around the slot than either cylinder.
Do not extend a slot past its calculated witness marks. Keep the bucket seal and
external top face-gasket surfaces clear of burrs, and pressure-test the common
chamber before acoustic measurement.

## Wall placement

The flat external plane is nominally 28.5 mm from the bore center. A full 5 mm
core would leave an unreliable 0.5 mm crevice at this face, so the base tube wall
is 3 mm and only the four slot regions extend to the full 5 mm neck depth. This
leaves a deliberate 2.5 mm common-cavity path between the base core and the
flat-side inner wall. Therefore:

- the 40 mm bore edge is 8.5 mm from the speaker wall;
- a 50 mm-OD host tube is 3.5 mm from the wall; and
- the largest socket adapter is tangent to the same wall plane.

The CAD tangent plane is a dimensional reference. Allow approximately 0.5–1 mm
between the printed flat and the real enclosure wall for wall texture, print
warp, and installation; the installed bore-center distance will therefore be
about 29.0–29.5 mm.

The four slots are rotated away from the directly wall-facing 180° direction.
This preserves several millimetres of local cavity behind even the closest slot,
while the large lobe on the opposite side carries most of the volume.

## Build

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_d_squat/generate_port_absorber_slotted_d_squat.py
```

Outputs are written only to
`build/sand_cube_190x210_port_absorber_slotted_d_squat/`.

See the parent
[science and tuning guide](../sand_cube_190x210_port_absorber_slotted_bucket/SCIENCE_AND_TUNING.md)
for the equations, Q limitations, and measurement procedure.

See the
[deep-research brief](DEEP_RESEARCH_BRIEF.md)
for the full research history, current system and CAD inputs, coupled
slot/depth/viscosity/Q/chamber trade-offs, print and feeler-gauge plan, open
uncertainties, and a copy-ready independent-validation prompt.

The externally generated
[Fable Rev. C report](FABLE_REV_C_REPORT.md)
is preserved separately and attributed. Its thermoviscous correction and other
claims are being reproduced in the repository models before they are promoted
into the canonical engineering brief.
