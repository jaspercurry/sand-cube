# 190 mm exact-spreadsheet Le Cléac'h horn family

This folder contains two printable B&C DE250 horn variants generated from the
exact 2007 Le Cléac'h spreadsheet recurrence. Both use the shared
length-driven solver in `model.py`, fit a 190 mm physical mouth envelope, keep
the 82.3821368 mm acoustic axial length, and use the same throat, wall,
spigot, flange, and two-hole mounting pattern.

## Variants

| Variant | 140° rollback | 160° rollback |
| --- | ---: | ---: |
| Source folder | `variants/rollback_140/` | `variants/rollback_160/` |
| Physical diameter | 190.0001 mm | 189.9995 mm |
| Acoustic mouth diameter | 186.130 mm | 184.739 mm |
| Acoustic length | 82.3821 mm | 82.3821 mm |
| Solved profile cutoff | 1002.01 Hz | 1045.07 Hz |
| Solved wavefront `T` | 0.494374 | 0.232772 |
| Full STEP depth | 93.5220 mm | 98.0357 mm |

### 140° rollback

The 140° version is the original accepted 190 mm baseline. It has the larger
acoustic mouth and slightly lower solved profile cutoff, giving it a small
theoretical advantage near the bottom of the horn's operating range. It is
also 4.514 mm shallower than the 160° version.

### 160° rollback

The 160° version curls the final lip farther back. Greater rollback generally
reduces the abruptness of the mouth termination, so it may produce slightly
smoother mouth impedance, response ripple, and off-axis contours. Because the
physical diameter and length are held fixed here, its acoustic mouth is 1.49%
smaller by area and its solved profile cutoff is 4.30% higher.

The cutoff values above are parameters solved by the Le Cléac'h recurrence.
They are not recommended crossover frequencies or predicted system response.
An axisymmetric BEM simulation or measurement with the intended driver and
enclosure is required to quantify the acoustic difference.

## Layout

- `model.py` — shared length-driven Le Cléac'h solve and printable solid
- `params.py` — shared parameter schema
- `variants/rollback_140/` — 140° parameters, build, checks, and review record
- `variants/rollback_160/` — 160° parameters, build, checks, and review record

Each variant writes its STEP and diagnostics to the matching directory under
`build/workbench/le_cleach_horn_190/variants/`.

## Build

```bash
.venv/bin/python workbench/designs/le_cleach_horn_190/variants/rollback_140/build.py
.venv/bin/python workbench/designs/le_cleach_horn_190/variants/rollback_160/build.py
```

Run the 140° build first because the 160° validator confirms that the baseline
artifact remains unchanged.
