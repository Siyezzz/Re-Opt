# Re-Opt

Re-Opt is a research notebook for treating multi-agent task delegation as an
optimization problem.

The starting question:

> If shortest-path and search algorithms help us move through stations in a
> graph, what is the equivalent for decomposing a large task across multiple
> agents under token, time, dependency, and quality constraints?

This repo starts from a deliberately imperfect first version and is meant to be
refined over repeated task runs. SEA is the memory layer: each run should leave
behind what was tried, what worked, what failed, and which task features made a
strategy better or worse.

## Current Notes

- [Multi-agent optimization frame](docs/multi-agent-optimization.md)
- [Iteration log](docs/iteration-log.md)

## Run The Seed Optimizer

```bash
python -m reopt.cli
python -m reopt.compare
python -m reopt.journal
python -m reopt.journal --append docs/optimization-runs.md
python -m reopt.export
python -m reopt.snapshot benchmark-results/seed-current.json
python -m reopt.diff previous.json current.json
python -m reopt.regression
python -m reopt.regression --check
python -m reopt.outcomes outcomes/seed-outcomes.json
python -m reopt.outcomes outcomes/seed-outcomes.json --write-weights weights/proposed-seed.json
python -m reopt.calibrate outcomes/seed-outcomes.json
python -m reopt.export --weights weights/proposed-seed.json
python -m reopt.adopt weights/proposed-seed.json
python -m reopt.adopt weights/proposed-seed.json --write-report adoption-reports/proposed-seed.md
python -m reopt.explain_adoption weights/proposed-seed.json --write-report docs/adoption-analysis/proposed-seed.md
python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md
python -m reopt.observed_pipeline --raw-goal-before docs/outcome-evidence/raw-goal-before.json --raw-goal-after docs/outcome-evidence/raw-goal-after.json --graph-id coding-debug-seed --strategy critical-path-a-star-v0 --observed-quality 0.85 --target-quality 0.8 --token-budget 12000 --time-budget-minutes 90 --missed-optional-harm 0.2 --evidence-ref OBSERVED_RUN_POINTER --write-report docs/outcome-evidence/observed-pipeline.md
python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-before.json --write docs/outcome-evidence/goal-before.json
python -m reopt.goal_snapshot --input docs/outcome-evidence/raw-goal-after.json --write docs/outcome-evidence/goal-after.json
python -m reopt.goal_snapshot --before docs/outcome-evidence/goal-before.json --after docs/outcome-evidence/goal-after.json --require-token-over 12000 --require-minute-over 90 --write docs/outcome-evidence/goal-delta.json
python -m reopt.observed_run --graph-id coding-debug-seed --strategy critical-path-a-star-v0 --observed-quality 0.85 --target-quality 0.8 --goal-before docs/outcome-evidence/goal-before.json --goal-after docs/outcome-evidence/goal-after.json --token-budget 12000 --time-budget-minutes 90 --missed-optional-harm 0.2 --evidence-ref OBSERVED_RUN_POINTER --require-signal token --require-signal minute --require-signal missed_optional --write outcomes/next-outcome.json --write-report docs/outcome-evidence/observed-run-capture.md
python -m reopt.quality_review docs/outcome-evidence/quality-review.json --write-report docs/outcome-evidence/quality-review.md
python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-evidence-ref
python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for quality --require-evidence-ref
python -m reopt.observed_evidence --candidate outcomes/next-outcome.json --write-weights weights/proposed-observed-evidence.json --write-report docs/outcome-evidence/observed-next-outcome.md --provenance "commit 69f87f4 Add capped adoption decision; 31 tests passed; regression gate passed"
python -m reopt.explain_adoption weights/proposed-observed-evidence.json --write-report docs/adoption-analysis/proposed-observed-evidence.md --write-smaller-weights weights/proposed-observed-quality.json
python -m reopt.adopt weights/proposed-observed-evidence.json --write-report adoption-reports/proposed-observed-evidence.md
python -m reopt.adopt weights/proposed-observed-quality.json --write-report adoption-reports/proposed-observed-quality.md
python -m reopt.increment_cap weights/proposed-observed-evidence.json --write-weights weights/proposed-capped-observed-evidence.json --write-report docs/weight-caps/observed-evidence.md
python -m reopt.outcome_consumption weights/proposed-observed-quality.json --write-report docs/outcome-consumption/proposed-observed-quality.md
python -m reopt.observed_evidence --candidate outcomes/next-outcome.json --ledger docs/outcome-consumption/ledger.json --write-weights weights/proposed-observed-consumption-aware.json --write-report docs/outcome-evidence/observed-consumption-aware.md --provenance "commit 69f87f4 Add capped adoption decision; 31 tests passed; regression gate passed"
python -m reopt.explain_adoption weights/proposed-observed-consumption-aware.json --write-report docs/adoption-analysis/proposed-consumption-aware.md
python -m reopt.increment_cap weights/proposed-observed-consumption-aware.json --write-weights weights/proposed-capped-consumption-aware.json --write-report docs/weight-caps/consumption-aware.md
python -m reopt.evidence_review --write-simulated --candidate outcomes/simulated-next-outcome.json --write-weights weights/proposed-expanded-evidence.json --write-report docs/outcome-evidence/simulated-next-outcome.md
python -m reopt.increment_cap weights/proposed-expanded-evidence.json --write-weights weights/proposed-capped-expanded-evidence.json --write-report docs/weight-caps/expanded-evidence.md
python -m reopt.adoption_decision --write-report docs/adoption-decisions/capped-expanded-evidence.md
python -m reopt.report_index --write docs/adoption-index.md
python -m reopt.next_target --write docs/next-target.md
python -m unittest discover -s tests
```

