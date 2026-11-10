# Repository Template

Private bootstrap template for new `sigtom` repositories using the repository-first Codex contract.

This repository provides the minimum structure for a fresh project:

- concise root `AGENTS.md` startup instructions;
- `docs/development.md` and `docs/security.md`;
- `.repo-contract.yml` repository policy declaration;
- `scripts/check_repository_contract.py` structural policy validation;
- a self-hosted reusable GitHub Actions contract workflow;
- `docs/ci-efficiency.md` CI efficiency baseline and rollout recipe;
- a tiny local caller workflow suitable for repositories created from this template.

The template is intentionally generic. New repositories must replace placeholder project facts with repository-specific purpose, validation commands, branch model, security boundaries, and live-mutation boundaries before feature implementation begins.

## Default branch model

The template defaults to:

```text
work branch -> dev -> explicit literal dev -> main
```

Projects that intentionally use direct-to-`main` or imported/upstream-mirror models must update `.repo-contract.yml`, `AGENTS.md`, and `docs/development.md` together.

## CI rule

GitHub Actions execution must use self-hosted/local runners only. GitHub-hosted labels such as `ubuntu-latest`, `windows-latest`, and `macos-latest` are prohibited.

## Validate

```sh
python3 scripts/check_repository_contract.py
python3 -m unittest tests/test_check_repository_contract.py
```

The check is structural; repository-specific tests remain owned by each generated repository.
