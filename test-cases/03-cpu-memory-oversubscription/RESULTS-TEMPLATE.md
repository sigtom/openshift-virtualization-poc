# Results: CPU and memory oversubscription

> **NOT TESTED.** Leave every result **Not run** until performed on the client
> cluster. Use **Pass**, **Fail**, **Blocked** or **Not run**. A missing
> prerequisite is **Blocked**, never Pass. Keep completed copies private.

Date: ______   Customer: ______   Administrator: ______
OCP: ______   Virtualization: ______   Test worker: ______
Approved by (Red Hat / client) and date: ______   Abort rule and contact: ______
Warm-up ____ s   Measure ____ s   Repeats ____ (proposal 300 / 900 / 3)

## VMs used (as found; do not change them)

Path used: **A existing VMs / B lab VMs**.   Owner permission and window: ______

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
| Running-VM vCPU: baseline / CPU phase / memory phase | |
| vCPU : logical CPU and vCPU : physical core, per phase | |
| Pod CPU requests and pod memory requests, per phase | |
| Guest configured RAM (sum), per phase | |
| Competitor count and how it was derived; approved ratio | |
| HCO CPU allocation ratio / density setting (read-only) | |

## Memory gate

| Prerequisite | Confirmed |
| --- | --- |
| Red Hat-approved swap mechanism for this version (name, reference) | |
| Limited to isolated workers; exact configuration saved privately | |
| Restoration record written before change; restored and verified after | |
| **Memory phase result** | Run / **Blocked** |

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
| Recovery returns to baseline | | |
| Restored every shared setting changed | | |
