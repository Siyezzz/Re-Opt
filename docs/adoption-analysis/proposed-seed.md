# Blocked Adoption Explanation

weights: weights/proposed-seed.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.029

Weight-level attribution:

| Weight | Baseline | Proposed | Worst utility delta | Total utility delta |
| --- | ---: | ---: | ---: | ---: |
| quality | 1.0 | 1.05 | +0.161 | +0.581 |
| token | 0.0001 | 0.0001086 | -0.094 | -0.225 |
| minute | 0.01 | 0.01077 | -0.081 | -0.195 |
| missed_optional | 0.25 | 0.45 | -0.090 | -0.090 |

Smaller reversible experiment:

- Adopt only `quality` first.
- This keeps every seed utility delta non-negative while preserving the best isolated improvement signal.
- Re-run adoption and regression before replacing the current baseline.

Proposed smaller weights:

- quality: 1.05
- token: 0.0001
- minute: 0.01
- risk: 0.15
- missed_optional: 0.25
- token_overrun_multiplier: 4.0
- minute_overrun: 0.08
