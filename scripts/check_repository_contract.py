#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".repo-contract.yml"
FORBIDDEN_RUNNERS = ("ubuntu-latest", "windows-latest", "macos-latest")
ALLOWED_MODELS = {"dev-main", "direct-main", "upstream-mirror"}
# Repo-scoped ARC scale sets are self-hosted but selected by name only, without the self-hosted label.
OPTIONAL_KEYS = {"arc_runner_scale_sets"}
ARC_SCALE_SET_NAME = re.compile(r"arc-[a-z0-9]+(?:-[a-z0-9]+)*")


def fail(message: str) -> None:
    raise SystemExit(f"repository-contract: {message}")


def parse_simple_yaml(path: pathlib.Path) -> dict[str, object]:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

    result: dict[str, object] = {}
    current_list: str | None = None

    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("  - "):
            if current_list is None:
                fail(f"unexpected list item at {path.name}:{lineno}")
            value = stripped[2:].strip()
            cast = result.get(current_list)
            if not isinstance(cast, list):
                fail(f"invalid list state for {current_list}")
            cast.append(value)
            continue

        if line.startswith(" "):
            fail(f"unsupported indentation at {path.name}:{lineno}")

        match = re.fullmatch(r"([A-Za-z0-9_]+):(?:\s*(.*))?", line)
        if not match:
            fail(f"unsupported YAML syntax at {path.name}:{lineno}")

        key, value = match.groups()
        if key in result:
            fail(f"duplicate key {key!r} in {path.name}")

        if value is None or value == "":
            result[key] = []
            current_list = key
            continue

        current_list = None
        if value.isdigit():
            result[key] = int(value)
        else:
            result[key] = value

    return result


def require_scalar(config: dict[str, object], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key} must be a non-empty scalar")
    return value


def require_list(config: dict[str, object], key: str) -> list[str]:
    value = config.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        fail(f"{key} must be a non-empty list")
    if len(value) != len(set(value)):
        fail(f"{key} must not contain duplicates")
    return value


def validate_config(config: dict[str, object]) -> None:
    expected_keys = {
        "version",
        "branch_model",
        "integration_branch",
        "stable_branch",
        "ci_runner_policy",
        "production_mutation",
        "work_branch_prefixes",
        "required_files",
    }
    unknown = set(config) - expected_keys - OPTIONAL_KEYS
    missing = expected_keys - set(config)
    if unknown:
        fail(f"unknown contract keys: {', '.join(sorted(unknown))}")
    if missing:
        fail(f"missing contract keys: {', '.join(sorted(missing))}")

    if config.get("version") != 1:
        fail("version must be 1")

    model = require_scalar(config, "branch_model")
    if model not in ALLOWED_MODELS:
        fail(f"unsupported branch_model {model!r}")

    require_scalar(config, "integration_branch")
    require_scalar(config, "stable_branch")

    if require_scalar(config, "ci_runner_policy") != "self-hosted-only":
        fail("ci_runner_policy must be self-hosted-only")
    if require_scalar(config, "production_mutation") != "explicit-approval":
        fail("production_mutation must be explicit-approval")

    require_list(config, "work_branch_prefixes")
    require_list(config, "required_files")
    arc_scale_sets(config)


def arc_scale_sets(config: dict[str, object]) -> set[str]:
    if "arc_runner_scale_sets" not in config:
        return set()
    names = require_list(config, "arc_runner_scale_sets")
    for name in names:
        if not ARC_SCALE_SET_NAME.fullmatch(name):
            fail(f"invalid ARC runner scale set name {name!r}")
    return set(names)


def validate_required_files(config: dict[str, object]) -> None:
    for rel in require_list(config, "required_files"):
        path = ROOT / rel
        if not path.is_file():
            fail(f"required file missing: {rel}")


def validate_docs(config: dict[str, object]) -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    development = (ROOT / "docs/development.md").read_text()
    security = (ROOT / "docs/security.md").read_text()

    required_phrases = {
        "AGENTS.md": ["duplicate", "stop", "self-hosted", "live"],
        "docs/development.md": ["duplicate", "stop", "self-hosted", "promotion"],
        "docs/security.md": ["secret", "live", "self-hosted", "approval"],
    }
    texts = {
        "AGENTS.md": agents.lower(),
        "docs/development.md": development.lower(),
        "docs/security.md": security.lower(),
    }
    for rel, phrases in required_phrases.items():
        for phrase in phrases:
            if phrase not in texts[rel]:
                fail(f"{rel} must document {phrase!r}")

    model = require_scalar(config, "branch_model")
    integration = require_scalar(config, "integration_branch")
    stable = require_scalar(config, "stable_branch")

    if model == "dev-main":
        for rel, text in (("AGENTS.md", agents), ("docs/development.md", development)):
            if integration not in text or stable not in text:
                fail(f"{rel} must document configured {integration}->{stable} branch model")


