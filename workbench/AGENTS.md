# Workbench scope

Use `$speaker-enclosure-cad` for all work in this directory. The workbench is a
disposable feedback loop for localized features, sections, and fit coupons; it
is not released geometry.

1. Keep one small Build123d-MCP scratch session per active design when it
   shortens iteration. Restart after switching designs or an unexplained native
   failure.
2. A scratch export is evidence, not authority. Record the exact artifact path
   and hash in `feedback.md` and never carry a copied `#...` reference to a
   regenerated artifact.
3. At each meaningful checkpoint provide programmatic checks, a read-only
   Text-to-CAD Viewer link for the user, and a Snapshot or focused render the
   agent inspected.
4. Normally render one isometric overview and at most one question-specific
   detail. Do not drive the interactive Viewer through routine browser
   automation.
5. Promote an accepted direction into normal parameterized Python, then run the
   full relevant build and diagnostics through the serial `cad_runner` before
   calling it complete.
6. Use AgentCAD only when persistent A/B history or overlays materially help.
