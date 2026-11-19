import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ai_totem.cli import write_outputs
from ai_totem.schemas import ValidationError
from test_support import ROOT


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def cli(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "ai_totem.cli", *args],
            cwd=self.cwd,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=30,
        )

    def assert_ok(self, *args):
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def prepare(self):
        self.assert_ok("init")
        self.assert_ok("challenge")

    def test_complete_workflow_and_both_reports(self):
        self.prepare()
        result = self.assert_ok(
            "evaluate", "--responses", str(ROOT / "examples/responses.synthetic.json")
        )
        self.assertNotIn("Paper Kite", result.stdout)
        self.assert_ok("report")
        data = json.loads((self.cwd / ".totem/report.json").read_text(encoding="utf-8"))
        self.assertEqual(data["summary"]["pass"], 6)
        self.assertTrue((self.cwd / ".totem/report.md").exists())
        self.assert_ok(
            "report",
            "--previous",
            ".totem/report.json",
            "--markdown",
            ".totem/paired.md",
            "--json",
            ".totem/paired.json",
        )

    def test_help_and_version(self):
        self.assertIn("0.1.0", self.assert_ok("--version").stdout)
        self.assertIn("No API", self.assert_ok("--help").stdout)
        for command in ("init", "challenge", "evaluate", "report"):
            self.assertIn("usage:", self.assert_ok(command, "--help").stdout)

    def test_overwrite_refused(self):
        self.assert_ok("init")
        path = self.cwd / ".totem/baseline.json"
        before = path.read_bytes()
        self.assertEqual(self.cli("init").returncode, 2)
        self.assertEqual(path.read_bytes(), before)

    def test_no_partial_multi_output_when_destination_exists(self):
        self.assert_ok("init")
        (self.cwd / "exists.json").write_text("keep", encoding="utf-8")
        result = self.cli("challenge", "--prompts-output", "exists.json")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.cwd / ".totem/challenges.json").exists())

    def test_distinct_paths_required(self):
        self.assert_ok("init")
        self.assertEqual(
            self.cli(
                "challenge", "--output", "same", "--prompts-output", "same"
            ).returncode,
            2,
        )
        self.assertFalse((self.cwd / "same").exists())

    def test_invalid_cli_inputs_are_clear_and_private(self):
        secret = "SYNTHETIC_PRIVATE_MARKER"
        (self.cwd / "bad.json").write_text('{"' + secret, encoding="utf-8")
        for args in (
            ("no-such-command",),
            ("evaluate",),
            ("init", "--template", "missing.json"),
            ("init", "--template", "bad.json"),
            ("init", "--id", "../escape"),
            ("report", "--evaluation", "bad.json"),
        ):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(secret, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_no_traceback(self):
        (self.cwd / "bad.json").write_bytes(b"\xff")
        result = self.cli("init", "--template", "bad.json")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_response_not_filled_by_cli(self):
        self.prepare()
        (self.cwd / "answers.json").write_text(
            json.dumps(
                {"schema_version": 1, "session_id": "no-answers", "responses": []}
            ),
            encoding="utf-8",
        )
        self.assert_ok("evaluate", "--responses", "answers.json")
        e = json.loads(
            (self.cwd / ".totem/evaluation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(e["summary"]["indeterminate"], 6)

    def test_failed_checks_do_not_mean_cli_error(self):
        self.prepare()
        answers = json.loads(
            (ROOT / "examples/responses.synthetic.json").read_text(encoding="utf-8")
        )
        answers["responses"][0]["structured"]["project_name"] = "wrong"
        (self.cwd / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
        self.assert_ok("evaluate", "--responses", "answers.json")
        e = json.loads(
            (self.cwd / ".totem/evaluation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(e["summary"]["fail"], 1)

    def test_io_failure_rolls_back_created_files(self):
        blocker = self.cwd / "blocker"
        blocker.write_text("file not directory", encoding="utf-8")
        first = self.cwd / "first.json"
        with self.assertRaises(OSError):
            write_outputs([(first, "data"), (blocker / "second.json", "data")])
        self.assertFalse(first.exists())

    def test_bad_json_shape_fails_gracefully(self):
        self.assert_ok("init")
        for shape in ([], {"schema_version": 1}, None):
            (self.cwd / "shape.json").write_text(json.dumps(shape), encoding="utf-8")
            result = self.cli(
                "challenge", "--challenge-set", "shape.json", "--include-ritual"
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
