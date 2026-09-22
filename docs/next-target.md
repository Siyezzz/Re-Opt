# Next Re-Opt Target

title: Review the clean smaller adoption experiment

rationale: A blocked proposal now has at least one clean smaller experiment. The next optimization should decide whether to adopt that reversible step or gather more outcome evidence before changing the baseline.

Evidence:

- latest_next_refinement=Review whether to adopt the clean observed quality increment, or first add outcome-consumption tracking so the same evidence cannot repeatedly push quality upward.
- blocked_reports=adoption-reports/proposed-observed-evidence.md, adoption-reports/proposed-seed.md
- clean_reports=adoption-reports/proposed-observed-quality.md

Suggested commands:

- `python -m reopt.adopt weights/proposed-observed-quality.json`
- `python -m reopt.regression --check`
