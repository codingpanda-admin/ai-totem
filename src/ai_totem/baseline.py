"""Explicit baseline creation; never inspect conversations or user profiles."""

from copy import deepcopy
from datetime import datetime, timezone
from importlib.resources import files
import json

from .schemas import validate_baseline


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_baseline(template=None, baseline_id="my-totem"):
    if template is None:
        template = json.loads(
            files("ai_totem")
            .joinpath("data/baseline.example.json")
            .read_text(encoding="utf-8")
        )
    data = deepcopy(validate_baseline(template))
    data.update(id=baseline_id, created_at=now())
    return validate_baseline(data)
