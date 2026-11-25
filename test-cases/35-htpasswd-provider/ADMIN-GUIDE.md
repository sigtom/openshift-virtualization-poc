# Administrator guide: HTPasswd user management

> **Verification status.** The create-provider path (console add, first login, `cluster-admin`
> binding, password rotation and cleanup) was rehearsed in the OpenShift 4.22 console. The
> steps were cross-checked against the 4.21 and 4.22 documentation; there was no 4.21 runtime
> rehearsal. Changes to an existing externally managed password source, a GitOps integration
> or an existing production identity provider were **not** rehearsed and are not verified.
> The installed version's documentation governs.

The customer follows the [walkthrough](RUNBOOK.md). This guide holds the commands. The only
steps that need a command line are changing the bcrypt hashes, done by one helper:
[`scripts/htpasswd-secret-user.py`](scripts/htpasswd-secret-user.py) `SECRET_NAME USER_NAME add|rotate|remove`.

**Run every command in this guide from `test-cases/35-htpasswd-provider` inside your
downloaded checkout** (the `scripts/...` paths are relative to it). Hash files are written
outside the checkout by absolute path, so the working directory never matters for them.

<a id="prepare"></a>

## Stage 1: Prepare

- [ ] The agreed user name and who it is for. `cluster-admin` gives that user full control of the cluster, so grant it only to the agreed user.
- [ ] A **second administrator session** (different browser profile or a kubeconfig) that stays open until the new login is verified.
- [ ] Inventory of providers, users and Secret ownership (below).
- [ ] `python3`, `htpasswd` (Apache utils) and `oc` (logged in) on the admin workstation.
- [ ] An unused test user name: letters, digits and `. _ @ + -` only.

Use a Linux administrator workstation or jump host for the short commands. On RHEL, install
the hash tool with `sudo dnf install httpd-tools python3`. Get `oc` from the console's
**Help → Command line tools** page if it is not already installed.

### Inventory

```sh
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\t"}{.type}{"\t"}{.mappingMethod}{"\t"}{.htpasswd.fileData.name}{"\n"}{end}'
oc get users
oc get identities
```

Record names and types only. For each HTPasswd provider note its Secret, then check who owns
it:

```sh
oc get secret SECRET_NAME -n openshift-config -o jsonpath='{.metadata.labels}{"\n"}{.metadata.annotations}{"\n"}{.metadata.ownerReferences}{"\n"}'
```

Argo CD or Flux labels, or an `ExternalSecret` owner, mean another system owns the Secret.
Then **edit the owning source or ask its owner**; a live edit would be reverted and the two would
fight. Do the same for the OAuth resource if it is managed.

### Choose the path

| Situation | Path |
| --- | --- |
| Existing HTPasswd provider, Secret **not** managed by GitOps or External Secrets | **Reuse:** the helper changes only the Secret's `htpasswd` content |
| Secret or OAuth resource managed by GitOps or External Secrets (even if you own it) | **Owner/source path:** change the owning source; the helper refuses these and there is no bypass |
| No HTPasswd provider, or you want a separate demonstration provider | **Create:** new file (`-c`) and a new dedicated provider. Other providers may exist; the provider and user names must be unused and the OAuth owner must permit it |

If an existing provider's Secret holds only one user, do not remove that user (the helper refuses
it): the provider is not yours to delete.

<a id="check"></a>

## Stage 2: Quick readiness check (ONE check)

```sh
oc whoami                                              # your existing admin
oc get clusteroperator authentication                  # Available=True, Progressing=False, Degraded=False
oc get oauth cluster -o jsonpath='{.spec.identityProviders[*].name}{"\n"}'   # providers match the inventory
oc get secret SECRET_NAME -n openshift-config -o name  # reuse path only
```

Ready only if the operator is settled, the providers match the inventory, the second session
works and the user name is not already used by another provider's identity (`oc get identities`).
Run it once.

<a id="user"></a>

## Stage 3: Perform

### 3.1 Add the user's hash (the only CLI-required step)

**Reuse path (existing Secret):** run the helper. It prompts for the password through
`htpasswd -B`, so the password never appears in arguments, environment or shell history.

```sh
scripts/htpasswd-secret-user.py SECRET_NAME TEST_USER add
```

The helper reads the current Secret, changes only that user's line and replaces the Secret using
the `resourceVersion` it read: a concurrent edit makes it fail rather than be overwritten. Other
users, other keys, labels and annotations are preserved. It uses private temporary files
(`0700`/`0600`) that it deletes afterwards (deletion is not secure erasure on an SSD), prints no
Secret, hash or password, and refuses Secrets owned by Argo CD, Flux or External Secrets: edit
the owning source instead. It does not touch the OAuth resource, roles or tokens. Use
`--help` for details.

**Create path (no HTPasswd provider yet):** make a new file in a private folder **outside the
checkout**, by absolute path, then upload it in 3.2. `-c` creates (and would erase an existing
file), so use it only here:

```sh
umask 077
mkdir -p "$HOME/poc-private/htpasswd"
chmod 700 "$HOME/poc-private" "$HOME/poc-private/htpasswd"
htpasswd -c -B "$HOME/poc-private/htpasswd/users.htpasswd" TEST_USER
```

Upload `$HOME/poc-private/htpasswd/users.htpasswd` in 3.2 and delete it in Stage 4. Never put it
in the repository, tickets, chat or screenshots.

### 3.2 Provider and Secret

