# Feedback log

## 2026-07-22 — intake

- User supplied the enclosure/baffle recovery brief and required a diagnosis
  and plan checkpoint before geometry edits.
- The approved baffle STEP was inspected in the interactive viewer. Its lower
  edge is planar across the full width and both lower corners terminate on the
  same print plane; the sculpted L/R/top perimeter and top hinge bead remain
  visible.
- The current bucket was inspected separately. It is not yet treated as a
  valid mate, and a deep curved/triangular upper fill-area structure is visible.
- No geometry was edited and no generator was run. A fresh provenance probe is
  required because the available validation report is older than the current
  STEP files.

## 2026-07-22 — provenance checkpoint

- User directed that routine CAD inspection use Build123d MCP `render_view()`,
  with one isometric and one question-specific section; promoted geometry must
  use direct headless STEP PNGs. Browser automation is fallback-only. The
  iteration contract was updated accordingly.
- MCP loaded the current bucket STEP as one solid: volume
  1,092,165.7564 mm³, 282 faces, bounds 190.0021 × 202.0 × 190.0021 mm.
- The focused upper-left fill-axis section is 1,081.2641 mm³ with 49 faces and
  bounds X −88.5…−83.5, Y −81…−47, Z 70…94.9182 mm.
- Agent visual review of the MCP section shows separate structures: a 3 mm
  front plate, a broad curved/deep ramp below it, and a smaller tubular fill
  transition. The full isometric HLR view confirms the overall enclosure but
  is visually dense; the section is the decisive view.
- Coordinated provenance job
  `20260722T172836-probe-front-bulkhead-e0ba129bc2` completed in 137.36 s,
  peak RSS 0.87 GiB, with clean process/workspace cleanup and no orphans.
- The canonical service-opening probe (X/Z ±84.75 mm, Y
  −79.0167…−67.2167 mm) contains 0.0 mm³ of bucket material. This rules out an
  inherited fixed-front shell/brace fragment inside the protected opening.
- In the upper-left probe, the canonical face plate has a 1.000000 presence
  ratio, the canonical support wedge 0.99999994, and the wanted fill support
  0.96704151. Across five Y slices from −74.3167 to −67.4167 mm, every occupied
  sample was attributed to face plate, support wedge, or fill support; no
  sample was an unattributed inherited bucket fragment.
- Provenance conclusion: the broad curved/triangular solid is created by
  `_front_bulkhead()` as
  `exact_outer.intersect(wedge_slab).cut(wedge_opening)`, followed by the
  fill-support keepout and fusion to the face plate. The wanted blister is a
  separate `_front_fill_feature()` hollow support. The complaint is therefore
  a design problem in the canonical wedge, not a tessellation artifact and not
  a resurrected legacy closure fragment.
- No production geometry was edited. Awaiting user approval of the proposed
  localized scratch candidate and bottom-complement plan.

## 2026-07-22 — corrected arrow target and Viewer trial

- User clarified the unwanted feature with an annotated section image. The
  target is the thin vertical planar tab in front of each upper fill opening,
  with matching instances at the two lower corners—not the broad/deep support
  wedge previously identified.
- The four-corner repetition identifies the target as the outer corner sector
  of the 3 mm planar bulkhead face ring produced by `_front_bulkhead()`:
  `exact_outer.intersect(slab).cut(inner_opening)`. The upper two sectors are
  pierced by fill passages; the same perimeter construction leaves the lower
  two sectors intact.
- Any design fix must delete or redefine the face-ring construction so those
  sectors are never generated. A downstream cutter or additional cleanup
  Boolean is explicitly rejected.
- User authorized a narrowly scoped `earthtojake/text-to-cad` Viewer trial
  against the exact existing STEP, with no design changes and no browser
  automation. Existing direct renders must be retained.

## 2026-07-22 — visual-channel correction

- The user rejected routine agent operation of the interactive OCP web viewer
  as unnecessarily indirect and visually expensive.
- This decision supersedes the shortcut in the preserved original brief that
  suggested relying on user web-viewer inspection instead of agent renders.
  The original brief remains unchanged as the verbatim intake record.
- From this checkpoint onward, programmatic geometry queries answer measurable
  questions, the agent inspects direct focused renders, and the interactive OCP
  viewer remains the user's rotation and exploration channel. Browser-driven
  CAD inspection is a documented fallback only.

## 2026-07-22 — pinned Text-to-CAD Viewer trial

- The exact reviewed artifact is
  `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_bucket.step`,
  SHA-256 `8cc4f826b530208d2f8b1db0cc69a35a31f7fb2093836e2bb8359b2dbfc8faa5`.
  It is newer than the current leaf generator and its directly imported
  lightweight-closure parent; no experiment generator is newer than the STEP.
