"""Teaching-over-solving gap diagnostic (Study 1 of the paper).

For each model m:

    Solve(m) = mean of the solving-oriented task scores
    Teach(m) = mean of the pedagogy-oriented task scores
    Gap(m)   = Teach(m) - Solve(m)

A positive gap means the model is relatively stronger at teaching than at
solving. A negative gap means the reverse. Across a set of models the
diagnostic also reports how far each model's rank moves between the two
views, and the Pearson and Spearman correlations between the composites,
with a leave-one-out range for Pearson.

The default task grouping is the one used in the paper for MathTutorBench.
Any benchmark with per-model task scores can be used by passing its own
solving and teaching columns.

Pure Python, no third-party dependencies.
"""
from __future__ import annotations

import csv
import json
import math
from importlib import resources
from pathlib import Path

# MathTutorBench grouping used in the paper.
MTB_SOLVE = ("problem_solving", "solution_correctness", "mistake_location",
             "mistake_correction")
MTB_TEACH = ("socratic_questioning", "scaffolding_win_rate", "pedagogy_if_win_rate",
             "scaffolding_hard", "pedagogy_if_hard")
MTB_COLUMNS = MTB_SOLVE + MTB_TEACH

# Column names people commonly use for the same MathTutorBench tasks.
_ALIASES = {
    "problemsolving": "problem_solving",
    "socraticquestioning": "socratic_questioning",
    "solutioncorrectness": "solution_correctness",
    "studentsolutioncorrectness": "solution_correctness",
    "solutionverification": "solution_correctness",
    "mistakelocation": "mistake_location",
    "mistakecorrection": "mistake_correction",
    "scaffoldingwinrate": "scaffolding_win_rate",
    "scaffoldinggeneration": "scaffolding_win_rate",
    "scaffolding": "scaffolding_win_rate",
    "pedagogyifwinrate": "pedagogy_if_win_rate",
    "pedagogyfollowing": "pedagogy_if_win_rate",
    "pedagogyif": "pedagogy_if_win_rate",
    "scaffoldinghard": "scaffolding_hard",
    "scaffoldinggenerationhard": "scaffolding_hard",
    "pedagogyifhard": "pedagogy_if_hard",
    "pedagogyfollowinghard": "pedagogy_if_hard",
}


class DiagnosticError(ValueError):
    """Raised for inputs the diagnostic cannot score."""


# ---------------------------------------------------------------- loading

def _canon(name: str) -> str:
    key = "".join(ch for ch in name.lower() if ch.isalnum())
    return _ALIASES.get(key, name.strip())


def load_scores(path, model_col: str = "model", canonicalize: bool = True) -> list[dict]:
    """Read a CSV with one row per model and one column per task score."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or model_col not in reader.fieldnames:
            raise DiagnosticError(f"{path}: needs a '{model_col}' column")
        rows = []
        for raw in reader:
            row = {"model": raw[model_col].strip()}
            for k, v in raw.items():
                if k == model_col or k is None:
                    continue
                row[_canon(k) if canonicalize else k.strip()] = v
            rows.append(row)
    return rows


def reference_scores() -> list[dict]:
    """The eight public MathTutorBench leaderboard models used in the paper."""
    path = resources.files("tos_diagnostic") / "data" / "mathtutorbench_leaderboard.csv"
    with resources.as_file(path) as p:
        return load_scores(p)


def reference_source() -> dict:
    path = resources.files("tos_diagnostic") / "data" / "mathtutorbench_leaderboard.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _number(value, model, col):
    if value is None or str(value).strip() == "":
        return None
    try:
        x = float(str(value).strip().rstrip("%"))
    except ValueError:
        raise DiagnosticError(f"{model}: '{col}' is not a number: {value!r}") from None
    if str(value).strip().endswith("%"):
        x /= 100.0
    if math.isnan(x):
        return None
    return x


# ---------------------------------------------------------------- statistics

def mean(xs):
    # math.fsum is exactly rounded, so results (and rounding at .xxx5 values)
    # are identical on every Python version. Plain sum() changed in 3.12.
    xs = list(xs)
    return math.fsum(xs) / len(xs) if xs else float("nan")


def pearson(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = mean(x), mean(y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def average_ranks(values):
    """Ranks starting at 1 for the smallest value; ties share their mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(x, y):
    return pearson(average_ranks(x), average_ranks(y))


