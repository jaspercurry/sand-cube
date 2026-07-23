Work in a new clean Codex worktree based on commit `789cf7f` from branch `codex/atomic-characterization-refactor`.

Use the repository-local `$speaker-enclosure-cad` skill throughout. Do not touch the dirty primary checkout, merge to `main`, push, or release.

# Mission

Refine the accepted Variant R Stage 1 bucket/baffle pair so the removable baffle owns the visible lower-front apron and the bucket/baffle parting line moves to the underside of the enclosure.

The current geometry is valid and well-validated, but its lower material ownership is aesthetically wrong: material below the baffle’s planar print face was transferred to the bucket, leaving a visible seam across the lower front face.

The desired result has:

- no bucket/baffle seam crossing the visible front face;
- the baffle owning the visible lower-front material;
- the bucket owning the complementary recessed material behind/underneath it;
- the seam leaving the sculpted side joint at the lowest practical point on each bottom corner;
- a smooth mirrored transition that turns downward and then runs across the underside;
- the underside seam positioned as low and visually hidden as practical for a speaker sitting on a desk or table; and
- a genuinely planar, stable, full-width baffle printing sole.

Preserve the current assembled exterior wherever practical. A small local change is explicitly allowed in the lowest corner and underside band when needed to create the clean transition.

# Required reading and authority

Read completely:

- `.agents/skills/speaker-enclosure-cad/SKILL.md` and applicable references;
- `workbench/designs/atomic_characterization_refactor/brief.md`;
- `workbench/designs/variant_r_flat_bottom_synthesis/brief.md`;
- `workbench/designs/variant_r_flat_bottom_synthesis/contract.md`;
- `workbench/designs/variant_r_flat_bottom_synthesis/feedback.md`;
- `workbench/designs/variant_r_flat_bottom_synthesis/evidence_manifest.json`;
- the active generator, validator, README, and HANDOFF under:
  `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/`;
- the canonical removable-front-baffle README, source manifest, and three reference artifacts.

The original atomic brief SHA-256 must remain:

`7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`

Create a new iteration directory:

`workbench/designs/variant_r_underside_seam_refinement/`

Preserve this prompt there verbatim as `brief.md`. Put interpreted requirements in `contract.md` and record findings chronologically in `feedback.md`. Do not overwrite the completed flat-bottom-synthesis iteration.

# Current validated baseline

Authoritative commit:

`789cf7f`

Current generator SHA-256:

`6d8072eb32a1e86b54528fe80144155d0fc2b9d0996bdc76a8168c06e4c91f0c`

Current validator SHA-256:

`13e0dc227c64cfaa555e0a709ba7220c373319c5289f23bd3769aee871e7ddef`

Validated artifact hashes:

- bucket STEP:
  `836c2132b09eb950d46f52c26396bc499c71109dcc25a46b4ade77cc7522cd6b`
- baffle STEP:
  `4036538dfccd55541ada5b92be1cee68498127093f55aa6d0f03af263dda6006`
- diagnostics:
  `c827b673c83dc925e1a24fe72ad71205e49f7608acb56873de59814273030196`
- review assembly:
  `ffcd16f32f113f992666eadadb3c29a82fc4b0b339e38affc2fc49495aaa31c8`

If ignored build artifacts are absent in the fresh worktree, regenerate the baseline through `cad_runner`; do not copy artifacts ad hoc from another checkout.

# Corrected ownership intent

The original prompt explicitly identified:

- the archived bottom-ownership assembly as the intended complementary ownership reference; and
- the flat-bottom baffle as the print-edge reference.

Use those references only for their documented contributions. Do not Boolean-combine or promote imported STEP geometry as authoritative source.

The current `_transfer_baffle_below_print_plane()` policy transfers lower baffle material to the bucket. Diagnose it carefully and replace or reverse that ownership policy in parameterized source.

The preferred architecture is a baffle-owned wrap-under apron or sole:

1. Preserve the exact sculpted left/right/top seam above the new lower-corner transition.
2. Continue the baffle’s visible front skin through the bottom-front region.
3. Turn the parting line down around each corner below the normal visual horizon.
4. Run the lower parting line on a downward-facing or recessed underside surface.
5. Give the bucket a complementary recess behind/above that baffle-owned material.
6. Keep the gasket and structural closure continuous behind the cosmetic seam.

