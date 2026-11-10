import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1]
ARC_KEY = "arc_runner_scale_sets:\n  - arc-demo-ci\n"
JOB = "jobs:\n  t:\n{runs_on}    steps:\n      - run: true\n"
LEGACY = "    runs-on:\n      - self-hosted\n"


class ContractCheckerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name) / "repo"
        shutil.copytree(SRC, self.root, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__"))
        # Replace checked-in workflows with minimal legacy ones so each test controls runs-on.
        # Fixtures start from a legacy contract: drop the template's own ARC entry.
        text = self.contract().read_text()
        self.contract().write_text(text.split("arc_runner_scale_sets:")[0])
        for wf in (self.root / ".github/workflows").iterdir():
            wf.write_text("on: push\n" + JOB.format(runs_on=LEGACY))

    def contract(self):
        return self.root / ".repo-contract.yml"

    def configure(self, extra=ARC_KEY):
        self.contract().write_text(self.contract().read_text() + extra)

    def workflow(self, runs_on):
        (self.root / ".github/workflows/extra.yml").write_text("on: push\n" + JOB.format(runs_on=runs_on))

    def run_check(self):
        proc = subprocess.run(
            [sys.executable, str(self.root / "scripts/check_repository_contract.py")],
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def assert_fails(self, runs_on, fragment):
        self.workflow(runs_on)
        code, out = self.run_check()
        self.assertNotEqual(code, 0, out)
        self.assertIn(fragment, out)

    def test_checked_in_template_passes_public_checker(self):
        proc = subprocess.run(
            [sys.executable, str(SRC / "scripts/check_repository_contract.py")], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_fixture_without_arc_key_passes_legacy(self):
        self.assertNotIn("arc_runner_scale_sets", self.contract().read_text())
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_listed_name_only_scalar_passes(self):
        self.configure()
        self.workflow("    runs-on: arc-demo-ci\n")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_listed_name_with_trailing_comment_passes(self):
        self.configure()
        self.workflow("    runs-on: arc-demo-ci # pool\n")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_unset_key_rejects_arc_name_as_legacy(self):
        self.assert_fails("    runs-on: arc-demo-ci\n", "must include self-hosted")

    def test_unlisted_name_fails(self):
        self.configure()
        self.assert_fails("    runs-on: arc-other-ci\n", "sole name-only")

    def test_quoted_name_fails(self):
        self.configure()
        self.assert_fails('    runs-on: "arc-demo-ci"\n', "sole name-only")

    def test_mixed_flow_list_fails(self):
        self.configure()
        self.assert_fails("    runs-on: [self-hosted, arc-demo-ci]\n", "sole name-only")

    def test_mixed_block_list_fails(self):
        self.configure()
        self.assert_fails("    runs-on:\n      - self-hosted\n      - arc-demo-ci\n", "sole name-only")

    def test_unlisted_arc_name_in_legacy_list_fails_when_configured(self):
        self.configure()
        self.assert_fails("    runs-on: [self-hosted, arc-other-ci]\n", "sole name-only")

    def test_hosted_label_mixed_with_arc_fails(self):
        self.configure()
        self.assert_fails("    runs-on: [arc-demo-ci, ubuntu-latest]\n", "forbidden")

    def test_expression_bypass_fails(self):
        self.configure()
        self.assert_fails("    runs-on: ${{ inputs.runner }}\n", "expression-built")
        self.assert_fails("    runs-on: arc-demo-ci ${{ github.head_ref }}\n", "expression-built")

    def test_expression_with_literal_self_hosted_fallback_fails(self):
        self.configure()
        self.assert_fails("    runs-on: ${{ inputs.runner || 'self-hosted' }}\n", "expression-built")
        self.assert_fails("    runs-on: [self-hosted, '${{ inputs.runner }}']\n", "expression-built")
        self.assert_fails("    runs-on:\n      - self-hosted\n      - ${{ inputs.runner }}\n", "expression-built")

    def test_expression_with_self_hosted_unchanged_when_key_unset(self):
        self.workflow("    runs-on: ${{ inputs.runner || 'self-hosted' }}\n")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_block_list_name_alone_fails(self):
        self.configure()
        self.assert_fails("    runs-on:\n      - arc-demo-ci\n", "sole name-only")

    def test_legacy_unchanged_with_and_without_key(self):
        for configured in (False, True):
            with self.subTest(configured=configured):
                if configured:
                    self.configure()
                self.workflow("    runs-on: [self-hosted, Linux]\n")
                self.assertEqual(self.run_check()[0], 0)
                self.workflow("    runs-on: some-label\n")
                self.assertNotEqual(self.run_check()[0], 0)

    def test_invalid_scale_set_names_fail(self):
        base = self.contract().read_text()
        for bad in ("ARC-demo", "arc_demo", "demo", "arc-", "arc--x"):
            with self.subTest(name=bad):
                self.contract().write_text(base + f"arc_runner_scale_sets:\n  - {bad}\n")
                code, out = self.run_check()
                self.assertNotEqual(code, 0, out)
                self.assertIn("invalid ARC runner scale set name", out)

    def test_duplicate_scale_sets_fail(self):
        self.configure("arc_runner_scale_sets:\n  - arc-a\n  - arc-a\n")
        code, out = self.run_check()
        self.assertNotEqual(code, 0, out)
        self.assertIn("duplicates", out)


if __name__ == "__main__":
    unittest.main()
