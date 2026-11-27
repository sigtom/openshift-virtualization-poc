# Test 04: network oversubscription

> **Client validation pending.** Target: OpenShift 4.21.31. Complete the client
> results sheet before calling the test passed.

For VMware/vCenter teams asking: *what happens to a VM's network transfer when
other VMs push traffic over the same link?* One fixed **measured flow** between
two VMs is repeated while **competitor flows** between other VM pairs add demand.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** |
| Cluster administrator | [Approvals, setup, bottleneck, metrics, cleanup](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Two ways to get the VMs

- **Path A (preferred): existing VMs, unchanged**, using the addresses and network they
  already have. The administrator checks a short suitability list and adds only reversible
  guest helper commands if tools are missing. No YAML is applied.
- **Path B (fallback): new lab VMs** from the manifests, only if no existing pair suits.

## The scenario

Layouts: same-host **control**, cross-host, or external server. Only a layout with a real
shared physical bottleneck can show oversubscription; same-host cannot. Measured flow:
`iperf3` TCP (forward and reverse) goodput and retransmits, separate ping RTT, and a
UDP flow at a fixed rate for loss and jitter. Competitor flows use separate ports and VM pairs
and are added in agreed load levels. Proposal: 5 min warm-up, 15 min measure, 3 repeats.

## Files

| File | Purpose |
| --- | --- |
| `REFERENCES.md` | Source matrix for OpenShift 4.21 and 4.22 and key differences |
| `guest-tools/` | Guest helper commands (`poc-*`) for existing Linux VMs (Path A) |
| `manifests/00-namespace.yaml` | Path B: project `perf-network-lab` |
| `manifests/01-measured-pair.yaml` | `netperf-server`, `netperf-client` (+ internal Service) |
| `manifests/02-…-pair-01.yaml`, `03-…-pair-02.yaml` | `netload-server-NN`, `netload-client-NN` (+ internal Service) |
| `scripts/render-competitor-pair.sh` | Print more uniquely named competitor pairs |

All VMs start Halted; nothing is labelled or started automatically. Replace every `REPLACE_*` first.

## Boundaries

- No ratio is declared safe. Approve the maximum offered load in writing first.
- The Pod-IP path is the default. An internal `ClusterIP` Service is optional, changes
  the path and is not comparable; no LoadBalancer or NodePort is created.
- Linux/RHEL guests only; Windows guests are not assumed compatible.
- iperf3 figures describe the network path, not an application. `fio` is optional,
  only for storage over the network, and never a network benchmark.
- Public repository: only redacted navigation and reference-output pictures. Keep credentials,
  identifying details and completed results private.

## Walkthrough verification

The OpenShift 4.22 console navigation, bounded cross-host UDP baseline, competing
traffic, stop checks and recovery were exercised with three repeats per phase.
Flow/listener counts were checked during the run and after cleanup. TCP received
only a short connectivity check; the full TCP and reverse-direction measurements
were **not run**.

This verifies the fixed-rate UDP procedure, **not** physical-link oversubscription or
a safe ratio. OpenShift 4.21 execution and new-VM provisioning on `vxflexos` /
Block / RWX remain unverified. The screenshots are redacted reference output.
