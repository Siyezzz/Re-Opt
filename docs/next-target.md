# Next Re-Opt Target

title: Gather evidence for remaining blocked weight increments

rationale: A smaller utility-weight experiment has been adopted, but the larger proposal still contains blocked increments. The next optimization should collect another outcome or split the remaining increments before changing more weights.

Evidence:

- latest_next_refinement=Collect or simulate a filled `outcomes/next-outcome.json` record, then compare whether the remaining blocked token, minute, and missed-optional increments are still negative under the expanded evidence set.
- adopted_reports=adoption-reports/proposed-quality-seed.md
- blocked_reports=adoption-reports/proposed-seed.md

Suggested commands:

- `python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md`
- `python -m reopt.outcome_intake --validate outcomes/next-outcome.json`
- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
