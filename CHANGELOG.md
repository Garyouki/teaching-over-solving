# Changelog

## 0.1.1

- Fix: composites now use exactly rounded summation (`math.fsum`). On Python 3.10 and 3.11, plain `sum()` put one paper value on the wrong side of a rounding boundary (LLaMA3.1-8B: Solve 0.428 and Gap +0.076 instead of 0.427 and +0.077). Results are now identical on every supported Python version.
- CI runs the tests and the paper reproduction on Python 3.10 to 3.13.

## 0.1.0

- Published on PyPI as `teaching-over-solving`. The command is `tos-diagnostic` (alias: `teaching-over-solving`).
- `tos-diagnostic paper`: reproduces Study 1 of the paper on the public MathTutorBench leaderboard.
- `tos-diagnostic score`: Solve, Teach, and Gap for your own models, with MathTutorBench or custom task groupings.
- Markdown reports and dependency-free SVG scatter plots.
- `tos-diagnostic rubrics`: agency-oriented density for tagged rubric items (Study 2; not yet re-validated against Table 2).
