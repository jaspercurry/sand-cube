# D-squat resonator source manifest

Inventory date: 2026-07-22

## Rev C integrated mechanical source

| File | SHA-256 |
|---|---|
| `generate_port_absorber_slotted_d_squat.py` | `9bcb1a728add4fa1b306158da1e782cf9c8441275fcf7ccc90c092a6259fbf97` |
| `model.py` | `38204b0194edb46bb650cfe5c6f32450e55646c941bd397493e73a68f75f049b` |
| `duct.py` | `bf78e1a790b236646c4c96af1c6e63d2d8a8ec271316a8368c8271bec0723f03` |
| `robust.py` | `9bda9c976dac9a7030ad29c9cec2b4399c99aee74a782f11caa44229318ed9b7` |
| `verify.py` | `028a728c113d1315a517510adc0e911c8c86ca118b2d989d12d6c4faaa949092` |

All live under
`experiments/sand_cube_190x210_port_absorber_slotted_d_squat/`.

## Rev D source

`experiments/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/generate_port_absorber_slotted_d_squat_rev_d.py`

SHA-256:
`e7c320c4e1514f9459e82b94e6bba4a58877ff2591b3ed7d1e4c6fc5f18ba9f1`

Rev D imports the Rev C generator, `model.py`, and `duct.py`; it is not a
standalone copied implementation.

## Reference evidence

| Local link | Repository path | SHA-256 |
|---|---|---|
| `links/integrated_rev_c_placement.step` | `workbench/designs/canonical_working_set/acoustics/d_squat_resonator/reference_evidence/internal_d_squat_absorber_installed.step` | `a16aeb1b440ef94a3cb208e4388eeac9c2acec238791fde4c33ebf0a3a4788ce` |
| `links/rev_d_assembly.step` | `workbench/designs/canonical_working_set/acoustics/d_squat_resonator/reference_evidence/port_absorber_d_squat_rev_d_assembly_finished_reference.step` | `3ed5020cf53511f676ec3ed9a709d44a81e112f5b91fb1757dfbf09f4fcb33da` |
| `links/rev_d_print_layout.step` | `workbench/designs/canonical_working_set/acoustics/d_squat_resonator/reference_evidence/port_absorber_d_squat_rev_d_print_layout.step` | `5936001348ce7d146519a8836507d6800b703cce71f0a3d808f2df20f818d76e` |
| `links/rev_d_diagnostics.json` | `workbench/designs/canonical_working_set/acoustics/d_squat_resonator/reference_evidence/diagnostics.json` | `b2486dd92bda832be28b2d1e0b54666c06e0641924a2231283b8c37717a28c01` |

Catalog identities: `exp-190x210-port-absorber-d-squat` and
`exp-190x210-port-absorber-d-squat-rev-d`, both studies.
