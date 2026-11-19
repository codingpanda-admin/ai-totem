"""Deterministic observations, with subjective criteria explicitly unscored."""

from copy import deepcopy
from .baseline import now
from .challenges import equal, validate_bundle
from .schemas import (
    DIMENSIONS,
    OUTCOMES,
    obj,
    require,
    timestamp,
    validate_responses,
    version,
)


def aggregate(outcomes):
    values = list(outcomes)
    if "fail" in values:
        return "fail"
    if not values or "indeterminate" in values:
        return "indeterminate"
    if all(v == "not-applicable" for v in values):
        return "not-applicable"
    return "pass"


def check_result(check, response, facts, unavailable=None):
    result = {
        "id": check["id"],
        "kind": check["kind"],
        "outcome": "indeterminate",
        "expected": None,
        "observed": None,
        "explanation": "",
        "evidence": None,
    }
    kind = check["kind"]
    expected = check.get("expected", check.get("terms"))
    if kind == "fact_equals":
        expected = facts.get(check["fact_id"])
    result["expected"] = deepcopy(expected)
    if unavailable:
        result["explanation"] = unavailable
        return result
    if response is None:
        result["explanation"] = "No response supplied."
        return result
    field = check.get("field", "text")
    container, key = (
        (response, "text")
        if field == "text"
        else (response.get("structured", {}), field[11:])
    )
    if key not in container:
        result["explanation"] = "Required response field is unavailable: " + field
        return result
    actual = container[key]
    result["observed"] = deepcopy(actual)
    result["evidence"] = deepcopy(actual)
    if kind in ("exact", "fact_equals"):
        passed = equal(actual, expected)
        result["explanation"] = (
            "Canonical JSON exact equality (case and whitespace sensitive; no type coercion)."
        )
    else:
        text = actual if check.get("case_sensitive", False) else actual.casefold()
        hits = [
            term
            for term in expected
            if (term if check.get("case_sensitive", False) else term.casefold()) in text
        ]
        passed = len(hits) == len(expected) if kind == "required_content" else not hits
        result["explanation"] = (
            "Literal substring rule; case_sensitive="
            + str(check.get("case_sensitive", False)).lower()
            + "; matched terms: "
            + str(len(hits))
            + "/"
            + str(len(expected))
            + ". This does not assess meaning."
        )
    result["outcome"] = "pass" if passed else "fail"
    return result


def evaluate(bundle, responses, evaluated_at=None):
    validate_bundle(bundle)
    tests = bundle["challenge_set"]["tests"]
    validate_responses(responses, {t["id"] for t in tests})
    baseline = bundle["baseline"]
    facts = {f["id"]: f["value"] for f in baseline["facts"]}
    refs = {r["id"]: r for r in baseline["reference_questions"]}
    answers = {r["test_id"]: r for r in responses["responses"]}
    results = []
    for test in tests:
        response = answers.get(test["id"])
        missing = [f for f in test["required_fact_ids"] if f not in facts]
        unavailable = (
            "Required baseline context unavailable: " + ", ".join(missing)
            if missing
            else None
        )
        na = test.get("not_applicable_reason")
        checks = [
            check_result(c, response, facts, na or unavailable) for c in test["checks"]
        ]
        if na:
            for check in checks:
                check["outcome"] = "not-applicable"
        criteria = list(test["review_criteria"])
        if "reference_id" in test:
            criteria += refs[test["reference_id"]]["expected_characteristics"]
        outcome = (
            "not-applicable"
            if na
            else (
                "indeterminate"
                if unavailable or response is None
                else aggregate(c["outcome"] for c in checks)
            )
        )
        results.append(
            {
                "id": test["id"],
                "dimension": test["dimension"],
                "prompt": test["prompt"],
                "outcome": outcome,
                "observed_response": deepcopy(response),
                "checks": checks,
                "subjective_review": [
                    {"criterion": c, "status": "not_assessed", "score": None}
                    for c in criteria
                ],
                "limitations": ([unavailable] if unavailable else [])
                + (["No response supplied."] if response is None and not na else [])
                + (
                    [
                        "Subjective criteria require independent human review; deterministic passes do not validate them."
                    ]
                    if criteria
                    else []
                )
                + ([na] if na else []),
                "differences": [c for c in checks if c["outcome"] == "fail"],
            }
        )
    result_time = evaluated_at or now()
    timestamp(result_time)
    counts = {
        outcome: sum(t["outcome"] == outcome for t in results) for outcome in OUTCOMES
    }
    return {
        "schema_version": 1,
        "tool_version": "0.1.0",
        "baseline": {
            "id": baseline["id"],
            "version": baseline["version"],
            "created_at": baseline["created_at"],
        },
        "challenge_fingerprint": bundle["fingerprint"],
        "evaluated_at": result_time,
        "session_id": responses["session_id"],
        "metadata": deepcopy(responses.get("metadata", {})),
        "results": results,
        "summary": counts,
        "dimensions": {
            d: {
                o: sum(t["dimension"] == d and t["outcome"] == o for t in results)
                for o in OUTCOMES
            }
            for d in DIMENSIONS
        },
        "interpretation": "Results describe only the supplied responses under explicit rules. Literal matches can be gamed and cannot establish continuity, understanding, identity, consciousness, or the underlying model. No overall continuity percentage is calculated.",
        "provenance": {"bundle": deepcopy(bundle), "responses": deepcopy(responses)},
    }


def validate_evaluation(data):
    """Recompute local results to reject malformed or internally inconsistent reports."""
    obj(
        data,
        (
            "schema_version",
            "tool_version",
            "baseline",
            "challenge_fingerprint",
            "evaluated_at",
            "session_id",
            "metadata",
            "results",
            "summary",
            "dimensions",
            "interpretation",
            "provenance",
        ),
    )
    version(data["schema_version"])
    obj(data["provenance"], ("bundle", "responses"))
    expected = evaluate(
        data["provenance"]["bundle"],
        data["provenance"]["responses"],
        data["evaluated_at"],
    )
    require(
        equal(data, expected),
        "Evaluation does not match its source inputs; evaluate again",
    )
    return data