- The existing agent renders were retained unchanged. Both
  `mcp_bucket_iso.png` and `mcp_upper_fill_section.png` were made by loading
  that exact STEP into the persistent Build123d MCP session and calling
  `render_view()`; neither was regenerated for this trial.
- No preinstalled `cad-viewer` command or Text-to-CAD Viewer skill was found.
  A disposable checkout of release `0.3.9`, exact commit
  `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`, was created at
  `build/tool-evaluations/text-to-cad-0.3.9`. Only its checkout-local Node
  dependencies were installed; the project `.venv`, `pyproject.toml`, locks,
  and dependency pins were not changed.
- One reusable Viewer is running on `127.0.0.1:4178`, rooted at the exact STEP
  directory. Browser automation was not used. The existing OCP viewer also
  remains live as a separate human-inspection path.
- The initial Viewer diagnosis was `missing_glb`: the STEP itself was current,
  but it had no hidden topology sidecar, so face/edge references were not yet
  available. The smallest isolated conversion read the existing STEP and
  wrote only `.simple_tongue_groove_bucket.step.glb` beside it.
- Sidecar generation ran through coordinated job
  `20260722T182720-viewer-sidecar-current-bucket-61b749ae1c`: worker PID 4198,
  elapsed 3.54 s, peak RSS 0.37 GiB, exit 0, clean workspace/process-group
  cleanup, and no orphaned processes. It did not rebuild or rewrite the STEP.
- The resulting 5,041,896-byte sidecar has SHA-256
  `88bd897f77b2d548e07d3fba552a75cd62b2ad5edcb61883ba7feb42bfa7bfc1`
  and records the exact STEP hash. Code-level loading through the Viewer's own
  runtime succeeded with one mesh part, schema-2 topology, 282 selectable
  faces, 828 selectable edges, 1,112 total references, and the
  `surface-edges` display profile. Copy tokens include `#o1`, `#s1`, `#fN`,
  and `#eN` for this single-part artifact.
- Version 0.3.9 supports orbit/pan/zoom, the single occurrence's visibility,
  face/edge/vertex/part selection and copied references, and X/Y/Z clip planes
  with position, flip, and reset controls. Human interaction itself remains
  for the user to confirm in the interactive channel.
- Any returned `#...` token is transient and local to this exact STEP hash.
  Future feedback must record the artifact path and token together, translate
  it to a semantic Build123d feature, define measurements/invariants before a
  source edit, and never retain the transient index as a source selector.

## 2026-07-22 — artifact-local reference `#f91`

- Artifact: `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_bucket.step`,
  SHA-256 `8cc4f826b530208d2f8b1db0cc69a35a31f7fb2093836e2bb8359b2dbfc8faa5`.
  Reference `#f91` is valid only for this artifact/hash.
- Viewer topology record: planar face, area 23.352861 mm², center
  `(-87.328406, -75.816667, 87.328406)` mm, normal `(0, -1, 0)`, and bounds
  `X=-90…-81.021323`, `Y=-75.816667`, `Z=81.021323…90` mm. This places it on
  the forward face at the upper-left outer corner.
- Its boundary contains the outer `X=-90` and `Z=90` runs, the parabolic inner
  boundary (20 mm radius about `X/Z=-72.1/+72.1`), and the 3 mm/1 mm corner
  rounds about `X/Z=-87/+87`. That topology identifies the exact thin corner
  tab selected by the user.
- Durable semantic mapping: upper-left outer corner sector of the 3 mm planar
  front-bulkhead face ring. It originates in `_front_bulkhead()` where
  `plate_blank = exact_outer.intersect(slab)` is cut by `inner_opening` to form
  `face_plate`; the fill keepout cuts the passage but leaves this sector. The
  completed face plate/support wedge is then fused into the bucket.
- `#f91` will not be used as a Build123d selector. Any source change will
  redefine or delete the face-ring sector construction and will validate all
  four semantic siblings, the fill passages, gasket support, and external
  silhouette before regeneration.

## 2026-07-22 — four-face removal authorization

- User selected `#f91`, `#f97`, `#f16`, and `#f21` on the same current bucket
  STEP and explicitly authorized removing their creating construction, with no
  downstream patch, cutter, mask, or cleanup Boolean.
- The four artifact-local faces are the forward planar upper-left,
  upper-right, lower-left, and lower-right sectors at
  `Y=-75.816667 mm`. They all map to the same durable semantic feature: the
  3 mm planar front-bulkhead face plate.
- Implementation decision: delete the complete planar face-plate construction
  from `_front_bulkhead()` and retain only the existing inner support wedge
  and hollow fill supports. This removes every face associated with the plate,
  not only the four selected topology indices.

## 2026-07-22 — source deletion and functional blocker

