# Administrator appendix: enable, verify and undo memory density

> **NOT TESTED. Administrator only. Written from documentation, never run here.**
> Source: Red Hat OpenShift Virtualization documentation, chapter
> *Postinstallation configuration*, section *Configuring higher VM workload density*
> ([4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/postinstallation-configuration),
> [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/postinstallation-configuration)).
> See [REFERENCES.md](REFERENCES.md). Re-read the section for the installed version on the
> day: if it differs from this appendix, the documentation wins. Customers never do any of this;
> their walkthrough needs only the result: *memory gate ticked* or *Blocked*.

**Why this exists.** A VM's memory *request* is about its guest RAM, and the scheduler
admits VMs only while requests fit the node. A memory-contention test needs competitors that
together want more RAM than the host has, which is refused unless memory density is on and
the nodes have swap. Without this procedure the memory phase is **Blocked**.

## The two scopes (do not mix them up)

| Change | Scope | Disruptive? |
| --- | --- | --- |
| **Memory density** (`memoryOvercommitPercentage` in the HyperConverged resource) | **Cluster-wide.** It is not limited to the test pool. It changes the memory request of every VM launched afterwards, on every node, and deploys the `wasp-agent` DaemonSet. VMs already running keep their current pod until it is recreated | Not a reboot, but it changes how every newly started VM is admitted |
| **Swap on nodes** (MachineConfig) | **One MachineConfigPool**: the dedicated test pool only | **Yes.** Each node of the pool drains and reboots, one at a time |

Get the cluster owner's written approval for the **cluster-wide** part as well as the
pool part. Do it in a change window in which nobody else starts VMs on nodes without swap.

**Mark the memory phase *Blocked*, never skipped or passed**, if any of: no worker-only
dedicated pool exists or can be approved; the feature or API is missing on the installed
version; approval is missing; or any node that would be selected is control plane. This case
ships no change for control-plane nodes.

## Step 0. Back up first (private folder outside this repository)

~~~sh
mkdir -p "$HOME/memdensity-backup" && cd "$HOME/memdensity-backup"
oc get hyperconvergeds.v1beta1.hco.kubevirt.io kubevirt-hyperconverged -n openshift-cnv -o yaml > hco.yaml
oc get mcp -o yaml > mcp.yaml
oc get mc -o name > mc-names.txt
oc get kubeletconfig -o yaml > kubeletconfig.yaml
oc get nodes --show-labels > nodes-labels.txt
oc get ds -A | grep -i wasp > wasp-before.txt || true
~~~

Console equivalent: open each object's **YAML** tab and download it. You will restore only the
fields you touched. Never replace a whole shared object from these copies.

## Step 1. Inspect the current state (console first)

1. **Virtualization → Overview → Settings → General settings → Memory density.** Write down
   whether **Configure memory density** is on and its value.
2. **Compute → MachineConfigPools:** every pool **Updated**, none **Degraded**.
3. **Compute → Nodes:** the test nodes are Ready.

**Branch: memory density is already on.** Record the value and *reuse it unchanged*: do not
change it, do not turn it off afterwards, and skip Steps 6 and 8-HCO. Check only swap on the
test nodes (Step 5) and the effective request (Step 7). If the value is too low for the plan,
stop and ask the owner.

## Step 2. Pin the API version before any command (do not guess a field path)

The HyperConverged resource is served in more than one API version, and **the field path
depends on the version**. Documentation: the 4.21 and 4.22 sections use the
`hyperconvergeds.v1beta1.hco.kubevirt.io` resource with `spec.higherWorkloadDensity`.
Some releases also serve `v1`, where the setting sits under `spec.virtualization`. Discover
what the installed cluster serves (standard `oc` discovery, nothing undocumented):

~~~sh
oc get crd hyperconvergeds.hco.kubevirt.io \
  -o jsonpath='{range .spec.versions[*]}{.name}{" served="}{.served}{" storage="}{.storage}{"\n"}{end}'
oc explain hyperconvergeds.v1beta1.hco.kubevirt.io.spec.higherWorkloadDensity
oc explain hyperconvergeds.v1.hco.kubevirt.io.spec.virtualization.higherWorkloadDensity
~~~

Use the **documented v1beta1 form below** whenever `v1beta1` is served and its explain output
shows `memoryOvercommitPercentage`. Use one API version for **every** get, explain and patch,
and write it on the sheet. If the version your documentation names is not served, or no
`memoryOvercommitPercentage` field exists in any served version: **stop, Blocked**. The console
setting in Step 6 does not depend on this choice, which is why it is the preferred route.
Do not use an unqualified `oc patch hco …`: the short name can resolve to a different version.

