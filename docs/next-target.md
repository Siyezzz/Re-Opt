# Next Re-Opt Target

title: Collect unconsumed outcome evidence before quality adoption

rationale: A clean observed-quality proposal exists, but the consumption audit shows its supporting quality signal has already been used for an earlier adoption. The next optimization should gather new unconsumed quality evidence before raising the quality weight again.

Evidence:

- latest_next_refinement=Run `reopt.observed_pipeline` on a real before/after goal pair, then inspect the generated consumption-aware review before considering any cost-weight changes.
- blocked_reports=adoption-reports/proposed-observed-consumption-aware.md, adoption-reports/proposed-observed-evidence.md, adoption-reports/proposed-seed.md
- clean_reports=adoption-reports/proposed-observed-quality.md
- consumption_audit=docs/outcome-consumption/proposed-observed-quality.md

Suggested commands:

- `python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for quality --require-evidence-ref`
- `python -m reopt.outcome_consumption weights/proposed-observed-quality.json --write-report docs/outcome-consumption/proposed-observed-quality.md`
- `python -m reopt.regression --check`
