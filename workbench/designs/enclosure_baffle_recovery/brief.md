# Fresh-context master prompt — enclosure/baffle recovery

Paste the block below into a new session. It is self-contained but points to
the full record in `HANDOFF.md` in the same directory.

---

We are working in `/Users/jaspercurry/Code/CAD - Enclosure`, a build123d
parametric speaker enclosure. First read `AGENTS.md`, then read
`experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/HANDOFF.md`
in full. The handoff is the authoritative record of a previous attempt that
built green but was physically wrong; it lists the exact issues, the corrected
architecture, and the mistakes to avoid. Do not skip it and do not start by
running a build.

## The vision

There are two variants with the same visible exterior but different
serviceable faces:

- **Variant A (this task), front-baffle hatch:** a removable front baffle that
  prints vertically, standing on a genuinely flat bottom edge with a brim. It
  is retained by a continuous top tongue-and-groove pivot hinge plus two bottom
  captive-nut screws. The enclosure bucket itself is intended to print from
  its rear/back face upward.
- **Variant B (later), bottom hatch/port:** integral front, removable bottom
  hatch, printed bottom-down. Do not start it. Its roof-bridging and
  port/floor-re-anchoring gates are documented in `HANDOFF.md`.

The most important interpretation is that “keep the seam between the baffle
and enclosure the same” means the **sculpted nested seam geometry**—the elegant
interface and its corner sealing—on the **left, right, and top**. It does not
mean merely preserving the visible exterior skin.

## Newly confirmed, concrete good reference: the baffle

The current independent baffle viewer shows the bottom treatment the user was
asking for: the baffle has a real, flat bottom face and can stand vertically on
the print bed. Its left/right/top sculpted seam and overall seam design are
also the right starting point.

Before running any generator that might overwrite `build/`, inspect this exact
artifact:

`/Users/jaspercurry/Code/CAD - Enclosure/build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_baffle.step`

Quick viewer:

`http://127.0.0.1:3939/baffle/viewer/?refresh=1641`

Treat this baffle as a **geometric reference for the approved flat bottom face
and the overall seam design**, not as proof that the pair is finished. The
enclosure was never updated to complement that bottom geometry. The current
bucket is therefore mismatched:

`/Users/jaspercurry/Code/CAD - Enclosure/build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_bucket.step`

Quick viewer:

`http://127.0.0.1:3939/bucket/viewer/`

The next design must transfer/remove the matching bottom region from the
bucket so the baffle owns the flat print base and the two parts form one
intentional complementary bottom seam. Do not undo or round away the baffle’s
approved flat bottom. Preserve the existing sculpted seam placement on the
left, right, and top.

## Corrected architecture: a hybrid seam

- **Left/right/top:** retain or restore the original sculpted nested seam
  exactly. This includes its functional corner sealing, not just its visible
  outline.
- **Bottom only:** use the flat seam required for the vertically printed
  baffle. The exterior may change only below the bottom corner, which the user
  has approved.
- Inherit what already works and make the bottom relationship complementary.
  Do not delete the whole seam and rebuild a generic lip.

Keep the 1.0 mm gasket compression controlled by one tunable constant. Keep
the validated continuous top tongue-and-groove hinge concept, but integrate it
with the preserved top sculpted seam. The two bottom screws remain future
work after the seam and bottom ownership are physically correct.

## Current bucket defect that must be diagnosed by provenance

There is still unintended material in front of the upper fill holes, visible
as a very specific curved/triangular solid with depth, and related small
segments appear near the corners/outside. Multiple attempted cleanups failed
and the obstruction returned. Do not call it a viewer or tessellation artifact
and do not add another downstream subtraction as a blind patch.

Probe the geometry in X/Y/Z around the complete front bulkhead plane and trace
the obstructing solid back to the exact source feature/boolean that creates
it. Inside the intended enclosure perimeter, that plane must be clear except
for the deliberate gasket/bulkhead structure. At all four corners, distinguish
intentional sealing material from stray closure fragments.

The fix must preserve all of the following:

- the external bucket skin and silhouette;
- the fill-hole locations, diameters, and clear passages;
- the wanted fill blisters (do not remove the blisters);
- the gasket face and its inner perimeter;
- the sculpted left/right/top seam and corner sealing.

Prefer removing or replacing the operation that creates the stray structure.
If a subtraction is genuinely the correct first-principles construction, it
must be part of a clear canonical bulkhead definition—not a late “hide the
artifact” patch.

## First-principles cleanup direction

