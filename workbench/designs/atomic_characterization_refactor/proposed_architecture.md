# Implemented module tree and ownership

Status: implementation, final strict acceptance, exact visual evidence and
independent adversarial re-review complete. The accepted current Variant R
geometry remains the sole baseline; no Variant I or corrected flat-bottom
geometry exists.

```text
src/enclosure_family/
├── datums.py                  # family coordinate contract
├── legacy_runtime.py          # serialized, exactly restored legacy binding
├── print_contracts.py         # shared print-contract schema only
├── variant_r/
│   ├── parameters.py          # Variant R dimensions/tolerances
│   ├── print_contracts.py     # bucket and baffle print metadata
│   ├── seam.py                # sculpted L/R/T plus flat-bottom perimeter
│   ├── bottom_ownership.py    # accepted lower material transfer/splice
│   ├── foundation.py          # explicit legacy foundation dependency bundle
│   ├── assembly.py            # independent Variant R composition owner
│   ├── inputs.py              # authoritative generated-input contract
│   ├── historical_capture.py  # immutable accepted-base capture recipe
│   ├── provenance.py          # producer/source/tool attestation
│   ├── release_provenance.py  # post-geometry release attestation writer
│   ├── measurements.py        # deterministic native geometry facts
│   ├── equivalence.py         # native-free numerical acceptance predicates
│   ├── export.py              # STEP publication and round-trip adapter
│   ├── artifacts.py           # required output identities
│   ├── verification.py        # evidence dimensions and tolerances
│   └── model.py               # one explicit owner per Variant R boundary
└── variant_i/
    └── interface.py           # independent future-only boundary; no geometry

scripts/
├── generate_variant_r.py      # thin coordinated immutable-base producer
└── run_historical_variant_r_base_capture.py

workbench/designs/atomic_characterization_refactor/
├── attest_variant_r_release.py       # observational release-source probe
├── package_variant_r_review.py       # attested visual assembly adapter
└── project_variant_r_attestations.py # native-free committed audit projection
```

The active geometry leaf is retained as a compatibility adapter while the
accepted construction foundation is reproduced from exact commit `789cf7f`.
It no longer owns parameters, seam policy, lower material composition,
retention alternatives, evidence policy or artifact publication. Its remaining
deep ancestry and visible serialized temporary bindings are contained behind
the explicit immutable foundation producer and `VariantRFoundation`; new owners
import no experiment module. Removing that inherited binding mechanism requires
a separate cascade rewrite and is not represented as complete in this landing.
For the landed compatibility path, one in-process `RLock` surrounds
apply/use/restore, restoration is identity-checked and unit-tested, the release
diagnostics prove two identical build fingerprints with two successful
restorations, and coordinated production is limited to one CAD worker.

## Family and variant boundaries

The family layer owns only the proven 190x210 coordinate semantics and neutral
print-contract schema. It does not merge this design's 2/3/2 wall stack with
the repository's unrelated 203 mm 3/12/3 legacy contract.

Variant R independently owns the accepted removable-baffle composition,
including the current imperfect flat-bottom/missing-material relationship.
Retention geometry is explicitly absent. No flag-driven alternate Variant R/I
generator remains.

Variant I owns only a future interface contract for a monolithic front,
open-bottom body and future hatch owner. Calling its geometry owner raises
`NotImplementedError`; it imports no Variant R module and cannot route future
geometry through the removable-baffle implementation.

## Verification and publication boundaries

Builders return shapes and deterministic build metadata. Measurement consumes
shapes without publication. Native-free equivalence policy consumes measurement
records. The workbench comparison scripts are evidence adapters only. STEP
publication and reimport live in `variant_r/export.py`; model entrypoints remain
thin and resource-coordinated. `.cad-project/models.toml` remains the sole model
catalog.

The authoritative foundation producer publishes only the base STEP and its
attestation. A clean checkout obtains the exact accepted input by archiving the
immutable geometry commit, applying the committed capture-only overlay at the
accepted build boundary, verifying the complete STEP DATA payload, and
canonicalizing only the accepted `FILE_NAME` timestamp. The real job time stays
in the attestation. Release evidence runs after geometry in a separate
coordinated process so evidence allocation cannot perturb the serialized legacy
build. Separate committed producer and release closure projections record every
loaded dependency, the exact release commit and job JSON, and all nine model
artifact hashes rather than relying on ignored `build/` artifacts. The release
job predates whole-tree-state recording, so the projection truthfully verifies
every dependency byte at the commit without claiming an unrecorded clean tree.

## Deferred geometry work

The next geometry task is narrowly scoped: correct the accepted flat-bottom
missing-material relationship using this architecture, with fresh product
authority and its own before/after evidence. Horn, tube, resonator, bracket,
electronics, supports, hatch, hinge and fastener work remain separate.
