# Development workflow

This document defines the default repository-local development model for repositories created from `sigtom/repo-template`.

Replace generic language with project-specific commands and exceptions before feature implementation begins.

## Task startup

For every task:

1. read root `AGENTS.md`;
2. read the assigned GitHub issue;
3. inspect existing branches and pull requests for the same task or promotion;
4. read only the current docs/code needed for that task;
5. use external memory only for cross-repository or historical context, not for basic repository orientation.

Do not create a second issue, branch, or PR for work that already has an active owner unless the current issue explicitly supersedes it.

## Default branch model

The default contract is:

```text
codex/*, feat/*, fix/*
          |
          v
        PR -> dev
              |
             STOP
              |
      explicit promotion
              |
       PR literal dev -> main
```

Rules:

- `dev` is the integration branch.
- `main` is stable.
- work branches normally start from current `dev`;
- normal task PRs target `dev`;
- only literal `dev` may target `main`;
- after normal task work merges to `dev`, stop unless promotion is explicitly part of the task;
- search for an existing `dev -> main` promotion PR before creating one;
- do not force-push reviewed work or rewrite ancestry merely to manipulate CI/review state.

A repository may intentionally use `direct-main` or `upstream-mirror` instead. If so, update `.repo-contract.yml`, this file, and `AGENTS.md` together. Do not let the configuration and prose disagree.

## Validation

Every repository must retain the structural contract check:

```sh
python3 scripts/check_repository_contract.py
```

Add exact repository-specific validation commands here as the project is built. Prefer the smallest relevant local check during development and broader validation at the PR/promotion boundary.

Where practical, projects may provide predictable wrappers such as:

```text
scripts/ci/fast
scripts/ci/full
scripts/ci/security
scripts/ci/release
```

Do not add wrappers unless they preserve the project's real validation semantics.

## CI policy

- GitHub Actions execution is self-hosted/local only.
- GitHub-hosted runner labels are prohibited.
- Repositories may opt in to repo-scoped ARC runner scale sets by listing exact names in the optional `.repo-contract.yml` key `arc_runner_scale_sets` (names match `arc-[a-z0-9]+(-[a-z0-9]+)*`). A listed name is accepted only as a bare scalar `runs-on: <name>`; unlisted, quoted, expression-built, or mixed legacy/ARC selectors and GitHub-hosted labels are rejected. With the key unset every `runs-on` must still include `self-hosted`. This template lists its own `arc-repo-template-ci` and its three workflows select it; new repositories inherit those files but not the template's runner registration, so after their own pool is live, bootstrap must replace that selector with the repository's own verified pool and verify a native job runs plus zero idle runners.
- PR validation should be path/event-aware where safe, but never with workflow-level path filters that hide a required check; the stable contract context always reports.
- Superseded PR source-validation runs cancel; manual runs use unique groups and do not cancel.
- Run proportional local checks and required native CI once per exact head; see `docs/ci-efficiency.md`.
- Do not blindly repeat expensive PR validation immediately after merge without a post-merge reason.
- Live operational/deployment workflows must remain distinct from ordinary source validation.
- Branch-flow checks apply to pull requests, not generic push events.

The repository contract workflow validates only structural policy. Product-specific build/test/security/release behavior remains local to the repository.

## Review boundary

Before merge:

- confirm the diff matches the assigned issue;
- confirm no duplicate issue/PR owns the same work;
- run the contract checker and relevant project tests;
- inspect the exact PR head/base and unresolved review state;
- ensure no live/deployment/credential mutation was smuggled into ordinary source work.

## Stop conditions

Stop and request review when proceeding would require any unrequested:

- `dev -> main` promotion;
- production/live deployment or restart;
- credential or secret lifecycle action;
- branch-protection/repository-setting change;
- destructive data migration;
- broadening of authorization, exposure, or trust boundaries.

Repository completion, promotion, deployment, and live acceptance are separate states unless the assigned issue explicitly combines them.
