# Compact 6 In Speaker

Date: 2026-07-01

This note documents the compact speaker CAD added under `src/compact_6in/`.
The design is a smaller, one-piece, sand-filled enclosure plus a separate
6 inch Le Cleac'h/JMLC horn targeted at the Eminence F110M-8 compression
driver.

## Scope

- Added a separate compact speaker package in `src/compact_6in/`.
- Added `scripts/generate_compact_6in.py` for STEP export and diagnostics.
- Added compact STEP viewer targets in `src/show_model.py`.
- Kept the compact model independent of the larger split-enclosure work.
- Modeled the enclosure as a single printed body. The rear passive-radiator
  face is the print-down face.

## Enclosure Geometry

The enclosure is not a strict cube anymore. The front was allowed to grow in
depth so the recessed driver face has enough structure without stealing as much
air volume.

- Outer X/Z size: 152.4 mm, 6.0 in.
- Outer Y depth: 171.45 mm, 6.75 in.
- Wall stack on side/top/bottom faces: 3 mm outer skin, 6 mm sand void,
  3 mm inner skin.
- Rear cap: 12 mm.
- Front cap before relief: 31.05 mm.
- Acoustic cavity baseline: 128.4 mm cube.
- External edge radius: 8 mm.
- Internal cavity corner radius: 2 mm.

The sand void uses point-like cylindrical bridge posts. The void cutters are
kept clear of the exterior fillet zone so the rounded edges do not open visible
slots in the outer skin.

## Front Baffle

The compact enclosure carries forward the large enclosure's visual
"black-hole" driver face:

- The visible front face has a revolved black-hole recess.
- The driver is rear-mounted from the acoustic cavity side.
- The cavity-side front wall is relieved so it follows the visible baffle curve
  where possible.
- A flat internal driver-seat annulus is preserved for the driver and heat-set
  insert bores.

Current compact baffle parameters:

- Driver cutout: 93 mm.
- Visible baffle outer diameter: 132 mm.
- Baffle blend depth: 18 mm.
- Cavity-side baffle wall thickness target: 10 mm.
- Internal driver-seat land outer diameter: 112 mm.
- Driver bolt-circle assumption: 100 mm.

This matches the design principle used by the large final enclosure in
`experiments/sand_cube_8_5_black_hole/generate_contoured_inner_variants.py`:
leave a flat rear driver-seat annulus, then remove unused front-cap material so
the inner wall follows the outside black-hole contour.

## Rear Hardware

The rear face carries the passive radiator, GX16 connector, and sand fill
ports.

- Passive radiator: Dayton Audio DSA135-PR.
- Passive radiator cutout: 111.76 mm.
- Passive radiator recess diameter: 136 mm.
- Passive radiator screw count: 4.
- GX16 connector hole: 16.2 mm.
- GX16 location: rear lower-left corner.
- Sand fill ports: rear upper corners.
- Sand fill ports are unthreaded in this compact version.

Local collars are added around rear functional cutouts so sand cannot migrate
through the wall sandwich.

## Horn

The compact horn is separate from the enclosure.

- Target driver: Eminence F110M-8.
- Mouth target: 6.0 in outer diameter.
- Profile: Le Cleac'h/JMLC recurrence.
- Throat: 25.4 mm.
- Current exported horn mouth bounding box: about 152.4 mm.
- F110M interface: first-pass female 1-3/8 in 18 TPI screw-on adapter.

The export also includes a simplified F110M-8 fit envelope because no public
manufacturer CAD model was found during the first search pass.

## Acoustic Working Numbers

The compact CAD diagnostics from the latest verified export reported:

- Rectangular acoustic cavity: 2.117 L.
- Added front-relief acoustic volume: 0.136 L.
- Estimated net volume after nominal woofer and PR intrusion: 1.903 L.
- Estimated ND105-8 displacement: 0.20 L.
- Estimated DSA135-PR intrusion: 0.15 L.

The Dayton ND105-8 is a small high-Q driver for this box size. With the current
net volume, the sealed-box sanity check is roughly:

- Vb/Vas: about 0.64, using Vas = 2.97 L.
- Qtc: about 1.06.
- Fc: about 107 Hz.

That means the passive radiator is important. The DSA135-PR is a good
displacement match:

- ND105-8 Vd: 20.6 cm3.
- DSA135-PR Vd: 60.3 cm3.
- PR/woofer Vd ratio: about 2.93x.

First-pass PR tuning estimates for the current 1.903 L box:

- Fb 65 Hz: add about 8 g.
- Fb 60 Hz: add about 13 g.
- Fb 58 Hz: add about 15 g.
- Fb 55 Hz: add about 20 g.
- Fb 50 Hz: add about 28 g.

Recommended starting point: add about 15 g to the PR, measure impedance, then
adjust toward a 55-60 Hz tuning. Use a protective high-pass around 38-45 Hz if
DSP bass extension is applied.

## Build And View

Generate the compact exports:

```bash
uv run python scripts/generate_compact_6in.py
```

Outputs are written under `build/compact_6in/`:

- `compact_6in_one_piece_enclosure.step`
- `compact_6in_f110m_jmlc_horn.step`
- `compact_6in_f110m_fit_envelope.step`
- `compact_6in_f110m_jmlc_horn_placed.step`
- `compact_6in_horn_f110m_fit_stack.step`
- `compact_6in_system_preview.step`
- `diagnostics.json`

View the full compact preview in OCP CAD Viewer:

```bash
bash scripts/view_model.sh --target compact-system-step --tab clip
```

View individual STEP exports:

```bash
bash scripts/view_model.sh --target compact-enclosure-step --tab clip
bash scripts/view_model.sh --target compact-horn-step --tab clip
bash scripts/view_model.sh --target compact-horn-fit-step --tab clip
```

## Validation Status

The last verified generation passed these checks:

- Enclosure is one valid solid.
- Horn is one valid solid.
- Outer enclosure bounding box is 152.4 x 171.45 x 152.4 mm.
- Side, top, and bottom exterior skin probes showed no missing samples.
- Front driver land remained solid at the insert/seat region.
- Cavity-side baffle relief opened the area outside the 112 mm driver-seat
  land.

## Open Items

- Verify the ND105-8 bolt circle and rear mounting clearance against the actual
  driver or a manufacturer drawing.
- Verify the DSA135-PR bolt circle and gasket compression on the printed rear
  face.
- Print a small test coupon for the F110M screw-on horn adapter before trusting
  the printed thread.
- Measure the built box impedance to set the final PR mass.
- Revisit splitting the enclosure into front/body/back pieces only after the
  single-piece compact version is mechanically validated.
