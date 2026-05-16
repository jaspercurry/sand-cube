# 8.5 In Sand Cube Black-Hole Front Experiment

This experiment keeps the Sand Cube rear hardware pattern but scales the outer
enclosure to 8.5 in and replaces the small front baffle recess with a face-scale
black-hole recess.

The front baffle is modeled as an integrated wall:

- visible face-scale black-hole curve
- flat rear driver-seat annulus integrated into that wall
- cavity-side relief that follows the front curve where possible
- no separate cylindrical standoff for the driver

Run from the repo root:

```bash
python experiments/sand_cube_8_5_black_hole/generate_variants.py
```

Outputs are written to `build/sand_cube_8_5_black_hole/`.

The current best direction is the 1 in curve-to-seat model with a contoured
inner front wall:

```bash
python experiments/sand_cube_8_5_black_hole/generate_contoured_inner_variants.py
```

Those outputs are written to
`build/sand_cube_8_5_black_hole/contoured_inner/`.
