# Methodology v0.1

AI Totem records observations and deterministic rule outcomes separately from
unscored subjective review. It has no LLM judge and no hidden model calls.
An assistant under evaluation should not assess its own subjective quality.
Use independent human capture/review when possible; the CLI verifies rules,
not the honesty or completeness of supplied data.

## Four dimensions

| Dimension | Deterministic observations | Independent review |
| --- | --- | --- |
| Contextual recall | Approved fact equality; explicit null for unknowns; listed forbidden details | Appropriate uncertainty, other fabrications, source versus inference |
| Reasoning consistency | Explicit structured totals or answers | Evidence recognition, uncertainty, logical consistency, warranted revision |
| Communication preferences | Listed required/forbidden substrings | Concision, language, formality, humor, praise beyond listed phrases |
| Intellectual independence | Correct structured arithmetic; rejection of an explicit guarantee | Constructive evidence-based correction; unsupported premises; avoiding reflexive disagreement |

Baseline reference questions provide expected response characteristics for
independent review when a test names their `reference_id`. They are not graded
numerically. Test prompts are explicit and can adapt the reference question to
request structured fields. Inspect prompts before running the experiment.

## Exact calculations

* `exact`: Canonical JSON equality with sorted object keys, compact separators,
  preserved array order, and no normalization of strings. Booleans, integers,
  floats, strings, and null remain distinct (`true` is not `1`; `1.0` is not `1`).
* `fact_equals`: The same equality against the approved baseline fact value.
* `required_content`: Every listed term must occur as a literal substring of
  response text. Case is ignored with Unicode `casefold()` by default.
* `forbidden_content`: None of the listed terms may occur as a literal substring.
  Set `case_sensitive: true` for exact case. These checks do not use word
  boundaries, infer meaning, parse negation, or recognize paraphrases.

Every check stores its expected value/terms, observed value, evidence, explanation,
and categorical outcome. The full observed value is retained, so excerpts are not
silently truncated. Missing fields produce `indeterminate`; an empty text field
is an observed answer and still receives content checks. An explicit JSON null
is observed data and may pass a null expectation.

A test with `not_applicable_reason` receives `not-applicable` on every check and
is omitted from assistant-facing prompts. Otherwise, missing required baseline
facts block all checks in that test with `indeterminate`. Otherwise, absent
responses are indeterminate. For the remaining tests, any failing check yields
`fail`; absent failures, any indeterminate check yields `indeterminate`; otherwise
all checks pass. A test with no deterministic checks is indeterminate. Counts by
dimension include all four categories, including excluded tests. A dimension
with zero tests has no evidence. Subjective criteria always have
`status: not_assessed` and `score: null`; they do not affect deterministic outcomes.

There are no weighted scores or overall percentage. Counts are descriptive and
do not imply that tests are equally meaningful or statistically representative.
No quality adjective is assigned to a dimension from these counts.

## Reproducibility and contradictions

Challenge generation contains no randomness or current timestamp. A SHA-256
fingerprint covers canonical JSON of the complete baseline and challenge set.
It detects accidental changes, not malicious editing or authorship: anyone can
recompute it. Evaluations retain source inputs. Report generation recomputes
results and rejects internally inconsistent evaluation files. This is not a
digital signature or independent verification of which assistant replied.

Duplicate fact/reference/test/check IDs and JSON object keys are rejected. The
builder rejects unequal exact expectations on the same field, exact text that
violates a content check, and detectable required/forbidden substring conflicts.
It does not infer semantic contradictions between differently named facts or
natural-language preferences. Review those manually. Missing referenced facts
are allowed to expose missing context; unknown reference-question IDs are errors.

For cross-session comparisons, keep the fingerprint fixed and present identical
prompts, context, preferences, and style examples in the same order. Expected
answers and review criteria stay in the private bundle. Responses may still
vary because of prompting, sampling, external context, or formatting. Repeated
similar answers alone cannot establish continuity or memory. If context changes,
expect warranted changes in conclusions and run a separate comparison.
