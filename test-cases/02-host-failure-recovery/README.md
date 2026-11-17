# Test 02: VM recovery after a host stops responding

> **FENCING LAB: NOT TESTED.** Written for client bare-metal hosts with iDRAC.
> Not run in our lab or on the client cluster; console steps are unverified.
> Complete administrator preparation first, then sign the pre-fault gates in
> the walkthrough's order.

For VMware/vCenter teams comparing this with vSphere HA host-failure restart.

An administrator stops the kubelet on one dedicated worker (a single,
reversible service failure, **not** proof of full hardware failure). The Node
Health Check Operator notices, the Fence Agents Remediation Operator
power-cycles the worker through its iDRAC (Redfish), and the VM restarts on a
second worker. The VM is **restarted, not live-migrated**: expect an outage and
no recovery-time promise.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** |
| Cluster administrator | [Prepare, gate and clean up](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## The scenario

- **Two dedicated worker-only nodes** (SOURCE and TARGET), never control plane,
  labelled `host-recovery-lab.example.com/pool=case02`.
- One small RHEL VM in its own project, on an administrator-approved PVC that
  both nodes can use.
- A NodeHealthCheck for only those two nodes, **shipped paused** and activated
  only after every gate.
- `fence_redfish` with action `reboot`; credentials live only in local Secrets.

## Files

| File | Purpose |
| --- | --- |
| `manifests/00-namespace.yaml` | Project for the VM (reuse if approved) |
| `manifests/00a-subscription-fence-agents-remediation.yaml` | FAR subscription, only if FAR is missing |
| `manifests/00b-subscription-node-health-check.yaml` | NHC subscription, only if NHC is missing |
| `manifests/01-far-template.yaml` | Fence agent template (fill in `REPLACE_*`) |
| `manifests/02-nhc-paused.yaml` | Paused health check for the pool |
| `manifests/03-recovery-vm.yaml` | Sample VM (starts Halted) |

Apply only the file a step names, never the whole folder. Use the
[server dry-run commands](ADMIN-GUIDE.md#dry-run) first (not yet performed).

## Boundaries

- Target OpenShift **4.21.31**; the **installed operator versions and CRD
  schemas govern**. Field names were read from pinned upstream reference versions
  (FAR v0.8.0, NHC v0.12.0) and the Red Hat 4.21 docs, not an installed cluster;
  see [reference sources](ADMIN-GUIDE.md#reference-sources).
- Needs N+1 capacity, shared storage that stays intact, and BMCs that stay
  reachable. Existing VMs on SOURCE must be disposable and approved.
- Public repository: no credentials, hostnames or evidence. Keep completed
  results private.