- The complete `face_plate` construction and its fusion into the bucket were
  deleted from `_front_bulkhead()`. No replacement solid, downstream cutter,
  masking Boolean, or face-index selector was added. The four Viewer tokens
  remain only provenance for the old STEP and are not used by source code.
- The first normal production build was blocked earlier in the unchanged
  longitudinal-rail cascade. The repository's standalone joint validator was
  then used, after syntax-only updates required by Build123d 0.11.1's
  `intersect()` return type.
- Coordinated production validation job
  `20260722T192248-validate-face-plate-removal-api-fcf8ac475e` reached the
  gasket invariant and rejected the deletion: bucket-side gasket support fell
  to `0.081510` while baffle-side support remained `1.000000`. The required
  minimum remains `0.985`; the gate was not weakened in production source.
- A disposable `/private/tmp` wrapper waived only that gasket threshold and
  redirected all outputs to `build/workbench/` so downstream consequences
  could be measured without overwriting the current STEP. Coordinated job
  `20260722T192833-scratch-export-deleted-face-plate-9e50c6e39f` then rejected
  the candidate because deleting the plate leaves a `6241.675075 mm3` opening
  in the front sand cap. No candidate outputs were published, and the process
  group was reaped cleanly with no orphaned workers.
- The last valid production STEP and both existing Viewer channels were left
  unchanged. Promotion is blocked pending an explicit choice between retaining
  the gasket/sand-seal requirements and accepting an intentionally unsupported,
  open front cavity; no additional geometry will be invented silently.

## 2026-07-22 — Text-to-CAD Snapshot trial

- The user accepted the Text-to-CAD Viewer/reference workflow for human review
  and requested a narrowly scoped Snapshot trial as the agent visual channel.
  Geometry was not rebuilt or changed for this experiment.
- Snapshot read the same current Viewer artifact,
  `build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_bucket.step`,
  using its existing hidden GLB topology sidecar. The STEP and sidecar retained
  SHA-256 values `8cc4f826b530208d2f8b1db0cc69a35a31f7fb2093836e2bb8359b2dbfc8faa5`
  and `88bd897f77b2d548e07d3fba552a75cd62b2ad5edcb61883ba7feb42bfa7bfc1`,
  respectively, with unchanged sizes and modification times after the trial.
  No model rebuild, STEP rewrite, or repeat tessellation occurred.
- The exact pinned Text-to-CAD 0.3.9 checkout required its Snapshot Python
  launcher dependencies. `playwright==1.60.0` and its matching Chromium were
  installed only under `build/tool-evaluations/text-to-cad-0.3.9`; the project
  `.venv`, dependency declarations, pins, and lockfiles were not modified.
- One Snapshot job loaded the existing sidecar once and reused the same runtime
  and source for exactly two 1600×1200 cameras: an orthographic isometric
  overview and a front orthographic view focused on the four repeated planar
  front sectors. No four-view packet was generated.
- The successful coordinated job was
  `20260722T193855-text-to-cad-snapshot-current-step-unsandboxed-eee27b82b6`:
  worker PID 99050, elapsed 4.118 s, peak RSS 872,218,624 bytes (0.81 GiB),
  exit 0, clean process-group cleanup, and no orphaned worker. A preceding
  sandboxed launch was cleanly reaped after macOS denied Chromium's MachPort
  rendezvous; it produced no images and was not retried as a geometry build.
- Snapshot saved only
  `build/workbench/enclosure_baffle_recovery/snapshot_trial/snapshot_iso_20260722T193855Z.png`
  and
  `build/workbench/enclosure_baffle_recovery/snapshot_trial/snapshot_front_plate_orthographic_20260722T193855Z.png`.
  It used a dedicated headless render page, with no browser chrome, interactive
  Viewer operation, manual camera manipulation, or Codex browser automation.
- Agent inspection: the Snapshot isometric is substantially clearer than the
  existing cyan hidden-line render. Opaque shading, restrained black edges,
  and cavity occlusion make the shell, front opening, top opening, seam, and
  internal supports easy to separate. The artifact is one part, so the single
  blue-gray part color is correct; no false assembly-color semantics appear.
- The Snapshot front orthographic correctly shows the overall four-corner
  context, but solid projection collapses depth and leaves the thin planar
  plate, broad support wedge, and hollow fill transition difficult to
  distinguish. The retained `mcp_upper_fill_section.png` is more decisive for
  the current removal question because its localized section separates those
  structures. This Snapshot trial therefore wins for overview readability but
  does not yet clearly replace the existing question-specific section path.
- No geometry mismatch was observed between the exported STEP, Viewer
  representation, and Snapshot images. Fine/tangent lines are less prominent
  in the shaded isometric, and the front view is depth-ambiguous by projection,
  but the visible shell, openings, seam, braces, and repeated front sectors are
  consistent with the current artifact.
