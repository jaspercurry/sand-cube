Work in `/Users/jaspercurry/Code/CAD - Enclosure`.

Use `$speaker-enclosure-cad` throughout this task.

# How to interpret this prompt

This prompt combines:

1. general project and product context;
2. the long-term enclosure-family vision; and
3. the task-specific instructions for atomic characterization and refactoring.

The context and long-term vision explain where the project is going. They are not authorization to make all described geometry changes now.

Only the explicitly authorized phases below may be executed:

- Phase A: read-only atomic characterization;
- Phase B: geometry-preserving atomic refactoring.

Mixing candidate geometry, reconciling the three removable-front references, designing the bottom hatch, revising printability geometry, and integrating acoustic components are later tasks.

If contextual aspirations conflict with the present refactor boundary, the refactor boundary wins.

# Mission

Turn the current collection of enclosure and baffle sources, experiments, handoffs, and reference artifacts into a trustworthy atomic model architecture.

First determine exactly what exists, which source owns it, what each reference proves, and how the current dependency chains work. Then refactor the reproducible geometry into small, explicit, independently verifiable units without intentionally changing geometry.

Optimize for:

- a single source of truth;
- strict separation of concerns;
- elegant modular code;
- explicit model and feature ownership;
- independent enclosure variants;
- fast feedback for ordinary edits;
- precise fit and interface feedback;
- release-quality evidence at meaningful checkpoints;
- minimal repeated CAD work; and
- a reusable AI-CAD workflow that can later be extracted into another repository.

The result should make later mix-and-match work safe and deliberate. Do not perform that mix-and-match work during this task.

# Start with the canonical working set

Begin with:

`workbench/designs/canonical_working_set/README.md`

Treat this directory as the trustworthy navigation and design map for the speaker project.

It distinguishes:

- authoritative parameterized Python source;
- supporting and historical source ancestry;
- accepted, hash-bound reference evidence;
- future geometry that does not yet exist; and
- archived work that should remain available but outside the active design surface.

Python source remains authoritative. STEP files, diagnostics, sidecars, and images under `build/` are derived reference evidence, not production source.

Files under `links/` point back to existing owners. Do not replace those links with copied source or STEP files. Do not flatten, move, or duplicate the older dependency chains merely to make navigation easier.

Read the working-set root files in full:

- `README.md` — entry point and current project status;
- `AGENTS.md` — scoped operating rules;
- `lineage.md` — existing generator ancestry and ownership boundaries;
- `contract.md` — organizational boundaries and acceptance criteria;
- `reference_checksums.sha256` — exact selected source and evidence hashes;
- `feedback.md` — how the map was created and validated;
- `archive/` — older variants outside the active design surface.

Then read the README and `source_manifest.md` for every selected component.

The canonical working set is a curated navigation layer. It must not become a competing model catalog or geometry registry.

# Fundamental project units

## 1. Removable-front-baffle enclosure

Directory:

`workbench/designs/canonical_working_set/enclosures/removable_front_baffle/`

This is the future two-piece enclosure:

1. an enclosure bucket; and
2. a separately printed removable front baffle.

Manufacturing intent:

- The bucket prints with its rear face on the print bed, like an open bucket growing upward toward the front.
- The baffle prints separately in a vertical orientation, standing on its narrow bottom edge.
- The baffle therefore requires a genuinely flat, stable, full-width bottom printing edge suitable for a brim.
- The vertical orientation is intended to reduce undesirable visible layer-line effects.
- The baffle retains a deliberate sculpted seam around its left, right, and top perimeter.
- The bucket and baffle must have intentional, complementary bottom material ownership.
- Future hinge and lower-fastener systems are deferred.

The desired eventual bucket/baffle pair currently draws from three distinct references:

### Near-perfect bucket

This supplies:

- the clean curved seating seam;
- preservation of the wanted sculpted relationship; and
- removal of the unwanted four corner/fill-port hunks.

Expected reference:

`build/workbench/enclosure_baffle_recovery/clean_corner_hunks_candidate_viewer/clean_corner_hunks_bucket.step`

It still has the wrong bottom material ownership. It is STEP-derived evidence and has not been promoted to authoritative parameterized source.

### Archived hybrid assembly

This supplies the intended bottom material-ownership relationship between bucket and flat-bottom baffle.

Expected reference:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/hybrid_seam_assembled.step`

The relevant bucket is the first/larger rigid solid identified in the working-set manifest. This reference predates the clean-corner-hunk result.

### Flat-bottom baffle

This supplies the required genuinely flat, full-width printing edge.

Expected reference:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_simple_tongue_groove_baffle/simple_tongue_groove_baffle.step`

