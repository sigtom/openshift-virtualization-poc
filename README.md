# OpenShift Virtualization POC tests

Hands-on tests for VMware/vCenter teams learning OpenShift Virtualization.

## Start here

| Test case | Customer walkthrough | Administrator preparation |
| --- | --- | --- |
| 01 — VM placement and migration | **[Run the tests](test-cases/01-scheduling-and-migration/RUNBOOK.md)** | [Prepare the lab](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#prepare) |
| 02 — VM recovery after host failure (**fencing NOT TESTED**) | **[Run the test](test-cases/02-host-failure-recovery/RUNBOOK.md)** | [Prepare and gate](test-cases/02-host-failure-recovery/ADMIN-GUIDE.md#prepare) |
| 05 — Storage IOPS (**client validation pending**; Dell layer **deferred**) | **[Run the test](test-cases/05-storage-iops/RUNBOOK.md)** | [Prepare](test-cases/05-storage-iops/ADMIN-GUIDE.md#prepare) |

Case 01 covers approved-host placement, VM separation, an impossible rule,
manual live migration and automatic placement-rule correction. Each test
shows the web console steps, matching CLI commands and the expected result.

Case 02 stops the kubelet on one dedicated worker, lets Node Health Check and
Fence Agents Remediation power-cycle it through its iDRAC, and shows the VM
restarting on a second worker. It is a restart, not a live migration, and not
proof of full hardware failure.

Case 05 measures IOPS, latency and throughput using an existing VM and its existing workload,
or an optional bounded read-only fio workload. PowerFlex measurements are recorded separately;
CSM-exported metrics require an existing installation. The Dell procedure is deferred.

The administrator prepares the cluster and VMs first. Customers then follow
one short walkthrough; detailed operator checks and cleanup stay in the
administrator guide.

The target is OpenShift 4.21.31. Validation boundaries differ by case:

- **Case 01:** CLI validation is complete; that
  does not replace client preflight or presenter UI verification.
- **Case 02:** **fencing NOT TESTED**, and
  its console steps are unverified. It was written from Red Hat 4.21 and upstream
  sources for client bare-metal iDRAC; the installed operator versions and schemas
  govern. It really power-cycles a server, so it needs administrator gates and
  approval first.

Use the [recording outline](test-cases/01-scheduling-and-migration/VIDEO-OUTLINE.md)
for a video and the [results sheet](test-cases/01-scheduling-and-migration/RESULTS-TEMPLATE.md)
to record outcomes. The YAML is generic: agree local worker and storage values
before use. Keep credentials and environment evidence out of this public repository.
