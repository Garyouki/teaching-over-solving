# Rubric agency rules (Study 2)

The paper counts a rubric item as:

- an **agency-dimension** item when its metadata involves instruction following
  or calibration to the student's level;
- an **agency-skill** item when its metadata names an explicit tutoring skill:
  asking guiding questions, giving hints, eliciting reflection, or diagnosing
  the learner's state.

Densities are the share of items in a use case with at least one matching tag.
The paper reports, on the public TutorBench sample (30 scenarios, 324 rubric
items):

| Use case | Rubrics | Agency dim. | Agency skill |
|---|---:|---:|---:|
| Adaptive explanation | 108 | 0.583 | 0.139 |
| Assessment/feedback | 109 | 0.688 | 0.294 |
| Active learning | 107 | 0.720 | 0.411 |

## What this package does

`tos-diagnostic rubrics` applies keyword rules to tags you supply. The default
keywords are in `src/tos_diagnostic/rubrics.py` (`DEFAULT_RULES`). To use your
own, write a JSON file:

```json
{
  "agency_dimension": ["instruction following", "calibration to student level"],
  "agency_skill": ["ask guiding questions", "hint", "elicit reflection", "identify misconception"]
}
```

and pass `--rules my_rules.json`.

## Status

The conversion from TutorBench's raw rubric format to tags, and the exact
keyword list used for the paper's Table 2, have **not yet been re-validated**
in this package. Until they are, treat `rubrics` output as a transparent
heuristic for your own tagged rubrics, not as a reproduction of Table 2.
Contributions that reproduce Table 2 exactly are welcome.