The user wants this enclosure code to become simpler, more elegant, modular,
and easier to alter without reviving legacy fragments. A promising canonical
construction is:

1. Define the external bucket shell once.
2. Define the planar front bulkhead/gasket support as a simple slab with
   explicit thickness.
3. Clip away everything outside the bucket’s intended outer boundary.
4. Clip away everything inside the gasket face’s inner perimeter.
5. If support is needed below the planar lip, generate a simple downward
   triangular/ramped web following the inner perimeter until it intersects the
   vertical inner wall. Control its landing height or angle with one explicit
   parameter.
6. Cut the two sand-fill passages through the final canonical result so they
   are guaranteed clear while their external blisters remain.

The enclosure walls are vertical and the gasket/bulkhead bottom is planar, so
do not preserve complex legacy corner-cap machinery unless inspection proves
it provides required geometry that the simple clipped slab/web cannot. This
is permission to refactor deliberately, but not permission to change the
external shell, gasket shape, or the approved L/R/T seam. First compare the
simple construction to the real reference geometry and show the user the
relevant section.

## Bottom fasteners, after the seam is approved

Do not design the gasket reroute first. Place the two screw axes so the screws
physically work: clear straight-down insertion, no exterior-edge breakthrough,
and no contact with the gasket face. A slightly more bottom-normal tilt can
raise the entry, but must remain bounded so the bore misses the captive M4 nut
slot. Use baffle-face-loaded captive hex nuts, not heat-set inserts. Show the
placement to the user before continuing. Only then reroute the bottom gasket
face around each screw as arc-up → flat → arc-down, with matching faces on both
parts, and make the bottom seal one continuous connected piece.

## Physical invariants

Green boolean numbers are necessary but not sufficient. Encode and inspect:

- screw insertion clearance;
- no exterior-edge breakthrough except the approved bottom band;
- gasket-face clearance;
- seam identity on the actual left/right/top seam, not a proxy outer-skin
  fingerprint;
- outside-gasket corner closure with no gap behind the seal;
- bottom-seal continuity;
- fill-passage clearance after every closure/bulkhead operation;
- matching complementary geometry between the approved baffle bottom and the
  revised bucket bottom.

## Internal tube context—do not integrate it yet

Once the enclosure packaging and serviceable seam are settled, a separate
printed internal acoustic tube assembly will be inserted. Keep it in mind for
space, access, and future mounting, but do not pull it into this seam task.

Canonical tube generator/source:

`/Users/jaspercurry/Code/CAD - Enclosure/experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py`

A current tube STEP from the closure’s authoritative ancestor build is:

`/Users/jaspercurry/Code/CAD - Enclosure/build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/sand_cube_190x210_single_oval_port_internal_tube.step`

The corresponding full-system assembly/cutaway context is in:

`/Users/jaspercurry/Code/CAD - Enclosure/build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_conformal_full_system/`

## Key implementation files

- Variant A generator:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/generate_sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle.py`
- Standalone validator:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/validate_simple_tongue_groove_baffle.py`
- Diagnostics:
  `/Users/jaspercurry/Code/CAD - Enclosure/build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/validation_diagnostics.json`
- Restore/compare the sculpted seam using the authoritative lightweight
  coherent closure and its `nested_seam_closure_concepts` ancestor, including
  the nested split, corner closure, and outside-gasket closure functions.
- `releases/enclosure_v1/*` is frozen/read-only and its baffle is superseded.

## Workflow and feedback cadence

Run all native CAD through the coordinator from the main repository:

`.venv/bin/python -m cad_runner run --repo . -- /absolute/script.py`

The full cascade currently fails at a pre-existing upstream viewer/cutaway
step. Use the standalone validator for focused work. Keep the feedback loop
tight: one feature at a time, minimal diagnostic/probe, and only the specific
viewer or seam section the user needs. Do not launch the full cascade, generate
every export, or perform expensive rendering after each small change. The user
can inspect the web viewer quickly; use that visual review instead of spending
many minutes trying to prove taste with proxy metrics.

Before cutting geometry, do these three things:

1. Inspect the exact known-good baffle STEP above and show/describe the flat
   bottom face that must survive.
2. Trace the current bucket’s fill-hole obstruction to its source operation,
   using direct spatial probes rather than guesses.
3. Propose a small, auditable plan to make the bucket complement the approved
   baffle bottom while preserving the L/R/T seam, external shell, gasket face,
   fill blisters, and fill passages.

Confirm that plan with the user before editing. After each approved feature,
perform only enough focused validation to be confident, update the relevant
viewer, and say that you are ready for the next piece of feedback.
