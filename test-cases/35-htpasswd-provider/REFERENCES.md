# Sources and applicability

The provider, Secret, password-file update and cluster-admin binding procedures were
cross-checked against the OpenShift 4.21 and 4.22 documentation. The create-provider path
was rehearsed in the 4.22 console only; there was no 4.21 runtime rehearsal, and a
documentation check is not an executed test.

| Topic | 4.21 | 4.22 |
| --- | --- | --- |
| Configure HTPasswd, update users and use the console | [Chapter 7](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/configuring-identity-providers) | [Chapter 7](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/configuring-identity-providers) |
| Identity mapping and existing user names | [Identity providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/understanding-identity-provider) | [Identity providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/understanding-identity-provider) |
| Cluster roles, bindings and cluster-admin | [Using RBAC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/using-rbac) | [Using RBAC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/using-rbac) |

Red Hat limits HTPasswd authentication to development environments; use an external
identity provider for production. This procedure is for an approved demonstration.
The commands use an interactive password prompt to keep passwords out of process
arguments and shell history. User names cannot contain `/`, `:` or `%`.