| API version | Resource name to type | Field |
| --- | --- | --- |
| v1beta1 (documented) | `hyperconvergeds.v1beta1.hco.kubevirt.io` | `spec.higherWorkloadDensity.memoryOvercommitPercentage` |
| v1 (only if the installed docs say so) | `hyperconvergeds.v1.hco.kubevirt.io` | `spec.virtualization.higherWorkloadDensity.memoryOvercommitPercentage` |

The commands below are written for v1beta1; for v1 replace the resource name and the JSON path.

## Step 3. Record the original value of exactly this field

~~~sh
R=hyperconvergeds.v1beta1.hco.kubevirt.io
oc get $R kubevirt-hyperconverged -n openshift-cnv -o jsonpath='parent={.spec.higherWorkloadDensity}{"\n"}value={.spec.higherWorkloadDensity.memoryOvercommitPercentage}{"\n"}'
~~~

Write both lines on the results sheet. Cases: **parent empty** (absent), **parent present, value
empty** (other keys may exist), **value present** (reuse branch if density is meant to stay).

## Step 4. Choose the pool (no control plane) and run the collision preflight

*Preferred:* an **existing**, approved, dedicated worker-only pool. For pool `POOL`:

~~~sh
oc get mcp POOL -o jsonpath='{.spec.nodeSelector}{"\n"}{.spec.machineConfigSelector}{"\n"}'
oc get nodes -l node-role.kubernetes.io/POOL -o name       # only the intended test node(s)
oc get nodes -l node-role.kubernetes.io/master -o name     # none of the above may appear here
oc get nodes -l node-role.kubernetes.io/control-plane -o name
~~~

**Stop** if an unrelated node, or any control-plane node, is selected.

**Collision preflight (stop on any hit):**

~~~sh
oc get mc -o yaml | grep -n -e '90-swap.conf' -e '/var/tmp/swapfile'     # expect no output
oc debug node/TESTNODE -- chroot /host sh -c 'ls /etc/openshift/kubelet.conf.d/ 2>&1; ls -l /var/tmp/swapfile 2>&1; swapon --show'
~~~

Expected: no MachineConfig mentions either name, the drop-in directory has no `90-swap.conf`,
`/var/tmp/swapfile` does not exist, and no swap is active (or swap is already provided by a
client mechanism: then **do not add another**; go to Step 6). Never overwrite a drop-in or swap
file that another configuration owns.

*If no pool exists:* a dedicated pool may be created, **only with the cluster owner's approval**,
from [`optional/custom-pool.template.yaml`](optional/custom-pool.template.yaml). It lists `worker`
and your new role, so the pool **inherits every worker MachineConfig**; a node that carries the
worker label and `node-role.kubernetes.io/ROLE=` is managed by the new pool. Joining or leaving a
pool can drain and reboot the node. Do it for **one** worker-only node with no other VMs:

1. Fill the template; `oc apply --dry-run=server -f FILE`; apply (console **Compute →
   MachineConfigPools → Create**).
2. Wait for the pool to show **Updated** with 0 nodes.
3. Label exactly one worker-only node (**Compute → Nodes → node → Actions → Edit labels**).
4. Wait until the pool shows 1 node and **Updated** again.
5. Rollback later: remove that label, wait for the node to rejoin `worker`, then delete only the pool you created.

Never use the generic `worker` pool for swap by default: it reboots every worker.

## Step 5. Prepare swap on the pool (disruptive; skip if swap already exists)

With **all lab VMs stopped** and no other workloads on the test node:

1. Swap size = node RAM × (percent ÷ 100 − 1), for example 16 GB at 150% = 8 GB (8192 MB).
   `/var/tmp` on the node needs that much free space.
2. Copy [`optional/swap-machineconfig.template.yaml`](optional/swap-machineconfig.template.yaml);
   replace `REPLACE_POOL_ROLE` (name and role label) and only the `REPLACE_SWAP_SIZE_MB` value token (keep the
   `SWAP_SIZE_MB` variable name unchanged). Diff it against the
   documentation section for the installed version.
3. `oc apply --dry-run=server -f FILE` must succeed. Console: **Compute → MachineConfigs →
   Create MachineConfig**.
4. Preflight again: pool **Updated** and not **Degraded**; Step 4 results still true; window open.
5. Apply. Watch **Compute → MachineConfigPools → POOL**: nodes cordon, drain, reboot, return,
   one at a time. `oc wait mcp POOL --for condition=Updated=True --timeout=-1s` waits.
6. Verify: `oc debug node/TESTNODE -- chroot /host free -m` shows swap of about the size set.

If the pool goes **Degraded** or a node stays NotReady: stop, add no more nodes, roll back
(Step 8), investigate.

## Step 6. Turn memory density on (console)

1. **Virtualization → Overview → Settings → General settings → Memory density.**
2. Turn on **Configure memory density**; choose the **approved** percentage (the console offers
   100% to 400% in 25% steps, for example 150%). **Save.**

