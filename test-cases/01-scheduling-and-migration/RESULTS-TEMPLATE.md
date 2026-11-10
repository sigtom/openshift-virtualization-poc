# Results - test case 01 (RHEL 9 / RWX / LongLifecycle)

Keep filled copies private. Each row stands on its own evidence: passed,
failed, blocked or not run. Console verification is a separate column.

Cluster: ______ Virtualization: ______ Descheduler operator: ______
RWX StorageClass: ______ Date: ______ Tester: ______ Presenter: ______

| Stage | CLI result | Evidence | Console verified (presenter) |
|---|---|---|---|
| 1 Preflight: versions, CRDs, profile enum | | | |
| 1 Preflight: rhel9 DataSource Ready, clone permission | | | |
| 1 Preflight: RWX class, 200 GiB capacity agreed | | | |
| 1 Preflight: nodes, arch, headroom, lab labels unused | | | |
| 1 Preflight: namespace + PriorityClass new | | | |
| 1 Preflight: pod priority inventory clean | | | |
| 2 Namespace / PriorityClass created, UIDs recorded | | | |
| 2 VMs created Halted, 5 clones Succeeded / Bound RWX | | | |
| 3 Placement on NODE_A, LiveMigratable, launcher priority/class exact | | | |
| 4 Spread on three pool nodes | | | |
| 5 Negative: FailedScheduling | | | |
| 6 Manual migration (optional, not descheduler evidence) | | | |
| 7.4 Generated policy: every DefaultEvictor threshold, EvictionsInBackground gate, HCO metric 0 / no alert | | | |
| 7.5 Predictive: RemovePodsViolatingNodeAffinity candidate, VM not moved | | | |
| 7.6 Priority re-check before Automatic | | | |
| 7.6 Automatic: eviction -> evacuation migration Succeeded | | | |
| 7.8 Continuity: VM UID, VMI UID, boot_id same; uptime increased | | | |
| 7.9 Restore of five fields verified (or created CR deleted, UID matched) | | | |
| 10 Cleanup: DVs/PVCs gone, namespace + PriorityClass deleted (UID matched), labels removed | | | |
| CPU/load-aware balancing | not run (optional, needs PSI) | | |

| Value | Before | After |
|---|---|---|
| Node | | |
| VM UID | | |
| VMI UID | | |
| boot_id | | |
| uptime (s) / time | | |
| Migration name / phase | (none) | |
