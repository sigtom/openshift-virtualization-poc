# Video outline - console first

Audience: VMware/vCenter administrators. About 25-30 minutes (segments add up
to about 28.5). Console first; CLI only as a short aside. The presenter owns
verification of every console step shown; none of it is verified by the author.

Before recording:

- [ ] Preflight (RUNBOOK 1) passed, including the pod priority inventory.
- [ ] Namespace and PriorityClass created, five VMs created, all root-disk clones `Succeeded` (RUNBOOK 2). All VMs Stopped.
- [ ] Descheduler owner agreed the window; snapshot taken (RUNBOOK 7.1-7.2).
- [ ] No `scheduling-lab.example.com/...` labels on any node.
- [ ] Optional picture-in-picture: two terminals, `oc get vmi -n virt-scheduling-lab -o wide -w` and `oc get vmim -n virt-scheduling-lab -w`.
- [ ] Hide cluster URLs, node and storage names you may not publish.

| # | Segment | Console | Message | ~min |
|---|---|---|---|---|
| 1 | Intro | VirtualMachines list: five RHEL 9 VMs, Stopped | Placement, spreading, an impossible rule, policy-driven live migration; map to DRS rules and vMotion | 2 |
| 2 | Host group = label | Nodes > NODE_A > Edit labels: `eligible=true` | A host group is a node label | 1.5 |
| 3 | Rule on the VM | placement-01 > Configuration > Scheduling (or YAML) | "Must run on hosts in group" lives in the VM | 1.5 |
| 4 | Placement | Start; Overview Node = NODE_A | Scheduler chooses only from the group | 2 |
| 5 | Inside the guest | Serial console: `boot_id`, uptime | Remember these; unprivileged demo user, RBAC-controlled, POC convenience only | 1.5 |
| 6 | Spreading | Label 3 nodes `spread-pool`; start spread-01..03; three nodes | VM-VM anti-affinity | 3 |
| 7 | Impossible rule | Start negative-01; Events: FailedScheduling; Stop | A "must" rule that can't be met is refused visibly | 2 |
| 8 | (Optional) manual vMotion | Label NODE_B; Actions > Migrate > Compute | A person asked for this; not the descheduler test | 2 |
| 9 | Descheduler | KubeDescheduler `cluster` YAML: Predictive, AffinityAndTaints + LongLifecycle, background evictions, priority threshold, lab namespace, limit 1 | Red Hat's virt-compatible profile set; Predictive = DRS Manual; priority threshold protects everything else | 2.5 |
| 10 | Health | Observe > Alerting: no HCOMisconfiguredDescheduler | Virtualization operator accepts this configuration | (in 9) |
| 11 | Break the rule | Add `eligible` to TARGET, remove from SOURCE; VM still on SOURCE | Changing the group doesn't move a running VM by itself | 1.5 |
| 12 | Dry run | descheduler pod Logs: candidate for placement-01 (node affinity) | It would act, but Predictive only reports | 1.5 |
| 13 | Automatic | YAML `mode: Automatic`; VM Migrating -> TARGET; Migrations: Succeeded | Eviction became a live migration | 3 |
| 14 | Continuity | Serial console: same boot_id, larger uptime | Same VM, same boot, persistent disk | 1.5 |
| 15 | Back to safe | YAML `mode: Predictive` (restore off camera, RUNBOOK 7.9) | Automation off right after the test | 1 |
| 16 | Wrap-up | README mapping | Not continuous DRS; CPU-based balancing needs PSI metrics, out of scope | 1.5 |

Reset between takes: RUNBOOK 9 (disks are kept). After the last take: RUNBOOK 7.9 and 10.

Do not: call segment 8 a descheduler result; claim CPU balancing; show the evidence folder, API URL or tokens.
