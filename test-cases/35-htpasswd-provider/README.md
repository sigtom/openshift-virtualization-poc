# Test Case 35 - HTPasswd Provider

> **Verification status.** The core create-provider path was rehearsed in the OpenShift 4.22
> console. The steps were cross-checked against the 4.21 and 4.22 documentation; there was no
> 4.21 runtime rehearsal. Changes to an existing externally managed password source, GitOps
> integration or existing production identity provider were not rehearsed and are not verified.

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
| Customer / participant | **[Start the walkthrough](RUNBOOK.md)** |
| Cluster administrator | [Preparation, commands, rotation, cleanup](ADMIN-GUIDE.md#prepare) |
| Everyone | [Record results](RESULTS-TEMPLATE.md) |

## Four stages

1. **Prepare:** the agreed user, inventory of existing providers and users, a second known-good admin session.
2. **ONE quick readiness check.**
3. **Perform and show results:** provider, user, `cluster-admin` binding, login, password rotation.
4. **Stop and clean up:** remove only what the test created, or follow the separate keep-account path.

## How it works

- The provider reads a **file of bcrypt hashes** stored in a Secret in `openshift-config`.
  The Kubernetes `User` API never stores a password. Do not create a `User` object with a
  password; the first successful login creates the `User` and `Identity` objects itself.
- The console cannot generate bcrypt hashes. For an existing Secret, one helper does it:
  `scripts/htpasswd-secret-user.py SECRET_NAME USER_NAME add|rotate|remove` (needs `python3`,
  `oc`, `htpasswd`). It prompts for the password, keeps the other users, keys and metadata,
  and fails on a concurrent change. It refuses Secrets managed by GitOps or External Secrets.
  Its mocked-command tests (`scripts/test_htpasswd_secret_user.py`) cover the logic without a cluster.
- `cluster-admin` is a cluster role. Granting it uses a ClusterRoleBinding and gives the
  agreed user full control of the cluster.

## Files

| File | Purpose |
| --- | --- |
| `templates/htpasswd-secret.template.yaml` | Placeholder-only Secret, for a genuinely new provider |
| `templates/oauth-htpasswd-entry.snippet.yaml` | One provider entry to **append**; not an applicable manifest |
| `templates/cluster-admin-binding.template.yaml` | ClusterRoleBinding to `cluster-admin` for one user |
| `scripts/htpasswd-secret-user.py` | Add, rotate or remove one user in an existing HTPasswd Secret |
| `scripts/test_htpasswd_secret_user.py` | Mocked-command tests (no cluster) |
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
