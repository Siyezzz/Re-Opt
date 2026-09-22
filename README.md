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
- `reopt.adopt` produces a review checklist for proposed utility weights
- `reopt.explain_adoption` explains blocked weight adoption and proposes smaller experiments
- `reopt.outcome_intake` generates the next fresh outcome-evidence request
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
