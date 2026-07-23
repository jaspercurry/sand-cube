# Bass-reflex tube source manifest

Inventory date: 2026-07-22

## Dependency order

| Stage | Generator SHA-256 |
|---|---|
| `experiments/sand_cube_190x210_single_oval_port/generate_sand_cube_190x210_single_oval_port.py` | `0ebe233087fb8724e89254385e5f00e8f3a197fbb3bb9e202e97874c73c3e3a8` |
| `experiments/sand_cube_190x210_header_port/generate_sand_cube_190x210_header_port.py` | `c20df6ac1eb83616babdb844eb8f1f336725eed714101bebe58d7f0d98d2b5ab` |
| `experiments/sand_cube_190x210_serviceable_tower/generate_sand_cube_190x210_serviceable_tower.py` | `3ef3e25ba9d1811ca32bcab4d9457beaff3a38052375619f88edb1d1e3d43a7b` |
| `experiments/sand_cube_190x210_internal_squat_absorber/generate_sand_cube_190x210_internal_squat_absorber.py` | `b3a8fdb7276c6dcca4a6c777083cdda1c27e4e673e540c884712ff5650d888c1` |
| `experiments/sand_cube_190x210_internal_squat_absorber_flush/generate_sand_cube_190x210_internal_squat_absorber_flush.py` | `888fe48ad804c6ac49f5805d237dd7974b686cac1bc09eeec5e8ef6d049bb474` |
| `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners/generate_sand_cube_190x210_internal_squat_absorber_rear_corners.py` | `1b2fcd344726f192b37e9081b6e41588b797a1a35e3301600ba2dbe77455307d` |

These source files were already present in the clean baseline and remain
tracked in place.

## Reference evidence

| Local link | Repository path | SHA-256 |
|---|---|---|
| `links/tube_reference.step` | `workbench/designs/canonical_working_set/acoustics/bass_reflex_tube/reference_evidence/sand_cube_190x210_single_oval_port_internal_tube.step` | `5667fa455b81f8fc0f9a4645677a359f7b9072f0750eaff4f39a2099255fa19c` |
| `links/route_diagnostics.json` | `workbench/designs/canonical_working_set/acoustics/bass_reflex_tube/reference_evidence/diagnostics.json` | `dce0dcd3452ee8a98cea69073a52b3c3a299e42ec1a0e5bd716197cbf27af913` |

Catalog identity: `exp-190x210-rear-corners` (supporting), with the preceding
port/tower/absorber experiments retained as dependencies and studies.
