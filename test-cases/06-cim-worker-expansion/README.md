# Test 06: add a spare physical worker with CIM

> **Status: expansion verified on 4.22.** Registration, installation,
> added Ready capacity, a Running check pod and check-workload cleanup were exercised.
> The 4.21 procedure was documentation-reviewed; this remains manual expansion.

For teams used to adding ESXi hosts to a vSphere cluster. Using the existing
Central Infrastructure Management (CIM) hub, you add one spare physical server
through its BMC, review its approval and disks, assign it to a managed workload cluster as a
worker, and confirm the cluster gained a Ready worker and its capacity. A
simple pod then runs on it.

**This is a manual expansion that you start.** It is not policy- or
load-triggered autoscaling, and it does not show the cluster expanding by itself.

Afterwards the new worker can be the SOURCE in
[Case 02](../02-host-failure-recovery/RUNBOOK.md): automatic Redfish recovery of
that worker and a test VM restarting elsewhere. Node recovery and VM restart are
separate outcomes there.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Run the test | **[Runbook](RUNBOOK.md)** (prepare, one readiness check, test, clean up) |
| Cluster administrator | [Commands and safety details](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Starting point (pre-existing, not part of this test)

- ACM/MCE with CIM configured, and a managed workload cluster.
- An unassigned host-inventory InfraEnv, reused unchanged when suitable.
  The runbook includes an optional separate-inventory procedure.
- A spare approved server with BMC access and only disposable disks connected.
  Disconnect disks or unpresent SAN LUNs with data or another OS to preserve.

Without spare hardware, review the procedure and record **Not run**. Removing
and re-adding an existing node does not demonstrate extra cluster capacity.

Official reference: [ACM 2.16 — Clusters](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.16/html-single/clusters/index).

## Files

| File | Purpose |
| --- | --- |
| `manifests/00-namespace.yaml` | Project for the check pod (workload cluster) |
| `manifests/01-worker-check-pod.yaml` | Small pod pinned to the new worker (fill the node name) |
| `manifests/02-baremetalhost-paused.yaml` | Host registration with cleaning disabled, initially paused |
| `manifests/03-unassigned-inventory.yaml` | Optional inventory using an existing approved pull Secret |

Apply only the file a step names. No Secret YAML is shipped; BMC credentials are
entered privately.

## Boundaries

- Expansion was rehearsed on 4.22; target-cluster execution is still required.
- Disk preservation was not established: an unchecked Format box and disabled
  BMH cleaning do not guarantee other boot records remain untouched.
- Keep credentials, environment addresses and completed results private. Guide images are redacted.
- Dell servers use the `idrac-virtualmedia` BMC address form, not the generic Redfish one.
