# Fable independent analysis — Rev. C (preserved source report)

> **Provenance and status:** This report was generated independently with
> Fable and supplied by Jasper Curry. It is preserved substantially verbatim as
> an external analysis. It is an important input to the project, not the
> canonical design authority. Numerical claims become canonical only after they
> are reproduced by the repository models and reconciled with measurement.
>
> The four scripts named near the end of the supplied report were not included
> with the source text. This repository is independently implementing auditable
> versions of those models and will not assume their unpublished results.

# Port-Mode Slit Absorber — Independent Analysis & Design Rules (Rev. C)

Independent third opinion, with my own numerical models (full thermoviscous slit impedance validated against the Poiseuille and 6/5-mass-factor limits, plus a 1D transmission-line model of the actual 513.6 mm port with the branch inserted) and two verification research passes (end-correction literature incl. the open-access Aulitto TU/e thesis and the Hildebrandt PDF read directly; micro-tooling market survey).

---

## 1. The verdict, and the one thing both previous documents missed

**Build it as drawn. But the reason it will work is not the reason either document gave.**

Both Rev. A and Rev. B modeled the slit as a nearly-lossless mass (the "Q = 3.62 boundary-layer trend") and then argued about how precisely you must tune it. When you solve the **full thermoviscous channel impedance** for a 0.40 mm × 5 mm-deep passage at w/δᵥ = 3.35, two things change:

1. **The oscillating air in the channel is ~19% heavier than bulk air** (Re(ρ_eff)/ρ = 1.193 at 335 Hz — a standard result of the parallel-plate Crandall/Maa solution, which neither document applied to the mass term). The as-drawn part therefore tunes near **292–309 Hz**, not 334.7 Hz, before any end-correction argument even starts.
2. **The channel resistance is roughly twice the duct's characteristic impedance** (R_branch ≈ 6.7×10⁵ Pa·s/m³ vs Z₀ = ρc/S_duct = 3.3×10⁵). Intrinsic branch Q ≈ **2.0–2.2**, not 3.6.

That second point flips the whole engineering posture. At R/Z₀ ≈ 2 the absorber is a **heavily damped side-branch damper**, not a sharp notch filter. Its own bandwidth is ~165 Hz. My duct simulation (branch at the antinode, mode at ~331 Hz) shows:

| Branch condition | Worst residual peak vs bare mode |
|---|---|
| Perfectly tuned, as-drawn R | −25.6 dB |
| Detuned **−10%** | −25.8 dB |
| Detuned +10% | −22.3 dB |
| **Built exactly as drawn, zero tuning** (f₀ lands 292–309 Hz vs mode 331) | **−25 to −27 dB** |
| Slit width anywhere 0.35–0.50 mm (V untouched) | −23.4 to −25.9 dB |
| Edges fully rounded vs ideally sharp | −25.8 vs −25.9 dB (no difference) |
| Placed at the tower (x = 400 mm) instead of the antinode | −23.1 dB |

Re-run with 4× wall losses (bare mode Q ≈ 27, more like a real bent port): everything compresses to −14…−17 dB but the *flatness* is identical — as-built no-tuning is still within ~1 dB of perfectly tuned, and width 0.35–0.50 mm still all works. (Absolute dB values are comparative — my 1D model straightens the bends and ignores 3D effects — but the flatness conclusions depend only on R/Z₀ and the branch bandwidth, which are robust.)

**Consequences, stated bluntly:**

