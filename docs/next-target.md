# Next Re-Opt Target

title: Split remaining blocked weight increments

rationale: A validation-clean synthetic outcome still leaves the expanded evidence proposal blocked. The next optimization should split or cap the remaining token, minute, and missed-optional increments before any adoption attempt.

Evidence:

- latest_next_refinement=Split or cap the remaining token, minute, and missed-optional increments before any adoption attempt.
- adopted_reports=adoption-reports/proposed-quality-seed.md
- blocked_reports=adoption-reports/proposed-seed.md
- evidence_review=docs/outcome-evidence/simulated-next-outcome.md

Suggested commands:

- `python -m reopt.evidence_review --write-simulated --candidate outcomes/simulated-next-outcome.json --write-weights weights/proposed-expanded-evidence.json --write-report docs/outcome-evidence/simulated-next-outcome.md`
- `python -m reopt.explain_adoption weights/proposed-expanded-evidence.json`
- `python -m reopt.regression --check`
