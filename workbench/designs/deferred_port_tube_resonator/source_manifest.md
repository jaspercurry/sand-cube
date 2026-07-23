# Bass-reflex tube and resonator source manifest

Inventory date: 2026-07-22

Repository HEAD observed during inventory:
`42db80c8c5575e8df00c1dddd76b27362f1d42fc`

The generator files listed below already had uncommitted working-tree changes
when this package was created. They were preserved in place and were not reset,
copied, or edited for this inventory. The SHA-256 values identify the exact
working-tree contents that were reviewed.

## Current tube lineage, in dependency order

1. Acoustic/enclosure baseline:
   `experiments/sand_cube_190x210_single_oval_port/`
   - `generate_sand_cube_190x210_single_oval_port.py`
   - `README.md`
   - Generator SHA-256:
     `0ebe233087fb8724e89254385e5f00e8f3a197fbb3bb9e202e97874c73c3e3a8`
2. Modular header route:
   `experiments/sand_cube_190x210_header_port/`
   - `generate_sand_cube_190x210_header_port.py`
   - `README.md`
   - Generator SHA-256:
     `c20df6ac1eb83616babdb844eb8f1f336725eed714101bebe58d7f0d98d2b5ab`
3. Serviceable tower/cartridge:
   `experiments/sand_cube_190x210_serviceable_tower/`
   - `generate_sand_cube_190x210_serviceable_tower.py`
   - Generator SHA-256:
     `3ef3e25ba9d1811ca32bcab4d9457beaff3a38052375619f88edb1d1e3d43a7b`
4. First enclosure-integrated D-squat resonator route:
   `experiments/sand_cube_190x210_internal_squat_absorber/`
   - `generate_sand_cube_190x210_internal_squat_absorber.py`
   - `README.md`
   - Generator SHA-256:
     `b3a8fdb7276c6dcca4a6c777083cdda1c27e4e673e540c884712ff5650d888c1`
5. Rear-flush placement iteration:
   `experiments/sand_cube_190x210_internal_squat_absorber_flush/`
   - `generate_sand_cube_190x210_internal_squat_absorber_flush.py`
   - `README.md`
   - Generator SHA-256:
     `888fe48ad804c6ac49f5805d237dd7974b686cac1bc09eeec5e8ef6d049bb474`
6. Current rear-corner route/placement baseline:
   `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners/`
   - `generate_sand_cube_190x210_internal_squat_absorber_rear_corners.py`
   - `README.md`
   - Generator SHA-256:
     `1b2fcd344726f192b37e9081b6e41588b797a1a35e3301600ba2dbe77455307d`

The rear-corner generator is the latest tube-route owner in this chain. Its
diagnostics record a continuous 40 mm bore, a 56 mm absorber service straight,
a 526.406968 mm complete physical centerline length, a 553.828873 mm effective
length, and a calculated 39.208938 Hz alignment for that build. Those values
are historical inputs, not values to copy into the final closure without
remeasurement.

## Resonator source lineage

Foundational/removable absorber studies:

- `experiments/sand_cube_190x210_port_absorber_collar/`
  - `generate_port_absorber_collar.py`
  - `README.md`, `DESIGN_ANALYSIS.md`
  - Generator SHA-256:
    `d571da9902059ff1ca048deea2f407c68dda6c09a3cc0853f9d6b5d53186a848`
- `experiments/sand_cube_190x210_port_absorber_bucket/`
  - `generate_port_absorber_bucket.py`
  - `README.md`, `SCIENCE_AND_TUNING.md`
  - Generator SHA-256:
    `8bee0039aff82761f672bf7d076c4aa90b95dbaa8f8f27f2c288e4963f624528`
- `experiments/sand_cube_190x210_port_absorber_slotted_bucket/`
  - `generate_port_absorber_slotted_bucket.py`
  - `README.md`, `SCIENCE_AND_TUNING.md`
  - Generator SHA-256:
    `8b9e8247728338c2c3486d71fd234cf8c98cd40ed7104e2646a07fda83077a8b`

Current integrated mechanical source (Rev C lineage):

- `experiments/sand_cube_190x210_port_absorber_slotted_d_squat/`
  - `generate_port_absorber_slotted_d_squat.py`
    - SHA-256:
      `9bcb1a728add4fa1b306158da1e782cf9c8441275fcf7ccc90c092a6259fbf97`
  - `model.py`
    - SHA-256:
      `38204b0194edb46bb650cfe5c6f32450e55646c941bd397493e73a68f75f049b`
  - `duct.py`
    - SHA-256:
      `bf78e1a790b236646c4c96af1c6e63d2d8a8ec271316a8368c8271bec0723f03`
  - `robust.py`
    - SHA-256:
      `9bda9c976dac9a7030ad29c9cec2b4399c99aee74a782f11caa44229318ed9b7`
  - `verify.py`
    - SHA-256:
      `028a728c113d1315a517510adc0e911c8c86ca118b2d989d12d6c4faaa949092`
  - `README.md`, `DEEP_RESEARCH_BRIEF.md`, `FABLE_REV_C_REPORT.md`

Latest independently versioned acoustic/calibration source (Rev D):

- `experiments/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/`
  - `generate_port_absorber_slotted_d_squat_rev_d.py`
  - `README.md`
  - Generator SHA-256:
    `e7c320c4e1514f9459e82b94e6bba4a58877ff2591b3ed7d1e4c6fc5f18ba9f1`

The integrated enclosure code imports the Rev C generator, not Rev D. The
integrated artifact therefore uses the 334.7 Hz / 7.166388 mm-slot design. Rev
D instead assumes its own 508.081579 mm main-port length definition, targets
338.25 Hz, and uses four nominal 0.400 x 9.066233 mm finished slots. These
length definitions and vintages must be reconciled against the final measured
route before integration.

## Exact review artifacts

Current tube in the enclosure-closure lineage:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/sand_cube_190x210_single_oval_port_internal_tube.step`

- SHA-256:
  `5667fa455b81f8fc0f9a4645677a359f7b9072f0750eaff4f39a2099255fa19c`
- This is packaging/reference evidence, not the owning source.

Current integrated Rev C resonator placement:

`build/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_lightweight_coherent_closure/internal_d_squat_absorber_installed.step`

- SHA-256:
  `a16aeb1b440ef94a3cb208e4388eeac9c2acec238791fde4c33ebf0a3a4788ce`
- Four separately printable solids in the existing placement.

Latest Rev D resonator assembly reference:

`build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/port_absorber_d_squat_rev_d_assembly_finished_reference.step`

- SHA-256:
  `3ed5020cf53511f676ec3ed9a709d44a81e112f5b91fb1757dfbf09f4fcb33da`
- The corresponding `diagnostics.json` labels it
  “not production-validated.”

Latest Rev D print-layout reference:

`build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/port_absorber_d_squat_rev_d_print_layout.step`

- SHA-256:
  `5936001348ce7d146519a8836507d6800b703cce71f0a3d808f2df20f818d76e`

## Supporting diagnostics

- Tube/placement diagnostics:
  `build/sand_cube_190x210_internal_squat_absorber_rear_corners/diagnostics.json`
- Rev D acoustic, geometry, manufacturing, and STEP checks:
  `build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/diagnostics.json`
- Verified Rev D response tables:
  `build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/verified_duct_response.csv`
  and
  `build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/verified_pressure_profile.csv`

## Preservation rule

Do not consolidate these experiments by deleting ancestors or copying their
code into the enclosure generator. Their explicit import lineage is valuable
design history. When work resumes, create one new integration iteration that
imports the accepted owners and adapts only the geometry required by the final
enclosure.
