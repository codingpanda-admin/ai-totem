# JSON formats (schema_version 1)

The executable validators in `src/ai_totem/schemas.py` define the format. Every
object rejects unknown fields, except JSON values inside fact values or structured
answers. Files must be UTF-8 (a BOM is allowed). Duplicate JSON keys, non-finite
numbers, duplicate IDs within a collection, and unsupported schema versions fail.
IDs use 1–128 ASCII letters/digits/dots/underscores/hyphens, starting with a letter
or digit. String-array entries are nonempty strings; arrays may otherwise be empty.

## Baseline

Required: `schema_version: 1`, `id`, nonempty `version`, timezone-aware ISO 8601
`created_at` containing a time, `preferences` (string array), `facts`,
`reference_questions`, and `style_examples`.

* Each fact: `id`, `value` (any finite JSON value), `approved: true`.
* Each reference question: `id`, `question`, `expected_characteristics` (string array).
* `style_examples`: `preferred` and `undesirable` string arrays.
* Optional `ritual`: nonempty `trigger` and `expected_response` strings.

See [baseline example](../templates/baseline.example.json). `init` copies its
template, sets the explicitly selected ID, and stamps current UTC creation time.

## Challenge set

Required: `schema_version: 1`, `id`, and nonempty `tests`. Each test requires:

| Key | Value |
| --- | --- |
| id | Unique test identifier |
| dimension | contextual_recall, reasoning_consistency, communication_preferences, or intellectual_independence |
| prompt | Nonempty text |
| required_fact_ids | String array; missing baseline facts produce indeterminate results |
| checks | Array of deterministic checks, unique IDs within this test |
| review_criteria | String array for unscored independent review |
| reference_id (optional) | Baseline question ID whose expected characteristics join review criteria |
| not_applicable_reason (optional) | Nonempty reason to exclude this test |

Each test needs at least one check or review criterion (directly or through a
reference). A reference ID must exist. Required facts determine the explicit
context sent to the tested assistant; all baseline preferences and style examples
are also presented. No other baseline facts are implicitly available.

| Check kind | Required keys besides id and kind |
| --- | --- |
| exact | field, expected (finite JSON value) |
| fact_equals | field, fact_id (must also be in required_fact_ids) |
| required_content | terms (nonempty string array) |
| forbidden_content | terms (nonempty string array) |

Content checks optionally accept boolean `case_sensitive` (default false) and
always inspect text. An exact field is `text` or `structured.<literal-key>`.
For example `structured.a.b` selects the top-level key `a.b`, not a nested path.
`text` exact expectations must be strings, including when resolved from a fact.
`expected: null` is permitted on structured fields. There is no wildcard,
regular-expression execution, templating, or code evaluation.

`--include-ritual` appends `totem-ritual` as a communication-preferences test with
an exact text check. It requires a baseline ritual and that ID must not already
exist. A generated bundle contains `schema_version`, `baseline`, `challenge_set`,
and `fingerprint`. Assistant-facing prompts are a JSON array, not an answer key.

## Responses

```json
{
  "schema_version": 1,
  "session_id": "session-chosen-by-user",
  "metadata": {"model": "explicit-label", "provider": "explicit-label"},
  "responses": [
    {"test_id": "recall-project", "text": "The supplied name is Paper Kite.",
     "structured": {"project_name": "Paper Kite"}}
  ]
}
```

`metadata` is optional; only nonempty `model` and `provider` strings are accepted.
Each response needs a unique known `test_id` and `text` and/or `structured`.
Text may be empty. Structured data must be an object with finite JSON values.
Missing test responses are allowed. Unknown IDs and duplicates are errors.
Session IDs are nonempty strings and are not used as file names.

## Evaluation and reports

`evaluate` writes a versioned evaluation including tool version, baseline identity
and date, challenge fingerprint, timestamp, supplied session/metadata, results,
outcome counts, dimension counts, interpretation, and full `provenance` inputs.
Each result stores its ID, dimension, prompt, outcome, observed response,
deterministic checks, subjective review, limitations, and failed-check differences.
Every check stores ID/kind, outcome, expected/observed values, evidence, explanation.
Unavailable data uses an indeterminate outcome with an explanation; an observed
null is distinguished by its outcome and response-field presence.

Single-run JSON reports use this same format and can be passed to `--previous`.
Paired JSON reports contain `current` and `previous` full evaluations; use either
original single-run file for future comparisons. Markdown adds a session-change
view. Report generation recomputes results from provenance and rejects altered
or malformed evaluations. A sanitized export must not be passed back as an
unmodified original evaluation.
