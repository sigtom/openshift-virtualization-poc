# Runbook - placement, spreading and descheduler-driven live migration (RHEL 9)

Each stage: **Console** step, then **CLI** equivalent, then **Expected** result
in both. Console steps follow the documented OpenShift 4.21 console; menu
names can differ by version. Console verification belongs to the presenter
and is pending until recorded in `RESULTS-TEMPLATE.md`; a CLI pass never
counts as a console pass. Run commands from this directory.

## 0. Conventions

```sh
export NS=virt-scheduling-lab
export DS_NS=openshift-kube-descheduler-operator
export PC=virt-scheduling-lab-evictable
export THRESHOLD=-999999999
# Replace with the client's approved values:
export NODE_A='worker-a' NODE_B='worker-b' NODE_C='worker-c'
export RWX_SC='replace-with-rwx-storage-class'
export LAB_EVIDENCE="$HOME/virt-lab-evidence-$(date +%Y%m%d-%H%M%S)"   # private, never in Git
mkdir -p "$LAB_EVIDENCE"
printf '%s\n' "$NODE_A" "$NODE_B" "$NODE_C" > "$LAB_EVIDENCE/approved-nodes.txt"
LAB_VMS="placement-01 spread-01 spread-02 spread-03 negative-01"
```

Every node used below (including TARGET in step 7) is one of NODE_A/B/C.
Tools: `oc`, `jq`, `curl`, and `virtctl` (console **?** > **Command Line Tools**).

| Node label | Meaning | Set on |
|---|---|---|
| `scheduling-lab.example.com/eligible=true` | approved for placement-01 | NODE_A, later moved |
| `scheduling-lab.example.com/spread-pool=true` | approved pool for spread VMs | NODE_A, NODE_B, NODE_C |
| `scheduling-lab.example.com/unsatisfiable` | must never exist | nobody |

Console - node label: **Compute > Nodes** > node > **Actions > Edit labels** >
`key=value` > **Save**; remove by clicking **x** on the chip > **Save**.

## 1. Preflight (read-only, on the client cluster)

**Stop** on any failure. Do not work around it by enabling features, applying
MachineConfigs or removing taints.

### 1.1 Versions, operators, CRDs, schema

Console: **Administration > Cluster Settings** (version); **Operators >
Installed Operators** (newer consoles: **Ecosystem > Installed Operators**):
OpenShift Virtualization and Kube Descheduler Operator show **Succeeded**.

```sh
oc get clusterversion version -o jsonpath='{.status.desired.version}{"\n"}'
oc get csv -n openshift-cnv
oc get csv -n $DS_NS
oc get hco -n openshift-cnv kubevirt-hyperconverged \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}'
oc get crd kubedeschedulers.operator.openshift.io virtualmachines.kubevirt.io \
  virtualmachineinstancemigrations.kubevirt.io datavolumes.cdi.kubevirt.io datasources.cdi.kubevirt.io
# profiles this descheduler release supports (from the HCOMisconfiguredDescheduler runbook)
oc get crd kubedeschedulers.operator.openshift.io -o json \
  | jq '.spec.versions[] | select(.name=="v1").schema.openAPIV3Schema.properties.spec.properties.profiles.items.enum[]'
oc explain kubedescheduler.spec.profileCustomizations.thresholdPriority --api-version=operator.openshift.io/v1
oc explain kubedescheduler.spec.profileCustomizations.devEnableEvictionsInBackground --api-version=operator.openshift.io/v1
oc explain kubedescheduler.spec.profileCustomizations.namespaces --api-version=operator.openshift.io/v1
oc explain kubedescheduler.spec.evictionLimits --api-version=operator.openshift.io/v1
oc explain virtualmachine.spec.template.spec.priorityClassName --api-version=kubevirt.io/v1
oc explain virtualmachine.spec.dataVolumeTemplates --api-version=kubevirt.io/v1
oc explain virtualmachineinstancemigration.spec.vmiName --api-version=kubevirt.io/v1
```

Expected: client version (4.21.31); both CSVs `Succeeded`; HCO
`Available=True`, `Degraded=False`; all CRDs exist; the profile enum contains
`AffinityAndTaints`, `LongLifecycle`, `EvictPodsWithLocalStorage`,
`EvictPodsWithPVC`; every `oc explain` prints a description.

### 1.2 RHEL 9 boot source

Console: **Virtualization > Bootable volumes** (project
`openshift-virtualization-os-images`): `rhel9` is listed and available.

```sh
oc get datasource rhel9 -n openshift-virtualization-os-images \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.reason}{"\n"}{end}{.spec.source}{"\n"}'
oc auth can-i create datavolumes.cdi.kubevirt.io --subresource=source -n openshift-virtualization-os-images
```

Expected: `Ready=True`; the clone permission check prints `yes`.

Resolve the DataSource's actual source before using the default 40Gi target disk.
The console's Bootable volume details link to its source PVC or VolumeSnapshot.
For the normal PVC-backed source, copy its name/namespace from the first command:

```sh
oc get datasource rhel9 -n openshift-virtualization-os-images -o jsonpath='{.spec.source}{"\n"}'
# Replace these with the source reported above; do not guess a versioned PVC name.
SOURCE_PVC='actual-source-pvc'
SOURCE_NS='openshift-virtualization-os-images'
oc get pvc "$SOURCE_PVC" -n "$SOURCE_NS" -o jsonpath='{.status.phase}{" capacity="}{.status.capacity.storage}{"\n"}'
```

