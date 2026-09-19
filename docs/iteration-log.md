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

## 2026-09-19 - Meta-Optimization Trace

### Objective

Record not just strategy outputs, but how Re-Opt solves the optimization
problem.

### Implementation

Added:

- `OptimizationDecision` and `OptimizationRun`
- `solve_optimization`, which compares candidate schedulers and selects one
  using an explicit utility function
- `format_optimization_run`, which explains model, candidate generation,
  scoring, selection, and next refinement
- `reopt.journal`, which renders optimization runs as Markdown
- `docs/optimization-runs.md`, the first persisted run journal

### Observed Result

The tight-budget benchmark now selects `budget-pruning-v0` because it fits hard
budgets with higher utility than the over-budget greedy baseline. Normal
benchmarks select the simpler greedy baseline because pruning changes nothing.

### Next Refinement

Make the journal append real run results automatically and add a commit-to-commit
comparison so Re-Opt can track whether each revolution improved the optimizer.

## 2026-09-19 - Appendable Journal

### Objective

Reduce the friction of recording optimization runs.

### Implementation

Added `append_seed_journal`, plus a CLI path:

```bash
python -m reopt.journal --append docs/optimization-runs.md
```

### Observed Result

The journal can now be rendered for inspection or appended to a Markdown file.
Tests cover both modes.

### Next Refinement

Prevent duplicate entries for the same benchmark/date pair and add structured
JSON output for machine comparison.

## 2026-09-19 - JSON Optimization Export

### Objective

Make optimization records machine-readable so future evaluators can compare
strategy choices across commits.

### Implementation

Added:

- `optimization_run_to_dict`
- `reopt.export`
- JSON export test coverage

### Observed Result

Seed benchmark runs can now be exported as stable JSON with candidate scores,
selected strategy, decision trace, and next refinement.

### Next Refinement

Add a comparator that reads two JSON exports and reports strategy changes,
utility deltas, and regressions.

## 2026-09-19 - JSON Export Diff

### Objective

Compare optimization records across runs or commits.

### Implementation

Added `reopt.diff`, which compares two JSON exports by objective and reports:

- selected strategy changes
- selected utility delta
- warning count delta

### Observed Result

The test suite now verifies that a changed selected strategy and utility
improvement are surfaced in the diff output.

### Next Refinement

Store export snapshots under a stable benchmark-results directory and compare
the current run against the previous committed snapshot.

## 2026-09-19 - Snapshot Writer

### Objective

Make JSON exports persistent so they can be compared later.

### Implementation

Added `reopt.snapshot`:

```bash
python -m reopt.snapshot benchmark-results/seed-current.json
```

### Observed Result

The snapshot writer creates parent directories and writes the current seed
optimization export as JSON. Tests verify the file can be parsed back and keeps
the expected selected strategy for the tight-budget benchmark.

### Next Refinement

Commit a baseline snapshot and add a command that compares the current generated
snapshot against the committed baseline.

## 2026-09-19 - Baseline Regression Check

### Objective

Turn snapshot export and diffing into a repeatable regression check.

### Implementation

Added:

- committed seed baseline snapshot
- `reopt.regression`, which compares the current generated seed export against
  the baseline

### Observed Result

The regression command reports unchanged strategies and zero utility deltas when
the current optimizer matches the committed baseline.

### Next Refinement

Make regression output fail with a non-zero exit code when utility drops,
warnings increase, or selected strategies change without an explicit approval.

## 2026-09-19 - Regression Gate

### Objective

Make baseline comparison enforceable, not just informational.

### Implementation

Added `python -m reopt.regression --check`, which exits non-zero when:

- selected strategy changes without `--allow-strategy-change`
- selected utility drops
- candidate warnings increase without `--allow-warning-increase`
- objectives are added or removed

### Observed Result

Tests now verify both the passing path and a failing path where the baseline
claims a higher utility than the current optimizer can reproduce.

### Next Refinement

Add a small CI workflow that runs tests and the regression gate on every push.

## 2026-09-19 - CI Regression Gate

### Objective

Make optimizer regression checks automatic on GitHub.

### Implementation

Added `.github/workflows/ci.yml`, which runs:

```bash
python -m unittest discover -s tests
python -m reopt.regression --check
```

on push and pull requests.

### Observed Result

The local commands pass before committing the workflow. The remote workflow will
now provide independent evidence on future pushes and pull requests.

### Next Refinement

Add a badge or CI status note after the first remote run is observed.

## 2026-09-19 - Missed Optional Evidence Penalty

### Objective

Prevent budget pruning from looking better merely because it deletes useful
optional evidence.

### Implementation

Extended `PlanScore` with:

- total value
- value coverage
- missed optional value

Then updated utility scoring:

```text
utility = value - token_cost - latency_cost - risk_cost
          - missed_optional_cost - violation_penalty
```

### Observed Result

The tight-budget benchmark still selects `budget-pruning-v0`, but the selected
utility now reflects that it dropped the optional secondary sweep.

### Next Refinement

Learn the missed-optional penalty from observed task outcomes instead of using a
fixed hand-tuned weight.

## 2026-09-19 - Explicit Utility Weights

### Objective

Make optimizer scoring weights inspectable and eventually learnable.

### Implementation

Added `UtilityWeights` and stored it on every `OptimizationRun`. JSON exports now
include the active weights that produced each selected utility.

### Observed Result

Strategy selection stays unchanged, but exported runs now preserve the scoring
configuration needed for future comparison and calibration.

### Next Refinement

Add outcome records and a calibration routine that proposes utility-weight
updates from observed quality, cost, and risk results.

## 2026-09-19 - Outcome-Based Weight Proposal

### Objective

Start connecting observed task outcomes back into optimizer weights.

### Implementation

Added:

- `OutcomeRecord`
- `propose_utility_weights`

The proposal function is intentionally conservative and does not mutate default
weights. It suggests higher quality, token, minute, or missed-optional penalties
only when observed outcomes show quality gaps, overruns, or harm from omitted
optional work.

### Observed Result

Tests verify that a low-quality, over-budget, over-time outcome with optional
evidence harm increases the relevant weights.

### Next Refinement

Persist outcome records and compare proposed weights against the current default
weights using the regression gate before adopting them.

## 2026-09-19 - Outcome Calibration Report

### Objective

Persist observed outcomes and turn them into a weight-calibration report.

### Implementation

Added:

- outcome JSON load/dump helpers
- `python -m reopt.outcomes outcomes/seed-outcomes.json`
- `outcomes/seed-outcomes.json`, a first synthetic seed outcome
- calibration report tests

### Observed Result

The calibration command proposes higher quality, token, minute, and
missed-optional penalties from a low-quality, over-budget, over-time tight
research outcome. Defaults remain unchanged.

### Next Refinement

Run proposed weights through benchmark exports without adopting them, then
compare against the current baseline to see which strategy choices would change.
