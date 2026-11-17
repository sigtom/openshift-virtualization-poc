# OpenShift Virtualization POC tests

Hands-on tests for VMware/vCenter teams learning OpenShift Virtualization.

## Start here

| Test case | Customer walkthrough | Administrator preparation |
| --- | --- | --- |
| 01 — VM placement and migration | **[Run the tests](test-cases/01-scheduling-and-migration/RUNBOOK.md)** | [Prepare the lab](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#prepare) |

Case 01 covers approved-host placement, VM separation, an impossible rule,
manual live migration and automatic placement-rule correction. Each test
shows the web console steps, matching CLI commands and the expected result.

The administrator prepares the cluster and VMs first. Customers then follow
one short walkthrough; detailed operator checks and cleanup stay in the
administrator guide.

The target is OpenShift 4.21.31. CLI validation was completed on a 4.22.11 lab
on 2026-11-10; that does not replace client preflight or presenter UI verification.

Use the [recording outline](test-cases/01-scheduling-and-migration/VIDEO-OUTLINE.md)
for a video and the [results sheet](test-cases/01-scheduling-and-migration/RESULTS-TEMPLATE.md)
to record outcomes. The YAML is generic: agree local worker and storage values
before use. Keep credentials and environment evidence out of this public repository.
