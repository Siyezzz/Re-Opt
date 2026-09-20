# Blocked Adoption Explanation

weights: weights/proposed-seed.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.190
- Select a scheduler for: Debug a failing feature and verify the fix: utility dropped by -0.145
- Select a scheduler for: Research a broad question and synthesize a position: utility dropped by -0.175

Weight-level attribution:

| Weight | Baseline | Proposed | Worst utility delta | Total utility delta |
| --- | ---: | ---: | ---: | ---: |
| token | 0.0001 | 0.0001086 | -0.094 | -0.226 |
| minute | 0.01 | 0.01077 | -0.081 | -0.196 |
| missed_optional | 0.25 | 0.45 | -0.090 | -0.090 |

Smaller reversible experiment:

- No single changed weight has non-negative utility deltas across all seed objectives.
