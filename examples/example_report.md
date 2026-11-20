# Example: two made-up tutors next to the public leaderboard

Generated 2026-11-20 with tos-diagnostic 0.1.0. 10 models.

- **Solve** = mean of: `problem_solving`, `solution_correctness`, `mistake_location`, `mistake_correction`
- **Teach** = mean of: `socratic_questioning`, `scaffolding_win_rate`, `pedagogy_if_win_rate`, `scaffolding_hard`, `pedagogy_if_hard`
- **Gap** = Teach − Solve. Positive means relatively stronger at teaching than at solving.

> **Scope.** This is a descriptive diagnostic on benchmark scores. It does not measure student learning, and a small number of models makes the correlations fragile.

## Summary

- Pearson correlation between Solve and Teach: 0.238. Spearman: 0.261.
- Leave-one-out Pearson ranges from 0.083 to 0.400.
- Removing **Qwen2.5-Math-7B-Instruct** changes Pearson the most (to 0.400).
- **example-tutor-A** falls from rank 2 on solving to rank 9 on teaching (gap -0.385).
- **example-tutor-B** rises from rank 6 on solving to rank 1 on teaching (gap +0.073).
- **Qwen2.5-Math-7B-Instruct** falls from rank 5 on solving to rank 10 on teaching (gap -0.452).
- **LLaMA3.1-8B-Instruct** rises from rank 9 on solving to rank 5 on teaching (gap +0.077).
- **Qwen2.5-7B-SocraticLM** rises from rank 10 on solving to rank 8 on teaching (gap -0.018).

## Models

| Model | Solve | Teach | Gap | Solve rank | Teach rank | Shift |
|---|---:|---:|---:|---:|---:|---:|
| LLaMA3.1-8B-Instruct *(reference)* | 0.427 | 0.504 | +0.077 | 9 | 5 | +4 |
| example-tutor-B | 0.537 | 0.610 | +0.073 | 6 | 1 | +5 |
| LLaMA3.2-3B-Instruct *(reference)* | 0.453 | 0.482 | +0.030 | 7 | 6 | +1 |
| Qwen2.5-7B-SocraticLM *(reference)* | 0.350 | 0.332 | -0.018 | 10 | 8 | +2 |
| Llemma-7B-ScienceTutor *(reference)* | 0.432 | 0.388 | -0.044 | 8 | 7 | +1 |
| LLaMA3.1-70B-Instruct *(reference)* | 0.593 | 0.520 | -0.073 | 4 | 4 | 0 |
| GPT-4o *(reference)* | 0.695 | 0.592 | -0.103 | 3 | 3 | 0 |
| LearnLM-1.5-Pro *(reference)* | 0.750 | 0.594 | -0.156 | 1 | 2 | -1 |
| example-tutor-A | 0.705 | 0.320 | -0.385 | 2 | 9 | -7 |
| Qwen2.5-Math-7B-Instruct *(reference)* | 0.568 | 0.116 | -0.452 | 5 | 10 | -5 |

*Reference* rows are the eight public MathTutorBench leaderboard models used in the paper.

![Solve versus Teach](example_scatter.svg)

Points below the diagonal are relatively stronger at solving than at teaching.

## How to read this

A strong solver is not automatically a strong tutor. A large negative gap is a flag to check whether the model gives away answers or skips scaffolding when a learner needs support. Report Solve and Teach separately rather than as one helpfulness score.

## Citation

Yao, Zheng, and Li. *Beyond Helpfulness: A Teaching-over-Solving Diagnostic for Measuring Educational Impact in LLM Tutors.* 5th Workshop on NLP for Positive Impact, 2026.
