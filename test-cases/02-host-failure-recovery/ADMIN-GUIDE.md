# Administrator guide: host-failure recovery

> **FENCING: NOT TESTED.** Execution is pending. Server dry-runs are **provided, not performed**. The **installed** operator versions and CRD schemas govern; where
> this guide and the cluster disagree, the cluster wins.

This case **really power-cycles a server**. You own approval, the outage budget
and the abort decision. Run commands from `test-cases/02-host-failure-recovery`.
Sources and pinned reference versions are listed at the [end](#reference-sources).

## Prepare

~~~sh
export OPNS=openshift-workload-availability NS=host-recovery-lab
export SOURCE='REPLACE_SOURCE_NODE' TARGET='REPLACE_TARGET_NODE'
~~~

### Requirements (all must be true)

- SOURCE and TARGET are **worker-only** (no `control-plane`/`master` role), dedicated
  to this test, with **spare capacity (N+1)**: TARGET can hold the VM alone.
- Everything else on SOURCE is **disposable and approved**; fencing affects all its workloads.
- A dedicated, Bound PVC with a bootable RHEL 9 image exists in `NS` ([below](#prepare-the-vm-disk)),
  and **shared storage stays reachable from both nodes**.
- Each node's **iDRAC is reachable from the FAR pods** and stays reachable (hosted outside the cluster).
- Each operator has a Ready controller replica on a healthy node **other than SOURCE**, so losing SOURCE cannot stop detection or fencing. Check the installed operator's supported placement and replica settings; do not patch its managed Deployment ad hoc.
- An **abort rule, outage budget and escalation contact** are agreed in writing with the owner.
  They are test limits, not a recovery-time claim. Manual recovery = **Fail**.
- You may SSH to SOURCE as an approved administrator (the fault uses it).

### Artifact files

Apply only the file a step names; never the folder.

| Artifact | Use |
| --- | --- |
| `manifests/00-namespace.yaml` | Only if `NS` does not exist |
| `manifests/00a-subscription-fence-agents-remediation.yaml` | Only if FAR is missing |
| `manifests/00b-subscription-node-health-check.yaml` | Only if NHC is missing |
| `manifests/01-far-template.yaml` | Fill node names, BMC hosts, Systems ids |
| `manifests/02-nhc-paused.yaml` | Check the selector; ships paused |
| `manifests/03-recovery-vm.yaml` | Fill `REPLACE_*`; ships Halted |

### Web console alternatives

Menu names are unverified on the client. Use **Search** to find a resource kind if its menu differs.
Use the console **or** the matching CLI section for each mutation, never both.

| Preparation | Web console | CLI section |
| --- | --- | --- |
| Operators | **Operators → Installed Operators** to check; **Software Catalog** to install only what is missing. Review the exact pending InstallPlan before approval. | [Operator check](#operator-check) |
| Node roles, capacity and workloads | **Compute → Nodes → node → Details / Pods**; verify worker-only roles and review all workloads. | [Roles and readiness](#verify-roles-and-readiness) |
| Project and boot disk | Create project **host-recovery-lab**, then use the approved RHEL boot-source workflow. Review volume/access mode and retain the prepared disk. | [Namespaces](#namespaces-and-ordering), [disk](#prepare-the-vm-disk) |
| Pool labels | On each of the two nodes, **Details → Labels → Edit**; add `host-recovery-lab.example.com/pool=case02`. | [Label the pool](#label-the-pool) |
| BMC Secrets | **Workloads → Secrets**, project `openshift-workload-availability`; create two **Key/value secrets** with the documented names and keys `--username`, `--password`. Enter actual values privately. | [Secrets](#fencing-secrets-from-private-local-files) |
| FAR template and paused NHC | **Search → Resources**; choose the respective kind, then **Create → YAML** and paste the customized named manifest. Confirm the NHC still has `pauseRequests`. | [Create](#create) |
| Stopped VM | **Virtualization → VirtualMachines → Create → From YAML**; paste `03-recovery-vm.yaml`. Confirm **Stopped**. | [Create](#create) |

BMC inventory, installed-agent TLS checks and server dry-runs need the administrator CLI. They have
no equivalent console validation in this guide. The [customer walkthrough](RUNBOOK.md) starts
only after these checks.

### Operator check

Reuse existing installs, namespace and OperatorGroup; modify nothing that exists.

~~~sh
oc get csv -n "$OPNS" | grep -Ei 'fence-agents|node-healthcheck'
oc get operatorgroup,subscription -n "$OPNS"
oc get pods -n "$OPNS" -o wide     # verify surviving Ready NHC and FAR controllers off SOURCE
~~~

In the console, **Operators → Installed Operators** shows each operator's status. Both rows below
show **Succeeded** (preparation view only; versions and the middle column are hidden, and this does not show
that fencing works):

![Fence Agents Remediation Operator installed and Succeeded](images/02-fencing-operator-succeeded.png)

![Node Health Check Operator installed and Succeeded](images/03-healthcheck-operator-succeeded.png)

If `$OPNS` or its OperatorGroup is absent, use the Red Hat install procedure (Operators →
Software Catalog). If **one** operator is missing, create **only** its Subscription (`oc create` fails safely if it exists):

~~~sh
oc create -f manifests/00a-subscription-fence-agents-remediation.yaml   # only if FAR is missing
oc create -f manifests/00b-subscription-node-health-check.yaml          # only if NHC is missing
oc get installplan -n "$OPNS" -o custom-columns=NAME:.metadata.name,CSV:.spec.clusterServiceVersionNames,APPROVED:.spec.approved
~~~

Approve **only** the InstallPlan whose CSV is the one you intend, then read back:

~~~sh
oc patch installplan REPLACE_INSTALLPLAN_NAME -n "$OPNS" --type=merge -p '{"spec":{"approved":true}}'
oc get csv -n "$OPNS"     # wait for Succeeded; record both versions
~~~

### Schema check

~~~sh
oc explain fenceagentsremediationtemplate.spec.template.spec
oc explain nodehealthcheck.spec
~~~

Confirm: `agent`, `remediationStrategy` (`ResourceDeletion`, `OutOfServiceTaint`), `retrycount`,
`retryinterval`, `timeout`, `sharedparameters`, `nodeparameters`, `nodeSecretNames`; and for NHC
`selector`, `minHealthy`, `unhealthyConditions`, `pauseRequests`, `remediationTemplate`.
A missing or renamed field means **stop and adapt the YAML**.

### Ownership check (no overlap)

Read full selectors, not just the summary table. Change nothing that exists.

~~~sh
oc get nodehealthcheck -o jsonpath='{range .items[*]}{.metadata.name}{" selector="}{.spec.selector}{" conditions="}{.spec.unhealthyConditions}{"\n"}{end}'
oc get machinehealthcheck -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{" selector="}{.spec.selector}{" unhealthy="}{.spec.unhealthyConditions}{"\n"}{end}'
oc get machineset -A -o wide
oc get machines -A -o wide
oc get fenceagentsremediationtemplate -A
# Only if the SNR CRD is installed:
oc get selfnoderemediationtemplate -A
oc get nodes -l host-recovery-lab.example.com/pool --show-labels
oc get node "$SOURCE" "$TARGET" -o jsonpath='{range .items[*]}{.metadata.name}{" unschedulable="}{.spec.unschedulable}{" taints="}{.spec.taints}{"\n"}{end}'
~~~

**STOP** if any NodeHealthCheck, MachineHealthCheck, Machine/MachineSet auto-remediation or other
controller could act on SOURCE or TARGET, or the pool label is already on another node. A custom
MachineHealthCheck also disables NHC. Do not disable or edit existing controllers without a **locally
approved design**. If SOURCE is already unschedulable, do not run this case.

### Verify roles and readiness

~~~sh
oc get nodes "$SOURCE" "$TARGET" --show-labels | grep -Ec 'node-role.kubernetes.io/(control-plane|master)'   # expect 0
oc get nodes "$SOURCE" "$TARGET" -o jsonpath='{range .items[*]}{.metadata.name}{" Ready="}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'   # both True
oc get pods -A --field-selector spec.nodeName="$SOURCE" -o wide   # review: all disposable/approved
oc get pods -A --field-selector spec.nodeName="$TARGET" -o wide
~~~

### Namespaces and ordering

`$OPNS` must already exist (operators). Create `$NS` **before** preparing the disk (a dry-run does not create it):

~~~sh
oc get namespace "$NS" || oc create -f manifests/00-namespace.yaml
~~~

### Prepare the VM disk

Do this before the VM is applied. Never reuse a production PVC. Use your approved image workflow,
for example **Virtualization → Catalog** (create a VM from the RHEL 9 template/boot source in `$NS`) or a
clone/import from the approved boot-source image, so the result is a **dedicated PVC named
`case02-vm-rootdisk`**. CDI must have prepared the boot disk correctly for its volume mode:
`Filesystem` holds the bootable disk image; `Block` holds the bootable raw disk. The VM manifest
can reference either mode. Remove any temporary VM with the console's **keep disks** option and
**keep the PVC**. Storage must be **RWX shared** between both nodes; RWO is acceptable only if you
have validated, with the storage owner, that the CSI driver releases and re-attaches the volume on
the other node after the node is fenced.

~~~sh
oc get pvc case02-vm-rootdisk -n "$NS" -o jsonpath='{.status.phase} {.spec.volumeMode} {.spec.accessModes} {.spec.storageClassName}{"\n"}'
~~~

**Expected:** `Bound`, the agreed `Filesystem` or `Block` mode, and the approved access mode/class.
For PowerFlex SAN, shared raw-block storage can be appropriate; do not request RWX Filesystem
unless the driver supports it. Have the storage owner verify CSI/CSM resiliency behavior and
`OutOfServiceTaint` support for the installed versions before this test.

### Label the pool

Exactly two nodes. Record that you added the label so cleanup removes only it.

~~~sh
oc label node "$SOURCE" host-recovery-lab.example.com/pool=case02
oc label node "$TARGET" host-recovery-lab.example.com/pool=case02
oc get nodes -l host-recovery-lab.example.com/pool=case02 -o name   # exactly two
~~~

### Private directory and CA

Create this **before** the inventory and Secrets. It must be outside the checkout and not shared.
Copy the BMC CA bundle (PEM) there explicitly; it is used only by your workstation's `curl`
(the FAR pod trust is checked separately).

~~~sh
umask 077; PRIV=$(mktemp -d)
cp /PRIVATE/PATH/TO/APPROVED-BMC-CA.pem "$PRIV/bmc-ca.pem"
~~~

### Read-only Redfish inventory: node → BMC mapping

Only `GET`s; nothing is reset. `curl` prompts for the password, which never goes in argv, a file or
history. Never use `-k`.

~~~sh
read -r -p 'BMC username: ' BMC_USER
curl --user "$BMC_USER" --cacert "$PRIV/bmc-ca.pem" --fail --silent --show-error \
  https://REPLACE_SOURCE_BMC_HOST/redfish/v1/Systems
curl --user "$BMC_USER" --cacert "$PRIV/bmc-ca.pem" --fail --silent --show-error \
  https://REPLACE_SOURCE_BMC_HOST/redfish/v1/Systems/REPLACE_SOURCE_SYSTEM_ID | python3 -m json.tool | grep -E '"(UUID|SerialNumber|PowerState|HostName)"'
oc get node "$SOURCE" -o jsonpath='{.status.nodeInfo.systemUUID}{"\n"}'
~~~

Repeat for TARGET with its own BMC host and Systems id. **Critical gate:** each Redfish `UUID` (and a
serial or asset tag you trust) matches the `systemUUID` of the **same** node, and the Systems id is the
one in the template. A swapped mapping power-cycles the wrong server. If it cannot be matched, confirm
by a second independent method or **stop**.

### Fencing Secrets (from private local files)

Keys are `--username` and `--password` (upstream semantics). Values never go in the repository or argv.
Existing Secrets are left alone; the names below must not already exist.

~~~sh
for n in source target; do
  read -r -p "$n BMC username: " u; printf '%s' "$u" > "$PRIV/$n.user"
  read -r -s -p "$n BMC password: " p; printf '%s' "$p" > "$PRIV/$n.pass"; echo
done; unset u p
for n in source target; do
  oc create secret generic "case02-bmc-$n" -n "$OPNS" \
    --from-file=--username="$PRIV/$n.user" --from-file=--password="$PRIV/$n.pass"
done
oc label secret case02-bmc-source case02-bmc-target -n "$OPNS" host-recovery-lab.example.com/case=02
~~~

Use a least-privilege BMC account allowed to read power state and reset. Files hold the value with
**no trailing newline**. Keep `$PRIV` until the trust check is done, then `shred -u "$PRIV"/*` and remove it.

### BMC certificate trust (both nodes)

`fence_redfish` verifies TLS unless `--ssl-insecure` is passed and has no CA-file option, so trust comes
from the FAR image. Check with the **installed** agent: a read-only `status` for **each** node, credentials
from the private files by stdin. Select a **Ready FAR manager on a node other than SOURCE**,
so these checks prove the fencing path from a controller that survives the fault. Record that pod/node
and use the same pod for the later log capture. `jq` is required; adapt the name prefix only after
checking the installed deployment identity. A missing surviving replica means **stop**.

~~~sh
POD=$(oc get pods -n "$OPNS" -o json | jq -r --arg source "$SOURCE" '
  [.items[]
   | select(.metadata.name | startswith("fence-agents-remediation-controller-manager-"))
   | select(.spec.nodeName != $source)
   | select(any(.status.conditions[]?; .type == "Ready" and .status == "True"))]
  | first | .metadata.name // empty')
test -n "$POD" || { echo 'STOP: no surviving Ready FAR manager pod found'; exit 1; }
oc get pod "$POD" -n "$OPNS" -o wide   # record pod and its node, which must differ from SOURCE
oc exec -n "$OPNS" "$POD" -c manager -- fence_redfish -o metadata | grep -Ei 'systems-uri|redfish-uri|ssl|action'
for n in source target; do
  case "$n" in
    source) H=REPLACE_SOURCE_BMC_HOST; S=REPLACE_SOURCE_SYSTEM_ID ;;
    target) H=REPLACE_TARGET_BMC_HOST; S=REPLACE_TARGET_SYSTEM_ID ;;
  esac
  printf 'ip=%s\nusername=%s\npassword=%s\nsystems-uri=/redfish/v1/Systems/%s\naction=status\n' \
    "$H" "$(cat "$PRIV/$n.user")" "$(cat "$PRIV/$n.pass")" "$S" \
    | oc exec -i -n "$OPNS" "$POD" -c manager -- fence_redfish
done
~~~

The stdin `name=value` form is the generic fence-agents convention; confirm against the metadata. **Expected:**
`Status: ON` for both. A TLS error means the image does not trust the BMC CA: **STOP**. `--ssl-insecure`
is never the default and needs separate written, local risk acceptance by the owner. Use only options in
the installed metadata.

### Dry-run

Provided, **not performed by the author**. Run after filling placeholders (namespace and CRDs must exist).

~~~sh
oc apply --dry-run=server -f manifests/01-far-template.yaml
oc apply --dry-run=server -f manifests/02-nhc-paused.yaml
oc apply --dry-run=server -f manifests/03-recovery-vm.yaml
~~~

Fix any rejection from the installed schema. A dry-run does not prove the fence works.

### Create

First confirm the reserved names are unused. Each read below must return **NotFound**;
an authorization or connection error is not evidence of absence. If anything exists, stop
and review its ownership instead of overwriting it. The approved disk and namespace are
prepared separately and are intentionally retained.

~~~sh
oc get fenceagentsremediationtemplate case02-far-redfish-reboot -n "$OPNS"
oc get nodehealthcheck case02-host-recovery
oc get vm recovery-vm -n "$NS"
~~~

Then create individually, in order: FAR template, **NHC (paused)**, VM (Halted).

~~~sh
oc create -f manifests/01-far-template.yaml
oc create -f manifests/02-nhc-paused.yaml
oc create -f manifests/03-recovery-vm.yaml
~~~

The VM's **Overview** page should read **Stopped** (preparation state; the VM has not been
started and nothing has been tested):

![recovery-vm on its Overview page with status Stopped](images/01-new-vm-stopped.png)

## Gates

Sign gates 1–7 in the [results sheet](RESULTS-TEMPLATE.md) before activation at customer step 5.
Gate 8 is the activation check: complete it before introducing the fault at step 7.

1. **Paused and scoped.** While paused, NHC (v0.12 reference) reports observed/healthy **0/0** and skips
   healthy-node cleanup, so **do not use its counts**. Check instead that `pauseRequests` holds
   `case02-setup-hold` and that the selector matches exactly the two Ready worker nodes:
   ~~~sh
   oc get nodehealthcheck case02-host-recovery -o jsonpath='{.status.phase} {.spec.pauseRequests}{"\n"}'
   oc get nodes -l host-recovery-lab.example.com/pool=case02,node-role.kubernetes.io/worker,'!node-role.kubernetes.io/control-plane','!node-role.kubernetes.io/master'
   ~~~
   Exactly two nodes, both Ready.
2. **Not disabled.** The Disabled evaluation runs before the pause check, so it is valid while paused:
   `oc get nodehealthcheck case02-host-recovery -o jsonpath='{.status.conditions}'` shows Disabled **False** (no
   custom MachineHealthCheck, no `RemediationTemplateNotFound`/`Invalid`).
3. **Mapping and trust** verified for both nodes.
4. **Kubelet** on SOURCE: `ssh core@SOURCE 'systemctl is-enabled kubelet; systemctl is-active kubelet'` prints `enabled`, `active`.
5. **Capacity and storage:** TARGET has room; PVC Bound and usable from TARGET.
6. **VM running on SOURCE** (runbook step 2) and SOURCE cordoned (step 4).
7. **Abort rule, outage budget and escalation contact** agreed; a second person holds iDRAC console access.
8. **Activation check (runbook step 5):** with SOURCE cordoned and Ready and the pause removed, NHC
   must show phase `Enabled`, **observed 2, healthy 2** before the fault. NHC v0.12 has no `Unschedulable` filter,
   so a cordoned Ready node counts as healthy. If it does not, pause again and **do not run the fault**.

## Evidence capture

The FAR object is created and deleted by NHC and may be gone before anyone looks. Start this **before the
fault**, with three terminals, saving to a private directory **outside the checkout**. Stop each with
**Ctrl+C** after recovery (runbook step 10).

~~~sh
mkdir -p "$HOME/.local/state" && EVID=$(mktemp -d "$HOME/.local/state/case02-evidence.XXXXXX") && echo "$EVID"
# terminal A (export OPNS EVID there first)
oc get fenceagentsremediation -n "$OPNS" --watch --output-watch-events -o json > "$EVID/far.json"
# terminal B (export NS EVID there first)
oc get vmi -n "$NS" --watch --output-watch-events -o json > "$EVID/vmi.json"
# terminal C
oc get nodes -l host-recovery-lab.example.com/pool=case02 --watch --output-watch-events -o json > "$EVID/nodes.json"
~~~

Evidence may contain environment details: keep it private. A single VMI API read does not by itself prove the
old guest stopped, so corroborate with the **iDRAC event/lifecycle log** (power-cycle time for SOURCE) and
SOURCE's **node boot ID** changing.

### Fence order

Captured, not post-hoc: the remediation's `FenceAgentActionSucceeded=True` `lastTransitionTime` must be earlier
than the new VMI's `creationTimestamp` (`jq` required; times have one-second resolution).

~~~sh
jq -r 'select(.object.status.conditions != null) | .object.status.conditions[] | select(.type=="FenceAgentActionSucceeded" and .status=="True") | .lastTransitionTime' "$EVID/far.json" | sort -u | head -n 1
jq -r 'select(.type=="ADDED") | .object.metadata.uid + " " + .object.metadata.creationTimestamp' "$EVID/vmi.json"
jq -r 'select(.object.metadata.name=="REPLACE_SOURCE_NODE") | .object.status.nodeInfo.bootID' "$EVID/nodes.json" | uniq
~~~

**Missing or tied fence evidence is Blocked, not Pass**, unless the iDRAC log clearly shows the reset before
the new instance was created.

## The fault and what to watch

Fault: `sudo systemctl stop kubelet` over SSH on SOURCE. One reversible service failure. Running guests
continue until the power-cycle, which is why fencing must precede the restart. Typical sequence: node Unknown
about 1 minute; NHC unhealthy after 300 s (phase `Remediating`, **healthy 1**); a FenceAgentsRemediation named
after SOURCE; FAR taints the node and runs the agent (up to 3 tries of up to 60 s); then the out-of-service
taint; the VM restarts on TARGET. Allow the configured 300-second unhealthy duration and the
agreed controller-response allowance. If no remediation follows by the agreed limit, abort and escalate;
do not interpret the normal detection wait as a failure.

~~~sh
oc logs -n "$OPNS" "$POD" -c manager --since=30m
oc get events -n "$OPNS" | grep -i remediation
~~~

**Back-out:** only before a remediation exists, `sudo systemctl start kubelet` over SSH or via the iDRAC
virtual console. **Never** force-delete the VM instance, the node or finalizers, and never reboot by hand
as an automatic pass.

## Abort and pause

Pausing (`pauseRequests`) stops **new** remediations immediately. It does **not** cancel one in flight, and while paused
NHC also skips cleanup of remediation objects for healthy nodes, so a paused NHC can leave the FAR object (and its
taints) in place after SOURCE recovers.

- **Normal end:** wait until the FAR object is gone, SOURCE is Ready and the remediation/out-of-service taints are
  cleared, **then** pause (runbook step 10).
- **Abort before a remediation exists:** pause, then back out the fault.
- **Abort or budget exceeded with a remediation in flight:** pausing may be used to stop *new* ones, but do not leave
  the in-flight remediation unbounded. Escalate to the owner at the budget limit. The owner decides, coordinated
  with you, to remove the pause so NHC's healthy-node cleanup can finish, or to restore the host through the iDRAC
  console. Record **Fail** if manual recovery was needed. Never delete the object, taints, VM instance or node by hand.
- Before any deletion, confirm the controllers are quiet and the BMC reports the server `On` and not mid-reset.

## Cordon ownership

SOURCE was schedulable in preflight and the customer cordons it at step 4, so you own that cordon. Uncordon it
only if no one else has cordoned it since. Never restore a cordon you did not make.

## Cleanup

Only after the remediation is complete and the NHC is re-paused. Remove only what you created and recorded.

| Object | Action |
| --- | --- |
| NodeHealthCheck `case02-host-recovery`, FAR template `case02-far-redfish-reboot` | Delete (label `host-recovery-lab.example.com/case=02`) once no FAR object exists |
| Secrets `case02-bmc-source`, `case02-bmc-target` | Delete only the test-created Secrets; preserve existing BMC accounts |
| VM `recovery-vm` | Delete the VM only; **keep the PVC and its data** unless its owner approves |
| Node label `host-recovery-lab.example.com/pool` | Remove from the nodes you labelled |
| Cordon on SOURCE | Uncordon only if you own it |
| Namespace `host-recovery-lab` | Keep while it holds the approved PVC |
| Evidence and `$PRIV` | Keep evidence private; shred `$PRIV` |
| Operators, `openshift-workload-availability`, OperatorGroup | **Keep** (shared) |

~~~sh
oc delete nodehealthcheck case02-host-recovery
oc delete fenceagentsremediationtemplate case02-far-redfish-reboot -n "$OPNS"
oc delete secret case02-bmc-source case02-bmc-target -n "$OPNS"
oc delete vm recovery-vm -n "$NS"
oc label node "$SOURCE" "$TARGET" host-recovery-lab.example.com/pool-
~~~

## Reference sources

Reference versions only; they are **not** the client's versions. The installed operators and schemas gate everything.

| Component | Reference |
| --- | --- |
| Node Health Check Operator | [v0.12.0](https://github.com/medik8s/node-healthcheck-operator/tree/v0.12.0), `internal/controller/nodehealthcheck_controller.go` (pause check precedes counting and healthy cleanup; no `Unschedulable` filter) |
| Fence Agents Remediation | [v0.8.0](https://github.com/medik8s/fence-agents-remediation/tree/v0.8.0) (CR fields, Secret keys, strategies) |
| fence_redfish | [ClusterLabs commit aed0666](https://github.com/ClusterLabs/fence-agents/blob/aed06661b0b6fd4e69d44672f59bb8d3eecccc67/agents/redfish/fence_redfish.py) (`--ip`, `--systems-uri`, TLS verify unless `--ssl-insecure`) |
| Red Hat docs (4.21) | [Fence Agents Remediation](https://docs.redhat.com/en/documentation/workload_availability_for_red_hat_openshift/4.21-0/html/remediation_fencing_and_maintenance/fence-agents-remediation-operator-remediate-nodes), [Node Health Check](https://docs.redhat.com/en/documentation/workload_availability_for_red_hat_openshift/4.21-0/html/remediation_fencing_and_maintenance/node-health-check-operator) |
