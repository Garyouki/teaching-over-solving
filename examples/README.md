# Examples

`example_models.csv` holds two **made-up** tutors in MathTutorBench format.
The numbers are invented to show how the diagnostic reads; they are not
results for any real model.

```bash
tos-diagnostic score examples/example_models.csv --reference \
    --report examples/example_report.md --svg examples/example_scatter.svg
```

`--reference` places your models next to the eight public MathTutorBench models
used in the paper. `example_report.md` and `example_scatter.svg` show the output.

`paper_report.md` and `paper_scatter.svg` are the paper's Study 1, regenerated with
`tos-diagnostic paper --report examples/paper_report.md --svg examples/paper_scatter.svg`.