- The existing `mcp_bucket_iso.png` and `mcp_upper_fill_section.png` retained
  their earlier modification times and SHA-256 values
  `b9c9602c6e620c2c3ffd2c08fc19f64e097b2b2d62890165721010e19fec5163`
  and `4cc0243918ae24e43b1bcb1c7dc42a630b69050a042404f1307a848ed14f97a2`;
  neither was regenerated.
- Decision for this iteration: prefer Snapshot for subsequent production STEP
  isometric overviews, retain Build123d MCP `render_view()` for in-memory
  scratch geometry, and keep the existing direct section renderer as fallback
  until a true Snapshot section/clip proves equally diagnostic. Durable
  repository rules are not changed by this one trial.

## 2026-07-22 — deleted-face-plate candidate loaded in Text-to-CAD Viewer

- At the user's request, the exact source-deletion candidate was exported for
  interactive review without modifying or rebuilding the last valid production
  STEP. The production source still contains no `face_plate` constructor,
  fusion, replacement solid, downstream cutter, or face-index selector.
- The rejected in-memory bucket was captured at the existing sand-cap
  validation stop and published only as the explicitly unpromoted workbench
  artifact
  `build/workbench/enclosure_baffle_recovery/deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step`,
  SHA-256 `a6f1974081abf980cea2b8eb4c29669e0f6a7bdd0ac4db46af49a09fd3409f3d`.
  This capture does not bypass or alter geometry; it preserves the exact solid
  already built before the known validation rejection.
- Coordinated export job
  `20260722T201248-deleted-face-plate-viewer-candidate-d769090907` used worker
  PID 17397, elapsed 232.807 s, peak RSS 1,308,557,312 bytes (1.22 GiB), exit
  0, four atomic outputs, clean process-group cleanup, and no orphaned worker.
- Deterministic candidate evidence: bucket STEP round-trips as one valid solid,
  volume `1080911.350297 mm3`, 300 faces, and 893 edges; the four old face
  signatures matching artifact-local tokens `#f91`, `#f97`, `#f21`, and
  `#f16` have zero matches. Bucket/baffle overlap, gasket overlaps, and fill
  passage blockage are each `0.0 mm3`.
- The known contract failures remain explicit: bucket-side gasket support is
  `0.082279` against the required `0.985`, while baffle-side support is
  `1.000000`; the non-fill sand-cap opening is `6241.862940 mm3`. The Viewer
  artifact is therefore evidence for the requested removal, not an accepted or
  production-ready enclosure.
- The Text-to-CAD topology sidecar was generated from that exact STEP under
  coordinated job
  `20260722T201727-viewer-sidecar-deleted-face-plate-candidate-e0d22f97cc`:
  worker PID 18473, elapsed 4.036 s, peak RSS 393,199,616 bytes (0.37 GiB),
  exit 0, clean cleanup, and no orphan. It contains one occurrence/shape, 300
  selectable faces, 893 selectable edges, no unmapped surface edges, and the
  exact candidate STEP hash. A first configuration-only attempt failed before
  CAD import because the checkout-local `cadpy` module path was missing; it
  produced no output and was cleanly reaped before the corrected bounded retry.
- The reusable Text-to-CAD Viewer was activated for the candidate directory at
  `http://127.0.0.1:4178/`; both the candidate link and the original artifact's
  explicit-directory link returned HTTP 200. New `#...` references are local
  only to candidate hash `a6f19740…3409f3d`; the old tokens must not be reused
  against this artifact.
- The mandatory direct review used one pinned Snapshot packet against the same
  sidecar: one isometric and one true `YZ` section at `X=-86 mm`. Coordinated
  job `20260722T201954-snapshot-deleted-face-plate-candidate-381c7e8658` used
  worker PID 21267, elapsed 3.593 s, peak RSS 890,028,032 bytes (0.83 GiB),
  exit 0, clean cleanup, and no orphan. The shared headless runtime reused the
  same source for both outputs without operating the interactive Viewer.
- Agent inspection: the isometric shows the four broad front corner plates are
  absent while the intended hollow upper fill supports, outer shell, and seam
  rails remain. The section shows the upper-left fill-support profile without
  the former 3 mm front plate; it also exposes the open-cap condition already
  quantified by the deterministic check. No discrepancy was observed among
  the candidate STEP, sidecar/Viewer representation, and saved Snapshot views.

## 2026-07-22 — correction from candidate-local face references

- Artifact: `build/workbench/enclosure_baffle_recovery/deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step`,
  SHA-256 `a6f1974081abf980cea2b8eb4c29669e0f6a7bdd0ac4db46af49a09fd3409f3d`.
  References `#f207`, `#f210`, `#f209`, `#f211`, `#f250`, `#f188`,
  `#f32`, and `#f190` are local only to this artifact/hash.
