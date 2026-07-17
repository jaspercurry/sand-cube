# Internally installed ultra-squat absorber

This isolated integration study places the unchanged 40 mm-bore D-shaped squat
absorber inside the existing 190 × 210 × 190 serviceable-tower enclosure.

The right-side rise moves forward so the absorber's D-flat clears the rear
2-3-2 wall.  The old pair of 67-degree R50 offset elbows becomes a pair of
approximately 46-degree elbows around an exact 56 mm diagonal service straight.
The absorber sits on that straight with its flat face toward the rear wall and
its chamber lobe toward the open cabinet volume.

The original serviceable-tower experiment and the standalone absorber study are
not modified.

The installed absorber removes approximately 0.10 L of usable enclosure volume.
This packaging version preserves the established external outlet height and
therefore lands near 39.75 Hz naturally.  Recovering an exact 39.1 Hz without a
taller outlet would require approximately 19 mm of additional internal effective
length in a subsequent route pass.

Build with:

```sh
.venv/bin/python \
  experiments/sand_cube_190x210_internal_squat_absorber/generate_sand_cube_190x210_internal_squat_absorber.py
```

Outputs are written to
`build/sand_cube_190x210_internal_squat_absorber/`.
