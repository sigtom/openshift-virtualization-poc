# Sources and applicability

> Procedures checked against the official 4.21 and 4.22 documentation listed below.
> Use the client’s installed version and complete its results sheet; documentation
> review does not establish an executed performance result.

## Source matrix

| Topic | OpenShift 4.21 (client) | OpenShift 4.22 | Applies as |
| --- | --- | --- | --- |
| Memory density, swap provisioning, `wasp-agent`, HyperConverged (OpenShift **Virtualization** section *Configuring higher VM workload density*, 5.7 / 5.7.1) | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/postinstallation-configuration) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/postinstallation-configuration) | Memory phase of case 03 |
| Networking: masquerade, port lists, Services, secondary networks | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/networking) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/networking) | Case 04 path and Service notes |
| Monitoring and VM metrics | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/monitoring) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/monitoring) | Dashboards, metric names |
| Managing VMs: consoles, guest agent, snapshots, migration | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/managing-vms) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/managing-vms) | Console access, guest checks |
| About OpenShift Virtualization | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/about) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/about) | Concepts for first-time readers |
| Creating a VM (templates, boot sources, DataSources) | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/creating-a-virtual-machine) | [4.22 book: Creating virtual machines](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/virtualization/index) | Path B VM shape |
| Advanced VM creation (cloud-init, storage) | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/advanced-vm-creation) | [4.22 book: Creating virtual machines](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/virtualization/index) | cloud-init limits, volumes |

## Memory swap: documented path and open question

- **Documented VM-specific path:** the OpenShift Virtualization section above (5.7 in the 4.21
  and 4.22 books) describes memory density with the `wasp-agent` (DaemonSet in `openshift-cnv`)
  and a swap procedure. Case 03 follows it.
- **Unresolved conflict:** the generic OpenShift Container Platform 4.21 documentation lists
  node swap as removed. This repository has not resolved how that fits the Virtualization
  section and does not state the support or Technology Preview status. Use the installed
  release's Virtualization procedure; ask Red Hat if its applicability is unclear.
- A bounded 4.22 rehearsal observed host and VM paging, then was aborted after exceeding
  a stop limit and losing worker responsiveness. Loaded and recovery benchmarks were not
  completed. The optional root-filesystem swap template was not run verbatim; see
  [verification limits](README.md#walkthrough-verification).

## Key applicability differences

| Area | 4.21 | 4.22 | What to do |
| --- | --- | --- | --- |
| HyperConverged API version | Documented against `hyperconvergeds.v1beta1.hco.kubevirt.io`, field `spec.higherWorkloadDensity.memoryOvercommitPercentage` | Documentation still targets `v1beta1`; the cluster may also serve `v1`, where the setting is under `spec.virtualization.higherWorkloadDensity` | Pin the API version in every `get`, `explain` and `patch` (MEMORY-DENSITY.md Step 0). Prefer the console setting |
| Memory dashboard | Do not assume a dedicated memory-density dashboard exists | May exist; verify | Use VM **Metrics** and node dashboards; verify series |
| Default masquerade networking | Guest sees an internal address; other pods reach the VM at the **pod IP**. Only ports listed on the interface are forwarded when a list exists | Same, verify | Use the pod IP; declare ports; a Service adds a forwarding step and is not comparable |
| Guest agent | Needed for some console data; `Running` does not mean the guest is ready | Same | Check the agent and a console login before measuring |
| Storage mode and cloning | Clone and snapshot behaviour depends on the StorageClass; `WaitForFirstConsumer` delays cloning | Same | Wait for the DataVolume to succeed, then boot-check (admin guide) |
| cloud-init size | `cloudInitNoCloud.userData` is limited to 2048 bytes | Same | Keep it minimal; scripts come from the image or `guest-tools/` |

Sizes, versions and wording must be checked against the installed release.

## Other primary sources

- [sysbench](https://github.com/akopytov/sysbench): `sysbench cpu help`, `sysbench memory help`.
- [stress-ng](https://github.com/ColinIanKing/stress-ng) and `man stress-ng` (`--vm-bytes`, `--vm-hang`, `--timeout`; verify `--vm-hang 0` on the installed build).
- [iperf3 manual page](https://github.com/esnet/iperf/blob/master/src/iperf3.1): `-B`, `-R`, `-p`, `-u`, `-b`, `-t`, `-O`, `-i`.
- [HammerDB documentation](https://www.hammerdb.com/docs/) (case 03, optional).
