# Test 03: CPU and memory oversubscription

> **Client validation pending.** Target: OpenShift 4.21.31. Complete the client
> results sheet before calling the test passed.

For VMware/vCenter teams asking: *what happens to my VM when many other VMs
share its host?* One fixed **measured VM** runs the same benchmark while
**competitor VMs** on the same worker add CPU demand, then memory demand.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** |
| Cluster administrator | [Approvals, setup, metrics, cleanup](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Two ways to get the VMs

- **Path A (preferred): existing VMs, unchanged.** The administrator checks a short
  suitability list, records the VMs' current sizes and worker, and adds only
  reversible guest helper commands if tools are missing. No YAML is applied.
- **Path B (fallback): new lab VMs** from the manifests below, only when no suitable
  existing VM is available.

## The scenario

For each comparison, use **one measured VM on one isolated worker**: measure it
at baseline, under competing load, and after stopping that load. Keep that VM and
its benchmark unchanged. CPU and memory can use different fixtures, but each
needs its own baseline and recovery results. Run the memory comparison only
after the administrator has prepared memory density and host swap.
Proposal: 5 min warm-up, 15 min measure, 3 repeats, all negotiable.

Tools: `sysbench` (CPU benchmark), `stress-ng` (bounded competitor load that
touches memory) and, optionally, HammerDB for a representative database
workload. Guest helper commands (`poc-sysbench`, `poc-load`, `poc-stats`) are
kept in `guest-tools/` and installed in the VM image (or copied into an existing VM) so the console user only types short commands.

## Files

| File | Purpose |
| --- | --- |
| `guest-tools/` | The guest helper commands (`poc-*`), for existing Linux VMs (Path A) |
| `REFERENCES.md` | Source matrix for OpenShift 4.21 and 4.22 and key differences |
| `MEMORY-DENSITY.md` | Admin appendix: check, enable, verify and undo memory density and swap |
| `optional/` | Admin-only swap MachineConfig and custom pool templates (never applied by default) |
| `manifests/03-memory-fixture.template.yaml` | Optional admin template: memory-only VM in a new namespace, only if no existing VM fits. These new VMs alone bypass the test cordon; existing VMs are unchanged |
| `manifests/00-namespace.yaml` | Path B: project `perf-cpumem-lab` |
| `manifests/01-measured-vm.yaml` | `cpumem-measured` (2 vCPU, 4 GiB, Halted) |
| `manifests/02-competitor-vm-01.yaml`, `-02.yaml` | `cpumem-load-01`, `cpumem-load-02` (same size, Halted) |
| `scripts/render-competitor.sh` | Print more uniquely named competitors |
| `hammerdb/tprocc-run.tcl` | Template database driver script (placeholders) |

Path B only: apply only the files an administrator step names. Replace every `REPLACE_*`
first. Nothing is labelled, started or reconfigured automatically.

## Boundaries

- **No ratio is declared safe.** The cluster owner agrees the ratios and
  competitor count before the run. Default is no overcommit.
- Allocation ratios are scheduling numbers, not utilization; both are recorded
  per host, never as cluster averages.
- Memory contention needs memory density (a **cluster-wide** HyperConverged setting)
  and swap on a worker-only pool (existing if verified exclusive, or a custom one) on the fast
  root filesystem, as approved by the storage owner. The [appendix](MEMORY-DENSITY.md) gives the
  procedure and an optional template targeting only that pool; nothing is applied
  automatically. Without it the memory phase is **Blocked**.
- Linux/RHEL guests only; Windows guests are not assumed compatible.
- sysbench figures are benchmark statistics, not application latency.
- Public repository: only redacted navigation and reference-output pictures. Keep
  credentials, identifying details and completed results private.

## Walkthrough verification

The OpenShift 4.22 console navigation, helper preparation, CPU baseline, bounded
competing CPU load, stop checks and recovery were exercised with three repeats
per phase. The screenshots are redacted reference output. This rehearsal did
**not** establish CPU oversubscription or a safe ratio.

The bounded OpenShift 4.22 memory rehearsal exercised density, new VM placement,
host swap and VM swap measurements. **It was aborted:** swap use exceeded the
agreed limit and the worker became unresponsive. The memory baseline completed;
loaded and recovery benchmarks did not. Paging was observed, but this was not a
successful performance comparison or a safe-ratio qualification.

That rehearsal used separately prepared temporary swap storage. The optional
root-filesystem swap MachineConfig was source-reviewed, not run verbatim.
OpenShift 4.21 execution and new-VM provisioning on `vxflexos` / Block / RWX
remain unverified. Complete your own prerequisites and results sheet.
