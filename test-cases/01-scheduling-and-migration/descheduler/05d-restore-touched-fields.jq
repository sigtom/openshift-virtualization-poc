# Builds a JSON Patch that restores ONLY the five KubeDescheduler spec fields the
# lab touched, from the snapshot taken before the lab. Everything else
# (metadata, ownership/tracking annotations, other spec fields, status) is left alone.
#
# Run it only after 05c (mode back to Predictive).
#
# Usage:
#   CUR_RV=$(oc get kubedescheduler cluster -n openshift-kube-descheduler-operator \
#              -o jsonpath='{.metadata.resourceVersion}')
#   jq --arg rv "$CUR_RV" -f descheduler/05d-restore-touched-fields.jq \
#      "$LAB_EVIDENCE/kubedescheduler-snapshot.json" > "$LAB_EVIDENCE/restore.patch.json"
#
# Guards (the API server applies the patch all-or-nothing):
#   1. resourceVersion must still equal CUR_RV (nobody wrote since you read it);
#   2. each of the five fields must still hold EXACTLY the lab Predictive value
#      (mode Predictive, interval 30, the four lab profiles in order,
#      profileCustomizations that is exactly
#      {devEnableEvictionsInBackground: true, thresholdPriority: -999999999,
#       namespaces: {included: [virt-scheduling-lab]}}, limits 1/1).
# If any guard fails, nothing is changed. Do not edit the guards to make it pass:
# someone else changed the object (or the server added defaults) - stop and
# review with the object's owner.
#
# After the guards, fields present in the snapshot are put back with their
# snapshot value and fields absent from the snapshot are removed.
.spec as $snap
| [ {op: "test", path: "/metadata/resourceVersion", value: $rv},
    {op: "test", path: "/spec/mode", value: "Predictive"},
    {op: "test", path: "/spec/deschedulingIntervalSeconds", value: 30},
    {op: "test", path: "/spec/profiles",
     value: ["AffinityAndTaints", "LongLifecycle", "EvictPodsWithLocalStorage", "EvictPodsWithPVC"]},
    {op: "test", path: "/spec/profileCustomizations",
     value: {devEnableEvictionsInBackground: true, thresholdPriority: -999999999,
             namespaces: {included: ["virt-scheduling-lab"]}}},
    {op: "test", path: "/spec/evictionLimits", value: {node: 1, total: 1}} ]
  + ( ["mode", "deschedulingIntervalSeconds", "profiles", "profileCustomizations", "evictionLimits"]
      | map( . as $f
             | if ($snap | has($f))
               then {op: "add", path: ("/spec/" + $f), value: $snap[$f]}
               else {op: "remove", path: ("/spec/" + $f)}
               end ) )
