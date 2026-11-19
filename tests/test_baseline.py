from copy import deepcopy
from importlib.resources import files
import tempfile
from pathlib import Path

from ai_totem.baseline import create_baseline
from ai_totem.schemas import ValidationError, read_json, validate_baseline
from test_support import Fixture, ROOT


class BaselineTests(Fixture):
    def test_synthetic_baseline_valid(self):
        self.assertIs(validate_baseline(self.baseline), self.baseline)

    def test_creation_does_not_mutate_template(self):
        before = deepcopy(self.baseline)
        result = create_baseline(self.baseline, "new-id")
        self.assertEqual(result["id"], "new-id")
        self.assertEqual(result["version"], before["version"])
        self.assertEqual(self.baseline, before)
        self.assertNotEqual(result["created_at"], before["created_at"])

    def test_packaged_default_template_available(self):
        self.assertEqual(create_baseline()["facts"], self.baseline["facts"])
        for name in ("baseline.example.json", "challenge-set.example.json"):
            self.assertEqual(
                files("ai_totem").joinpath("data", name).read_bytes(),
                (ROOT / "templates" / name).read_bytes(),
            )

    def test_invalid_baselines(self):
        mutations = [
            lambda b: b.pop("id"),
            lambda b: b.update(extra=True),
            lambda b: b.update(schema_version=True),
            lambda b: b.update(schema_version=2),
            lambda b: b.update(id="../escape"),
            lambda b: b.update(created_at="2026-01-01"),
            lambda b: b.update(created_at="2026-01-01T00:00:00"),
            lambda b: b["facts"][0].update(approved=False),
            lambda b: b["facts"][0].update(approved="true"),
            lambda b: b["style_examples"].update(preferred="not an array"),
            lambda b: b.update(preferences=[3]),
            lambda b: b["ritual"].update(trigger=""),
            lambda b: b.update(version=""),
            lambda b: b.update(reference_questions=[{}]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)):
                b = deepcopy(self.baseline)
                mutation(b)
                with self.assertRaises(ValidationError):
                    validate_baseline(b)

    def test_contradictory_duplicate_fact(self):
        self.baseline["facts"].append(
            {"id": "project_name", "value": "Another Project", "approved": True}
        )
        with self.assertRaises(ValidationError):
            validate_baseline(self.baseline)

    def test_duplicate_reference_questions(self):
        self.baseline["reference_questions"] *= 2
        with self.assertRaises(ValidationError):
            validate_baseline(self.baseline)

    def test_optional_ritual_and_empty_baseline(self):
        for key in ("facts", "reference_questions", "preferences"):
            self.baseline[key] = []
        self.baseline.pop("ritual")
        validate_baseline(self.baseline)

    def test_nonfinite_fact_rejected(self):
        self.baseline["facts"][0]["value"] = float("nan")
        with self.assertRaises(ValidationError):
            validate_baseline(self.baseline)

    def test_json_parser_rejects_duplicates_nonfinite_bad_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            for payload in (
                b'{"id":1,"id":2}',
                b'{"n":NaN}',
                b'{"n":Infinity}',
                b"{bad",
                b"\xff\xfe",
                b'{"text":"\\ud800"}',
                b'{"n":' + b"9" * 5000 + b"}",
            ):
                path.write_bytes(payload)
                with self.assertRaises(ValidationError):
                    read_json(path)

    def test_utf8_bom_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            path.write_text('{"text":"caf\u00e9"}', encoding="utf-8-sig")
            self.assertEqual(read_json(path)["text"], "caf\u00e9")