CLI equivalent, same API version as Steps 2–3. A **merge patch** creates the parent object if it
is absent and leaves every other field alone:

~~~sh
oc patch $R kubevirt-hyperconverged -n openshift-cnv --type=merge \
  -p '{"spec":{"higherWorkloadDensity":{"memoryOvercommitPercentage":150}}}'
oc get $R kubevirt-hyperconverged -n openshift-cnv -o jsonpath='{.spec.higherWorkloadDensity}{"\n"}'
~~~

**Verify the agent:** `oc get ds -A | grep wasp-agent` (the namespace differs by version) then
`oc rollout status ds/wasp-agent -n NAMESPACE_FOUND`. Console: **Workloads → DaemonSets**, all
projects, filter *wasp*. Pods Running on the test nodes. Read the section for the installed
version to see **which pod QoS classes receive swap**; do not assume which VMs benefit.

## Step 7. Verify the effective memory request

A VM picks up the request when its launcher pod is created, so use a VM started **after** Step 6.

1. Start one competitor (**Actions → Start**) and wait for **Running**.
2. Console: **Workloads → Pods →** the `virt-launcher-…` pod **→ YAML**, field
   `resources.requests.memory`. CLI:

~~~sh
oc get pod -n NAMESPACE -l kubevirt.io/domain=COMPETITOR_VM \
  -o jsonpath='{.items[0].spec.containers[?(@.name=="compute")].resources}{"\n"}'
~~~

3. **Expected:** the request is **below** the guest RAM (about guest RAM ÷ the density ratio
   plus overhead). Record guest RAM, density value and actual request. If equal to guest RAM,
   memory density is **not** in effect: stop; the memory phase is Blocked.
4. `free -m` on the node shows swap; host swap metrics respond (admin guide, metrics).

Derive the competitor count from **actual** admitted requests (**Compute → Nodes → node →
Details → Allocated resources**), never from the ratio alone.

## Step 8. After the test: stop, check headroom, restore, verify

Do these in order.

1. **Stop all test load and VMs** (`poc-load stop`, then stop the VMs). Memory used by swap
   does **not** necessarily drain by itself: idle pages can stay in swap.
2. **Check headroom on the node.** Swapped-out pages must fit back in RAM if swap goes away:
   `MemAvailable` (`free -m`, "available") must exceed swap *used* with a clear margin. If it
   does not, do not remove swap while anything runs: stop more workloads on that node first.
   Removing swap config reboots the node, but do not rely on that to clean up under pressure.
3. **Restore memory density** (skip if you reused an existing setting). Console: **Virtualization →
   Overview → Settings → General settings → Memory density**, set the recorded value, or turn it
   off if it was off. CLI, restoring **only** the field you touched, using the Step 3 record:

   - *Value was present* (for example 100): set it back:
     `oc patch $R kubevirt-hyperconverged -n openshift-cnv --type=merge -p '{"spec":{"higherWorkloadDensity":{"memoryOvercommitPercentage":100}}}'`
   - *Parent existed with other keys, value absent*: remove only the value:
     `oc patch $R kubevirt-hyperconverged -n openshift-cnv --type=merge -p '{"spec":{"higherWorkloadDensity":{"memoryOvercommitPercentage":null}}}'`
   - *Parent was absent entirely*: remove the parent you created:
     `oc patch $R kubevirt-hyperconverged -n openshift-cnv --type=merge -p '{"spec":{"higherWorkloadDensity":null}}'`

   Never `oc replace` or `oc apply` the saved `hco.yaml`.
4. **Remove the swap configuration you added:** delete **only** the MachineConfig you created
   (**Compute → MachineConfigs →** `90-…-perf-swap` **→ Delete**). The pool reboots node by node.
   Wait for **Updated**.
5. **Verify swap is gone:** `free -m` shows swap `0` on the test node; no leftover
   `/var/tmp/swapfile` (delete the file you created if the removal left it, with the owner's
   approval). Confirm the `wasp-agent` DaemonSet is gone if you caused it.
6. **Remove the pool you created**, if any (Step 4 rollback). Never delete a pool you did not create.
7. **Verify against the backup:** only the field you touched differed, and now matches Step 3;
   `oc get mc -o name` against `mc-names.txt`; node labels against `nodes-labels.txt`; pools Updated.
8. Record the restoration on the results sheet.

## Known cautions

- Memory overcommit can lower performance on heavily used systems; that is part of what is measured.
- Which VM pods receive swap is defined in the documentation for the installed version. Read it; do not assume.
- Red Hat tracks issues with `wasp-agent` during upgrades and at very high ratios: do not run
  this during a cluster upgrade, and re-read the known issues for the installed version.
- Guidance on the kubelet `failSwapOn` setting has changed between releases; follow the section
  for the installed version (it may use a `KubeletConfig`). This appendix ships none.
