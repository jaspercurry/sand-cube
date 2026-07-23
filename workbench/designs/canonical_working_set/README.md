# Canonical working set

This directory is the clean entry point for the enclosure cleanup and future
refactor. It does not declare unfinished geometry to be production-ready.
Instead, it keeps three different things visibly separate:

1. **authoritative source** — the current parameterized Python owner;
2. **accepted reference evidence** — exact, hash-bound STEP or diagnostic
   files that establish a desired shape or relationship; and
3. **future canonical output** — geometry that does not exist until the
   relevant source has been reconciled, built, validated, and accepted.

The files under each `links/` directory are relative symbolic links. They make
the working set easy to navigate without flattening or relocating the existing
experiment dependency chains. Hash-bound artifact links resolve to immutable
component-local `reference_evidence/` files; source and handoff links resolve
to their real repository owners. Edit authoritative source only after reading
the component contract and its original handoff.

This map is now self-contained in a clean Git checkout. Its selected evidence,
source, handoff, and deferred-project links resolve without access to the
intake checkout or ignored `build/` output. The component manifests retain the
original generated paths and freshness caveats.

## Start here

| Unit | Current role | Geometry status |
|---|---|---|
| [Removable front baffle](enclosures/removable_front_baffle/README.md) | Active enclosure recovery | Three approved reference roles; no reconciled final pair yet |
| [Integral front / bottom hatch](enclosures/integral_front_bottom_hatch/README.md) | Independent future enclosure variant | Full-perimeter exterior frozen; monolithic source branch and hatch not built |
| [40 mm bass-reflex tube](acoustics/bass_reflex_tube/README.md) | Deferred packaging lineage | Preserved historical route; blocked on final enclosure |
| [D-squat resonator](acoustics/d_squat_resonator/README.md) | Deferred Rev C/Rev D reconciliation | Rev C placement and Rev D acoustic references remain distinct |
| [Smaller-enclosure horn](horn/README.md) | Placeholder and formula owner | Current ~222 mm horn is a source reference, not the final 190 mm-package horn |
| [Archive index](archive/README.md) | Navigation for older work | Retained in place; not part of the active working surface |

The enclosure variants share a design family but deliberately use different
bottom/front ownership. Read [the enclosure family overview](enclosures/README.md)
before borrowing geometry between them. The port and resonator remain deferred
until their enclosure gate is satisfied.

## Landing context

- Inventory date: 2026-07-22
- Clean landing base: `73b29e51434e4a139efcb09574f8dc1c94bd485f`
  (`origin/main` at intake).
- Read-only input HEAD:
  `ea5539f3372e1bad5ad05eba85f4bd9a53e8c868`.
- Landing branch: `codex/input-landing`; the commit containing this record is
  the reviewed input-landing commit.
- The dirty input checkout remains untouched. Exact source dispositions,
  hashes, sizes, and exclusions are recorded in
  `../input_landing_2026_07_22/`.

## Rules for the next refactor

- Python is authoritative; linked files under `reference_evidence/` are
  evidence only.
- Do not edit or regenerate a hash-bound reference in place.
- Do not collapse the linked experiment ancestry into this directory.
- Start a new independent variant for the integral-front enclosure.
- Do not touch tube or resonator geometry until the relevant final enclosure
  source, STEP outputs, hashes, volume, keepouts, and installation path are
  accepted.
- Run native CAD through `cad_runner`, and use the repository review workflow
  for any visible checkpoint.

See [lineage.md](lineage.md) for the dependency boundaries and
[contract.md](contract.md) for the organizational acceptance criteria. Run
`shasum -a 256 -c reference_checksums.sha256` from this directory to verify
that the self-contained linked working set has not drifted from this
checkpoint. A clean checkout is required to pass this check.