Only its specifically documented contributions are approved. Do not infer that every hinge, tongue-and-groove, gasket, fastener, or seam detail in that artifact is accepted.

These three ingredients have not yet been reconciled into one accepted parameterized source or final bucket/baffle pair. That reconciliation is later geometry-synthesis work, not part of this equivalence-only refactor.

## 2. Integral-front/bottom-hatch enclosure

Directory:

`workbench/designs/canonical_working_set/enclosures/integral_front_bottom_hatch/`

This is an independent future enclosure variant with:

- the intended full-perimeter exterior;
- a permanent, seamless integral front/baffle;
- an open bottom during printing; and
- a separately printed bottom hatch added later.

Manufacturing intent:

- The enclosure prints in its normal upright orientation.
- The open bottom face sits on the print bed.
- The hatch is absent during the enclosure print.
- The open bottom provides access for removing internal support if needed.
- The front is part of the main enclosure body, so there is no removable-front seam.

Its future source should branch semantically from the monolithic model before the existing removable-baffle joint divides the geometry into a bucket and baffle.

The removable-baffle gasket gap, joint, fasteners, nut slots, and service features must eventually be absent from this variant. Do not merely suppress their final solids while retaining hidden dependence on removable-baffle construction.

However, removing those features and designing the bottom hatch are future geometry tasks. During this refactor, identify their source stages and establish a clean ownership boundary without changing the model.

The existing full-perimeter centered-captive-nut bucket, baffle, assembly, and diagnostics under the lightweight coherent closure lineage are reference evidence. Resolve the documented source/artifact freshness caveat before treating them as reproducible baselines.

## 3. Bass-reflex tube

Directory:

`workbench/designs/canonical_working_set/acoustics/bass_reflex_tube/`

This preserves the rear-corner, continuous nominal 40 mm bore and serviceable-tower lineage.

Its historic routing, tuning, and packaging are references only.

Do not modify or integrate tube geometry until the selected enclosure has:

- accepted parameterized source;
- current artifacts and hashes;
- established net volume;
- explicit keepouts;
- settled floor structure;
- a service and installation path; and
- an accepted print strategy.

During the enclosure refactor, record only its interface, keepout, volume, and access dependencies.

## 4. D-squat resonator

Directory:

`workbench/designs/canonical_working_set/acoustics/d_squat_resonator/`

Preserve two intentionally distinct references:

- Rev C is the existing mechanical-placement reference.
- Rev D is the latest acoustic/calibration study and has the wider nominal slot.

Rev D is not an automatic replacement for Rev C and is not production-validated.

The provisional 338.25 Hz target must eventually be checked against physical measurements of the final bare printed port. Do not claim that CAD alone validates that acoustic target.

Do not refactor or integrate resonator geometry during this enclosure task. Record only the mechanical interface and deferred dependency.

## 5. Horn

Directory:

`workbench/designs/canonical_working_set/horn/`

The current horn is a formula and construction reference. It may be too large for the intended smaller enclosure.

The repository contains the Le Cleac’h/JMLC calculation and construction implementation. A future smaller horn should receive its own explicit parameter model and owner rather than silently resizing or overwriting the stable horn.

Do not resize or integrate the horn until the enclosure envelope, mounting interface, and available package are accepted.

During this task, record horn clearance and mounting dependencies only.

## 6. Archive

The working-set `archive/` directory identifies historical and superseded work.

Preserve it for provenance and comparison. Do not make archived candidates part of the active source surface unless a manifest identifies a specific approved contribution.

# Product north star

The eventual enclosure family should contain two polished variants with the same intended design language and, wherever genuinely appropriate, the same exterior envelope and shared primitives.

## Variant R — removable front

- Rear-face-down printed bucket.
- Separate vertically printed baffle.
- Flat full-width baffle printing edge.
- Sculpted left/right/top seam.
- Complementary bottom material ownership.
- Future top hinge and lower fasteners.

## Variant I — integral front

- Permanent, seamless integral front/baffle.
- Upright print orientation.
- Open bottom placed on the print bed.
- Separately printed future bottom hatch.
- No hidden removable-front joint or service geometry.

The variants should share family-level dimensions and genuinely identical primitives where evidence supports that sharing. They must retain independent assembly owners and variant-specific closure architecture.

Do not implement these final variants yet. The present task prepares trustworthy atoms for the later synthesis session.