The current implementation is intentionally small:

- `reopt.models` defines task graphs, constraints, roles, and schedule plans
- `reopt.scheduler` contains the first critical-path/A*-style heuristic
- `reopt.compare` compares baseline and budget-aware strategies
- `reopt.optimizer` records how a strategy is selected
- `reopt.journal` renders optimization runs as Markdown
- `reopt.export` renders optimization runs as JSON for future evaluation
- `reopt.snapshot` writes JSON exports to a file
- `reopt.diff` compares two JSON exports
- `reopt.regression` compares current seed output against the committed baseline
- `reopt.outcomes` proposes utility-weight updates from observed outcomes
- `reopt.calibrate` previews proposed weights against the regression baseline
- `reopt.calibrate --ledger` excludes already-consumed field signals from calibration
- `reopt.adopt` produces a review checklist for proposed utility weights
- `reopt.explain_adoption` explains blocked weight adoption and proposes smaller experiments
- `reopt.outcome_intake` generates the next fresh outcome-evidence request
- `reopt.outcome_intake --require-unconsumed-for` validates that a filled outcome supplies a new field-specific signal
- `reopt.goal_snapshot` normalizes Codex goal snapshots for observed-run capture
- `reopt.observed_run` captures an observed run from before/after counters or goal snapshots, with optional required-signal checks
- `reopt.observed_pipeline` runs snapshot normalization, capture, validation, and consumption-aware review, with overridable output paths for smoke tests
- `reopt.quality_review` scores observed quality from an explicit rubric before quality evidence is consumed
- `reopt.observed_evidence` reviews fresh observed outcome evidence before adoption
- `reopt.outcome_consumption` blocks repeated use of already-consumed outcome signals
- `reopt.evidence_review` probes expanded outcome evidence before adoption
- `reopt.increment_cap` searches for clean caps on blocked weight increments
- `reopt.adoption_decision` decides whether clean capped increments are meaningful enough to adopt
- `reopt.report_index` summarizes adoption review artifacts
- `reopt.next_target` suggests the next refinement from current artifacts
- `reopt.benchmarks` contains seed tasks for early comparisons
- `tests` checks that the seed plans are valid enough to iterate on
- GitHub Actions runs tests and the regression gate on push and pull requests

## Core Idea

A task can be modeled as a dependency graph:

- nodes are subtasks, checks, decisions, or artifacts
- edges are prerequisites or information flow
- node weights estimate token cost, wall-clock time, risk, and expected value
- agents are execution resources with role-specific strengths and context limits
- the scheduler chooses who does what, in what order, with what budget

The goal is not one universal best workflow. The goal is a learning optimizer
that maps task shape to a good coordination strategy, then updates that mapping
after every observed run.

## First Research Direction

1. Formalize the task graph and constraints.
2. Define a small set of general-purpose agent roles.
3. Compare planning strategies inspired by graph/search algorithms.
4. Record outcomes with SEA so future runs can adapt.
5. Refine the scheduler from observed evidence, not vibes.
