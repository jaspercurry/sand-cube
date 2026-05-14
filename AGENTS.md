# Codex Operating Notes

This project uses build123d for a parametric speaker enclosure. Prefer small,
auditable feature commits and diagnostics after every geometry change.

## Build123d Gotchas

1. When revolving a profile drawn on `Plane.XZ`, use `Axis.Z`. Keep the profile
   entirely in `x >= 0`.
2. Splines used as recessed-baffle blend profiles must specify tangents at both
   endpoints. Use horizontal-in, vertical-out for the driver recess.
3. Avoid selecting circular edges by shape alone. If filleting circular edges,
   filter by both geometry type and a radius predicate.
4. After creating a sketch face for revolve, assert the sketch area is positive.
5. Keep bracing inside the sand void point-like: cylindrical posts and corner
   gussets only. Do not add closed ribs that can trap sand or air.

## Geometry Contract

- Nominal outer cube: 203 mm.
- Outer skin: 3 mm.
- Sand void: 12 mm.
- Inner skin: 3 mm.
- CAD units: millimeters.

## Workflow

1. Update `params.py` before geometry if a sourced hardware dimension changes.
2. Implement one feature at a time under `src/features/`.
3. Keep generated CAD in `build/`, which is ignored.
4. Run the geometry script after each feature and inspect diagnostics before
   moving on.

