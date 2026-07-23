# Archive and status index

This folder makes older work easy to set aside without deleting or relocating
it. The authoritative lifecycle registry remains `.cad-project/models.toml`.

“Archived” here means **outside the active working surface**, not safe to
delete. Several historical-looking experiments are imported by the active
leaf and must remain intact until the source is deliberately refactored.

See [status_index.md](status_index.md) for the practical classification.

## Rules

- Do not move experiment directories merely to make the tree look cleaner.
- Do not delete a historical experiment until import/dependency checks prove
  that no active or supporting owner uses it.
- Keep frozen releases under `releases/` unchanged.
- Keep rejected workbench candidates as chronological evidence; do not present
  them as alternatives in the canonical working-set links.
- When a model is genuinely promoted, renamed, moved, or archived, update
  `.cad-project/models.toml` in the same change and run
  `scripts/cad_review.py check-catalog`.
