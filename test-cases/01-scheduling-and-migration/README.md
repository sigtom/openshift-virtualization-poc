# Test 01: VM placement and migration

For VMware/vCenter teams learning OpenShift Virtualization.

You will use prepared RHEL 9 VMs to try five things: approved-host placement,
VM separation, an impossible rule, a live migration you request, and automatic
correction of a placement-rule violation. The full result needs both moves.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** — web console actions, optional CLI equivalents and expected results |
| Cluster administrator | [Prepare and supervise the lab](ADMIN-GUIDE.md#prepare) — prerequisites, setup, isolation checks and recovery |
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

Target OpenShift version: **4.21.31**. Complete preflight against the installed
Virtualization and Descheduler Operator versions before the session.

The preparation and all five console scenarios have been exercised with newly
created VMs, including manual and automatic live migration, guest continuity,
and restoration of the shared configuration. Screenshots illustrate the steps.
The execution used alternate shared filesystem storage; **vxflexos / Block / RWX
provisioning remains unverified**. Complete the storage preflight on the target
cluster.
Keep completed results and environment evidence private.

Technical configuration, Red Hat references, reset and disk cleanup are in
the [administrator guide](ADMIN-GUIDE.md). YAML files remain under manifests/,
priorityclass/, actions/ and descheduler/; apply only the file named in the
relevant step, never the whole repository.