def workflow_files() -> list[pathlib.Path]:
    root = ROOT / ".github/workflows"
    if not root.is_dir():
        return []
    return sorted([*root.glob("*.yml"), *root.glob("*.yaml")])


def runs_on_text(lines: list[str], index: int) -> str:
    """Return the value text of the runs-on key at lines[index], including contiguous block-list items."""
    first = lines[index]
    value = first.split(":", 1)[1]
    if value.strip() and not value.strip().startswith("#"):
        return value
    indent = len(first) - len(first.lstrip())
    items = []
    for line in lines[index + 1 :]:
        if line.strip().startswith("-") and len(line) - len(line.lstrip()) >= indent:
            items.append(line)
        elif line.strip() and not line.strip().startswith("#"):
            break
    return "\n".join(items)


def validate_workflows(config: dict[str, object]) -> None:
    scale_sets = arc_scale_sets(config)
    for path in workflow_files():
        text = path.read_text()
        lowered = text.lower()
        for token in FORBIDDEN_RUNNERS:
            if token in lowered:
                fail(f"forbidden GitHub-hosted runner {token!r} in {path.relative_to(ROOT)}")

        lines = text.splitlines()
        for index, line in enumerate(lines):
            where = f"{path.relative_to(ROOT)}:{index + 1}"
            scalar = re.match(r"^\s*runs-on:\s*([^#\[]+?)\s*(?:#.*)?$", line)
            if scalar and scalar.group(1) in scale_sets:
                continue
            if scale_sets and re.match(r"^\s*runs-on:", line):
                # Expression-built selectors can resolve to untrusted values even beside a literal self-hosted.
                if "${{" in runs_on_text(lines, index):
                    fail(f"expression-built runs-on is not allowed when ARC scale sets are configured in {where}")
                # Any ARC-style name outside an exact name-only scalar is mixed or unlisted: reject.
                if re.search(r"(?<![A-Za-z0-9_-])arc-[A-Za-z0-9_-]+", runs_on_text(lines, index)):
                    fail(f"ARC runner scale sets must be the sole name-only runs-on value in {where}")
            if re.match(r"^\s*runs-on:\s*[^#\[]+", line):
                if "self-hosted" not in line:
                    fail(f"runs-on must include self-hosted in {where}")
            if re.match(r"^\s*runs-on:\s*$", line):
                block = "\n".join(lines[index + 1 : index + 6])
                if "self-hosted" not in block:
                    fail(f"runs-on block must include self-hosted in {where}")


def branch_allowed(config: dict[str, object], head: str, base: str) -> tuple[bool, str]:
    model = require_scalar(config, "branch_model")
    integration = require_scalar(config, "integration_branch")
    stable = require_scalar(config, "stable_branch")
    prefixes = tuple(require_list(config, "work_branch_prefixes"))

    if model in {"dev-main", "upstream-mirror"}:
        if base == stable:
            ok = head == integration
            return ok, f"only literal {integration} may target {stable}"
        if base == integration:
            ok = head == integration or head.startswith(prefixes)
            return ok, f"PRs to {integration} must use an approved work branch prefix"
        return False, f"unsupported PR target {base!r} for {model}"

    if model == "direct-main":
        if base != stable:
            return False, f"direct-main repositories only accept PRs to {stable}"
        ok = head.startswith(prefixes)
        return ok, f"PRs to {stable} must use an approved work branch prefix"

    return False, f"unsupported branch model {model}"


def main(argv: list[str]) -> int:
    config = parse_simple_yaml(CONFIG)
    validate_config(config)

    if len(argv) == 4 and argv[1] == "--branch-flow":
        head, base = argv[2], argv[3]
        ok, reason = branch_allowed(config, head, base)
        print(f"repository-contract: head={head} base={base} model={config['branch_model']}")
        if not ok:
            print(f"repository-contract: {reason}", file=sys.stderr)
            return 1
        return 0

    if len(argv) != 1:
        print("usage: check_repository_contract.py [--branch-flow HEAD BASE]", file=sys.stderr)
        return 2

    validate_required_files(config)
    validate_docs(config)
    validate_workflows(config)
    print("repository-contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
