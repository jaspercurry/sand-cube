# Fresh-context prompt — Variant A rework

Paste the block below into a new session. It is self-contained but points to the full record in `HANDOFF.md` (same directory).

---

We are working in `/Users/jaspercurry/Code/CAD - Enclosure` — a build123d parametric speaker enclosure. First read `AGENTS.md`, then read `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/HANDOFF.md` in full — it is the authoritative record of a previous attempt that built green but was physically wrong, and it lists the exact issues, the corrected plan, and the mistakes to avoid. Do not skip it.

**The vision — two variants, identical visible exterior, different serviceable face:**
- **Variant A (this task): "front baffle hatch"** — a removable front baffle that prints vertically (flat bottom base + brim); retained by a continuous top tongue-and-groove hinge (pivot in) + 2 bottom captive-nut screws.
- **Variant B (later): "bottom hatch/port"** — integral front, removable bottom hatch, prints bottom-down. Not started; has two gating problems (roof bridging; port/floor re-anchoring) documented in HANDOFF.md.

**The single most important thing to get right:** "keep the seam between baffle and enclosure the same" means the **sculpted nested seam geometry** (the elegant interface + corner sealing the user designed) on the **left, right, and top** — NOT just the visible outer skin. The previous attempt deleted that seam in the name of "simplification" and guarded only the outer skin. Do not repeat this.

**Corrected architecture — a HYBRID SEAM:**
- Left / right / top: **restore the original sculpted seam exactly** (this also re-seals the corners).
- Bottom only: the new **flat seam** (so the baffle prints upright); its exterior may change **only below the bottom corner** (not really visible — user-approved).
- **Approach: inherit the original design and surgically change ONLY the bottom (+ the top hinge + the 2 bottom screws). Do NOT delete the seam and rebuild.**

**Keep (already correct):** the bottom flat faces on both parts; the 1.0 mm gasket compression (one tunable constant); the top tongue-and-groove hinge concept (validated at −6° pivot, seal-preserving relief, gasket support 1.0).

**Fix these (all found by the user — see HANDOFF §4-5):**
1. Restore the sculpted seam + corner sealing on L/R/T.
2. Bottom screw bores currently **break through the enclosure edge** and **clip the gasket face**, and there's **no clear insertion shot**. First **place the 2 holes so they physically work** — straight-down insertion clearance, clear of the gasket, not through the edge — tilting the screws a bit more perpendicular to raise the entry (bounded so the bore misses the nut slot). **Show the user the placement before rerouting anything.**
3. Then reroute the bottom gasket face around the holes (arc-up → flat → arc-down), adding matching faces to both parts.
4. Make the bottom seal one continuous piece ("connect the plastic").
5. Clear the material obstructing the fill holes without removing the fill blister.

**Add these validation invariants (their absence let the failures pass as "green"):** screw insertion clearance; no exterior edge breakthrough (except the permitted bottom band); gasket-face clearance; **seam identity on L/R/T** (check the seam, not just the outer skin); corner seal (re-instate the outside-gasket closure audit that was dropped); bottom seal continuity.

**Build/validate:** all CAD via `.venv/bin/python -m cad_runner run --repo . -- /abs/script.py` from the main repo. The full cascade fails at an upstream viewer step (pre-existing env drift) — validate via the standalone harness (`validate_simple_tongue_groove_baffle.py`). `releases/enclosure_v1/*` is frozen/read-only; the V1 baffle is superseded.

**Work style the user expects:** surgical changes (inherit what works, change only what's needed); when told a past approach was bad, delete it and don't reference it; show the user the *specific* geometry they care about early and cheaply (a seam section), don't infer preservation from a proxy metric; green numbers ≠ good design — invariants must encode physical assemblability. Implement one feature at a time, rebuild, validate, and check with the user before committing to the next.

Start by proposing your plan for restoring the sculpted seam on three sides while keeping the flat bottom, and confirm it with the user before cutting geometry.
