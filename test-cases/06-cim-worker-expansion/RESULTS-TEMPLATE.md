# Results: add a spare physical worker with CIM

> **Blank results sheet.** Start each new run as **Not run**; enter only results
> observed during that run. Guide rehearsal results do not fill this sheet.

Date: ______   Administrator: ______   ACM/MCE: ______   OCP: ______
Inventory: ______   Workload cluster: ______   Spare host: ______
BMC vendor and address form used: ______   Intended install disk: ______
Owner approval to add, use and retain: ______

**Boundary:** manual expansion, not autoscaling. Fill in the expansion result
right after the check pod is Running (runbook C6), before any optional recovery
test; recovery can remove that pod.

## Final result

| Result | Pass when | Outcome |
| --- | --- | --- |
| **Expansion** | Host registered, approved, assigned as worker; node Ready; worker count and capacity up; check pod Running on it | |
| **Recovery (optional)** | Recorded in the [Case 02 results](../02-host-failure-recovery/RESULTS-TEMPLATE.md) | |

## Readiness check

| Check | Yes / No |
| --- | --- |
| Inventory healthy; workload cluster Ready | |
| Spare host reachable by BMC; vendor-appropriate address form | |
| Owner approval and install disk recorded; all connected disks disposable | |
| Before-counts recorded | |

## Observations

| Step | Expected | Observed |
| --- | --- | --- |
| Register (YAML upload) | Host appears in inventory | |
| Review approval | Host approved or already approved, still unassigned | |
| Assign | Role Worker, correct cluster and install disk | |
| Agent / node | Installed; new node Ready as worker | |
| Check pod | Running on the new worker | |

| Value | Before | After |
| --- | --- | --- |
| Total Ready node count | | |
| Dedicated worker node count | | |
| Total allocatable CPU | | |
| Total allocatable memory | | |

## Cleanup

| Item | Done |
| --- | --- |
| Check pod deleted; project deleted only if created for this run and empty | |
| Worker left installed for the next agreed test | |
| Inventory unchanged | |
