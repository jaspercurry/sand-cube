# Square-Cropped Le Cleac'h Front with Post-Trim R8 Blend

This isolated enclosure-only study fixes the exposed legacy-fillet crescent in
the first 15 mm Le Cleac'h preview by reversing the construction order:

1. Generate the exact Le Cleac'h 2007 surface beyond the raw 190 x 190 mm
   square.
2. Cut that surface into a sharp square cabinet.
3. Apply the cabinet edge blend to the new three-dimensional perimeter.

The nominal R8 blend is evaluated at 7.999 mm because an exact 8.000 mm
rolling-ball fillet is mathematically tangent to the unchanged 87 mm
black-hole crest and degenerates in OpenCascade. The 0.001 mm relief is below
manufacturing resolution while keeping the operation robust.

The virtual horn is inverse-compensated so the *finished*, post-fillet physical
corner is 15 mm behind the black-hole crest. Functional assemblies are omitted
for this aesthetic preview, and the authoritative rear-corner experiment is
unchanged.

Run:

```sh
../../.venv/bin/python generate_sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_r8.py
```

Outputs are written to the matching directory under `build/`.
