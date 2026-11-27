# Results: CPU and memory oversubscription

> **NOT TESTED.** Leave every result **Not run** until performed on the client
> cluster. Use **Pass**, **Fail** (including an aborted run), **Blocked** or **Not run**. A missing
> prerequisite is **Blocked**, never Pass. Keep completed copies private.

Date: ______   Customer: ______   Administrator: ______
OCP: ______   Virtualization: ______   Test worker: ______
Approved by (Red Hat / client) and date: ______   Abort rule and contact: ______
Warm-up ____ s   Measure ____ s   Repeats ____ (proposal 300 / 900 / 3)
Required memory result: performance comparison under assigned guest RAM above physical RAM (VM paging is recorded as an observation, not a pass condition): ______
Record allocation overcommit, VM paging and performance validity separately.

## VMs used (as found; do not change them)

Path used: **A existing VMs / B lab VMs**. Memory phase VMs (if different from the CPU VMs): ______ (their own baseline, loaded and recovery rows below).   Owner permission and window: ______

| Role | VM and project | vCPU (sockets × cores × threads) | Guest RAM | Worker | Tools and versions | OS |
| --- | --- | --- | --- | --- | --- | --- |
| Measured | | | | | | |
| Competitor 1 | | | | | | |
| Competitor 2 | | | | | | |

Changes made to any VM or guest (tools added, anything else) and how they were undone: ______

## Host capacity (test worker only, never averages)

| Item | Value |
| --- | --- |
| Logical CPUs / physical cores / threads per core | |
| Allocatable CPU / allocatable memory | |
| Kubelet node-available / pod-available memory; sample time and stop floor for each | |
| Running-VM vCPU: baseline / CPU phase / memory phase | |
| vCPU : logical CPU and vCPU : physical core, per phase | |
| Pod CPU requests and pod memory requests, per phase | |
| VMs Running per phase (baseline / loaded / recovery) and who changes their power state | |
| Guest configured RAM (sum), per phase (for example baseline 4 GiB / loaded 284 GiB / recovery 4 GiB) | |
| **Actual assigned ratio** per phase, with its denominator (physical / OS-visible / allocatable); the HCO setting is not this ratio | |
| **Admission ratio:** total running guest RAM ÷ installed physical RAM, per memory step (assigned, not resident) | |
| Other ratios, if used: guest RAM ÷ OS-visible RAM; pod requests ÷ allocatable (label each separately) | |
| Installed RAM / OS-visible RAM / allocatable memory | |
| Measured VMI `metadata.uid`, node and resources (same for all 9 runs; restart or migration = invalid). Competitor VMI ids may differ between phases | |
| Actual launcher memory request, reduced guest-memory component, overhead and node allocatable (as measured) | |
| Actual launcher QoS class; cgroup swap allowance (`memory.swap.max`) and `memory.swap.current` | |
| Guest swap as found, per VM (on/off, size; not changed on reused VMs) | |
| Competitor count and how it was derived; approved ratio | |
| HCO CPU allocation ratio / density setting (read-only; a setting, **not** the admission ratio above) | |

## Memory prerequisites

| Prerequisite | Confirmed |
| --- | --- |
| Source used: OpenShift Virtualization section *Configuring higher VM workload density* (installed version, page date) | |
| Release-specific documentation checked; any Red Hat clarification received | |
| HyperConverged API version pinned; original density value (parent / value) | |
| Test node's actual MachineConfigPool and node list (not the worker label alone); worker-only; no control plane | |
| Initial cordon, taints and labels of the test node (recorded before any change); temporary taint added/removed; final cordon state | |
| Swap configured vs documented formula value (RAM × (density ÷ 100% − 1)); bounded demonstration or full ratio | |
| `wasp-agent` pod Ready on the test node (not only the DaemonSet rollout) | |
| New fixture VMs: namespace, disk created by VM or by administrator (DataVolume/PVC Ready) | |
| Optional prepared image: DataVolume, DataSource, PVC name and UID, source PVC, storage class/mode used (NFS rehearsal does not qualify vxflexos) | |
| Swap storage: backing disk, filesystem, free space, file path and storage owner approval | |
| Swap size and headroom (from the approver) | |
| New rendered MachineConfig name, and node running it (`currentConfig`, state Done) | |
| Cluster-wide effect (HCO setting and `wasp-agent`) approved by owner | |
| `stress-ng --vm-hang 0` verified on installed build (version, observed behaviour) | |
| Restoration record written before change; restored and verified after | |
| **Memory phase result** | Pass / Fail (aborted) / **Blocked** / Not run |

