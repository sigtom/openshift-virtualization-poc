# Sources and applicability

> Procedures must be checked against the installed release. Reading a document is not an executed
> result. Client console verification is **pending**.

## Red Hat

| Topic | 4.21 | 4.22 |
| --- | --- | --- |
| Virtualization monitoring and VM metrics | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/monitoring) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/monitoring) |
| Managing VMs, console, disks | [4.21](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/virtualization/managing-vms) | [4.22](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/virtualization/managing-vms) |
| Monitoring stack: configuring user workload monitoring | [4.21](https://docs.redhat.com/en/documentation/monitoring_stack_for_red_hat_openshift/4.21/html-single/configuring_user_workload_monitoring/index) | [4.22](https://docs.redhat.com/en/documentation/monitoring_stack_for_red_hat_openshift/4.22/html-single/configuring_user_workload_monitoring/index) |

The monitoring procedures were reviewed for both versions. Installed APIs and permissions govern;
client console execution remains pending.

Upstream: [KubeVirt metrics](https://kubevirt.io/monitoring/metrics.html) (`kubevirt_vmi_storage_*` counters),
[fio documentation](https://fio.readthedocs.io/en/latest/fio_doc.html) (`--readonly`, `allow_file_create`,
`rate_iops`, `direct`, `percentile_list`, JSON output).

## Dell (deferred layer; reference evidence, not an upgrade recommendation)

| Topic | Source | Note |
| --- | --- | --- |
| Current manuals | [Dell Container Storage Modules manuals](https://www.dell.com/support/product-details/en-us/product/container-storage-modules/resources/manuals) | Use the current 1.18 documents (1.18.2 release); older GitHub docs are legacy |
| Support matrix, OpenShift | [CSM 1.18 OpenShift compatibility](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_support_matrix_118/red-hat-openshift-compatibility?guid=guid-2b70e769-a821-440f-a8c9-b5b071498eab&lang=en-us) | Lists supported OpenShift, CSM and operator version combinations. Match your versions before installing or upgrading |
| Support matrix, virtualization | [CSM 1.18 virtualization](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_support_matrix_118/virtualization?guid=guid-7197fcd5-3b68-499a-9689-8a9e7178dbfa&lang=en-us) | Check PowerFlex Observability support for your OpenShift and PowerFlex versions, connection type and host kernel against E-Lab |
| Legacy matrix | [csm-docs support matrix](https://dell.github.io/csm-docs/docs/supportmatrix) | **Legacy only**: stops at 4.20; not evidence that 4.21 is unsupported |
| Operator CRD (installed schema governs) | [csm-operator v1.13.0 CRD](https://github.com/dell/csm-operator/blob/v1.13.0/bundle/manifests/storage.dell.com_containerstoragemodules.yaml) ([raw](https://raw.githubusercontent.com/dell/csm-operator/v1.13.0/bundle/manifests/storage.dell.com_containerstoragemodules.yaml)) | `spec.modules` is plural; older prose that writes `spec.module` is stale. Use the tag matching the installed Operator |
| Administrator guide | [CSM administrator guide](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_administrator_guide/Container-Storage-Modules-overview?guid=guid-e87a5431-b3cc-46b1-957d-a97242ea4d2a&lang=en-us) | Lifecycle, troubleshooting |
| Operator on OpenShift | [Install the operator using OpenShift](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_administrator_guide/install-the-container-storage-modules-operator-using-openshift?guid=guid-f1a77208-325e-45a5-a4d6-4d4571957823&lang=en-us) | Full new install is out of scope |
| Observability (generic, current) | [Installing observability](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_administrator_guide/installing-observability?guid=guid-e578cc65-eab3-4685-9da3-ba28a2b6200a&lang=en-us) | Its sample is a different array family (PowerMax): do not copy `driverType`/`configVersion` |
| PowerFlex on OpenShift (legacy, technically relevant) | [Observability via operator](https://dell.github.io/csm-docs/docs/getting-started/installation/openshift/powerflex/csmoperator/csm-modules/observability/) | Release must be checked against the installed version |
| Dashboards | [Importing dashboards](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_administrator_guide/importing-container-storage-modules-for-observability-dashboards?guid=guid-df62ce55-1c7a-404d-957e-0bc8c81bd5ac&lang=en-us) | PowerFlex: I/O Performance by Provisioned Volume / by Kubernetes Node; CSI Driver Provisioned Volume Topology |
| PowerFlex metrics | [Metrics](https://dell.github.io/csm-docs/v3/observability/metrics/powerflex/) | v3 legacy names; discover the current names on the client |

The Dell Operator, PowerFlex observability, support-matrix, metrics, dashboard and lifecycle guidance
was reviewed. This does not replace checking the installed release: every Dell execution step remains
deferred and untested on the actual backend.

Additional support checks: [storage platforms](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_support_matrix_118/Storage-platforms?guid=guid-3e0c8824-ff76-498e-baf8-0b6ea57254b7&lang=en-us) and [lifecycle guidance](https://www.dell.com/support/manuals/en-us/container-storage-modules/csm_life_cycle_management_guide/Upgrading-Container-Storage-Modules?guid=guid-8f29b6c5-ef6c-4906-9e9d-dc98649cd4e2&lang=en-us). Driver upgrade or migration is outside this case.
