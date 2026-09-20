# Next Re-Opt Target

title: Review the capped expanded-evidence proposal

rationale: The remaining blocked increments now have a capped clean proposal. The next optimization should decide whether this tiny reversible step is meaningful enough to adopt or should wait for observed evidence.

Evidence:

- latest_next_refinement=Review whether the capped expanded-evidence proposal is meaningful enough to adopt, or whether it should wait for observed evidence instead of synthetic planning probes.
- adopted_reports=adoption-reports/proposed-quality-seed.md
- blocked_reports=adoption-reports/proposed-seed.md
- cap_review=docs/weight-caps/expanded-evidence.md

Suggested commands:

- `python -m reopt.adopt weights/proposed-capped-expanded-evidence.json`
- `python -m reopt.regression --check`
