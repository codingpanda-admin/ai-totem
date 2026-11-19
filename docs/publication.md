# Publication readiness — v0.1.0

Prepared on November 19, 2026. **Public publication approved by the user.**

Confirmed destination: [codingpanda-admin/ai-totem](https://github.com/codingpanda-admin/ai-totem).
The owner account was verified and the public repository created after approval.
The user explicitly authorized source push and the v0.1.0 GitHub release after
CI passes. The originally proposed owner was unavailable; the user selected this
destination instead. PyPI publication is outside this request.

Live publication status is available in [Actions](https://github.com/codingpanda-admin/ai-totem/actions)
and [Releases](https://github.com/codingpanda-admin/ai-totem/releases).

## Repository contents for review

```text
ai-totem/
  README.md, SKILL.md, LICENSE, pyproject.toml, MANIFEST.in
  .gitignore, .gitattributes
  .github/workflows/tests.yml
  agents/openai.yaml
  src/ai_totem/
    __init__.py, cli.py, baseline.py, challenges.py
    evaluator.py, report.py, schemas.py
    data/                         packaged synthetic defaults
  templates/                      editable synthetic baseline/challenge set
  examples/                       synthetic replies, ritual, generated report
  tests/                          64 offline unittest cases
  docs/
    schemas.md, methodology.md, privacy.md, limitations.md
    publication.md, release-notes-v0.1.0.md
```

## Completed checks

- [x] Implemented all four CLI commands and evaluation dimensions.
- [x] Validated skill metadata with skill-creator's `quick_validate.py`.
- [x] Ran all **64 tests successfully on Windows with Python 3.14.6**.
- [x] Built a universal Python wheel with standard packaging tools.
- [x] Installed the wheel with `pip --no-index` into a fresh virtual environment;
  confirmed the imported module came from that environment's `site-packages`.
- [x] Independently installed the source with `pip install .` in another fresh
  environment and ran the documented init → challenge → evaluate → report workflow.
- [x] Repeated all 64 tests in each installed environment and ran `pip check`.
- [x] Verified that package metadata declares zero runtime dependencies and that
  packaged templates match the editable source examples.
- [x] Confirmed `.totem/` and conventional private file names are ignored by Git.
- [x] Reviewed imported-text handling, absence of network/eval/transcript execution,
  private report contents, no-overwrite behavior, and synthetic-only fixtures.
- [x] Scanned staged publication files for common credential formats, private-key
  blocks, email addresses, and absolute home-directory paths; no matches found.
  Also reviewed the generated files for real conversations or user details.
  This bounded scan is not a guarantee that arbitrary future additions are safe.
- [x] Prepared the MIT license, README, methodology, privacy/limitations documents,
  synthetic report, source archive, wheel, and release-notes draft.

CI is configured for Windows and Linux with Python 3.11–3.14. Before the initial
push, remote jobs had not run. Release publication requires all matrix jobs to
pass for the exact release commit. Local verification used 3.14.6. The CLI makes no model calls and the
fixture results are a demonstration, not evidence of any assistant's continuity.

## Approval received

- [x] Confirm the intended GitHub owner and repository name.
- [x] Approve **public** repository creation or use of that exact destination.
- [x] Approve pushing this reviewed source, tagging `v0.1.0`, and creating a GitHub
  release using [the prepared release notes](release-notes-v0.1.0.md).

## Publication sequence

Verify authenticated access and whether the destination already exists. If an
existing repository has unrelated contents or the approved owner is unavailable,
stop and resolve that discrepancy before modifying it. Recheck staged files,
run the full test suite, make the initial local commit using the user's intended
Git identity, and push only the reviewed branch to the confirmed destination.
Do not force-push. Confirm CI passes before creating the v0.1.0 tag and release.
Attach the built distributions and checksums if desired within the approval.

Reports can contain private text, context, and full input provenance. Never add
local `.totem/` runs, installation logs, virtual environments, or credentials to
the public repository. Keep release artifacts separate from local user data.
