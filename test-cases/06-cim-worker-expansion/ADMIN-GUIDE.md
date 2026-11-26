# Administrator guide: CIM worker expansion

> **Status: results verified with a 4.21 hub and 4.22 workload cluster.**
> Registration, installation, added Ready capacity and a Running check pod were
> exercised. Cleanup was held for review. A 4.21 workload cluster was not tested;
> this remains manual expansion.

Reference for commands and safety detail; the step-by-step flow is the
[runbook](RUNBOOK.md) and is not repeated here. This case is a **manual**
expansion, not policy- or load-triggered autoscaling.

Official reference: [ACM 2.16 — Clusters](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.16/html-single/clusters/index).
Installing ACM/MCE and importing the workload cluster are pre-existing
prerequisites and are out of scope here.

Terms: **CIM** is Central Infrastructure Management. **BMC** is the server's
remote-management controller. An **InfraEnv** (the "inventory") is the
host-inventory object on the hub.

## Prepare

### Requirements

- Existing, configured CIM and a managed workload cluster. Do not create or
  initialise the hub.
- A host-inventory InfraEnv, reused **unchanged**: do not edit its pull secret,
  SSH key, NTP, proxy or labels.
- A spare approved physical host with BMC access and **only disposable disks
  connected**. Disconnect disks or unpresent SAN LUNs containing data or another
  OS before discovery. The install disk will be overwritten.
- A BMC address with the vendor-appropriate URI. Dell iDRAC uses
  `idrac-virtualmedia://`, not the generic `redfish-virtualmedia://`.
- BMC credentials stay private. No password goes in this repository.

### Administrator preparation (runbook A4)

This is the one entry point for preparation. Work on the **hub**, in one
terminal, and do the four steps in order. You hand back a usable inventory, a
private BMC Secret and a filled, paused host file. Do not upload the file or
start discovery here.

**1. Set the values** (names from runbook A1):

~~~sh
export INV_NS='REPLACE_INVENTORY_NAMESPACE'     # namespace of the host-inventory InfraEnv
export INV='REPLACE_INFRAENV_NAME'
export HOST='REPLACE_SPARE_HOST_NAME'
~~~

**2. Choose the inventory.** Reuse an existing one, unchanged, if it passes
this read-only check: `clusterRef` empty and `autoApprove` not `true`.

~~~sh
oc get infraenv "$INV" -n "$INV_NS" -o jsonpath='{.metadata.name}{" clusterRef="}{.spec.clusterRef}{" autoApprove="}{.spec.agentApproval.autoApprove}{"\n"}'
oc get agent -n "$INV_NS" -o custom-columns=NAME:.metadata.name,APPROVED:.spec.approved,ROLE:.spec.role,CLUSTER:.spec.clusterDeploymentName.name,STAGE:.status.progress.currentStage
oc get baremetalhost -n "$INV_NS"
~~~

Hosts found by BMC can still be approved automatically, so keep the new host
unassigned until the disk review. If `clusterRef` is set the inventory is not
suitable. Create a separate one (optional):

1. In **Host inventory**, note the namespace and approved pull-Secret name of
   the existing inventory. Do not display or copy the Secret's contents.
2. Fill [`03-unassigned-inventory.yaml`](manifests/03-unassigned-inventory.yaml)
   with a new inventory name, that namespace, the existing pull-Secret name and
   your SSH public key. Match the OpenShift version to the workload cluster.
3. The example uses DHCP. For bonds, VLANs or static IPs, have the network
   administrator supply a host-specific NMStateConfig labelled to match the
   template's selector, including the storage network if the worker will run VMs.
4. Console: **Quick create (+) → Import YAML**, choose the inventory project,
   paste the definition, **Create**. Or:
   ~~~sh
   oc create -f manifests/03-unassigned-inventory.yaml
   ~~~
5. Wait until the new inventory shows its discovery image. Then set `INV` and
   `INV_NS` (step 1) to it.

**3. Create the private BMC Secret.** Use a separate Secret for this host: the
host controller can take ownership of it and remove it when the host is deleted.
Create it from files, never from literals. The keys are `username` and
`password`. (The console's **With BMC Form** takes them directly; this runbook
uses the paused file, which needs the Secret.)

~~~sh
umask 077; PRIV=$(mktemp -d)
read -r -p 'BMC username: ' u; printf '%s' "$u" > "$PRIV/username"
read -r -s -p 'BMC password: ' p; printf '%s' "$p" > "$PRIV/password"; echo
unset u p
oc create secret generic "$HOST-bmc-secret" -n "$INV_NS" \
  --from-file=username="$PRIV/username" --from-file=password="$PRIV/password"
