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
python -m reopt.diff previous.json current.json
python -m unittest discover -s tests
```

The current implementation is intentionally small:

- `reopt.models` defines task graphs, constraints, roles, and schedule plans
- `reopt.scheduler` contains the first critical-path/A*-style heuristic
- `reopt.compare` compares baseline and budget-aware strategies
- `reopt.optimizer` records how a strategy is selected
- `reopt.journal` renders optimization runs as Markdown
- `reopt.export` renders optimization runs as JSON for future evaluation
- `reopt.diff` compares two JSON exports
- `reopt.benchmarks` contains seed tasks for early comparisons
- `tests` checks that the seed plans are valid enough to iterate on

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