## Memory ramp (one row per step; values come from the approver, not this form)

Record admission, VM paging and workload performance separately. VM paging is **Observed**,
**Not observed** (zero swap with good metrics) or **Blocked** (feature or metrics unavailable).
Resident payload, node working set, guest swap and host swap are separate observations.

| Step | Guests holding / bytes each / duration | Memory actually touched (guest used; launcher working set) | Admission: guest RAM ÷ physical | Holds active before and after each repeat? | VM paging: Observed / Not observed / Blocked (node swap-out rising? launcher swap > 0?) | Measured-VM memory result | Stop rule hit? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | |
| 2 | | | | | | | |

Stop thresholds (swap-used limit, kubelet node-available floor, kubelet pod-available floor, Linux available-memory floor, I/O-wait limit and sample period, off-node missing-sample limit, hold bytes): ______
Ramp VM background holds (pid, bytes, timeout, start/stop time, still matching command?): ______
Residual swap after release: cold pages only / sustained swap I/O during a measurement: ______
Hold duration = remaining ramp + settle + (warm-up + measure) × repeats + margin: ______ s
A repeat with an expired hold is invalid; mark it in the measured-workload table.
First step with attributable host swap (or "none"): ______   Stopped at planned safe headroom? ______   Abort used? ______

## Measured workload

Record one row per workload, phase, load level and repetition. Copy rows as needed.
Compare CPU results with the CPU baseline, memory results with the memory baseline,
and application results with the same application baseline.

| Phase / load level | Workload and exact command | Repeat | Start UTC | End UTC | Throughput and unit | Latency avg / p95 / max (ms) | Log / graph reference | Invalid? Why |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | CPU | 1 | | | events/s | | | |
| Baseline | Memory | 1 | | | MiB/s | | | |
| CPU contention | CPU | 1 | | | events/s | | | |
| Memory contention | Memory | 1 | | | MiB/s | | | |
| Recovery | CPU | 1 | | | events/s | | | |
| Recovery | Memory | 1 | | | MiB/s | | | |

For an agreed application workload, also record its data size, users/concurrency,
throughput (for example HammerDB NOPM) and p95/p99 latency if reported. Synthetic
CPU and memory bandwidth results do not establish application performance.

## Host and VM signals per phase (from the verified queries)

| Signal | Baseline | CPU | Memory | Recovery |
| --- | --- | --- | --- | --- |
| Host CPU busy; CPU pressure / throttling (if available) | | | | |
| Guest steal / vCPU wait | | | | |
| Host memory available; working set vs guest RAM | | | | |
| Memory pressure; swap used; swap in/out; major faults | | | | |
| OOM kills, evictions, restarts, **migrations** (any = invalid run) | | | | |
| Series not available on this version | | | | |

## Final results

| Result | Outcome | Notes |
| --- | --- | --- |
| Baseline stable (repeats agree) | | |
| CPU contention effect observed / not observed | | |
| Memory contention effect observed / not observed / Blocked | | |
| VM paging Observed / Not observed / Blocked (separate from performance) | | |
| Loaded runs valid: stable agreed load, safe headroom, no eviction, OOM, restart or migration | | |
| Recovery returns to baseline | | |
| Restored every shared setting changed | | |
