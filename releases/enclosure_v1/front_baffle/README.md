# Front Baffle V1 — print release

Status: **final V1; currently being printed**  
Frozen: **2026-07-20**

This folder is the immutable record of the exact four-fin front baffle approved
for the first physical print. Future baffle changes belong in development and
must be released as a later version; do not edit these V1 files in place.

## Canonical deliverables

- `artifacts/front_baffle_v1.step` — exact final CAD solid.
- `artifacts/front_baffle_v1_x2d_pla_matte.3mf` — exact native Bambu Studio
  project used for the Bambu Lab X2D / Bambu PLA Matte print.

The native project is already oriented with the gasket/collar face on the
textured plate and records 0.12 mm layers, six walls, seven top and bottom
shells, 0% sparse infill, supports off, and a 5 mm outer brim.

## Clean source boundary

The accepted baffle before the four permanent fins is frozen as
`source/inputs/front_baffle_v1_approved_pre_fin.step`. That STEP contains the
approved exterior, sealed gasket corners, driver collar, screw tunnels, and M4
nut traps. Freezing it prevents the final release from inheriting the long chain
of abandoned enclosure and bucket experiments.

`source/generate_front_baffle_v1.py` is the isolated release builder. It adds
only the four approved fins using the frozen values in
`source/front_baffle_v1_parameters.json`. The exact scripts used during the
original CAD and Bambu export are retained byte-for-byte under
`source/provenance/`; they are provenance, not the clean release entry point.

Run the release builder only through the repository CAD coordinator:

```sh
.venv/bin/python -m cad_runner run --repo . -- \
  releases/enclosure_v1/front_baffle/source/generate_front_baffle_v1.py
```

It writes a verification rebuild under `build/releases/enclosure_v1/` and does
not overwrite the canonical release artifacts.

## Verification

- `verification/geometry_diagnostics.json` records the approved CAD checks.
- `verification/bambu_project_diagnostics.json` records the native X2D project
  and mesh checks.
- `verification/rebuild_diagnostics.json` records the isolated release rebuild.
- `verification/checksums.sha256` locks every canonical artifact and source
  input to this release.
- `manifest.json` explains the release contents and boundary.
