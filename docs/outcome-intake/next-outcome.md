# Outcome Evidence Intake

title: Collect a new outcome before more weight changes

rationale: The next target asks for evidence before changing the remaining blocked weight increments. A new outcome should come from a different task shape or a fresh run, so calibration does not repeatedly consume the same tight-research observation.

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

Suggested JSON record:

```json
[
  {
    "actual_minutes": 0,
    "actual_tokens": 0,
    "graph_id": "coding-debug-seed",
    "missed_optional_harm": 0.0,
    "observed_quality": 0.0,
    "strategy": "critical-path-a-star-v0",
    "target_quality": 0.8,
    "time_budget_minutes": 90,
    "token_budget": 12000
  }
]
```

Suggested commands:

- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json`
- `python -m reopt.outcomes outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
