# Test case 01 - VM placement, spreading and descheduler-driven live migration

A disposable OpenShift Virtualization POC for VMware/vCenter administrators.
It uses Red Hat Enterprise Linux 9 VMs built from the `rhel9-server-small`
common template, persistent RWX root disks, and a descheduler configuration
taken from Red Hat's guidance for virtualization.

| Test | Scope |
|---|---|
| 01 Placement on approved nodes | required |
| 02 Spread across an approved pool (VM-VM anti-affinity) | required |
| 03 Impossible rule refused with `FailedScheduling` | required |
| 05 Descheduler evicts a rule-violating VM -> live migration, guest keeps running | required |
| 04 Manual live migration | optional diagnostic, never descheduler evidence |
| CPU/load-aware balancing | optional, not run ([OPTIONAL-CPU-AWARE.md](OPTIONAL-CPU-AWARE.md)) |

Procedure: [RUNBOOK.md](RUNBOOK.md). Every stage gives the console (web UI)
step, then the CLI equivalent, then the expected result in both.
Recording plan: [VIDEO-OUTLINE.md](VIDEO-OUTLINE.md). Results: [RESULTS-TEMPLATE.md](RESULTS-TEMPLATE.md).

## Status

- CLI lab validation **passed on 2026-11-10**: RHEL 9 VMs on RWX disks,
  approved-node placement, three-node spreading, an impossible scheduling
  rule, manual live migration, and policy-triggered live migration.
- The tested descheduler had background evictions enabled and a priority
  threshold in both generated profiles. HCO's misconfigured-descheduler
  metric was 0, with no matching alert. Guest boot identity and a test-file
  checksum stayed unchanged through live migration.
- Console steps are **pending presenter verification** while recording.
  Record that separately in the results template.
- Validation used OpenShift 4.22.11 / Virtualization 4.22.9 / Kube Descheduler
  Operator 5.4.3. The target is 4.21.31; this is not acceptance of that client
  environment. Run its version/operator/schema/storage preflight there.

## VMware concepts mapped to OpenShift

| vSphere | OpenShift Virtualization | Test |
|---|---|---|
| Host group + VM-Host "must run on" rule | node label + required `nodeAffinity` in the VM | 01, 02 |
| VM-VM anti-affinity "separate VMs" | `podAntiAffinity`, `topologyKey: kubernetes.io/hostname` | 02 |
| "must" rule with an empty host group | unsatisfiable affinity -> `FailedScheduling` | 03 |
| manual vMotion | `VirtualMachineInstanceMigration` / console **Migrate** | 04 |
| DRS Manual (recommend only) | descheduler `mode: Predictive` | 05 |
| DRS Fully Automated, rule-violation fix | descheduler `mode: Automatic`, `RemovePodsViolatingNodeAffinity` | 05 |

Not continuous DRS: placement happens at start; required rules are
"IgnoredDuringExecution". The descheduler runs on an interval, evicts a VM that
now breaks its rule, and OpenShift Virtualization turns the eviction into a
live migration. Editing a running VM's scheduling rules may show "restart
required"; this lab moves node labels instead, so no restart is needed.

## Descheduler configuration and why

```yaml
mode: Predictive            # Automatic only in an explicit, separate step
deschedulingIntervalSeconds: 30
profiles: [AffinityAndTaints, LongLifecycle, EvictPodsWithLocalStorage, EvictPodsWithPVC]
profileCustomizations:
  devEnableEvictionsInBackground: true
  thresholdPriority: -999999999
  namespaces: {included: [virt-scheduling-lab]}
evictionLimits: {node: 1, total: 1}
```

- **LongLifecycle + `devEnableEvictionsInBackground: true`** is the
  virtualization-compatible configuration that works without PSI metrics. The
  HCOMisconfiguredDescheduler runbook lists it as the third choice after
  `KubeVirtRelieveAndMigrate` / `DevKubeVirtRelieveAndMigrate`, which require
  PSI metrics. The 4.21 virtualization documentation (PDF, section 9.18.13.2)
  documents LongLifecycle for VMs; current HTML pages prefer
  `KubeVirtRelieveAndMigrate` with PSI. Versions differ: check what your
  release supports (RUNBOOK 1.1).
