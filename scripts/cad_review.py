"""Coordinate Text-to-CAD review without importing native CAD libraries."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cad_verification import VerificationProfile  # noqa: E402
from scripts.cad_verification_io import (  # noqa: E402
    contract_profile_report,
    review_packet_report,
)


PROJECT_CONFIG = ROOT / ".cad-project/project.toml"
READ_ONLY_SERVER_NAME = "server.readonly.mjs"
READ_ONLY_LAUNCHER_NAME = "start-agent-viewer.readonly.mjs"


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def load_project_config(path: Path = PROJECT_CONFIG) -> dict:
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    if config.get("schema_version") != 1:
        raise RuntimeError(f"Unsupported CAD project schema in {path}")
    if config.get("runtime", {}).get("concurrency_limit") != 1:
        raise RuntimeError("This coordinator currently supports one heavy CAD worker")
    if config.get("viewer", {}).get("read_only") is not True:
        raise RuntimeError("Text-to-CAD Viewer must be configured read-only")
    return config


def repo_path(value: str | Path) -> Path:
    path = (ROOT / value).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise RuntimeError(f"Configured path escapes the repository: {value}")
    return path


def viewer_tool_root(config: dict) -> Path:
    override = os.environ.get("TEXT_TO_CAD_ROOT")
    return (
        Path(override).expanduser().resolve()
        if override
        else repo_path(config["viewer"]["tool_root"])
    )


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Pinned Text-to-CAD {label} changed: expected one patch anchor, found {count}"
        )
    return text.replace(old, new, 1)


def prepare_read_only_viewer(tool_root: Path) -> tuple[Path, Path]:
    """Create generated sibling entrypoints with generation disabled.

    The exact source anchors are intentional: a future upstream change fails
    closed instead of silently launching a generation-capable Viewer.
    """

    viewer_root = tool_root / "viewer"
    server_source = viewer_root / "src/server/server.mjs"
    launcher_source = viewer_root / "scripts/start-agent-viewer.mjs"
    if not server_source.is_file() or not launcher_source.is_file():
        raise RuntimeError(f"Pinned Viewer sources are missing under {viewer_root}")

    server = _replace_once(
        server_source.read_text(encoding="utf-8"),
        'const stepArtifactBackendEnabled = localAssetBackendEnabled && typeof backend.generateStepArtifact === "function";',
        "const stepArtifactBackendEnabled = false; // Repository-enforced read-only mode.",
        "server",
    )
    read_only_server = server_source.with_name(READ_ONLY_SERVER_NAME)
    if (
        not read_only_server.is_file()
        or read_only_server.read_text(encoding="utf-8") != server
    ):
        read_only_server.write_text(server, encoding="utf-8")

    launcher = launcher_source.read_text(encoding="utf-8")
    launcher = _replace_once(
        launcher,
        'path.join(resolvedPackageRoot, "src", "server", "server.mjs"),',
        f'path.join(resolvedPackageRoot, "src", "server", "{READ_ONLY_SERVER_NAME}"),',
        "launcher server target",
    )
    launcher = _replace_once(
        launcher,
        "    serverInfo &&\n    serverInfo.app === VIEWER_SERVER_APP_ID &&",
        "    serverInfo &&\n"
        "    serverInfo.stepArtifactGenerationAvailable === false &&\n"
        "    serverInfo.app === VIEWER_SERVER_APP_ID &&",
        "launcher reuse policy",
    )
    read_only_launcher = launcher_source.with_name(READ_ONLY_LAUNCHER_NAME)
    if (
        not read_only_launcher.is_file()
        or read_only_launcher.read_text(encoding="utf-8") != launcher
    ):
        read_only_launcher.write_text(launcher, encoding="utf-8")
    return read_only_server, read_only_launcher


def require_viewer_runtime(config: dict) -> tuple[Path, Path]:
    tool_root = viewer_tool_root(config)
    expected = config["viewer"]
    completed = subprocess.run(
        ["git", "-C", str(tool_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    actual_commit = completed.stdout.strip() if completed.returncode == 0 else ""
    if actual_commit != expected["commit"]:
        raise RuntimeError(
            f"Expected Text-to-CAD commit {expected['commit']}; "
            f"found {actual_commit or 'missing checkout'}"
        )
    package_path = tool_root / "viewer/package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    if str(package.get("version", "")) != expected["version"]:
        raise RuntimeError(
            f"Expected Text-to-CAD {expected['version']}; found {package.get('version')}"
        )
    if not (tool_root / "viewer/node_modules").is_dir():
        raise RuntimeError(
            f"Viewer dependencies are missing under {tool_root / 'viewer'}"
        )
    _, launcher = prepare_read_only_viewer(tool_root)
    return tool_root, launcher


def _base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid Viewer URL: {value}")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def fetch_server_info(viewer_url: str, timeout: float = 2.0) -> dict:
    with urlopen(f"{_base_url(viewer_url)}/__cad/server", timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_read_only_server(info: dict, config: dict) -> None:
    if info.get("app") != "cad-viewer" or info.get("dynamicRoot") is not True:
        raise RuntimeError("URL is not a compatible local CAD Viewer")
    if info.get("stepArtifactGenerationAvailable") is not False:
        raise RuntimeError(
            "Viewer can generate STEP artifacts; do not use it for this repo"
        )
    if info.get("backend") != "local-fs":
        raise RuntimeError(f"Unexpected Viewer backend: {info.get('backend')}")
    if str(info.get("viewerVersion", "")) != config["viewer"]["version"]:
        raise RuntimeError(f"Unexpected Viewer version: {info.get('viewerVersion')}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_link(step: Path, viewer_url: str, config: dict) -> tuple[str, str]:
    artifact_root = repo_path(config["artifact_root"])
    step = step.expanduser().resolve()
    if not step.is_file():
        raise FileNotFoundError(step)
    try:
        step.relative_to(artifact_root)
    except ValueError as error:
        raise RuntimeError(f"Artifact must be under {artifact_root}: {step}") from error
    parsed = urlsplit(viewer_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    # Scope the interactive catalog to the artifact's own directory.  The
    # build tree can contain many historical CAD outputs, and asking the
    # Viewer to enumerate all of them can exceed its client-side catalog
    # timeout.  The artifact-root check above still enforces repository scope.
    query["dir"] = str(step.parent)
    query["file"] = step.name
    link = urlunsplit((parsed.scheme, parsed.netloc, "/", urlencode(query), ""))
    return link, sha256_file(step)


def command_viewer(args: argparse.Namespace, config: dict) -> int:
    _, launcher = require_viewer_runtime(config)
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required to run Text-to-CAD Viewer")
    artifact_root = repo_path(config["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    viewer = config["viewer"]
    command = [
        node,
        str(launcher),
        "--viewer-start-mode",
        "serve",
        "--host",
        viewer["host"],
        "--port",
        str(viewer["preferred_port"]),
        "--dir",
        str(artifact_root),
    ]
    if args.json:
        command.append("--json")
    os.execvpe(node, command, os.environ.copy())
    return 1


def command_check_server(args: argparse.Namespace, config: dict) -> int:
    info = fetch_server_info(args.viewer_url)
    assert_read_only_server(info, config)
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


def command_link(args: argparse.Namespace, config: dict) -> int:
    info = fetch_server_info(args.viewer_url)
    assert_read_only_server(info, config)
    link, digest = artifact_link(args.step, args.viewer_url, config)
    step = args.step.expanduser().resolve()
    sidecar = step.with_name(f".{step.name}.glb")
    if not sidecar.is_file():
        raise FileNotFoundError(f"Viewer link requires the exact sidecar: {sidecar}")
    payload = {
        "schema_version": 1,
        "record_id": f"viewer-record.{step.stem.lower().replace('_', '-')}",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "url": link,
        "server": {
            key: info.get(key)
            for key in (
                "app",
                "backend",
                "dynamicRoot",
                "stepArtifactGenerationAvailable",
                "viewerVersion",
            )
        },
        "artifacts": [
            {
                "path": str(step.relative_to(ROOT)),
                "sha256": digest,
            },
            {
                "path": str(sidecar.relative_to(ROOT)),
                "sha256": sha256_file(sidecar),
            },
        ],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.record:
        record = args.record.expanduser().resolve()
        record.relative_to(ROOT)
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


def _installed_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def command_doctor(_args: argparse.Namespace, config: dict) -> int:
    failures: list[str] = []
    checks: list[tuple[str, str, str]] = []

    for distribution, expected in (
        ("build123d", config["dependencies"]["build123d"]),
        ("cadquery-ocp-novtk", config["dependencies"]["cadquery_ocp_novtk"]),
    ):
        actual = _installed_version(distribution)
        checks.append(
            (
                distribution,
                "OK" if actual == expected else "FAIL",
                f"expected {expected}, found {actual}",
            )
        )

    mcp_config = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
    mcp_pin = f"build123d-mcp@{config['dependencies']['build123d_mcp']}"
    checks.append(
        ("Build123d MCP pin", "OK" if mcp_pin in mcp_config else "FAIL", mcp_pin)
    )

    catalog_check = _model_catalog_run(config, "check", capture_output=True)
    catalog_detail = (
        catalog_check.stdout.strip().removeprefix("OK  model catalog: ")
        if catalog_check.returncode == 0
        else catalog_check.stderr.strip() or catalog_check.stdout.strip()
    )
    checks.append(
        (
            "model catalog",
            "OK" if catalog_check.returncode == 0 else "FAIL",
            catalog_detail or "catalog check produced no details",
        )
    )

    try:
        tool_root, _ = require_viewer_runtime(config)
        checks.append(("read-only Viewer overlay", "OK", str(tool_root)))
    except Exception as error:  # Doctor aggregates actionable setup failures.
        checks.append(("read-only Viewer overlay", "FAIL", str(error)))

    preferred_url = (
        f"http://{config['viewer']['host']}:{config['viewer']['preferred_port']}"
    )
    try:
        info = fetch_server_info(preferred_url, timeout=0.5)
        safe = info.get("stepArtifactGenerationAvailable") is False
        status = "OK" if safe else "WARN"
        detail = (
            "read-only"
            if safe
            else (
                "generation enabled; never use this URL—the safe launcher will use another port"
            )
        )
        checks.append(("Viewer on preferred port", status, detail))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        checks.append(
            ("Viewer on preferred port", "OK", "not running or probe blocked")
        )

    for name, status, detail in checks:
        print(f"{status}  {name}: {detail}")
        if status == "FAIL":
            failures.append(name)
    return 1 if failures else 0


def _model_catalog_run(
    config: dict,
    command: str,
    *arguments: str,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    catalog = repo_path(config["model_catalog"])
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/model_catalog.py"),
            "--catalog",
            str(catalog),
            command,
            *arguments,
        ],
        cwd=ROOT,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def command_check_catalog(_args: argparse.Namespace, config: dict) -> int:
    return _model_catalog_run(config, "check").returncode


def command_models(args: argparse.Namespace, config: dict) -> int:
    arguments: list[str] = []
    if args.experiments:
        arguments.append("--experiments")
    elif args.all:
        arguments.append("--all")
    if args.status:
        arguments.extend(["--status", args.status])
    if args.json:
        arguments.append("--json")
    return _model_catalog_run(config, "list", *arguments).returncode


def command_sidecar(args: argparse.Namespace, _config: dict) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/text_to_cad_artifacts.py"),
        "sidecar",
        str(args.step),
    ]
    if args.kind:
        command.extend(["--kind", args.kind])
    if args.artifact_root:
        command.extend(["--artifact-root", str(args.artifact_root)])
    if args.force:
        command.append("--force")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def command_snapshot(args: argparse.Namespace, _config: dict) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/text_to_cad_artifacts.py"),
        "snapshot",
        "--job",
        str(args.job),
    ]
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def command_stats(args: argparse.Namespace, config: dict) -> int:
    from cad_runner.statistics import collect_job_statistics, render_job_statistics

    state_root = repo_path(config["artifact_root"]) / "cad-jobs"
    statistics = collect_job_statistics(state_root, target_limit=args.limit)
    if args.json:
        print(json.dumps(statistics.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_job_statistics(statistics))
    return 0


def _print_verification_report(report: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(
        f"{report['document']} {report['status']}: "
        f"{report['profile']} ({report['path']})"
    )
    for requirement in report["requirements"]:
        actual = requirement.get("actual")
        actual_text = (
            "missing" if actual is None else f"{actual['value']} {actual['unit']}"
        )
        print(
            f"  {requirement['status'].upper()} "
            f"{requirement['requirement_id']}: {actual_text}"
        )
    for issue in report.get("issues", ()):
        print(
            f"  ERROR {issue['path']}: {issue['message']} [{issue['code']}]",
            file=sys.stderr,
        )


def command_verify_contract(args: argparse.Namespace, _config: dict) -> int:
    try:
        report = contract_profile_report(
            args.contract,
            VerificationProfile(args.profile),
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    _print_verification_report(report, as_json=args.json)
    return 0


def command_verify_packet(args: argparse.Namespace, _config: dict) -> int:
    try:
        report = review_packet_report(
            args.contract,
            args.packet,
            requested_profile=(
                VerificationProfile(args.profile) if args.profile else None
            ),
            repository_root=ROOT,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    _print_verification_report(report, as_json=args.json)
    return 0 if report["success"] else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    viewer = subparsers.add_parser("viewer", help="start or reuse the read-only Viewer")
    viewer.add_argument("--json", action="store_true")
    viewer.set_defaults(handler=command_viewer)

    check = subparsers.add_parser(
        "check-server", help="verify a running Viewer is read-only"
    )
    check.add_argument("viewer_url")
    check.set_defaults(handler=command_check_server)

    link = subparsers.add_parser(
        "link", help="create a hash-bound Viewer artifact link"
    )
    link.add_argument("step", type=Path)
    link.add_argument("--viewer-url", required=True)
    link.add_argument("--record", type=Path)
    link.set_defaults(handler=command_link)

    doctor = subparsers.add_parser("doctor", help="check pins and Viewer safety")
    doctor.set_defaults(handler=command_doctor)

    catalog_check = subparsers.add_parser(
        "check-catalog", help="verify model records and experiment coverage"
    )
    catalog_check.set_defaults(handler=command_check_catalog)

    models = subparsers.add_parser(
        "models", help="list primary models or the full experiment inventory"
    )
    model_scope = models.add_mutually_exclusive_group()
    model_scope.add_argument("--experiments", action="store_true")
    model_scope.add_argument("--all", action="store_true")
    models.add_argument("--status")
    models.add_argument("--json", action="store_true")
    models.set_defaults(handler=command_models)

    sidecar = subparsers.add_parser(
        "sidecar", help="generate one topology sidecar through cad_runner"
    )
    sidecar.add_argument("step", type=Path)
    sidecar.add_argument("--kind", choices=("part", "assembly"), default="part")
    sidecar.add_argument("--artifact-root", type=Path)
    sidecar.add_argument("--force", action="store_true")
    sidecar.set_defaults(handler=command_sidecar)

    snapshot = subparsers.add_parser(
        "snapshot", help="run one Snapshot job through cad_runner"
    )
    snapshot.add_argument("--job", type=Path, required=True)
    snapshot.add_argument("--json", action="store_true")
    snapshot.set_defaults(handler=command_snapshot)

    stats = subparsers.add_parser(
        "stats", help="summarize CAD job duration, outcomes, and resource use"
    )
    stats.add_argument("--limit", type=positive_int, default=5)
    stats.add_argument("--json", action="store_true")
    stats.set_defaults(handler=command_stats)

    verify = subparsers.add_parser(
        "verify",
        help="validate native-free design contracts and review packets",
    )
    verify_subparsers = verify.add_subparsers(dest="verification_kind", required=True)
    contract = verify_subparsers.add_parser(
        "contract",
        help="validate a contract and report one composed profile",
    )
    contract.add_argument("contract", type=Path)
    contract.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        required=True,
    )
    contract.add_argument("--json", action="store_true")
    contract.set_defaults(handler=command_verify_contract)

    packet = verify_subparsers.add_parser(
        "packet",
        help="validate packet semantics, artifacts, and selected-profile status",
    )
    packet.add_argument("contract", type=Path)
    packet.add_argument("packet", type=Path)
    packet.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in VerificationProfile),
        help="fail if the packet was produced for a different profile",
    )
    packet.add_argument("--json", action="store_true")
    packet.set_defaults(handler=command_verify_packet)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config = None if args.command == "verify" else load_project_config()
    return int(args.handler(args, config))


if __name__ == "__main__":
    raise SystemExit(main())
