# Results: HTPasswd login

> Record your own run here. Use **Pass**, **Fail**, **Blocked**, **Not run** or
> **Not available**. Never write a password, hash, token or Secret content here.
> Keep completed copies private.

Date: ____   Customer: ____   Administrator: ____   Approved by: ____
OpenShift version: ____   Console URL: ____
Path: Create / Reuse / Owner   End state: Cleanup / Keep-account

## Inventory (names only)

| Item | Value |
| --- | --- |
| Existing providers before (name, type) | ____ |
| HTPasswd Secret reused or created / managed by (nobody, GitOps, external) | ____ |
| Test user / provider name / Secret name / mappingMethod | ____ / ____ / ____ / claim |
| Binding name (UID saved in the private run folder) | ____ |
| Second administrator session confirmed | ____ |

## Steps

| Step | Result | Time UTC | Notes |
| --- | --- | --- | --- |
| Readiness check passed (name unused in users, identities and password files; binding name free) | | | |
| Test user added; other users' names unchanged | | | |
| Authentication settled | | | |
| First login; User and Identity created by the login | | | |
| `cluster-admin` binding created by this test; **Compute → Nodes** opens | | | |
| Password changed; new password works | | | |
| Old password refused | | | |
| Existing users still log in | | | |
| Existing sessions after the change (not ended automatically) | | | |
| Cleanup done (binding and Secret removed only after their UIDs matched) or keep-account recorded | | | |

Unexpected changes to existing providers, users or Secrets: ____
Console labels that differed from the walkthrough: ____
