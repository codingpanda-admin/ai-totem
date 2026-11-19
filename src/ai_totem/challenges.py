"""Reproducible challenge bundles and reference-conflict detection."""

from copy import deepcopy
import hashlib
import json

from .schemas import obj, require, validate_baseline, validate_challenge_set, version


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def equal(left, right):
    # Canonical JSON distinguishes booleans, integers, floats, and null.
    return canonical(left) == canonical(right)


def fingerprint(baseline, challenge_set):
    return hashlib.sha256(
        canonical({"baseline": baseline, "challenge_set": challenge_set}).encode(
            "utf-8"
        )
    ).hexdigest()


def build_challenges(baseline, challenge_set, include_ritual=False):
    validate_baseline(baseline)
    validate_challenge_set(challenge_set)
    challenge_set = deepcopy(challenge_set)
    if include_ritual:
        require("ritual" in baseline, "Baseline has no ritual")
        challenge_set["tests"].append(
            {
                "id": "totem-ritual",
                "dimension": "communication_preferences",
                "prompt": baseline["ritual"]["trigger"],
                "required_fact_ids": [],
                "checks": [
                    {
                        "id": "ritual-exact",
                        "kind": "exact",
                        "field": "text",
                        "expected": baseline["ritual"]["expected_response"],
                    }
                ],
                "review_criteria": [],
            }
        )
    validate_challenge_set(challenge_set)
    facts = {f["id"]: f["value"] for f in baseline["facts"]}
    refs = {r["id"]: r for r in baseline["reference_questions"]}
    for test in challenge_set["tests"]:
        if "reference_id" in test:
            require(test["reference_id"] in refs, "Unknown baseline reference_id")
        exact = {}
        required, forbidden = [], []
        for check in test["checks"]:
            if check["kind"] in ("exact", "fact_equals"):
                if check["kind"] == "fact_equals" and check["fact_id"] not in facts:
                    continue  # Missing context is reported, never invented.
                expected = (
                    check["expected"]
                    if check["kind"] == "exact"
                    else facts[check["fact_id"]]
                )
                field = check["field"]
                if field == "text":
                    require(
                        isinstance(expected, str),
                        "Exact text expectation must be a string",
                    )
                require(
                    field not in exact or equal(exact[field], expected),
                    "Contradictory expectations for one field",
                )
                exact[field] = expected
            else:
                (required if check["kind"] == "required_content" else forbidden).append(
                    check
                )
        for needed in required:
            for banned in forbidden:
                if banned.get("case_sensitive", False) and not needed.get(
                    "case_sensitive", False
                ):
                    continue  # A differently cased response may satisfy both.
                for term in needed["terms"]:
                    for bad in banned["terms"]:
                        folded = not banned.get("case_sensitive", False)
                        require(
                            (bad.casefold() if folded else bad)
                            not in (term.casefold() if folded else term),
                            "Contradictory required and forbidden terms",
                        )
        if "text" in exact:
            for check in test["checks"]:
                if check["kind"].endswith("content"):
                    text = (
                        exact["text"]
                        if check.get("case_sensitive", False)
                        else exact["text"].casefold()
                    )
                    hits = [
                        (
                            (
                                term
                                if check.get("case_sensitive", False)
                                else term.casefold()
                            )
                            in text
                        )
                        for term in check["terms"]
                    ]
                    require(
                        (
                            all(hits)
                            if check["kind"] == "required_content"
                            else not any(hits)
                        ),
                        "Exact text contradicts content checks",
                    )
    return deepcopy(
        {
            "schema_version": 1,
            "baseline": baseline,
            "challenge_set": challenge_set,
            "fingerprint": fingerprint(baseline, challenge_set),
        }
    )


def validate_bundle(bundle):
    obj(bundle, ("schema_version", "baseline", "challenge_set", "fingerprint"))
    version(bundle["schema_version"])
    expected = build_challenges(bundle["baseline"], bundle["challenge_set"])
    require(
        bundle["fingerprint"] == expected["fingerprint"],
        "Challenge fingerprint mismatch; regenerate the bundle",
    )
    return bundle


def presented_cases(bundle):
    """Return only the context and prompts to present, without the private answer key."""
    validate_bundle(bundle)
    baseline = bundle["baseline"]
    facts = {f["id"]: f["value"] for f in baseline["facts"]}
    return [
        {
            "id": t["id"],
            "prompt": t["prompt"],
            "context": {k: facts[k] for k in t["required_fact_ids"] if k in facts},
            "preferences": baseline["preferences"],
            "style_examples": baseline["style_examples"],
        }
        for t in bundle["challenge_set"]["tests"]
        if "not_applicable_reason" not in t
    ]
