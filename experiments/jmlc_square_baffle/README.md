# JMLC Square Baffle Experiment

This folder explores a square-cropped Le Cleac'h/JMLC-inspired front baffle for
the sand cube without touching the production enclosure generator.

Run from the repo root:

```bash
python experiments/jmlc_square_baffle/explore_variants.py
```

Generate STEP files for the corrected visible-flare 140 degree variants:

```bash
python experiments/jmlc_square_baffle/generate_visible_flare_cubes.py
```

Outputs are written to `build/jmlc_square_baffle/`:

- `variants.json`
- `variants.csv`
- `profiles_by_mouth.png`
- `profiles_square_mouth_by_exit_angle.png`
- `profiles_320_mouth_by_exit_angle.png`
- `visible_flare_140/*_visible_flare_cube.step`
- `visible_flare_140/visible_flare_140_comparison.step`
