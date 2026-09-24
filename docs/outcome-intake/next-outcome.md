# Outcome Evidence Intake

title: Collect unconsumed quality evidence

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
- At least one new outcome must have observed_quality below target_quality, and that outcome must not already be consumed for quality.

Suggested JSON record:

```json
[
  {
    "actual_minutes": 0,
    "actual_tokens": 0,
    "evidence_ref": "REPLACE_WITH_OBSERVED_RUN_POINTER",
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

- `python -m reopt.observed_pipeline --raw-goal-before docs/outcome-evidence/raw-goal-before.json --raw-goal-after docs/outcome-evidence/raw-goal-after.json --graph-id coding-debug-seed --strategy critical-path-a-star-v0 --observed-quality 0.65 --target-quality 0.8 --token-budget 12000 --time-budget-minutes 90 --missed-optional-harm 0.0 --evidence-ref OBSERVED_RUN_POINTER --require-signal quality --write-report docs/outcome-evidence/observed-pipeline.md`
- `python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-before.json --write docs/outcome-evidence/goal-before.json`
- `python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-after.json --write docs/outcome-evidence/goal-after.json`
- `python -m reopt.goal_snapshot --before docs/outcome-evidence/goal-before.json --after docs/outcome-evidence/goal-after.json --write docs/outcome-evidence/goal-delta.json`
- `python -m reopt.observed_run --graph-id coding-debug-seed --strategy critical-path-a-star-v0 --observed-quality 0.65 --target-quality 0.8 --token-budget 12000 --goal-before docs/outcome-evidence/goal-before.json --goal-after docs/outcome-evidence/goal-after.json --time-budget-minutes 90 --missed-optional-harm 0.0 --evidence-ref OBSERVED_RUN_POINTER --require-signal quality --write outcomes/next-outcome.json --write-report docs/outcome-evidence/observed-run-capture.md`
- `python -m reopt.quality_review docs/outcome-evidence/quality-review.json --write-report docs/outcome-evidence/quality-review.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for quality --require-evidence-ref --quality-review docs/outcome-evidence/quality-review.json`
- `python -m reopt.outcomes outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
