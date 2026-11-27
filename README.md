# OpenShift Virtualization POC tests

Hands-on tests for VMware/vCenter teams learning OpenShift Virtualization.

## Start here

| Test case | Walkthrough | Administrator preparation |
| --- | --- | --- |
| 01 — VM placement and migration | **[Run the tests](test-cases/01-scheduling-and-migration/RUNBOOK.md)** | [Prepare the lab](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#prepare) |
| 02 — VM restart after a source worker stops responding (**rehearsed on 4.22**) | **[Run the test](test-cases/02-host-failure-recovery/RUNBOOK.md)** | [Prepare](test-cases/02-host-failure-recovery/ADMIN-GUIDE.md#prepare) |
| 03 — CPU and memory oversubscription (**client validation pending**) | **[Run the test](test-cases/03-cpu-memory-oversubscription/RUNBOOK.md)** | [Prepare](test-cases/03-cpu-memory-oversubscription/ADMIN-GUIDE.md#prepare) and [memory density](test-cases/03-cpu-memory-oversubscription/MEMORY-DENSITY.md) |
| 04 — Network oversubscription (**client validation pending**) | **[Run the test](test-cases/04-network-oversubscription/RUNBOOK.md)** | [Prepare](test-cases/04-network-oversubscription/ADMIN-GUIDE.md#prepare) |
| 05 — Storage IOPS (**client validation pending**; Dell layer **deferred**) | **[Run the test](test-cases/05-storage-iops/RUNBOOK.md)** | [Prepare](test-cases/05-storage-iops/ADMIN-GUIDE.md#prepare) |
| 06 — Add a spare physical worker with CIM (**rehearsed on 4.22**; manual expansion, not autoscaling) | **[Run the test](test-cases/06-cim-worker-expansion/RUNBOOK.md)** | [Prepare](test-cases/06-cim-worker-expansion/ADMIN-GUIDE.md#prepare) |
| 35 — HTPasswd login | **[Run the test](test-cases/35-htpasswd-provider/RUNBOOK.md)** | [Prepare](test-cases/35-htpasswd-provider/ADMIN-GUIDE.md#prepare) |

Case 01 covers approved-host placement, VM separation, an impossible rule, a
live migration you request, and automatic placement-rule correction. The full
result needs both migrations. Each test shows the web console steps, matching
CLI commands and the expected result.

Case 02 stops the kubelet (the node's agent) on one approved worker. Node Health
Check and Fence Agents Remediation then power-cycle that worker through its BMC,
and the VM restarts on a separate healthy host. It is a restart, not a live
migration, and not proof of full hardware failure.

Case 06 uses the existing CIM hub to add one spare physical worker to a managed
cluster, then checks the new Ready worker, its capacity and a simple pod. It is a
manual expansion, not autoscaling. The new worker can then be Case 02's source.

Cases 03 and 04 measure one fixed workload while other VMs add CPU, memory or
network demand on the same worker or link. They **prefer existing VMs, unchanged**:
a short suitability checklist, and guest helper commands copied in only if
missing. New lab VMs are an optional fallback. No ratio is claimed safe. The optional host-memory overcommit phase needs the memory-density setting
and node swap. Follow the linked memory-density procedure before running it.

Case 05 measures IOPS, latency and throughput using an existing VM and its existing
workload, or an optional bounded read-only fio workload. PowerFlex measurements are
recorded separately and need an existing Dell installation; that procedure is deferred.

Case 35 adds a local HTPasswd login, makes it a cluster administrator, changes its
password and removes the test access, in one walkthrough.

The administrator prepares the cluster and VMs first. Participants then follow
one walkthrough; detailed checks, recovery and cleanup notes stay in the
administrator guide.

## Tools

The YAML files install nothing inside a VM. Guest tools (`sysbench`, `stress-ng`,
`iperf3`, `fio`) and the small `poc-*` helper commands are prepared separately by the
administrator: either in an approved VM image, or added to an existing VM through the
owner's package route and by copying the helpers from the case's `guest-tools/` folder.
Each case's administrator guide shows how. Administrator commands use standard `oc`,
`jq` and Linux tools on a jump host.

## Status

The target is OpenShift 4.21. The rehearsals below ran on OpenShift 4.22, mostly
on alternate shared storage. None of them proves the client's 4.21 cluster or its
storage.

- **Case 01:** preparation and all five console scenarios were exercised with fresh
  VMs on alternate shared storage. New **vxflexos / Block / RWX** disks still need
  target-cluster checks.
- **Case 02:** automatic Redfish fencing of one source worker, VM restart on a healthy
  destination and source recovery were exercised. A captured fence-success event came
  before the replacement VM instance was created. After the **latest** run, cleanup was
  held for review; an earlier rehearsal completed fixture cleanup. Alternate shared
  storage was used.
- **Case 03:** CPU baseline, time-limited competing load, stop checks and recovery were
  exercised. Actual CPU oversubscription was not established. Memory preparation,
  swap activation across boots, guest-RAM admission overcommit and three memory
  baselines were exercised. The latest ramp was aborted by a pod-allocation memory
  eviction before test-VM paging was observed. Loaded and recovery memory benchmarks
  were not completed; no safe ratio is established.
- **Case 04:** a bounded cross-host UDP baseline, competing traffic, stop checks and
  recovery were exercised. TCP had only a short connectivity check. Physical-link
  oversubscription and full TCP measurements remain unverified.
- **Case 05:** a guest read workload capped at 100 IOPS, exact disk mapping, Observe Metrics
  measurements, recovery and fixture cleanup were exercised. The native IOPS card's
  numbers remain unverified; use the prepared Observe queries. PowerFlex and Dell
  metrics were **Not available / Not run**.
- **Case 06:** CIM registration, installation, added Ready capacity and a Running check
  pod were exercised with a 4.21 hub. After the **latest** run, cleanup was held for
  review; an earlier rehearsal removed its check workload. It starts from an existing
  CIM setup and a spare approved server; it does not show autoscaling.
- **Case 35:** provider setup, first login, native password update, cluster-admin access,
  new-password login, old-password refusal and scoped cleanup were exercised with a
  temporary test account. Reusing an existing provider remains unverified.

For the other cases, later command changes were checked with sample data and limited server dry-runs
(validation without saving changes). The complete cluster tests have not been repeated.

Use each case's results sheet to record outcomes. Keep credentials, filled-in YAML
copies and environment evidence out of this repository.

## Storage terms

New-VM disk templates use **vxflexos / Block / ReadWriteMany (RWX)**:

- **vxflexos** is the StorageClass name of the Dell PowerFlex CSI driver.
- **Block** gives the VM a raw disk device rather than a file on a filesystem.
- **ReadWriteMany (RWX)** lets two hosts attach the same disk at once, which live
  migration and a restart on another host need.
- A **PVC** (persistent volume claim) is the request for a VM disk; a **DataVolume**
  fills it from an image.

Confirm the installed storage driver, its StorageProfile and the image copy path before
creating new VMs. Existing-VM paths keep their current disks unchanged. Console pictures
show navigation and may show alternate storage; they do not validate PowerFlex. See the
[storage preflight](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#13-shared-block-storage).
