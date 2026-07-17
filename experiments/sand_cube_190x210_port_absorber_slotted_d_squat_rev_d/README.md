# D-squat port absorber — Rev. D

This is a new, independently versioned design. It does not overwrite the
earlier 7.166 mm D-squat variant.

Rev. D preserves the 40 mm bore, 30 mm body, 5 mm local passage depth, removable
D bucket, 53.3298 cm³ common cavity, and separate 46/50 mm-OD socket adapters.
It changes the acoustic geometry after reproducing the Fable Rev. C viscous
analysis and updating the port to the enclosure-integrated 508.0816 mm route.

## Nominal result

| Quantity | Value |
|---|---:|
| Integrated-route model target | 338.25 Hz |
| Finished slots | 4 × 0.400 × 9.066233 mm |
| Physical depth | 5.000 mm |
| Total area | 14.368627 mm² |
| Common cavity | 53.329815 cm³ |
| Slit center | local z = 12.000 mm |
| Boss land above/below | 4.466884 mm each |
| Mid-end model | 337.18 Hz; Q 2.34; R/Z₀ 1.62 |
| End range 0.65–1.50 mm | 348.52–327.98 Hz |

The slot length minimizes the worst frequency error across the chosen inertial
end-correction bracket. It is not a claim that end correction is known.

The integrated service-straight body center is 276.8816 mm from the inlet. The
opening is 3 mm toward the inlet because the slot moved down within the body, so
its modeled path is 273.8816 mm. The 1-D pressure amplitude there is 0.993 of
the antinode value.

## Manufacturing

- The core prints vertically with 0.30 × 4.00 mm sacrificial pilots.
- The bucket prints inverted; adapters print plate-down.
- The calibration coupon includes one full-length 9.066 mm-class slot plus the
  shorter orientation/width tests.
- Finish the gap from the cavity side, measure it through the depth, then extend
  length symmetrically.
- The bucket requires a real gasket and positive retention.
- The adapters remain fit references, not a validated structural tower joint.

## Build

```sh
MPLCONFIGDIR=/tmp/mpl .venv/bin/python \
  experiments/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/generate_port_absorber_slotted_d_squat_rev_d.py
```

Outputs are written only to:

`build/sand_cube_190x210_port_absorber_slotted_d_squat_rev_d/`

The generated `diagnostics.json` contains the exact branch inputs, end cases,
conditional duct comparison, land dimensions, slot connections, bore checks,
and STEP round-trip results.

See the canonical
[engineering report](../sand_cube_190x210_port_absorber_slotted_d_squat/DEEP_RESEARCH_BRIEF.md)
and the separately preserved
[Fable Rev. C report](../sand_cube_190x210_port_absorber_slotted_d_squat/FABLE_REV_C_REPORT.md).
