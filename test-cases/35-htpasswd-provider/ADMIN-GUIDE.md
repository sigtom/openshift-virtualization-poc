# Administrator reference: HTPasswd login

> **Status.** The console steps were exercised on OpenShift 4.22. There is no saved proof yet
> of the password-change login check. The 4.21 steps were checked against documentation only.
> See [verification notes](#verification-notes).

The complete test, in order, is the [walkthrough](RUNBOOK.md). This page covers only what
comes before it, the reuse details, recovery and troubleshooting. The commands follow Red
Hat's *Update users for an htpasswd identity provider* procedure ([sources](REFERENCES.md)).
Passwords are typed at the `htpasswd` prompt (no `-b`), so they never appear in command
arguments or shell history.

<a id="prepare"></a>

## Prepare

- [ ] The agreed test user name and who it is for. Use letters, digits and `. _ @ + -` only.
- [ ] Approval to give that user `cluster-admin` (full control of the cluster) for the test.
- [ ] A **second administrator session** that stays open until cleanup is done.
- [ ] A Linux jump host with `oc` (logged in as an administrator), `htpasswd`, `base64` and `jq`.
- [ ] The inventory and path choice below, written on the [results sheet](RESULTS-TEMPLATE.md).

On RHEL, `sudo dnf install httpd-tools jq` provides `htpasswd` and `jq`. Get `oc` from the
console's **Help → Command line tools** page; choose your jump host's operating system and
CPU architecture.

![Command Line Tools page with Linux oc downloads](images/09-command-line-tools.png)

### Inventory (names only)

```sh
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\t"}{.type}{"\t"}{.mappingMethod}{"\t"}{.htpasswd.fileData.name}{"\n"}{end}'
oc get users
oc get identities
```

Record names and types only. For each HTPasswd provider, the last column is its Secret.
Check who manages that Secret. This view prints no Secret data and no annotation values:

```sh
oc get secret SECRET_NAME -n openshift-config -o json | jq '{dataKeys: (.data // {} | keys), ownerReferences: [.metadata.ownerReferences[]? | .kind + "/" + .name], labels: (.metadata.labels // {}), annotationKeys: (.metadata.annotations // {} | keys), managers: ([.metadata.managedFields[]?.manager] | unique)}'
```

Signs that another system manages the Secret: an `ExternalSecret` or other owner reference,
Argo CD or Flux labels or annotation keys, or a GitOps controller among the managers. Then
**change the owning source, or ask its owner**. A live edit would be reverted. Check the OAuth
resource the same way (`oc get oauth cluster -o json | jq ...` with the same filter).

### Choose the path

| Situation | Path |
| --- | --- |
| No HTPasswd provider, or you want a separate demonstration provider | **Create:** a new password file and a new provider. The provider and user names must be unused, and the OAuth owner must agree |
| An existing HTPasswd provider whose Secret nobody else manages | **Reuse:** add one line to its password file, change only that line, remove only that line at cleanup |
| The Secret or OAuth resource is managed by GitOps or an operator | **Owner path:** the owner changes the source. Do not run the walkthrough's Secret commands |

The walkthrough's readiness check (step 1) confirms the name is unused everywhere, including
inside existing password files.

<a id="check"></a>

## Readiness check

The single readiness check is [step 1 of the walkthrough](RUNBOOK.md#1-quick-readiness-check-once).
Run it once, just before step 2.

<a id="secret-update"></a>

## How the Secret update works (reuse path and password change)

Each change uses the same three moves:

1. **Read.** Save the whole Secret as JSON in the run folder, decode its `htpasswd` key into a
   file, and list the user names. An empty list means the key is missing or empty: stop,
   because `htpasswd` would then write a file with one user and the others would lose access.
2. **Change one line.** `htpasswd -B` adds a user or sets a new password; `htpasswd -D`
   removes a user. Other lines stay as they are. Check the user name count before and the
   names list after.
3. **Save.** `jq` puts the changed file back into the saved JSON, and `oc replace` sends it.
   The labels, annotations, other keys and the version number come from the saved copy.
   If the Secret changed after the read, OpenShift refuses the write with *the object has
   been modified*. Read again and repeat; never force it.

Only one administrator changes a given Secret at a time. The version check catches a
collision, but it is better to avoid one.

The test name is checked inside every password file before it is added. A person can have a
valid line in a password file without a User object, because the User is created only at
first login. Without that check, adding the "new" name could change that person's password.
Changing the password of the test user in step 6 is the opposite check: the name must be there.

A Secret that was once created with `oc apply` can carry an old copy of its data in an
annotation. The update keeps that annotation unchanged. Do not print annotation values.

## Login names and providers

The provider uses `mappingMethod: claim`. Its identities are `PROVIDER_NAME:TEST_USER`. A login
whose user name is already taken by an identity from another provider is **refused**, which
prevents silent account takeover.

The YAML route for a new provider, if the console cannot be used: append the
[entry snippet](templates/oauth-htpasswd-entry.snippet.yaml) to the existing
`spec.identityProviders` list of the `cluster` OAuth object. Do **not** apply it as a
resource; that would replace the whole list. If you create the Secret yourself, base the
[template](templates/htpasswd-secret.template.yaml) on the private password file and create
it with `oc create -f`.

<a id="rollback"></a>

## Recovery

- **Never restore an old saved copy** of the password file or Secret. It would drop users
  added since and could bring back a retired password. Read the current Secret again and
  repeat the change.
- If authentication does not settle, stop editing. Check its conditions
  (`oc get clusteroperator authentication -o yaml`) and the `oauth-openshift` pods in
  `openshift-authentication`. Keep the second administrator session open.
- If the test user's grant must end at once, delete its binding (walkthrough step 7, first
  block) and its tokens. A password change alone does not end existing sessions.

<a id="troubleshooting"></a>

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Login says invalid | Secret saved? Authentication settled? Hash made with `-B`? User name case? |
| Login refused after a name collision | Another provider owns that user name (`claim`) |
| *the object has been modified* | Someone changed the Secret after you read it. Read again and repeat |
| A count in the walkthrough differs | Stop. The name is already used, or the file is empty or missing. Do not add or remove anything |
| Existing users cannot log in | Stop, keep the second session, check authentication and the owning source. Do not reset other users' passwords |
| A change was reverted | A GitOps or operator owner reconciled it; change the owning source |
| Provider missing in the console | The OAuth list was edited elsewhere; compare with the inventory |

<a id="verification-notes"></a>

## Verification notes

- Console provider setup, first login, `cluster-admin` access and cleanup were exercised on
  OpenShift 4.22.
- An earlier form of the file and Secret commands (rebuilding the Secret with
  `oc create secret ... --dry-run=client | oc replace`) was checked on 4.22 with temporary
  Secrets. The current commands (versioned `oc replace` of the saved Secret, the named
  binding created new) were checked only with local sample files and a server-side dry run of a
  Secret, not in a full run.
- No saved screenshot or recording shows the password-change login check (new password
  works, old one refused). Record it in your own run.
- 4.21 was checked against documentation only. Managed password sources, GitOps integration
  and existing production identity providers remain unverified.
