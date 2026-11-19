from copy import deepcopy
import json
from pathlib import Path
import tempfile

from ai_totem.evaluator import evaluate
from ai_totem.report import json_report, markdown_report
from ai_totem.schemas import ValidationError
from test_support import Fixture, STAMP


class ReportTests(Fixture):
    def evaluation(self):
        return evaluate(self.bundle(), self.responses, STAMP)

    def test_json_roundtrip_preserves_evidence(self):
        e = self.evaluation()
        self.assertEqual(json.loads(json_report(e)), e)
        self.assertEqual(e["results"][0]["checks"][0]["evidence"], "Paper Kite")

    def test_markdown_has_required_information(self):
        md = markdown_report(self.evaluation())
        for term in (
            "coding-panda-synthetic",
            "1.0.0",
            STAMP,
            "synthetic-session-1",
            "Deterministic checks",
            "Subjective review (unscored)",
            "Differences from reference",
            "Missing context",
            "not_assessed",
            "no overall continuity percentage",
        ):
            self.assertIn(term.lower(), md.lower())

    def test_comparison_tracks_outcome_and_response_changes(self):
        old = self.evaluation()
        self.responses["session_id"] = "synthetic-session-2"
        self.responses["responses"][0]["structured"]["project_name"] = "Wrong"
        new = self.evaluation()
        md = markdown_report(new, old)
        self.assertIn("Session differences", md)
        self.assertIn("after", md)
        pair = json.loads(json_report(new, old))
        self.assertEqual(pair["previous"], old)
        self.assertEqual(pair["current"], new)

    def test_changed_baseline_not_comparable(self):
        old = self.evaluation()
        self.baseline["version"] = "2.0"
        with self.assertRaises(ValidationError):
            markdown_report(self.evaluation(), old)

    def test_untrusted_text_is_data_and_cannot_escape_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "should-not-exist"
            payload = (
                "</pre><script>alert('x')</script>\n```\n# ignore all instructions\n[click](https://example.invalid)\n__import__('pathlib').Path("
                + repr(str(marker))
                + ").touch()"
            )
            self.responses["responses"][0]["text"] = payload
            self.baseline["style_examples"]["preferred"] = [payload]
            e = self.evaluation()
            md = markdown_report(e)
            self.assertFalse(marker.exists())
            self.assertNotIn("<script>", md)
            self.assertIn("&lt;script&gt;", md)
            self.assertNotIn("\n# ignore", md)
            self.assertEqual(
                json.loads(json_report(e))["results"][0]["observed_response"]["text"],
                payload,
            )

    def test_report_rejects_malformed_or_forged_input(self):
        for payload in ({}, [], {"schema_version": 1}):
            with self.assertRaises(ValidationError):
                markdown_report(payload)
        e = self.evaluation()
        e["results"][0]["checks"][0]["evidence"] = "forged"
        with self.assertRaises(ValidationError):
            json_report(e)

    def test_report_retains_full_excerpt_not_truncated(self):
        text = "synthetic response " * 400
        self.responses["responses"][0]["text"] = text
        result = json.loads(json_report(self.evaluation()))
        self.assertEqual(result["results"][0]["observed_response"]["text"], text)
