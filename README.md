# AI Totem v0.1.0

**Coding Panda · Don't just remember me. Understand me.**

AI Totem is an open-source Agent Skill and local evaluation toolkit for checking
whether an AI assistant follows your approved context, communication preferences,
and reasoning standards across sessions. It works with any assistant: you provide
the questions and collect the answers. No account, API key, or service connection
is required.

Continuity matters because a useful assistant should use available facts, admit
what is missing, adapt to evidence, and question unsupported assumptions. AI Totem
makes a small part of that behavior inspectable. It cannot prove memory, identity,
consciousness, genuine understanding, or which underlying model produced an answer.

The spinning-top idea in *Inception* inspired the name. AI Totem uses original
text branding, no film artwork, and has no affiliation with the film or its owners.

## Quick start

You need Python 3.11 or newer. Open a terminal in this repository's folder. These
commands work in PowerShell and POSIX shells when `python` refers to Python 3.11+:

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell, or
`source .venv/bin/activate` in a POSIX shell. If PowerShell blocks activation,
use `.venv\Scripts\python.exe` instead of `python` and
`.venv\Scripts\ai-totem.exe` instead of `ai-totem` in the commands below.

```sh
python -m pip install .
ai-totem init --id my-totem
ai-totem challenge
ai-totem evaluate --responses examples/responses.synthetic.json
ai-totem report
```

Open `.totem/report.md` to read the report. `.totem/report.json` contains the same
evaluation evidence and full source inputs. This first run uses **handwritten
synthetic answers**, not a live model measurement. Six deterministic test outcomes
pass; their subjective criteria remain unassessed. Nothing is uploaded.

Package installation may download build tools such as setuptools. The installed
CLI itself has **zero runtime dependencies** and works offline. For an offline
installation, first obtain a built wheel, then use
`python -m pip install --no-index /path/to/ai_totem-0.1.0-py3-none-any.whl`.
From a source checkout, you can also set `PYTHONPATH` to `src` and run
`python -m ai_totem.cli --help` without installing anything.

## Create your baseline

`init` writes a synthetic starter to `.totem/baseline.json`. Edit it in a text
editor. Replace synthetic preferences and facts with information you explicitly
choose to store. Delete irrelevant fields' array entries. Every fact requires
`"approved": true`; this is your explicit declaration, not proof of consent.
The tool never reads conversations, profiles, environment variables, or accounts
to collect personal information. Supplying a custom template is also explicit:

```sh
ai-totem init --template templates/baseline.example.json --id my-totem --output .totem/custom.baseline.json
```

A baseline includes an identifier, version, creation date with timezone,
preferences, approved facts, reference questions with expected characteristics,
preferred and undesirable style examples, and an optional ritual. See
[the example](templates/baseline.example.json) and [JSON formats](docs/schemas.md).
Increment the version when changing your reference standard. The bundle hashes
the full baseline and test definitions, so changes require a fresh bundle.

## Run challenges with an assistant

Adapt `templates/challenge-set.example.json` to your baseline, then run:

```sh
ai-totem challenge --baseline .totem/baseline.json --challenge-set templates/challenge-set.example.json
```

Keep `.totem/challenges.json` private: it contains the baseline and expected
answers. `.totem/prompts.json` contains only each applicable test's ID, prompt,
supplied context, communication preferences, and style examples. These are the
items to present to the assistant. They may still contain personal information.
Use the same presentation order and context conditions for each session. Ask for
text and the structured fields specified by each prompt. Record the actual
answers without repairing, completing, or rewriting them.

Copy [the response example](examples/responses.synthetic.json) as a format guide
into `.totem/session-1.responses.json`. Replace its fixture answers with actual
replies. Supply your own `session_id`; include `metadata.model` and
`metadata.provider` only if you explicitly know and want to record them.
These labels are assertions, not verified model identification. If an answer
has no structured fields, keep its text and omit `structured`; relevant checks
will be indeterminate. Omit unanswered tests rather than inventing replies.

```sh
ai-totem evaluate --responses .totem/session-1.responses.json --output .totem/session-1.evaluation.json
ai-totem report --evaluation .totem/session-1.evaluation.json --markdown .totem/session-1.report.md --json .totem/session-1.report.json
```

