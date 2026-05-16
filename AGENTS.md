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

## Horn / Onshape Import Gotchas

1. The B&C DE250 JMLC horn wall imports cleanly in Onshape when it is built as
   an exact revolved acoustic surface, thickened into a wall, then converted to
   NURBS before STEP export.
2. Do not use the explicit inner/outer meridian-wall construction for the
   rolled-back horn unless it is revalidated in Onshape. It can pass local
   OpenCascade validity checks while rendering as a transparent one-sided skin.
3. The adapter/flange acoustic cut must use the same JMLC profile and meet the
   horn wall exactly. A positive radial clearance can leave the adapter as a
   separate smaller solid; `_primary_shape()` may then silently discard it.
4. Healthy horn STEP export signs: one solid, no boundary edges, no
   non-manifold edges, no self-interference, and no `OFFSET_SURFACE` entities.

## Horn Bracket Gotchas

1. The folded horn bracket is a 4 mm sheet-metal part. Keep the base, bend, and
   upright at the same material thickness. Do not model the bend as a sharp
   inside corner.
2. In `src/features/bracket.py`, verify the `Plane.XZ` upright extrusion by
   checking the final bounding box. During debugging, positive extrusion placed
   the upright one material thickness forward in `-Y`, leaving a 4 mm gap
   between the metal bracket and compression-driver face.
3. The clamp stack must close exactly: bracket front face, bracket rear face,
   horn spigot rear face, and compression-driver mounting face should be checked
   numerically after every bracket or horn adapter change.
4. The bracket throat clearance hole is intentionally oversized so the 4 mm
   metal sheet is outside the acoustic path. The printed horn spigot passes
   through that oversized hole and meets the compression-driver face directly.

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
