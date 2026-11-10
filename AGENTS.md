# Repository instructions

This repository was created from the `sigtom/repo-template` repository-first contract.

Before feature implementation begins, replace generic template text with repository-specific facts. Do not leave placeholder purpose, validation, security, or live-operation language in an active project.

## Start here

1. Read `README.md` for repository purpose and current architecture/operations map.
2. Read `docs/development.md` for branch, PR, CI, duplicate-work, validation, and stop rules.
3. Read `docs/security.md` for secrets, trust boundaries, production/live mutation, and data-safety rules.
4. Read the assigned GitHub issue and inspect existing branches/PRs for the same work before creating anything.
5. Continue existing work rather than creating duplicate task or promotion PRs.

Repository files plus current GitHub issue/PR state define intended repo-local work. Approved live-system readback is authoritative for current runtime state.

## Default branch model

Unless this repository deliberately changes `.repo-contract.yml` and `docs/development.md` together:

- integration branch: `dev`;
- stable branch: `main`;
- work branches: `codex/*`, `feat/*`, `fix/*`;
- normal task PRs target `dev`;
- only literal `dev` may target `main`;
- after a task PR merges to `dev`, stop unless promotion is explicitly requested.

## Validation

Run the repository contract check before review:

```sh
python3 scripts/check_repository_contract.py
```

Add and document repository-specific tests as the project is implemented. Do not invent deployment or live mutation as a validation step.

## CI

GitHub Actions must use self-hosted/local runners only. Never introduce GitHub-hosted runner labels such as `ubuntu-latest`, `windows-latest`, or `macos-latest`.

Keep local checks proportional and run required native CI once per exact head; see `docs/ci-efficiency.md`.

## Safety boundary

- Never commit credentials, tokens, API keys, private keys, secret-bearing environment files, or rendered runtime secrets.
- Source changes, tests, CI success, or branch promotion do not authorize production deployment or live infrastructure mutation.
- Do not weaken branch protection, repository visibility, authentication, secret handling, or live-system safety as incidental cleanup.
- Stop when the assigned issue reaches its repository-defined PR/merge boundary unless promotion or live action is explicitly included.
