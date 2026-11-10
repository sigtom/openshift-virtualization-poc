# OpenShift Virtualization POC test cases

Hands-on demonstrations for VMware/vCenter teams evaluating OpenShift Virtualization.

Each numbered case provides generic YAML, web console steps, equivalent CLI commands, expected results, and reset/cleanup instructions. Select approved workers and tailor the documented storage/boot-source values for your POC cluster before applying a case.

| Test case | Covers | Status |
| --- | --- | --- |
| [01 — Scheduling and migration](test-cases/01-scheduling-and-migration/) | Approved host placement, VM spreading, an impossible rule, manual live migration, and policy-driven descheduler migration | CLI lab validation passed; web UI/video pending presenter verification |

The first case targets OpenShift 4.21.31. The lab runs 4.22.11, so lab results do not certify the client version. Run the case's version/operator/schema/storage checks on the client first.

The required test uses the documented LongLifecycle/background-eviction path. It does not require a PSI MachineConfig rollout. CPU-load-aware balancing is a separate optional topic.

Start with the case README and [walkthrough](test-cases/01-scheduling-and-migration/RUNBOOK.md). Apply only the file named in each step; never apply the repository recursively. These are POC examples, not an automatically synchronized GitOps deployment.

This public repository intentionally uses a single main branch and no CI. Keep client names, cluster endpoints, credentials, and raw environment evidence out of source. Video links will be added after presenter review.
