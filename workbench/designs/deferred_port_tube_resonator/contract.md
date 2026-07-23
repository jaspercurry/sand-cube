# Deferred bass-reflex tube and resonator contract

## Status and scope

This is an inventory and preservation checkpoint only. Do not change, rebuild,
retune, relocate, or promote the bass-reflex tube, tower, absorber/resonator,
enclosure, or baffle in this pass.

The future design task is to adapt the existing 40 mm bass-reflex tube and the
D-shaped squat resonator to the final accepted 190 x 210 enclosure and closure.
The enclosure/baffle fundamentals are not yet accepted, so packaging work is
deliberately deferred.

## Baselines to preserve

- Tube architecture: the 40 mm continuous-bore, separately printable internal
  tube, serviceable tower, rear-corner route, and outlet-flare lineage recorded
  in `source_manifest.md`.
- Current integrated resonator placement: the four-piece D-squat cartridge on
  the 56 mm rear-flush service straight. This currently uses the older Rev C
  resonator geometry.
- Latest resonator acoustic study: the independently versioned Rev D D-squat
  source and outputs. Rev D is research/calibration geometry and is explicitly
  not production-validated or yet integrated into the enclosure route.
- Current enclosure context: `workbench/designs/enclosure_baffle_recovery/`.
  None of its unpromoted STEP candidates is automatically the final packaging
  baseline.

## Must remain unchanged until resumption

- All existing experiment source and research notes.
- The distinction between current integrated Rev C geometry and the later Rev
  D acoustic calibration.
- A continuous, unobstructed 40 mm main airway.
- Separately printable tube/tower/resonator parts and service access.
- Existing artifact and source provenance; generated STEP files are evidence,
  while parameterized Python remains authoritative.

## Resume gate

Do not begin geometry work until the final accepted enclosure and baffle source
and exact STEP artifacts are identified. At resumption, record their paths,
hashes, net acoustic volume, wall/brace geometry, service opening, print
orientation, and available installation path before changing the tube.

## Future acceptance criteria

- Recalculate the bass-reflex alignment from the final measured net air volume,
  final airway, flare geometry, and one consistently defined physical/effective
  length model. Do not carry forward a nominal 39 Hz result without rerunning
  the calculation.
- Measure the bare printed port's unwanted resonance before treating the Rev D
  338.25 Hz target as authoritative. Preserve model uncertainty and do not
  claim the resonator is validated from CAD alone.
- Resolve the old integrated 7.166 mm slot against the Rev D 9.066 mm slot
  intentionally; do not silently mix them.
- Keep the 40 mm airway continuous with zero material intrusion through the
  tube, adapters, and resonator.
- Check enclosure, woofer, baffle, bracing, fill-path, rear-wall, floor, and
  installation-sweep clearances programmatically.
- Verify tube mounting, tower joint, resonator gasket/retention, print
  orientation, and assembly/service sequence.
- At each visible checkpoint provide deterministic checks, the read-only
  Text-to-CAD Viewer link, and only one isometric plus the one section/detail
  that answers the current packaging question. Do not operate the Viewer with
  browser automation for routine agent inspection.

## Known blockers

- The enclosure and baffle are not yet final.
- Rev D is not yet integrated into the enclosure tube.
- The bare-port resonance and final net acoustic volume have not been measured
  on the final printed assembly.
