# Administrator reference: HTPasswd

> **Verification status.** Console provider setup, first login, `cluster-admin` access and
> cleanup were exercised on OpenShift 4.22. The standard file/Secret commands were verified
> separately on 4.22 using temporary Secrets. The 4.21 steps were checked against
> documentation only. Managed password sources, GitOps integration and existing production
> identity providers remain unverified.

The full **new temporary provider** sequence (tools, private folder, create, login, admin
binding, rotate, cleanup) is in the [walkthrough](RUNBOOK.md) and is not repeated here. This
page covers what the walkthrough leaves out: inventory and ownership, claim collisions,
reusing an **existing** provider, recovery and troubleshooting. Commands are standard Linux
jump-host commands from Red Hat's *Update users for an htpasswd identity provider* procedure
([sources](REFERENCES.md)); passwords are typed at the `htpasswd` prompt, never with `-b`.

Run all reference commands as your existing administrator. Commands use the Bash setup and private file
`$HOME/poc-private/htpasswd/users.htpasswd` from the
[walkthrough's preparation](RUNBOOK.md#prepare).

<a id="prepare"></a>

## Inventory and Secret ownership

Record provider names and types only:

```sh
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\t"}{.type}{"\t"}{.mappingMethod}{"\t"}{.htpasswd.fileData.name}{"\n"}{end}'
oc get users
oc get identities
```

For each HTPasswd provider note its Secret, then check who owns it:

```sh
oc get secret SECRET_NAME -n openshift-config -o jsonpath='{.metadata.labels}{"\n"}{.metadata.annotations}{"\n"}{.metadata.ownerReferences}{"\n"}'
```

Argo CD or Flux labels, or an `ExternalSecret` owner, mean another system owns the Secret. Then
**edit the owning source or ask its owner**; a live edit would be reverted and the two would
fight. Do the same for the OAuth resource if it is managed. This simple replacement is only for
a **dedicated, unmanaged HTPasswd-only Secret**; if the Secret holds other data or metadata that
must be preserved, do not use it, and make no destructive change to shared metadata.

| Situation | Path |
| --- | --- |
| No HTPasswd provider, or you want a separate demonstration provider | **Create:** follow the [walkthrough](RUNBOOK.md). Provider and user names must be unused and the OAuth owner must permit it |
| Existing HTPasswd provider, dedicated Secret **not** managed by GitOps or External Secrets | **Reuse:** below |
| Secret or OAuth resource managed by GitOps or an operator | **Owner/source path:** change the owning source; do not replace the Secret live |

Existing OAuth providers stay unchanged on every path. Only one administrator updates a Secret at a
time; if another edit occurs, fetch the latest file and repeat your change.

<a id="check"></a>

## Readiness for reuse

Run the walkthrough's [readiness check](RUNBOOK.md#check) once, and also confirm the Secret:

```sh
oc get secret SECRET_NAME -n openshift-config -o name
```

## Claim collisions

New providers use `mappingMethod: claim`: the identity is `PROVIDER_NAME:TEST_USER`, and a login
whose user name is already taken by an identity from another provider is **refused**. This
prevents silent account takeover. Before adding a user, confirm no other provider has that name
(`oc get identities`).

<a id="user"></a>

## Reuse an existing provider: add a user

`SECRET_NAME` is the Secret this provider references: read it from the OAuth YAML
(`htpasswd.fileData.name`). Always fetch the latest file first. Never use `-c` here; it would
erase the file. `htpasswd -B` adds the user (or changes the password if the line exists) and
leaves other users' lines alone. Do not edit the OAuth resource.

```sh
oc get secret SECRET_NAME -n openshift-config -o jsonpath='{.data.htpasswd}' | base64 --decode > "$HOME/poc-private/htpasswd/users.htpasswd"
htpasswd -B "$HOME/poc-private/htpasswd/users.htpasswd" TEST_USER
oc create secret generic SECRET_NAME --from-file=htpasswd="$HOME/poc-private/htpasswd/users.htpasswd" --dry-run=client -o yaml -n openshift-config | oc replace -f -
oc get clusteroperator authentication
```

Wait for Available True, Progressing False, Degraded False. Then continue with the
walkthrough's [first login](RUNBOOK.md#first-login), [admin binding](RUNBOOK.md#user) and [rotation](RUNBOOK.md#rotate) steps,
using this `SECRET_NAME`. After rotation, return to [reuse cleanup below](#reuse-cleanup).
**Do not use walkthrough step 8 for an existing provider:** it removes the whole provider and
Secret. Do not paste hashes into the console by hand.

<a id="rotate"></a>

## Reuse an existing provider: rotate or remove

**Rotate:** the same four commands as above; `htpasswd -B` on an existing line changes only that
user's password. See the [walkthrough's rotation step](RUNBOOK.md#rotate) for the sign-in checks.

<a id="reuse-cleanup"></a>

**Remove the test user's line** (account retired, provider kept). Remove the binding first:

```sh
oc delete clusterrolebinding BINDING_NAME
oc get secret SECRET_NAME -n openshift-config -o jsonpath='{.data.htpasswd}' | base64 --decode > "$HOME/poc-private/htpasswd/users.htpasswd"
cut -d: -f1 "$HOME/poc-private/htpasswd/users.htpasswd"
```

The last command shows user names only. **Confirm another user will remain** after the test
user is removed. If not, stop and contact the provider owner: never remove the last user of a
retained provider. Then:

```sh
htpasswd -D "$HOME/poc-private/htpasswd/users.htpasswd" TEST_USER
oc create secret generic SECRET_NAME --from-file=htpasswd="$HOME/poc-private/htpasswd/users.htpasswd" --dry-run=client -o yaml -n openshift-config | oc replace -f -
oc get clusteroperator authentication
```

**Wait** for Available True, Progressing False and Degraded False (run the last command again if
needed). Once settled, remove the retired account resources:

```sh
oc delete user TEST_USER
oc delete identity PROVIDER_NAME:TEST_USER
oc delete oauthaccesstokens --field-selector=userName=TEST_USER
rm "$HOME/poc-private/htpasswd/users.htpasswd"
```

Never delete the provider or Secret on this path, and never remove existing providers, users or
Secrets. The token line applies when the account is retired (not kept); never list token values.
To keep the account instead, keep the user and binding, delete the local file, and record the
owner and review date.

## Sessions

Changing a password does **not** revoke existing OAuth tokens or console sessions. If access must
end, that is a separate action (sign-out, or deleting that user's OAuth access tokens per the
authentication documentation). Do not claim rotation revoked access.

## Recovery and rollback

Never restore an old saved copy of the file: it would drop users added since and could revive a
retired password. Fetch the current Secret again and repeat the change. If the operator does not
settle, check its conditions and the OAuth pods, do not edit further, and keep the second
administrator session open.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Login says invalid | Secret updated? operator settled? hash from `-B`? name case |
| Login refused after a collision | Another provider owns that user name (`claim`) |
| Existing users broke | Stop, keep the administrator session open, and check the authentication operator and owning source; do not reset other users' passwords |
| Change reverted | A GitOps or operator owner reconciled it; edit the owning source |
| Provider missing in console | OAuth list edited elsewhere; compare with the inventory |
