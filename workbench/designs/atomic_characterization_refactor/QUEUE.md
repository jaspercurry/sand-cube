# Atomic characterization/refactor queue

Status: queued for execution in a separate Codex task.

- Verbatim prompt: `brief.md`
- Prompt SHA-256:
  `7cb5fad7514df1670ba9fd017cce0d44369564018515e3b4ec5be2c55d4bb96e`
- Approved input-landing commit:
  `2c94314b8cee90c3733991d48143375227a7d6b8`
- Integration branch: `codex/atomic-characterization-base`

The separate task must read `brief.md` in full and follow the repository
`speaker-enclosure-cad` skill. It must perform Phase A in its own clean
worktree and stop at the prompt's characterization checkpoint for user
approval. It must not silently proceed into Phase B, geometry synthesis, or
any later product-design phase.

This queue record does not authorize geometry work in the task that created
it.
