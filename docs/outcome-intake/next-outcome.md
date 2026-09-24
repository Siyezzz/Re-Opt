# Outcome Evidence Intake

title: Collect unconsumed token, minute, missed_optional evidence

rationale: The next target asks for field-specific signals that have not already been used to justify weight adoptions. A fresh outcome should satisfy the listed unconsumed signal checks before any related weight is raised.

Do not reuse:

- tight-research-seed/budget-pruning-v0: tokens=7600/7000, minutes=70/65, quality=0.7/0.8

Required fields:

- graph_id
- strategy
- observed_quality
- target_quality
- actual_tokens
- token_budget
- actual_minutes
- time_budget_minutes
- missed_optional_harm
- evidence_ref

Required signals:

- Each candidate record must include a non-placeholder evidence_ref.
- At least one new outcome must have actual_tokens above token_budget, and that outcome must not already be consumed for token.
- At least one new outcome must have actual_minutes above time_budget_minutes, and that outcome must not already be consumed for minute.
- At least one new outcome must have missed_optional_harm above 0, and that outcome must not already be consumed for missed_optional.

Suggested JSON record:

```json
[
  {
    "actual_minutes": 95,
    "actual_tokens": 13000,
    "evidence_ref": "REPLACE_WITH_OBSERVED_RUN_POINTER",
    "graph_id": "coding-debug-seed",
    "missed_optional_harm": 0.2,
    "observed_quality": 0.85,
    "strategy": "critical-path-a-star-v0",
    "target_quality": 0.8,
    "time_budget_minutes": 90,
    "token_budget": 12000
  }
]
```

Suggested commands:

- `python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-before.json --write docs/outcome-evidence/goal-before.json`
- `python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-after.json --write docs/outcome-evidence/goal-after.json`
- `python -m reopt.observed_run --graph-id coding-debug-seed --strategy critical-path-a-star-v0 --observed-quality 0.85 --target-quality 0.8 --token-budget 12000 --goal-before docs/outcome-evidence/goal-before.json --goal-after docs/outcome-evidence/goal-after.json --time-budget-minutes 90 --missed-optional-harm 0.2 --evidence-ref OBSERVED_RUN_POINTER --require-signal token --require-signal minute --require-signal missed_optional --write outcomes/next-outcome.json --write-report docs/outcome-evidence/observed-run-capture.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for token --require-evidence-ref`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for minute --require-evidence-ref`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for missed_optional --require-evidence-ref`
- `python -m reopt.outcomes outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
