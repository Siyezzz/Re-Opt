# Expanded Outcome Evidence Review

candidate: outcomes/simulated-next-outcome.json
existing: outcomes/seed-outcomes.json
proposed_weights: weights/proposed-expanded-evidence.json
source: synthetic simulation

# Outcome Intake Validation

status: clean

# Utility Weight Calibration

outcomes: 2

| Weight | Current | Proposed | Delta |
| --- | ---: | ---: | ---: |
| quality | 1.05 | 1.075 | +0.025000 |
| token | 0.0001 | 0.0001043 | +0.000004 |
| minute | 0.01 | 0.01038 | +0.000380 |
| risk | 0.15 | 0.15 | +0.000000 |
| missed_optional | 0.25 | 0.35 | +0.100000 |
| token_overrun_multiplier | 4.0 | 4.0 | +0.000000 |
| minute_overrun | 0.08 | 0.08 | +0.000000 |

Outcome signals:

- tight-research-seed/budget-pruning-v0: quality_gap=0.100, token_overrun=600, time_overrun=5, missed_optional_harm=0.400
- coding-debug-seed/critical-path-a-star-v0: quality_gap=0.000, token_overrun=0, time_overrun=0, missed_optional_harm=0.000

# Utility Weight Adoption Checklist

weights: weights/proposed-expanded-evidence.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.015

Required adoption steps:

- Review the calibration report and regression preview.
- Confirm strategy changes, utility drops, and warning changes are intended.
- Commit the proposed weights only with an updated baseline snapshot.
- Record the adoption rationale in the iteration log and SEA.

# Optimization Export Diff

## Select a scheduler for: Answer a research question under a tight budget

- strategy: unchanged
- utility_delta: -0.015
- warning_delta: +0

## Select a scheduler for: Debug a failing feature and verify the fix

- strategy: unchanged
- utility_delta: +0.032
- warning_delta: +0

## Select a scheduler for: Research a broad question and synthesize a position

- strategy: unchanged
- utility_delta: +0.018
- warning_delta: +0

Interpretation:

- The synthetic outcome is validation-clean, but it is not observed evidence.
- Treat this review as a planning probe; do not adopt weights from synthetic evidence alone.
