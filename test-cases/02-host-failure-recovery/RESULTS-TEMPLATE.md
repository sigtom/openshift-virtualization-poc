# Results: VM recovery after a host stops responding

> **FENCING: NOT TESTED.** Leave every result **Not run** until the test is
> actually performed on the client cluster. Keep completed copies and raw
> evidence private. Use **Pass**, **Fail**, **Blocked** or **Not run**.
> Missing fence evidence is **Blocked**, never Pass.

Date: ______   Customer: ______   Administrator: ______
OCP: ______   Virtualization: ______   FAR operator: ______   NHC operator: ______
SOURCE: ______   TARGET: ______
Abort rule, outage budget and escalation contact (test limits, not a recovery-time claim): ______

## Final results (record separately)

| Result | Pass when | Outcome |
| --- | --- | --- |
| **VM restart** | Every observation below passes, including captured fence order and iDRAC corroboration | |
| **Host return** | SOURCE Ready; remediation object gone; remediation and out-of-service taints cleared; NHC cleanup done before re-pause | |

## Observations

| Check | Expected | Web console | CLI | Notes |
| --- | --- | --- | --- | --- |
| Start | VM Running on SOURCE | | | |
| Pool, paused | Two Ready worker nodes by direct `get nodes`; `pauseRequests` set (counts ignored) | | | |
| Cordon | SOURCE unschedulable and Ready | | | |
| Activation | NHC Enabled, observed 2, healthy 2, before fault | | | |
| Fault | Kubelet stopped by administrator over SSH (no console equivalent) | n/a | | |
| Remediation | NHC Remediating, healthy 1; FAR created for SOURCE | | | |
| Fence | `FenceAgentActionSucceeded` true; SOURCE power-cycled | | | |
| Recovery | VM Running on TARGET, no manual step | | | |
| Duplicate | One instance of the VM at any time | | | |
| Manual action needed? | No (any manual recovery = Fail) | | | |

## Evidence

| Value | Before | After |
| --- | --- | --- |
| Node hosting VM | | |
| VM instance UID | | |
| Guest boot ID | | |
| Persist token | | |
| Heartbeat | | |
| SOURCE node boot ID | | |

| Captured ordering evidence | Value |
| --- | --- |
| Capture files saved privately outside the checkout (far, vmi, nodes) | |
| FAR `FenceAgentActionSucceeded` true `lastTransitionTime` (from capture) | |
| New VMI UID and `creationTimestamp` (from capture) | |
| Fence time earlier than new VMI creation? | |
| iDRAC event log shows SOURCE power-cycle (time) | |
| Elapsed fault → VM Running (observed only) | |

## Administrator sign-off

| Gate | Confirmed / evidence |
| --- | --- |
| Operator versions recorded; schema checked; server dry-runs run | |
| No overlapping NHC / MHC / Machine auto-remediation (full selectors read); nothing existing modified | |
| Two worker-only Ready nodes labelled; none is control plane; N+1 capacity | |
| Namespace created before disk; agreed Block/Filesystem RHEL 9 PVC dedicated, storage failover validated | |
| Node → BMC mapping matched read-only (UUID) for both nodes | |
| BMC certificate trusted by the installed agent for both nodes; no `--ssl-insecure` | |
| Secrets created from private files; no credentials in repo, argv or history | |
| Kubelet enabled and active before the fault | |
| NHC Disabled condition False while paused | |
| After activation: Enabled, 2 observed / 2 healthy, SOURCE cordoned and Ready, before fault | |
| Evidence capture running before the fault; kept private | |
| Surviving Ready NHC/FAR controller replicas off SOURCE; shared storage intact; BMC reachable | |
| FAR object gone, SOURCE Ready, remediation taints cleared, **then** paused | |
| Cordon removed only if owned; cleanup kept PVC, operators and namespaces | |
