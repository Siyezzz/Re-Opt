# Outcome Evidence Intake

title: Collect unconsumed quality evidence

rationale: The next target asks for a quality signal that has not already been used to justify a quality-weight adoption. A fresh outcome should show an observed quality gap before the quality weight is raised again.

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

- At least one new outcome must have observed_quality below target_quality, and that outcome must not already be consumed for quality.

Suggested JSON record:

```json
[
  {
    "actual_minutes": 0,
    "actual_tokens": 0,
    "graph_id": "coding-debug-seed",
    "missed_optional_harm": 0.0,
    "observed_quality": 0.65,
    "strategy": "critical-path-a-star-v0",
    "target_quality": 0.8,
    "time_budget_minutes": 90,
    "token_budget": 12000
  }
]
```

Suggested commands:

- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for quality`
- `python -m reopt.outcomes outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
