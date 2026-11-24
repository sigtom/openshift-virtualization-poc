# Test 05: storage IOPS

> **Client validation pending.** Target: OpenShift 4.21. Console steps are unverified until
> client verification. Complete the results sheet first.

For teams asking: *what I/O rate, latency and throughput does a VM's disk show while an agreed
workload runs, and what do the layers report?* One bounded, read-only workload runs inside a
VM; the numbers are read at each layer that is available.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** |
| Cluster administrator | [Approvals, mapping, metrics, cleanup](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Layers

| Layer | Source | Needs Dell? |
| --- | --- | --- |
| Guest workload | `poc-fio` output (or the existing application's own report) | No |
| VM disk | OpenShift VM **Metrics** / **Observe → Metrics** (`kubevirt_vmi_storage_*`) | No |
| Backend volume | Dell PowerFlex metrics or read-only array UI | Yes, **deferred** |

A missing **optional** layer (Dell) is **Not available / Not run** for that layer only. The native case
passes only when every agreed required layer has its evidence. Never claim PowerFlex
was validated from another backend's numbers. Values at different layers are not expected to
be equal.

## Files

| File | Purpose |
| --- | --- |
| `guest-tools/poc-fio` | One Python 3 helper: safe fixture, bounded read test, status, cleanup |
| `optional/00-namespace.yaml`, `optional/01-storage-vm.yaml` | Optional new Halted VM (only if no existing VM suits) |
| `optional/powerflex-servicemonitor.template.yaml` | Deferred Dell template, never applied by default |
| `DELL-OBSERVABILITY.md` | **Deferred** PowerFlex/Dell metrics procedure |
| `REFERENCES.md` | Sources |

## Boundaries

- An existing VM and its existing workload can be monitored **unchanged**; no helper is required.
- The `poc-fio` reference preparation **writes** one new fixture file (default 256 MiB); the
  measured test then only reads. No raw devices, formatting, cache dropping, snapshots, migrations,
  driver upgrades, node changes or guest/cluster default changes.
- The default workload is capped; it is **not** a capacity benchmark.
- `direct=1` bypasses the guest page cache only, not host or array caches.
- This case never installs Dell CSM. The Dell layer is optional and deferred until all other
  non-destructive tests are done and the administrator approves.
- Public repository: no credentials, hostnames, addresses or results. Keep evidence private.
