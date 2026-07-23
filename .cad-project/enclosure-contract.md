# Enclosure project contract

- CAD units are millimeters.
- Parameterized Python source is authoritative. Files under `build/` are
  derived review artifacts.
- Identify the exact enclosure variant before applying dimensions. Do not
  apply the archived 203 mm Sand Cube dimensions to the 190 mm, 200 mm,
  190-by-210 mm, 8.5-inch, or compact variants.
- `.cad-project/models.toml` is the repository map for model identity, status,
  ownership, primary entrypoint, and output location. It does not override the
  owning source's dimensions or geometry.
- Read dimensions from the owning parameter module or generator and record
  them in the iteration contract. Update that source before changing geometry
  when a sourced hardware dimension changes.
- Keep bracing in a sand void point-like unless the active design contract
  explicitly establishes drainage and fill behavior. Closed ribs can trap sand
  or air.
- Preserve a freeform user brief verbatim under
  `workbench/designs/<iteration>/brief.md`; put interpreted acceptance criteria
  in `contract.md` and chronological review decisions in `feedback.md`.

The legacy `src/enclosure.py` model is the 203 mm enclosure with a 3 mm outer
skin, 12 mm sand void, and 3 mm inner skin. Those values are not repository-wide
defaults.