Do not reintroduce the old flat-edge reference’s `0.350323 mm` below-plane transition nubs. The new baffle must terminate on one true lowest planar face with no trimmed topology below it.

# Protected invariants

- Bucket and baffle remain separate, single valid solids.
- Both STEP files round-trip as one valid solid.
- Closed bucket/baffle overlap remains at or below `0.001 mm³`.
- The accepted sculpted left/right/top seam remains exact above the explicitly defined lower-corner transition.
- Driver opening, recess, mounting interfaces, fill passages and blisters, sand containment, wall structure, and protected exterior remain unchanged.
- Bucket and baffle gasket support ratios remain `1.0`.
- The lower gasket run remains one connected component.
- Bottom corner sealing remains complete.
- The baffle’s minimum-Z topology lies entirely on its planar printing face.
- Print-contact width and area must be no worse than the current measured `187.020979 mm` and `2277.950023 mm²`, unless a clearly superior stable footprint is measured and justified.
- Avoid thin knife edges, disconnected lower islands, sand/air traps, inaccessible support, and unsupported ledges.
- All monkeypatched ancestor state must be restored.
- `BUILD_TOP_HINGE=False` and `BUILD_BOTTOM_SCREWS=False`. Do not add retention geometry in this task.

The previous contract’s strict lower-band exterior-identity preference is superseded by this user correction. Preserve the assembled exterior where practical, but seam visibility and correct baffle ownership take priority within the smallest necessary lower-corner/underside band.

# Required seam-visibility checks

Convert the aesthetic requirement into measurable evidence:

- no shared bucket/baffle boundary may cross the front-facing lower apron;
- the lower shared boundary must be downward-facing, rearward-recessed, or otherwise hidden below the defined corner transition;
- front projection and a normal desk-level camera must show uninterrupted baffle-owned material across the lower front;
- the seam transition must be mirrored left/right and tangent or otherwise intentionally smooth;
- report the transition’s start location, minimum height, underside setback, wall thickness, and distance from the visible front silhouette.

Do not infer these facts solely from a bounding box or screenshot.

# Surface smoothness and Viewer triangulation

The current STEP is an analytic manifold B-rep with B-spline surfaces, not triangle geometry. The visible polygons in the web Viewer are primarily tessellation and edge-overlay artifacts.

Do not redesign the B-rep merely to remove Viewer mesh lines. Instead:

- audit tangent/normal continuity across the visible front surface and lower-corner transitions;
- distinguish real topological edges from Viewer tessellation;
- generate a smooth-shaded, sufficiently fine review sidecar or render;
- provide a close-up without distracting edge overlays if the tooling supports it; and
- record the intended fine mesh/export policy for later print preparation.

Do not claim perfect physical smoothness until continuity and fine-render evidence pass. Physical FDM surface quality remains dependent on slicing, layer height, printer calibration, and material.

# Workflow and checkpoint

Begin with preflight, current-baseline regeneration if required, and read-only diagnosis.

Then create the smallest useful parameterized lower-corner/underside candidate or coupon. Do not modify the production generator before this focused candidate answers the ownership and seam-placement question.

Provide one meaningful design checkpoint containing:

1. normal desk-level front view proving there is no visible front seam;
2. low underside view showing the actual seam path;
3. one section through a bottom corner showing ownership, gasket continuity, wall thickness, and print sole;
4. exact dimensions and validity/overlap measurements; and
5. a read-only Viewer link to the exact candidate.

Wait for user approval at this one design checkpoint.

After approval, proceed directly through production promotion without routine intermediate stops:

- encode the accepted result in the authoritative parameterized source;
- extend the validator with the new ownership and visibility checks;
- run complete coordinated fit and release validation;
- regenerate STEP files, topology sidecars, Viewer assembly, and inspected Snapshots;
- compare the promoted output with the accepted candidate;
- update the canonical working set and checksum map deliberately;
- create a standard release-verification packet and evidence manifest;
- run doctor, catalog, lightweight, entrypoint-safety, lint, checksum, JSON, and diff checks; and
- make focused local commits.

Do not stop with scratch geometry or stale Viewer artifacts. Do not push, merge, or release.