- The earlier assertion that the old selected face signatures were absent was
  wrong. That check ran on the pre-export shape; STEP healing renumbered the
  faces, and the exported candidate contains the same four front-face
  signatures. The Snapshot interpretation that the plates were absent was
  therefore also wrong. The user's Viewer selection correctly showed that the
  obstruction survived.
- Read-only coordinated topology inspection resolved the selected geometry as
  four shallow outer-corner sectors on `Y=-75.816667 mm`. The selected side
  and cylindrical faces extend only `0.7–1.2 mm` behind that plane. The old
  upper-left `#f91` signature is exactly candidate `#f207`; old upper-right
  `#f97` is exactly candidate `#f188`; candidate `#f32` and `#f190` are the
  lower-left and lower-right signatures.
- Coordinated provenance job
  `20260722T203351-trace-selected-corner-residue-450d433bfe` used worker PID
  46803, elapsed `105.461 s`, peak RSS `888,619,008 bytes` (`0.83 GiB`), exit
  0, atomic report publication, clean workspace/process-group cleanup, and no
  orphaned process.
- The lower-left and lower-right selected volumes are present `100%` in the
  imported monolithic base, remain `100%` after the nested split, receive `0%`
  coverage from the existing broad-interface reset, receive `0%` coverage
  from the projected service-opening reset, and receive `0%` contribution from
  the support wedge or fill-support additions. The repeated object is thus an
  inherited base-shell remainder, not the deleted face plate and not a current
  added feature.
- Source correction: keep the existing cleanup operation, but update its
  existing outer envelope from the stale `184.2 mm` span to the enclosure
  width plus `2 mm`, and update its existing rear limit from only `0.2 mm`
  behind the shoulder to the full existing `3 mm` front-bulkhead depth. This
  changes the partition that owns the residue; it adds no new cutter, mask,
  cleanup pass, or transient topology selector.

## 2026-07-22 — actual inherited front component removed

- Correction to the immediately preceding provenance note: the Viewer-selected
  planar faces are on the baffle-bed plane at `Y=-75.816667 mm`; the bucket
  shoulder is exactly `1.0 mm` rearward at `Y=-74.816667 mm`. The first probe
  window was shifted rearward by that millimetre and was rerun on the exact
  selected plane before the source decision was finalized.
- Coordinated exact-plane verification job
  `20260722T204803-verify-exact-selected-volume-b2529b1dba` used worker PID
  97290, elapsed `101.199 s`, peak RSS `972,554,240 bytes` (`0.91 GiB`), exit
  0, clean process/workspace cleanup, and no orphan. The corrected existing
  reset covers `100%` of the old candidate volume in all four measured
  `1.20 mm`-deep semantic corner regions; the post-reset bucket contains
  `0.0 mm3` of every region.
- Widening the reset exposed the actual ownership boundary. The existing cut
  separates a `1,070,334.824 mm3` rear bucket from a `59,922.659 mm3` obsolete
  front component whose complete bounds are ahead of the joint
  (`Y=-87.000000…-78.966667 mm`). The old corner sectors were the bridges that
  incorrectly kept that front component attached to the bucket.
- Production-source change: the existing broad-interface reset now uses the
  full enclosure span and an intentionally oversized near-square outer
  envelope, and its existing rear limit reaches the full `3 mm` interface
  depth. The old one-solid cut assumption was replaced by retaining the
  semantically rearward solid after that existing cut, thereby omitting the
  detached obsolete front component. No new Boolean, mask, cleanup pass,
  face-index selector, or replacement blocker was added.
- The first disposable exporter failed cleanly because it expected to capture
  the old sand-cap exception, but the corrected construction proceeded past
  that exception. The wrapper was changed to export the successful returned
  candidate directly; the same failed path was not retried.
- Coordinated candidate export job
  `20260722T205438-export-successful-front-component-candidate-53dc30c660`
  used worker PID 8935, elapsed `205.521 s`, peak RSS `1,279,852,544 bytes`
  (`1.19 GiB`), exit 0, four atomic outputs, clean process/workspace cleanup,
  and no orphan.
- New review artifact:
  `build/workbench/enclosure_baffle_recovery/front_component_removed_candidate_viewer/front_component_removed_bucket.step`,
  SHA-256 `7acc893e36c83b416ccadaf10b82387b91cc47d24eb5618499c95c2f91fffa58`.
  It round-trips as one valid solid, volume `1,077,371.815612 mm3`, with 219
  faces and 627 edges. None of the four old selected planar signatures exists
  after STEP export. Bucket/baffle overlap, gasket overlaps, and fill-passage
  blockage are all `0.0 mm3`.
- The candidate is not promoted: bucket-side gasket support is `0.0` against
  the required `0.985`, while baffle-side support is `1.0`. The current
  non-fill sand-cap audit reports a negative oriented-volume value and is not
  accepted as proof of closure; that uncertainty remains explicit.