# Future printability intent

Print orientation must become a first-class design constraint.

For both variants, internal braces, walls, and transitions should eventually:

- grow from supported geometry where practical;
- avoid abrupt unsupported horizontal ledges;
- respect reasonable overhang angles;
- avoid inaccessible trapped support;
- maintain service access;
- preserve sand-fill and drainage behavior; and
- place layer lines appropriately for appearance and strength.

For Variant R:

- characterize the bucket’s rear-face-down build direction;
- characterize the baffle’s vertical build direction;
- protect its flat bed-contact edge; and
- identify seam, bracing, or collar geometry that may be difficult in those orientations.

For Variant I:

- characterize the open-bottom-down orientation;
- identify whether the open bottom provides adequate support-removal access;
- identify internal structures that should later grow gradually from walls; and
- reserve a clean bottom-hatch boundary.

This task records current printability behavior and risks. It does not redesign the geometry to correct them.

# Sources of truth

Maintain these authority boundaries:

- Parameterized Python owns geometry.
- Owning parameter modules own dimensions and tolerances.
- `.cad-project/models.toml` owns model identity, lifecycle, owner, entrypoint, validator, and output location.
- The canonical working set owns navigation and provenance only.
- Files under `build/` are derived, hash-bound evidence.
- Released files under `releases/` are immutable.
- Viewer `#...` references are transient artifact-local review handles, never source selectors.

Use one machine-readable atomic manifest as the authoritative atom description. Human-readable maps and matrices must be generated from it or refer to it instead of duplicating facts manually.

# Mandatory preflight

1. Confirm this task is running on a clean dedicated branch or worktree based on local `main`.
2. Confirm local `main` contains commit `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868` or a descendant.
3. Confirm the separate input-landing task has committed:
   - the canonical working set;
   - its intended links and checksum file;
   - the selected source inputs;
   - the enclosure recovery record; and
   - any other user-supplied files intended for characterization.
4. Check whether the working-set README or manifests still describe their sources as untracked, modified, or observed at an obsolete HEAD. Refresh those provenance statements deliberately; do not rewrite unrelated history.
5. Run the working-set checksum verification.
6. Run `.venv/bin/python scripts/cad_review.py doctor`.
7. Run catalog validation and the native-free lightweight suite.
8. Reuse the repository `.venv` and pinned tools. Do not upgrade the CAD stack.
9. Run all native CAD through `cad_runner`.
10. Preserve unrelated and uncommitted user work. Never reset, clean, overwrite, or broadly commit it.
11. Treat `releases/enclosure_v1/` as immutable.

If required inputs are missing or exist only in another dirty checkout, stop before editing. Report the exact missing paths. Do not copy them ad hoc.

Read before acting:

- repository and scoped `AGENTS.md` files;
- the complete `$speaker-enclosure-cad` skill and applicable references;
- `.cad-project/project.toml`;
- `.cad-project/models.toml`;
- `.cad-project/enclosure-contract.md`;
- `docs/DEVELOPMENT.md`;
- `cad_verification/README.md`;
- all canonical working-set root and selected component documents;
- `workbench/designs/enclosure_baffle_recovery/`;
- every selected owner, parameter source, generator, validator, and handoff; and
- the relevant source ancestry named in `lineage.md`.

Preserve this prompt verbatim in the iteration’s `brief.md`. Put interpreted requirements in `contract.md` and chronological findings and decisions in `feedback.md`.

# Target source architecture

Do not create one giant generator controlled by flags such as `removable_front=True`.

Aim for three layers.

## Shared enclosure-family layer

Only place a feature here after proving identical semantics and geometry across the relevant variants.

Possible responsibilities include:

- family-level dimensions;
- named datums and coordinate conventions;
- exterior profile definitions;
- material and wall parameters;
- pure reusable geometry primitives;
- print-orientation metadata;
- generic measurement helpers; and
- neutral validation predicates.

If existing models disagree, record the disagreement. Do not force false commonality merely to reduce line count.

## Variant R owner

Owns:

- bucket composition;
- front service opening;
- sculpted left/right/top seat;
- bottom material ownership;
- separate flat-bottom baffle;
- gasket and seam relationship;
- future hinge interface;
- future lower-fastener interface; and
- rear-face-down bucket and vertical-baffle print contracts.

## Variant I owner

Owns:

- monolithic/integral front composition;
- continuous front exterior;
- open bottom;
- future hatch boundary; and
- upright, open-bottom-down print contract.

