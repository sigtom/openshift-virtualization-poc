"""Mocked-command tests for htpasswd-secret-user.py. No cluster is contacted.

Run: python3 -m unittest -v test_htpasswd_secret_user   (from this directory)

Fake `oc` and `htpasswd` executables are put first on PATH. The fake oc keeps a
"server" copy of the Secret and rejects a replace whose resourceVersion differs,
like the real API server. The fake htpasswd edits the file the way the real tool
does (-B sets or appends a line, -D deletes it) and never sees a password.
"""
import base64
import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "htpasswd-secret-user.py")

FAKE_OC = r"""#!/usr/bin/env python3
import json, os, sys
d = os.environ["FAKE_DIR"]
a = sys.argv[1:]
def load(n):
    with open(os.path.join(d, n)) as f:
        return json.load(f)
if a[:2] == ["get", "secret"]:
    if a[2:] != [a[2], "-n", "openshift-config", "-o", "json"]:
        sys.exit(2)
    sys.stdout.write(json.dumps(load("server.json")))
    # a concurrent writer bumps the version right after we read
    if os.path.exists(os.path.join(d, "bump")):
        s = load("server.json"); s["metadata"]["resourceVersion"] = "999"
        json.dump(s, open(os.path.join(d, "server.json"), "w"))
elif a[0] == "replace":
    assert a[1:3] == ["-n", "openshift-config"] and a[3] == "-f"
    path = a[4]
    mode = os.stat(path).st_mode & 0o777
    sent = json.load(open(path))
    open(os.path.join(d, "replace-mode"), "w").write(oct(mode))
    open(os.path.join(d, "replace-dir"), "w").write(os.path.dirname(path))
    if sent["metadata"]["resourceVersion"] != load("server.json")["metadata"]["resourceVersion"]:
        sys.stderr.write("Error: Operation cannot be fulfilled: Conflict\n")
        sys.exit(1)
    json.dump(sent, open(os.path.join(d, "replaced.json"), "w"))
else:
    sys.exit(2)
"""

FAKE_HTPASSWD = r"""#!/usr/bin/env python3
import os, sys
a = sys.argv[1:]
with open(os.path.join(os.environ["FAKE_DIR"], "htpasswd-argv"), "w") as f:
    f.write("\n".join(a))
assert a[0] in ("-B", "-D") and len(a) == 3, a   # never -b, never a password argument
flag, path, user = a
if os.environ.get("FAKE_HTPASSWD_FAIL"):
    open(path, "w").write("garbage-partial")
    sys.exit(1)
lines = [l for l in open(path).read().split("\n") if l]
if flag == "-D":
    lines = [l for l in lines if l.split(":")[0] != user]
else:
    new = user + ":$2y$05$NEWHASHFORTEST"
    for i, l in enumerate(lines):
        if l.split(":")[0] == user:
            lines[i] = new
            break
    else:
        lines.append(new)
open(path, "w").write("\n".join(lines) + "\n")
"""

ALICE = "alice:$2y$05$ALICEOLDHASH"
BOB = "bob:$2y$05$BOBHASH"
CAROL = "carol:$2y$05$CAROLHASH"


def b64(text):
    return base64.b64encode(text.encode()).decode()