- Coordinated Text-to-CAD sidecar job
  `20260722T205843-viewer-sidecar-front-component-removed-45e8890aaf` used
  worker PID 20163, elapsed `2.528 s`, peak RSS `364,904,448 bytes`
  (`0.34 GiB`), exit 0, clean cleanup, and no orphan. The exact STEP hash is
  embedded in a one-occurrence topology sidecar with 219 selectable faces,
  627 selectable edges, and zero unmapped surface edges.
- The pinned Viewer at port 4178 was restarted/reused and returned HTTP 200 for
  the exact new artifact. Browser automation was not used.
- Coordinated Snapshot job
  `20260722T205943-snapshot-front-component-removed-56163087ba` used worker PID
  21892, elapsed `3.083 s`, peak RSS `792,412,160 bytes` (`0.74 GiB`), exit 0,
  clean cleanup, and no orphan. It read the same STEP/sidecar once and produced
  only an isometric plus a `YZ` section at `X=-86 mm`.
- Agent visual comparison: the old section contained the forward upper-fill
  tab and the matching lower-corner flange. Both are absent in the new
  section. The new isometric shows the open front perimeter and only the
  intended hollow upper fill mouths. No repeated four-corner blocker is
  visible; the gasket-support failure remains a separate measurable blocker.

## 2026-07-22 — repaired candidate with required bulkhead restored

- The earlier wrong deletion of the shoulder face plate was restored from its
  original source construction and reconciled with the current exact-inner-skin
  support wedge. This is a restoration of required gasket/sand-cap structure,
  not a replacement for the removed inherited front component. The restored
  plate begins at the bucket shoulder (`Y=-74.816667 mm`), one millimetre behind
  the obsolete component's selected front plane (`Y=-75.816667 mm`).
- The obsolete inherited front component remains omitted by the corrected
  interface partition. Post-export validation still finds zero matches for all
  four old selected planar signatures.
- Coordinated export job
  `20260722T210309-restored-bulkhead-front-component-removed-11e5cb965c`
  used worker PID 32450, elapsed `207.991 s`, peak RSS `1,291,026,432 bytes`
  (`1.20 GiB`), exit 0, four atomic outputs, clean process/workspace cleanup,
  and no orphan.
- Exact review artifact:
  `build/workbench/enclosure_baffle_recovery/front_component_removed_restored_bulkhead_candidate_viewer/front_component_removed_bucket.step`,
  SHA-256 `5b1af7984c32370eb343d44dc313d92eec57bf203cdc8211349f48e0d45cd73e`.
  It round-trips as one valid solid, volume `1,101,336.367678 mm3`, with 220
  faces and 632 edges.
- Deterministic checks: bucket and baffle gasket support are both `1.0`
  (required minimum `0.985`); unclosed non-fill sand-cap volume is `0 mm3`;
  fill-passage blockage is `0 mm3`; bucket/baffle and gasket overlaps are all
  `0 mm3`; and the old selected planar signatures are absent after STEP.
- Coordinated Text-to-CAD sidecar job
  `20260722T210648-viewer-sidecar-restored-bulkhead-candidate-5fe6552abb`
  used worker PID 33675, elapsed `2.524 s`, peak RSS `362,561,536 bytes`
  (`0.34 GiB`), exit 0, clean cleanup, and no orphan. The sidecar embeds the
  exact STEP hash and provides one occurrence, 220 selectable faces, 632
  selectable edges, and zero unmapped surface edges.
- The pinned Viewer was activated for this exact directory and its exact-file
  URL returned HTTP 200. Browser automation was not used.
- Coordinated Snapshot job
  `20260722T210725-snapshot-restored-bulkhead-candidate-b425dde3ec` used worker
  PID 37630, elapsed `3.090 s`, peak RSS `776,912,896 bytes` (`0.72 GiB`), exit
  0, clean cleanup, and no orphan. It generated only the isometric and left
  fill-axis `YZ` section from the exact Viewer STEP/sidecar.
- Agent visual inspection: the old upper forward tab and lower-corner flange
  remain absent. The restored shoulder wall is visible behind the joint, the
  upper fill mouth remains hollow, and the four repeated blocker sectors do
  not reappear. No mismatch was observed between the exported STEP, Viewer
  sidecar, and Snapshot images.

## 2026-07-22 — user rejected whole-component deletion; restore and retrace

- The user confirmed that the last candidate wrongly deleted the curved seam
  structure that seats the removable front baffle.  That seam is required and
  must be restored exactly.
- The unwanted geometry remains the four radiused hunks of plastic sitting on
  the flat front face: the two upper pieces directly in front of the fill
  holes and the corresponding two lower-corner pieces.  The previously
  supplied artifact-local references identify faces on those hunks, not the
  wanted seam ring.
