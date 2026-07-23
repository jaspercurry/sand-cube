from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from scripts.cad_review import (
    READ_ONLY_LAUNCHER_NAME,
    READ_ONLY_SERVER_NAME,
    artifact_link,
    load_project_config,
    parser,
    prepare_read_only_viewer,
)


class CadReviewTest(unittest.TestCase):
    def test_stats_command_is_native_free_and_has_machine_readable_output(self) -> None:
        args = parser().parse_args(["stats", "--limit", "3", "--json"])

        self.assertEqual(args.command, "stats")
        self.assertEqual(args.limit, 3)
        self.assertTrue(args.json)

    def test_verification_commands_compose_profiles_without_native_cad(self) -> None:
        contract = parser().parse_args(
            ["verify", "contract", "contract.json", "--profile", "fit"]
        )
        packet = parser().parse_args(
            ["verify", "packet", "contract.json", "packet.json", "--json"]
        )

        self.assertEqual(contract.profile, "fit")
        self.assertEqual(packet.verification_kind, "packet")
        self.assertTrue(packet.json)

    def test_project_manifest_has_serial_read_only_contract(self) -> None:
        config = load_project_config()
        self.assertEqual(config["runtime"]["concurrency_limit"], 1)
        self.assertTrue(config["viewer"]["read_only"])
        self.assertEqual(config["dependencies"]["build123d"], "0.11.1")
        self.assertEqual(config["dependencies"]["build123d_mcp"], "0.3.79")
        self.assertEqual(config["model_catalog"], ".cad-project/models.toml")

    def test_claude_adapter_points_to_the_canonical_skill(self) -> None:
        root = Path(__file__).resolve().parents[1]
        claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
        adapter = (root / ".claude/skills/speaker-enclosure-cad/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("@AGENTS.md", claude)
        self.assertIn(
            ".agents/skills/speaker-enclosure-cad/SKILL.md",
            adapter,
        )

    def test_generated_viewer_overlay_disables_generation_and_unsafe_reuse(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="cad-viewer-overlay-") as temporary:
            tool_root = Path(temporary)
            server_dir = tool_root / "viewer/src/server"
            launcher_dir = tool_root / "viewer/scripts"
            server_dir.mkdir(parents=True)
            launcher_dir.mkdir(parents=True)
            (server_dir / "server.mjs").write_text(
                'const stepArtifactBackendEnabled = localAssetBackendEnabled && typeof backend.generateStepArtifact === "function";\n',
                encoding="utf-8",
            )
            (launcher_dir / "start-agent-viewer.mjs").write_text(
                'path.join(resolvedPackageRoot, "src", "server", "server.mjs"),\n'
                "return Boolean(\n"
                "    serverInfo &&\n"
                "    serverInfo.app === VIEWER_SERVER_APP_ID &&\n"
                ");\n",
                encoding="utf-8",
            )

            server, launcher = prepare_read_only_viewer(tool_root)
            self.assertEqual(server.name, READ_ONLY_SERVER_NAME)
            self.assertEqual(launcher.name, READ_ONLY_LAUNCHER_NAME)
            self.assertIn("stepArtifactBackendEnabled = false", server.read_text())
            launcher_text = launcher.read_text()
            self.assertIn(READ_ONLY_SERVER_NAME, launcher_text)
            self.assertIn(
                "serverInfo.stepArtifactGenerationAvailable === false",
                launcher_text,
            )

            # Regeneration is deterministic and idempotent.
            self.assertEqual((server, launcher), prepare_read_only_viewer(tool_root))

    def test_artifact_link_scopes_catalog_to_artifact_directory(self) -> None:
        root = Path(__file__).resolve().parents[1]
        build = root / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cad-link-", dir=build) as temporary:
            step = Path(temporary) / "candidate.step"
            step.write_bytes(b"STEP candidate")
            link, _digest = artifact_link(
                step,
                "http://127.0.0.1:4179/?dir=stale&file=stale.step",
                {"artifact_root": "build"},
            )

            query = parse_qs(urlsplit(link).query)
            self.assertEqual(query["dir"], [str(step.parent.resolve())])
            self.assertEqual(query["file"], [step.name])