- The **irreversible-tuning anxiety is over-engineered**. Rev. B's displacement-plug system, Rev. A's "measure-then-lengthen" ritual, the ±0.03 mm feeler-gauge metrology, the sharp-edge "build requirement" — all of these solve a precision problem this design does not have. Deep channel (t/w = 12.5) + low porosity put you on a **flat plateau** roughly ±12% wide in frequency and ±0.07 mm wide in slit width.
- Rev. B's "print the bucket at 62 cm³ and plug down" points the **wrong direction anyway**: viscous mass loading plus the larger slit end correction mean the as-drawn part lands *low*. If you tune at all, you'll be *removing* volume (raising f₀), so the drawn 53.3 cm³ is already the "oversized" end of the range. My solve for exact tuning to 335 Hz gives V ≈ **40–46 cm³** depending on the end-correction scenario.
- Rev. B's sharp-edge obsession is misplaced *for this geometry*: the resistive end correction (Aulitto fit: 0.425·w ≈ 0.17 mm per side) is ~7% of the 5 mm channel's distributed resistance. Edge condition matters enormously for thin plates (t ≈ w); it is nearly irrelevant at t = 12.5w. Don't butcher the edges, but don't build a religion around them.
- Rev. B's Q-correction ("higher Q = deeper notch, so Q 3.6 is fine") is right about notch depth and wrong about what you should optimize. The correct objective is **worst residual peak**, and it's maximized at R/Z₀ ≈ 1.5–3 (my sweep: −25.6 dB at R/Z₀ = 2–3, degrading to −13.8 dB at R/Z₀ = 0.3 because the mode splits into two lightly-damped shoulders, and to −20 dB at R/Z₀ = 6 because the branch stops accepting flow). **The drawn design happens to sit at the optimum.** That is the single luckiest — or best — feature of this design.

---

## 2. The design rules you asked for

These are the formulas to size any future variant, with validity limits.

**Rule 1 — Resistance target (the master rule).**
Size the slits so that at resonance

> **R_branch / Z₀ ≈ 1.5–3**, where Z₀ = ρc/S_duct (= 3.29×10⁵ Pa·s/m³ for your 40 mm bore)

R_branch = Re[jωρ_eff·t/S_total]·(1 + 2δ_res/t), with the full parallel-plate solution
ρ_eff(ω) = ρ / [1 − tanh(β)/β], β = (w/2)√(jω/ν), ν = μ/ρ ≈ 1.50×10⁻⁵ m²/s.
Validity: slit aspect ≥ ~6:1 (yours is 18:1), kw ≪ 1.
Practical corollary: for a channel ~10 slit-widths deep, R/Z₀ lands in this window when **w/δᵥ ≈ 2.5–4** and total open area is ~0.5–1.5% of the bore. δᵥ = √(2ν/ω) = 0.120 mm at 335 Hz. Your 0.40 mm at w/δᵥ = 3.35 is centered in the window.

**Rule 2 — Tuning.**
f₀ = (c/2π)·√(S_total / (V·L_eff)), with
> **L_eff = t·Re(ρ_eff)/ρ + 2δ_in**

The viscous mass factor Re(ρ_eff)/ρ: 1.20 (w/δᵥ→0), **1.19 at w/δᵥ=3.3**, 1.09 at w/δᵥ=6, →1 for w/δᵥ→∞. Do not omit it — it alone is a −5% frequency shift here.
δ_in per side for an isolated low-porosity slit (Aulitto thesis, TU/e 2023, p.19, low-Sh forms): δ_in/w ≈ (1 − ln 4Φ)/π to −2.17 + 2.18·Φ^−0.13, giving **δ_in ≈ 0.55–0.74 mm per side** at your effective porosity — i.e. total ≈ 1.1–1.5 mm, roughly double the provisional 0.651 mm. (The classical periodic-array log formula explodes at Φ = 0.9% and is inapplicable — the divergence is an artifact of infinite tiling.) Note Aulitto's fits are technically below your shear number, so treat δ_in as a **0.33–0.75 mm/side bracket** to be closed by measurement.
Corollary: as-drawn f₀ ≈ 292–309 Hz. To sit at 335 Hz exactly: **V ≈ 40–46 cm³**. But per Rule 4 you likely won't need to move it.

