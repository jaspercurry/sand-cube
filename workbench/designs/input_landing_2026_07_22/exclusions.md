# Deliberate exclusions

The following primary-checkout changes were reviewed and left behind. A path
ending in `/` means the entire untracked directory was excluded.

## Unrelated repository and toolchain changes

- `.agents/skills/speaker-enclosure-cad/SKILL.md`
- `.codex/config.toml`
- `AGENTS.md`
- `README.md`
- `archive/README.md`
- `cad_runner/cli.py`
- `cad_runner/coordinator.py`
- `docs/CAD_TROUBLESHOOTING.md`
- `docs/COMPACT_6IN_SPEAKER.md`
- `docs/ELECTRONICS_ENCLOSURE.md`
- `docs/LOCAL_CAD_VIEWING.md`
- `pyproject.toml`
- `uv.lock`
- `result.json`
- `scripts/cad_review.py`
- `scripts/check_cad_entrypoints.py`
- `scripts/generate_final_system_assembly.py`
- `scripts/render_f3d_previews.sh`
- `scripts/text_to_cad_artifacts.py`
- `scripts/view_model.sh`
- `scripts/audit_step.py`
- `scripts/diagnose_horn_bracket_stack.py`
- `tests/test_cad_review.py`
- `tests/test_cad_runner.py`
- `.github/dependabot.yml`

The dirty `.gitignore` and `.cad-project/models.toml` were not copied. Instead,
this landing reconstructs only the scoped ignore exceptions and selected
catalog records required by the selected payload. The dirty catalog's new
horn validators and three unrelated experiments are excluded.

## Unrelated experiment changes

- `experiments/jmlc_square_baffle/README.md`
- `experiments/max_black_hole_baffle/README.md`
- `experiments/sand_cube_190x210_header_port/README.md`
- `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_centered_captive_nut/README.md`
- `experiments/sand_cube_8_5_black_hole/README.md`
- `experiments/viscoelastic_test_molds/README.md`
- `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_le_cleach_front_15mm/`
- `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_parabolic_side_g1_corner_fill_curved_gasket/`
- `experiments/sand_cube_190x210_internal_squat_absorber_rear_corners_sculpted_front/`

## Unrelated workbench changes

- `workbench/README.md`
- `workbench/SESSION_PROMPT.md`
- `workbench/VERSIONS.md`
- `workbench/agentcad/`
- `workbench/designs/joint_coupon/build.py`
- `workbench/designs/joint_coupon/feedback.md`
- `workbench/designs/joint_coupon/model.py`
- `workbench/designs/joint_coupon/params.json`
- `workbench/designs/joint_coupon/agentcad_design.py`
- `workbench/designs/joint_coupon/agentcad_spec.json`
- `workbench/designs/joint_coupon/render_review.py`
- `workbench/diagnostics/`
- `workbench/tests/`

The untracked primary copy of
`workbench/designs/canonical_working_set/` was byte-equivalent to the clean
baseline and was therefore base-satisfied, not recopied. This landing changes
only its evidence portability, manifests, and links.

## Generated material

All ignored `build/` output remains excluded except the thirteen exact files
listed as `selected-promote` in `intake_manifest.csv`. No `__pycache__`,
virtual environment, Snapshot, GLB, PNG, log, or general build subtree is
included.