- Root-cause correction: the prior source change widened the shared broad
  interface reset and replaced the one-solid cut with selection of the
  rearward Boolean result.  That discarded a mixed front component containing
  wanted seam geometry.  This inference and deletion were over-broad.
- Approved next action: restore the pre-mistake reset envelope and one-solid
  cut first.  Then use the selected face regions as semantic volumes and test
  their occupancy after each named construction stage until the exact creator
  is identified.  Delete or redefine only that creator, while independently
  proving the curved seat, gasket face, fill passages/blisters, and exterior
  shell are retained.

## 2026-07-22 — exact selected-face provenance and minimal source correction

- The user's additional A/B observation was adopted as a first-principles
  constraint: the rejected whole-front deletion removed both the unwanted
  hunks and the wanted elegant seat, so the correct boundary is the rear flat
  interface layer only—not the entire connected front construction.
- On immutable artifact
  `deleted_face_plate_candidate_viewer/deleted_face_plate_bucket.step`, the
  planar faces corresponding to `#f207`, `#f188`, `#f32`, and `#f190` were
  resolved by plane, center, area, bounds, and artifact face position.  Their
  1.20 mm-deep semantic target volumes total `148.741055572 mm3`.
- All four targets exist 100% in the imported base and survive the nested
  split 100%.  They are not created by the support wedge or fill supports;
  small coincident overlaps from later additions do not account for their
  source volume.
- Exact creator/retention cause: the existing
  `_broad_interface_reset()` outer envelope used `184.2 mm` width and a
  `20.0 mm` corner radius.  That cutter covers exactly 0% of every selected
  target, so the hunks are inherited shell material left behind outside the
  reset's overly rounded corners.
- Radius/width sweep under coordinated job
  `20260722T215333-trace-selected-corner-hunk-width-744942fc60` showed that an
  `r7.0 mm`, `184.3 mm` envelope covers every selected target 100%, leaves
  `0.0 mm3`, remains one valid connected bucket, and retains the original
  `Y=-87.0000001 mm` forward extent.  The cutter's original Y limits are
  unchanged and remain 0.05 mm behind the protected forward-seat slice.
- Production-source correction: replace only the existing reset width/radius
  literals `184.2, 20.0` with `184.3, 7.0`.  No new cutter, Boolean stage,
  cleanup pass, face selector, or rearward-depth expansion is added.

## 2026-07-22 — corrected seam-retaining corner-hunk candidate

- Correction to the semantic target depth recorded immediately above: the
  unwanted material occupies the exact `1.00 mm` layer from the baffle-bed
  plane to the shoulder plane.  The earlier `1.20 mm` probe included
  `0.20 mm` of the wanted shoulder face behind the target.  The corrected four
  target volumes total `128.886025777 mm3`.
- The production source retains the original one-solid cut and original rear
  limit (`SHOULDER_Y + 0.20`).  Its only geometry change is the existing
  `_broad_interface_reset()` outer profile from `184.2 mm, r20.0 mm` to
  `184.3 mm, r7.0 mm`.  The earlier whole-front-solid selection and reset-depth
  expansion remain removed.
- Full source validation job
  `20260722T213335-restored-seam-baseline-validation-56885d05e4` restored the
  reference/hybrid/complete construction but stopped at two strict seam sample
  mismatches out of 1,248.  A later full source candidate job
  `20260722T220435-build-clean-corner-hunks-candidate-final-target-153e30780f`
  stalled for `1040.222 s` inside the authoritative joint build and was
  cleanly cancelled and reaped with no outputs or orphaned processes.  The
  production-source promotion is therefore not claimed as validated.
- To obtain an auditable A/B review without another blind native-build retry,
  a disposable candidate was derived from the exact pre-mistake production
  bucket STEP, SHA-256
  `8cc4f826b530208d2f8b1db0cc69a35a31f7fb2093836e2bb8359b2dbfc8faa5`,
  by applying the same corrected reset profile only across the original
  baffle-bed-to-shoulder layer.  It is review evidence, not promoted source.
- Coordinated job
  `20260722T222424-build-step-derived-clean-hunks-candidate-8f7f4462c8`
  used worker PID `42319`, elapsed `48.473 s`, peak RSS `988,692,480 bytes`
  (`0.92 GiB`), exit 0, four atomic outputs, clean workspace/process-group
  cleanup, and no orphan.
- Exact review STEP:
  `build/workbench/enclosure_baffle_recovery/clean_corner_hunks_candidate_viewer/clean_corner_hunks_bucket.step`,
  SHA-256 `eaeed68103e3110ca3e888ece90002a7f2f98a8b174fab5906e7fb0bd9350b97`.
  It round-trips as one valid solid with 257 faces and 739 edges.
