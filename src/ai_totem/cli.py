"""Offline file-in/file-out command-line interface."""

import argparse
from importlib.resources import files
import json
from pathlib import Path
import sys

from . import __version__
from .baseline import create_baseline
from .challenges import build_challenges, presented_cases
from .evaluator import evaluate
from .report import json_report, markdown_report, pretty
from .schemas import ValidationError, read_json, require


def write_outputs(outputs):
    """Never overwrite data. Preflight all destinations before creating any file."""
    destinations = [Path(path).resolve() for path, _ in outputs]
    require(
        len(set(destinations)) == len(destinations), "Output paths must be distinct"
    )
    require(
        all(not path.exists() for path in destinations),
        "Output exists; choose a new path (files are never overwritten)",
    )
    made = []
    try:
        for path, (_, content) in zip(destinations, outputs):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                made.append(path)
                stream.write(content)
    except OSError:
        for path in made:
            path.unlink(missing_ok=True)
        raise


def parser():
    p = argparse.ArgumentParser(
        prog="ai-totem",
        description="Coding Panda's local continuity checks. No API, network, or overall continuity score.",
        epilog="Example: ai-totem init --id my-totem\nAll default user outputs are stored in .totem/.",
    )
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser(
        "init", help="Create a synthetic starter baseline for explicit editing"
    )
    init.add_argument(
        "--template",
        help="User-supplied baseline JSON; default is the bundled synthetic example",
    )
    init.add_argument(
        "--id", default="my-totem", help="Baseline identifier (default: my-totem)"
    )
    init.add_argument("--output", default=".totem/baseline.json")
    challenge = sub.add_parser(
        "challenge",
        help="Build a repeatable private answer key and assistant-facing prompts",
    )
    challenge.add_argument("--baseline", default=".totem/baseline.json")
    challenge.add_argument(
        "--challenge-set",
        help="Challenge-set JSON; default is the bundled synthetic example",
    )
    challenge.add_argument(
        "--include-ritual",
        action="store_true",
        help="Add the baseline's optional exact-response ritual",
    )
    challenge.add_argument(
        "--output",
        default=".totem/challenges.json",
        help="Private bundle with baseline and answer key",
    )
    challenge.add_argument(
        "--prompts-output",
        default=".totem/prompts.json",
        help="Assistant-facing context and prompts, without checks or reference answers",
    )
    ev = sub.add_parser(
        "evaluate", help="Evaluate explicitly supplied responses; no model is contacted"
    )
    ev.add_argument("--challenges", default=".totem/challenges.json")
    ev.add_argument(
        "--responses", required=True, help="Response JSON with user-supplied session_id"
    )
    ev.add_argument("--output", default=".totem/evaluation.json")
    report = sub.add_parser(
        "report",
        help="Write Markdown and JSON reports, optionally compare a previous run",
    )
    report.add_argument("--evaluation", default=".totem/evaluation.json")
    report.add_argument(
        "--previous",
        help="Previous evaluation JSON or single-run JSON report (same challenge fingerprint)",
    )
    report.add_argument("--markdown", default=".totem/report.md")
    report.add_argument("--json", dest="json_output", default=".totem/report.json")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            template = read_json(args.template) if args.template else None
            write_outputs([(args.output, pretty(create_baseline(template, args.id)))])
            print(
                "Created local baseline. Default template is synthetic; edit and explicitly approve your own facts before use."
            )
        elif args.command == "challenge":
            challenge_set = (
                read_json(args.challenge_set)
                if args.challenge_set
                else json.loads(
                    files("ai_totem")
                    .joinpath("data/challenge-set.example.json")
                    .read_text(encoding="utf-8")
                )
            )
            bundle = build_challenges(
                read_json(args.baseline), challenge_set, args.include_ritual
            )
            write_outputs(
                [
                    (args.output, pretty(bundle)),
                    (args.prompts_output, pretty(presented_cases(bundle))),
                ]
            )
            print(
                "Created repeatable challenges and prompts. Keep the answer-key bundle private; present only prompts and their context."
            )
        elif args.command == "evaluate":
            result = evaluate(read_json(args.challenges), read_json(args.responses))
            write_outputs([(args.output, pretty(result))])
            print("Evaluated supplied responses. Subjective criteria remain unscored.")
        else:
            evaluation = read_json(args.evaluation)
            previous = read_json(args.previous) if args.previous else None
            md, js = markdown_report(evaluation, previous), json_report(
                evaluation, previous
            )
            write_outputs([(args.markdown, md), (args.json_output, js)])
            print(
                "Created Markdown and JSON reports. Review private context and response excerpts before sharing."
            )
    except (ValidationError, OSError, RecursionError):
        # Do not print file names or exception strings containing imported data.
        # Validation messages are authored here and do not contain response text.
        error = sys.exc_info()[1]
        message = (
            str(error)
            if isinstance(error, ValidationError)
            else "File operation or input nesting failed; check paths, permissions, and JSON depth."
        )
        print("ai-totem: " + message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