rm -f "$PRIV/username" "$PRIV/password"
rmdir "$PRIV"
unset PRIV
~~~

No Secret YAML is shipped, so a template cannot be applied by mistake.

**4. Fill the paused host file.** Fill
[`02-baremetalhost-paused.yaml`](manifests/02-baremetalhost-paused.yaml) with
`$HOST`, `$INV_NS`, `$INV`, the BMC address and the Secret name
`$HOST-bmc-secret`. Keep the file outside the repository. It starts paused with
cleaning disabled and certificate verification on, and holds the Secret's name,
not its contents. Turning certificate verification off is a host-specific
exception that needs written owner approval.

Disabled cleaning does not protect other disks or boot records, and the
Assisted Installer's disk preparation is separate. Only disposable disks may be
connected; the **Format** checkbox is no protection.

Return to the runbook (section B).

### Start discovery (runbook C1, after the upload)

The runbook's C1 does the upload. Right after it, with `INV_NS` and `HOST`
set, confirm the saved settings, then start discovery:

~~~sh
oc get baremetalhost "$HOST" -n "$INV_NS" -o jsonpath='{.spec.automatedCleaningMode}{" "}{.metadata.annotations.baremetalhost\.metal3\.io/paused}{"\n"}'
# Expected: disabled true   (if not, stop; do not start discovery)
oc patch baremetalhost "$HOST" -n "$INV_NS" --type=merge -p '{"spec":{"online":true}}'
oc annotate baremetalhost "$HOST" -n "$INV_NS" baremetalhost.metal3.io/paused-
~~~

Then do the runbook's disk review (C2) before approving (C2) or assigning (C3).

For reference, **Add hosts → With BMC form** shows the fields below. It also
offers NMState and MAC-to-interface mapping for static or bonded networks.
The runbook's YAML upload makes the cleaning and TLS settings explicit.

![BMC form fields before any private values are entered](images/01-bmc-form.png)

## Observe the host (hub)

Registration, approval and assignment are separate stages. Check each before moving on.

BMC registration can approve the resulting Agent automatically even when the
InfraEnv does not approve ISO-discovered hosts automatically. Keep this test's
inventory unassigned: no `spec.clusterRef`. Review the disk before assigning the
host to any cluster; assignment can immediately start installation.

![Disk review before assignment; serial numbers are redacted](images/09-discovered-disks.png)

~~~sh
oc get baremetalhost "$HOST" -n "$INV_NS" -o jsonpath='{.status.provisioning.state} {.status.poweredOn}{"\n"}'
oc get agent -n "$INV_NS" -o custom-columns=NAME:.metadata.name,APPROVED:.spec.approved,ROLE:.spec.role,STAGE:.status.progress.currentStage
oc get agent AGENT_NAME -n "$INV_NS" -o jsonpath='{.status.inventory.disks}{"\n"}'     # confirm the install disk
~~~

## Workload cluster checks

Switch to the workload cluster context before running these.

~~~sh
oc get nodes -l node-role.kubernetes.io/worker,'!node-role.kubernetes.io/control-plane'
oc get node REPLACE_NEW_WORKER_NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}{"\n"}'
oc describe node REPLACE_NEW_WORKER_NODE | grep -A8 -i 'Allocatable'
oc get csr | grep -i pending      # only if the node stays pending
~~~

Approve a CSR only if you recognise it as this host's bootstrap request.

## Troubleshooting

- **Host not discovered:** check BMC address form, boot MAC, credentials and
  network path to the BMC; see the host's conditions with `oc describe baremetalhost`.
- **Agent not approved or not available:** approval is a separate action
  (runbook C2); assignment needs an approved Agent.
- **Install fails or stalls:** read the Agent's conditions and the installation
  events in the console; confirm the install disk and cluster were correct.
- **Node pending:** check pending CSRs (above), then the Agent stage.

Stop and ask the owner before repeating an installation on a host.

## Cleanup summary

| Object | Action |
| --- | --- |
| `new-worker-check` pod | Delete (it may already be gone if Case 02 recovery removed it) |
| `cim-expansion-check` project | Delete only if this run created it and it is empty |
| New worker | Leave installed for the next agreed test |
| Inventory InfraEnv | Leave unchanged |
| BMC Secret referenced by the installed host | Keep; the host registration still needs it |
| Private input files | Removed after Secret creation |
