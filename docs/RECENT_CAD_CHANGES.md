# Recent CAD Changes

This note summarizes the CAD work brought onto `main` after the 8.5 in Sand Cube enclosure and horn assembly cleanup.

## 220 mm Horn Mouth

- Updated the B&C DE250 JMLC horn target in `params.py`.
- Changed `horn_mouth_outer_d` from `218.37` to `222.463`.
- The calibrated exported horn mouth bounding box is now approximately `220.0 mm x 220.0 mm`.
- The DE250 adapter, flange, bolt pattern, throat, rear spigot, and bracket interface dimensions were left unchanged.
- This change was made to match the newer third-party `220 mm` enclosure envelope.

## STL Connector Recess Experiments

The following derived STL files were created in the Downloads folder for physical fit testing of the GX16/GTX-style rear connector on the third-party unibody enclosure STL:

- `OSS V1.0 - Unibody Main Enclosure - GX16 rear recess 24x5.stl`
- `OSS V1.0 - Unibody Main Enclosure - GX16 inside recess 24x7.stl`
- `OSS V1.0 - Unibody Main Enclosure - GX16 inside recess 24x3p5.stl`
- `OSS V1.0 - Unibody Main Enclosure - GX16 inside recess 24mm 4mm web.stl`
- `OSS V1.0 - Unibody Main Enclosure - GX16 15p8 hole 24mm recess 4mm web.stl`

The latest fit-test version uses:

- Existing outer/front connector recess: `20.0 mm` diameter.
- New inner/back connector recess: `24.0 mm` diameter.
- Remaining material thickness between recess floors: `4.0 mm`.
- Through-hole diameter: `15.8 mm`.

Those STL files are not stored in git because they were generated under `~/Downloads` from an external STL source.

## Third-Party Enclosure Measurements

The inspected third-party unibody enclosure STL measured:

- Overall enclosure envelope: `220 mm x 220 mm x 220 mm`.
- Passive radiator through opening: `156.0 mm`.
- Passive radiator flange recess: `183.0 mm`.
- Front driver/black-hole opening: approximately `130.2 mm`.
- Dual-wall stack: `3 mm` outer skin, `12 mm` void, `3 mm` inner skin.

This is similar to the Sand Cube design intent but not identical to the repo-generated `215.9 mm` enclosure.
