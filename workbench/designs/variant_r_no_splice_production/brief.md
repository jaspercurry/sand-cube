Implement and verify the production Variant R no-splice correction, then prepare an exact read-only CAD Viewer artifact for user review. Work autonomously in this fresh worktree and commit the focused result; do not merge or push main.

Start/safety:
- Read all applicable AGENTS.md and use the repository-local `speaker-enclosure-cad` skill throughout.
- Verify the starting ref is current `origin/main`, expected merge commit `5ec9980` containing the reviewed enclosure atomic refactor. Stop and report if it differs materially.
- Reuse `/Users/jaspercurry/Code/CAD - Enclosure/.venv` and pinned project tools. All native CAD, STEP, sidecar, Snapshot and substantial geometry diagnostics must run through `cad_runner`; no upgrades.
- Preserve unrelated work and use a new `codex/` branch in the worktree.

Exact product goal:
- Remove the unwanted full-width horizontal B-rep splice line around Z=-80.1 mm from both the visible Variant R baffle apron and the corresponding enclosure/bucket exterior.
- Preserve overall enclosure form, dimensions, driver opening/recess, sculpted L/R/T seam, gasket path/support, bucket/baffle separation, print orientation/contact, and every unrelated feature. Do not redesign geometry or touch Variant I, horn, electronics, fasteners, retention, or acoustics.
- A topology change is expected and required to remove the real edge; do not claim literal topology identity. Avoid same-domain healing, splitter removal, cosmetic mesh suppression, or tolerance widening.

Validated specification/evidence:
- Read commit `5f5bbf3c2aca0f55f35ae734c8dc0c6004897f75` and the full `workbench/designs/variant_r_underside_seam_refinement/` records via git. It is a validated workbench candidate, not a production implementation; do not simply describe or cherry-pick it as the fix.
- Promote its construction cleanly through the refactored Variant R owners: use the continuous exact-edge flat-bottom donor already exposed by the foundation/composer, bypass the whole-part Z=-80 splice and lower material-transfer operations in the active path, and trim only the baffle’s sub-sole excess to the validated planar sole at Z=-91.495 mm. Discard the ~0.355323 mm underside-only band as specified. Implement one explicit source of truth for this sole plane and honest audit metadata.
- Keep the correction localized to the refactored Variant R assembly/bottom ownership/parameters/print-contract boundary. Do not rewrite the legacy cascade or broaden architecture.

Acceptance:
- Create a concise new iteration brief/contract/feedback record preserving this user direction and clearly separating preserved form from necessary B-rep topology change.
- Run native-free checks first, then the smallest proportional CAD build/fit/topology comparison, then release/round-trip and visual evidence.
- Require zero old-splice-height edges and zero unrelated full-width lower-apron edges on both baffle and bucket. Compare against the validated candidate expectations (candidate baffle 91 faces/257 edges) and diagnose any mismatch rather than normalizing it.
- Prove one valid solid per part, assembly three solids, zero unintended overlap, continuous bottom seal, full gasket support, planar baffle sole/contact at Z=-91.495 mm meeting the prior width/area minima, protected visible-surface continuity/deviation, unchanged intended seams/features, and STEP round-trip.
- Generate the smallest matched edge-overlay/smooth visual evidence, inspect it, and publish the exact final review STEP plus current sidecar with a read-only Viewer link. The former line must be visibly absent from the baffle and side.
- Update current model/atomic ownership/known-boundary records only where authoritative facts change; preserve the prior refactor history rather than rewriting it. Catalog ownership should remain unchanged unless genuinely required. Run catalog/entrypoint/lint/fast checks.
- Commit the complete focused correction with a clean worktree. Final response must report branch and commit, changed ownership path, exact geometry checks, timings/peak memory, artifact/sidecar/Snapshot hashes, and the exact Viewer URL/path. Do not merge or push.
