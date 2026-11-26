# Test Case 35 - HTPasswd Provider

> **Verification status.** Console provider setup, first login, `cluster-admin` access and
> cleanup were exercised on OpenShift 4.22. The standard `htpasswd` and `oc` file/Secret
> updates were verified separately on 4.22 using temporary Secrets. The 4.21 steps were
> checked against documentation only. Managed password sources and existing production
> identity providers remain unverified.

For teams asking: *how do we add a local login, make it a cluster administrator, and later
change its password, without disturbing the logins we already have?* The walkthrough sets up
a new temporary HTPasswd identity provider, adds one test user, grants that user `cluster-admin`,
and rotates its password.

**Scope.** Red Hat's documentation describes HTPasswd for development rather than
production. Treat it here as a short POC or emergency local-access mechanism. For production
use an external identity provider.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Everyone | **[Start the walkthrough](RUNBOOK.md)**: one complete new-provider path |
| Cluster administrator | [Reference: existing provider, ownership, rollback, troubleshooting](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Walkthrough steps

The [walkthrough](RUNBOOK.md) covers: prepare (tools, private folder, new password file),
one readiness check, create the provider in the console, first login, `cluster-admin`
binding, verify, rotate the password, and clean up in order.

## How it works

- The provider reads a **file of bcrypt hashes** stored in a Secret in `openshift-config`.
  The Kubernetes `User` API never stores a password. Do not create a `User` object with a
  password; the first successful login creates the `User` and `Identity` objects itself.
- The console cannot generate bcrypt hashes. Use standard commands on a Linux jump host
  (`oc`, `htpasswd` from RHEL `httpd-tools`, `base64`): retrieve the file from the Secret,
  run `htpasswd -B` (add or rotate, with a password prompt) or `htpasswd -D` (remove),
  then replace the Secret with `oc create secret generic ... --dry-run=client -o yaml | oc replace -f -`.
  This is for a dedicated, unmanaged HTPasswd-only Secret; if GitOps or an operator owns it, or
  it holds other data to preserve, its owner updates the owning source. See the
  [administrator guide](ADMIN-GUIDE.md#user).
- `cluster-admin` is a cluster role. Granting it uses a ClusterRoleBinding and gives the
  agreed user full control of the cluster.

## Files

| File | Purpose |
| --- | --- |
| `templates/htpasswd-secret.template.yaml` | Placeholder-only Secret, for a genuinely new provider |
| `templates/oauth-htpasswd-entry.snippet.yaml` | One provider entry to **append**; not an applicable manifest |
| `templates/cluster-admin-binding.template.yaml` | ClusterRoleBinding to `cluster-admin` for one user |
| `REFERENCES.md` | Sources |

## Boundaries

- Existing OAuth providers, users and Secrets are **preserved**. You may add a separate dedicated demonstration provider (unused names, OAuth owner permits it) or reuse an existing unmanaged one.
- If GitOps or an external-secrets tool owns the Secret or OAuth resource, change the owning source or ask its owner; do not fight it live.
- Passwords, hash files and Secret data never go into Git, reports, chat or screenshots.
- A password change does **not** revoke existing sessions or tokens.
- No real demo accounts or passwords are shipped.

## Screenshots

Redact file hashes, Secret data, password fields, tokens and any hostnames or account names
before adding any picture. The file-upload form shows the hashes, so never capture it with a
file loaded.
