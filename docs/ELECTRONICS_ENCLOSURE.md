# Electronics Enclosure

This documents the focused electronics enclosure layout for the hidden
Raspberry Pi 5, DAC HAT, four-channel amp, rear-mounted buck converter, and
rear service connectors.

The active CAD lives in `src/features/electronics.py` as the
`thin_plate_inline_separate_mic` variant. Earlier broad layout studies are
kept in the same file but are archived by `active_layout_variants()`.

## Active Layout

- Overall outside envelope: `166 x 124 x 60 mm`.
- Main box height: `57 mm`; screw-on lid thickness: `3 mm`.
- Orientation convention: the rear service face is `+Y`.
- When facing the rear:
  - Raspberry Pi rear USB/Ethernet ports are on the right.
  - Amplifier and GX outputs are on the left.
  - Buck converter mounts vertically on the outside rear face.
  - Microphone is intentionally external/separate for this iteration.

The active placement is a thin hidden plate intended to fit on a 256 mm square
printer bed while keeping the hardware accessible from the rear face.

## Component Fit

### Amplifier

- Active footprint: `94 x 108 mm`, rotated so the amp heat sink runs
  front-to-back, perpendicular to the rear service face.
- Clearance height: `36 mm`.
- Mounting rectangle:
  - Long axis center-to-center: `101.7 mm`.
  - Narrow axis center-to-center: `88.0 mm`.
  - Hole diameter assumption: `3.0 mm`.
- Printed stand-offs are `3 mm` tall for the current fit pass.

### Raspberry Pi 5 and HAT

- Pi service envelope in this enclosure: `56 x 90 x 42 mm`.
- Pi uses four front-to-back adjustment slots in the floor rather than fixed
  posts. This allows the real board/feet to slide until the USB/Ethernet faces
  land correctly in the rear openings.
- Rear I/O is split into three smaller bays instead of one large bridge:
  - left USB stack
  - middle USB stack
  - Ethernet
- A `10.83 mm` power input hole sits above the Pi rear I/O group, with slight
  vertical relief for FDM ovaling.

The Pi board dimensions and mounting pattern were based on Raspberry Pi 5 and
HAT mechanical drawings. The port windows remain fit-study geometry until the
real Pi/HAT stack and cable overmolds are validated.

### Buck Converter

- Rear-mounted vertical body envelope: `62 x 21 x 58 mm`.
- Rear locating pins:
  - Diameter: `5.8 mm`.
  - Projection depth: `4.0 mm`.
  - Center-to-center spacing: `53.67 mm`.
  - Pin center height: `29.0 mm` above the bottom of the buck body/enclosure.
- Bottom rear wire entry:
  - Width: `17.0 mm`.
  - Height: `3.0 mm`.
  - Through depth: wall thickness plus `5.0 mm`.
  - Internal chamfer: `6 x 6 mm` to reduce wire pinching.

### GX Outputs

- Two GX14-style four-pin output connectors provide four amp channels total.
- Through cutout size: `14.8 x 15.8 mm`.
- Recess size for the measured collar: `19.0 x 19.8 mm`.
- Measured collar OD: `18.06 mm`.
- Recess depth: `1.2 mm`.
- Centers are packed between the rear-mounted buck body and the rear-view left
  inner sidewall to reduce heat-sink interference risk.

## Lid and Printing Details

- Lid is a separate part with four recessed cheese-head screw holes.
- The base has four corner screw receivers:
  - Boss OD: `10.0 mm`.
  - Self-tap pilot diameter: `2.5 mm`.
  - Screw engagement: `2.0 mm`.
  - The receiver uses a short lofted, wall-grown ramp so it does not need full
    height pillars down to the floor.
- Top, side, front, and bottom vents use small print-friendly openings instead
  of long unsupported bridges.
- The fast-fit print variant thins walls/floor/lid to `1.6 mm` and uses a
  faster suggested PLA profile for layout validation.

## Generated Files

Generated CAD and 3MF files are written under `build/electronics_enclosure/`.
`build/` is ignored by git, so regenerate these files after cloning or after
geometry changes.

Main printable 3MF exports:

- `build/electronics_enclosure/thin_plate_inline_separate_mic_base_with_standoffs.3mf`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_screw_on_lid.3mf`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_fast_fit_base.3mf`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_fast_fit_lid.3mf`

STEP exports for inspection:

- `build/electronics_enclosure/thin_plate_inline_separate_mic_printed_enclosure.step`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_electronics_assembly.step`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_base_with_standoffs.step`
- `build/electronics_enclosure/thin_plate_inline_separate_mic_screw_on_lid.step`

## Commands

Generate STEP/layout study files:

```bash
python scripts/generate_electronics_enclosure_layouts.py
```

Generate printable 3MF files:

```bash
python scripts/generate_electronics_3mf.py
```

Open the normal OCP CAD viewer target with the lid separated:

```bash
bash scripts/view_model.sh --target electronics-open-lid --tool distance --tab tree
```

## Open Fit Items

- Validate the Pi rear I/O vertical position with the real removable feet.
- Replace the Pi floor slots with fixed screw holes after the fit position is
  known.
- Re-check GX connector fit after printing because rear-wall circular holes can
  print slightly undersized or oval.
- Validate buck converter noise and wire routing near the amp before treating
  the rear-mounted buck position as final.
- If Bambu Studio reports floating regions, first check the short horizontal
  rear buck pins. They are connected to the rear wall but can look like tiny
  cantilevers to a slicer.
