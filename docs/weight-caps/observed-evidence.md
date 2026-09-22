# Utility Increment Cap Review

proposed_weights: weights/proposed-observed-evidence.json
baseline: benchmark-results/seed-baseline.json
capped_weights: weights/proposed-capped-observed-evidence.json
largest_clean_ratio: 0.011

Changed weights:

| Weight | Baseline | Proposed | Capped |
| --- | ---: | ---: | ---: |
| quality | 1.05 | 1.075 | 1.050275 |
| token | 0.0001 | 0.0001043 | 0.0001 |
| minute | 0.01 | 0.01038 | 0.0100042 |
| missed_optional | 0.25 | 0.35 | 0.2511 |

# Utility Weight Adoption Checklist

weights: weights/proposed-capped-observed-evidence.json
baseline: benchmark-results/seed-baseline.json
status: clean

Required adoption steps:

- Review the calibration report and regression preview.
- Confirm strategy changes, utility drops, and warning changes are intended.
- Commit the proposed weights only with an updated baseline snapshot.
- Record the adoption rationale in the iteration log and SEA.

# Optimization Export Diff

## Select a scheduler for: Answer a research question under a tight budget

- strategy: unchanged
- utility_delta: +0.000
- warning_delta: +0

## Select a scheduler for: Debug a failing feature and verify the fix

- strategy: unchanged
- utility_delta: +0.000
- warning_delta: +0

## Select a scheduler for: Research a broad question and synthesize a position

- strategy: unchanged
- utility_delta: +0.000
- warning_delta: +0
