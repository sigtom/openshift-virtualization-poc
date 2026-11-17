# Customer walkthrough: VM recovery after a host stops responding

> **FENCING LAB: NOT TESTED.** This case has not been run in our lab or the client
> environment, and the web console steps are unverified. Nothing here is a pass
> until the [results sheet](RESULTS-TEMPLATE.md) is filled in on the client cluster.

**Goal:** see a running VM restart on a second worker after an administrator
stops the first worker's kubelet and the cluster power-cycles that worker
through its iDRAC.

**This is not proof of full hardware failure, and it is not a
zero-downtime or live-migration test.** The VM is interrupted and restarted.
No recovery time is promised.

| Step | Who | What happens |
| --- | --- | --- |
| 1 | You | Confirm the starting state |
| 2 | You | Start the VM on the SOURCE worker |
| 3 | You | Record "before" evidence |
| 4 | You | Cordon SOURCE and check the pool |
| 5 | Administrator | Activate the health check and verify it |
| 6 | Administrator | Start the evidence capture |
| 7 | Administrator | Stop the kubelet on SOURCE (the fault) |
| 8 | You | Watch SOURCE get power-cycled and the VM restart on TARGET |
| 9 | You | Record "after" evidence and judge two results |
| 10 | You + administrator | Return to a safe state |

## Before you start