**Rule 3 — Depth.**
Keep **t/w ≥ 10**. Deep channels put the loss in the distributed viscous term, which (a) achieves Rule 1 without meshes or wool, (b) makes edge radius, taper, and roughness second-order, (c) makes nonlinear detuning small (only the end correction, ~11% of L_eff, is amplitude-sensitive → ~+3% max shift — Rev. B got this right). Your 5.0 mm on 0.4 mm is t/w = 12.5. Good. Don't thin it.

**Rule 4 — Tolerance budget (what actually matters, in order).**
1. **Nothing at first order.** Within w = 0.35–0.50 mm, f₀-error ±12%, V ±20%, placement 0.25L–0.75L, edge condition anything reasonable → all within ~3 dB of optimum. Aim for w = 0.40 ± 0.05 mm and move on.
2. What *can* hurt: w < 0.30 mm across a whole slit (R/Z₀ > 4.5, −20 dB → costs 6 dB) — fused pilots are the main risk, so the post-finishing pass is about **opening fused slots to ≥0.35 mm**, not about hitting 0.400 sharp.
3. **Chamber leaks** — the one un-modeled failure mode with real teeth. A leak is a parallel low-resistance branch that both detunes and shorts the cavity. Gasket integrity beats slit metrology. Leak-test the sealed bucket (block slits with tape, apply gentle pressure, listen/soap-film) before any acoustic test.
4. Temperature: −0.6 Hz/°C, tracks the duct mode. Ignore.

**Rule 5 — Placement.**
Coupling ∝ sin²(πx/L), but with R/Z₀ ≈ 2 the penalty is compressed: tower (0.41 coupling) costs only 2.5 dB in the smooth model, ~4 dB in the lossy model. **Put it wherever it's easiest to build and seal — the tower is fine.** Fighting the 67° bend for the last 2–4 dB is bad ROI on a first article. (Rev. B's two-half-units idea: real but small — skip for v1.)

**Rule 6 — Volume as the trim knob (kept from Rev. B, direction corrected).**
f ∝ 1/√V. Print the bucket at the drawn 53.3 cm³ and design the lid for **adding** displacement plugs (up to ~15 cm³ → +15% f₀). This is the reversible trim if measurement ever shows you need it; expect not to use it.

---

## 3. Nonlinearity — the finding nobody had

Both documents argued about nonlinear behavior *at 335 Hz*. The louder mechanism is **at 39 Hz**: at reflex tuning the port carries large volume velocity, and the pressure standing across the branch at mid-port is ~ωρ·u_port·x. My estimate:

| Port velocity (39 Hz) | Pressure at slits | Slit velocity | Strouhal ωw/u |
|---|---|---|---|
| 5 m/s (loud) | ~380 Pa (143 dB) | 3.2 m/s | 0.031 |
| 10 m/s (very loud) | ~760 Pa (149 dB) | 6.3 m/s | 0.016 |
| 20 m/s (limit) | ~1520 Pa (155 dB) | 12.6 m/s | 0.008 |

St ≪ 1 → the slits are **fully jetting on loud bass**, even though the absorber is far below its resonance. Consequences: the branch flow is <1% of port flow, so the **39.12 Hz alignment is untouched**; the jets dissipate a little energy (harmless); but four 0.4 mm slits pulsing at 3–13 m/s may generate **audible broadband hiss/buzz on bass transients** (Re ≈ 90–350, so likely faint, but unverified). Add to the test plan: loud 35–45 Hz sine, ear/mic at the module. If it hisses, the fix is more slit perimeter at lower velocity (e.g. 6 slits) or slightly wider slits — both stay inside the Rule-1 window.

At 335 Hz the branch self-limits: velocity rises → resistance rises (Aulitto 2022, Eq. 6, ΔR ≈ (4/3π)ρu/C_v², C_v = 0.82) → moves from R/Z₀ = 2 toward 4 → costs ~2 dB. Detuning ~+3% max. Non-issue.

---

## 4. Literature cross-check (what the subagents verified)

