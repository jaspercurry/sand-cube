# Proposed module tree and ownership

Status: partially implemented. `src/enclosure_family/datums.py` now owns the
verified coordinate-contract pilot; every other module below remains proposed.
The atom facts and readiness states remain authoritative in
`atomic_manifest.json`.

```text
src/enclosure_family/
├── parameters.py
├── datums.py
├── primitives.py
├── measurements.py
├── validation.py
├── print_contracts.py
├── variant_r/
│   ├── parameters.py
│   ├── service_opening.py
│   ├── seam.py
│   ├── bottom_ownership.py
│   ├── gasket.py
│   ├── bucket.py
│   ├── baffle.py
│   ├── assembly.py
│   ├── validate.py
│   └── export.py
└── variant_i/
    ├── parameters.py
    ├── integral_body.py
    ├── open_bottom.py
    ├── hatch_interface.py
    ├── assembly.py
    ├── validate.py
    └── export.py
```

Thin cataloged entrypoints would call the two independent `assembly.py`
owners. They would not import one another and would not share a flag-driven
generator.

## Family boundary

The family layer may own units, named datums, explicitly accepted 190x210
dimensions, pure exterior/profile primitives, neutral measurements and
validation predicates, and print-orientation metadata. Geometry enters this
layer only after a semantic and numerical equivalence proof across variants.

The current 2/3/2 wall stack must not be merged with legacy 203 mm 3/12/3
parameters by name. Fill routing and braces require shared upstream primitives
plus explicit variant terminations/composition; they are not presently proven
as identical complete features.

## Variant R boundary

Variant R owns the service cut, front bulkhead/gasket support, sculpted
left/right/top seam, lower material ownership, separate baffle, gasket
relationship, future hinge/fastener interfaces and both print contracts. Its
bucket and baffle validator must measure complementary occupancy, gap/overlap,
corner seal, fill clearance, driver opening, protected sections and independent
STEP round-trips.

## Variant I boundary

Variant I owns one monolithic front/body composition, the open bottom, future
hatch boundary and open-bottom-down print contract. It branches from a neutral
body before any removable partition. No removable gap, land, nut slot,
fastener, hinge or service-opening builder may be imported and then suppressed.

## Verification and evidence boundary

Geometry builders return shapes and deterministic metadata. Measurement and
validation are pure consumers. Export is a separate adapter. Entry points are
thin and safe to import. `.cad-project/models.toml` remains the only model
registry.

Each variant eventually needs:

- one independent model identity and owner;
- one parameter source;
- one generator/entrypoint;
- one validator;
- one output root;
- fast analytic checks;
- coordinated fit/section checks; and
- release-only STEP round-trip plus Viewer/Snapshot evidence.

## Proposed first pilot

`family.coordinate_contract` is the recommended first pilot because it is
metadata-only, exact and broadly consumed. It can consolidate units, axis
polarity and named planes without touching a Boolean.

Preconditions:

1. explicit user approval to pass the checkpoint;
2. a deliberate decision to repair the current source baseline or select a
   different reproducible Python owner; and
3. no geometry extraction until that baseline is green.

The next geometry pilot should be chosen only after the baseline decision.
`R.front_bulkhead_gasket_support` is a useful later candidate because it has a
clear owner and strong section invariants, but it is currently blocked by the
ancestor build failure.

## Pilot result

The family coordinate contract now has one native-free immutable owner for
units, the 190x210x190 envelope, the +10 mm Y center, named planes, and axis
polarity. Existing 190x210 source consumers use that datum owner. The extraction
did not add a model, generator, Boolean, or variant flag, so the catalog remains
unchanged.