Each variant must have an independent authoritative assembly owner, generator, validator, and output.

Separate:

- pure parameter data;
- geometry builders;
- variant assembly composition;
- deterministic measurement;
- verification and evidence adapters;
- export; and
- thin entrypoints.

Avoid:

- circular imports;
- hidden source mutation;
- monkeypatching ancestors;
- deep experiment imports in future production owners;
- copied dimensions;
- copied schemas;
- copied profile policies; and
- competing catalogs.

# Phase A — read-only atomic characterization

Do not edit geometry source in Phase A.

Create a chronological workbench iteration containing:

- `brief.md`;
- `contract.md`;
- `feedback.md`;
- the authoritative machine-readable atomic manifest;
- generated or referential human-readable maps;
- baseline records; and
- compatibility and dependency reports.

## Inventory

For every selected source, candidate, and artifact, record:

- exact path and SHA-256;
- catalog identity and lifecycle status;
- owner, supporting source, historical source, or derived-evidence role;
- parameter ownership;
- units, datums, coordinate system, axes, and transforms;
- construction and Boolean stages;
- import ancestry and hidden mutation;
- outputs and output paths;
- validators and enforced invariants;
- exact STEP, diagnostics, sidecar, and image hashes;
- what the item demonstrably gets right;
- what it gets wrong or leaves unresolved;
- source/artifact freshness;
- downstream consumers;
- confidence and uncertainty.

## Atom discovery

Derive the final atom list from the actual source. Investigate at least:

- exterior envelope;
- exterior shell;
- inner wall and sand void;
- rear face;
- integral front;
- removable front opening;
- front bulkhead and gasket support;
- sculpted left/right/top seam;
- bottom material ownership;
- baffle body;
- flat baffle print edge;
- driver opening and mounting interfaces;
- gasket land and compression;
- corner sealing;
- fill blisters and fill passages;
- braces and internal supports;
- print datums and build orientations;
- support-sensitive transitions;
- future hinge interface;
- future fastener interface;
- future hatch interface; and
- deferred horn, tube, resonator, bracket, and electronics interfaces.

For each atom, record:

- stable semantic ID;
- owning variant;
- owning source and parameters;
- dependency and consumer relationships;
- mating atoms;
- candidate references;
- reproducible baseline;
- protected invariants;
- fit tolerances;
- print-orientation implications;
- conflicts;
- whether it is actually shareable; and
- refactor readiness.

## Variant comparison

Produce a derived matrix showing:

- atoms that are currently identical;
- atoms intended to be identical but currently different;
- intentionally variant-specific atoms;
- ambiguous ownership;
- STEP-only evidence;
- stale or unreproducible baselines;
- deferred geometry; and
- blockers to later synthesis.

Do not confuse matching names, dimensions, or bounding boxes with semantic equivalence.

## Reproducible baseline

Before refactoring any geometry, prove that its owning Python source can reproduce an accepted baseline.

Programmatic geometry is authoritative for:

- validity;
- solid and meaningful topology counts;
- dimensions and bounds;
- volume and center of mass;
- wall thickness;
- protected-section occupancy;
- gasket support and compression;
- corner closure;
- fill-passage clearance;
- part complement, gap, and overlap;
- interference and clearances;
- transforms; and
- STEP round-trip.

Record exact old source, input, STEP, sidecar, diagnostics, and visual-evidence hashes.

A changed STEP hash is evidence of changed serialization, not proof of geometric drift. A matching bounding box is not proof of equivalence. Use semantic measurements and protected sections with explicit tolerances.

If Python cannot reproduce a reference, retain that reference as evidence and mark the source boundary blocked. Do not promote re-imported STEP geometry as authoritative source.

## Printability characterization

For each part and variant, record:

- intended bed-contact face;
- build direction;
- seating footprint;
- brim or adhesion assumptions;
- unsupported surfaces;
- overhang angles;
- bridges;
- trapped-support risk;
- support-removal access;
- abrupt versus gradual brace growth;
- sand or air traps;
- layer-line implications; and
- later geometry work required.

Do not correct these issues during Phase A or the equivalence refactor.

# Characterization checkpoint

Before editing source architecture, present:

- authoritative input inventory;
- atomic map;
- family/variant compatibility matrix;
- dependency graph;
- reproducible baseline report;
- printability report;
- unresolved source/artifact conflicts;
- proposed module tree;
- proposed ownership boundaries; and
- proposed first pilot atom.

Wait for user approval. Do not proceed automatically through this gate.

