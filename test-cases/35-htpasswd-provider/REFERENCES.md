# Sources and applicability

The provider, Secret, password-file update and cluster-admin procedures were checked against
the OpenShift 4.21 and 4.22 documentation. Console provider setup, login, cluster-admin access
and cleanup were exercised on 4.22. An earlier form of the file and Secret commands was checked
on 4.22 with temporary Secrets; the current conditional update was checked only with local
sample files. There was no 4.21 runtime rehearsal. A documentation check is not an executed test.

| Topic | 4.21 | 4.22 |
| --- | --- | --- |
| Configure HTPasswd, update users and use the console | [Chapter 7](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/configuring-identity-providers) | [Chapter 7](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/configuring-identity-providers) |
| Identity mapping and existing user names | [Identity providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/understanding-identity-provider) | [Identity providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/understanding-identity-provider) |
| Cluster roles, bindings and cluster-admin | [Using RBAC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/authentication_and_authorization/using-rbac) | [Using RBAC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/using-rbac) |

The `htpasswd` options (`-B`, `-c`, `-D`, interactive prompt) are described in the
[Apache htpasswd documentation](https://httpd.apache.org/docs/2.4/programs/htpasswd.html).
The version check used when saving the Secret is standard Kubernetes optimistic concurrency
([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions)).

Red Hat limits HTPasswd authentication to development environments; use an external
identity provider for production. This procedure is for an approved demonstration.
The commands use an interactive password prompt to keep passwords out of process
arguments and shell history. User names cannot contain `/`, `:` or `%`.
