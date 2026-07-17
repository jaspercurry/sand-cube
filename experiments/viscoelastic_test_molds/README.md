# Viscoelastic rebound test molds

This experiment contains two small FDM-printable tools:

1. A two-piece mold for a nominal **25 mm polyurethane ball**.
2. A circular tray that leaves a **40 mm diameter x 12.5 mm thick** test coupon
   supported in its mold for repeatable 15 mm steel-ball drop comparisons.

The dimensions are parametric near the top of
`generate_viscoelastic_test_molds.py`. Generated STEP and STL files are written
to the local `build/` folder.

## Generate the files

From the repository root:

```sh
uv run python experiments/viscoelastic_test_molds/generate_viscoelastic_test_molds.py
```

The most convenient print files are:

- `sphere_mold_two_piece_print_layout.stl` — both mold halves, cavity-up and
  support-free.
- `coupon_tray_two_up_print_layout.stl` — two identical test trays.

For a Bambu Lab X2D with a 0.4 mm nozzle, ready-to-slice PLA projects are also
provided:

- `25mm_sphere_mold_x2d_pla.3mf` — 0.12 mm High Quality, five walls, 30%
  gyroid, no supports.
- `40x12p5_coupon_trays_x2d_pla.3mf` — 0.20 mm Standard, four walls, 25%
  gyroid, no supports.

Open either project in Bambu Studio, select the PLA actually loaded in the
printer, confirm the build plate, slice, inspect the preview, and print. The
projects target Bambu PLA Basic at 220 °C with a 55 °C textured plate; use your
filament manufacturer's profile if printing another PLA.

Individual STL and editable STEP files are also generated. The script stops if
any individual part is invalid or ceases to be a single solid, and writes all
dimensions and geometry diagnostics to `build/diagnostics.json`.

Render a quick geometry preview with:

```sh
uv run python experiments/viscoelastic_test_molds/render_preview.py
```

## Design details

### 25 mm sphere mold

- Nominal finished sphere: 25.0 mm diameter, about 8.18 mL before sprue waste.
- Mold block: 48 x 48 mm; each half is 17.5 mm thick.
- Four integral 4.0 mm registration pins with 4.4 mm mating holes.
- Funnel socket: 6.6 mm diameter. This gives a measured 6.18 mm funnel stem
  0.21 mm radial clearance instead of relying on a nearly zero-clearance
  nominal 6.2 mm printed hole.
- The socket steps down to a short 4.0 mm pour gate to reduce the cured sprue.
- Two 1.2 mm witness vents near the high point prevent an inserted funnel from
  air-locking the cavity. Stop pouring when both vents show material.
- The equator is the parting line. Expect to trim a fine equatorial witness line
  and the three small sprue/vent nibs after cure.

Print the supplied orientation with the outside flat faces on the bed and the
cavities facing upward. This avoids support inside the mold surface. Use at
least four perimeters and a reasonably stiff material. PETG is a practical
choice, but a smooth, well-sealed mold surface matters more than the filament
name.

Before the first full casting, dry-fit the pins. Lightly ream the holes if they
bind; do not force the mold closed. Seal visible layer porosity and use the mold
release recommended for the casting material. Clamp the closed mold lightly
with two small clamps or opposing binder clips. Heavy clamping can bow an FDM
block and create an equatorial step.

### Coupon tray

- Finished coupon: 40.0 mm diameter x 12.5 mm thick, about 15.71 mL.
- Tray wall and floor: 3.0 mm.
- Fill slightly proud and strike once across the rim with a straight edge. Cure
  and test the sample while it remains in the tray.

The 12.5 mm thickness is deliberate. It matches the standard specimen thickness
used by ISO 4662 rubber rebound testing, and a 15 mm ball is within that method's
12.45–15.05 mm impact-tip range. This simple free-ball setup is still only a
comparative shop test: it does not reproduce the standard pendulum, impact
energy, holding force, or data reduction.

## Suggested comparison procedure

1. Print both trays in the same job and mark them before pouring.
2. Mix, pour, cure, and condition both materials at the same temperature and
   humidity. Compare them at the same age; seven days is a useful fully cured
   checkpoint for the published VytaFlex properties.
3. Put each tray on the same massive, rigid surface. Measure drop height from
   the **bottom of the ball** to the coupon surface.
4. Start with a 250 mm drop. Release without push or spin, centered on the pad.
5. Record from the side in high-frame-rate video with a vertical scale in the
   same plane as the ball. Avoid a wide-angle camera view.
6. Give each sample three conditioning drops, then record at least ten drops,
   alternating samples to reduce temperature and timing bias. Use the median
   rebound height.
7. Report rebound resilience as `100 x rebound height / drop height`. A lower
   value means more energy loss in this setup and is consistent with greater
   hysteresis. Hardness alone does not determine the result.

If a soft coupon visibly bottoms against the printed floor, reduce the drop
height or increase `coupon_depth` and regenerate both trays. Geometry, cure age,
temperature, release method, and ball condition must stay fixed for a useful
comparison.

## VytaFlex handling assumptions

This design assumes Smooth-On **VytaFlex 30 and 60**. The current manufacturer
technical bulletin lists 1:1 mix ratios by volume, mixed viscosities of 1,800
and 2,000 cP, pot lives of 30 and 60 minutes, and 16-hour cure times. It also
says vacuum degassing is not necessary, shrinkage is below 0.001 in/in, and
urethane is adhesive, so suitable sealing and release are important.

Manufacturer source: [VytaFlex Series technical bulletin](https://www.smooth-on.com/tb/files/Vytaflex_Series_TB.pdf)

Standards context: [ISO 4662:2017 overview](https://www.iso.org/standard/68111.html)
