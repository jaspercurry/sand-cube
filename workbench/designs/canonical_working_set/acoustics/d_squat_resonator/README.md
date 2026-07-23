# D-squat resonator

## Two baselines that must remain distinct

1. The linked `integrated_rev_c_placement.step` shows the existing four-piece
   placement on the 56 mm service straight. It uses Rev C geometry with a
   nominal `7.166388 mm` slot.
2. Rev D is the latest acoustic/calibration study. It targets a provisional
   `338.25 Hz` bare-port mode and uses four nominal
   `0.400 × 9.066233 mm` finished slots. It is not integrated or
   production-validated.

Use Rev C for placement provenance and Rev D for the latest calibration
method. Do not silently copy Rev D dimensions into the old placement or carry
the old route-length definition into Rev D.

## Resume gate

The final enclosure and bare final port must be established first. Measure the
bare printed port before treating 338.25 Hz as authoritative. CAD can prove
geometry, bore clearance, cavity/slot dimensions, gasket and retention space,
printing, and service access; it cannot prove modal suppression.

## Local links

| Link | Meaning |
|---|---|
| `links/rev_c_source` | Integrated mechanical source and supporting model code |
| `links/rev_d_source` | Latest independently versioned calibration source |
| `links/deferred_project_record` | Shared tube/resonator contract and resume gate |
| `links/integrated_rev_c_placement.step` | Existing placement reference |
| `links/rev_d_assembly.step` | Latest Rev D assembly reference |
| `links/rev_d_print_layout.step` | Latest Rev D manufacturing layout |
| `links/rev_d_diagnostics.json` | Rev D calculations, limitations, and checks |

See [source_manifest.md](source_manifest.md) for exact hashes.
