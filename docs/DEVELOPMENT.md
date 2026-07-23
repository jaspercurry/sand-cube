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
or UNVERIFIED evidence is nonzero. Verification is intentionally usable from a
minimal checkout containing only `cad_verification`, `scripts/cad_review.py`,
and `scripts/cad_verification_io.py`; it does not load project config or the CAD
runner.

Run the cataloged joint-coupon proof through its owner at
`workbench/designs/joint_coupon/build.py`: use `fast` for the analytic pass,
`fit` only when mating, clearance, interference, or section evidence matters,
and `release` for STEP round-trip plus Viewer/Snapshot handoff. The profile
composition is defined only in
[`cad_verification/policy.py`](../cad_verification/policy.py), and the packet
schema and execution-success rules are defined only in
[`cad_verification/model.py`](../cad_verification/model.py) and
[`cad_verification/validation.py`](../cad_verification/validation.py).
Repository command, URL, file, and coupon bindings live in
[`scripts/cad_verification_io.py`](../scripts/cad_verification_io.py) and
[`workbench/designs/joint_coupon/packet.py`](../workbench/designs/joint_coupon/packet.py).
The immutable pre-integration comparison fixture is documented under
`workbench/designs/joint_coupon/baseline/`; it compares measurements within
tolerance and does not claim byte-identical STEP exports.

## CAD job statistics

Completed, failed, queued, and running CAD jobs leave JSON records under the
configured artifact root. Summarize them without importing the CAD kernel:

```bash
.venv/bin/python scripts/cad_review.py stats
```

The report includes state and target counts, elapsed-time percentiles, time
consumed by completed and failed work, maximum peak RSS, recent and slow
targets, malformed or incomplete record counts, terminal success rate,
all-time and bounded-recent failed-time share, same-target-and-command failure
streaks, and one deterministic recommendation. Use `--json` for a stable
machine-readable report or `--limit N` to change the recent/slow list length.
Treat `stop-and-diagnose` as a retry stop for that exact target and command:
isolate the failure with a cheap fixture or focused diagnostic before
launching it again.

Coordinated workers automatically retain an unhandled Python exception's type,
message, and optional semantic phase in the job record. Diagnostic and
validator code may use `cad_runner.phase("semantic-name")` around a costly
boundary and raise `cad_runner.ContractRejection("stable.code", "measured
reason")` for an expected, identified geometry rejection. A signal, resource
kill, or external exit without an envelope remains explicitly less certain;
the runner does not guess from log text.

## Compaction-safe AI CAD iterations

Keep long-lived intent in `brief.md` and measurable acceptance in `contract.md`.
For a multi-step or expensive task, create a compact live state beside them:

```bash
.venv/bin/python scripts/cad_review.py workflow init \
  workbench/designs/ITERATION/state.json \
  --iteration-id ITERATION \
  --model-id MODEL \
  --objective "One-sentence objective" \
  --brief workbench/designs/ITERATION/brief.md \
  --contract workbench/designs/ITERATION/contract.md \
  --source path/to/owning_source.py \
  --open-question "The one question this candidate must answer" \
  --next-action "Run the native-free fast checks"
```

After compaction or handoff, use `workflow show STATE.json`. The resulting
resume card is the intended restart context; do not inject the long prompt
again unless the card reports stale hashes or leaves a material ambiguity.

Advance one gate at a time with `workflow advance`, supplying the expected
current stage, next stage, exact evidence files, and updated question/action.
Use `workflow gate --profile fit` before full fit and `--profile release` before
release. Fit remains blocked until visual smoke is accepted, and release
remains blocked until fit passes. After any authoritative source edit, use
`workflow revise` with the complete source list; that increments the revision
and invalidates the old evidence.
