from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from cad_runner.coordinator import (
    JobSupervisor,
    ResourceLimits,
    owned_process_group_pids,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def wait_for(path: Path, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {path}")


def pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


class CadRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cad-runner-test-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "build").mkdir()
        self.lock_path = self.root / "global" / "heavy-worker.lock"
        self.workspace_root = self.repo / "build" / ".jobs"
        self.state_root = self.repo / "build" / "states"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def worker(self, name: str, body: str) -> Path:
        path = self.repo / name
        path.write_text(
            "from __future__ import annotations\n"
            "def main():\n"
            + "".join(f"    {line}\n" for line in body.splitlines())
            + "if __name__ == '__main__':\n"
            "    main()\n",
            encoding="utf-8",
        )
        return path

    def supervisor(self, **limit_overrides) -> JobSupervisor:
        values = {
            "warning_rss_bytes": 512 * 1024 * 1024,
            "hard_limit_rss_bytes": 1024 * 1024 * 1024,
            "termination_grace_seconds": 0.5,
            "poll_interval_seconds": 0.02,
        }
        values.update(limit_overrides)
        return JobSupervisor(
            self.repo,
            limits=ResourceLimits(**values),
            lock_path=self.lock_path,
            workspace_root=self.workspace_root,
            state_root=self.state_root,
        )

    def test_success_failure_and_cancellation_clean_temporary_workspaces(self) -> None:
        success = self.supervisor().run(
            self.worker("success.py", "return None"), name="success"
        )
        self.assertEqual(success.state, "completed")
        self.assertTrue(success.cleanup["workspace_removed"])
        self.assertFalse(Path(success.cleanup["workspace"]).exists())

        failure = self.supervisor().run(
            self.worker("failure.py", "raise RuntimeError('expected failure')"),
            name="failure",
        )
        self.assertEqual(failure.state, "failed")
        self.assertEqual(failure.failure_kind, "python_exception")
        self.assertEqual(
            failure.failure_details["exception_type"],
            "builtins.RuntimeError",
        )
        self.assertEqual(failure.failure_details["message"], "expected failure")
        self.assertTrue(failure.cleanup["workspace_removed"])
        self.assertFalse(Path(failure.cleanup["workspace"]).exists())

        running = self.root / "cancel-running"
        cancelled_worker = self.worker(
            "cancelled.py",
            "from pathlib import Path\n"
            f"Path({str(running)!r}).write_text('running')\n"
            "import time\n"
            "time.sleep(30)",
        )
        cancel_event = threading.Event()
        result_holder = []
        thread = threading.Thread(
            target=lambda: result_holder.append(
                self.supervisor().run(
                    cancelled_worker,
                    name="cancelled",
                    cancel_event=cancel_event,
                )
            )
        )
        thread.start()
        wait_for(running)
        cancel_event.set()
        thread.join(timeout=8)
        self.assertFalse(thread.is_alive())
        cancelled = result_holder[0]
        self.assertEqual(cancelled.state, "cancelled")
        self.assertTrue(cancelled.cleanup["workspace_removed"])
        self.assertEqual(
            cancelled.cleanup["owned_process_group"]["remaining_owned_pids"], []
        )

    def test_failure_envelope_distinguishes_phase_and_contract_rejection(
        self,
    ) -> None:
        phased = self.supervisor().run(
            self.worker(
                "phased.py",
                "from cad_runner import phase\n"
                "with phase('overlap-check'):\n"
                "    raise AttributeError('empty result has no solids')",
            ),
            name="phased-failure",
        )
        self.assertEqual(phased.failure_kind, "python_exception")
        self.assertEqual(phased.failure_details["phase"], "overlap-check")
        self.assertEqual(
            phased.failure_details["exception_type"],
            "builtins.AttributeError",
        )
        self.assertIn("during overlap-check", phased.failure_message)

        rejected = self.supervisor().run(
            self.worker(
                "rejected.py",
                "from cad_runner import ContractRejection\n"
                "raise ContractRejection("
                "'fit.interference', 'unexpected overlap is 2 mm^3')",
            ),
            name="contract-rejection",
        )
        self.assertEqual(rejected.failure_kind, "contract_rejection")
        self.assertEqual(rejected.failure_details["code"], "fit.interference")
        self.assertIn("[fit.interference]", rejected.failure_message)

    def test_successful_worker_cannot_spoof_a_failed_result(self) -> None:
        result = self.supervisor().run(
            self.worker(
                "spoof.py",
                "import os\n"
                "from pathlib import Path\n"
                "from cad_runner.telemetry import write_failure_envelope\n"
                "write_failure_envelope("
                "Path(os.environ['CAD_JOB_FAILURE_PATH']), "
                "RuntimeError('spoofed failure'))",
            ),
            name="successful-spoof",
        )

        self.assertEqual(result.state, "completed")
        self.assertIsNone(result.failure_kind)
        self.assertIsNone(result.failure_details)
        self.assertIn(
            "ignored worker failure envelope after successful exit",
            result.warnings,
        )

    def test_failure_telemetry_never_masks_the_original_exception(self) -> None:
        result = self.supervisor().run(
            self.worker(
                "unprintable.py",
                "class OriginalFailure(RuntimeError):\n"
                "    def __str__(self):\n"
                "        raise RuntimeError('stringification failed')\n"
                "raise OriginalFailure()",
            ),
            name="unprintable-failure",
        )

        self.assertEqual(result.state, "failed")
        self.assertEqual(result.failure_kind, "worker_exit")
        self.assertIsNone(result.failure_details)
        log = Path(result.log_path).read_text(encoding="utf-8")
        self.assertIn("OriginalFailure", log)

    def test_child_process_is_reaped(self) -> None:
        result = self.supervisor().run(
            self.worker("reaped.py", "return None"), name="reaped"
        )
        self.assertEqual(result.state, "completed")
        self.assertIsNotNone(result.worker_pid)
        self.assertFalse(pid_exists(result.worker_pid))
        self.assertEqual(owned_process_group_pids(result.process_group_id), [])
        self.assertTrue(result.cleanup["owned_process_group"]["reaped"])

    def test_native_crash_is_not_retried(self) -> None:
        counter = self.root / "crash-count"
        worker = self.worker(
            "crash.py",
            "from pathlib import Path\n"
            f"counter = Path({str(counter)!r})\n"
            "counter.write_text(counter.read_text() + 'x' if counter.exists() else 'x')\n"
            "import os, signal\n"
            "os.kill(os.getpid(), signal.SIGSEGV)",
        )
        result = self.supervisor().run(worker, name="native-crash")
        self.assertEqual(result.state, "failed")
        self.assertEqual(result.failure_kind, "native_or_forced_termination")
        self.assertIsNone(result.failure_details)
        self.assertIn("no retry", result.failure_message)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(counter.read_text(), "x")

    def test_outputs_are_hidden_until_atomic_publication(self) -> None:
        final = self.repo / "build" / "artifact.step"
        final.write_text("old-valid", encoding="utf-8")
        staged = self.root / "staged-ready"
        worker = self.worker(
            "atomic.py",
            "import os\n"
            "from pathlib import Path\n"
            "target = Path(os.environ['CAD_JOB_STAGE_ROOT']) / 'build/artifact.step'\n"
            "target.parent.mkdir(parents=True, exist_ok=True)\n"
            "target.write_text('partial')\n"
            f"Path({str(staged)!r}).write_text('ready')\n"
            "import time\n"
            "time.sleep(0.4)\n"
            "target.write_text('new-valid')",
        )
        results = []
        thread = threading.Thread(
            target=lambda: results.append(
                self.supervisor().run(worker, name="atomic-output")
            )
        )
        thread.start()
        wait_for(staged)
        self.assertEqual(final.read_text(), "old-valid")
        thread.join(timeout=8)
        self.assertFalse(thread.is_alive())
        result = results[0]
        self.assertEqual(result.state, "completed")
        self.assertEqual(final.read_text(), "new-valid")
        self.assertEqual(result.final_outputs[0]["publication"], "atomic_replace")

    def test_external_ad_hoc_entrypoint_uses_the_same_atomic_staging(self) -> None:
        external = self.root / "external_cad_diagnostic.py"
        final_dir = self.repo / "build" / "external-diagnostic"
        external.write_text(
            "from pathlib import Path\n"
            f"OUT = Path({str(final_dir)!r})\n"
            "def main():\n"
            "    OUT.mkdir(parents=True, exist_ok=True)\n"
            "    (OUT / 'result.txt').write_text('valid')\n"
            "if __name__ == '__main__':\n"
            "    main()\n",
            encoding="utf-8",
        )
        result = self.supervisor().run(external, name="external-diagnostic")
        self.assertEqual(result.state, "completed")
        self.assertEqual((final_dir / "result.txt").read_text(), "valid")
        self.assertEqual(len(result.final_outputs), 1)
        self.assertTrue(result.cleanup["workspace_removed"])

    def test_resource_limit_is_clear_and_leaves_no_orphan(self) -> None:
        worker = self.worker(
            "memory.py",
            "payload = bytearray(32 * 1024 * 1024)\n"
            "import time\n"
            "time.sleep(30)\n"
            "return len(payload)",
        )
        result = self.supervisor(
            warning_rss_bytes=512 * 1024,
            hard_limit_rss_bytes=1024 * 1024,
        ).run(worker, name="memory-limit")
        self.assertEqual(result.state, "failed")
        self.assertEqual(result.failure_kind, "resource_limit")
        self.assertIn("hard RSS limit", result.failure_message)
        self.assertGreater(result.peak_rss_bytes, 1024 * 1024)
        self.assertEqual(
            result.cleanup["owned_process_group"]["remaining_owned_pids"], []
        )
        self.assertFalse(pid_exists(result.worker_pid))

    def test_worker_spawn_has_no_unsafe_fork_options(self) -> None:
        source = (PROJECT_ROOT / "cad_runner" / "coordinator.py").read_text()
        tree = ast.parse(source)
        popen_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "Popen"
        ]
        self.assertEqual(len(popen_calls), 1)
        keywords = {keyword.arg: keyword.value for keyword in popen_calls[0].keywords}
        self.assertNotIn("preexec_fn", keywords)
        self.assertIsInstance(keywords["start_new_session"], ast.Constant)
        self.assertTrue(keywords["start_new_session"].value)
        entrypoint = (PROJECT_ROOT / "cad_runner" / "entrypoint.py").read_text()
        self.assertNotIn("os.fork(", entrypoint)
        imported_modules = {
            node.names[0].name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import) and node.names
        } | {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertNotIn("multiprocessing", imported_modules)

        fake_process = object()
        with mock.patch(
            "cad_runner.coordinator.subprocess.Popen", return_value=fake_process
        ) as popen:
            with (self.root / "log").open("wb") as log_stream:
                returned = self.supervisor()._spawn_worker(
                    [sys.executable, "worker.py"],
                    environment=os.environ,
                    log_stream=log_stream,
                )
        self.assertIs(returned, fake_process)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertNotIn("preexec_fn", popen.call_args.kwargs)

    def test_second_interprocess_worker_queues_until_first_exits(self) -> None:
        first_started = self.root / "first-started"
        second_started = self.root / "second-started"
        release = self.root / "release-first"
        first_worker = self.worker(
            "first.py",
            "from pathlib import Path\n"
            f"Path({str(first_started)!r}).write_text('started')\n"
            f"release = Path({str(release)!r})\n"
            "import time\n"
            "while not release.exists(): time.sleep(0.02)",
        )
        second_worker = self.worker(
            "second.py",
            "from pathlib import Path\n"
            f"Path({str(second_started)!r}).write_text('started')",
        )
        environment = os.environ.copy()
        environment["CAD_GLOBAL_RUNTIME_DIR"] = str(self.root / "global")
        environment["PYTHONPATH"] = (
            str(PROJECT_ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
        )

        def command(script: Path, name: str) -> list[str]:
            return [
                sys.executable,
                "-m",
                "cad_runner",
                "run",
                "--repo",
                str(self.repo),
                "--name",
                name,
                "--poll-seconds",
                "0.02",
                "--grace-seconds",
                "0.5",
                "--",
                str(script),
            ]

        first = subprocess.Popen(
            command(first_worker, "first"),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        second = None
        try:
            wait_for(first_started)
            second = subprocess.Popen(
                command(second_worker, "second"),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            time.sleep(0.3)
            self.assertFalse(second_started.exists())
            queued_states = [
                json.loads(path.read_text())
                for path in (self.repo / "build" / "cad-jobs").glob("*.json")
            ]
            self.assertTrue(
                any(
                    state.get("name") == "second" and state.get("state") == "queued"
                    for state in queued_states
                )
            )
            release.write_text("go")
            first_output, _ = first.communicate(timeout=8)
            second_output, _ = second.communicate(timeout=8)
            self.assertEqual(first.returncode, 0, first_output)
            self.assertEqual(second.returncode, 0, second_output)
            self.assertTrue(second_started.exists())
        finally:
            for process in (first, second):
                if process is not None and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)

    def test_coordinator_import_is_cad_free_and_entrypoint_policy_passes(self) -> None:
        code = (
            "import sys; import cad_runner.coordinator; "
            "bad=[n for n in sys.modules if n.split('.')[0] in "
            "{'OCP','build123d','cadquery','vtk','ocp_vscode'}]; "
            "print(bad); raise SystemExit(bool(bad))"
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PROJECT_ROOT)
        isolated = subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(isolated.returncode, 0, isolated.stdout + isolated.stderr)
        policy = subprocess.run(
            [sys.executable, "scripts/check_cad_entrypoints.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(policy.returncode, 0, policy.stdout + policy.stderr)

        for path in PROJECT_ROOT.rglob("*.py"):
            relative = path.relative_to(PROJECT_ROOT)
            if any(
                part == "build" or part == "__pycache__" or part.startswith(".")
                for part in relative.parts
            ):
                continue
            if relative in {
                Path("cad_runner/coordinator.py"),
                Path("tests/test_cad_runner.py"),
                Path("scripts/check_cad_entrypoints.py"),
            }:
                continue
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("subprocess.Popen", source, str(relative))
            self.assertNotIn("preexec_fn", source, str(relative))
            self.assertNotIn("os.fork(", source, str(relative))
            self.assertNotIn("start_new_session", source, str(relative))

    def test_entrypoint_audit_covers_nested_imports_and_cataloged_coupon(self) -> None:
        from scripts.check_cad_entrypoints import (
            MARKER,
            entrypoint_source_violations,
            repository_cad_entrypoints,
            source_requires_cad_guard,
        )

        coupon = PROJECT_ROOT / "workbench/designs/joint_coupon/build.py"
        self.assertIn(coupon, repository_cad_entrypoints())
        nested = (
            "def build():\n    from build123d import Box\n    return Box(1, 1, 1)\n"
        )
        self.assertTrue(source_requires_cad_guard(nested))

        coupon_text = coupon.read_text(encoding="utf-8")
        without_guard = coupon_text.replace(MARKER, "", 1)
        self.assertTrue(
            any(
                "missing CAD coordinator guard" in issue
                for issue in entrypoint_source_violations(
                    Path("workbench/designs/joint_coupon/build.py"),
                    without_guard,
                )
            )
        )

    def test_native_free_exception_modules_fail_closed_on_cad_import(self) -> None:
        from scripts.check_cad_entrypoints import source_requires_cad_guard

        for relative in (
            Path("scripts/cad_review.py"),
            Path("scripts/cad_verification_io.py"),
            Path("scripts/cad_workflow_cli.py"),
        ):
            source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertFalse(source_requires_cad_guard(source), str(relative))
            self.assertTrue(
                source_requires_cad_guard(
                    source + "\nif False:\n    import build123d\n"
                ),
                str(relative),
            )


if __name__ == "__main__":
    unittest.main()