- **Hildebrandt thesis read directly** (HAW PDF): 123 cm³ common chamber (p. 29), four 50×0.2 mm slits = 40 mm² (p. 30), simulated 653 Hz / measured 675 Hz (Fig. 3.14, 5.3), target Q = 1, as-built Q = 3.25 (p. 29), ≈19 dB reduction bare / +7 dB with foam (Figs. 5.3–5.4). No wool in the built chambers — geometric resistance only, common cavity. His numbers check out and his w/δᵥ = 2.4, t/w = 10 puts him in the **same damping-dominated regime** — independent confirmation that this class of device delivers ~19 dB in real hardware despite a 3.4% tuning miss. That miss costing him nothing is exactly the flat-plateau behavior my sims predict.
- **Aulitto TU/e thesis (open access)**: end-correction forms quoted in Rule 2; resistive correction δ_res/w = 0.425, porosity-independent, edge-dominated; inertial correction porosity-dependent, log-divergent for isolated slits. Her high-shear-number corrections (Eqs. 2.27–2.29, the regime you're actually in) were not extracted — read pp. 27–29 if you ever need the last few percent; you don't for v1.
- **Ingard 1953** (via Selamet & Radavich): cavity-side correction δ ≈ 0.85(d_c/2)(1 + 1.25 d_c/d_v) — circular geometry, direction only.
- Caveats: Aulitto JASA 2021 itself is paywalled (thesis used instead); Maa 2000 primary not directly read; Ingard & Ising 1967 not retrievable. Nothing critical rests on these.

---

## 5. Manufacturing: the tooling answer

**Do not buy 0.4 mm end mills.** The subagent's market survey: no commercial 0.4 mm carbide end mill has anywhere near 5 mm of flute (typical usable flute at that diameter is 0.5–1.5×D; 5 mm depth is a 12.5:1 ratio that doesn't exist as a catalog item). Cheap "0.4 mm" AliExpress/uxcell PCB bits (~$10/10 pc) are taper-ground isolation-routing tips with <0.5 mm of cut. And without a rigid CNC, drill-press/Dremel runout (0.05–0.15 mm) is 12–40% of the tool diameter — guaranteed breakage. This option is closed; stop considering it.

**What to use instead, ranked:**
1. **Jeweler's/piercing saw, #5 blade — kerf ≈ 0.40 mm** (blade size charts: #0 = 0.28, #5 = 0.40, #9 = 0.55 mm). Saws a straight, sharp-edged 0.4 mm kerf through 5 mm of plastic; reaches through a printed pilot slot; a saw frame + blade assortment is ~$20–40. This is your primary sizing tool and it is almost comically well-matched to the job.
2. **Diamond lapping film (~$15–40 assortment) glued to a 0.30–0.35 mm feeler blade** — final calibration/cleanup after sawing, sneaking up by film-thickness increments.
3. Cutting broaches (0.4→0.7 mm taper, ~$80 set) — touch-up only; the taper widens the entrance if pushed deep. Needle files are too wide (≥0.5 mm) to fit the slot.

**Feeler gauges (yours, incoming):** blades are ~12.7 mm wide vs your 7.2 mm slot — they **cannot pass through**; you'll gauge with a tip corner, which checks entrance width only and will miss an hourglass profile deeper in. Two fixes: grind one 0.40 blade to ~5 mm width as a through-going GO gauge, and keep an unmodified 0.45 as NO-GO at the entrance. Check a cheap set's 0.40 blade against a micrometer first (quality blades hold ±0.01–0.02 mm; unbranded can be several× worse). Given Rule 4, ±0.05 mm acceptance is fine — the gauges are go/no-go references, not the precision bottleneck the previous documents made them.

**Printing:** 0.30 mm pilots below the 0.4 mm line width will partly fuse — expected; they're saw guides, not slots. The curved 4-orientation coupon is still worth one print: what you're learning is *which orientations fuse worst*, not chasing ±0.03 mm. FDM negative features print 0.1–0.3 mm undersize (community consensus; maker projects like `juliendorra/3D-printable-sound-absorbers` default to 0.8 mm perforations precisely because sub-0.5 mm FDM slots are unreliable) — the pilot-then-finish plan is right. A 0.2 mm nozzle (~$21, exists for X2D) would shrink finishing stock but not eliminate finishing; optional.