For a snapshot-backed source, inspect the reported VolumeSnapshot instead:
`oc get volumesnapshot ACTUAL_SNAPSHOT -n ACTUAL_NAMESPACE -o yaml`.
Require `readyToUse: true` and inspect `status.restoreSize`. Stop if the source
cannot be resolved or is not ready. Its capacity/restore size must fit the
40Gi disk requested in each VM's DataVolume template; otherwise increase
**all five** disk requests before applying the YAML. Allow the storage
provider's filesystem/clone overhead in the capacity plan.

### 1.3 RWX storage

Console: **Storage > StorageClasses** > `$RWX_SC`; **Storage > StorageProfiles**
(if shown) lists ReadWriteMany / Filesystem.

```sh
oc get storageclass "$RWX_SC" -o jsonpath='{.provisioner}{" binding="}{.volumeBindingMode}{"\n"}'
oc get storageprofile "$RWX_SC" -o jsonpath='{.status.claimPropertySets}{" clone="}{.status.cloneStrategy}{"\n"}'
```

Expected: the class exists; `claimPropertySets` includes `ReadWriteMany` with
`Filesystem`. Five root disks = 5 x 40 GiB = **200 GiB guest disk requests**; confirm with
the storage owner that capacity plus provisioner headroom is available (a
`copy`/host-assisted clone writes the full image per disk; snapshot or CSI
clones may be thin). With `WaitForFirstConsumer`, clones start only when a VM
first starts.

### 1.4 Nodes and compute headroom

Console: **Compute > Nodes**: NODE_A/B/C **Ready**, no lab labels.

```sh
oc get nodes $NODE_A $NODE_B $NODE_C -L kubevirt.io/schedulable -L kubernetes.io/arch
oc get nodes $NODE_A $NODE_B $NODE_C -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
oc get nodes -l scheduling-lab.example.com/eligible
oc get nodes -l scheduling-lab.example.com/spread-pool
oc get nodes -l scheduling-lab.example.com/unsatisfiable
for n in $NODE_A $NODE_B $NODE_C; do oc describe node "$n" | sed -n '/Allocated resources/,/Events/p'; done
oc get kubevirt -n openshift-cnv -o jsonpath='{.items[0].spec.configuration.migrations}{"\n"}'
```

Expected: Ready, `kubevirt.io/schedulable=true`, `amd64`, no
`NoSchedule`/`NoExecute` taints; the three lab-label queries return nothing
cluster-wide. Fixed footprint: at most 4 running VMs plus 1 migration target
(negative-01 stays Pending), i.e. up to 5-6 launcher pods of 2 GiB guest
memory plus virt-launcher overhead each, plus short-lived CDI clone pods.
Each approved node needs room for two launchers within its allocatable
requests. Migration limits: blank means platform defaults; fail only if
`parallelMigrationsPerCluster` or `parallelOutboundMigrationsPerNode` is
explicitly `0`.

### 1.5 Namespace and PriorityClass must be new

```sh
oc get namespace $NS            # Expected: NotFound
oc get priorityclass $PC        # Expected: NotFound
```

If either exists, stop unless it is positively this test case's own object:
its UID equals the one recorded in an earlier run's evidence folder, and (for
the namespace) a full inventory shows only lab objects:

```sh
oc api-resources --verbs=list --namespaced -o name > "$LAB_EVIDENCE/ns-types.txt"
fail=0
while read -r r; do oc get "$r" -n $NS --ignore-not-found -o name || fail=1; done \
  < "$LAB_EVIDENCE/ns-types.txt" > "$LAB_EVIDENCE/ns-inventory.txt"
[ "$fail" = 0 ] && echo "inventory complete" || echo "INVENTORY INCOMPLETE - stop"
cat "$LAB_EVIDENCE/ns-inventory.txt"
```

Errors are not hidden: any type that cannot be listed makes the inventory
incomplete, and an incomplete inventory is a stop (have a cluster admin run
it). Allowed content: the five VMs and their VMIs, launcher/CDI pods,
DataVolumes, PVCs, migrations, plus the namespace's automatic objects
(default ServiceAccounts and their secrets, `kube-root-ca.crt` and
`openshift-service-ca.crt`, default RoleBindings). Never reuse a foreign
namespace or PriorityClass.

### 1.6 Pod priority inventory (protects every non-lab workload)

