# CI efficiency baseline

Bounded baseline for repositories created from this template. It is guidance plus small workflow hygiene, not a CI platform, generic engine, or new schema. Adapters for expensive suites are proven later in per-repo pilots.

## Template workflow behavior

- `repository-contract` has no `paths` filter. The cheap, stable `Repository contract` context always reports on PRs to `dev`/`main`, including edits that touch only checker regression tests. It always runs the current checker and unit tests fresh.
- Concurrency cancels superseded **pull_request** source validations only, grouped per PR number. Manual runs (`workflow_dispatch`) use a unique `run_id`+`run_attempt` group and never cancel. A reusable workflow called via `workflow_call` sees the caller's event context, so the group lives only in the callee; the caller has none, so the two cannot self-cancel.
- Gitleaks stays a fresh full-history scan. Branch-flow stays PR-only.
- Job names, workflow names, runner selectors, permissions, and the branch model are unchanged; required-check contexts remain stable.

## Proportional local checks

| Change | Local check before PR |
| --- | --- |
| Docs/config only | focused doc/config check, `git diff --check`, secret scan of the diff |
| Behavior change | focused tests for that behavior plus the above |
| Shared behavior, or a concrete CI gap the focused checks cannot cover | full local suite |

Do not run blanket unrelated suites. Required native CI runs once for the exact PR candidate; repeat for a changed head/base, a failure, or a concrete unresolved validation concern. Remove a duplicate push-triggered run only when the PR run provides equivalent coverage.

Add tests only when they catch a plausible failure independently, through known public behavior. Do not add tests for existence, constants, or coverage numbers.

## Rollout recipe for a repository

1. Identify the required stable status contexts and the branch model (`.repo-contract.yml`). Never rename or drop them.
2. Go PR-first; avoid redundant pushes and post-merge reruns unless there is a post-merge reason.
3. Keep unique native, release, signing, publish, live, manual, and external audits. Do not replace them with cheaper checks.
4. Scope validation only when safe. Include both sides of renames and deletions and inspect dependencies in both the base and head. Unknown or shared paths, missing dependency information, or an untrustworthy diff run the full fallback. Never use workflow-level path filters that can hide a required check.
5. When subprocess fixtures exercise scoping or reuse logic, scrub inherited `VALIDATE_*` (or the repo's equivalent) control variables. For that behavior, add a regression that pollutes the parent environment and a negative control that proves the actual engine is exercised.
6. Use the existing governance factory and scoped local per-repo PRs. Preserve custom workflow roles, runner pools, and check contexts; change no central sharing permission.
7. Consider a manual or staggered nightly full run where meaningful.
8. Record measured cold and hit timings per repo. Make no extrapolated speed claims.

## Artifact and receipt reuse

Off by default for cheap template checks (they run fresh in seconds).

An expensive, deterministic source suite may opt in only after native proof of a cold run and a same-tree hit. A reusable result requires all of:

- exact full-tree identity plus suite and toolchain identity;
- a successful same-repository native run/job/attempt as the source;
- reviewed source provenance;
- expiry/deadline checks; expired, missing, or malformed receipts fail to a full run.

Never reuse results of secret, provenance, scope, fixture, or receipt checks, nor anything depending on a mutable advisory DB, live systems, or release writes.

Keep build artifacts and dependency caches distinct from validation receipts. A cache speeds work; only a receipt can stand in for a validation, and only under the rules above. Never execute untrusted artifacts.

Implementation references: [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) and [reusable-workflow concurrency and context](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations).
