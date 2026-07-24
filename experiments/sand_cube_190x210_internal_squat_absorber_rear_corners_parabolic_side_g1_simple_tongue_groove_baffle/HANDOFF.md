# Two-Variant Enclosure Closure — Handoff & Course Correction

> **2026-07-24 supersession note:** The Variant R seam and print-edge course
> correction described below is now resolved in production source. The exact
> sculpted left/right/top edge geometry is retained, the continuous flat-bottom
> donor is used without a whole-part splice or lower material transfer, and
> only the baffle sub-sole is discarded at `Z=-91.495 mm`. The exact twelve
> internal bucket-only micro-omissions are the authorized no-splice delta.
> Top-hinge and lower-fastener work remains deferred, so the retention sections
> below are historical context and future-design input rather than claims about
> the current accepted geometry. See
> `workbench/designs/variant_r_no_splice_production/` and this experiment's
> `README.md` for the current measured status.

Status: **Variant A geometry builds green but is physically wrong and must be re-done with the corrected architecture below.** Read this whole file before touching code. A ready-to-paste brief for a fresh agent is in `NEXT_AGENT_PROMPT.md` (same dir).

---

## 1. The vision — two variants, identical visible exterior, different serviceable face

Both variants keep the **same sweeping exterior**: parabolic-side G1 front fairing (edge-midpoint pullback 8.0 mm / corner pullback 15.0 mm), superellipse sides, 4 mm rear roll, `edge_fillet_r = 8.0`; body ~190(w) × 210(d) × 190(h) mm.

- **Variant A — "front baffle hatch":** the front baffle is a **removable** part; you service the driver/interior by taking the baffle off. Baffle prints **vertically** (flat bottom base + brim). Retention = a continuous **top tongue-and-groove hinge** (pivot the baffle in) + **2 bottom captive-nut screws**. *(This is what was attempted — see §3-4.)*
- **Variant B — "bottom hatch / port":** the front baffle is **integral** with the enclosure (monolithic front); you service via a removable **bottom hatch** (radiused sheet + inner lip + ~8 screws into captive nuts). Prints **bottom-down**. **NOT started.** It has two hard gating problems flagged earlier: (a) the flat ~176 mm interior ceiling can't bridge bottom-down without heavy internal support; (b) the folded port/PR lower duct sits on and bolts to the solid −88 floor, so opening the bottom is a base-level re-anchoring job, not a leaf edit.

---

## 2. THE MISUNDERSTANDING THAT SANK VARIANT A (read first)

The user said **"keep the seam between the baffle and the enclosure the same."** That means the **sculpted nested seam geometry** — the elegant interface + corner sealing the user hand-designed — on **left / right / top**. It does **NOT** mean only the visible outer skin.

What went wrong: chasing "radical simplification," Variant A **deleted the nested seam + the corner-closure panels + the outside-gasket closure + the 45° transition** and replaced them with a plain lip. Enormous effort then went into *proving the outer skin was byte-identical* — i.e. **guarding the wrong invariant** while destroying the interface the user actually cared about. The corner sealing went with it.

### Corrected architecture — a HYBRID SEAM
- **Left / right / top:** restore the **original sculpted seam** exactly (this also restores corner sealing).
- **Bottom only:** the **new flat seam** (needed so the baffle prints upright). The bottom exterior may change **only below the bottom corner**, where it isn't really visible — the user has approved that.

### Corrected APPROACH
Flip from **"delete everything and rebuild minimal"** to **"inherit the original design and surgically change ONLY the bottom (+ the top hinge + the 2 bottom screws)."** Do not delete the seam. This structurally prevents the whole class of error that happened.

---

## 3. What is RIGHT and must be kept
- The **bottom flat faces** on **both** the baffle and the enclosure. The baffle now has a clean face to print vertically from, and the enclosure matches. Keep these.
- The **gasket spec**: purchased weatherstrip 5 mm wide × 2 mm tall, compressed to a **1.0 mm gap**, driven by ONE tunable constant (`GASKET_CLOSED_GAP_MM` at generator line ~122; also patch `source.SHOULDER_Y` — computed at module import).
- The **top tongue-and-groove hinge concept** (continuous bead-in-groove, pivot-in) — the hinge itself validated: −6° pivot, seal-preserving relief (0.0 swept interference at every angle), gasket support stays 1.0. Keep the concept; re-integrate it on top of the restored sculpted seam.

## 4. The issues the user found (annotated viewer screenshots)
1. **Sculpted seam destroyed on L/R/T** — replaced with a plain lip. RESTORE it.
2. **"Not sealed – big gap behind gasket face"** at the corners — the deleted corner closures were *sealing* the corners. Restoring the sculpted seam on L/R/T re-seals them; the **bottom** corners (flat seam) need their own small closure.
3. **"open hole!" — bottom screw bores break THROUGH the enclosure edge.** Unacceptable.
4. **"screw hole hitting gasket face"** — the bores clip the gasket sealing land.
5. **No clear insertion shot** — the pocket doesn't extend to give a straight-down path to actually get a reasonable-length screw in.
6. **"connect the plastic"** — the flat bottom seal is discontinuous (islands between the fastener pockets); must be one connected run.
7. **"weird extra material blocking fill hole"** — clear the obstruction *without* removing the fill blister (the blister is wanted).
8. The bottom now has **less material** (the baffle took some for its flat print face), so the bottom fastener is a tight squeeze.

