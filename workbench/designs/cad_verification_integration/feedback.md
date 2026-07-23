# CAD verification integration feedback

## 2026-07-22 — integration start

- Both source commits were verified as sibling commits based on `42db80c8c5575e8df00c1dddd76b27362f1d42fc`.
- Session 3 paths were absent. Session 2 collided only at `pyproject.toml`, `uv.lock`, `scripts/cad_review.py`, and `tests/test_cad_review.py`; current user versions were retained and the commit changes are being applied semantically.
- The catalog identifies `joint-coupon` as the scoped workbench proof. No catalog record or active production geometry will change.
- Initial doctor check passed CAD pins, MCP pin, and catalog consistency but found no Text-to-CAD checkout under this worktree's configured build path. An existing matching checkout will be reused if available; no download or upgrade is authorized.

## 2026-07-22 — integrated proof

- Reused the existing Python environment and pinned Text-to-CAD 0.3.9 checkout at commit `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`; no CAD runtime dependency was upgraded.
- Canonical lightweight gate: 66 tests and 9 subtests passed in 2.33 s; catalog check reported 10 primary models and 41 experiment families; 82 CAD entrypoints passed the safety policy; Ruff passed.
- Final coordinated profile jobs all exited zero, cleaned their workspaces, and left no orphans:
  - fast `20260723T002457-joint-coupon-fast-74dba6bd6b`: 0.517 s, peak RSS 180,224 bytes, 8 native-free results;
  - fit `20260723T002458-joint-coupon-fit-c12c52acb8`: 3.549 s, peak RSS 471,891,968 bytes, 25 cumulative results;
  - release `20260723T002502-joint-coupon-release-52e7f7edf4`: 3.049 s, peak RSS 490,782,720 bytes, 32 programmatic results and four post-export evidence results in the final 36-result packet.
- Sidecar job `20260723T002516-text-to-cad-artifacts-927192fe58` completed in 1.044 s. The two-view Snapshot batch `20260723T002517-text-to-cad-artifacts-6b87332718` completed in 2.584 s (1,524.786 ms reported by Snapshot) while reusing the one exact STEP/sidecar import.
- Assembly STEP SHA-256: `b0cc16b7046b3090507db97185979241ac19a1634088a707c32026a1a35230fc`; sidecar SHA-256: `4a223505a6e76c5f46d81110db65a2ea2d5aa2e65eb10976c500744aae28a98e`. Packet assembly independently reads the GLB container and requires its embedded `stepHash` to equal the current STEP hash.
- The isometric Snapshot shows two coherent rigid parts, four through-holes, and a uniform open seam. The YZ section at X=0 shows the tongue registered inside the groove with visible bilateral and tip clearance. No missing body, inversion, or section artifact was seen. Gasket placement and interference remain programmatic claims because the rigid assembly STEP intentionally excludes the separate gasket reference STEP.
- `cad_review verify packet` returned PASS for fast (8/8), fit (25/25), and release (36/36), with current source/input/artifact fingerprints. Negative CLI tests cover failed, malformed, stale, missing, profile-mismatched, and UNVERIFIED evidence.
- Exact Viewer link: `http://127.0.0.1:4179/?dir=%2FUsers%2Fjaspercurry%2F.codex%2Fworktrees%2Fe5bc%2FCAD+-+Enclosure%2Fbuild%2Fworkbench%2Fjoint_coupon&file=joint_coupon_assembly.step`. It targets the repository-enforced read-only server; no interactive Viewer automation was used.
- One superseded coordinator record, `20260723T002246-joint-coupon-fast-03c32eb96e`, failed before model execution because the reproduction command incorrectly supplied a Python binary where `cad-run` expects a script path. It produced no outputs, was not retried, and is not referenced by any packet.
- Remaining uncertainty: the coupon has not been physically printed, so material, process, and printer variation are not verified.
