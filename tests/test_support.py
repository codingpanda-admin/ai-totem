"""Only synthetic fixtures; test discovery runs from the repository root."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from ai_totem.challenges import build_challenges

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-01-02T03:04:05Z"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class Fixture(unittest.TestCase):
    def setUp(self):
        self.baseline = load("templates/baseline.example.json")
        self.challenge_set = load("templates/challenge-set.example.json")
        self.responses = load("examples/responses.synthetic.json")

    def bundle(self):
        return build_challenges(self.baseline, self.challenge_set)

    def single(self, index=0):
        self.challenge_set["tests"] = [deepcopy(self.challenge_set["tests"][index])]
        test_id = self.challenge_set["tests"][0]["id"]
        self.responses["responses"] = [
            r for r in self.responses["responses"] if r["test_id"] == test_id
        ]
        return self.challenge_set["tests"][0]