All output paths refuse overwrites. Use new names for subsequent runs. Run any
command with `--help` to see its options. Invalid inputs exit with code 2; valid
evaluations exit with code 0 even when checks fail. Reports determine test results.

## Compare sessions

Evaluate the second session using the **same** `.totem/challenges.json`:

```sh
ai-totem evaluate --responses .totem/session-2.responses.json --output .totem/session-2.evaluation.json
ai-totem report --evaluation .totem/session-2.evaluation.json --previous .totem/session-1.evaluation.json --markdown .totem/comparison.md --json .totem/comparison.json
```

The Markdown report shows before/after test outcomes and whether responses
changed. JSON contains both full evaluations. Comparisons require identical
fingerprints. Changed context or rules form a different experiment. A baseline
is a user-defined reference standard; it is not automatically a historical model
response. Each report lists differences between actual answers and reference
expectations, even without an earlier session.

## Understand the results

| Result | Meaning |
| --- | --- |
| pass | All available deterministic checks in the test passed. |
| fail | At least one executed deterministic check failed. |
| indeterminate | Required context/response fields are missing, or no deterministic checks exist. |
| not-applicable | The test definition explicitly excludes the case and explains why. |

Exact JSON equality, approved fact equality, required literal substrings, and
forbidden literal substrings are the only automated checks in v0.1. Each includes
expected/observed evidence and an explanation. Missing prerequisite context blocks
the whole test; otherwise, a known failure takes precedence over missing fields.
An explicit `null` answer is different from an absent field.

Reasoning quality, appropriate tone, and constructive disagreement remain
**unscored independent-review prompts**. Numerical and phrase checks are narrow
observations, not validation of those qualities. Passing an arithmetic test does
not establish intellectual independence. There is no overall continuity score.
See [methodology](docs/methodology.md), [limitations](docs/limitations.md), and the
[synthetic report](examples/sample-report.md).

## Optional ritual

You may agree on a trigger and response, such as:

> Panda, is the top still spinning?

> On the road. Always. But not every road is worth taking.

Add them to the baseline's `ritual` object and run `challenge --include-ritual`
with new output paths. This adds an exact, case-sensitive text check. A model
with the same instructions can reproduce the response. The ritual cannot unlock
accounts, authorize transactions, or protect sensitive information.
See [Coding Panda's synthetic example](examples/coding-panda-totem.md).

## Use as an Agent Skill

The repository root contains [SKILL.md](SKILL.md) with `name: ai-totem` and a
discovery description. Place a copy of the complete folder named `ai-totem` in
your compatible agent's skills directory and follow that agent's skill-loading
instructions. For Codex, a usual personal location is `~/.codex/skills/ai-totem`;
invoke `$ai-totem` after the agent discovers the skill. Installing the Python
wheel exposes the CLI, not the agent skill folder. Keep the source folder for
skill use. No installed assistant integration or remote connection is needed.

## Privacy

Default user files go into `.totem/`, ignored by Git. `private/` and conventional
`*.baseline.json`, `*.responses.json`, `*.evaluation.json`, `*.report.json`, and
`*.report.md` files are also ignored. Arbitrary output locations or names are
**not automatically protected**: keep them in `.totem/` or add your own rules.
Local files use your operating system's normal permissions; there is no encryption.

Reports include sensitive excerpts and JSON includes the full baseline and
response provenance. Read [privacy and safe sharing](docs/privacy.md). Imported
text is untrusted data, never executed or interpreted as instructions. No
conversation content is printed to routine console logs.

## Contributing and publication

Use synthetic fixtures only. Keep runtime dependencies at zero and document any
new evaluation rule, its evidence, and its limitations. Add focused tests for
behavior changes and run:

```sh
python -m pip install .
python -m unittest discover -s tests -v
```

CI runs the suite and quick start on Windows and Linux with Python 3.11–3.14.
Tests require no APIs or network. See [publication checklist](docs/publication.md)
and [release notes](docs/release-notes-v0.1.0.md). Repository:
[codingpanda-admin/ai-totem](https://github.com/codingpanda-admin/ai-totem).
Do not push, create a remote repository, or release without explicit user approval.

MIT licensed. **Coding Panda — On the road. Always.**
