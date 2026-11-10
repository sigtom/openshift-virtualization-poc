# Optional: load-aware rebalancing - not run, not part of pass/fail

Red Hat's preferred descheduler profile for virtualization is
`KubeVirtRelieveAndMigrate` (first choice in the HCOMisconfiguredDescheduler
runbook; the current documentation pairs it with load-aware settings such as
`devActualUtilizationProfile` and `devDeviationThresholds`). It requires **PSI
metrics enabled on the nodes**; the operator reports a Degraded condition
("can only be used when PSI metrics are enabled") otherwise.

Enabling PSI is a kernel argument delivered by a MachineConfig, which reboots
nodes in a rolling fashion. That is a platform change with its own owner,
approval and maintenance window; this test case provides no MachineConfig.
On clusters where control-plane and worker roles share nodes, the documented
worker-pool example does not apply as written.

This test case therefore uses the documented fallback (`LongLifecycle` with
`devEnableEvictionsInBackground: true`) and tests rule-driven migration
(`RemovePodsViolatingNodeAffinity`). A move caused by LongLifecycle's
`LowNodeUtilization` is not counted as a result.

If a client wants a load-aware evaluation later, plan it separately: PSI
already enabled by the platform owner; a measured per-node baseline of the
metric the profile uses; a bounded, time-limited guest load on small VMs; a
non-namespace eviction guard (`thresholdPriority` plus a reserved class, as
here) proven in Predictive; eviction limits 1/1; a stop condition; and the
same guarded snapshot/restore as RUNBOOK 7.2 and 7.9. If small VMs cannot
move the metric past the threshold, the result is inconclusive - do not load
whole hosts.