def make_secret(lines=(ALICE, BOB), **meta):
    metadata = {"name": "htpass-test", "namespace": "openshift-config", "resourceVersion": "42",
                "uid": "u-1", "labels": {"team": "ops"}, "annotations": {"note": "keep me"}}
    metadata.update(meta)
    return {"apiVersion": "v1", "kind": "Secret", "type": "Opaque", "metadata": metadata,
            "data": {"htpasswd": b64("\n".join(lines) + "\n"), "extra": b64("other-key-value")}}


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fake = os.path.join(self.tmp.name, "state")
        self.bin = os.path.join(self.tmp.name, "bin")
        os.mkdir(self.fake)
        os.mkdir(self.bin)
        for name, body in (("oc", FAKE_OC), ("htpasswd", FAKE_HTPASSWD)):
            p = os.path.join(self.bin, name)
            with open(p, "w") as f:
                f.write(body)
            os.chmod(p, 0o755)
        self.private_tmp = os.path.join(self.tmp.name, "tmpdir")
        os.mkdir(self.private_tmp)

    def serve(self, secret):
        with open(os.path.join(self.fake, "server.json"), "w") as f:
            json.dump(secret, f)

    def run_helper(self, *args, env_extra=None, path=None):
        env = {"PATH": path if path is not None else self.bin + os.pathsep + "/usr/bin:/bin",
               "FAKE_DIR": self.fake, "TMPDIR": self.private_tmp, "HOME": self.tmp.name}
        env.update(env_extra or {})
        return subprocess.run([sys.executable, HELPER, *args], capture_output=True, text=True, env=env)

    def replaced(self):
        p = os.path.join(self.fake, "replaced.json")
        if not os.path.exists(p):
            return None
        with open(p) as f:
            return json.load(f)

    def assert_not_mutated(self):
        self.assertIsNone(self.replaced())

    def assert_clean(self, result):
        for leaked in ("$2y$", "HASH", "other-key-value", b64(ALICE)):
            self.assertNotIn(leaked, result.stdout + result.stderr)
        self.assertEqual(os.listdir(self.private_tmp), [])

    def test_add_keeps_other_users_keys_and_metadata(self):
        original = make_secret()
        self.serve(original)
        r = self.run_helper("htpass-test", "carol", "add")
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = copy.deepcopy(original)
        expected["data"]["htpasswd"] = b64("\n".join([ALICE, BOB, "carol:$2y$05$NEWHASHFORTEST"]) + "\n")
        self.assertEqual(self.replaced(), expected)  # same resourceVersion, labels, extra key
        self.assert_clean(r)

    def test_rotate_changes_only_that_user(self):
        original = make_secret((ALICE, BOB, CAROL))
        self.serve(original)
        r = self.run_helper("htpass-test", "bob", "rotate")
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = copy.deepcopy(original)
        expected["data"]["htpasswd"] = b64("\n".join([ALICE, "bob:$2y$05$NEWHASHFORTEST", CAROL]) + "\n")
        self.assertEqual(self.replaced(), expected)
        with open(os.path.join(self.fake, "htpasswd-argv")) as f:
            self.assertEqual(f.read().split("\n")[0], "-B")
        self.assert_clean(r)

    def test_remove_keeps_everyone_else(self):
        original = make_secret((ALICE, BOB, CAROL))
        self.serve(original)
        r = self.run_helper("htpass-test", "bob", "remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = copy.deepcopy(original)
        expected["data"]["htpasswd"] = b64("\n".join([ALICE, CAROL]) + "\n")
        self.assertEqual(self.replaced(), expected)

    def test_private_permissions_and_cleanup_on_success(self):
        self.serve(make_secret())
        r = self.run_helper("htpass-test", "carol", "add")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.fake, "replace-mode")) as f:
            self.assertEqual(f.read(), "0o600")
        self.assertEqual(os.listdir(self.private_tmp), [])

    def test_stale_version_conflict_does_not_overwrite(self):
        self.serve(make_secret())
        open(os.path.join(self.fake, "bump"), "w").close()
        r = self.run_helper("htpass-test", "carol", "add")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("conflict", r.stderr.lower())
        self.assert_not_mutated()
        self.assert_clean(r)

    def test_managed_sources_are_refused(self):
        cases = {
            "external owner": {"ownerReferences": [{"apiVersion": "external-secrets.io/v1beta1",
                                                    "kind": "ExternalSecret", "name": "x", "uid": "u"}]},
            "argo label": {"labels": {"argocd.argoproj.io/instance": "app"}},
            "argo annotation": {"annotations": {"argocd.argoproj.io/tracking-id": "a:b"}},
            "flux label": {"labels": {"kustomize.toolkit.fluxcd.io/name": "flux-system"}},
        }
        for name, meta in cases.items():
            with self.subTest(name):
                self.serve(make_secret(**meta))
                r = self.run_helper("htpass-test", "carol", "add")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("owning source", r.stderr)
                self.assert_not_mutated()
                self.assertFalse(os.path.exists(os.path.join(self.fake, "htpasswd-argv")))

    def test_failed_htpasswd_does_not_mutate(self):
        self.serve(make_secret())
        r = self.run_helper("htpass-test", "bob", "rotate", env_extra={"FAKE_HTPASSWD_FAIL": "1"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("htpasswd failed", r.stderr)
        self.assert_not_mutated()
        self.assert_clean(r)

    def test_existing_state_rules(self):
        self.serve(make_secret())
        for user, action in (("alice", "add"), ("zed", "rotate"), ("zed", "remove")):
            r = self.run_helper("htpass-test", user, action)
            self.assertNotEqual(r.returncode, 0, (user, action))
        self.assert_not_mutated()

    def test_last_user_not_removed(self):
        self.serve(make_secret((ALICE,)))
        r = self.run_helper("htpass-test", "alice", "remove")
        self.assertNotEqual(r.returncode, 0)
        self.assert_not_mutated()

    def test_unsafe_and_option_like_inputs_rejected_before_any_call(self):
        self.serve(make_secret())
        bad = [("htpass-test", "-b", "add"), ("-n", "carol", "add"), ("htpass-test", "a:b", "add"),
               ("htpass-test", "a/b", "add"), ("htpass-test", "a%b", "add"), ("htpass-test", "a b", "add"),
               ("htpass-test", "ca\nrol", "add"), ("Bad_Name", "carol", "add"),
               ("htpass-test", "carol", "--delete"), ("htpass-test", "carol"),
               ("htpass-test", "carol", "add", "extra")]
        for args in bad:
            with self.subTest(args=args):
                r = self.run_helper(*args)
                self.assertNotEqual(r.returncode, 0)
        self.assert_not_mutated()
        self.assertFalse(os.path.exists(os.path.join(self.fake, "htpasswd-argv")))

    def test_missing_prerequisite(self):
        os.remove(os.path.join(self.bin, "htpasswd"))
        self.serve(make_secret())
        r = self.run_helper("htpass-test", "carol", "add", path=self.bin)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("htpasswd not found", r.stderr)
        self.assert_not_mutated()

    def test_help(self):
        r = self.run_helper("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("add|rotate|remove", r.stdout)


if __name__ == "__main__":
    unittest.main()
