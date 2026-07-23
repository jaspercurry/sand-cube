# CAD feedback-loop rollout evidence

Integration base:
`7f2ee318b7aedbb3cb86a5cec16b49f30c28c5b3`.

Candidate:
`e9359c45f81946d5f63d950fdcca0e434cff690760efd5c2aa8188b8cc05edd2`.

## Architecture exercised

- The production generator remains the authority for geometry, all nine STEP
  exports, and STEP round-trip diagnostics.
- Static Viewer generation is a separate coordinated job that reads an
  already-published STEP and a sidecar accepted only through its verified
  content-addressed cache entry.
- The target verification adapter composes `fast`, explicit visual acceptance,
  `fit`, forced `release`, and independent-review workflow gates around one
  hash-bound candidate.
- Native reusable measurement semantics come from
  `cad_geometry_checks.native`; the top-level `cad_geometry_checks` package
  remains native-free.
- Fit and release import each artifact once per stage. Fit shares five imports
  across five contact checks and topology summaries. Release shares nine
  imports across the cumulative checks.
- Cache identity includes candidate, source, artifact, settings, producer
  schema, and tool identities. Release skips cache restoration and performs a
  forced regeneration.
- Visual acceptance is evidence only for visual completeness. Its record
  forbids measurable pixel claims and is checked against the exact candidate,
  hardware STEP, verified sidecar, static-review provenance, Snapshot
  provenance, and Snapshot hash.

## Successful supervised jobs

| Job | Purpose | Elapsed | Peak RSS | Result |
| --- | --- | ---: | ---: | --- |
| `20260723T211801-generate-sand-cube-190x210-single-oval-port-43ef802b42` | unchanged integration-base production baseline | 105.594 s | 885,719,040 B | 9 STEP, diagnostics, and 2 coupled Viewers |
| `20260723T213107-single-oval-port-production-separated-ad3d2212a1` | separated production | 88.353 s | 880,459,776 B | 9 STEP and diagnostics; no review output |
| `20260723T213359-single-oval-port-fast-e85fa9ff57` | initial fast binding | 0.520 s | 180,224 B | candidate and fast evidence |
| `20260723T213419-text-to-cad-artifacts-be29120844` | cold sidecar | 9.668 s | 757,661,696 B | cache publish |
| `20260723T213436-text-to-cad-artifacts-4fa88d2f25` | warm sidecar | 0.537 s | 131,072 B | verified cache hit |
| `20260723T213448-single-oval-port-static-review-a8bed49a2f` | separate static review | 8.653 s | 755,286,016 B | one import/tessellation |
| `20260723T213549-text-to-cad-artifacts-ee956b2ee4` | Snapshot visual smoke | 8.773 s | 4,684,562,432 B | inspected PNG and provenance |
| `20260723T213649-single-oval-port-fit-cold-33eadda207` | initial cold fit | 90.875 s | 598,753,280 B | cache publish |
| `20260723T213835-single-oval-port-fit-warm-9909e210d4` | initial warm fit | 0.513 s | 180,224 B | verified cache hit |
| `20260723T213851-single-oval-port-fit-invalidated-623a53ce10` | initial controlled invalidation | 93.849 s | not recorded here | new cache key |
| `20260723T214051-single-oval-port-release-forced-d431454332` | initial forced release | 133.940 s | 649,854,976 B | forced regeneration |
| `20260723T214724-geometry-checks-native-final-9474ce5793` | reusable native geometry fixtures | 5.578 s | 487,063,552 B | all fixture assertions passed |
| `20260723T215001-single-oval-port-fast-r4-3adc903ef9` | final candidate binding | 0.519 s | 180,224 B | same candidate |
| `20260723T215043-single-oval-port-fit-cold-r4-6e40d237a8` | final cold fit after source change | 90.398 s | 566,231,040 B | 89.636 s measurement; cache publish |
| `20260723T215219-single-oval-port-fit-warm-r4-8a75a72c81` | final warm fit | 0.508 s | 180,224 B | 0 s measurement; verified cache hit |
| `20260723T215228-single-oval-port-fit-invalidated-r4-94f3f94d2d` | final controlled invalidation | 89.418 s | 605,339,648 B | 88.592 s measurement; new key |
| `20260723T215415-single-oval-port-release-forced-r4-855f624367` | final forced release | 134.486 s | 685,195,264 B | 133.721 s measurement; cache bypass |

Every successful job reports its workspace removed, its owned process group
reaped, and no remaining owned PIDs. The all-nine release topology/import stage
is the exposed slow stage. No arbitrary performance threshold was introduced.

The final fit cold/warm cache key is
`73f2876c70d56a275659ef9c602493a1a718b2183563dbe400a17f2c608176fc`.
Changing the controlled identity from `controlled-source-v2` to
`controlled-source-v3` produced cache key
`2fe8253f81a45500aba6553fe4cbd4c7bf4839c179ab3efca096c86aaa107fb1`.
The forced release key was
`678479dde818eb81aa7462f8599720664a76ddbc1f467e1e1a63df1a80d72223`,
with status `forced_regeneration`, not `hit`.

## Expected and deliberately unsuccessful jobs

| Job | Elapsed | Expected failure | Publication and cleanup |
| --- | ---: | --- | --- |
| `20260723T213314-single-oval-port-fast-e93c26922c` | 0.516 s | output-directory argument was initially redirected by the runner; fixed by removing the reserved parameter name | 0 outputs; clean |
| `20260723T213524-text-to-cad-artifacts-f6565cdc30` | 2.033 s | Chromium was denied by the macOS sandbox; rerun with approved GUI isolation | 0 outputs; clean |
| `20260723T214317-single-oval-port-review-deliberate-failure-bc8516f4c7` | 4.568 s | diagnostics JSON deliberately supplied instead of a verified GLB | 0 outputs; production STEP and prior review preserved; clean |
| `20260723T214716-geometry-checks-native-final-9fbb89a9da` | 0.509 s | runner was mistakenly given an interpreter command instead of a Python entrypoint | 0 outputs; corrected job passed; clean |

The deliberate review failure left the hardware STEP at
`8f51fed279909389be6497c94b14c030963ef8ed8d0987dc7897d6de42501443`
and the successful review provenance at
`e7ada642a119c9d52a8f1ae027bd5f6a2b639107ede03b2434662aee1bf1bc2d`.

## Artifact comparison

The integration-base and separated-production STEP byte sizes are identical
for every one of the nine outputs. Raw SHA-256 values differ because Open
Cascade writes the export time into the STEP `FILE_NAME` header. Replacing
only the separated file's header timestamp with the recorded baseline
timestamp reconstructs the exact baseline SHA-256 for all nine files. Thus
every non-timestamp byte is identical. The per-file baseline and current
hashes are recorded in `baseline-step-sha256.txt` and the hash-bound release
evidence.

## Test and policy commands

- Pinned-environment doctor with the read-only Text-to-CAD overlay: passed.
- Full lightweight suite after the rollout: 169 tests and 19 subtests passed,
  model catalog passed, 57 CAD entrypoints passed, and Ruff passed.
- Focused rollout, geometry-check, cache, workflow, runner, and telemetry set:
  96 tests passed before the final visual-lineage addition; the rollout file
  then passed 7 tests and Ruff, and the final full suite included that test.
- Native reusable geometry fixture entrypoint through `cad_runner`: passed.
- Exact workflow-state hash validation: current through `release_passed`.
- `git diff --check`: passed before final review preparation.

Two focused-test attempts named nonexistent test files and collected no tests;
the corrected focused command is the 96-test result above. These were command
selection errors, not product failures.
