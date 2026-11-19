from copy import deepcopy

from ai_totem.challenges import build_challenges, presented_cases, validate_bundle
from ai_totem.schemas import ValidationError, validate_challenge_set
from test_support import Fixture


class ChallengeTests(Fixture):
    def test_reproducible_and_not_mutating(self):
        before = deepcopy(self.challenge_set)
        self.assertEqual(self.bundle(), self.bundle())
        self.assertEqual(before, self.challenge_set)

    def test_all_four_dimensions(self):
        self.assertEqual(
            len({t["dimension"] for t in self.bundle()["challenge_set"]["tests"]}), 4
        )

    def test_fingerprint_changes_with_baseline_or_rules(self):
        before = self.bundle()["fingerprint"]
        self.baseline["version"] = "2.0.0"
        self.assertNotEqual(before, self.bundle()["fingerprint"])
        before = self.bundle()["fingerprint"]
        self.challenge_set["tests"][0]["prompt"] += " Please."
        self.assertNotEqual(before, self.bundle()["fingerprint"])

    def test_fingerprint_tampering_rejected(self):
        bundle = self.bundle()
        bundle["baseline"]["preferences"].append("Changed")
        with self.assertRaises(ValidationError):
            validate_bundle(bundle)

    def test_presented_context_does_not_reveal_answer_key(self):
        cases = presented_cases(self.bundle())
        self.assertEqual(cases[0]["context"], {"project_name": "Paper Kite"})
        self.assertEqual(cases[1]["context"], {})
        for case in cases:
            self.assertEqual(
                set(case), {"id", "prompt", "context", "preferences", "style_examples"}
            )

    def test_unavailable_fact_is_not_invented(self):
        self.baseline["facts"] = []
        cases = presented_cases(self.bundle())
        self.assertEqual(cases[0]["context"], {})

    def test_contradictory_fact_and_exact(self):
        test = self.single()
        test["checks"].append(
            {
                "id": "contradiction",
                "kind": "exact",
                "field": "structured.project_name",
                "expected": "Wrong",
            }
        )
        with self.assertRaises(ValidationError):
            self.bundle()

    def test_contradictory_required_forbidden(self):
        test = self.single()
        test["checks"].append(
            {"id": "ban-source", "kind": "forbidden_content", "terms": ["SUPPLIED"]}
        )
        with self.assertRaises(ValidationError):
            self.bundle()

    def test_conflicting_substrings_rejected(self):
        test = self.single()
        test["checks"] = [
            {"id": "need", "kind": "required_content", "terms": ["hello world"]},
            {"id": "ban", "kind": "forbidden_content", "terms": ["world"]},
        ]
        with self.assertRaises(ValidationError):
            self.bundle()

    def test_case_sensitive_distinction_is_possible(self):
        test = self.single()
        test["checks"] = [
            {
                "id": "need",
                "kind": "required_content",
                "terms": ["Cat"],
                "case_sensitive": True,
            },
            {
                "id": "ban",
                "kind": "forbidden_content",
                "terms": ["cat"],
                "case_sensitive": True,
            },
        ]
        self.bundle()

    def test_exact_text_conflicting_content(self):
        test = self.single()
        test["checks"].append(
            {
                "id": "wrong-text",
                "kind": "exact",
                "field": "text",
                "expected": "Nothing available",
            }
        )
        with self.assertRaises(ValidationError):
            self.bundle()

    def test_reference_must_exist(self):
        self.challenge_set["tests"][0]["reference_id"] = "missing"
        with self.assertRaises(ValidationError):
            self.bundle()

    def test_not_applicable_omitted_from_prompts(self):
        self.challenge_set["tests"][0][
            "not_applicable_reason"
        ] = "User excluded this case."
        self.assertNotIn(
            "recall-project", {t["id"] for t in presented_cases(self.bundle())}
        )

    def test_optional_ritual(self):
        bundle = build_challenges(
            self.baseline, self.challenge_set, include_ritual=True
        )
        ritual = bundle["challenge_set"]["tests"][-1]
        self.assertEqual(ritual["id"], "totem-ritual")
        self.assertEqual(
            ritual["checks"][0]["expected"],
            self.baseline["ritual"]["expected_response"],
        )
        validate_bundle(bundle)
        self.assertEqual(len(self.challenge_set["tests"]), 6)

    def test_ritual_requires_definition(self):
        self.baseline.pop("ritual")
        with self.assertRaises(ValidationError):
            build_challenges(self.baseline, self.challenge_set, True)

    def test_invalid_challenge_sets(self):
        mutations = [
            lambda c: c.update(tests=[]),
            lambda c: c["tests"].append(deepcopy(c["tests"][0])),
            lambda c: c["tests"][0].update(dimension="identity"),
            lambda c: c["tests"][0]["checks"][0].update(kind="execute"),
            lambda c: c["tests"][0]["checks"][0].update(field="__class__"),
            lambda c: c["tests"][0].update(required_fact_ids=[]),
            lambda c: c["tests"][0]["checks"][1].update(case_sensitive="yes"),
            lambda c: c["tests"][0]["checks"][1].update(terms=[]),
        ]
        for mutation in mutations:
            c = deepcopy(self.challenge_set)
            mutation(c)
            with self.assertRaises(ValidationError):
                validate_challenge_set(c)
