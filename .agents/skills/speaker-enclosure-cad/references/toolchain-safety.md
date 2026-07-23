# Toolchain and resource safety

## Source of configuration

Read `.cad-project/project.toml` for versions, paths, units, and concurrency.
Do not copy pins into another script or instruction file. Run:

```bash
.venv/bin/python scripts/cad_review.py doctor
```

Use automatic update awareness, not automatic production upgrades. Report a
new Build123d, OCP, Build123d-MCP, or Text-to-CAD release; update pins only in a
separate tested change after the CAD validation suite passes.

## Native CAD jobs

The current `cad_runner` uses one machine-wide exclusive lock, so heavy CAD
jobs are serial. Every substantial generator, preview builder, sidecar,
Snapshot, and native diagnostic must enter through the coordinator before
importing Build123d, OCP, CadQuery, VTK, or related libraries.

- Run one model in one fresh spawned process.
- Keep the coordinator import-clean and native-CAD-free.
- Never use `fork`, `preexec_fn`, or a multiprocessing fork context after CAD
  or threaded libraries initialize.
- Never blindly retry SIGSEGV, OOM, forced termination, or an unknown native
  crash. Record it and investigate; retry only a named transient error once.
- Clean only the current job's workspace. Generated job files belong in
  `build/`; reuse the stable project `.venv`.
- For an external diagnostic, run
  `.venv/bin/python -m cad_runner run --repo . -- /absolute/script.py`.

For substantial jobs report job ID, worker PID, elapsed time, current/peak RSS,
exit status, outputs, cleanup, and absence of owned orphan processes.

## Viewer and artifacts

Start Viewer only through `scripts/start_text_to_cad_viewer.sh` or
`scripts/cad_review.py viewer`. The generated overlay disables the Viewer-side
STEP-artifact endpoint and refuses to reuse a server reporting generation
enabled. Sidecar and Snapshot operations go through `scripts/cad_review.py`,
which delegates native work to `cad_runner`.

Keep the upstream Text-to-CAD runtime isolated under the ignored `build/`
checkout. Do not install its unpinned Build123d or `cadquery-ocp` dependencies
into this project environment.

## MCP

The project-scoped Build123d-MCP server may own one persistent in-memory scratch
session. It is useful for local experiments and focused rendering and does not
need another `cad_runner` wrapper because the MCP host owns its lifecycle. It
does not replace parameterized source, production diagnostics, or exported
artifact review.
