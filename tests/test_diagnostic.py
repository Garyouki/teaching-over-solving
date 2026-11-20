import math

import pytest

from tos_diagnostic import DiagnosticError, composites, diagnose, load_scores, with_reference
from tos_diagnostic.diagnostic import leaderboard_ranks, pearson, spearman


def _csv(tmp_path, text, name="s.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_leaderboard_header_aliases(tmp_path):
    p = _csv(tmp_path, "model,Problem Solving,Socratic Questioning,Solution Correctness,"
             "Mistake Location,Mistake Correction,Scaffolding Win Rate,Pedagogy IF Win Rate,"
             "Scaffolding (Hard),Pedagogy IF (Hard)\nm,1,0,1,1,1,0,0,0,0\n")
    m = composites(load_scores(p))[0]
    assert (m["solve"], m["teach"], m["gap"]) == (1.0, 0.0, -1.0)


def test_percent_values(tmp_path):
    p = _csv(tmp_path, "model,a,b\nm,80%,0.4\n")
    m = composites(load_scores(p, canonicalize=False), ["a"], ["b"])[0]
    assert m["solve"] == pytest.approx(0.8) and m["gap"] == pytest.approx(-0.4)


def test_custom_columns_for_another_benchmark(tmp_path):
    p = _csv(tmp_path, "model,accuracy,scaffold,rigor\n"
             "x,0.9,0.5,0.3\ny,0.6,0.7,0.6\nz,0.8,0.4,0.5\nw,0.5,0.6,0.7\n")
    r = diagnose(load_scores(p, canonicalize=False), ["accuracy"], ["scaffold", "rigor"])
    by = {m["model"]: m for m in r["models"]}
    assert by["x"]["teach"] == pytest.approx(0.4)
    assert by["y"]["rank_shift"] == by["y"]["solve_rank"] - by["y"]["teach_rank"]
    assert len(r["loo_pearson"]) == 4


def test_missing_scores_are_errors_unless_allowed(tmp_path):
    p = _csv(tmp_path, "model,a,b,c\nm,0.5,,0.7\n")
    rows = load_scores(p, canonicalize=False)
    with pytest.raises(DiagnosticError, match="missing solve scores"):
        composites(rows, ["a", "b"], ["c"])
    m = composites(rows, ["a", "b"], ["c"], allow_missing=True)[0]
    assert m["solve"] == 0.5 and m["missing"] == ["b"]


def test_bad_inputs(tmp_path):
    with pytest.raises(DiagnosticError, match="duplicate"):
        composites([{"model": "m", "a": "1", "b": "1"}, {"model": "m", "a": "1", "b": "1"}],
                   ["a"], ["b"])
    with pytest.raises(DiagnosticError, match="both groups"):
        composites([{"model": "m", "a": "1"}], ["a"], ["a"])
    with pytest.raises(DiagnosticError, match="not a number"):
        composites([{"model": "m", "a": "x", "b": "1"}], ["a"], ["b"])
    with pytest.raises(DiagnosticError, match="needs a 'model' column"):
        load_scores(_csv(tmp_path, "name,a\nm,1\n"))


def test_reference_merge_lets_user_rows_win():
    rows = with_reference([{"model": "GPT-4o", "problem_solving": "0"}])
    assert len(rows) == 8
    assert sum(1 for r in rows if r.get("_reference")) == 7


def test_small_sets_skip_unstable_statistics():
    r = diagnose([{"model": "a", "x": "0.2", "y": "0.3"},
                  {"model": "b", "x": "0.4", "y": "0.1"}], ["x"], ["y"])
    assert math.isnan(r["pearson"]) and r["loo_pearson_range"] is None


def test_stat_helpers():
    assert pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)
    assert leaderboard_ranks([0.5, 0.9, 0.9, 0.1]) == [3, 1, 1, 4]
