# Archive

This folder preserves older CAD generators that produced useful historical
models but are no longer the current production candidate.

## `old_enclosure.py`

This is the latest 203 mm Sand Cube generator before the 8.5 in black-hole
enclosure experiment became the active design. It is kept intact so the old
cube, old horn preview, and old diagnostics can still be regenerated for
comparison.

Use:

```bash
uv run python scripts/generate_archive_old_enclosure.py
```

Outputs go to `build/archive/old_enclosure/`.
