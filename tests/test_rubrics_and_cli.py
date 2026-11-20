import json
import xml.dom.minidom
from pathlib import Path

import pytest

from tos_diagnostic.cli import main
from tos_diagnostic.rubrics import density, load_items, load_rules

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_rubric_density_on_tagged_items():
    res = density(load_items(EXAMPLES / "example_rubrics.jsonl"))
    assert res["active_learning"]["rubrics"] == 3
    assert res["active_learning"]["agency_dimension"] == pytest.approx(2 / 3)
    assert res["active_learning"]["agency_skill"] == pytest.approx(2 / 3)
    assert res["adaptive_explanation"]["agency_skill"] == 0.0
    assert res["all"]["rubrics"] == 5


def test_rubric_csv_and_custom_rules(tmp_path):
    csv_path = tmp_path / "r.csv"
    csv_path.write_text("use_case,tags\nu,custom tag;other\nu,none\n")
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"agency_dimension": ["custom"], "agency_skill": ["zzz"]}))
    res = density(load_items(csv_path), load_rules(rules))
    assert res["u"]["agency_dimension"] == 0.5 and res["u"]["agency_skill"] == 0.0
    rules.write_text(json.dumps({"agency_dimension": []}))
    with pytest.raises(ValueError):
        load_rules(rules)


def test_paper_command_writes_report_and_valid_svg(tmp_path, capsys):
    rep, svg, js = tmp_path / "r.md", tmp_path / "f.svg", tmp_path / "r.json"
    main(["paper", "--report", str(rep), "--svg", str(svg), "--json", str(js)])
    out = capsys.readouterr().out
    assert "pearson 0.4217" in out and "spearman 0.6905" in out
    text = rep.read_text()
    assert "Qwen2.5-Math-7B-Instruct** falls from rank 4 on solving to rank 8" in text
    assert "![Solve versus Teach](f.svg)" in text
    xml.dom.minidom.parseString(svg.read_text())  # well-formed
    assert json.loads(js.read_text())["n_models"] == 8


def test_score_with_reference(tmp_path, capsys):
    rep = tmp_path / "r.md"
    main(["score", str(EXAMPLES / "example_models.csv"), "--reference", "--report", str(rep)])
    text = rep.read_text()
    assert "example-tutor-A" in text and "*(reference)*" in text
    assert "10 models" in text


def test_score_errors_exit_cleanly(tmp_path, capsys):
    bad = tmp_path / "b.csv"
    bad.write_text("model,problem_solving\nm,0.5\n")
    with pytest.raises(SystemExit) as e:
        main(["score", str(bad)])
    assert e.value.code == 2
    assert "missing" in capsys.readouterr().err
