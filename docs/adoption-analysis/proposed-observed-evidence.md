# Blocked Adoption Explanation

weights: weights/proposed-observed-evidence.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.015

Weight-level attribution:

| Weight | Baseline | Proposed | Worst utility delta | Total utility delta |
| --- | ---: | ---: | ---: | ---: |
| quality | 1.05 | 1.075 | +0.079 | +0.287 |
| token | 0.0001 | 0.0001043 | -0.047 | -0.113 |
| minute | 0.01 | 0.01038 | -0.040 | -0.098 |
| missed_optional | 0.25 | 0.35 | -0.045 | -0.045 |

Smaller reversible experiment:

- Adopt only `quality` first.
- This keeps every seed utility delta non-negative while preserving the best isolated improvement signal.
- Re-run adoption and regression before replacing the current baseline.

Proposed smaller weights:

- quality: 1.075
- token: 0.0001
- minute: 0.01
- risk: 0.15
- missed_optional: 0.25
- token_overrun_multiplier: 4.0
- minute_overrun: 0.08
