# Administrator guide: network oversubscription

> **Client validation pending.** Target: OpenShift **4.21.31**. Check the client’s
> installed APIs, console paths, metric series and guest packages before the session.
> Procedures are checked against the official 4.21 and 4.22 references; no
> production capacity ratio is implied.


The customer follows the [walkthrough](RUNBOOK.md). This guide holds the
complex parts: approvals, topology, the shared bottleneck, tools, firewall, ports,
metrics, reset.

<a id="prepare"></a>

## Preparation checklist

- [ ] [Approvals](#approvals) recorded.
- [ ] [Preflight](#preflight) done; network facts recorded.
- [ ] **Path A first:** [existing VMs checked, tools added](#path-a). Only if none suit: Path B.
- [ ] Path B only: [tool image](#tools), [labels](#labels), [lab created](#create).
- [ ] [Bottleneck and load plan](#plan) written and approved.
- [ ] [Metrics](#metrics) queries verified.

<a id="approvals"></a>

## 1. Approvals

- Written approval by the client owner (and Red Hat if they advise) for the layout,
  the **maximum offered load**, the window, an abort rule and a named contact.
  There is no universal safe ratio.
- **Oversubscription needs a real shared physical bottleneck** (a node NIC, a
  bonded uplink, a switch port or an inter-switch link). **Same-host traffic is a
  control only**: it never leaves the node and cannot show uplink contention.
- Test traffic can disturb real traffic on that link. Choose a quiet link and window.

<a id="preflight"></a>

## 2. Read-only preflight: record network facts

Console: **Administration → Cluster Settings**; **Networking → NetworkPolicies**
(project of the VMs); **Compute → Nodes → node → Details**.

| Record | How |
| --- | --- |
| OpenShift and Virtualization versions | Cluster Settings, **Operators → Installed Operators** |
| Cluster network (CNI) and its **MTU** | `oc get network.config cluster -o jsonpath='{.status.networkType}{" "}{.status.clusterNetworkMTU}{"\n"}'`; guest MTU from `poc-net-info` |
| NIC model and **rate** per test node, bond/teaming mode | Node shell `ip -d link`, `ethtool IFACE` (or your inventory), per node |
| Topology | Same switch or different, uplink speed, **switch oversubscription ratio**, LACP hash mode, other traffic on the link. Ask the network team; this cannot be read from the cluster |
| NetworkPolicy | Any policy in the VM project that blocks pod-to-pod traffic on the test ports |
| Egress / external path | If an external server is used: its address kept **outside this repository**, the firewall rule, the route |

Remember that a bond with hash-based load balancing may send **one** flow down one
member link; several competitor flows may then spread over different links, and
no single link is full. Record the bond mode and the hash policy.

<a id="path-a"></a>

## 3. Path A (preferred): use existing VMs, unchanged

Use VMs that already exist and already reach each other. **Nothing is applied,
moved, resized or restarted.** Path B (new lab VMs) is a fallback.

### 3.1 Suitability checklist (all must be yes)

| Check | How |
| --- | --- |
| Owner permission, non-critical approved window | Written, with abort rule and contact |
| Linux (RHEL-like) guests; **Windows is not assumed compatible** (scripts and commands are Linux only) | VM **Overview** (OS) |
| `iperf3` present or addable; console/guest access you are allowed to use | `iperf3 --version` in the guest |
| Resources fixed in the window | Record vCPU and RAM from **Configuration → Details** |
| Placement mapping | **Overview → Node** (or `oc get vmi -A -o wide`): record which VM is on which worker; pick a pair that already crosses the link you want to test. Prefer selecting existing VMs over moving any |
| Existing connectivity | From the client guest, `ping` and a short `iperf3` to the server's existing reachable address work (Step 3.3) |
| Shared bottleneck, isolation | See [section 6](#plan) |

If all pass, **no change is required** beyond optional guest tools. Record current
sizes and placement on the sheet.

### 3.2 Address to use

1. **First choice: the server VM's existing Pod IP** (console **Overview**), or any
   address clients can already reach. Use the same address in every phase.
2. A `ClusterIP` Service (an internal name that forwards to the VM) only if the Pod IP
   cannot be used. A Service adds a forwarding step, so its results are **not
   comparable** with Pod-IP results. Never mix them in one comparison, and never use
   a Service result to stand for a secondary-network (direct NIC) path.
3. A new interface or an externally exposed Service (LoadBalancer, NodePort) is **out
   of scope**; stop and decide with the owner.

### 3.3 Tools, ports and firewall: smallest reversible change first

| Missing | Smallest change | Disruption |
| --- | --- | --- |
| helper commands | Copy the files in `guest-tools/` into one folder as an ordinary guest user (for example `~/poc-bin`), make them executable, and `export PATH="$HOME/poc-bin:$PATH"` | Guest only, **no restart**. Undo: remove only copied helper files |
| iperf3 | Install via the owner's approved package route (normally in RHEL 9 AppStream; verify). Record version | Guest only. Undo with the package manager |
| Listener reachable | Listeners use ports 5201-5208 above 1024, so no root is needed to start them. If the **guest firewall** blocks them, the **owner** opens just those ports on the **server** VMs, for example `sudo firewall-cmd --add-port=5201-5208/tcp --add-port=5201-5208/udp` (runtime only, gone at reboot, which is the safest) | Guest only |
| NetworkPolicy blocks | Ask the project owner to allow the test ports from the client VM for the window; remove afterwards | Project object, record and undo |
| VM interface lists ports | A masquerade VM with an explicit `ports:` list only accepts those ports; if the existing VM lists some, use those port numbers (or Step 3.5) | Port numbers only |

Do **not** edit cloud-init, users or storage, delete guest data, or restart workloads
to make the test work. Anything needing a **VM restart or configuration edit** is in 3.5.

### 3.4 Existing application as the measured workload

An existing application path can be the approved representative workload. Freeze its
**dataset, version and concurrency** and run it identically in every phase. Keep
`iperf3` as the reproducible reference. The application must report its own
throughput and latency (p95/p99); otherwise record **not reported**.

<a id="adapt"></a>

### 3.5 Last resort: adapt one stopped, disposable existing VM

Only if no unchanged VM works, the owner agrees, and the VM's current definition is saved
privately (console **YAML → copy**). **A stopped VM must be started again: that is a restart
of that VM.** Edit only these fields under `spec.template.spec`, note the old value of each,
and restore only those:

| Field | Why | Rollback |
| --- | --- | --- |
| `domain.devices.interfaces[name=default].ports` | add the listener ports (TCP and UDP 5201-5208) only if a `ports:` list already exists and omits them | put the old list back |

Keep existing placement rules unchanged; choose an already suitable VM or the
optional new pair. Adding a node-affinity term can broaden an existing rule.

Never replace `cloudInitNoCloud`, users or volumes; never paste a whole saved copy over
the object. After the test: stop, restore the port list, start, record the restart.

<a id="tools"></a>

## 4. Path B: tool image

Path B VMs call `iperf3` but do not install it and set no password. Their cloud-init is
minimal (Kubernetes limits `cloudInitNoCloud.userData` to **2048 bytes**), so the helper
commands are **not** embedded: `guest-tools/` is their single source. Build an approved image
using the owner's authorized method (for example a temporary administrator-only cloud-init with
an approved SSH public key, over an approved repository), install `iperf3` and, as root,
`install -m 0755 guest-tools/poc-* /usr/local/bin/`. If the image also opens TCP and UDP
**5201-5208** in `firewalld` on server VMs, do it once here (`firewall-cmd --permanent --add-port=...`).
Run `cloud-init clean`, stop it, publish its disk as a DataSource (**Virtualization → Bootable
volumes → Add volume**) and put its name and namespace into the `REPLACE_*` values. Remove the
temporary access afterwards. Verify `iperf3 --version` and that `poc-net-info` runs in a VM
made from it.

<a id="labels"></a>

## 5. Path B: topology labels (applied by you, never automatically)

Servers need node label `perf-lab.example.com/net-server-host=true`, clients
`perf-lab.example.com/net-client-host=true`. **Console: Compute → Nodes → node →
Actions → Edit labels.**

| Layout | Labels |
| --- | --- |
| Same-host control | **Both** labels on **one** worker. Cannot show physical contention |
| Cross-host | Server label on worker A only, client label on worker B only (no other node labelled) |
| External server | Client label only; the server is outside (address kept private) |

Verify exactly the intended nodes carry each label:
`oc get nodes -l perf-lab.example.com/net-server-host=true` and `…net-client-host=true`.
Competitor VMs use the same labels so their flows share the same two hosts.
Before changing labels, record each original value privately. At the end, restore
those values; remove a label only if it was absent before this case.

<a id="plan"></a>

## 6. Bottleneck, offered load and accounting

1. **Name the shared bottleneck** (for example *worker A uplink, 25 Gbit/s*). If the
   layout has none (same-host), say "control only" on the sheet.
2. **Offered load plan.** Level N total = competitor flows × rate per flow. Choose
   levels, from light to approved maximum, relative to the bottleneck: e.g. 25%, 50%,
   100%, 125% of its line rate, **only if the owner approves**. Defaults are
   conservative: 2 flows × 200 Mbit/s. The rate is a cap per flow
   (`poc-net-load start … MBPS_PER_FLOW`).
3. **Check the generators are not the limit.** A 2-vCPU VM may top out before a fast
   link: watch guest CPU during the baseline. Add competitor pairs rather than raising
   one VM's load past its CPU.
4. **Accounting.** Count each transfer **once, at its receiver**. A host NIC counts
   send and receive; for a cross-host transfer do not add worker A's transmit to worker
   B's receive. Per-link totals compare against that link's rate. Never average over
   the cluster.
5. **Phases / runs.** Baseline, increasing levels, recovery baseline; each = warm-up,
   measure, repeats (proposal 5 min / 15 min / 3, negotiable), same in all phases; UTC
   timestamps printed by the scripts.
6. **Measured flow stays unchanged.** Same command, VM pair, port and address every run.
   TCP forward, optional TCP reverse (`tcp-rev`), TCP goodput and retransmits at the
   receiver; **ping RTT recorded separately** (it is answered by the pod network and
   may not reach the guest); bounded UDP (fixed offered rate) for loss and jitter.
7. **Ports.** One listener per simultaneous test (`iperf3` serves one test at a time
   and answers "server busy" otherwise). Measured server: 5201 (TCP), 5202 (UDP).
   Competitor server: 5201…5204, one per flow.
8. `iperf3 -B` binds to the guest's own interface address; `poc-net-info` shows it.

<a id="create"></a>

## 7. Path B: create the lab

After creation, record the name and `metadata.uid` of each VM, DataVolume, PVC and case Service
privately (**VM → YAML**, or `oc get vm,dv,pvc,svc -n perf-network-lab -o yaml`).
Keep this record for cleanup. Do not reuse a pre-existing object as a new one.

Replace the remaining `REPLACE_*` values (tool DataSource name and namespace).
New disks default to **vxflexos / Block / ReadWriteMany**. In **Storage →
StorageClasses**, open **vxflexos**; check its StorageProfile supports this
combination and ask the storage administrator to confirm the image can be copied
or cloned into it. The DataSource must be Ready and fit the requested disk.
After population, open each PVC and verify **Bound**, **vxflexos**, **Block**, and
**ReadWriteMany**. Stop on unsupported storage or clone errors. Existing VMs on
Path A can keep their current storage. Apply from the case directory (console
**+ → Import YAML**):

~~~sh
oc apply -f manifests/00-namespace.yaml
oc apply -f manifests/01-measured-pair.yaml
oc apply -f manifests/02-competitor-pair-01.yaml -f manifests/03-competitor-pair-02.yaml
~~~

| Object | Name |
| --- | --- |
| Measured | VMs `netperf-server`, `netperf-client`; Service `netperf-server` |
| Pair 01 | `netload-server-01`, `netload-client-01`; Service `netload-server-01` |
| Pair 02 | `netload-server-02`, `netload-client-02`; Service `netload-server-02` |

More pairs: every name must be unique (VM, DataVolume, hostname, both labels, Service and its
selector). Generate rather than copy by hand:

~~~sh
bash scripts/render-competitor-pair.sh 03 > /tmp/netload-pair-03.yaml   # then fill REPLACE_*
~~~

The VMs declare TCP+UDP **ports 5201-5208** (competitor servers 5201-5204, measured
server 5201-5202) on the default masquerade interface, because a masquerade VM with a
port list accepts only those ports. The **guest firewall** on **server VMs** must also allow
them (baked into the image, or opened by the owner as in 3.3); clients need no inbound port. The **ClusterIP** Services are internal, selected by one VM's label, and
unused by default (see 3.2).

Verify: VMs **Stopped**, DataVolumes **Succeeded**, labels on the right nodes
(section 5), `oc get svc -n perf-network-lab` shows only `ClusterIP`.

### Boot readiness: Running is not ready

Check these as **separate statuses** and record each on the sheet. Do not assume
**Running** means the guest is usable.

1. **Disk first.** The DataVolume must be **Succeeded** (console **Storage →
   PersistentVolumeClaims**, or `oc get dv -n NAMESPACE`). With `WaitForFirstConsumer`
   storage the clone only starts when the VM first starts: wait for it. Snapshot- or
   clone-based sources need a compatible image (the VM's UEFI boot, a disk at least as
   large as the source) and a StorageClass whose clone strategy is supported; confirm with
   the storage owner before any workload.
2. **Boots to a login.** Open the **Console** tab: a login prompt, then the auto-login shell.
3. **Guest agent** shows as connected on the VM **Overview** (separate from Running). Missing
   agent is a note, not a blocker, unless the plan needs it.
4. **Tools present** (`command -v` for each, below) and **firewall** as described for the case.
5. **Block on storage errors.** If **VM events** or the console show I/O errors or the VM
   is **Paused** with a storage reason, stop. Do **not** keep resuming or restarting it, and do
   not proceed to measuring: hand it to the storage owner.
6. **Firewall and listener.** From the client, a short `poc-iperf-run tcp SERVER_IP 5201 0 5` works.

<a id="metrics"></a>

## 8. Metrics

Console: VM **Metrics** tab; **Observe → Dashboards** (*Node Exporter / USE Method /
Node*, *Node Exporter / Nodes*), choose the node and the UTC window (names pending
verification). Queries in **Observe → Metrics** — **verify each series exists** before
using it; write "not available" otherwise. Replace `NODE`, `DEV`.

| Need | Candidate series (verify) |
| --- | --- |
| NIC throughput | `rate(node_network_transmit_bytes_total{device="DEV"}[1m])`, `rate(node_network_receive_bytes_total{device="DEV"}[1m])` (× 8 for bit/s) |
| NIC rate | `node_network_speed_bytes` |
| Drops and errors | `rate(node_network_receive_drop_total[1m])`, `rate(node_network_transmit_drop_total[1m])`, `…_errs_total` |
| Host TCP retransmits | `rate(node_netstat_Tcp_RetransSegs[1m])` |
| Per VM traffic | `kubevirt_vmi_network_transmit_bytes_total`, `kubevirt_vmi_network_receive_bytes_total` |
| Guest CPU (generator limit) | VM **Metrics** tab; guest `top` |

Also record per run: iperf3 goodput, Retr, RTT, UDP loss/jitter, UDP offered rate.
Any **VM migration, restart, or node event** in the window invalidates the run.

<a id="storage"></a>

## 9. Optional: storage over the network (fio)

`fio` is **not** a network benchmark. Storage-over-network testing is a separate,
optional measurement with its own approved storage procedure, directory, size,
duration and cleanup. Do not improvise a write command or reuse an existing file.
This network walkthrough provides no storage write command. Record any separately
approved storage results apart from the iperf3 results.

<a id="reset"></a>

## 10. Reset between takes and clean up

- Stop all flows: `poc-net-load stop` on every competitor client, `poc-iperf-server stop`
  on servers; wait 5 minutes between takes.
- **Path A (existing VMs):** remove only the exact helper files you copied for this
  case. Keep any pre-existing tools and other files in `~/poc-bin`. Ask the owner
  before removing packages. Confirm VM sizes and placement still match the sheet.
- **Path B (new VMs):** save results first. Use **Virtualization → VirtualMachines**,
  select project `perf-network-lab`, and delete only the named VMs you created
  for this case. Check each name and UID against your private creation record
  (**VM → YAML → metadata.uid**); a project label alone is not proof of ownership.
  Delete associated disks only after the storage owner agrees. A `Retain` PV
  keeps its data after PVC deletion; report it rather than deleting the PV yourself.

CLI alternative, one verified object at a time (replace `NAME`):

~~~sh
oc get vm NAME -n perf-network-lab -o jsonpath='{.metadata.uid}{"\n"}'
oc delete vm NAME -n perf-network-lab
oc get dv,pvc,svc -n perf-network-lab
~~~

If a DataVolume, PVC or case Service remains, verify its name and UID against the creation record,
then delete only that named object. For Services, use **Networking → Services**,
select the project, open the recorded Service and choose **Delete**. Keep the project; its owner can check all
resource types before deciding whether to remove it. Never use `--all` for cleanup.
Restore node labels to the values recorded before setup, using **Compute → Nodes →
node → Actions → Edit labels**. Remove only labels this case added; preserve
pre-existing labels. Undo only firewall/NetworkPolicy changes made for this test.

<a id="sources"></a>

## Sources

- [REFERENCES.md](REFERENCES.md): source matrix for OpenShift 4.21 and 4.22 (networking, monitoring, managing VMs) and the differences that matter.
- [iperf3 manual page](https://github.com/esnet/iperf/blob/master/src/iperf3.1): `-B`, `-R`, `-p`, `-u`, `-b`, `-t`, `-O`, `-J`, `-D`.
- [sysbench](https://github.com/akopytov/sysbench) and [stress-ng](https://github.com/ColinIanKing/stress-ng) (case 03).
- OpenShift 4.21 Virtualization documentation: virtual machine networking (masquerade, port lists, Services).