- **Create path, console (preferred):** **Administration → Cluster Settings → Configuration**,
  filter for `OAuth`, open **OAuth → Add → HTPasswd**, enter a unique name, use **Browse…** to
  choose the file, then press **Add**. The console creates a generated Secret and appends the
  provider (`mappingMethod: claim`) to the existing list, keeping the other providers. **Record
  the generated Secret name**: on the OAuth page open **YAML**, find your provider under
  `identityProviders`, and read its `htpasswd.fileData.name`. Record the name only; do not edit.
  **Stop any screenshot or recording before loading the file:** the upload form shows the file
  contents, including hashes. Resume only after you are back on the OAuth details page. YAML
  fallback: append the
  [entry snippet](templates/oauth-htpasswd-entry.snippet.yaml) to the existing OAuth list; do
  **not** apply it as a resource. If you create the Secret yourself, base the
  [template](templates/htpasswd-secret.template.yaml) on the private file.
- **Reuse path:** the helper in 3.1 already updated the Secret. If it reports a conflict,
  someone else changed the Secret: re-run it, do not force. Console users can view the Secret,
  but do not paste hashes by hand.

Wait for the rollout. After **Add**, the page links **View authentication conditions for
reconfiguration status.** (or use **Administration → Cluster Settings → ClusterOperators →
authentication**). Wait for Available True, Progressing False, Degraded False. CLI alternative
(Ctrl+C once it settles):

```sh
oc get clusteroperator authentication -w
```

The provider's `mappingMethod` is `claim`: the identity is `PROVIDER_NAME:TEST_USER` and a login
whose user name is already taken by an identity from another provider is **refused**, which
prevents silent account takeover. Confirm no other provider has `TEST_USER` (the readiness check).

### 3.3 First login creates the User

Log in as the test user in a fresh separate browser session (private window or another
profile). Before the grant, the account should lack node-administration access. This creates the `User`
and `Identity`:

```sh
oc get user TEST_USER
oc get identity PROVIDER_NAME:TEST_USER
```

Do not create a `User` yourself and do not put a password in any object.

### 3.4 Grant cluster-admin (explicit full privilege)

Console: **User Management → RoleBindings → Create binding → Cluster-wide role binding**, role
`cluster-admin`, subject User `TEST_USER`. CLI equivalent, or the
[template](templates/cluster-admin-binding.template.yaml):

```sh
oc adm policy add-cluster-role-to-user cluster-admin TEST_USER
```

(The CLI binding has a generated name; record it. The console form lets you choose the name.)
Verify as the test user: reload and confirm **Compute → Nodes** opens. A sidebar label alone is
not proof of authorization. For a CLI check, `oc auth can-i '*' '*' --all-namespaces` run as
the test user should say `yes`.

Keep the second administrator session open until this works.

### 3.5 Rotate the password

```sh
scripts/htpasswd-secret-user.py SECRET_NAME TEST_USER rotate
oc get clusteroperator authentication -w
```

After the rollout, sign the test user out and log in with the **new** password (works).
Sign out again, then try the **old** password once: it is refused (for example,
"Invalid login or password. Please try again."). Check that other users still log in.

**Sessions:** changing the password does **not** revoke existing OAuth tokens or console
sessions. If access must end, that is a separate action (sign-out, or deleting that
user's OAuth access tokens per the authentication documentation). Do not claim rotation
revoked access.

### Recovery and rollback

Never restore an old saved copy of the file: it would drop users added since and could
revive a retired password. Re-run the helper (`rotate` or `remove`) against the current Secret.
If the operator does not settle, check its conditions and the OAuth pods, do not edit further, and
keep the second session.

## Stage 4: Stop and clean up

Remove **only what this test created**.

**Cleanup, provider created by this test** (the Secret then holds only the test user, so never
run the helper's `remove`):

1. `oc delete clusterrolebinding BINDING_NAME` (console: **User Management → RoleBindings**).
2. Remove **only this provider**: on the **OAuth** page, in the **Identity providers** table, open
   **Actions** (three dots) on **only this provider's row** → **Remove identity provider** →
   **Remove**. Names in the table are not links. Confirm the remaining list equals the inventory.
3. Wait for the authentication operator: Available True, Progressing False, Degraded False.
4. `oc delete secret SECRET_NAME -n openshift-config` (only the generated Secret this test
   created; removing the provider does not delete it).
5. `oc delete user TEST_USER` and `oc delete identity PROVIDER_NAME:TEST_USER`.
6. Retiring this account (not keeping it):
   `oc delete oauthaccesstokens --field-selector=userName=TEST_USER`. Never list token values.
7. `rm "$HOME/poc-private/htpasswd/users.htpasswd"`.

**Cleanup, existing unmanaged provider reused** (keep the provider, Secret and other users):

```sh
oc delete clusterrolebinding BINDING_NAME
scripts/htpasswd-secret-user.py SECRET_NAME TEST_USER remove
oc get clusteroperator authentication -w
oc delete user TEST_USER
oc delete identity PROVIDER_NAME:TEST_USER
```

If the test user is the provider's only user, stop: do not delete the provider or Secret; ask its
owner. Never remove existing providers, users or Secrets. If the account is retired, also run
`oc delete oauthaccesstokens --field-selector=userName=TEST_USER`.

**Keep-account path:** keep the provider, Secret, user and binding. Delete the local hash file,
record the owner and review date, and apply your own credential policy. The account remains full
cluster-admin until someone removes the binding. Deleting a local file does not guarantee
secure erasure on an SSD.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Login says invalid | Secret updated? operator settled? hash from `-B`? name case |
| Login refused after a collision | Another provider owns that user name (`claim`) |
| Existing users broke | Stop, keep the administrator session open, and check the authentication operator and owning source; do not reset other users' passwords |
| Change reverted | A GitOps or external-secrets owner reconciled it; edit the owning source |
| Provider missing in console | OAuth list edited elsewhere; compare with the inventory |
