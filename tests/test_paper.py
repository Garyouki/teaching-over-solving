"""The diagnostic must reproduce Study 1 of the paper from the public leaderboard."""
import pytest

from tos_diagnostic import diagnose, reference_scores

# Paper, Table 1: (Solving, Pedagogy) composites.
TABLE_1 = {
    "LearnLM-1.5-Pro": (0.750, 0.594),
    "GPT-4o": (0.695, 0.592),
    "LLaMA3.1-70B-Instruct": (0.593, 0.520),
    "LLaMA3.1-8B-Instruct": (0.427, 0.504),
    "LLaMA3.2-3B-Instruct": (0.453, 0.482),
    "Llemma-7B-ScienceTutor": (0.432, 0.388),
    "Qwen2.5-7B-SocraticLM": (0.350, 0.332),
    "Qwen2.5-Math-7B-Instruct": (0.568, 0.116),
}


@pytest.fixture(scope="module")
def result():
    return diagnose(reference_scores())


def test_table_1_composites(result):
    got = {m["model"]: (round(m["solve"], 3), round(m["teach"], 3)) for m in result["models"]}
    assert got == TABLE_1


def test_correlations(result):
    # The paper prints 0.421; the exact value is 0.4217 (it rounds to 0.422).
    assert result["pearson"] == pytest.approx(0.4217, abs=5e-5)
    assert round(result["spearman"], 3) == 0.690
    lo, hi = result["loo_pearson_range"]
    assert round(lo, 3) == 0.251 and round(hi, 3) == 0.887
    drop, value = max(result["loo_pearson"], key=lambda kv: kv[1])
    assert drop == "Qwen2.5-Math-7B-Instruct" and round(value, 3) == 0.887


def test_rank_shifts_described_in_the_paper(result):
    by = {m["model"]: m for m in result["models"]}
    m = by["LLaMA3.1-8B-Instruct"]
    assert (m["solve_rank"], m["teach_rank"], round(m["gap"], 3)) == (7, 4, 0.077)
    m = by["Qwen2.5-Math-7B-Instruct"]
    assert (m["solve_rank"], m["teach_rank"], round(m["gap"], 3)) == (4, 8, -0.452)
