# Next Re-Opt Target

title: Collect observed evidence before adopting capped increments

rationale: The capped expanded-evidence proposal is clean but too small to show a benchmark effect, and its supporting evidence is synthetic. The next optimization should collect observed task evidence before changing default utility weights again.

Evidence:

- latest_next_refinement=Collect a real observed outcome record, validate it through outcome intake, and only then rerun calibration or adoption review.
- adopted_reports=adoption-reports/proposed-quality-seed.md
- blocked_reports=adoption-reports/proposed-seed.md
- decision_report=docs/adoption-decisions/capped-expanded-evidence.md

Suggested commands:

- `python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json`
- `python -m reopt.calibrate outcomes/next-outcome.json`
- `python -m reopt.regression --check`