---

## 6. First-article spec and test plan

**Build (one part, this week):**
- Slits: 4 × nominal 0.40 mm × 7.17 mm × 5.0 mm deep — **as drawn**. Acceptance: every slit passes 0.35 GO through full depth, refuses 0.45 at entrance. Edges: neat, not fetishized.
- Cavity: 53.3 cm³ **as drawn**; lid designed to accept stick-on displacement plugs (provision for ~15 cm³ total).
- Location: **tower** (or as close to the bend as prints cleanly — either is fine per Rule 5).
- Gasket sealed; **leak-test before acoustic test** (tape over slits, pressurize gently, soap film).

**Measure (in order, same mic position, fixed drive):**
1. Bare port (no module): find the real mode — expect ~325–340 Hz. This calibrates everything; it does *not* gate the build.
2. Port + module with slits taped over: isolates the module body's effect on the pipe (geometry control).
3. Port + module active: expect the ~330 Hz peak to drop 10–25 dB depending on the port's real bare Q. Sweep + decay spectrogram.
4. If (and only if) the residual peak sits >5 dB above the plateau my sims predict, check for leaks first, then trim: measured f₀ too low → add plugs (each cm³ ≈ +1%·f₀/2 ≈ +3 Hz); too high (unlikely) → you have 53.3−40 ≈ 13 cm³ of headroom already built in… meaning you'd remove plugs you didn't install — in that corner case, extend one pair of slits with the saw (+length raises f₀, √-slowly, ~+10 Hz per +1 mm across all four).
5. Level series: 80/90/100 dB sweeps (linearity at 335 Hz) + loud 39 Hz sine (listen for slit hiss; verify reflex alignment unchanged via impedance or near-field port output at 20–60 Hz).

**What would change my verdict:** measured bare mode outside 290–380 Hz (re-derive); residual peak stuck >8 dB above prediction after leak-check (then the 3D bend/branch interaction is doing something my 1D model can't see — that's when a second unit at the other sin²-favorable location earns its keep); audible slit noise at bass levels (widen/add slits per §3).

---

## 7. Scorecard vs the two prior documents

| Question | Rev. A | Rev. B | This analysis |
|---|---|---|---|
| As-drawn tuning | 334.7 Hz nominal, worry ±7% | same, tune-by-volume upward | **292–309 Hz** (viscous mass + slit end correction, both omitted before) — and it doesn't matter |
| Intrinsic Q | 3.62 as bound | 3.62 as trend | **≈ 2.0–2.2** from full solution |
| R vs Z₀ | not computed | not computed | **≈ 2× — accidentally optimal** |
| Tuning precision needed | high (irreversible dread) | medium (plug system) | **low: ±10% ≈ 2 dB** |
| Sharp edges | caution | build requirement | **second-order at t/w = 12.5** |
| Placement | antinode critical | antinode vs 2 halves | **tower fine (−2…−4 dB)** |
| Cavity 53 cm³ | "too small" | "matched, keep" | keep; exact-tune value is 40–46 cm³, plateau makes it moot |
| Nonlinearity | √2 walk-off (wrong) | +3% at 335 Hz (right) | +3% at 335 Hz **plus the real one: 39 Hz slit jetting / possible hiss** |
| 0.4 mm end mills | — | — | **don't exist at 5 mm flute; jeweler's saw #5 = 0.40 mm kerf is the tool** |

*Models and scripts: `model.py`, `duct.py`, `verify.py`, `robust.py` (validated against Poiseuille and low-frequency mass limits; duct model is 1D lossy TMM with box compliance and unflanged radiation; absolute dB comparative, sensitivity conclusions robust).*
