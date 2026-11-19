"""Strict, dependency-free validation for v1 JSON input formats."""

import json
import math
import re
from datetime import datetime
from pathlib import Path

DIMENSIONS = (
    "contextual_recall",
    "reasoning_consistency",
    "communication_preferences",
    "intellectual_independence",
)
OUTCOMES = ("pass", "fail", "indeterminate", "not-applicable")


class ValidationError(ValueError):
    """An input does not satisfy the documented schema."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def obj(value, required, optional=(), label="object"):
    require(isinstance(value, dict), f"{label}: expected an object")
    require(set(required) <= value.keys(), f"{label}: missing required field(s)")
    require(value.keys() <= set(required) | set(optional), f"{label}: unknown field(s)")


def string(value, label, empty=False):
    require(
        isinstance(value, str) and (empty or bool(value.strip())),
        f"{label}: expected a nonempty string",
    )


def identifier(value, label):
    string(value, label)
    require(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value) is not None,
        f"{label}: use 1-128 letters, digits, dots, underscores or hyphens",
    )


def strings(value, label):
    require(isinstance(value, list), f"{label}: expected an array")
    for item in value:
        string(item, label)


def records(value, label):
    require(isinstance(value, list), f"{label}: expected an array")
    seen = set()
    for item in value:
        require(
            isinstance(item, dict) and "id" in item,
            f"{label}: expected objects with id",
        )
        identifier(item["id"], label)
        require(
            item["id"] not in seen,
            f"{label}: duplicate id (possibly contradictory references)",
        )
        seen.add(item["id"])


def version(value):
    require(type(value) is int and value == 1, "schema_version: expected integer 1")


def timestamp(value):
    string(value, "timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError("timestamp: expected ISO 8601") from None
    require(
        parsed.tzinfo is not None and "T" in value,
        "timestamp: timezone and time required",
    )


def json_value(value):
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeError:
            raise ValidationError("JSON strings must contain valid Unicode") from None
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        require(math.isfinite(value), "JSON numbers must be finite")
        return
    if isinstance(value, list):
        for item in value:
            json_value(item)
        return
    if isinstance(value, dict):
        require(all(isinstance(k, str) for k in value), "JSON keys must be strings")
        for key in value:
            json_value(key)
        for item in value.values():
            json_value(item)
        return
    raise ValidationError("Expected a JSON value")


def validate_baseline(data):
    obj(
        data,
        (
            "schema_version",
            "id",
            "version",
            "created_at",
            "preferences",
            "facts",
            "reference_questions",
            "style_examples",
        ),
        ("ritual",),
    )
    version(data["schema_version"])
    identifier(data["id"], "baseline id")
    string(data["version"], "baseline version")
    timestamp(data["created_at"])
    strings(data["preferences"], "preferences")
    records(data["facts"], "facts")
    for fact in data["facts"]:
        obj(fact, ("id", "value", "approved"))
        require(
            fact["approved"] is True,
            "Facts must be explicitly approved (approved: true)",
        )
        json_value(fact["value"])
    records(data["reference_questions"], "reference_questions")
    for ref in data["reference_questions"]:
        obj(ref, ("id", "question", "expected_characteristics"))
        string(ref["question"], "question")
        strings(ref["expected_characteristics"], "expected_characteristics")
    obj(data["style_examples"], ("preferred", "undesirable"))
    for examples in data["style_examples"].values():
        strings(examples, "style examples")
    if "ritual" in data:
        obj(data["ritual"], ("trigger", "expected_response"))
        string(data["ritual"]["trigger"], "trigger")
        string(data["ritual"]["expected_response"], "expected_response")
    return data


def validate_challenge_set(data):
    obj(data, ("schema_version", "id", "tests"))
    version(data["schema_version"])
    identifier(data["id"], "challenge set id")
    records(data["tests"], "tests")
    require(bool(data["tests"]), "At least one test is required")
    for test in data["tests"]:
        obj(
            test,
            (
                "id",
                "dimension",
                "prompt",
                "required_fact_ids",
                "checks",
                "review_criteria",
            ),
            ("reference_id", "not_applicable_reason"),
        )
        require(test["dimension"] in DIMENSIONS, "Unknown dimension")
        string(test["prompt"], "prompt")
        strings(test["required_fact_ids"], "required_fact_ids")
        require(
            len(set(test["required_fact_ids"])) == len(test["required_fact_ids"]),
            "Duplicate required fact",
        )
        strings(test["review_criteria"], "review_criteria")
        if "reference_id" in test:
            identifier(test["reference_id"], "reference_id")
        if "not_applicable_reason" in test:
            string(test["not_applicable_reason"], "not_applicable_reason")
        records(test["checks"], "checks")
        for check in test["checks"]:
            kind = check.get("kind")
            require(
                kind
                in ("exact", "fact_equals", "required_content", "forbidden_content"),
                "Unknown check kind",
            )
            required = (
                ("id", "kind", "field", "fact_id")
                if kind == "fact_equals"
                else (
                    ("id", "kind", "field", "expected")
                    if kind == "exact"
                    else ("id", "kind", "terms")
                )
            )
            obj(
                check, required, ("case_sensitive",) if kind.endswith("content") else ()
            )
            if kind in ("exact", "fact_equals"):
                string(check["field"], "field")
                require(
                    check["field"] == "text"
                    or (
                        check["field"].startswith("structured.")
                        and len(check["field"]) > 11
                    ),
                    "field: use text or structured.<literal-key>",
                )
                if kind == "fact_equals":
                    identifier(check["fact_id"], "fact_id")
                    require(
                        check["fact_id"] in test["required_fact_ids"],
                        "fact_equals must declare its fact in required_fact_ids",
                    )
                else:
                    json_value(check["expected"])
                    if check["field"] == "text":
                        require(
                            isinstance(check["expected"], str),
                            "Exact text expectation must be a string",
                        )
            else:
                strings(check["terms"], "terms")
                require(bool(check["terms"]), "Content checks need at least one term")
                require(
                    type(check.get("case_sensitive", False)) is bool,
                    "case_sensitive must be boolean",
                )
        require(
            bool(test["checks"] or test["review_criteria"] or test.get("reference_id")),
            "Test needs checks or review criteria",
        )
    return data


def validate_responses(data, allowed_ids=None):
    obj(data, ("schema_version", "session_id", "responses"), ("metadata",))
    version(data["schema_version"])
    string(data["session_id"], "session_id")
    obj(data.get("metadata", {}), (), ("model", "provider"))
    for value in data.get("metadata", {}).values():
        string(value, "metadata")
    require(isinstance(data["responses"], list), "responses: expected an array")
    seen = set()
    for response in data["responses"]:
        obj(response, ("test_id",), ("text", "structured"))
        identifier(response["test_id"], "test_id")
        require(response["test_id"] not in seen, "Duplicate response test_id")
        seen.add(response["test_id"])
        if allowed_ids is not None:
            require(
                response["test_id"] in allowed_ids,
                "Response references unknown test_id",
            )
        require(
            "text" in response or "structured" in response,
            "Response requires text or structured data",
        )
        if "text" in response:
            string(response["text"], "response text", empty=True)
        if "structured" in response:
            require(
                isinstance(response["structured"], dict),
                "structured: expected an object",
            )
            json_value(response["structured"])
    return data


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def read_json(path):
    """Read data only: no evaluation, interpolation, imports, or transcript logging."""
    try:
        data = json.loads(
            Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_pairs
        )
        json_value(data)
        return data
    except ValidationError:
        raise
    except (ValueError, RecursionError, UnicodeError):
        raise ValidationError("Invalid JSON input (contents omitted)") from None