# Phase B — geometry-preserving atomic refactor

After approval, refactor exactly one atom at a time.

The refactor must not intentionally change:

- exterior shape;
- wall structure;
- seam geometry;
- bottom ownership;
- gasket behavior;
- fill paths;
- braces;
- assembly position;
- hatch geometry;
- hinge or fastener behavior; or
- printability.

For every atom:

1. Identify its exact owning baseline.
2. List preserved parameters and invariants.
3. Make the smallest extraction or architectural change.
4. Run the native-free `fast` contract and lightweight checks.
5. Run coordinated `fit` checks for geometry-producing or interface atoms.
6. Compare against the frozen baseline with semantic measurements and protected sections.
7. Generate only the smallest useful visual comparison.
8. Stop on any unexplained mismatch.
9. Record before/after source and artifact hashes.
10. Update the feedback log.
11. Make one focused commit.

After the first successfully refactored atom, provide another user checkpoint showing:

- the source change;
- module boundary;
- equivalence evidence;
- timing and peak memory;
- visual comparison; and
- any architectural lessons.

Wait for confirmation before applying the pattern to the remaining atoms.

Use `release` verification only for complete meaningful milestones and the final refactor.

Update `.cad-project/models.toml` in the same commit only when identity, lifecycle, owner, parameters, entrypoint, validator, or output changes. Run `scripts/cad_review.py check-catalog` after every catalog edit.

# Evidence channels

## Programmatic geometry

Authoritative for measurable and functional claims.

## Text-to-CAD Viewer

The human interactive channel for rotation, clipping, visibility, and selection.

Record every copied `#...` reference with:

- exact STEP path;
- STEP SHA-256;
- copied token;
- semantic feature;
- question or requested change; and
- protected surrounding geometry.

Never retain transient indices in source logic.

## Text-to-CAD Snapshot

The agent visual-review channel for exported production STEP.

Normally produce:

- one isometric overview; and
- at most one question-specific section or detail.

Use the exact STEP and sidecar loaded in the Viewer. Import or tessellate once and reuse it across cameras.

## Build123d-MCP

Use `render_view()` only for disposable in-memory scratch geometry before a current production STEP exists.

## Focused repository renderer

Use when Snapshot cannot clearly express a required section, clip, highlight, isolation, or diagnostic view.

## Browser automation

Use only as a documented fallback for Viewer behavior that cannot be verified through geometry, sidecars, Snapshot, or direct renders.

# Completion and independent review

The task is complete only when:

- every in-scope atom has one unambiguous owner;
- each parameter and tolerance has one source of truth;
- shared primitives have proven identical semantics;
- Variant R and Variant I retain independent assembly owners;
- refactored models reproduce their own baselines within explicit tolerances;
- no mix-and-match geometry or redesign entered the refactor;
- fast, applicable fit, final release, catalog, entrypoint-safety, and lightweight checks pass;
- evidence is bound to exact current source and artifact hashes;
- meaningful final models have current Viewer and agent-inspected Snapshot evidence;
- printability findings are documented; and
- physical-print uncertainty remains explicit.

Then spawn a separate read-only adversarial review agent against the exact final commit in a clean checkout.

Review for:

- competing sources of truth;
- duplicated parameters or policies;
- accidental variant coupling;
- flag-driven architecture;
- geometry drift hidden by weak comparisons;
- stale or self-asserted evidence;
- incorrect provenance;
- catalog errors;
- unsafe CAD entrypoints;
- missing print contracts; and
- premature geometry changes.

Classify findings as Blocker, Should-fix, or Nit. Fix all Blocker and Should-fix findings and repeat review until none remain.

Do not merge to `main`, push, release, reconcile the three removable-front references, design the bottom hatch, resize the horn, or integrate acoustic components during this task.

# Final handoff

Finish with:

- final source/module tree;
- atomic ownership map;
- family/variant compatibility matrix;
- before/after measurements and hashes;
- fast/fit/release timing and memory statistics;
- printability findings;
- review findings and resolutions;
- unresolved risks and product decisions; and
- the proposed scope for the later model-synthesis task.

That later task will deliberately construct:

1. the rear-face-down bucket plus vertically printed removable baffle, using accepted contributions from the clean bucket, bottom-ownership, and flat-edge references; and
2. the upright, open-bottom-down integral-front enclosure with a clean future bottom-hatch boundary.

Horn, tube, resonator, bracket, electronics, final support-aware bracing, hatch mechanics, hinge mechanics, and fastener refinement remain subsequent phases.