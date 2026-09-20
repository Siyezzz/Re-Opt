# Next Re-Opt Target

title: Gather evidence for remaining blocked weight increments

rationale: A smaller utility-weight experiment has been adopted, but the larger proposal still contains blocked increments. The next optimization should collect another outcome or split the remaining increments before changing more weights.

Evidence:

- latest_next_refinement=Gather another outcome record before proposing more utility-weight changes, so the same tight-research outcome is not repeatedly reused to push quality upward.
- adopted_reports=adoption-reports/proposed-quality-seed.md
- blocked_reports=adoption-reports/proposed-seed.md

Suggested commands:

- `python -m reopt.explain_adoption weights/proposed-seed.json`
- `python -m reopt.regression --check`
