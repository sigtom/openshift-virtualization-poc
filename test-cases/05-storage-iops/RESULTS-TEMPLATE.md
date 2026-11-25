# Results: storage IOPS

> **NOT TESTED.** Leave results **Not run** until performed. Use **Pass**, **Fail**, **Blocked**,
> **Not run** or **Not available**. The native case is Pass only if **every agreed required layer** has
> its evidence; a missing required layer is Blocked / Not run. An unavailable **optional** layer (Dell) is
> recorded separately and does not affect the native result. Keep completed copies private.

Date: ____   Customer: ____   Administrator: ____   OCP / Virtualization: ____
Approved by and date: ____   Max IOPS cap: ____   Abort rule and contact: ____

## Mapping (private)

| Item | Value |
| --- | --- |
| VM / project | |
| Directory and filesystem under test; root disk? (OS background I/O) | |
| Guest device and serial (or verified VMI target mapping) | |
| VM disk name (`drive` label) / PVC / PV | |
| CSI driver / volumeHandle | |
| Backend volume (Dell layer) | Not run |

## Workload

Existing application / `poc-fio`: ____   Pattern: ____   Block size: ____   Queue depth: ____
Fixture size: ____ (written once by prepare)   Cap: ____ IOPS   Warm-up ____ s  Measure ____ s  Repeats ____
Changes to VM/guest and how undone: ____

Prepared Observe links: IOPS ____   Throughput ____   Latency ____

## Measurements

| Phase / repeat | Start UTC | End UTC | Guest IOPS | Guest KiB/s | Guest clat mean / p95 / p99 (ms) | VM-metric IOPS | VM-metric KiB/s | VM-metric read/write latency (ms) | Notes / invalid? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline idle | | | | | | | | | |
| Workload 1 | | | | | | | | | |
| Workload 2 | | | | | | | | | |
| Workload 3 | | | | | | | | | |
| Recovery idle | | | | | | | | | |

Queries saved (private location): ____   Series with no data (record as not available, never 0): ____
Scrape interval: ____   Rate window used: ____ (default 2m, at least 4 intervals)

The table above records the guest phase windows. Record each VM query's actual
window below; the default final two minutes lie **inside** the guest's three-minute
measurement. Compare trends, not identical-window arithmetic.

| Phase / repeat | VM query evaluation UTC | Rate window start/end UTC | Samples inside window | Saved query and returned series reference |
| --- | --- | --- | --- | --- |
| Baseline idle | | | | |
| Workload 1 | | | | |
| Workload 2 | | | | |
| Workload 3 | | | | |
| Recovery idle | | | | |

Native card discrepancy or missing display (if any): ____

## Layers

Required layers agreed before the run (tick): [ ] guest workload  [ ] VM disk metrics  [ ] other: ____

| Layer | Required / optional | Outcome | Mapping unambiguous? | Notes |
| --- | --- | --- | --- | --- |
| Guest workload | | | | |
| VM disk metrics | | | | |
| Dell PowerFlex (deferred; CSM needed only for exported metrics) | Optional | Not run / Not available | | Recorded separately |

## Final

| Result | Outcome |
| --- | --- |
| Native case (**Pass only if every required layer above has evidence**; otherwise Blocked / Not run) | |
| Optional layers (separate; do not change the native result) | |
| Fixture removed; helper disposition recorded; existing VM unchanged | |
