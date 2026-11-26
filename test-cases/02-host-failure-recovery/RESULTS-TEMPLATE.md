# Results: VM restart after a source worker stops responding

> **Blank results sheet.** Start each new run as **Not run**; enter only results
> observed during that run. Guide rehearsal results do not fill this sheet.

Date: ______   Administrator: ______
OCP: ______   Virtualization: ______   FAR operator: ______   NHC operator: ______
SOURCE: ______   TARGET: ______   VM (reused or disposable): ______
Approved destination hosts: ______   Actual destination after recovery: ______
Abort rule and escalation contact (test limits, not a recovery-time claim): ______

## Final results (record separately)

| Result | Pass when | Outcome |
| --- | --- | --- |
| **VM restart** | VM restarts on an approved healthy destination as a new VMI with captured fence order and BMC corroboration | |
| **Node recovery** | SOURCE Ready; remediation object gone; remediation and out-of-service taints cleared; NHC cleanup done before re-pause | |

## Readiness check (all yes before the fault)

| Check | Yes / No |
| --- | --- |
| Exactly one node matches the selector and it is SOURCE; TARGET unlabelled and not in the template | |
| All other nodes Ready; TARGET has room; shared vxflexos / Block / RWX storage reachable | |
| NHC and FAR controllers Ready on nodes other than SOURCE | |
| No overlapping NHC / MHC / remediation | |
| Health check paused, Disabled condition False; kubelet on SOURCE enabled and active | |
| VM Running on SOURCE | |

## Observations

| Check | Expected | Web console | CLI | Notes |
| --- | --- | --- | --- | --- |
| Cordon | SOURCE unschedulable and Ready | | | |
| Activation | NHC Enabled, observed 1, healthy 1, before fault | | | |
| Fault | Kubelet stopped over SSH (no console equivalent) | n/a | | |
| Remediation | NHC Remediating (observed 1, healthy 0); remediation for SOURCE | | | |
| Fence | `FenceAgentActionSucceeded` true; SOURCE power-cycled | | | |
| Recovery | New VMI Running on an approved healthy destination, no manual step | | | |
| Duplicate | One instance at any time | | | |
| Manual action needed? | No (any manual recovery = Fail) | | | |

## Evidence

| Value | Before | After |
| --- | --- | --- |
| Node hosting VM | | |
| VMI UID | | |
| SOURCE node boot ID | | |
| Optional guest note | | |

| Captured ordering evidence | Value |
| --- | --- |
| Capture files saved privately (far, vmi, nodes) | |
| Fence success time vs. new VMI creation time | |
| BMC event log shows SOURCE power-cycle (time) | |
| Elapsed fault to VM Running (observed only) | |

## Cleanup

| Item | Done |
| --- | --- |
| Health check paused after outcome; evidence kept | |
| SOURCE uncordoned when healthy (if owned) | |
| Owned VM, label, template, Secret removed; operators and shared objects kept | |
