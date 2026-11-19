"""Markdown and JSON reports; imported material is always quoted data."""

import html
import json

from .evaluator import validate_evaluation


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def quote(value):
    # JSON-encode before HTML escaping: newlines, fences, links and tags cannot
    # escape their quoted data block in Markdown viewers that support HTML.
    return "<pre>" + html.escape(pretty(value).rstrip()) + "</pre>"


def markdown_report(evaluation, previous=None):
    validate_evaluation(evaluation)
    if previous is not None:
        validate_evaluation(previous)
        from .schemas import require

        require(
            previous["challenge_fingerprint"] == evaluation["challenge_fingerprint"],
            "Session comparison requires identical challenge fingerprints",
        )
    e = evaluation
    lines = [
        "# AI Totem comparison report",
        "",
        "Coding Panda — Don't just remember me. Understand me.",
        "",
        "## Run",
        "",
        quote(
            {
                "baseline": e["baseline"],
                "evaluated_at": e["evaluated_at"],
                "session_id": e["session_id"],
                "explicit_metadata": e["metadata"],
                "challenge_fingerprint": e["challenge_fingerprint"],
            }
        ),
        "",
        "## Deterministic outcomes",
        "",
        "Counts of test outcomes; these are not continuity scores.",
        "",
        "| Outcome | Tests |",
        "| --- | ---: |",
    ]
    lines += [f"| {key} | {value} |" for key, value in e["summary"].items()]
    lines += [
        "",
        "| Dimension | Pass | Fail | Indeterminate | Not applicable |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, counts in e["dimensions"].items():
        lines.append(
            "| "
            + name.replace("_", " ")
            + " | "
            + " | ".join(
                str(counts[k])
                for k in ("pass", "fail", "indeterminate", "not-applicable")
            )
            + " |"
        )
    if previous is not None:
        old = {t["id"]: t for t in previous["results"]}
        lines += [
            "",
            "## Session differences",
            "",
            "Same baseline and challenge fingerprint. Outcome changes do not identify their cause.",
            "",
            quote(
                {
                    "previous_session": previous["session_id"],
                    "current_session": e["session_id"],
                    "changes": [
                        {
                            "test_id": t["id"],
                            "before": old[t["id"]]["outcome"],
                            "after": t["outcome"],
                            "response_changed": old[t["id"]]["observed_response"]
                            != t["observed_response"],
                        }
                        for t in e["results"]
                    ],
                }
            ),
        ]
    for index, test in enumerate(e["results"], 1):
        lines += [
            "",
            f"## Test {index}: {test['dimension'].replace('_', ' ')}",
            "",
            quote(
                {"id": test["id"], "prompt": test["prompt"], "outcome": test["outcome"]}
            ),
            "",
            "### Observed response (untrusted data)",
            "",
            quote(test["observed_response"]),
            "",
            "### Deterministic checks",
            "",
            quote(test["checks"]),
            "",
            "### Differences from reference expectations",
            "",
            quote(test["differences"]),
            "",
            "### Subjective review (unscored)",
            "",
            quote(test["subjective_review"]),
            "",
            "### Missing context and limitations",
            "",
            quote(test["limitations"]),
        ]
    lines += [
        "",
        "## Interpretation",
        "",
        e["interpretation"],
        "",
        "Results may reflect prompting, available context, chance, or response formatting. This report cannot determine whether a model remembers earlier sessions. Every subjective criterion remains unassessed.",
        "",
        "Reports contain supplied text and context. Review and sanitize before sharing. The JSON report also contains the full baseline and input provenance.",
        "",
        "The optional ritual is reproducible by any model with the same instructions. Never use it to unlock accounts, authorize transactions, or protect sensitive information.",
        "",
    ]
    return "\n".join(lines)


def json_report(evaluation, previous=None):
    validate_evaluation(evaluation)
    # Keep the evaluation reusable as a previous report; Markdown contains the
    # side-by-side view, while JSON retains both complete runs when comparing.
    if previous is None:
        return pretty(evaluation)
    markdown_report(evaluation, previous)  # same validation/comparability gate
    return pretty({"current": evaluation, "previous": previous})
