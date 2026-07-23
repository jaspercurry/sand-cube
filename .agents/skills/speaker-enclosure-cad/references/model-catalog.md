# Model catalog

`.cad-project/models.toml` is the repository's navigation and lifecycle index.
It answers which model is current, where its authoritative source lives, how it
is built or validated, and where its generated output belongs. It does not
duplicate geometry parameters and never outranks the owning Python source.

## Use it

List the short primary-model map before choosing a baseline:

```bash
.venv/bin/python scripts/cad_review.py models
```

Use `models --experiments` for all experiment families, `models --all` for both
sets, and `scripts/model_catalog.py show <id>` for one complete record. Run:

```bash
.venv/bin/python scripts/cad_review.py check-catalog
```

after any catalog edit and before completing model-topology or lifecycle work.
`cad_review.py doctor` includes the same check.

## Update boundary

Update the catalog in the same change when any of these happens:

- a primary model or immediate `experiments/` family is added or removed;
- a model or experiment is renamed or moved;
- a primary model changes owner, parameters, build entrypoint, validator, or
  output location;
- work is promoted from experiment to stable source;
- a design becomes the active development baseline, a frozen release, or an
  archive.

Do not edit the catalog merely because a parameter value or internal helper
changed. Those facts belong in source and the iteration contract.

## Meanings

Primary model states are `stable`, `development`, `released`, `workbench`, and
`archived`. Experiment states are `active`, `promoted-support`, `supporting`,
`study`, and `historical`:

- `active` is the experiment currently being iterated;
- `promoted-support` still implements a stable API and therefore must not be
  casually deleted;
- `supporting` is an ancestor or base used by current work;
- `study` is available research without a current production claim;
- `historical` is superseded but retained for comparison or provenance.

Keep IDs stable when paths or display names change. Generated output paths may
be absent, but every recorded source, entrypoint, parameter, validator, release,
and workbench path must exist. The checker also compares the experiment list
with every immediate directory under `experiments/`, making uncataloged work a
deterministic failure instead of a memory-dependent convention.
