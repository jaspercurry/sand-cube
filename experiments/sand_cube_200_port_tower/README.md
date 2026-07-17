# 200 mm Sand Cube Port Tower

This is an isolated derivative of the validated `FINAL_200_VARIANT`. It does
not replace the existing final enclosure. The generator imports the baseline
read-only, closes the passive-radiator rear opening, adds a sealed top receiver,
and fits a separately printable flared resonant-port tower.

## Selected alignment

The duct is a conventional bass-reflex Helmholtz neck, not a quarter-wave line.
A 43 Hz quarter-wave path would be about 2.0 m long. The final circular throat
area is 1,100 mm² (37.43 mm equivalent diameter); its exact length is solved
from the final OpenCascade-measured net volume after the base, E150HE-44 STEP,
GX16, binding posts, and in-box port envelope are subtracted.

The acoustic model uses Dayton Audio's official E150HE-44 series-coil data:

- [Dayton/Parts Express E150HE-44 specification sheet](https://www.parts-express.com/pedocs/specs/295-102--epique-e150he-44-spec-sheet.pdf)
- [Dayton Audio E150HE-44 product page](https://www.daytonaudio.com/product/1911/e150he-44-5-1-2-dvc-mmag-extended-range-subwoofer-4-ohms-per-coil)
- [Dayton/Parts Express E180HE-PR specification sheet](https://www.parts-express.com/pedocs/specs/295-114--epique-e180he-pr-spec-sheet.pdf)

The JSON diagnostics are the source of truth for final volume, tuning, port
velocity, excursion, line modes, clearances, and solid validity.

The validated generation measures 4.904 L net, solves a 334.51 mm physical
centerline (361.53 mm effective), and places the outlet 154.51 mm / 6.08 in
above the enclosure. The lumped model predicts F3 at 48.2 Hz. Peak modeled port
velocity is 15.27 m/s (Mach 0.045) at 25 W, 21.59 m/s (Mach 0.063) at 50 W,
30.53 m/s (Mach 0.089) at 100 W, and 43.18 m/s (Mach 0.126) at the driver's
200 W thermal rating.

## Geometry and manufacture

- Base envelope remains exactly 200 x 200 x 200 mm.
- Rear PR recess, service opening, and insert bores are restored to a solid
  14 mm rear cap. GX16 and both sand-fill paths remain unchanged.
- A solid receiver bridges the 2-3-2 mm top stack. The port cannot enter the
  sand void; a flat gasket seals the removable tower at the top surface.
- The tube is laterally centered at `x=0` and stays aft at `y=55.5` to clear
  the woofer motor. Its exact swept envelope locally clears the aft vertical
  center rail and horizontal waist rail; both rails retain both wall contacts.
- The binding posts move forward to `y=5` on a new rounded island connected to
  the existing top island, clearing the centered receiver.
- The tower is printed upright from its inlet flare. This keeps the long bore
  vertical and avoids the severe trapped support that an integral tower would
  create in the enclosure's rear-face-down print orientation.
- The centered DE250 support is an open-top, 6 mm-wall U cup molded directly
  into the tube. The driver drops into the cup from above and slides forward
  against a 4 mm, 100 mm-diameter mounting ring with a 42 mm acoustic opening
  and both B&C bolt patterns. The cup rim is rounded and the old offset plate
  and diagonal strut are gone. The supplied `objects/Compression
  DriverDE250.step` is the B&C DE250; no separate “BMC” component exists in the
  project.

## Generate

From the repository root:

```bash
.venv/bin/python experiments/sand_cube_200_port_tower/generate_sand_cube_200_port_tower.py
```

Outputs are written only to `build/sand_cube_200_port_tower/`:

- `sand_cube_200_port_tower_base.step`
- `sand_cube_200_port_tower.step`
- `sand_cube_200_port_tower_gasket.step`
- `sand_cube_200_port_tower_assembly.step`
- `sand_cube_200_port_tower_hardware_check.step`
- `diagnostics.json`
- `viewer/viewer/index.html` plus its static assets

## Known limits

This enclosure remains port-output-limited before the E150HE-44 reaches its
200 W thermal rating. The 25 W and 50 W cases are the useful continuous checks;
100 W is a short-term stress case, and the unfiltered 200 W result is included
to show why the thermal number is not an acoustic operating target. Use a
fourth-order 28-30 Hz high-pass. The long duct also has an audible-frequency
pipe mode, so cavity lining and the final woofer-to-horn crossover must be
validated on the physical prototype without placing damping inside the port.
