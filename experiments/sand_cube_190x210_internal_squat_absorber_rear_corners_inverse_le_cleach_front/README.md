# Inverse Le Cléac'h front-profile solver

This isolated study solves a virtual parent horn for the authoritative
rear-corner enclosure without generating CAD geometry.

The calculation calls the repository's direct transcription of Jean-Michel
Le Cléac'h's 2007 `pavillon_JMLC.xls` recurrence (workbook cells B24:H4028).
It does not use the faster exploratory JMLC approximation.

The default solve fixes the virtual parent throat to the authoritative
variant's existing 130.5 mm woofer opening and a 60 degree throat half-angle.
For each requested corner
pullback it solves cutoff frequency and the spreadsheet `T` parameter so that:

- the unique 90 degree/frontmost crest is at the existing 87 mm black-hole
  radius; and
- the actual R8 cabinet diagonal corner is pulled back by the requested amount.

Run from the repository root:

```bash
.venv/bin/python experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_inverse_le_cleach_front/solve_inverse_le_cleach_front.py
```

Use `--corner-pullbacks` to explore other values. Results and profile plots are
written to the matching isolated directory under `build/`.
