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

Required signals:

- At least one new outcome must have actual_tokens above token_budget, and that outcome must not already be consumed for token.
- At least one new outcome must have actual_minutes above time_budget_minutes, and that outcome must not already be consumed for minute.
- At least one new outcome must have missed_optional_harm above 0, and that outcome must not already be consumed for missed_optional.

Suggested JSON record:

```json
[
  {
    "actual_minutes": 95,
    "actual_tokens": 13000,
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

- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for token`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for minute`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for missed_optional`
- `python -m reopt.outcomes outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
