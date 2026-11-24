# Results: network oversubscription

> **NOT TESTED.** Leave every result **Not run** until performed on the client
> cluster. Use **Pass**, **Fail**, **Blocked** or **Not run**. Missing prerequisites
> are **Blocked**, never Pass. Keep completed copies private.

Date: ______   Customer: ______   Administrator: ______
OCP: ______   Virtualization: ______
Approved by and date: ______   Max offered load approved: ______   Abort rule and contact: ______
Warm-up ____ s   Measure ____ s   Repeats ____ (proposal 300 / 900 / 3)

## VMs and layout (as found; do not change them)

Path used: **A existing VMs / B lab VMs**.   Owner permission and window: ______

| Role | VM and project | vCPU / RAM | Worker | Address used (Pod IP, or other) |
| --- | --- | --- | --- | --- |
| Measured server | | | | |
| Measured client | | | | |
| Competitor server(s) | | | | |
| Competitor client(s) | | | | |

Layout: **same-host control / cross-host / external**.   Address kind (same in every run): ______
Changes made to any VM or guest, and how undone: ______

## Network facts (admin)

| Item | Value |
| --- | --- |
| CNI / cluster network and MTU; guest MTU | |
| NIC model and rate per test node; bond mode and hash policy | |
| Switch topology, uplink rate, switch oversubscription | |
| **Shared bottleneck** (or "control only") and its rate | |
| NetworkPolicy / firewall handling (ports opened, by whom, undone) | |

## Measured flow (same command every phase)

Record one row per protocol, load level and repetition; copy rows as needed.

| Load level | Protocol / exact command | Competitor flows × rate | Repeat | Start UTC | End UTC | Receiver Mbit/s | Sender Retr | RTT min/avg/max | UDP offered rate / loss / jitter | Log / graph reference | Invalid? Why |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | TCP | none | 1 | | | | | | | | |
| 1 | TCP | | 1 | | | | | | | | |
| 2 | TCP | | 1 | | | | | | | | |
| Recovery | TCP | none | 1 | | | | | | | | |

Record TCP reverse and UDP in separate rows with their own baseline and recovery.

Application throughput and p95/p99 latency, if an existing application is used (dataset,
version and concurrency frozen): ______ (**not reported** if it cannot report them).

## Link and host signals (each transfer counted once, per link, not cluster averages)

| Level | Link total (sum of receivers) vs link rate | NIC drops / errors | Host TCP retransmits | Generator VM CPU | Migrations / restarts / events |
| --- | --- | --- | --- | --- | --- |
| Baseline | | | | | |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| Recovery | | | | | |

Series not available on this version: ______

## Final results

| Result | Outcome | Notes |
| --- | --- | --- |
| Baseline stable | | |
| Contention effect observed / not observed (**not observed on same-host or an unfilled link is not a finding**) | | |
| Recovery returns to baseline | | |
| Everything touched was restored (tools, ports, policy, labels) | | |
