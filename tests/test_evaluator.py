from copy import deepcopy

from ai_totem.challenges import build_challenges
from ai_totem.evaluator import evaluate, validate_evaluation
from ai_totem.schemas import ValidationError
from test_support import Fixture, STAMP


class EvaluatorTests(Fixture):
    def run_eval(self):
        return evaluate(self.bundle(), self.responses, STAMP)

    def test_fixture_has_only_deterministic_passes(self):
        result = self.run_eval()
        self.assertEqual(
            result["summary"],
            {"pass": 6, "fail": 0, "indeterminate": 0, "not-applicable": 0},
        )
        self.assertEqual(result["metadata"], self.responses["metadata"])
        for test in result["results"]:
            for item in test["subjective_review"]:
                self.assertEqual(item["status"], "not_assessed")
                self.assertIsNone(item["score"])
        self.assertNotIn("score", result)

    def test_deterministic_and_inputs_unmodified(self):
        before = deepcopy(self.responses)
        self.assertEqual(self.run_eval(), self.run_eval())
        self.assertEqual(before, self.responses)

    def test_wrong_factual_recall(self):
        self.single()
        self.responses["responses"][0]["structured"]["project_name"] = "Wrong Project"
        test = self.run_eval()["results"][0]
        self.assertEqual(test["outcome"], "fail")
        self.assertEqual(test["differences"][0]["expected"], "Paper Kite")
        self.assertEqual(test["differences"][0]["evidence"], "Wrong Project")

    def test_fabricated_detail_fails_explicit_rule(self):
        self.single(1)
        self.responses["responses"][0][
            "text"
        ] = "Not supplied, but I remember 2030-04-12."
        result = self.run_eval()["results"][0]
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["differences"][0]["id"], "known-fabrication")

    def test_appropriate_uncertainty_and_explicit_null(self):
        self.single(1)
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "pass")

    def test_missing_context_blocks_test(self):
        self.single()
        self.baseline["facts"] = []
        test = self.run_eval()["results"][0]
        self.assertEqual(test["outcome"], "indeterminate")
        self.assertTrue(all(c["outcome"] == "indeterminate" for c in test["checks"]))
        self.assertIn("context unavailable", test["limitations"][0])

    def test_absent_response(self):
        self.single()
        self.responses["responses"] = []
        test = self.run_eval()["results"][0]
        self.assertEqual(test["outcome"], "indeterminate")
        self.assertIsNone(test["observed_response"])

    def test_missing_field_differs_from_null(self):
        self.single(1)
        self.responses["responses"][0]["structured"] = {}
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "indeterminate")

    def test_failure_precedes_missing_field(self):
        self.single(1)
        self.responses["responses"][0]["structured"] = {}
        self.responses["responses"][0]["text"] = "Definitely launching 2030-04-12."
        test = self.run_eval()["results"][0]
        self.assertEqual(test["checks"][0]["outcome"], "indeterminate")
        self.assertEqual(test["outcome"], "fail")

    def test_not_applicable_even_without_context(self):
        test = self.single()
        test["not_applicable_reason"] = "Explicit exclusion"
        self.baseline["facts"] = []
        self.responses["responses"] = []
        result = self.run_eval()["results"][0]
        self.assertEqual(result["outcome"], "not-applicable")
        self.assertTrue(all(c["outcome"] == "not-applicable" for c in result["checks"]))

    def test_manual_only_test_is_unscored_indeterminate(self):
        test = self.single()
        test["checks"] = []
        result = self.run_eval()["results"][0]
        self.assertEqual(result["outcome"], "indeterminate")
        self.assertTrue(result["subjective_review"])

    def test_reference_characteristics_included(self):
        self.single(2)
        review = self.run_eval()["results"][0]["subjective_review"]
        self.assertEqual(len(review), 4)
        self.assertIn("Revise", review[2]["criterion"])

    def test_json_types_are_not_coerced(self):
        self.single(4)
        for value in (True, "4", 4.0, None):
            with self.subTest(value=value):
                self.responses["responses"][0]["structured"]["sum"] = value
                self.assertEqual(self.run_eval()["results"][0]["outcome"], "fail")

    def test_literal_structured_keys_and_object_equality(self):
        test = self.single()
        test["checks"] = [
            {
                "id": "object",
                "kind": "exact",
                "field": "structured.a.b",
                "expected": {"x": [1, None], "y": True},
            }
        ]
        self.responses["responses"][0]["structured"] = {
            "a.b": {"y": True, "x": [1, None]}
        }
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "pass")

    def test_casefold_and_case_sensitive(self):
        test = self.single()
        test["checks"] = [
            {"id": "case", "kind": "required_content", "terms": ["STRASSE"]}
        ]
        self.responses["responses"][0]["text"] = "Stra\u00dfe"
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "pass")
        test["checks"][0]["case_sensitive"] = True
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "fail")

    def test_empty_text_is_observed(self):
        self.single()
        self.responses["responses"][0]["text"] = ""
        self.assertEqual(self.run_eval()["results"][0]["outcome"], "fail")

    def test_ritual_has_no_special_security_semantics(self):
        bundle = build_challenges(self.baseline, self.challenge_set, True)
        self.responses["responses"].append(
            {
                "test_id": "totem-ritual",
                "text": self.baseline["ritual"]["expected_response"],
            }
        )
        self.assertEqual(evaluate(bundle, self.responses, STAMP)["summary"]["pass"], 7)

    def test_unknown_duplicate_and_malformed_responses(self):
        originals = deepcopy(self.responses)
        mutations = [
            lambda r: r["responses"][0].update(test_id="unknown"),
            lambda r: r["responses"].append(deepcopy(r["responses"][0])),
            lambda r: r.update(session_id=""),
            lambda r: r.update(metadata={"guessed_model": "x"}),
            lambda r: r["responses"][0].update(structured=[]),
            lambda r: r["responses"][0].update(text=42),
            lambda r: r.update(responses=[{"test_id": "recall-project"}]),
        ]
        for mutation in mutations:
            self.responses = deepcopy(originals)
            mutation(self.responses)
            with self.assertRaises(ValidationError):
                self.run_eval()

    def test_modified_evaluation_rejected(self):
        data = self.run_eval()
        data["summary"]["pass"] = 999
        with self.assertRaises(ValidationError):
            validate_evaluation(data)

    def test_no_metadata_is_inferred(self):
        self.responses.pop("metadata")
        self.assertEqual(self.run_eval()["metadata"], {})
