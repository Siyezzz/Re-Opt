# Blocked Adoption Explanation

weights: weights/proposed-observed-consumption-aware.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.095
- Select a scheduler for: Debug a failing feature and verify the fix: utility dropped by -0.073
- Select a scheduler for: Research a broad question and synthesize a position: utility dropped by -0.087

Weight-level attribution:

| Weight | Baseline | Proposed | Worst utility delta | Total utility delta |
| --- | ---: | ---: | ---: | ---: |
| token | 0.0001 | 0.0001043 | -0.047 | -0.113 |
| minute | 0.01 | 0.01038 | -0.040 | -0.098 |
| missed_optional | 0.25 | 0.35 | -0.045 | -0.045 |

Smaller reversible experiment:

- No single changed weight has non-negative utility deltas across all seed objectives.