## 5. The bottom-fastener plan (the user's stated order)
1. **Place the 2 bottom holes so they WORK first:** a clear straight-down insertion shot, clear of the gasket face, not breaking through the edge. The screws are ~45–48° from vertical into **baffle-face-loaded captive M4 hex nuts** (NOT heat-set — pull-out risk). Bucket blister ~12.5 mm, nut pocket 7.4 × 3.6, head recess 9.8 × 3.6, clearance bore 4.5.
2. To lift the entry off the edge, **tilt the screws a bit more perpendicular** to the bottom face — but **bounded** so the bore doesn't climb into the **nut slot**. This "raise the hole vs. miss the nut slot" squeeze is the crux; solve it empirically.
3. **Show the user the placement**, then design the **gasket-face reroute** around the holes: **arc-up → flat → arc-down**, adding matching faces on both the enclosure and the baffle.
4. **Hardest region:** the two **bottom corners**, where the sculpted seam meets the flat bottom, the screw holes, the gasket reroute, and the corner sealing all collide.

## 6. Validation invariants — existing + the ones that were MISSING
Existing (kept green but insufficient): single valid solid; STEP round-trip 1↔1 valid; gasket support ratio ≥ 0.985; exterior identity (fairing area + bbox + skin fingerprint); fill-passage clearance.

**NEW invariants that must be added — their absence let the physical failures pass as "green":**
- **Screw insertion clearance:** a straight cylinder swept along the screw axis from outside must be unobstructed (you can actually insert the screw).
- **No exterior edge breakthrough:** the bore must not open through the outer edge, except within the permitted bottom band (below the bottom corner).
- **Gasket-face clearance:** the bore must not clip the gasket sealing face.
- **Seam identity (L/R/T):** the sculpted seam must match the original — a check on the *seam*, not just the outer skin. (Clip/compare the seam region, or compare seam cross-sections, against the original.)
- **Corner seal:** no gap behind the gasket at the corners (re-instate the `_audit_bucket_front_closure` outside-gasket check that was dropped — it is what would have caught the open corners).
- **Bottom seal continuity:** the bottom seal must be one connected solid.

## 7. Build / environment notes
- All CAD through the coordinator, from the **main repo** (`/Users/jaspercurry/Code/CAD - Enclosure`): `.venv/bin/python -m cad_runner run --repo . -- /abs/script.py`. Concurrency is now allowed within RAM headroom.
- The **full cascade fails at an upstream viewer step** (`simplified._build_robust_viewer_cutaway` → "cutaway did not produce valid solids" on the *inherited* assembly) — pre-existing environment/geometry drift, NOT this work. **Validate via the standalone harness** (pattern: `generate_bucket_front_transition_candidate.py`; here: `validate_simple_tongue_groove_baffle.py`).
- `releases/enclosure_v1/*` is **frozen/read-only**. The V1 baffle is **superseded** (throwaway prototype) — drop the frozen-V1 interference check for new work.
- The Variant A generator inherits a deep chain of **untracked** ancestor generators that live only in the main-repo working tree (the closure generator, the nested-seam / corner-closure / outside-gasket sources, etc.). Work in that tree.

## 8. Key files
- Variant A generator: `experiments/…_simple_tongue_groove_baffle/generate_…_simple_tongue_groove_baffle.py`
- Validator (standalone harness): `…/validate_simple_tongue_groove_baffle.py`
- Build outputs: `build/…_simple_tongue_groove_baffle/{simple_tongue_groove_bucket.step, simple_tongue_groove_baffle.step, validation_diagnostics.json}`
- **Restore the sculpted seam from:** the authoritative closure generator + its `nested_seam_closure_concepts` ancestor, and the `_baffle_corner_closure_panels` / `_outside_gasket_face_closure` / nested-split functions the Variant A generator deleted.

## 9. Process lessons (so the next attempt doesn't repeat them)
1. **Guarded the wrong invariant.** When the user says "keep X the same," pin down *exactly what X is* (here: the seam geometry, not the outer skin) and validate against *that*. Show the specific feature (a **section through the seam**) early — don't infer preservation from a proxy metric.
2. **Over-deleted "cruft."** The sculpted seam + corner closures were **functional**, not cruft. Default to **surgical** change: inherit what works, change only what the goal requires (here, only the bottom, for printing).
3. **Green numbers ≠ good design.** Every invariant was green while the part was physically broken (open corners, screw holes through the edge/gasket, no insertion shot). Invariants must encode **physical assemblability**, not just internal booleans.
4. **Show the user the thing they care about, early and cheaply.** A single seam section shown early would have caught the whole miss on day one instead of after the full build.