def leaderboard_ranks(values):
    """1 = highest score. Ties share the best rank (1, 2, 2, 4)."""
    return [1 + sum(1 for w in values if w > v) for v in values]


# ---------------------------------------------------------------- diagnostic

def composites(rows, solve_cols=MTB_SOLVE, teach_cols=MTB_TEACH, allow_missing=False):
    """Compute Solve, Teach, and Gap for each model row."""
    solve_cols, teach_cols = tuple(solve_cols), tuple(teach_cols)
    if not solve_cols or not teach_cols:
        raise DiagnosticError("need at least one solving column and one teaching column")
    overlap = set(solve_cols) & set(teach_cols)
    if overlap:
        raise DiagnosticError(f"columns cannot be in both groups: {sorted(overlap)}")
    seen, out = set(), []
    for row in rows:
        model = row["model"]
        if not model:
            raise DiagnosticError("a row has an empty model name")
        if model in seen:
            raise DiagnosticError(f"duplicate model: {model}")
        seen.add(model)
        parts = {}
        for group, cols in (("solve", solve_cols), ("teach", teach_cols)):
            vals, missing = [], []
            for c in cols:
                if c not in row:
                    missing.append(c)
                    continue
                v = _number(row[c], model, c)
                if v is None:
                    missing.append(c)
                else:
                    vals.append(v)
            if missing and not allow_missing:
                raise DiagnosticError(
                    f"{model}: missing {group} scores for {missing}. "
                    "Pass allow_missing=True (CLI: --allow-missing) to average the "
                    "available scores instead.")
            if not vals:
                raise DiagnosticError(f"{model}: no {group} scores at all")
            parts[group] = (mean(vals), missing)
        solve, teach = parts["solve"][0], parts["teach"][0]
        out.append({
            "model": model,
            "solve": solve,
            "teach": teach,
            "gap": teach - solve,
            "missing": parts["solve"][1] + parts["teach"][1],
            "reference": bool(row.get("_reference")),
        })
    return out


def diagnose(rows, solve_cols=MTB_SOLVE, teach_cols=MTB_TEACH, allow_missing=False) -> dict:
    """Full diagnostic over a set of models."""
    models = composites(rows, solve_cols, teach_cols, allow_missing)
    s = [m["solve"] for m in models]
    t = [m["teach"] for m in models]
    rs, rt = leaderboard_ranks(s), leaderboard_ranks(t)
    for m, a, b in zip(models, rs, rt):
        m["solve_rank"], m["teach_rank"] = a, b
        m["rank_shift"] = a - b  # positive: rises when evaluation moves to teaching
    n = len(models)
    loo = []
    if n >= 4:
        for i in range(n):
            loo.append((models[i]["model"],
                        pearson([v for j, v in enumerate(s) if j != i],
                                [v for j, v in enumerate(t) if j != i])))
    return {
        "n_models": n,
        "solve_columns": list(solve_cols),
        "teach_columns": list(teach_cols),
        "models": models,
        "pearson": pearson(s, t),
        "spearman": spearman(s, t),
        "loo_pearson": loo,
        "loo_pearson_range": ((min(v for _, v in loo), max(v for _, v in loo))
                              if loo else None),
    }


def with_reference(rows):
    """Append the public MathTutorBench models (marked as reference) to user rows.

    User models that share a name with a reference model replace it.
    """
    names = {r["model"] for r in rows}
    ref = [dict(r, _reference=True) for r in reference_scores() if r["model"] not in names]
    return list(rows) + ref