LongLifecycle's `LowNodeUtilization` ignores the namespace include, so
`thresholdPriority` is the boundary. Every pod outside the lab namespace must
have an explicit numeric priority >= `$THRESHOLD`, must not use `$PC`, and must
not carry `descheduler.alpha.kubernetes.io/evict` (that annotation bypasses the
evictor's filters). A missing (`null`) priority is **not** zero: it is a stop.

```sh
if oc get pods -A -o json > "$LAB_EVIDENCE/pods-all.json"; then echo "pod list complete"; else echo "INVENTORY INCOMPLETE - stop"; fi
jq '.items | length' "$LAB_EVIDENCE/pods-all.json"
jq -r --arg ns "$NS" --arg pc "$PC" --argjson t "$THRESHOLD" '
  .items[]
  | select(.metadata.namespace != $ns)
  | select(.spec.priority == null
           or .spec.priority < $t
           or .spec.priorityClassName == $pc
           or ((.metadata.annotations // {}) | has("descheduler.alpha.kubernetes.io/evict")))
  | "\(.metadata.namespace)/\(.metadata.name) priority=\(.spec.priority) class=\(.spec.priorityClassName // "-")"
' "$LAB_EVIDENCE/pods-all.json" | tee "$LAB_EVIDENCE/priority-violations.txt"
# PriorityClasses below the threshold or global defaults
oc get priorityclass -o json | jq -r --argjson t "$THRESHOLD" '
  .items[] | select(.value < $t or .globalDefault == true)
  | "\(.metadata.name) value=\(.value) globalDefault=\(.globalDefault)"'
```

Expected: the pod list is complete; `priority-violations.txt` is **empty**;
the class query shows no class with a value below the threshold (a
`globalDefault` class is acceptable only if its value is >= the threshold).
Agree with the cluster owner that, during the short test window, no new pod
outside the lab uses `$PC` or the force-evict annotation. Console: there is no
single view for this; use the CLI result.

### 1.7 Permissions

```sh
oc auth can-i create namespaces
oc auth can-i create priorityclasses.scheduling.k8s.io
oc auth can-i list pods -A
oc auth can-i patch nodes
oc auth can-i patch kubedeschedulers.operator.openshift.io -n $DS_NS
oc auth can-i get pods --subresource=log -n $DS_NS
oc auth can-i get routes -n openshift-monitoring
```

Expected: `yes` for all. After step 2.1 also check in `$NS`: `create
virtualmachines.kubevirt.io`, `patch virtualmachines.kubevirt.io`, `create
virtualmachineinstancemigrations.kubevirt.io`, `get
virtualmachineinstances.subresources.kubevirt.io --subresource=console`.

## 2. Create the lab

### 2.1 Namespace

- Console: top bar **+** (Import YAML) > paste `manifests/00-namespace.yaml` > **Create**.
- CLI:
  ```sh
  oc create -f manifests/00-namespace.yaml
  oc get namespace $NS -o jsonpath='{.metadata.uid}{"\n"}' | tee "$LAB_EVIDENCE/namespace-uid.txt"
  ```
- Expected: **Home > Projects** lists `virt-scheduling-lab`; UID recorded.

### 2.2 Reserved PriorityClass

- Console: **+** (Import YAML) > paste `priorityclass/virt-scheduling-lab-evictable.yaml` > **Create**.
- CLI:
  ```sh
  oc create -f priorityclass/virt-scheduling-lab-evictable.yaml
  oc get priorityclass $PC -o jsonpath='{.metadata.uid}{" value="}{.value}{" globalDefault="}{.globalDefault}{" preemption="}{.preemptionPolicy}{"\n"}' \
    | tee "$LAB_EVIDENCE/priorityclass-uid.txt"
  ```
- Expected: value `-1000000000`, `globalDefault=false`, `preemption=Never`; UID recorded.
  Console: **Home > Search** > `PriorityClass` > `virt-scheduling-lab-evictable`.

### 2.3 VMs (after replacing the storage class)

- Console: select project `virt-scheduling-lab` > **+** (Import YAML) > paste
  `01-placement-vm.yaml`, change `storageClassName: REPLACE_WITH_RWX_STORAGE_CLASS`
  to the client class, **Create**. Repeat for `02-spread-vms.yaml` (three
  occurrences) and `03-negative-unsatisfiable-vm.yaml`.
- CLI:
  ```sh
  for f in manifests/01-placement-vm.yaml manifests/02-spread-vms.yaml manifests/03-negative-unsatisfiable-vm.yaml; do
    sed "s/REPLACE_WITH_RWX_STORAGE_CLASS/$RWX_SC/g" "$f" > "$LAB_EVIDENCE/$(basename "$f")"
  done
  grep -l REPLACE_WITH "$LAB_EVIDENCE"/0*.yaml && echo "PLACEHOLDER LEFT - stop"
  oc create -f "$LAB_EVIDENCE/01-placement-vm.yaml" -f "$LAB_EVIDENCE/02-spread-vms.yaml" \
            -f "$LAB_EVIDENCE/03-negative-unsatisfiable-vm.yaml"
  oc get vm -n $NS
  ```
- Expected: five VMs, all **Stopped** (`Halted`), no VMI.

### 2.4 Wait for the root-disk clones

- Console: each VM may show **Provisioning** / a DataVolume progress; **Storage >
  PersistentVolumeClaims** (project `virt-scheduling-lab`) shows `*-rootdisk` **Bound**.
- CLI:
  ```sh
  oc get dv,pvc -n $NS
  for vm in $LAB_VMS; do oc wait dv/"$vm"-rootdisk -n $NS --for=condition=Ready --timeout=30m; done
  ```
- Expected: each DataVolume phase `Succeeded`, each PVC `Bound`, access mode
  `RWX`. With a `WaitForFirstConsumer` class the DVs wait (`PendingPopulation`
  / `WaitForFirstConsumer`) until the VM first starts; then wait after starting
  (negative-01's disk never populates in that case, which is fine). Do not
  start a VM whose disk is still cloning.

## 3. Test 01 - placement (required)

1. Label NODE_A eligible - Console: Edit labels on NODE_A.
   CLI: `oc label node $NODE_A scheduling-lab.example.com/eligible=true`
2. Start placement-01 - Console: **Virtualization > VirtualMachines** >
   `placement-01` > **Actions > Start**.
   CLI: `oc patch vm placement-01 -n $NS --type merge -p '{"spec":{"runStrategy":"Always"}}'`
3. Verify.
   - Console: **Overview**: Running, **Node** = NODE_A; **Configuration >
     Scheduling** shows the affinity rule.
   - CLI:
     ```sh
     oc wait vmi placement-01 -n $NS --for=condition=Ready --timeout=10m
     oc get vmi placement-01 -n $NS -o wide
     oc get vmi placement-01 -n $NS -o jsonpath='{range .status.conditions[*]}{.type}={.status}{" "}{end}{"\n"}'
     oc get pod -n $NS -l vm.kubevirt.io/name=placement-01 \
       -o jsonpath='{range .items[*]}{.metadata.name}{" priority="}{.spec.priority}{" class="}{.spec.priorityClassName}{"\n"}{end}'
     ```
   - Expected: node NODE_A; `Ready=True`, `LiveMigratable=True`,
     `AgentConnected=True`; launcher pod `priority=-1000000000
     class=virt-scheduling-lab-evictable` exactly. If not LiveMigratable, stop
     (check RWX access mode and `evictionStrategy`).
4. Guest identity - Console: **Console** tab > **Serial console** > Enter; a
   `cloud-user@placement-01` prompt appears (first boot can take a few
   minutes). CLI: `virtctl console placement-01 -n $NS` (leave with `Ctrl+]`). Run:
   ```sh
   cat /proc/sys/kernel/random/boot_id
   cut -d' ' -f1 /proc/uptime
   sudo -n true; echo "sudo exit=$?"      # expected: non-zero (no sudo)
   ```
   Record boot_id, uptime and time of day.

**Pass**: on NODE_A only, Ready, LiveMigratable, exact priority/class.

## 4. Test 02 - spread (required)

1. Console: Edit labels on NODE_A, NODE_B, NODE_C: `scheduling-lab.example.com/spread-pool=true`.
   CLI: `oc label node $NODE_A $NODE_B $NODE_C scheduling-lab.example.com/spread-pool=true`
2. Console: start spread-01, -02, -03. CLI:
   ```sh
   for vm in spread-01 spread-02 spread-03; do
     oc patch vm "$vm" -n $NS --type merge -p '{"spec":{"runStrategy":"Always"}}'
   done
   ```
3. Verify - Console: VM list (**Node** column) shows three different pool nodes.
   CLI:
   ```sh
   oc get vmi -n $NS -l cohort=spread -o custom-columns=NAME:.metadata.name,NODE:.status.nodeName,PHASE:.status.phase
   oc get pod -n $NS -l cohort=spread -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority,CLASS:.spec.priorityClassName
   ```
   Expected: three distinct nodes from NODE_A/B/C; launcher priority `0`, no class.
4. Halt the spread VMs afterwards (console **Stop**, or patch `runStrategy: Halted`) to keep step 7 easy to read.

**Pass**: three VMs on three different pool nodes, none outside the pool.

## 5. Test 03 - impossible rule (required)

1. Start negative-01 (console **Start**, or CLI patch `runStrategy: Always`).
2. Verify - Console: VM not Running; **Events** tab shows `FailedScheduling`.
   CLI:
   ```sh
   oc get pods -n $NS -l vm.kubevirt.io/name=negative-01
   oc get events -n $NS --field-selector reason=FailedScheduling
   ```
   Expected: launcher pod `Pending`; `0/N nodes are available: ... didn't match Pod's node affinity/selector`.
3. Halt it (console **Stop**, or patch `runStrategy: Halted`).

**Pass**: Pending + FailedScheduling, never Running.

## 6. Test 04 - manual live migration (optional diagnostic)

Not descheduler evidence. Skip it if the descheduler should be the first migration on the recording.

1. Console: Edit labels on NODE_B: add `eligible=true`. CLI: `oc label node $NODE_B scheduling-lab.example.com/eligible=true`
2. Console: `placement-01` > **Actions > Migrate > Compute** (older: **Migrate**). CLI: `oc create -f actions/04-manual-migration.yaml`
3. Verify - Console: **Migrating**, then Node = NODE_B. CLI: `oc get vmim -n $NS` (`Succeeded`), `oc get vmi placement-01 -n $NS -o wide`.

## 7. Test 05 - descheduler-driven live migration (required)

The VM's node stops being eligible; the running VM is not moved by the label
change itself. `AffinityAndTaints` (`RemovePodsViolatingNodeAffinity`) finds
the violation and evicts the launcher pod; OpenShift Virtualization answers
the eviction with 429 and live-migrates instead; the scheduler picks an
eligible node.

### 7.1 Ownership and writer pause

```sh
oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{.metadata.uid}{"\n"}{.metadata.annotations}{"\n"}{.metadata.labels}{"\n"}'
oc get kubedescheduler cluster -n $DS_NS --show-managed-fields \
  -o jsonpath='{range .metadata.managedFields[*]}{.manager}{" "}{.operation}{" "}{.time}{"\n"}{end}'
```

If GitOps, ACM or another team can write it, agree a pause and window with
the owner. Do not proceed while another writer is active; never `oc apply` /
`oc replace` the whole object, never delete or re-create an existing one. An
existing object that is Degraded only because a profile needs PSI does not
block this test (the lab profiles do not need PSI).

### 7.2 Snapshot - or create if absent

Existing object (normal case):

```sh
oc get kubedescheduler cluster -n $DS_NS -o json > "$LAB_EVIDENCE/kubedescheduler-snapshot.json"
jq '.spec | {mode, deschedulingIntervalSeconds, profiles, profileCustomizations, evictionLimits}' "$LAB_EVIDENCE/kubedescheduler-snapshot.json"
RV0=$(jq -r .metadata.resourceVersion "$LAB_EVIDENCE/kubedescheduler-snapshot.json")
```

Console: KubeDescheduler `cluster` > **YAML** > **Download** (keep it private).

No object (NotFound): create it with the lab values and record its UID; then
skip 7.4's patch (but **not** 7.4's verification):

```sh
oc create -f descheduler/05e-create-if-absent.yaml
oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{.metadata.uid}{"\n"}' | tee "$LAB_EVIDENCE/kubedescheduler-created-uid.txt"
```

### 7.3 Starting state

- placement-01 Running, LiveMigratable: `SOURCE=$(oc get vmi placement-01 -n $NS -o jsonpath='{.status.nodeName}')`
- TARGET: another approved node, Ready with headroom, e.g. `TARGET="$NODE_C"`.
- Only SOURCE and TARGET may carry `eligible`; remove it from the third
  approved node. A non-approved node with the label is a stop.
- Spread VMs halted; negative-01 halted. No migration in progress (`oc get vmim -n $NS`).
- Record before-values (7.8): VM UID, VMI UID, node, boot_id, uptime.

### 7.4 Lab configuration in Predictive + verification

Patch (skip if you created the object in 7.2):

```sh
jq --arg rv "$RV0" '.[0].value = $rv' descheduler/05a-lab-predictive.patch.json > "$LAB_EVIDENCE/05a.json"
oc patch kubedescheduler cluster -n $DS_NS --type=json --patch-file="$LAB_EVIDENCE/05a.json"
```

Console alternative: in the `cluster` YAML editor set only these five fields,
leaving everything else, and **Save** (the console refuses if the object
changed since opened):

```yaml
spec:
  mode: Predictive
  deschedulingIntervalSeconds: 30
  profiles: [AffinityAndTaints, LongLifecycle, EvictPodsWithLocalStorage, EvictPodsWithPVC]
  profileCustomizations:
    devEnableEvictionsInBackground: true
    thresholdPriority: -999999999
    namespaces:
      included: [virt-scheduling-lab]
  evictionLimits: {node: 1, total: 1}
```

Verify what the operator generated (always, also after 05e):

```sh
oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
oc rollout status deploy/descheduler -n $DS_NS --timeout=180s
oc get deploy descheduler -n $DS_NS -o jsonpath='{.spec.template.spec.containers[0].args}{"\n"}' | tee "$LAB_EVIDENCE/args-predictive.txt"
oc get configmap cluster -n $DS_NS -o jsonpath='{.data.policy\.yaml}' > "$LAB_EVIDENCE/policy-predictive.yaml"
grep -c 'name: DefaultEvictor' "$LAB_EVIDENCE/policy-predictive.yaml"
grep -n -A2 'priorityThreshold' "$LAB_EVIDENCE/policy-predictive.yaml"
grep -n -E 'RemovePodsViolatingNodeAffinity|LowNodeUtilization|virt-scheduling-lab|maxNoOfPodsToEvict' "$LAB_EVIDENCE/policy-predictive.yaml"
```

HCO health (console: **Observe > Metrics**, query
`kubevirt_hco_misconfigured_descheduler`; **Observe > Alerting**, search
`HCOMisconfiguredDescheduler`):

```sh
# Read-only Prometheus queries using the existing monitoring pod.
# Requires permission to exec into this namespace; no token is printed or passed to curl.
oc exec -n openshift-monitoring prometheus-k8s-0 -c prometheus -- \
  promtool query instant http://localhost:9090 kubevirt_hco_misconfigured_descheduler
oc exec -n openshift-monitoring prometheus-k8s-0 -c prometheus -- \
  promtool query instant http://localhost:9090 'ALERTS{alertname="HCOMisconfiguredDescheduler"}'
```

If monitoring access is restricted, have the monitoring owner run the queries
or use the console Metrics page. Do not change monitoring RBAC for this test.

Expected - stop if any item fails:

- no condition `Degraded=True`, and no PSI error (`can only be used when PSI
  metrics are enabled`); `status.readyReplicas` on the CR can be stale - trust
  the Deployment rollout;
- args contain `--dry-run=true`, `--descheduling-interval=30s` and the
  `EvictionsInBackground=true` feature gate;
- **every** DefaultEvictor block has `priorityThreshold` with value
  `-999999999` (the `priorityThreshold` count equals the DefaultEvictor
  count);
- `RemovePodsViolatingNodeAffinity` is present and limited to
  `virt-scheduling-lab`; `LowNodeUtilization` is present (its namespace scope
  is the protected-namespace exclusion, as expected - priority is the guard);
  eviction limits 1 per node and 1 total;
- metric value `0` (it can take a minute to update); `ALERTS` result empty.

### 7.5 Trigger and dry run

1. Label TARGET first, then remove the label from SOURCE.
   Console: Edit labels on TARGET (add), then SOURCE (remove). CLI:
   ```sh
   oc label node "$TARGET" scheduling-lab.example.com/eligible=true
   oc label node "$SOURCE" scheduling-lab.example.com/eligible-
   ```
2. Watch at least two intervals:
   ```sh
   oc logs deploy/descheduler -n $DS_NS --since=5m | tee "$LAB_EVIDENCE/predictive-log.txt" \
     | grep -i -E 'evict|RemovePodsViolatingNodeAffinity|LowNodeUtilization'
   oc get vmi placement-01 -n $NS -o wide
   oc get vmim -n $NS
   ```
   Console: **Workloads > Pods** > `descheduler-...` > **Logs**; VM Overview Node unchanged.

Expected: a dry-run eviction candidate for `virt-launcher-placement-01-...`
attributed to `RemovePodsViolatingNodeAffinity`; VMI still on SOURCE; no new
migration. **Stop** if any other pod appears as a candidate. A candidate from
`LowNodeUtilization` alone does not count. No candidate after 5 minutes: 7.7.

### 7.6 Automatic (explicit step)

Immediately before: repeat **1.6** (pod priority inventory) and re-check the
lab pods; both must still be clean:

```sh
oc get pods -n $NS -o json | jq -r '.items[]
  | "\(.metadata.name) priority=\(.spec.priority) class=\(.spec.priorityClassName // "-") evict-annotation=\((.metadata.annotations // {}) | has("descheduler.alpha.kubernetes.io/evict"))"'
```

Expected: only placement-01's launcher has `priority=-1000000000
class=virt-scheduling-lab-evictable`; no lab pod has the evict annotation.

```sh
RV1=$(oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{.metadata.resourceVersion}')
jq --arg rv "$RV1" '.[0].value = $rv' descheduler/05b-lab-automatic.patch.json > "$LAB_EVIDENCE/05b.json"
oc patch kubedescheduler cluster -n $DS_NS --type=json --patch-file="$LAB_EVIDENCE/05b.json"
date -u +%FT%TZ | tee "$LAB_EVIDENCE/automatic-start.txt"
oc rollout status deploy/descheduler -n $DS_NS --timeout=180s
oc get deploy descheduler -n $DS_NS -o jsonpath='{.spec.template.spec.containers[0].args}{"\n"}'
```

05b applies only if the resourceVersion is the one just read and all five
fields are exactly the lab values (full `profileCustomizations` including the
background flag and threshold). If it fails, stop and review with the owner;
do not edit guards or guess server defaults. Console alternative: compare the
five fields with the 7.4 block first, then change only `mode` to `Automatic`.

Expected: args no longer contain `--dry-run=true`. Watch (5-minute limit),
two terminals since `oc get -w` watches one type:

```sh
oc get vmi placement-01 -n $NS -o wide -w
oc get vmim -n $NS -w
oc logs deploy/descheduler -n $DS_NS --since=10m | tee "$LAB_EVIDENCE/automatic-log.txt" \
  | grep -i -E 'placement-01|evict|evacuation'
```

Expected: the log names the current `virt-launcher-placement-01-...` pod
under `RemovePodsViolatingNodeAffinity`, followed by a cluster-created
migration. With background evictions enabled, the log can report
`evictionRequests=1` and `evictedPods=0`: the VM migration is handled in
the background. Do not require an error/HTTP 429 log line. If a version does
log `Eviction triggered evacuation of VMI ...`, that response is expected.
A transient `EvictionRequested=True` might be too brief to observe.
The cluster-created migration (normally `kubevirt-evacuation-...`) reaches
`Succeeded`; VMI node = TARGET. Console: VM **Migrating** then Node = TARGET;
**Virtualization > Overview > Migrations** (or **Home > Search** >
`VirtualMachineInstanceMigration`) shows Succeeded.

Then **immediately** back to Predictive:

```sh
oc patch kubedescheduler cluster -n $DS_NS --type=json --patch-file=descheduler/05c-back-to-predictive.patch.json
oc rollout status deploy/descheduler -n $DS_NS --timeout=180s
oc get deploy descheduler -n $DS_NS -o jsonpath='{.spec.template.spec.containers[0].args}{"\n"}'   # --dry-run=true again
```

### 7.7 Timeout or anything unexpected

No migration within 5 minutes, a failed migration, a non-lab candidate, or a
move attributed only to `LowNodeUtilization`:

1. Apply 05c at once.
2. Diagnose without forcing: generated policy (7.4); launcher pod has the
   required nodeAffinity; TARGET labelled, Ready, untainted, headroom; VMI
   `LiveMigratable=True`; descheduler logs.
3. No node drain, no pod delete, no manual migration presented as a
   descheduler result. Record **blocked** or **failed** with evidence.

### 7.8 Guest continuity

Before (7.3) and after:

```sh
oc get vm placement-01 -n $NS -o jsonpath='{.metadata.uid}{"\n"}'
oc get vmi placement-01 -n $NS -o jsonpath='{.metadata.uid}{" "}{.status.nodeName}{"\n"}'
oc get vmi placement-01 -n $NS -o jsonpath='{.status.migrationState.sourceNode}{" -> "}{.status.migrationState.targetNode}{" completed="}{.status.migrationState.completed}{" failed="}{.status.migrationState.failed}{"\n"}'
oc get vmi placement-01 -n $NS -o jsonpath='{range .status.conditions[*]}{.type}={.status}{" "}{end}{"\n"}'
```

Guest (serial console; it reconnects after the move): `cat /proc/sys/kernel/random/boot_id`, `cut -d' ' -f1 /proc/uptime`.

**Pass** only if all hold: no migration created by you for this attempt; the
log attributes the eviction to `RemovePodsViolatingNodeAffinity`; migration
`Succeeded` SOURCE -> TARGET; VM UID and VMI UID unchanged; boot_id unchanged
and uptime increased by about the elapsed time; `Ready`, `LiveMigratable`,
`AgentConnected` all `True` afterwards.

### 7.9 Restore

Existing object - after 05c:

```sh
CUR_RV=$(oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{.metadata.resourceVersion}')
jq --arg rv "$CUR_RV" -f descheduler/05d-restore-touched-fields.jq \
  "$LAB_EVIDENCE/kubedescheduler-snapshot.json" > "$LAB_EVIDENCE/restore.patch.json"
cat "$LAB_EVIDENCE/restore.patch.json"       # review
oc patch kubedescheduler cluster -n $DS_NS --type=json --patch-file="$LAB_EVIDENCE/restore.patch.json"
F='.spec | {mode, deschedulingIntervalSeconds, profiles, profileCustomizations, evictionLimits}'
diff <(jq -S "$F" "$LAB_EVIDENCE/kubedescheduler-snapshot.json") \
     <(oc get kubedescheduler cluster -n $DS_NS -o json | jq -S "$F")      # expect no output
```

The restore patch first tests the resourceVersion **and** that all five fields
still hold exactly the lab Predictive values; any concurrent change makes it
fail with nothing written. Then only those five fields return to the
snapshot; metadata, status and other fields are untouched. On failure stop
and review with the owner.

Console alternative (no full-YAML paste): open the YAML; first compare the
five fields with the expected lab values (7.4 block, `mode: Predictive`) and
stop on any difference; then set only those five fields to their snapshot
values (delete a field the snapshot lacks); Save; run the `diff` above.

Created object (05e) - delete only if the UID matches:

```sh
test "$(oc get kubedescheduler cluster -n $DS_NS -o jsonpath='{.metadata.uid}')" = \
     "$(cat "$LAB_EVIDENCE/kubedescheduler-created-uid.txt")" \
  && oc delete kubedescheduler cluster -n $DS_NS || echo "UID MISMATCH - not deleting"
```

After restore: hand the object back to its owner and confirm their tool is in
sync. A configuration that was Degraded for PSI before returns to that state,
and the descheduler Deployment may be scaled to 0; HCO's metric/alert return
to whatever the original configuration produces. Operator-created
ServiceAccounts, RBAC, ConfigMaps and Services may remain: leave them; never
delete cluster RBAC or other operator-owned objects.

## 8. Evidence (read-only, private)

```sh
oc get nodes $(cat "$LAB_EVIDENCE/approved-nodes.txt") -L scheduling-lab.example.com/eligible,scheduling-lab.example.com/spread-pool > "$LAB_EVIDENCE/nodes.txt"
oc get vm,vmi,vmim,dv,pvc,pods -n $NS -o wide > "$LAB_EVIDENCE/lab-objects.txt"
oc get vmi -n $NS -o yaml > "$LAB_EVIDENCE/vmi.yaml"
oc get vmim -n $NS -o yaml > "$LAB_EVIDENCE/vmim.yaml"
oc get events -n $NS --sort-by=.lastTimestamp > "$LAB_EVIDENCE/events.txt"
oc get kubedescheduler cluster -n $DS_NS -o yaml > "$LAB_EVIDENCE/kubedescheduler-now.yaml"
```

Contains cluster names and UIDs: keep out of the public repository.

## 9. Reset between recording takes

Root disks are kept between takes (guest changes persist; boot_id changes on each start).

1. Descheduler in Predictive (7.6 last block) or restored (7.9).
2. Migrations: `oc get vmim -n $NS -o custom-columns=NAME:.metadata.name,VMI:.spec.vmiName,PHASE:.status.phase`.
   Any phase other than `Succeeded`/`Failed`: **stop and wait**; never delete an in-flight migration.
3. Halt the five named VMs and wait for their VMIs to go:
   ```sh
   for vm in $LAB_VMS; do
     oc get vm "$vm" -n $NS >/dev/null && oc patch vm "$vm" -n $NS --type merge -p '{"spec":{"runStrategy":"Halted"}}'
   done
   for vm in $LAB_VMS; do oc wait vmi/"$vm" -n $NS --for=delete --timeout=300s; done
   ```
   Console: stop each VM; list shows **Stopped**.
4. Delete only finished migrations of the lab VMs:
   ```sh
   oc get vmim -n $NS -o json | jq -r '.items[]
     | select(.status.phase == "Succeeded" or .status.phase == "Failed")
     | select(.spec.vmiName as $v | ["placement-01","spread-01","spread-02","spread-03","negative-01"] | index($v))
     | .metadata.name' | while read -r m; do oc delete vmim "$m" -n $NS; done
   ```
5. Labels - only the recorded approved nodes:
   ```sh
   for n in $(cat "$LAB_EVIDENCE/approved-nodes.txt"); do
     oc label node "$n" scheduling-lab.example.com/eligible- scheduling-lab.example.com/spread-pool-
   done
   oc get nodes -l scheduling-lab.example.com/eligible; oc get nodes -l scheduling-lab.example.com/spread-pool
   ```
   A "not found" message for a label a node never had is harmless. If the
   cluster-wide checks still list a node, it is not yours: leave it and find out who set it.
6. Optional fresh disks: delete a halted VM (its DataVolume and PVC go with it,
   section 10 step 3) and re-create it from the edited YAML in `$LAB_EVIDENCE`; wait
   for the clone again (2.4).
7. Start again at step 3.

## 10. Cleanup

1. Descheduler restored (7.9) and handed back, or the created one deleted with the UID guard.
2. Reset 9.2-9.4 (no in-flight migrations; VMs halted).
   Before deleting any disk, record its PV and reclaim policy:
   ```sh
   oc get pvc -n $NS -o custom-columns=CLAIM:.metadata.name,UID:.metadata.uid,PV:.spec.volumeName \
     | tee "$LAB_EVIDENCE/lab-claims-before-delete.txt"
   for pv in $(oc get pvc -n $NS -o jsonpath='{range .items[*]}{.spec.volumeName}{"\n"}{end}'); do
     oc get pv "$pv" -o jsonpath='{.metadata.name}{" claim="}{.spec.claimRef.namespace}{"/"}{.spec.claimRef.name}{" claimUID="}{.spec.claimRef.uid}{" reclaim="}{.spec.persistentVolumeReclaimPolicy}{"\n"}'
   done | tee "$LAB_EVIDENCE/lab-pv-policies-before-delete.txt"
   ```
   Console: open each lab PVC's volume link and inspect the PV's reclaim policy.
3. Delete the VMs; their DataVolumes and PVCs (test data) are owned by the VMs and must disappear:
   ```sh
   for vm in $LAB_VMS; do oc delete vm "$vm" -n $NS --ignore-not-found; done
   oc get dv,pvc -n $NS        # wait until empty
   ```
   Console: **Virtualization > VirtualMachines** > each VM > **Actions >
   Delete** (keep "delete disks" selected); **Storage > PersistentVolumeClaims** is empty.
   If any `*-rootdisk` PVC remains, check its ownerReferences, then delete it by name.
   PVC API deletion does not by itself prove backend data erasure. Storage
   cleanup follows the PV reclaim policy and CSI provider. With `Delete`,
   verify each recorded lab PV and provider volume are removed as expected.
   With `Retain`, use the recorded namespace/claim UID to identify the exact
   residual lab PVs and hand them to the storage owner for approved cleanup.
   Do not delete unrelated Released PVs or remove storage finalizers.
4. Namespace - only if the UID matches and the inventory (1.5 loop) is complete and lab-only:
   ```sh
   test "$(oc get namespace $NS -o jsonpath='{.metadata.uid}')" = "$(cat "$LAB_EVIDENCE/namespace-uid.txt")" \
     && oc delete namespace $NS || echo "UID MISMATCH - not deleting"
   ```
   Run the 1.5 inventory loop first and continue only if it prints
   `inventory complete` and lists nothing but lab and automatic objects.
5. PriorityClass - only if the UID matches and no pod uses it:
   ```sh
   oc get pods -A -o json | jq -r --arg pc "$PC" '.items[] | select(.spec.priorityClassName == $pc) | "\(.metadata.namespace)/\(.metadata.name)"'   # expect empty
   test "$(oc get priorityclass $PC -o jsonpath='{.metadata.uid}')" = "$(cut -d' ' -f1 "$LAB_EVIDENCE/priorityclass-uid.txt")" \
     && oc delete priorityclass $PC || echo "UID MISMATCH - not deleting"
   ```
6. Node labels from the recorded approved nodes (9.5).
7. Console: project gone from **Home > Projects**; no `virt-scheduling-lab-evictable`
   in **Home > Search** > PriorityClass; approved nodes show no lab labels.

## 11. Client tailoring checklist

- [ ] Approved nodes, RWX StorageClass and capacity agreed with their owners.
- [ ] `rhel9` DataSource Ready (or the client's approved RHEL 9 source substituted in all four VM files).
- [ ] Label domain `scheduling-lab.example.com`, namespace and PriorityClass names acceptable (namespace also in the descheduler patches).
- [ ] Descheduler owner identified, pause window agreed, snapshot taken.
- [ ] Pod priority inventory clean; owner agrees not to use the reserved class or force-evict annotation during the window.
- [ ] Console RBAC for the lab namespace limited to the demo team.
- [ ] Preflight passed on the client version itself.

## 12. Troubleshooting

| Symptom | Likely cause |
|---|---|
| DataVolume stuck `CloneScheduled`/`Pending` | StorageClass name, capacity, clone permission, or WaitForFirstConsumer (start the VM) |
| `LiveMigratable=False` | PVC not RWX, or another non-migratable device |
| launcher pod rejected: priority class not found | 2.2 skipped |
| HCO metric `1` / alert firing | profiles/customizations not exactly the lab set; AffinityAndTaints with background evictions alone is not accepted |
| Descheduler never names placement-01 | include not applied, operand not rolled out, VM without required nodeAffinity, local-storage/PVC profiles missing, or priority not below threshold |
| `readyReplicas: 0` on the CR | can be stale; check conditions and the Deployment |
| Serial console asks for login | cloud-init still running on first boot |
