# Variant A — removable front baffle, simple tongue-and-groove seam

A leaf experiment on top of
`…_parabolic_side_g1_lightweight_coherent_closure` (the closure, imported as
`previous`).  It **monkeypatches the closure's front-joint hooks** — it never
edits any shared ancestor generator in place, and writes only under
`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/`.

The exterior parabolic-G1 skin (8 mm edge / 15 mm corner pullback, superellipse
sides, 4 mm rear roll, `edge_fillet_r = 8`) is preserved byte-for-byte; every
new feature is recessed behind the gasket shoulder.

## The one compression knob

`GASKET_CLOSED_GAP_MM = 1.0` in the generator module. Because the closure's
`source.SHOULDER_Y` is frozen at import from the *old* gap, `generate()` (and the
validation harness) patch **both** `source.GASKET_CLOSED_GAP_MM` **and**
`source.SHOULDER_Y = BAFFLE_BED_Y + GASKET_CLOSED_GAP_MM`, and restore both in a
`finally`. Every seam Y is derived from `SHOULDER_Y`/`BAFFLE_BED_Y`, so the whole
seam tracks the single number.

## Deleted vs kept

**Deleted** (all recessed seam cruft — never the exterior skin): the
outside-gasket face closure, the four baffle corner-closure panels, the 45°
continuous bucket front transition and its quadrants, the full-annulus
closed-skin probe, the captive-M4-nut apparatus, and the vestigial
SERVICE_BYPASS center dip in the gasket perimeter (`single._perimeter_wire` is
patched to run the top/bottom straight).

**Kept (user-mandated):** the gasket seal; the two front fill holes and their
hollow blister supports; a bucket gasket-shoulder land growing out of the
vertical front wall (restores `gasket_bucket_support_ratio`); the wall-stack
sand cap; a plain ~6 mm inner lip (baffle land); and one minimal baffle
stiffening rib.

## New joint

* **Top:** a continuous tongue-and-groove hinge (internal, `Z ≤ ~86`, zero
  exterior geometry). The enclosure front-lip carries a concave groove that
  wraps > 180° to capture the baffle's convex bead against lift-out; the baffle
  bead sits behind the enclosure lip to resist forward pull-out. Assembly:
  engage the top bead, pivot the bottom in. The nested plug/socket is replaced
  by a shallow top-only lead-in so the pivot does not jam.
* **Bottom:** two counterbored screws on the flat hidden print-underside into
  brass M4 heat-set inserts in the bucket (no snap fits), pulling the bottom to
  the same 1.0 mm gasket compression.

## Implementation status — all three stages VERIFIED GREEN

Validated through `cad_runner` with `validate_simple_tongue_groove_baffle.py`
(flags `BUILD_TOP_HINGE = BUILD_BOTTOM_SCREWS = True`). Every stage keeps:
single valid solid + STEP round-trip valid (bucket & baffle), **gasket support
1.0000 on both faces**, exterior bbox delta **0.0 on all axes**, isolation
restored + reproducible.

* **Stage 1 (seal):** cruft deleted, minimal seal, fills unobstructed + reach
  the void, sand cap sealed.
* **Stage 2 (top hinge):** straight-walled top-only lead-in split (replaces the
  nested socket); seal-safe pivot relief (keep-clear protected) giving
  **swept interference 0.0** across the −6° arc; convex bead / concave groove
  with a narrow neck so the front-lip overhangs the bead — **captured** against
  −Y pull-out (1.66 mm³) and +Z lift-out (7.93 mm³). Hinge Z = **83.0** (below
  the gasket band's inner edge at 85.6, the real constraint).
* **Stage 3 (bottom fastener):** two captive M4 hex nuts (adapted from the
  original geometry) at ±30 mm, 48° from vertical, baffle-service-face loaded,
  Ø12.5 blister clipped to the bucket side, head/shaft bores unobstructed
  (≤0.01 mm³), nut seat present, light retention rib. The only exterior effect
  is a <2 mm² sliver at the fairing's **hidden Z=−95 bottom edge** (the
  permitted bottom band); the front/sides/top stay byte-identical (bbox 0.0).

## Staging & validation

Stage flags `BUILD_TOP_HINGE` / `BUILD_BOTTOM_SCREWS` gate the retention
features. Geometry is validated through `cad_runner` with
`validate_simple_tongue_groove_baffle.py`, which drives the hooks directly on
the authoritative full-detail base solid and asserts every invariant (single
solid, STEP round-trip, gasket support ≥ 0.985 on both faces, exterior
identity, fill passages, sand-cap seal, isolation/restore).

> **Environment note.** The shared full cascade (`generate()` →
> `previous.generate()`) currently dies at an upstream *preview* step,
> `simplified._build_robust_viewer_cutaway`, which clips the **inherited**
> assembly and fails OCCT validity on this machine — this happens for the
> **unchanged baseline** too. All manufacturing geometry validates green; the
> failure is a rendering artifact of inherited solids, not of this closure.
> Geometry is therefore validated with the standalone harness (the same pattern
> the closure ships as `generate_bucket_front_transition_candidate.py`).
