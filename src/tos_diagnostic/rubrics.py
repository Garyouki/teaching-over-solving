"""Agency-oriented rubric density (Study 2 of the paper).

Given rubric items that carry metadata tags, count how many items reward
agency-preserving tutoring:

- agency-dimension density: share of items with at least one tag about
  instruction following or calibration to the student's level;
- agency-skill density: share of items with at least one explicit tutoring-skill
  tag such as asking guiding questions, giving hints, eliciting reflection, or
  diagnosing the learner's state.

The mapping is a transparent keyword rule on tags, not a human coding study.
Rules can be replaced with a JSON file.

Input is one rubric item per line (JSONL) or per row (CSV):

    {"use_case": "active_learning", "tags": ["instruction following", "ask guiding questions"]}

Status: the paper's Table 2 was computed on the public TutorBench sample.
Converting that dataset's raw rubric format into these tags has not yet been
re-validated against Table 2 in this package. See docs/rubric_rules.md.
"""
from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path

DEFAULT_RULES = {
    "agency_dimension": [
        "instruction following",
        "instruction-following",
        "calibration to student",
        "student level",
        "student-level",
        "calibrat",
    ],
    "agency_skill": [
        "guiding question",
        "hint",
        "elicit",
        "reflection",
        "misconception",
        "learner state",
        "student state",
        "diagnos",
    ],
}


def load_rules(path=None) -> dict:
    if not path:
        return {k: list(v) for k, v in DEFAULT_RULES.items()}
    rules = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("agency_dimension", "agency_skill"):
        if key not in rules or not isinstance(rules[key], list) or not rules[key]:
            raise ValueError(f"rules file needs a non-empty list '{key}'")
    return rules


def load_items(path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        items = [{"use_case": r.get("use_case", "").strip(),
                  "tags": [t.strip() for t in (r.get("tags") or "").split(";") if t.strip()]}
                 for r in rows]
    else:
        with open(path, encoding="utf-8") as f:
            items = [json.loads(line) for line in f if line.strip()]
    for i, it in enumerate(items):
        if not it.get("use_case"):
            raise ValueError(f"item {i}: missing use_case")
        if not isinstance(it.get("tags"), list):
            raise ValueError(f"item {i}: tags must be a list")
    return items


def _matches(tags, keywords):
    low = [str(t).lower() for t in tags]
    return any(k.lower() in t for t in low for k in keywords)


def density(items, rules=None) -> OrderedDict:
    rules = rules or DEFAULT_RULES
    groups = OrderedDict()
    for it in items:
        groups.setdefault(it["use_case"], []).append(it)
    groups["all"] = list(items)
    out = OrderedDict()
    for name, its in groups.items():
        n = len(its)
        dim = sum(_matches(it["tags"], rules["agency_dimension"]) for it in its)
        skill = sum(_matches(it["tags"], rules["agency_skill"]) for it in its)
        out[name] = {"rubrics": n,
                     "agency_dimension": dim / n if n else float("nan"),
                     "agency_skill": skill / n if n else float("nan")}
    return out
