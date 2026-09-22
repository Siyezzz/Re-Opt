# Utility Weight Adoption Checklist

weights: weights/proposed-observed-evidence.json
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
