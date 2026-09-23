# Utility Weight Adoption Checklist

weights: weights/proposed-observed-consumption-aware.json
baseline: benchmark-results/seed-baseline.json
status: blocked

Blocking regression signals:

- Select a scheduler for: Answer a research question under a tight budget: utility dropped by -0.095
- Select a scheduler for: Debug a failing feature and verify the fix: utility dropped by -0.073
- Select a scheduler for: Research a broad question and synthesize a position: utility dropped by -0.087

Required adoption steps:

- Review the calibration report and regression preview.
- Confirm strategy changes, utility drops, and warning changes are intended.
- Commit the proposed weights only with an updated baseline snapshot.
- Record the adoption rationale in the iteration log and SEA.

# Optimization Export Diff

## Select a scheduler for: Answer a research question under a tight budget

- strategy: unchanged
- utility_delta: -0.095
- warning_delta: +0

## Select a scheduler for: Debug a failing feature and verify the fix

- strategy: unchanged
- utility_delta: -0.073
- warning_delta: +0

## Select a scheduler for: Research a broad question and synthesize a position

- strategy: unchanged
- utility_delta: -0.087
- warning_delta: +0
