# Recording outline

> Follow the [walkthrough](RUNBOOK.md). Show no passwords, hash files, Secret data, tokens or
> account names. Do not type a password on camera. **Stop recording before the file upload
> (the form shows the hashes) and resume on the OAuth details page.**

| Scene | Show | Explain |
| --- | --- | --- |
| 1. Introduce | OAuth page listing existing providers | "We add one local login and keep everything else." |
| 2. Provider | Add HTPasswd up to the name field, pause for the upload, resume on the result; or the reused Secret (content hidden) | "The file holds password hashes; the user API does not." |
| 3. Settle | authentication ClusterOperator settles | "The login service restarts with the change." |
| 4. First login | Private window logs in; Users page lists the new user | "Login creates the user." |
| 5. Grant | Cluster-wide role binding to cluster-admin | "Full cluster control, so it is deliberate." |
| 6. Prove | Compute → Nodes opens for the new user after reload | "Same console, more rights." |
| 7. Rotate | New password works, old refused | "Existing sessions are not ended by this." |
| 8. Finish | Binding removed, then Actions → Remove identity provider on only this row; or keep-account | "Only what we created is removed." |
