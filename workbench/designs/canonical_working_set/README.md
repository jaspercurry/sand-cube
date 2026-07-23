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
the working set easy to navigate without copying, flattening, or relocating
the existing experiment dependency chains. Edit the real source only after
reading the component contract and its original handoff.

This is a map of the captured local working tree, not a self-contained archive.
A clean Git checkout intentionally lacks ignored `build/` evidence and several
still-uncommitted source or handoff directories. Nineteen convenience links are
therefore expected to be unresolved in a clean checkout until those exact local
dependencies are restored. The component manifests remain portable: they record
each repository path, role, tracking state, and available SHA-256 independently
of whether its convenience link currently resolves.

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

## Repository state captured

- Inventory date: 2026-07-22
- Observed repository HEAD: `42db80c8c5575e8df00c1dddd76b27362f1d42fc`
- The working tree already contained extensive modified and untracked user
  work. No pre-existing source or artifact was moved, copied, reset, or
  overwritten while creating this map.
- All three user-supplied enclosure-reference hashes and the existing deferred
  manifests were rechecked against the current files.

## Rules for the next refactor

- Python is authoritative; linked files under `build/` are evidence only.
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
the linked working set has not drifted from this checkpoint when the captured
local dependencies are present. A clean checkout is not expected to pass that
artifact-completeness check by itself.
