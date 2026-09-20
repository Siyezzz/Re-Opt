# Next Re-Opt Target

title: Explain and reduce blocked adoption proposals

rationale: The current self-evolution loop has at least one blocked proposed weight change. The next optimization should explain why it is blocked and propose a smaller reversible experiment.

Evidence:

- latest_next_refinement=Implement the suggested target: explain why the blocked proposal fails and derive a smaller reversible experiment that may reduce the blocked utility drop.
- blocked_reports=adoption-reports/proposed-seed.md

Suggested commands:

- `python -m reopt.adopt weights/proposed-seed.json`
- `python -m reopt.calibrate outcomes/seed-outcomes.json`
- `python -m reopt.regression --check`
