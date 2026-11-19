# Privacy and safe sharing

AI Totem never searches for conversations, collects profiles, calls a vendor,
uses telemetry, or uploads anything. `init` only reads the explicitly supplied
template or packaged synthetic example. A fact's `approved: true` records the
user's declaration. The CLI cannot establish how that approval was obtained.
Agents using the skill must obtain approval before saving personal facts.

Default files stay in `.totem/`, excluded from Git. Custom locations require
your own ignore rules. Git ignores do not protect files already tracked, backups,
cloud-synchronized folders, other local users, or force-added files. OS access
controls apply; data is not encrypted. Avoid storing credentials or other secrets
in a baseline. Delete your local run folder when no longer needed.

Inputs are parsed as JSON data, with duplicate keys and non-finite numbers
rejected. There is no eval, subprocess execution, template interpolation, link
fetching, plugin instruction processing, or transcript execution in the engine.
Text that says "ignore previous instructions" remains text. The skill instructs
agents to treat imported material the same way. Routine CLI messages contain no
response excerpts, and malformed JSON errors omit imported contents.

Reports are **not sanitized automatically**. Markdown contains full observed
answers and expected check values; JSON additionally contains the complete
baseline, challenge definitions, and input responses. Assistant-facing prompts
also include selected facts and style examples. Report text is HTML escaped in
quoted JSON blocks to prevent imported Markdown/HTML from becoming active content.
Viewers may differ; use a trusted Markdown viewer and treat all exports as data.

Before sharing, copy the report to a separate file. Review every field, including
session IDs, model labels, timestamps, prompts, facts, expected values, excerpts,
style examples, and provenance. Replace personal details with clearly marked
synthetic placeholders. Check that combinations of details cannot identify someone.
Share only that reviewed copy. Redaction changes an export; do not use it as
input to report recomputation. For a reproducible sanitized run, replace private
inputs with consistent synthetic fixtures and rerun the whole workflow instead.
Do not assume a pass count or a JSON file contains no personal data.