The administrator completes [preparation](ADMIN-GUIDE.md#prepare) before step 1.
Sign [gates 1–7](ADMIN-GUIDE.md#gates) before activation at step 5, then gate 8 after
activation and before the fault at step 7. You need the **SOURCE** and **TARGET** worker names,
project **host-recovery-lab**, VM **recovery-vm** (Stopped), and the agreed **abort
rule and outage budget** (write them on the [results sheet](RESULTS-TEMPLATE.md)).

Use the **web console or the CLI** for each change, never both. Console menu
names are version dependent and unverified; if one is missing, use
**Import YAML** or the CLI. The fault (step 7) has no console equivalent.

<details>
<summary>Using the CLI? Set values once</summary>

~~~sh
cd test-cases/02-host-failure-recovery
export NS=host-recovery-lab
export OPNS=openshift-workload-availability
export SOURCE='REPLACE_SOURCE_NODE'
export TARGET='REPLACE_TARGET_NODE'
~~~

</details>

**Stop and call the administrator** if any result differs from **Expected**, or if
anything asks you to reboot, force-delete or edit a node, a VM instance or a
finalizer by hand.

## 1. Confirm the starting state

**In the web console:** open **Compute → Nodes**. SOURCE and TARGET are **Ready**
and schedulable. Open **Virtualization → VirtualMachines**, project
**host-recovery-lab**: **recovery-vm** is **Stopped**.

**Expected:** two Ready pool nodes; one Stopped VM.

<details>
<summary>CLI</summary>

~~~sh
oc get node "$SOURCE" "$TARGET"
oc get vm recovery-vm -n "$NS"
~~~

</details>

## 2. Start the VM on SOURCE

**In the web console:** **recovery-vm → Actions → Start**. Wait for **Running**.

**Expected:** **Running** on **SOURCE**. If it is on TARGET, **stop** and ask the
administrator.

<details>
<summary>CLI</summary>

~~~sh
oc patch vm recovery-vm -n "$NS" --type=merge -p '{"spec":{"runStrategy":"Always"}}'
oc wait vmi/recovery-vm -n "$NS" --for=condition=Ready --timeout=10m
oc get vmi recovery-vm -n "$NS" -o wide
~~~

</details>

## 3. Record "before" evidence

Write on the results sheet: the instance **UID**, the **Node**, SOURCE's **boot ID**,
and the guest **boot ID**, **persist token** and **heartbeat**. The guest check is
read-only and uses the SSH key your administrator set up (no password exists).
`-i` is the documented identity-file flag; run `virtctl ssh --help` if your
`virtctl` differs.

~~~sh
virtctl ssh -n "$NS" -i ~/.ssh/REPLACE_PRIVATE_KEY cloud-user@vm/recovery-vm \
  --command 'cat /proc/sys/kernel/random/boot_id; cat /var/lib/case02/persist.txt; curl -s localhost:8080/heartbeat.log | tail -n 2'
oc get vmi recovery-vm -n "$NS" -o jsonpath='{.metadata.uid}{"\n"}'
oc get node "$SOURCE" -o jsonpath='{.status.nodeInfo.bootID}{"\n"}'
~~~

**Expected:** a boot ID, a persist token and fresh heartbeat lines.

## 4. Cordon SOURCE and check the pool

A cordon, **not** a drain: the VM is not moved. It keeps the restarted VM off SOURCE.
The administrator recorded that SOURCE was schedulable before; if not, **stop**.

**In the web console:** **Compute → Nodes → SOURCE → Actions → Mark as unschedulable**.
Then filter **Nodes** by label `host-recovery-lab.example.com/pool=case02`.

**Expected:** exactly **two** worker nodes, both **Ready**, SOURCE showing
*Scheduling disabled*. The health check is still **Paused** (its counts read 0 while
paused; ignore them).

<details>
<summary>CLI</summary>

~~~sh
oc adm cordon "$SOURCE"
oc get nodes -l host-recovery-lab.example.com/pool=case02,node-role.kubernetes.io/worker,'!node-role.kubernetes.io/control-plane','!node-role.kubernetes.io/master'
oc get nodehealthcheck case02-host-recovery -o jsonpath='{.spec.pauseRequests}{"\n"}'
~~~

</details>

## 5. Administrator: activate and verify the health check

> **HANDOFF → administrator.** Only after [gates 1–7](ADMIN-GUIDE.md#gates) are signed
> and the abort rule is agreed. From here a real fence can happen.

Remove the pause (console: **Compute → NodeHealthChecks → case02-host-recovery → YAML**,
delete `pauseRequests`; or CLI):

~~~sh
oc patch nodehealthcheck case02-host-recovery --type=merge -p '{"spec":{"pauseRequests":null}}'
oc get nodehealthcheck case02-host-recovery -o jsonpath='{.status.phase} observed={.status.observedNodes} healthy={.status.healthyNodes}{"\n"}'
~~~

**Expected, with SOURCE cordoned and Ready, before any fault:** `Enabled`,
**observed 2, healthy 2** (allow a minute to refresh). **If not, pause again
(step 10 command), do not run the fault, and stop.**

## 6. Administrator: start the evidence capture

> **HANDOFF → administrator.** The remediation object is short-lived and the health
> check may delete it before you look. Capture first, in
> [three private terminals](ADMIN-GUIDE.md#evidence-capture), and keep them running until step 10.

## 7. Administrator: stop the kubelet on SOURCE (the fault)

> **HANDOFF → administrator, separate SSH terminal.** No console equivalent. Afterwards
> `oc debug` to SOURCE will not work. The kubelet was confirmed **enabled and
> active**, so the power-cycle brings it back.

~~~sh
ssh core@REPLACE_SOURCE_NODE 'sudo systemctl stop kubelet'
~~~

Note the time. **Do not reboot the node by hand**: that is not an automatic pass.
Back-out is only possible **before** a remediation exists: start the kubelet over
SSH or the iDRAC console. Once one exists, do not interfere; wait.

## 8. Watch the recovery

**In the web console:** keep **Compute → Nodes**, **Compute → NodeHealthChecks →
case02-host-recovery** and **Virtualization → VirtualMachines** open. Expect:

1. SOURCE turns **Not Ready** within about a minute.
2. After about **5 minutes**, the health check shows **Remediating** with
   **healthy 1** and SOURCE is power-cycled.
3. The VM restarts on **TARGET** as a **new instance** and becomes **Running**.
4. SOURCE returns **Ready** after its reboot.

**Expected:** the VM runs on TARGET **after** SOURCE was fenced. The administrator
records **Fail** if the agreed budget passes or manual recovery is needed.

<details>
<summary>CLI</summary>

~~~sh
oc get node "$SOURCE" -w   # separate terminal; Ctrl+C stops only this watch
# In another terminal:
oc get nodehealthcheck case02-host-recovery -o jsonpath='{.status.phase} observed={.status.observedNodes} healthy={.status.healthyNodes}{"\n"}'
oc get vmi -n "$NS" -o wide
~~~

</details>

## 9. Record "after" evidence and judge two results

Repeat the step 3 guest and node checks, then compare. The fence-before-restart
order comes from the **captured files**, not from a later `oc get`.

| Check | Pass when |
| --- | --- |
| Node | VM is on **TARGET** |
| Instance UID | **Different** from before |
| Guest boot ID | **Different** (a restart, not a migration) |
| Persist token | **Same** (the disk survived) |
| Heartbeat | Lines resume; the gap is visible |
| Fence order | Captured fence-success time is **earlier** than the new instance's creation time ([how](ADMIN-GUIDE.md#fence-order)) |
| Corroboration | iDRAC event log shows the power-cycle; SOURCE boot ID changed |
| Duplicate | Only **one** instance of recovery-vm at any time |

Record **two separate results**:

- **VM restart pass:** every row above passes. Missing fence evidence is **Blocked**, not Pass.
- **Host return pass:** SOURCE is Ready, its remediation object is gone and the remediation taints are cleared (step 10). The cordon remains until you uncordon it.

## 10. Return to a safe state

In this order:

1. Wait until SOURCE is **Ready**, the remediation object is **gone** (the health
   check deletes it) and its **remediation/out-of-service taints are cleared**:
   ~~~sh
   oc get fenceagentsremediation -n "$OPNS"
   oc get node "$SOURCE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status} {.spec.taints}{"\n"}'
   ~~~
   Pausing too early can block this cleanup. **Never** delete the object, the VM
   instance, the node or a finalizer by hand.
2. Stop the capture terminals with **Ctrl+C**.
3. **Pause** the health check again (console YAML, or):
   ~~~sh
   oc patch nodehealthcheck case02-host-recovery --type=merge -p '{"spec":{"pauseRequests":["case02-setup-hold"]}}'
   ~~~
4. Uncordon SOURCE **only if you cordoned it in step 4** (**Actions → Mark as
   schedulable**, or `oc adm uncordon "$SOURCE"`).
5. Hand over to the administrator for [cleanup](ADMIN-GUIDE.md#cleanup) and the [results sheet](RESULTS-TEMPLATE.md).

Stuck or aborting? See [abort and pause](ADMIN-GUIDE.md#abort-and-pause).
