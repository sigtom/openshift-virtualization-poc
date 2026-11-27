# Dell PowerFlex observability (DEFERRED, NOT TESTED)

> **Do not run this** until **all** other non-destructive tests are complete **and** the administrator approves
> in writing. It needs an actual PowerFlex environment with Dell Container Storage Modules (CSM) **already
> installed**; this case never installs it. Without it, the Dell layer is **Not available / Not run**, which is
> not a failure of the native case. Never claim PowerFlex validated from another backend. Keep real names,
> versions and output outside the repository. Every step below is untested.

Do the steps in order: checks → inspect → prerequisites → enable → verify → roll back. Replace `CSM_NS`, `NAME`.

## 1. Before you start (all must be yes)

- [ ] A PowerFlex backend exists and the volume under test maps exactly to a PowerFlex volume ([mapping](ADMIN-GUIDE.md#mapping)).
- [ ] CSM is **operator-managed**. If the driver is Helm-managed or CSM is absent: **stop**. Do not deploy a second CSI
      driver or adopt the existing one. Native VM metrics and a **read-only** array view can still proceed; any install or
      migration is a separate approved infrastructure change (Dell's operator procedure is in [REFERENCES](REFERENCES.md)).
- [ ] Installed Operator, CSM and PowerFlex versions appear in Dell's current support matrix for the installed OpenShift
      version. The matrix is evidence, not approval to upgrade; do not upgrade for this case.
- [ ] `oc get ns CSM_NS --show-labels` does **not** show `openshift.io/cluster-monitoring=true` (user workload monitoring
      does not scrape such a namespace).

## 2. Inspect (read-only) and save a private backup

~~~sh
umask 077
mkdir -p "$HOME/poc-private/storage-iops"
chmod 700 "$HOME/poc-private" "$HOME/poc-private/storage-iops"
oc get csv -A | grep -i -e dell -e cert-manager
oc get csm -A
oc get csm NAME -n CSM_NS -o yaml > "$HOME/poc-private/storage-iops/csm-before.yaml"
oc get pods,svc -n CSM_NS
~~~

The saved copy may name secrets; it stays in that private folder. Record the driver, its `configVersion`, secret
references and every existing module. These stay **unchanged**. The installed CRD's schema governs: the module
list is `spec.modules` (plural) in the current Operator CRD ([tagged CRD](REFERENCES.md)); older vendor prose that
writes `spec.module` is stale. Check yours with `oc explain csm.spec.modules`.

## 3. Prerequisites

**cert-manager** must already be deployed (reuse it; install no second): `oc get crd certificates.cert-manager.io`.
Verify its operator and deployments are Ready in **Operators → Installed Operators** and **Workloads → Deployments**
in its installed project. A CRD alone does not prove it is running. If missing or unhealthy, stop; that is a separate change.

Also check `oc get ns CSM_NS --show-labels` for `openshift.io/user-monitoring=false`. If present,
the owner must approve enabling monitoring: in **Administration → Namespaces → CSM_NS → Labels**,
record its original value in the private notes, then remove only that opt-out label. Do not add a platform monitoring label.

**User workload monitoring** (console, administrator):

1. **Workloads → ConfigMaps**, project `openshift-monitoring`, open `cluster-monitoring-config`, **YAML** tab.
2. Under `data`, the `config.yaml` value is one block of YAML. Add the line `enableUserWorkload: true` at its top level and
   **keep every other line unchanged**. **Save**. If the line already exists as `true`, change nothing. If it exists as
   `false`, stop and ask the owner.
3. If the ConfigMap does not exist, create **only** this ConfigMap (**+ → Import YAML**):

~~~yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-monitoring-config
  namespace: openshift-monitoring
data:
  config.yaml: |
    enableUserWorkload: true
~~~

4. Verify: `oc -n openshift-user-workload-monitoring get pods` shows the prometheus-operator, prometheus-user-workload
   and thanos-ruler-user-workload pods Running. Confirm the steps against the monitoring documentation for the
   installed version ([REFERENCES](REFERENCES.md)).

## 4. Enable observability (touch only these fields)

Console: **Operators → Installed Operators → Dell Container Storage Modules → Container Storage Module →** the existing
PowerFlex resource **→ YAML**. Edit only the observability entry in `spec.modules` and its `components`, matching the
installed schema and release; add or change nothing else. Shape only; **never paste or replace the whole resource** and
never copy `driverType` or `configVersion` from any example (the generic current observability page shows a different
array family):

~~~yaml
spec:
  modules:
    - name: observability
      enabled: true
      components:
        - name: otel-collector
          enabled: true
        - name: metrics-powerflex
          enabled: true
~~~

Write the previous values of every field you touch in the private folder. Enable nothing extra (gateway monitoring, SDC
monitoring and similar are not needed for IOPS). Use the console edit; no CLI patch is provided because an index-based
patch can hit the wrong list entry.

## 5. Verify the data is scraped

~~~sh
oc get pods,svc -n CSM_NS
oc get servicemonitor -n CSM_NS
oc get svc -n CSM_NS --show-labels
oc get svc SVC -n CSM_NS -o jsonpath='{range .spec.ports[*]}{.name}{"\t"}{.port}{"\n"}{end}'
~~~

The new pods should be Ready and the service should list a port named `exporter-https` (metrics over HTTPS). If a
monitor already exists for it, use it **read-only**: do not edit, label or delete it, now or at rollback. Otherwise
add two new objects as follows. Both are created new for this case and are never changed if they already exist.

Choose two unused names, for example `CA_CM=poc-powerflex-ca-05` and `MON=poc-powerflex-observability-05`, and check:

~~~sh
CA_CM='poc-powerflex-ca-05'; MON='poc-powerflex-observability-05'
oc -n CSM_NS get configmap "$CA_CM"          # expected: NotFound
oc -n CSM_NS get servicemonitor "$MON"       # expected: NotFound
~~~

If either exists, it belongs to someone else: choose another name.

1. Create a ConfigMap from the **CA file the owner supplies** (a public certificate; no private key, never in the
   repo). The label is added only after the create succeeds, so an existing object is never labelled:

   ~~~sh
   if oc -n CSM_NS create configmap "$CA_CM" --from-file=ca.crt=/path/to/owner-supplied-ca.pem; then
     oc -n CSM_NS label configmap "$CA_CM" perf-lab.example.com/case=05
     oc -n CSM_NS get configmap "$CA_CM" -o jsonpath='{.metadata.uid}{"\n"}' > "$HOME/poc-private/storage-iops/ca-configmap.uid"
   else
     echo "STOP: not created. Choose another name; leave the existing object alone."
   fi
   ~~~

2. Find a name the certificate is valid for (**serverName must be one of its Subject Alternative Names**) from the
   serving certificate the owner supplies:

   ~~~sh
   openssl x509 -in /path/to/owner-supplied-server-cert.pem -noout -ext subjectAltName
   ~~~

3. Copy `optional/powerflex-servicemonitor.template.yaml` into the private folder as `servicemonitor.yaml` and
   replace every `REPLACE_*`: the monitor name (`$MON`), the namespace, one label of the Service (from
   `--show-labels`), the SAN name, the ConfigMap name (`$CA_CM`) and `ca.crt`.
   Check `grep -n '^[^#]*REPLACE_' "$HOME/poc-private/storage-iops/servicemonitor.yaml"` prints nothing.
4. Validate, then create it (`create` refuses an existing monitor) and save its UID:

   ~~~sh
   oc create --dry-run=server -f "$HOME/poc-private/storage-iops/servicemonitor.yaml"
   oc create -f "$HOME/poc-private/storage-iops/servicemonitor.yaml" &&
   oc -n CSM_NS get servicemonitor "$MON" -o jsonpath='{.metadata.uid}{"\n"}' > "$HOME/poc-private/storage-iops/servicemonitor.uid"
   ~~~

Do not use `insecureSkipVerify`, even if a vendor legacy example does. In **Observe → Targets** (source: user), the
target for `CSM_NS` must be **Up**; if it is not, read the error, fix the CA or SAN, and do not weaken TLS.

## 6. Read and interpret the metrics

In **Observe → Metrics**, discover what exists:

~~~promql
count by (__name__) ({__name__=~"powerflex_.*"})
~~~

Record the actual current names, types and labels; the legacy names below are only an expectation.

| Metric (verify) | Unit | Calculation |
| --- | --- | --- |
| `powerflex_volume_read_iops_per_second`, `…_write_iops_per_second` | ops/s, **already a rate** | **No `rate()`**. Total = read + write |
| `powerflex_volume_read_bw_megabytes_per_second`, `…_write_…` | **MB/s**, not MiB/s | Convert before comparing with KiB/s |
| `powerflex_volume_read_latency_milliseconds`, `…_write_…` | ms | Per volume; do not weight with other volumes |

Node-level equivalents (`powerflex_export_node_*`, verify) exist. Filter by the unique PowerFlex system and volume ID,
or by a confirmed PVC/PV label. **De-duplication:** inspect the unique target, system and volume labels first
(`count by (instance, pod, system_id, volume_id) (powerflex_volume_read_iops_per_second)`, with labels as found).
If the same volume appears from more than one scrape target, choose **one** verified target. Do not blanket `max` or
`sum`: per-node series are legitimate separate contributions, and only genuine duplicates are dropped.

Gateway or module-health metrics are not volume performance; driver `csi_operations_seconds` measures provisioning
API calls, **not** guest IOPS.

**Dashboards.** Dell's current import page names *PowerFlex: I/O Performance by Provisioned Volume*, *…by Kubernetes
Node* and *CSI Driver Provisioned Volume Topology*; import them per the official page into a Grafana the owner already
runs. Nothing is installed automatically.

**Array side (read-only).** Use the volume performance view of the array manager as described in the manual for the
installed PowerFlex version; find the exact menu there rather than from this guide, and make no array changes.

## 7. Roll back (only what you touched)

1. Delete only the monitor and CA ConfigMap this case created, each only if its UID still matches the one you saved.
   A shared monitor you reused stays untouched.

   ~~~sh
   P="$HOME/poc-private/storage-iops"
   [ "$(oc -n CSM_NS get servicemonitor "$MON" -o jsonpath='{.metadata.uid}')" = "$(cat "$P/servicemonitor.uid")" ] && oc -n CSM_NS delete servicemonitor "$MON" || echo "Not deleting the monitor: UID differs or no record"
   [ "$(oc -n CSM_NS get configmap "$CA_CM" -o jsonpath='{.metadata.uid}')" = "$(cat "$P/ca-configmap.uid")" ] && oc -n CSM_NS delete configmap "$CA_CM" || echo "Not deleting the ConfigMap: UID differs or no record"
   ~~~
2. In the console, set only the fields you changed back to the saved values. Remove `enableUserWorkload` only if you
   added it (or delete the ConfigMap only if you created it, with the owner's approval). Keep every other line.
3. If this case removed `openshift.io/user-monitoring=false`, restore exactly that label and value
   through the same Namespace **Labels** editor. Leave every other label unchanged.
4. Verify the CSM resource, its pods and native VM I/O are healthy as before.

**Never** delete the CSM resource, operator, driver, cert-manager or shared monitoring configuration.
