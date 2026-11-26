# Test 02: VM restart after a source worker stops responding

> **Status: recovery and cleanup verified on 4.22.** Automatic Redfish fencing,
> a new VM instance on a healthy destination, source-node recovery and fixture
> cleanup were exercised. The 4.21 procedure was documentation-reviewed;
> **vxflexos / Block / RWX provisioning remains unverified**.

For VMware/vCenter teams comparing this with vSphere HA host-failure restart.

An administrator stops the kubelet on **one** approved worker (SOURCE). Node
Health Check notices, Fence Agents Remediation automatically power-cycles
SOURCE through its BMC (Redfish), and the VM is interrupted and restarts on a
separate healthy host (TARGET) as a new instance. The VM is **restarted, not
live-migrated**, and no outage time is promised. A stopped kubelet is not proof of
full hardware failure.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Run the test | **[Runbook](RUNBOOK.md)** (prepare, one readiness check, test, clean up) |
| Cluster administrator | [Commands and safety details](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

This case can follow [Case 06](../06-cim-worker-expansion/RUNBOOK.md), using the
newly added worker as SOURCE.

## The scenario

- **SOURCE:** one approved non-control-plane worker with the label
  `host-recovery-lab.example.com/source=case02`. It is the only node the health
  check selects (`maxUnhealthy: 1`, no `minHealthy`).
- **TARGET:** a separate healthy virtualization host, outside the selector,
  never labelled, fenced or faulted. The scheduler may choose another approved
  healthy destination; record the actual host.
- **VM:** an existing approved VM reused unchanged if it fits and runs on SOURCE;
  otherwise a disposable VM. Client VM storage stays **vxflexos / Block / RWX**.
- The health check ships **paused**; credentials live only in a local SOURCE Secret.

## Files

| File | Purpose |
| --- | --- |
| `manifests/00-namespace.yaml` | Project for the VM (reuse if approved) |
| `manifests/00a-subscription-fence-agents-remediation.yaml` | FAR subscription, only if FAR is missing |
| `manifests/00b-subscription-node-health-check.yaml` | NHC subscription, only if NHC is missing |
| `manifests/01-far-template.yaml` | Fence agent template, SOURCE only (fill `REPLACE_*`) |
| `manifests/02-nhc-paused.yaml` | Paused source-only health check |
| `manifests/03-recovery-vm.yaml` | Disposable VM, only if none fits (starts Halted) |

Apply only the file a step names, never the whole folder.

## Boundaries

- Target OpenShift **4.21.31**; installed operator versions and CRD schemas
  govern. The recovery rehearsal used alternate shared storage and does not
  validate the target storage driver.
- Needs surviving Ready nodes with spare capacity, shared storage that stays
  intact, NHC and FAR controllers running off SOURCE, and a BMC that stays reachable.
- Public repository: no credentials, hostnames or evidence. Keep completed
  results private.
