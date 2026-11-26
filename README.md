# OpenShift Virtualization POC tests

Hands-on tests for VMware/vCenter teams learning OpenShift Virtualization.

## Start here

| Test case | Customer walkthrough | Administrator preparation |
| --- | --- | --- |
| 01 — VM placement and migration | **[Run the tests](test-cases/01-scheduling-and-migration/RUNBOOK.md)** | [Prepare the lab](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#prepare) |
| 02 — VM restart after a source worker stops responding (**rehearsed on 4.22**) | **[Run the test](test-cases/02-host-failure-recovery/RUNBOOK.md)** | [Prepare](test-cases/02-host-failure-recovery/ADMIN-GUIDE.md#prepare) |
| 03 — CPU and memory oversubscription (**client validation pending**) | **[Run the test](test-cases/03-cpu-memory-oversubscription/RUNBOOK.md)** | [Prepare](test-cases/03-cpu-memory-oversubscription/ADMIN-GUIDE.md#prepare) and [memory density](test-cases/03-cpu-memory-oversubscription/MEMORY-DENSITY.md) |
| 04 — Network oversubscription (**client validation pending**) | **[Run the test](test-cases/04-network-oversubscription/RUNBOOK.md)** | [Prepare](test-cases/04-network-oversubscription/ADMIN-GUIDE.md#prepare) |
| 05 — Storage IOPS (**client validation pending**; Dell layer **deferred**) | **[Run the test](test-cases/05-storage-iops/RUNBOOK.md)** | [Prepare](test-cases/05-storage-iops/ADMIN-GUIDE.md#prepare) |
| 06 — Add a spare physical worker with CIM (**rehearsed on 4.22**; manual expansion, not autoscaling) | **[Run the test](test-cases/06-cim-worker-expansion/RUNBOOK.md)** | [Prepare](test-cases/06-cim-worker-expansion/ADMIN-GUIDE.md#prepare) |
| 35 — HTPasswd Provider | **[Run the test](test-cases/35-htpasswd-provider/RUNBOOK.md)** | [Prepare](test-cases/35-htpasswd-provider/ADMIN-GUIDE.md#prepare) |

Case 01 covers approved-host placement, VM separation, an impossible rule,
manual live migration and automatic placement-rule correction. Each test
shows the web console steps, matching CLI commands and the expected result.

Case 02 is a source-only pilot: it stops the kubelet on one approved worker, lets
Node Health Check and Fence Agents Remediation power-cycle it through its BMC,
and shows the VM restarting on a separate healthy host. It is a restart, not a
live migration, and not proof of full hardware failure.

Case 06 uses the existing CIM hub to add one spare physical worker to a managed
cluster, then checks the new Ready worker, its capacity and a simple pod. It is a
manual expansion, not autoscaling. The new worker can then be Case 02's source.

Cases 03 and 04 measure one fixed workload while other VMs add CPU, memory or
network demand on the same worker or link. They **prefer existing VMs, unchanged**
(a short suitability checklist, reversible guest tools only); new lab VMs are an
optional fallback. They target 4.21.31, with procedures checked against the 4.21
and 4.22 documentation. Bounded CPU and network console walkthroughs have been
rehearsed on 4.22; client execution and actual oversubscription qualification
remain pending. No ratio is claimed safe. Memory
contention needs a cluster-wide setting and node swap, so it has its own gated
administrator procedure.

Case 05 measures IOPS, latency and throughput using an existing VM and its existing workload,
or an optional bounded read-only fio workload. PowerFlex measurements are recorded separately;
CSM-exported metrics require an existing installation. The Dell procedure is deferred.

Case 35 adds a local HTPasswd login, grants the test user cluster-admin, rotates its
password and removes the demonstration access. It includes console steps, redacted
screenshots and administrator commands.

The administrator prepares the cluster and VMs first. Customers then follow
one short walkthrough; detailed operator checks and cleanup stay in the
administrator guide.

The target is OpenShift 4.21.31. Validation boundaries differ by case:

- **Case 01:** preparation and all five console scenarios have been exercised
  with fresh VMs on alternate shared storage. New **vxflexos / Block / RWX** disk
  provisioning still needs target-cluster validation. Complete client preflight.
- **Case 02:** source-only automatic Redfish fencing, VM restart on a healthy
  destination, source recovery and fixture cleanup exercised on 4.22. A captured
  fence-success event preceded creation of the replacement VMI. Alternate shared
  storage was used; **vxflexos / Block / RWX provisioning remains unverified**.
- **Case 06:** CIM registration, installation, added Ready capacity, a Running
  check pod and check-workload cleanup exercised on 4.22. It starts from an existing CIM
  setup and a spare approved server; it does not demonstrate autoscaling.

- **Case 03:** CPU baseline, bounded competing load, stop checks and recovery
  exercised in the 4.22 web console. Actual CPU oversubscription was not established.
  Memory remains **Blocked** until a dedicated worker-only pool and host-swap
  prerequisites are available; enabling memory density was not exercised.

- **Case 04:** bounded cross-host UDP baseline, competing traffic, stop checks and
  recovery exercised in the 4.22 web console. TCP received only a short connectivity
  check. Physical-link oversubscription and full TCP measurements remain unverified.

- **Case 05:** bounded guest read workload, exact disk mapping, Observe Metrics
  measurements, recovery and fixture cleanup exercised in the 4.22 web console
  on alternate shared storage. The native IOPS-card numerical display remains
  unverified; use the prepared Observe queries. PowerFlex and Dell metrics were
  **Not available / Not run**.

- **Case 35:** console provider setup, first login, cluster-admin access and cleanup
  were exercised on 4.22. Standard `htpasswd` and `oc` file/Secret create, add, rotate
  and remove commands were verified separately on 4.22 using temporary Secrets.
  The 4.21 steps were checked against documentation only. Managed identity sources
  remain unverified.

Use each case's results sheet to record outcomes.
The YAML is generic: agree local worker and storage values
before use. Keep credentials and environment evidence out of this public repository.

New-VM disk templates use **vxflexos / Block / ReadWriteMany (RWX)**. Confirm
the installed storage driver, StorageProfile and image-population path before
creation. Existing-VM paths can keep suitable disks unchanged. Console images
illustrate navigation and may show alternate storage; they do not validate
PowerFlex provisioning. See the [storage preflight](test-cases/01-scheduling-and-migration/ADMIN-GUIDE.md#13-shared-block-storage).
