"""Markdown report and SVG scatter plot for the gap diagnostic."""
from __future__ import annotations

import datetime
import math
from xml.sax.saxutils import escape

from . import __version__


def _f(x, d=3, sign=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def render(result: dict, title: str = "Teaching-over-solving diagnostic",
           svg_name: str | None = None) -> str:
    models = sorted(result["models"], key=lambda m: m["gap"], reverse=True)
    has_ref = any(m["reference"] for m in models)
    lines = []
    w = lines.append
    w(f"# {title}")
    w("")
    w(f"Generated {datetime.date.today().isoformat()} with tos-diagnostic {__version__}. "
      f"{result['n_models']} models.")
    w("")
    w("- **Solve** = mean of: " + ", ".join(f"`{c}`" for c in result["solve_columns"]))
    w("- **Teach** = mean of: " + ", ".join(f"`{c}`" for c in result["teach_columns"]))
    w("- **Gap** = Teach − Solve. Positive means relatively stronger at teaching than at "
      "solving.")
    w("")
    w("> **Scope.** This is a descriptive diagnostic on benchmark scores. It does not "
      "measure student learning, and a small number of models makes the correlations "
      "fragile.")
    w("")

    w("## Summary")
    w("")
    w(f"- Pearson correlation between Solve and Teach: {_f(result['pearson'])}. "
      f"Spearman: {_f(result['spearman'])}.")
    if result["loo_pearson_range"]:
        lo, hi = result["loo_pearson_range"]
        w(f"- Leave-one-out Pearson ranges from {_f(lo)} to {_f(hi)}.")
        drop, val = max(result["loo_pearson"], key=lambda kv: abs(kv[1] - result["pearson"]))
        w(f"- Removing **{drop}** changes Pearson the most (to {_f(val)}).")
    movers = [m for m in models if abs(m["rank_shift"]) >= 2]
    for m in sorted(movers, key=lambda m: -abs(m["rank_shift"])):
        direction = "rises" if m["rank_shift"] > 0 else "falls"
        w(f"- **{m['model']}** {direction} from rank {m['solve_rank']} on solving to rank "
          f"{m['teach_rank']} on teaching (gap {_f(m['gap'], sign=True)}).")
    if not movers:
        w("- No model moves two or more ranks between the two views.")
    w("")

    w("## Models")
    w("")
    head = "| Model | Solve | Teach | Gap | Solve rank | Teach rank | Shift |"
    sep = "|---|---:|---:|---:|---:|---:|---:|"
    w(head)
    w(sep)
    for m in models:
        name = m["model"] + (" *(reference)*" if m["reference"] else "")
        if m["missing"]:
            name += " †"
        w(f"| {name} | {_f(m['solve'])} | {_f(m['teach'])} | {_f(m['gap'], sign=True)} | "
          f"{m['solve_rank']} | {m['teach_rank']} | {m['rank_shift']:+d} |".replace("| +0 |", "| 0 |"))
    w("")
    if has_ref:
        w("*Reference* rows are the eight public MathTutorBench leaderboard models used in "
          "the paper.")
    if any(m["missing"] for m in models):
        w("† Averaged over the available scores only; some task scores were missing.")
    w("")
    if svg_name:
        w(f"![Solve versus Teach]({svg_name})")
        w("")
        w("Points below the diagonal are relatively stronger at solving than at teaching.")
        w("")

    w("## How to read this")
    w("")
    w("A strong solver is not automatically a strong tutor. A large negative gap is a "
      "flag to check whether the model gives away answers or skips scaffolding when a "
      "learner needs support. Report Solve and Teach separately rather than as one "
      "helpfulness score.")
    w("")
    w("## Citation")
    w("")
    w("Yao, Zheng, and Li. *Beyond Helpfulness: A Teaching-over-Solving Diagnostic for "
      "Measuring Educational Impact in LLM Tutors.* 5th Workshop on NLP for Positive "
      "Impact, 2026.")
    w("")
    return "\n".join(lines)


def scatter_svg(result: dict, width: int = 640, height: int = 520) -> str:
    """Solve (x) versus Teach (y) with the diagonal. No dependencies."""
    pad_l, pad_r, pad_t, pad_b = 64, 24, 24, 56
    pw, ph = width - pad_l - pad_r, height - pad_t - pad_b
    vals = [v for m in result["models"] for v in (m["solve"], m["teach"])]
    lo = max(0.0, math.floor(min(vals) * 10) / 10 - 0.05)
    hi = min(1.0, math.ceil(max(vals) * 10) / 10 + 0.05)
    if hi - lo < 0.2:
        hi = lo + 0.2

    def sx(v):
        return pad_l + (v - lo) / (hi - lo) * pw

    def sy(v):
        return pad_t + (1 - (v - lo) / (hi - lo)) * ph

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif" '
         f'font-size="12">',
         f'<rect width="{width}" height="{height}" fill="#ffffff"/>']
    tick = math.ceil(lo * 10) / 10
    while tick <= hi + 1e-9:
        x, y = sx(tick), sy(tick)
        o.append(f'<line x1="{x:.1f}" y1="{pad_t}" x2="{x:.1f}" y2="{pad_t + ph}" '
                 f'stroke="#eeeeee"/>')
        o.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + pw}" y2="{y:.1f}" '
                 f'stroke="#eeeeee"/>')
        o.append(f'<text x="{x:.1f}" y="{pad_t + ph + 18}" text-anchor="middle" '
                 f'fill="#555555">{tick:.1f}</text>')
        o.append(f'<text x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" '
                 f'fill="#555555">{tick:.1f}</text>')
        tick = round(tick + 0.1, 10)
    o.append(f'<rect x="{pad_l}" y="{pad_t}" width="{pw}" height="{ph}" fill="none" '
             f'stroke="#999999"/>')
    o.append(f'<line x1="{sx(lo):.1f}" y1="{sy(lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}" '
             f'stroke="#999999" stroke-dasharray="4 4"/>')
    o.append(f'<text x="{pad_l + pw / 2}" y="{height - 16}" text-anchor="middle" '
             f'fill="#222222">Solve composite</text>')
    o.append(f'<text transform="translate(18 {pad_t + ph / 2}) rotate(-90)" '
             f'text-anchor="middle" fill="#222222">Teach composite</text>')
    points = [(sx(m["solve"]), sy(m["teach"]), m) for m in result["models"]]
    for x, y, m in points:
        color = "#9aa5b1" if m["reference"] else "#2563eb"
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"/>')

    # Greedy label placement: try four spots around each point and keep the
    # first one that does not overlap a placed label or a point.
    placed = []

    def crowding(box):
        """None if the label leaves the canvas, else how many things it overlaps."""
        x0, y0, x1, y1 = box
        if x0 < 4 or x1 > width - 4 or y0 < pad_t or y1 > pad_t + ph:
            return None
        hits = sum(1 for b in placed
                   if not (x1 < b[0] or x0 > b[2] or y1 < b[1] or y0 > b[3]))
        hits += sum(1 for px, py, _ in points
                    if x0 - 9 < px < x1 + 9 and y0 - 9 < py < y1 + 9)
        return hits

    for x, y, m in sorted(points, key=lambda p: (p[1], p[0])):
        label = m["model"]
        tw, th = 6.6 * len(label), 12
        spots = [("start", x + 8, y - 6), ("start", x + 8, y + 16),
                 ("end", x - 8, y - 6), ("end", x - 8, y + 16),
                 ("start", x + 8, y - 20), ("end", x - 8, y - 20),
                 ("start", x + 8, y + 30), ("end", x - 8, y + 30)]
        best = None
        for order, (anchor, tx, ty) in enumerate(spots):
            x0 = tx if anchor == "start" else tx - tw
            box = (x0, ty - th, x0 + tw, ty + 2)
            score = crowding(box)
            if score is None:
                continue
            if best is None or (score, order) < best[0]:
                best = ((score, order), (anchor, tx, ty, box))
            if score == 0:
                break
        if best is None:  # nothing fits on the canvas: place left of the point
            anchor, tx, ty = "end", x - 8, y - 6
            best = (None, (anchor, tx, ty, (tx - tw, ty - th, tx, ty + 2)))
        chosen = best[1]
        anchor, tx, ty, box = chosen
        placed.append(box)
        # Leader line from the point to the nearest corner of its label.
        lx = box[0] if anchor == "start" else box[2]
        ly = box[3] if ty < y else box[1]
        o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" '
                 f'stroke="#bbbbbb" stroke-width="0.8"/>')
        o.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" '
                 f'fill="#222222">{escape(label)}</text>')
    o.append("</svg>")
    return "\n".join(o)