- Deterministic checks: selected hunk target remaining `0.0 mm3`; fill-passage
  blockage `0.0 mm3`; bucket/baffle overlap `0.0 mm3`; exterior bounds exactly
  unchanged on all six limits; forward extent retained at
  `Y=-87.0000001 mm`; and gasket-support ratio unchanged at
  `0.9904914529`.  The protected forward-seat slice and corrected reset remain
  separated by `3.15 mm` in this exact STEP-derived test.
- Coordinated topology-sidecar job
  `20260722T222525-text-to-cad-artifacts-ccc7688eca` used worker PID `43060`,
  elapsed `3.029 s`, peak RSS `376,389,632 bytes` (`0.35 GiB`), exit 0, clean
  cleanup, and no orphan.  It generated the exact-artifact 4,936,236-byte GLB
  sidecar, SHA-256
  `5ce3cf846bd77dd696c5a4e7404813947e5d46f9b0213ac5ac0d5d8fa08466d3`.
  The read-only pinned Text-to-CAD Viewer was reused on port 4179, and the
  exact hash-bound link was generated without browser automation.
- The first Snapshot attempt failed before rendering because macOS denied the
  sandboxed headless Chromium rendezvous; it produced no output and was
  cleanly reaped.  The documented unsandboxed Snapshot path then completed in
  coordinated job
  `20260722T222720-text-to-cad-artifacts-e590280741`: worker PID `49820`,
  elapsed `2.571 s`, reported render time `1838.620 ms`, peak RSS
  `851,968,000 bytes` (`0.79 GiB`), exit 0, clean cleanup, and no orphan.
- One Snapshot packet reused the exact existing STEP sidecar and generated
  only an isometric overview plus a true `YZ` section at `X=-86.0 mm`; it did
  not operate the interactive Viewer, include browser chrome, rebuild the STEP,
  or tessellate once per camera.
- Agent inspection: the Snapshot isometric clearly shows the restored curved
  perimeter seating seam around the front opening and no broad radiused corner
  masses on the flat interface.  The section shows the left fill passage open
  to the front and the retained seat profiles above and below it.  Snapshot is
  materially easier to read than the preserved cyan hidden-line overview;
  its shaded faces, explicit edges, cavity, and hatched section are coherent.
  No mismatch was observed among the candidate STEP, sidecar/Viewer, and saved
  images.  The preserved `mcp_bucket_iso.png` and
  `mcp_upper_fill_section.png` were not regenerated or overwritten.

## 2026-07-22 — Viewer catalog-timeout repair

- The user reported `CAD catalog unavailable: Timed out loading CAD catalog
  after 10s` on the candidate Viewer handoff.  Geometry and sidecars were left
  unchanged.
- Port 4178 was diagnosed as an older generation-enabled Viewer and is not an
  approved repository review channel.  Port 4179 is the pinned 0.3.9 read-only
  Viewer with STEP artifact generation disabled.
- The failed handoff scoped the directory catalog to the entire `build/` tree.
  The repository link helper now scopes `dir` to the exact STEP's containing
  directory and `file` to its basename, while retaining the existing check
  that the artifact is under the configured `build/` root.
- The candidate-directory catalog returns HTTP 200, contains exactly the
  corrected bucket and unchanged baffle STEP files, and completed in
  `0.087556 s`.  The exact-file page returned HTTP 200 in `0.001504 s`.
- Four focused `unittest` checks passed, including the new artifact-directory
  link-scope regression test.  No CAD geometry, STEP, sidecar, or Snapshot was
  rebuilt or modified.

## 2026-07-22 — three-reference artifact handoff

- User confirmed that `simple_tongue_groove_baffle.step` is the desired
  flat-bottom baffle reference.  Only its genuinely flat print edge is
  approved for the next refactor; its tongue-and-groove and other seam details
  are not thereby approved.
- The current near-finished enclosure reference remains the unpromoted
  `clean_corner_hunks_bucket.step`: it retains the wanted curved seating seam
  and removes the four unwanted corner/fill-port hunks, but still has the
  wrong bottom material ownership.
- The older standalone bucket that paired with the validated flat-bottom
  hybrid was overwritten by a later build.  Its exact geometry survives in
  the immutable `hybrid_seam_assembled.step` as the first/larger of two valid
  solids (bucket volume `1111212.853475 mm3`; baffle volume
  `233360.515637 mm3`).  This assembly is the safe bottom-transfer enclosure
  reference: it has the complementary flat bottom and exact left/right/top
  seam, but predates the current corner-hunk removal.
- A coordinated attempt to detach that bucket into a new standalone STEP was
  rejected because the detached STEP re-imported as an invalid solid; kernel
  normalization did not repair it.  No output was published.  The untouched
  archived assembly is supplied instead so the handoff does not silently
  introduce damaged geometry.
