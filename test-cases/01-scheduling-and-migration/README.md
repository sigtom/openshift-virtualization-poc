# Test 01: VM placement and migration

For VMware/vCenter teams learning OpenShift Virtualization.

You will use prepared RHEL 9 VMs to try five things: approved-host placement,
VM separation, an impossible rule, manual live migration, and automatic
correction of a placement-rule violation.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** — web console actions, optional CLI equivalents and expected results |
| Cluster administrator | [Prepare and supervise the lab](ADMIN-GUIDE.md#prepare) — prerequisites, setup, isolation checks and recovery |
| Presenter | [Recording outline](VIDEO-OUTLINE.md) — the same order, with a short explanation for each scene |
| Everyone | [Record results](RESULTS-TEMPLATE.md) — customer observations and administrator sign-off |

The customer walkthrough starts with **five Stopped VMs and prepared disks**.
It is not a cluster installation guide. Choose the web UI or the equivalent
CLI for each change; do not perform the same action twice.

## What the test demonstrates

| Familiar VMware idea | OpenShift equivalent |
| --- | --- |
| VM-to-host “must run” rule | A node label and required node affinity |
| Keep related VMs apart | Hard pod anti-affinity |
| Manual vMotion | Manual live migration |
| Automatic rule correction | Descheduler request followed by live migration |

This is **not continuous DRS or a CPU-load-balancing test**. The required
scenario uses a documented no-PSI configuration. [CPU-aware balancing](OPTIONAL-CPU-AWARE.md)
is optional and outside this walkthrough.

## Test status

CLI lab validation passed on **2026-11-10**, using OCP 4.22.11,
Virtualization 4.22.9 and Kube Descheduler Operator 5.4.3. The target client
version is **4.21.31**, which requires its own preflight.

Presenter verification of the **web console and video remains pending**.
Keep completed results and environment evidence private.

Technical configuration, Red Hat references, reset and disk cleanup are in
the [administrator guide](ADMIN-GUIDE.md). YAML files remain under manifests/,
priorityclass/, actions/ and descheduler/; apply only the file named in the
relevant step, never the whole repository.
