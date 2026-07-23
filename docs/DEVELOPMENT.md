# Lightweight development checks

The repository keeps runtime CAD pins and paths in
`.cad-project/project.toml`, Python package requirements in `pyproject.toml`,
the Python version in `.python-version`, and exact resolved packages in
`uv.lock`. Do not copy those versions into setup scripts or CI.

Create or update the project environment, including the test and lint tools,
with one locked command:

```bash
uv sync --locked --group dev
```

Run every native-CAD-free development check with one command:

```bash
uv run --locked --group dev python scripts/check_lightweight.py
```

That command runs the unit tests, model-catalog consistency check, CAD
entrypoint safety policy, and Ruff over the maintained statistics,
review/catalog/check tooling, and their tests. Geometry entrypoints are covered
by the dedicated safety policy; they are not pulled into this infrastructure
lint baseline. The suite does not run an enclosure generator, load a native CAD
library, or write generated geometry. The lightweight GitHub Actions workflow
calls the same script.

## Staged CAD verification

The single profile, check-cost, and evidence-channel policy lives in
[`cad_verification/policy.py`](../cad_verification/policy.py). Validate a design
contract and inspect its composed requirement set before CAD work:

```bash
.venv/bin/python scripts/cad_review.py verify contract CONTRACT.json --profile fast
```

Validate a completed packet, including current artifact/source/input hashes,
with `verify packet CONTRACT.json PACKET.json --profile PROFILE`. Packet success
means every requirement selected by that profile is present and PASS; missing
or UNVERIFIED evidence is nonzero. The cataloged joint-coupon proof under
`workbench/designs/joint_coupon/` demonstrates the repository adapter without
coupling the portable package to Build123d or an enclosure model.

## CAD job statistics

Completed, failed, queued, and running CAD jobs leave JSON records under the
configured artifact root. Summarize them without importing the CAD kernel:

```bash
.venv/bin/python scripts/cad_review.py stats
```

The report includes state and target counts, elapsed-time percentiles, time
consumed by completed and failed work, maximum peak RSS, recent and slow
targets, and malformed or incomplete record counts. Use `--json` for a stable
machine-readable report or `--limit N` to change the recent/slow list length.
