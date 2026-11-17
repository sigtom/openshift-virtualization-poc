# Results: VM placement and migration

Keep completed copies and raw environment evidence private. Use **Pass**,
**Fail**, **Blocked** or **Not run** for each result. A CLI pass does not verify
the web console.

Date: ______   Presenter: ______   Administrator: ______
OCP: ______   Virtualization: ______   Descheduler operator: ______

## Customer observations

| Test | Expected result | Web console result | CLI result | Evidence / notes |
| --- | --- | --- | --- | --- |
| 1. Approved host | placement-01 starts on Worker A | | | |
| 2. Separation | Three spread VMs use three approved workers | | | |
| 3. Impossible rule | negative-01 stays unscheduled; FailedScheduling appears | | | |
| 4. Manual move — optional | Person-requested migration succeeds to Worker B | | | |
| 5. Predictive | Node-affinity candidate appears; VM stays on SOURCE | | | |
| 5. Automatic | Node-affinity request causes a new cluster-created migration to TARGET | | | |
| 5. Continuity | Same boot and running-instance IDs; uptime increases; VM healthy | | | |
| CPU-load balancing | Outside this walkthrough | Not run | Not run | Optional separate evaluation |

## Automatic-migration evidence

| Value | Before | After |
| --- | --- | --- |
| Worker | | |
| VM UID | | |
| Running-instance (VMI) UID | | |
| Guest boot ID | | |
| Guest uptime and observation time | | |
| Automatic migration name / phase | No new automatic migration | |

## Administrator sign-off

| Required checkpoint | Confirmed / evidence |
| --- | --- |
| Preflight complete on this cluster: versions/APIs, source capacity, storage, permissions, nodes and ownership | |
| Exclusive lab namespace and PriorityClass identities recorded; VM disks prepared | |
| Actual placement launcher priority/class and Ready/LiveMigratable/AgentConnected verified | |
| Original shared-descheduler configuration saved before editing | |
| Predictive: background evictions, both priority filters, namespace handling, limits and HCO health verified | |
| Immediately before Automatic: full priority and force-annotation inventories repeated; lab pods checked | |
| Automatic move attributed to RemovePodsViolatingNodeAffinity; no manual request substituted | |
| Returned to Predictive immediately after success or stop condition; dry-run mode verified | |
| Original shared settings restored with guarded readback, or newly created CR removed with UID check | |
| Lab reset or cleanup completed; retained storage handled according to reclaim policy | |
