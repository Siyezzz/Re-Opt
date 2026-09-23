# Next Re-Opt Target

title: Collect unconsumed cost and optional-harm evidence

rationale: Consumption-aware calibration removes the already-consumed quality signal, and the remaining token, minute, and missed-optional increments have no clean cap. The next optimization should gather fresh unconsumed evidence for those non-quality signals before changing cost weights.

Evidence:

- latest_next_refinement=Fill `outcomes/next-outcome.json` with a real observed run that has both a non-placeholder `evidence_ref` and unconsumed token, minute, and missed-optional signals; then rerun consumption-aware evidence review.
- blocked_reports=adoption-reports/proposed-observed-consumption-aware.md, adoption-reports/proposed-observed-evidence.md, adoption-reports/proposed-seed.md
- consumption_aware_cap=docs/weight-caps/consumption-aware.md

Suggested commands:

- `python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for token --require-evidence-ref`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for minute --require-evidence-ref`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for missed_optional --require-evidence-ref`
- `python -m reopt.regression --check`
