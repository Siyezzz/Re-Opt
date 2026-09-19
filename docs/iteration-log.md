# Iteration Log

## 2026-09-19 - Seed Frame

### Objective

Record the first version of Re-Opt: a framework for optimizing multi-agent task
delegation under token, time, dependency, and quality constraints.

### Initial Design

The first version models a task as a directed graph and treats role assignment,
execution order, budget allocation, and verification as scheduler decisions.

### Working Hypothesis

For large ambiguous tasks, a role pipeline with Orchestrator, Decomposer,
Researcher, Builder, Critic, Verifier, Synthesizer, and Memory Curator should
produce better quality per run than a single linear agent flow.

### Expected Weakness

The first version is conceptual. It does not yet include:

- a scoring function calibrated by data
- executable scheduler code
- benchmark tasks
- SEA feedback records tied to repeated independent outcomes
- comparisons against simple baselines

### Next Refinement

Create a small benchmark suite with task types such as coding, research,
writing, debugging, and planning. For each task, compare:

- single-agent baseline
- critical-path scheduler
- A*-style heuristic scheduler
- breadth-first discovery followed by parallel execution

Track quality, time, token use, number of corrections, and user satisfaction.

## 2026-09-19 - Executable Seed

### Objective

Move from conceptual notes to a runnable optimizer prototype.

### Implementation

Added:

- task graph, task node, constraint, role, and schedule plan models
- `critical-path-a-star-v0` heuristic scheduler
- two seed benchmark graphs
- CLI output for inspecting schedules
- unit tests for basic schedule validity

### Working Hypothesis

An inspectable heuristic baseline is better than a purely conceptual framework
because every future refinement can compare against it.

### Expected Weakness

The prototype is still greedy. It does not yet:

- estimate parallel wall-clock time
- prune plans when budgets are exceeded
- compare multiple candidate schedules
- learn role weights from SEA outcomes
- score final task quality

### Next Refinement

Add at least one alternative scheduler and a benchmark runner that compares
strategies on the same task graphs.

## 2026-09-19 - First Strategy Comparison

### Objective

Make Re-Opt compare more than one scheduling strategy.

### Implementation

Added:

- `budget-pruning-v0`, a scheduler that removes optional low-priority work when
  the plan exceeds token or time budgets
- a tight-budget research benchmark
- plan scoring with serial minutes, parallel minutes, covered value, and covered
  risk
- `python -m reopt.compare` for side-by-side strategy output

### Observed Result

On the tight research benchmark, the greedy baseline exceeded the token budget.
The budget-pruning scheduler dropped the optional secondary sweep and fit within
the budget.

### Next Refinement

Add a quality penalty for dropping optional work. A scheduler that fits the
budget is not automatically better if it loses important evidence.
