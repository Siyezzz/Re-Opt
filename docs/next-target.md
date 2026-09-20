# Next Re-Opt Target

title: Review the clean smaller adoption experiment

rationale: A blocked proposal now has at least one clean smaller experiment. The next optimization should decide whether to adopt that reversible step or gather more outcome evidence before changing the baseline.

Evidence:

- latest_next_refinement=Decide whether to adopt the clean smaller experiment into the baseline or gather another outcome record before changing committed utility weights.
- blocked_reports=adoption-reports/proposed-seed.md
- clean_reports=adoption-reports/proposed-quality-seed.md

Suggested commands:

- `python -m reopt.adopt weights/proposed-quality-seed.json`
- `python -m reopt.regression --check`
