"""Command-line interface: ``tos-diagnostic <command>``."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .diagnostic import (MTB_SOLVE, MTB_TEACH, DiagnosticError, diagnose, load_scores,
                         reference_scores, reference_source, with_reference)
from .report import render, scatter_svg


def _cols(text):
    return tuple(c.strip() for c in text.split(",") if c.strip())


def _print_table(result):
    print(f"{'model':32s} {'solve':>6s} {'teach':>6s} {'gap':>7s}  rank S->T")
    for m in sorted(result["models"], key=lambda m: m["gap"], reverse=True):
        tag = " (ref)" if m["reference"] else ""
        print(f"{(m['model'] + tag)[:32]:32s} {m['solve']:6.3f} {m['teach']:6.3f} "
              f"{m['gap']:+7.3f}  {m['solve_rank']}->{m['teach_rank']}")
    print(f"pearson {result['pearson']:.4f}   spearman {result['spearman']:.4f}")
    if result["loo_pearson_range"]:
        lo, hi = result["loo_pearson_range"]
        print(f"leave-one-out pearson {lo:.3f} to {hi:.3f}")


def _write_outputs(result, args, title):
    svg_name = None
    if args.svg:
        Path(args.svg).write_text(scatter_svg(result), encoding="utf-8")
        svg_name = Path(args.svg).name
    if args.report:
        Path(args.report).write_text(render(result, title, svg_name), encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    for label, path in (("report", args.report), ("figure", args.svg), ("json", args.json)):
        if path:
            print(f"{label} written to {path}")


def cmd_paper(args):
    src = reference_source()
    print(f"Source: {src['source']}")
    result = diagnose(reference_scores())
    _print_table(result)
    _write_outputs(result, args, "Teaching-over-solving diagnostic: public MathTutorBench "
                                 "leaderboard")


def cmd_score(args):
    rows = load_scores(args.scores, model_col=args.model_col,
                       canonicalize=not (args.solve or args.teach))
    custom = bool(args.solve or args.teach)
    if custom and not (args.solve and args.teach):
        raise DiagnosticError("pass both --solve and --teach, or neither")
    solve = _cols(args.solve) if custom else MTB_SOLVE
    teach = _cols(args.teach) if custom else MTB_TEACH
    if args.reference:
        if custom:
            raise DiagnosticError("--reference only works with the default MathTutorBench columns")
        rows = with_reference(rows)
    result = diagnose(rows, solve, teach, allow_missing=args.allow_missing)
    _print_table(result)
    _write_outputs(result, args, args.title or "Teaching-over-solving diagnostic")


def cmd_rubrics(args):
    from .rubrics import density, load_items, load_rules
    res = density(load_items(args.items), load_rules(args.rules))
    print(f"{'use case':28s} {'rubrics':>7s} {'agency dim.':>12s} {'agency skill':>13s}")
    for name, r in res.items():
        print(f"{name[:28]:28s} {r['rubrics']:7d} {r['agency_dimension']:12.3f} "
              f"{r['agency_skill']:13.3f}")
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"json written to {args.json}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="tos-diagnostic",
        description="Separate how well an LLM tutor solves from how well it teaches.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="command", required=True)

    def outputs(p):
        p.add_argument("--report", help="write a Markdown report here")
        p.add_argument("--svg", help="write a Solve-vs-Teach scatter plot (SVG) here")
        p.add_argument("--json", help="write full results as JSON here")

    p = sub.add_parser("paper", help="reproduce the paper's Study 1 on the public leaderboard")
    outputs(p)
    p.set_defaults(func=cmd_paper)

    p = sub.add_parser("score", help="score your own models from a CSV of task scores")
    p.add_argument("scores", help="CSV: one row per model, one column per task score")
    p.add_argument("--model-col", default="model", help="name of the model column")
    p.add_argument("--solve", help="comma-separated solving columns (custom benchmark)")
    p.add_argument("--teach", help="comma-separated teaching columns (custom benchmark)")
    p.add_argument("--reference", action="store_true",
                   help="compare against the eight public MathTutorBench models")
    p.add_argument("--allow-missing", action="store_true",
                   help="average available scores when some task scores are missing")
    p.add_argument("--title", help="report title")
    outputs(p)
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("rubrics", help="agency-oriented density of tagged rubric items")
    p.add_argument("items", help="JSONL or CSV with use_case and tags per rubric item")
    p.add_argument("--rules", help="JSON file with agency_dimension and agency_skill keywords")
    p.add_argument("--json", help="write results as JSON here")
    p.set_defaults(func=cmd_rubrics)

    args = ap.parse_args(argv)
    try:
        args.func(args)
    except DiagnosticError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