- **AffinityAndTaints** provides `RemovePodsViolatingNodeAffinity`, the
  strategy this test exercises. It honors the namespace include.
  AffinityAndTaints with background evictions **alone** is not on the HCO
  list and raises `HCOMisconfiguredDescheduler`.
- **LongLifecycle's `LowNodeUtilization` ignores the namespace include.** The
  hard boundary is therefore `thresholdPriority` (Nodes documentation): pods
  with priority at or above `-999999999` are protected by the priority filter.
  This requires the clean inventory and reserved-class checks below; the
  force-evict annotation bypasses that filter. Only
  `placement-01` uses the reserved PriorityClass
  `virt-scheduling-lab-evictable` (`-1000000000`). The runbook inventories all
  pods before Predictive and again right before Automatic.
- `EvictPodsWithLocalStorage` / `EvictPodsWithPVC`: virt-launcher pods use
  local volumes and PVCs and are skipped without them.
- No PSI MachineConfig is applied or proposed.

## Files

```text
manifests/          (apply after replacing REPLACE_WITH_RWX_STORAGE_CLASS; all VMs Halted)
  00-namespace.yaml
  01-placement-vm.yaml             placement-01: eligible-node affinity, reserved PriorityClass
  02-spread-vms.yaml               spread-01..03: pool label + hard anti-affinity
  03-negative-unsatisfiable-vm.yaml
priorityclass/virt-scheduling-lab-evictable.yaml   cluster-scoped; create explicitly, UID-guarded cleanup
actions/04-manual-migration.yaml   optional; starts a migration when created
descheduler/        singleton changes, never directory-apply
  05a-lab-predictive.patch.json    guarded patch -> lab config (dry run)
  05b-lab-automatic.patch.json     guarded patch -> Automatic
  05c-back-to-predictive.patch.json
  05d-restore-touched-fields.jq    builds the guarded restore of the five touched fields
  05e-create-if-absent.yaml        only when no KubeDescheduler exists
```

## VMs

`rhel9-server-small` basis: 1 socket / 1 core / 1 thread, 2 GiB, SMM + EFI,
virtio disk and NIC, RNG, masquerade pod network. Root disk cloned from the
`rhel9` DataSource in `openshift-virtualization-os-images` (the standard
boot source OpenShift Virtualization provides; no image is published here)
onto a client **RWX Filesystem** StorageClass, 40 GiB each (golden image is
about 32 GiB). Root disks are **persistent**: guest changes survive stop/start,
`boot_id` changes on every boot. Five VMs = 200 GiB logical.

No passwords or keys; root and SSH password login disabled. As a deliberate
POC console convenience, the serial console auto-logs in as unprivileged
`cloud-user` (no sudo); RBAC on the VM console controls who gets it. Not a
production guest policy. `qemu-guest-agent` ships in the image and is only
enabled; nothing is installed or updated. No Service, Route or LoadBalancer is
created. Node names, storage classes and label domains are placeholders.

## References

- HCOMisconfiguredDescheduler alert runbook:
  <https://github.com/openshift/runbooks/blob/master/alerts/openshift-virtualization-operator/HCOMisconfiguredDescheduler.md>
- OpenShift 4.21 Nodes - controlling pod placement (affinity, descheduler profiles, `thresholdPriority`, Predictive mode):
  <https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/nodes/controlling-pod-placement-onto-nodes-scheduling>
- OpenShift 4.21 Virtualization - live migration:
  <https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/live-migration>
- OpenShift 4.21 Virtualization - storage:
  <https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/storage>
- OpenShift 4.21 Virtualization (PDF; descheduler for VMs, section 9.18.13.2):
  <https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/pdf/virtualization/OpenShift_Container_Platform-4.21-Virtualization-en-US.pdf>
