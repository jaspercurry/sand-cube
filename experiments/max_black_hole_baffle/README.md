# Max Black-Hole Baffle Experiment

This isolated experiment makes sharp-corner 8 in cube blocks whose front face is
almost entirely a circular recessed baffle. The circular depression starts at
the largest circle that fits the square face and blends down to a 5.5 in driver
hole.

Run from the repo root:

```bash
python experiments/max_black_hole_baffle/generate_variants.py
```

Outputs are written to `build/max_black_hole_baffle/`:

- `depth_0_50in.step`
- `depth_1_00in.step`
- `depth_1_50in.step`
- `depth_2_00in.step`
- `max_black_hole_comparison.step`
- `diagnostics.json`

