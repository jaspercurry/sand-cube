# 160° rollback comparison contract

## Baseline

- Shared source: `workbench/designs/le_cleach_horn_190/model.py`
- Parameters:
  `workbench/designs/le_cleach_horn_190/variants/rollback_140/params.py`
- Artifact:
  `build/workbench/le_cleach_horn_190/variants/rollback_140/le_cleach_horn_190_rollback_140.step`
- Baseline terminal wall angle: 140°

## Candidate

Create a separately named 160° horn from the exact 2007 Le Cléac'h recurrence.
Do not overwrite or silently modify the 140° baseline.

## Constraints

- Terminal wall angle: 160° within numerical sampling tolerance
- Physical X/Y envelope: 190.0 ± 0.01 mm
- Acoustic axial length: 82.38213681735276 ± 0.001 mm
- Throat, wall, flange, spigot, and bolt geometry unchanged
- One valid solid after construction and after STEP round trip
- No uniform post-generation scaling
- Profile spline deviation below 0.003 mm
- No open boundaries, non-manifold edges, or self-interference

The solver may change the calibrated acoustic mouth input and Le Cléac'h
wavefront parameter `T` so the new terminal angle still satisfies the frozen
length and physical envelope.

## Review

- Preserve the 140° artifact
- Export a separately named 160° STEP
- Generate an exact artifact-reference Viewer link
- Inspect a direct 160° render and compare it with the 140° baseline
- Record numerical and visual findings chronologically
