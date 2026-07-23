# CAD visual review

## Evidence channels

### Programmatic geometry

Use kernel queries as the authority for validity, dimensions, clearances,
interference, topology, alignment, wall thickness, and contract acceptance.
Never infer a measurable fact from pixels when geometry can answer it. Convert
visual concerns affecting fit or function into deterministic checks before
claiming validation.

### Human review

Use the repository's read-only Text-to-CAD Viewer for exported STEP/STP:

```bash
.venv/bin/python scripts/cad_review.py sidecar build/path/model.step --kind part
bash scripts/start_text_to_cad_viewer.sh --json
.venv/bin/python scripts/cad_review.py link build/path/model.step \
  --viewer-url 'http://127.0.0.1:PORT/?dir=...'
```

Use `--kind assembly` for an assembly STEP. Return the exact generated link.
Do not invoke the upstream Viewer launcher directly: the repository launcher
creates a read-only overlay and refuses to reuse a server that can generate
artifacts.

Do not routinely drive the Viewer through browser automation. It is the user's
interactive channel for rotation, clipping, visibility, selection, and copied
artifact-local references. Browser control is a documented fallback only for
testing Viewer behavior that cannot be verified through the artifact, sidecar,
Snapshot, or direct renderer; record why it was required.

### Agent visual review

Use Text-to-CAD Snapshot for an exported production STEP. Render the exact STEP
and topology sidecar provided to the Viewer. Import or tessellate that artifact
once, then reuse it across the normal overview and question-specific camera:

```bash
.venv/bin/python scripts/cad_review.py snapshot \
  --job build/workbench/iteration/snapshot-job.json
```

Use Build123d-MCP `render_view()` only while scratch geometry remains in memory
before a current production STEP exists. Once reviewing an exported production
STEP, use the repository's coordinated focused renderer when Snapshot cannot
express the required section, clip, highlight, camera, isolated feature, or
diagnostic view clearly. Do not import a production STEP into MCP merely to
render it. Snapshot may use headless Chromium internally; invoke its
deterministic command rather than operating the Viewer.

Normally produce one isometric overview and at most one question-specific
section, clip, orthographic, or detail view. Reuse one imported or tessellated
artifact across cameras. State which renderer produced each image and why.

## Artifact-local references

Record every copied `#...` reference with:

- exact artifact path;
- STEP SHA-256;
- copied reference;
- semantic feature description;
- requested change;
- geometry that must remain unchanged.

The token is valid only for that artifact hash. Never retain it as a durable
Build123d face or edge selector. Translate it into semantic source geometry,
named datums, dimensional constraints, or robust geometric predicates. After
regeneration, provide a new link and rediscover a reference only if needed.

A browser screenshot does not replace a direct agent render when one is
reasonably available. An agent render does not replace the interactive link
needed for a completed human-review checkpoint, and neither visual channel
replaces deterministic geometry checks.
