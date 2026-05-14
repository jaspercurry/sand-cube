# Research Validation

Date: 2026-05-14

This file validates the supplied playbook before the CAD work starts. The
short version: the overall design direction is strong, but several dimensions,
tool assumptions, and BOM costs need correction before committing geometry.

## High-Confidence Keepers

- Use code-CAD with build123d and keep parameters in source control.
- Build the baffle recess as a revolved profile rather than chasing fragile
  post-boolean edge fillets.
- Use a point-like bracing strategy in the sand void: posts, collars, corner
  gussets, and local reinforcement rings.
- Prefer a permissive MIT license for a forkable maker repo.
- Validate passive radiator dimensions before CAD. This is not optional.

## Corrections Before CAD

- The Dayton Epique E180HE-PR is the right family match, but the official
  mechanical drawing is more useful than the abbreviated spec sheet for CAD.
  Use `pr_cutout_dia = 151.5`, `pr_overall_dia = 181.5`,
  `pr_recess_depth = 6.0`, `pr_bolt_circle_r = 84.75`, `pr_screw_count = 6`,
  and `pr_depth = 54.0` unless a newer official drawing says otherwise.
- Current Parts Express public pricing for the E180HE-PR appears much lower
  than the report's roughly $100 estimate, so the BOM should be recalculated.
- The E180HE-PR's published Vd is 258.59 cm3. Dayton's own product page says
  passive radiator displacement should generally be at least 2x the active
  driver Vd. The E150HE-44 spec sheet lists Vd as 139.7 cm3, so one E180HE-PR
  is close but slightly under that 2x rule. This is acceptable for a prototype
  with DSP limits, but it is a real output-risk note.
- The build123d 3MF export API needs a hands-on check. Current documentation
  says 3MF and STL mesh export are handled by `Mesher().write(...)`, while the
  report uses `export_3mf(...)`. Do not bake `export_3mf` into scripts until it
  imports in the local environment.
- `uv` is not installed on this Mac yet. The repo can still be scaffolded, but
  setup should include installing `uv` before dependency sync.
- The Claude-specific files in the report should be translated to Codex-era
  project guidance. This repo uses `AGENTS.md` as the starting point.
- The Polymaker material recommendation needs a current purchase check.
  Polymaker's current public pages show PETG product-line changes, so the
  practical recommendation may become Polymaker PETG or Bambu PETG-HF rather
  than legacy PolyLite PETG.

## Open Questions

- Confirm Dayton E150HE-44 physical depth against the mechanical drawing and
  actual mounting direction before implementing the front/rear internal
  clearance. The sourced product page and spec sheet agree on 122 mm cutout,
  152 mm OD, and 140 mm bolt circle; depth still deserves a physical sanity
  check because the driver and PR nearly consume the 167 mm internal span.
- Check acoustic volume before freezing the 203 mm cube. The nominal inner
  cavity is roughly 4.66 L before driver, PR, bracing, and rings. Dayton's
  product page lists a 0.15 ft3 sealed recommendation for the E150HE-44, about
  4.25 L, so the design is in the neighborhood but not spacious.
- Verify rear assembly clearance with physical parts. The E150HE-44 is
  rear-mounted and must pass through the rear PR opening before the PR is
  installed. The current CAD uses a 156 mm rear service aperture under the
  externally mounted PR flange because the sourced 151.5 mm PR cutout is too
  tight for a 152 mm driver OD once tolerances are included.
- Confirm whether build123d-mcp is installable and currently maintained enough
  to trust for this project. It should be treated as optional until installed.
- Decide whether the first CAD milestone exports STEP only, or also attempts
  3MF immediately after local API verification.
- Test one printed M20x2 thread coupon before committing to a printed fill
  plug for the full enclosure.

## Source Links

- Dayton Audio Epique E180HE-PR product page:
  https://www.parts-express.com/Epique-E180HE-PR-7-carbon-fiber-Cone-Passive-Radiator-295-114
- Dayton Audio Epique E180HE-PR spec sheet:
  https://www.daytonaudio.com/images/resources/295-114--epique-e180he-pr-spec-sheet.pdf
- Dayton Audio Epique E150HE-44 product/spec source:
  https://www.parts-express.com/Dayton-Audio-Epique-E150HE-44-5-1-2-DVC-MMAG-Subwoofer-295-102
- build123d import/export documentation:
  https://build123d.readthedocs.io/en/stable/import_export.html
- build123d operations documentation:
  https://build123d.readthedocs.io/en/stable/operations.html
- Bambu Lab PETG HF filament guide:
  https://us.store.bambulab.com/products/petg-hf
- Polymaker PolyLite PETG product page:
  https://polymaker.com/product/polylite-petg/
