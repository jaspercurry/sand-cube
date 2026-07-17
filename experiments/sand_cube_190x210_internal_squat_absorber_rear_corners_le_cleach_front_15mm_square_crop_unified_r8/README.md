# Square-Cropped Le Cleac'h Front with Unified R8 Perimeter

This isolated enclosure-only study removes the segmented front boundary and
corner patches from the staged-fillet square-crop experiment.

Construction order:

1. Generate the exact Le Cleac'h 2007 surface beyond the sharp 190 x 190 mm
   square.
2. Crop the sharp cabinet with that surface.
3. Round the eight non-front cabinet edges.
4. Apply all six topological front-perimeter edges simultaneously as one
   nominal R8 rolling-ball operation.

The two long halves of each side silhouette now meet only at the unavoidable
revolution seam. There are no short staged-fillet transition curves at the
front corners. The virtual horn is inverse-compensated to 10.0914 mm at the
pre-fillet physical-corner radius so the completed corner measures 15 mm.

The effective CAD fillet remains 7.999 mm to avoid exact tangency with the
unchanged 87 mm black-hole crest.

Run:

```sh
../../.venv/bin/python generate_sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm_square_crop_unified_r8.py
```

Outputs are written to the matching directory under `build/`.
