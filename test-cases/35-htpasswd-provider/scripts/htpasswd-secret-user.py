#!/usr/bin/env python3
"""Add, rotate or remove one user in an OpenShift HTPasswd Secret.

Usage: htpasswd-secret-user.py SECRET_NAME USER_NAME add|rotate|remove

Requires python3 (stdlib only), oc (already logged in) and htpasswd (Apache utils).
"""
import base64
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

NAMESPACE = "openshift-config"
KEY = "htpasswd"
MODES = ("add", "rotate", "remove")
SECRET_RE = re.compile(r"^[a-z0-9]([-a-z0-9.]{0,251}[a-z0-9])?$")
USER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@+-]{0,127}$")
MANAGED_MARKERS = ("argocd.argoproj.io", "fluxcd.io", "external-secrets.io")

HELP = """Usage: htpasswd-secret-user.py SECRET_NAME USER_NAME add|rotate|remove

Changes ONE user's line in the 'htpasswd' key of a Secret in namespace
openshift-config. Other users, other keys and all metadata are kept. The Secret
is replaced with the resourceVersion it was fetched with, so a concurrent edit
makes the update fail instead of being overwritten.

  add     USER_NAME must not exist yet
  rotate  USER_NAME must exist; the new password replaces the old one
  remove  USER_NAME must exist (the last remaining user is not removed)

htpasswd prompts for the password; it is never taken from arguments or the
environment. Secrets owned by Argo CD, Flux or External Secrets are refused:
edit the owning source instead. The OAuth resource, role bindings, tokens and
the oc context are not touched. Existing tokens stay valid after a rotation.
"""


class Fail(Exception):
    pass


def run(cmd, capture_err=True):
    try:
        return subprocess.run(
            cmd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if capture_err else None)
    except OSError:
        raise Fail("could not run " + cmd[0])


def managed_source(secret):
    meta = secret.get("metadata") or {}
    for ref in meta.get("ownerReferences") or []:
        if ref.get("kind") == "ExternalSecret" or "external-secrets.io" in str(ref.get("apiVersion", "")):
            return True
    for field in ("labels", "annotations"):
        for key in (meta.get(field) or {}):
            if any(m in key for m in MANAGED_MARKERS):
                return True
    return False


def parse_lines(raw):
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def user_of(line):
    return line.split(b":", 1)[0]


def validate(argv):
    if len(argv) != 3 or any(a.startswith("-") for a in argv):
        raise Fail("expected exactly SECRET_NAME USER_NAME add|rotate|remove (see --help)")
    secret, user, mode = argv
    if mode not in MODES:
        raise Fail("action must be add, rotate or remove")
    if not SECRET_RE.match(secret):
        raise Fail("invalid Secret name")
    if not USER_RE.match(user):
        raise Fail("unsafe user name: use letters, digits and . _ @ + - only, starting with a letter or digit")
    return secret, user.encode(), mode


def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(HELP, end="")
        return 0
    secret_name, user, mode = validate(argv)
    for tool in ("oc", "htpasswd"):
        if shutil.which(tool) is None:
            raise Fail(tool + " not found in PATH")

    got = run(["oc", "get", "secret", secret_name, "-n", NAMESPACE, "-o", "json"])
    if got.returncode != 0:
        first = got.stderr.decode(errors="replace").strip().splitlines()[:1]
        raise Fail("could not read the Secret: " + (first[0] if first else "oc get failed"))
    try:
        secret = json.loads(got.stdout)
        old_raw = base64.b64decode(secret["data"][KEY], validate=True)
    except (ValueError, KeyError, TypeError):
        raise Fail("Secret has no valid '%s' key" % KEY)
    if secret.get("kind") != "Secret" or not (secret.get("metadata") or {}).get("resourceVersion"):
        raise Fail("unexpected response from oc get")
    if managed_source(secret):
        raise Fail("this Secret is managed by Argo CD, Flux or External Secrets: "
                   "change the owning source instead; a live edit would be reverted")

    old = parse_lines(old_raw)
    exists = any(user_of(l) == user for l in old)
    if mode == "add" and exists:
        raise Fail("user already exists; use rotate")
    if mode in ("rotate", "remove") and not exists:
        raise Fail("user does not exist; use add")
    if mode == "remove" and len(old) == 1:
        raise Fail("refusing to remove the last user; change the OAuth provider in the console instead")

    old_signal = signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    workdir = tempfile.mkdtemp(prefix="htpasswd-user-")
    try:
        os.chmod(workdir, 0o700)
        path = os.path.join(workdir, "users.htpasswd")
        write_private(path, old_raw)

        flag = "-D" if mode == "remove" else "-B"
        if run(["htpasswd", flag, path, user.decode()], capture_err=False).returncode != 0:
            raise Fail("htpasswd failed; the Secret was not changed")

        with open(path, "rb") as fh:
            new_raw = fh.read()
        new = parse_lines(new_raw)
        others_before = [l for l in old if user_of(l) != user]
        others_after = [l for l in new if user_of(l) != user]
        mine = [l for l in new if user_of(l) == user]
        old_mine = [l for l in old if user_of(l) == user]
        ok = others_before == others_after
        if mode == "remove":
            ok = ok and not mine
        else:
            ok = ok and len(mine) == 1 and mine != old_mine
        if not ok:
            raise Fail("htpasswd result was not as expected; the Secret was not changed")
        if new_raw and not new_raw.endswith(b"\n"):
            new_raw += b"\n"

        secret["data"][KEY] = base64.b64encode(new_raw).decode()
        payload = os.path.join(workdir, "secret.json")
        write_private(payload, json.dumps(secret).encode())

        res = run(["oc", "replace", "-n", NAMESPACE, "-f", payload])
        if res.returncode != 0:
            err = res.stderr.decode(errors="replace")
            if "Conflict" in err or "has been modified" in err:
                raise Fail("the Secret changed while you worked (conflict); nothing was overwritten. Re-run.")
            raise Fail("oc replace failed; the Secret may be unchanged (details withheld). Check access, then re-run.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        signal.signal(signal.SIGTERM, old_signal)

    verb = {"add": "added", "rotate": "rotated", "remove": "removed"}[mode]
    print("User '%s' %s in Secret %s/%s." % (user.decode(), verb, NAMESPACE, secret_name))
    print("Wait for: oc get clusteroperator authentication  (Available, not Progressing).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print("error: %s" % exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("error: interrupted; the Secret is unchanged unless oc replace had already finished", file=sys.stderr)
        sys.exit(130)
