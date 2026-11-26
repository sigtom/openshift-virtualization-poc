# HTPasswd login: walkthrough

> **Status.** The console steps (add a provider, first login, cluster-admin, cleanup) were
> exercised on OpenShift 4.22. There is no saved proof yet of the password-change login check
> (new password works, old one is refused); record it in your own run. The 4.21 steps were
> checked against documentation only. [Details](ADMIN-GUIDE.md#verification-notes).

**Goal:** add a local test login, make it a cluster administrator, change its password, and
then remove it, while the existing logins keep working.

This is the one walkthrough for the whole test. Each step says where it happens:

- **Console** steps happen in the OpenShift web console. The participant can click while the
  administrator watches.
- **Terminal** steps are run by the administrator on a Linux jump host with `oc` (logged in
  as an administrator), `htpasswd`, `base64` and `jq`. Use one Bash terminal for the whole
  run and keep it open.

Before you start, the administrator completes the short [preparation](ADMIN-GUIDE.md#prepare):
the list of existing logins, the choice of **create** path (a new demonstration provider) or
**reuse** path (an existing provider), and the [results sheet](RESULTS-TEMPLATE.md).
Passwords are handed over privately and never written on the sheet.

**Keep a second administrator session open** (another browser profile or terminal) until the
end. If anything goes wrong, you still have a working way in.

## 1. Quick readiness check (once)

**Terminal.** Set the names from the results sheet and make a new private run folder. The
folder holds the password file and saved copies for this run only.

```bash
TEST_USER='poc-user'
PROVIDER_NAME='poc-htpasswd'
BINDING_NAME='poc-cluster-admin-poc-user'
umask 077
RUN_DIR=''
mkdir -p "$HOME/poc-private/htpasswd" && chmod 700 "$HOME/poc-private" "$HOME/poc-private/htpasswd" &&
  RUN_DIR=$(mktemp -d "$HOME/poc-private/htpasswd/run-XXXXXX") && echo "Run folder: $RUN_DIR"
```

Continue only if the last line printed `Run folder:` and a path. If it printed an error or
nothing, stop and fix the folder problem first. Later commands check that this folder exists
and do nothing if it does not.

Write the run folder path in your private notes. If you have to open a new terminal later,
set the three names again and set `RUN_DIR` to that path. On the reuse path, also set
`SECRET_NAME` to the provider's Secret from the preparation inventory.

Now run the check:

```bash
oc whoami
oc get clusteroperator authentication
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\n"}{end}'
oc get user "$TEST_USER"
oc get identities -o jsonpath='{range .items[*]}{.user.name}{"\n"}{end}' | grep -cxF "$TEST_USER"
oc get clusterrolebinding "$BINDING_NAME"
```

Then, for **each** HTPasswd Secret in the inventory, check that its password file does not
already list the test name. This finds an account that exists in a file but has never logged
in, so it has no User object yet:

```bash
oc get secret EXISTING_SECRET -n openshift-config -o jsonpath='{.data.htpasswd}' | base64 --decode | cut -d: -f1 | grep -cxF "$TEST_USER"
```

**Ready when:** `oc whoami` shows your administrator; authentication shows Available `True`,
Progressing `False`, Degraded `False`; the provider list matches the inventory; the user and
the binding are `NotFound`; and every count prints `0`. The second administrator session works.

If any item differs, stop. Choose another test name, or ask the provider's owner. Do not
continue with a name that is already in use.

## 2. Add the test user

### Create path: new provider

**Terminal.** Create the password file. `htpasswd` asks for the password twice. `-c` creates
a new file. The checks in front run it only inside the run folder and only if no password
file is there yet, so nothing else can be overwritten:

```bash
[ -d "$RUN_DIR" ] && [ ! -e "$RUN_DIR/users.htpasswd" ] && htpasswd -c -B "$RUN_DIR/users.htpasswd" "$TEST_USER"
```

If no password prompt appears, `RUN_DIR` is not set or the file already exists: stop and check.

**Hand the file to the browser.** The console upload reads the file from the computer that
runs the browser. If the browser runs on the jump host, use `$RUN_DIR/users.htpasswd` as it
is. Otherwise copy the file privately (for example with `scp`) to a private folder on the
browser computer, and delete that copy right after the upload.

**Console.** Pause any screenshot or recording first: the form shows the file contents.

1. Open **Administration → Cluster Settings → Configuration**, filter for `OAuth` and open **OAuth**.
   Write down the providers listed. They should match the inventory.
2. Open **Add → HTPasswd**. Enter the provider name from your sheet.
3. Click **Browse…**, choose the password file, then click **Add**.
4. Return to the OAuth details page before you resume recording.

![HTPasswd provider setup form before uploading the password file](images/01-provider-setup-form.png)

![Dedicated demonstration provider added; existing provider names are hidden](images/03-provider-added.png)

**Terminal.** The console stored the file in a new Secret. Find its name and save its UID, so
cleanup can later prove it removes only this Secret:

```bash
SECRET_NAME=$(oc get oauth cluster -o json | jq -r --arg p "$PROVIDER_NAME" '.spec.identityProviders[] | select(.name == $p) | .htpasswd.fileData.name')
echo "Secret: $SECRET_NAME"
oc get secret "$SECRET_NAME" -n openshift-config -o jsonpath='{.metadata.uid}{" "}{.metadata.creationTimestamp}{"\n"}' | tee "$RUN_DIR/secret.uid"
```

**Expected:** one Secret name, created a minute ago. Write the name on the sheet.

**Create path done.** Skip the reuse path below and continue with
[step 3](#3-wait-for-authentication-to-settle).

### Reuse path: existing provider

Use this only on the reuse path. Never use it on a file you just created.

The administrator adds one line to the provider's password file. Other users' lines stay as
they are, and the provider list does not change.

**Terminal.** Read the current file:

```bash
[ -d "$RUN_DIR" ] && oc get secret "$SECRET_NAME" -n openshift-config -o json > "$RUN_DIR/add-before.json" &&
  jq -r '.data.htpasswd // ""' "$RUN_DIR/add-before.json" | base64 --decode > "$RUN_DIR/add.htpasswd" &&
  cut -d: -f1 "$RUN_DIR/add.htpasswd" && cut -d: -f1 "$RUN_DIR/add.htpasswd" | grep -cxF "$TEST_USER"
```

**Expected:** the existing user names, then `0`. If the list is empty, or the count is not
`0`, stop. Do not add the user.

Add the user (it asks for the password twice), then list the names again:

```bash
[ -s "$RUN_DIR/add.htpasswd" ] && htpasswd -B "$RUN_DIR/add.htpasswd" "$TEST_USER" && cut -d: -f1 "$RUN_DIR/add.htpasswd"
```

**Expected:** the same names as before, plus the test user. If nothing printed, stop. Save
the change:

```bash
jq --rawfile f "$RUN_DIR/add.htpasswd" '.data.htpasswd = ($f | @base64)' "$RUN_DIR/add-before.json" > "$RUN_DIR/add-after.json" &&
  oc replace -f "$RUN_DIR/add-after.json"
```

**What these two lines protect.** The saved copy keeps the Secret's labels, annotations, other
keys and its version number; only the password file changes. If anyone changed the Secret
after you read it, `oc replace` refuses with *the object has been modified*. Nothing was
changed then: start this step again from the first command. Do not force it.

**Reuse path done.** Continue with step 3.

## 3. Wait for authentication to settle

**Console.** After **Add** (create path), click **View authentication conditions for
reconfiguration status.** Or open **Administration → Cluster Settings → ClusterOperators →
authentication**. Wait for Available `True`, Progressing `False`, Degraded `False`. This can
take a few minutes.

**Terminal** alternative: run `oc get clusteroperator authentication` until it settles.

![Settled authentication conditions; dates are hidden](images/04-authentication-ready.png)

## 4. First login

1. **Console.** Open a fresh, separate browser session (a private window or another profile).
   On the login page choose the provider from your sheet and sign in as the test user.
   **Expected:** login works. The user cannot open **Compute → Nodes** yet.
2. In your administrator session open **User Management → Users**. The test user now exists.
   The login created it; do not create users by hand.

   ![Test user and its provider identity created by the first login](images/05-user-created.png)

**Terminal** check:

```bash
oc get user "$TEST_USER"
oc get identity "$PROVIDER_NAME:$TEST_USER"
```

## 5. Grant cluster-admin

`cluster-admin` gives the user full control of the cluster. Grant it only to the agreed user.

**Console.** In your administrator session:

1. Open **User Management → RoleBindings → Create binding**.
2. Choose **Cluster-wide role binding**.
3. Enter the binding name from your sheet, role **cluster-admin**, subject **User** and the
   test user's name.
4. Click **Create**.

![Example cluster-wide binding with the cluster-admin role and a User subject, before clicking Create](images/02-cluster-admin-binding-form.png)

![The newly created cluster-wide binding](images/06-admin-binding-created.png)

**Terminal** alternative to the console form, from this case's folder in the repository:

```bash
[ -d "$RUN_DIR" ] && sed -e "s/REPLACE_BINDING_NAME/$BINDING_NAME/" -e "s/REPLACE_USER/$TEST_USER/" templates/cluster-admin-binding.template.yaml > "$RUN_DIR/binding.yaml" &&
  oc create -f "$RUN_DIR/binding.yaml"
```

**Expected:** `clusterrolebinding.rbac.authorization.k8s.io/<name> created`, or the console
opens the new binding's page. If creation fails for any reason, including *already exists*,
stop. Do not use, record or later delete a binding this step did not create.

**Terminal**, only after a successful create: check that the binding gives `cluster-admin` to
the test user and nobody else, then save its UID for cleanup.

```bash
oc get clusterrolebinding "$BINDING_NAME" -o jsonpath='{.roleRef.kind}/{.roleRef.name} {range .subjects[*]}{.kind}/{.name};{end}{"\n"}'
```

**Expected:** exactly `ClusterRole/cluster-admin User/<test user>;` with one subject. If it
shows another role or any other subject, stop: do not save the UID or use the binding.
Otherwise save the UID:

```bash
[ -d "$RUN_DIR" ] && oc get clusterrolebinding "$BINDING_NAME" -o jsonpath='{.metadata.uid}{"\n"}' | tee "$RUN_DIR/binding.uid"
```

Other cluster-admin bindings are not touched.

**Console.** In the test user's window, reload the page. **Expected:** **Compute → Nodes** now
opens. A menu entry alone does not prove access; the page must open.

## 6. Change the password

**Terminal.** Read the current file. This time the test user must be in it:

```bash
[ -d "$RUN_DIR" ] && oc get secret "$SECRET_NAME" -n openshift-config -o json > "$RUN_DIR/rotate-before.json" &&
  jq -r '.data.htpasswd // ""' "$RUN_DIR/rotate-before.json" | base64 --decode > "$RUN_DIR/rotate.htpasswd" &&
  cut -d: -f1 "$RUN_DIR/rotate.htpasswd" && cut -d: -f1 "$RUN_DIR/rotate.htpasswd" | grep -cxF "$TEST_USER"
```

**Expected:** the user names, then `1`. Otherwise stop.

Set the new password (no `-c`) and check the names are unchanged:

```bash
[ -s "$RUN_DIR/rotate.htpasswd" ] && htpasswd -B "$RUN_DIR/rotate.htpasswd" "$TEST_USER" && cut -d: -f1 "$RUN_DIR/rotate.htpasswd"
```

If nothing printed, stop. Then save:

```bash
jq --rawfile f "$RUN_DIR/rotate.htpasswd" '.data.htpasswd = ($f | @base64)' "$RUN_DIR/rotate-before.json" > "$RUN_DIR/rotate-after.json" &&
  oc replace -f "$RUN_DIR/rotate-after.json"
```

If `oc replace` says *the object has been modified*, nothing changed: start this step again.
Then wait for authentication to settle as in step 3.

**Console.**

1. Sign out the test user and close that private window. Open a fresh private
   window and sign in with the **new** password. **Expected:** it works.
2. Close it and open another fresh private window. Try the **old** password once.
   **Expected:** it is refused (for example,
   *Invalid login or password. Please try again.*).
3. Confirm your administrator session and the other logins still work.

A password change does **not** end sessions or tokens that already exist. Ending them is a
separate step (sign-out, or deleting the user's tokens in step 7).

## 7. Clean up

Remove only what this test created. If the sheet says **keep the account**, skip to the end
of this section.

**Terminal.** Remove the binding first, but only if it is still the one this test created:

```bash
CUR=$(oc get clusterrolebinding "$BINDING_NAME" -o jsonpath='{.metadata.uid}')
if [ -n "$CUR" ] && [ "$CUR" = "$(cut -d' ' -f1 "$RUN_DIR/binding.uid")" ]; then oc delete clusterrolebinding "$BINDING_NAME"; else echo "STOP: not the binding this test created. Leave it."; fi
```

### Create path

1. **Console.** On the **OAuth** page, in the **Identity providers** table, open **Actions**
   (three dots) on **only this provider's row** → **Remove identity provider** → **Remove**.
   Names in the table are not links. Check that the remaining list matches the inventory.

   ![Remove only the dedicated demonstration provider](images/08-remove-provider-confirmation.png)

2. Wait for authentication to settle (step 3).
3. **Terminal.** Removing the provider does not delete its Secret. Delete it, but only if it is
   the one saved in step 2:

   ```bash
   CUR=$(oc get secret "$SECRET_NAME" -n openshift-config -o jsonpath='{.metadata.uid}')
   if [ -n "$CUR" ] && [ "$CUR" = "$(cut -d' ' -f1 "$RUN_DIR/secret.uid")" ]; then oc delete secret "$SECRET_NAME" -n openshift-config; else echo "STOP: not the Secret this test created. Leave it."; fi
   ```

4. Continue with **Remove the account** below.

### Reuse path

Remove only the test user's line. The provider, its Secret and the other users stay.

**Terminal.** Read the file. The test user must be listed, and at least one other user must
remain after it is removed:

```bash
[ -d "$RUN_DIR" ] && oc get secret "$SECRET_NAME" -n openshift-config -o json > "$RUN_DIR/remove-before.json" &&
  jq -r '.data.htpasswd // ""' "$RUN_DIR/remove-before.json" | base64 --decode > "$RUN_DIR/remove.htpasswd" &&
  { cut -d: -f1 "$RUN_DIR/remove.htpasswd" | grep -cxF "$TEST_USER"; cut -d: -f1 "$RUN_DIR/remove.htpasswd" | grep -cvxF "$TEST_USER"; }
```

**Expected:** `1`, then `1` or more. If the second count is `0`, stop and ask the provider's
owner: never remove a provider's last user. Then remove the line and save:

```bash
[ -s "$RUN_DIR/remove.htpasswd" ] && htpasswd -D "$RUN_DIR/remove.htpasswd" "$TEST_USER" && cut -d: -f1 "$RUN_DIR/remove.htpasswd"
```

**Expected:** the names list no longer shows the test user. If nothing printed, stop. Then save:

```bash
jq --rawfile f "$RUN_DIR/remove.htpasswd" '.data.htpasswd = ($f | @base64)' "$RUN_DIR/remove-before.json" > "$RUN_DIR/remove-after.json" &&
  oc replace -f "$RUN_DIR/remove-after.json"
```

**Expected:** `secret/<name> replaced`. On *the object has been modified*,
start this step again. Wait for authentication to settle (step 3).

### Remove the account (both paths)

**Terminal:**

```bash
oc delete user "$TEST_USER"
oc delete identity "$PROVIDER_NAME:$TEST_USER"
oc delete oauthaccesstokens --field-selector=userName="$TEST_USER"
[ -d "$RUN_DIR" ] && rm -r "$RUN_DIR"
```

The last line deletes the run folder with the password file and the saved copies. Deleting a
file does not guarantee secure erasure on an SSD.

**Console.** Filter **User Management → Users** by the exact test user name. **Expected:**
**No Users found**. Check that the provider list matches the inventory.

![Users filtered to poc-user after cleanup: No Users found](images/10-user-cleanup.png)

### Keep-account path

Keep the provider, Secret, user and binding. Delete only the run folder
(`rm -r "$RUN_DIR"`). Record the owner and a review date on the sheet. The account stays a full
cluster administrator until someone removes the binding.

## Stop and ask the administrator if

- a certificate warning appears,
- an existing user can no longer log in,
- the authentication ClusterOperator stays Progressing or Degraded,
- the provider list changed unexpectedly,
- a command prints `STOP`, or a check gives a different count.

Do not retry in a loop. Record what happened and stop; do not mark the test Pass. The
administrator's [reference](ADMIN-GUIDE.md#troubleshooting) covers recovery.
