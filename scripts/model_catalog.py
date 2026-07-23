"""List and validate the repository's human-maintained CAD model catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = ROOT / ".cad-project/project.toml"
DEFAULT_CATALOG = ROOT / ".cad-project/models.toml"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class CatalogError(RuntimeError):
    """Raised when the catalog cannot be loaded or does not match the repo."""


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise CatalogError(f"Could not load {path}: {error}") from error


def catalog_path(project_config: Path = PROJECT_CONFIG) -> Path:
    config = _load_toml(project_config)
    configured = config.get("model_catalog", ".cad-project/models.toml")
    path = (ROOT / configured).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise CatalogError(f"Model catalog escapes the repository: {configured}")
    return path


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    path = path or catalog_path()
    catalog = _load_toml(path)
    if catalog.get("schema_version") != 1:
        raise CatalogError(f"Unsupported model catalog schema in {path}")
    return catalog


def _repo_path(value: str, *, field: str) -> Path:
    path = (ROOT / value).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise CatalogError(f"{field} escapes the repository: {value}")
    return path


def _validate_id(value: object, *, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        errors.append(f"{label} has invalid id {value!r}")


def _validate_existing_path(
    item: dict[str, Any], field: str, *, label: str, errors: list[str]
) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"{label} is missing {field}")
        return
    try:
        path = _repo_path(value, field=f"{label}.{field}")
    except CatalogError as error:
        errors.append(str(error))
        return
    if not path.exists():
        errors.append(f"{label}.{field} does not exist: {value}")


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    """Return deterministic catalog/repository consistency errors."""

    errors: list[str] = []
    policy = catalog.get("policy", {})
    model_statuses = set(policy.get("model_statuses", []))
    experiment_statuses = set(policy.get("experiment_statuses", []))
    experiment_root_value = policy.get("experiment_root", "experiments")

    if not model_statuses:
        errors.append("policy.model_statuses must not be empty")
    if not experiment_statuses:
        errors.append("policy.experiment_statuses must not be empty")

    models = catalog.get("models", [])
    experiments = catalog.get("experiments", [])
    if not isinstance(models, list) or not models:
        errors.append("models must contain at least one [[models]] entry")
        models = []
    if not isinstance(experiments, list):
        errors.append("experiments must be an array of tables")
        experiments = []

    seen_ids: set[str] = set()
    for index, model in enumerate(models):
        label = f"models[{index}]"
        if not isinstance(model, dict):
            errors.append(f"{label} must be a table")
            continue
        model_id = model.get("id")
        _validate_id(model_id, label=label, errors=errors)
        if isinstance(model_id, str):
            if model_id in seen_ids:
                errors.append(f"duplicate catalog id: {model_id}")
            seen_ids.add(model_id)
            label = f"model {model_id}"
        if model.get("status") not in model_statuses:
            errors.append(f"{label} has unknown status {model.get('status')!r}")
        for field in ("name", "kind", "source", "entrypoint"):
            if field in {"source", "entrypoint"}:
                _validate_existing_path(model, field, label=label, errors=errors)
            elif not isinstance(model.get(field), str) or not model[field]:
                errors.append(f"{label} is missing {field}")
        for field in ("implementation", "parameters", "validator", "release", "workbench"):
            if field in model:
                _validate_existing_path(model, field, label=label, errors=errors)
        output = model.get("output")
        if not isinstance(output, str) or not output:
            errors.append(f"{label} is missing output")
        else:
            try:
                _repo_path(output, field=f"{label}.output")
            except CatalogError as error:
                errors.append(str(error))

    try:
        experiment_root = _repo_path(
            str(experiment_root_value), field="policy.experiment_root"
        )
    except CatalogError as error:
        errors.append(str(error))
        experiment_root = ROOT / "experiments"

    listed_directories: set[str] = set()
    for index, experiment in enumerate(experiments):
        label = f"experiments[{index}]"
        if not isinstance(experiment, dict):
            errors.append(f"{label} must be a table")
            continue
        experiment_id = experiment.get("id")
        _validate_id(experiment_id, label=label, errors=errors)
        if isinstance(experiment_id, str):
            if experiment_id in seen_ids:
                errors.append(f"duplicate catalog id: {experiment_id}")
            seen_ids.add(experiment_id)
            label = f"experiment {experiment_id}"
        if experiment.get("status") not in experiment_statuses:
            errors.append(f"{label} has unknown status {experiment.get('status')!r}")
        for field in ("name", "family"):
            if not isinstance(experiment.get(field), str) or not experiment[field]:
                errors.append(f"{label} is missing {field}")
        _validate_existing_path(experiment, "directory", label=label, errors=errors)
        _validate_existing_path(experiment, "entrypoint", label=label, errors=errors)
        directory = experiment.get("directory")
        if isinstance(directory, str):
            if directory in listed_directories:
                errors.append(f"duplicate experiment directory: {directory}")
            listed_directories.add(directory)
            try:
                resolved = _repo_path(directory, field=f"{label}.directory")
                if resolved.parent != experiment_root:
                    errors.append(
                        f"{label}.directory must be an immediate child of "
                        f"{experiment_root_value}: {directory}"
                    )
            except CatalogError:
                pass

    actual_directories = {
        path.relative_to(ROOT).as_posix()
        for path in experiment_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    } if experiment_root.is_dir() else set()
    for missing in sorted(actual_directories - listed_directories):
        errors.append(f"uncataloged experiment directory: {missing}")
    for stale in sorted(listed_directories - actual_directories):
        errors.append(f"cataloged experiment directory is missing: {stale}")

    return errors


def _selected_entries(
    catalog: dict[str, Any], *, include: str, status: str | None
) -> list[dict[str, Any]]:
    if include == "models":
        entries = list(catalog["models"])
    elif include == "experiments":
        entries = list(catalog["experiments"])
    else:
        entries = [*catalog["models"], *catalog["experiments"]]
    if status:
        entries = [item for item in entries if item.get("status") == status]
    return entries


def _print_table(entries: Iterable[dict[str, Any]]) -> None:
    rows = [
        (
            str(item.get("id", "")),
            str(item.get("status", "")),
            str(item.get("kind", item.get("family", ""))),
            str(item.get("name", "")),
        )
        for item in entries
    ]
    if not rows:
        print("No catalog entries matched.")
        return
    headers = ("ID", "STATUS", "KIND/FAMILY", "NAME")
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(4)]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(4)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(row[i].ljust(widths[i]) for i in range(4)))


def command_check(_args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    errors = validate_catalog(catalog)
    if errors:
        for error in errors:
            print(f"FAIL  {error}", file=sys.stderr)
        return 1
    print(
        "OK  model catalog: "
        f"{len(catalog['models'])} primary models, "
        f"{len(catalog['experiments'])} experiment families"
    )
    return 0


def command_list(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    include = "all" if args.all else "experiments" if args.experiments else "models"
    entries = _selected_entries(catalog, include=include, status=args.status)
    if args.json:
        print(json.dumps(entries, indent=2, sort_keys=True))
    else:
        _print_table(entries)
    return 0


def command_show(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    entries = _selected_entries(catalog, include="all", status=None)
    match = next((item for item in entries if item.get("id") == args.id), None)
    if match is None:
        print(f"Unknown catalog id: {args.id}", file=sys.stderr)
        return 2
    print(json.dumps(match, indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--catalog", type=Path, help="override the configured catalog")
    subparsers = root.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="validate catalog and repo coverage")
    check.set_defaults(handler=command_check)

    listing = subparsers.add_parser("list", help="list primary models by default")
    scope = listing.add_mutually_exclusive_group()
    scope.add_argument("--experiments", action="store_true")
    scope.add_argument("--all", action="store_true")
    listing.add_argument("--status")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=command_list)

    show = subparsers.add_parser("show", help="show one model or experiment record")
    show.add_argument("id")
    show.set_defaults(handler=command_show)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        catalog = load_catalog(args.catalog.resolve() if args.catalog else None)
    except CatalogError as error:
        print(f"FAIL  {error}", file=sys.stderr)
        return 1
    return int(args.handler(args, catalog))


if __name__ == "__main__":
    raise SystemExit(main())
