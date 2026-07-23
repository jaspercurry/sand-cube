# Geometry gotchas

## Build123d

- Revolve a profile drawn on `Plane.XZ` around `Axis.Z`; keep its radial
  coordinate in `x >= 0` and assert the sketch area is positive.
- Give recessed-baffle blend splines tangents at both endpoints: horizontal-in
  and vertical-out for the driver recess.
- Select circular fillet edges with geometry type plus a radius predicate, not
  circular shape alone.
- Keep sand-void bracing point-like—cylindrical posts and corner gussets—unless
  the active design explicitly validates fill and drainage. Avoid closed ribs
  that trap sand or air.

## JMLC horn and Onshape

- For the B&C DE250 JMLC horn, build the exact revolved acoustic surface,
  thicken it into a wall, and convert it to NURBS before STEP export.
- Do not reuse the explicit inner/outer meridian-wall construction for the
  rolled-back horn without a fresh Onshape import check. Local OpenCascade
  validity can still produce a transparent one-sided skin downstream.
- Cut the adapter/flange acoustic path with the same JMLC profile and make it
  meet the horn wall exactly. Positive radial clearance can leave a separate
  solid that `_primary_shape()` silently discards.
- Healthy horn STEP evidence is one solid, no boundary or non-manifold edges,
  no self-interference, and no `OFFSET_SURFACE` entities. Still perform the
  final Onshape import check for risky horn/adapter topology.

## Folded horn bracket

- Keep the base, bend, and upright at the same 4 mm sheet thickness; model a
  real bend rather than a sharp inside corner.
- In `src/features/bracket.py`, check the final bounding box after the
  `Plane.XZ` upright extrusion. The wrong direction previously placed the
  upright one thickness forward in `-Y` and created a 4 mm face gap.
- Numerically check bracket front/rear faces, horn-spigot rear face, and driver
  mounting face after every bracket or adapter change.
- Keep the bracket throat hole oversized. The printed spigot passes through
  the metal and meets the compression-driver face directly, keeping sheet
  metal outside the acoustic path.
