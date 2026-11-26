# Test Case 35 - HTPasswd Provider

> **Status.** The console steps were exercised on OpenShift 4.22. There is no saved proof yet
> of the password-change login check; record it in your own run. The 4.21 steps were checked
> against documentation only. [Details](ADMIN-GUIDE.md#verification-notes).

For teams asking: *how do we add a local login, make it a cluster administrator, and later
change its password, without disturbing the logins we already have?* The case sets up (or
reuses) an HTPasswd identity provider, adds one test user, grants that user `cluster-admin`,
and rotates its password.

**Scope.** Red Hat's documentation describes HTPasswd for development rather than
production. Treat it here as a short POC or emergency local-access mechanism. For production
use an external identity provider.

## Choose your guide

| Your role | Open this |
| --- | --- |
| Everyone running the test | **[The walkthrough](RUNBOOK.md)**: readiness, add, grant, change password, clean up |
| Cluster administrator | [Preparation and reference](ADMIN-GUIDE.md#prepare): inventory, path choice, recovery |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## How it works

- The provider reads a **password file** (bcrypt hashes) stored in a Secret in
  `openshift-config`. The Kubernetes `User` object never stores a password. The first
  successful login creates the `User` and `Identity` objects.
- The console cannot make bcrypt hashes. The administrator uses standard Linux commands on a
  jump host: `htpasswd -B` to add a user or set a password, `htpasswd -D` to remove one, and
  `oc` with `jq` to read and save the Secret. The save keeps the Secret's other content and is
  refused if someone changed the Secret in the meantime
  ([details](ADMIN-GUIDE.md#secret-update)).
- If GitOps or an operator manages the Secret, its owner changes the source instead.
- `cluster-admin` is a cluster role. The test grants it with one named ClusterRoleBinding,
  created new for this test and removed at cleanup only if it is still that same binding.

## Files

| File | Purpose |
| --- | --- |
| `templates/htpasswd-secret.template.yaml` | Placeholder-only Secret, for a genuinely new provider |
| `templates/oauth-htpasswd-entry.snippet.yaml` | One provider entry to **append**; not an applicable manifest |
| `templates/cluster-admin-binding.template.yaml` | Named ClusterRoleBinding to `cluster-admin` for one user (create only) |
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
