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

## 2026-09-19 - Calibration Preview

### Objective

Evaluate proposed utility weights before adopting them.

### Implementation

Added `python -m reopt.calibrate outcomes/seed-outcomes.json`, which:

1. loads outcome records
2. proposes new utility weights
3. exports seed runs under those proposed weights
4. diffs the proposed-weight export against the committed baseline

### Observed Result

The preview shows which benchmark utilities or strategy choices would change
without mutating defaults or refreshing the baseline.

### Next Refinement

Add an approval path that can adopt proposed weights only after the regression
preview is reviewed and committed with an explicit baseline update.

## 2026-09-19 - Proposed Weight Files

### Objective

Make proposed utility weights portable without adopting them as defaults.

### Implementation

Added:

- `UtilityWeights.to_dict` and `UtilityWeights.from_dict`
- utility-weight JSON load/dump helpers
- `python -m reopt.outcomes outcomes/seed-outcomes.json --write-weights weights/proposed-seed.json`
- `python -m reopt.export --weights weights/proposed-seed.json`

### Observed Result

Proposed weights can now be saved, loaded, and used for benchmark exports while
the default optimizer remains unchanged.

### Next Refinement

Add a command that compares a proposed-weight export against the baseline and
emits an adoption checklist.

## 2026-09-19 - Utility Weight Adoption Checklist

### Objective

Prevent proposed utility weights from being adopted without a review trail.

### Implementation

Added `python -m reopt.adopt weights/proposed-seed.json`, which:

- loads proposed utility weights
- exports seed benchmark runs under those weights
- compares the export against the committed baseline
- reports clean or blocked adoption status
- prints required adoption steps

### Observed Result

The checklist provides a reviewable bridge from proposed weights to intentional
baseline updates without mutating defaults automatically.

### Next Refinement

Persist proposed-weight files in a dedicated `weights/` directory only after
their adoption checklist is reviewed.

## 2026-09-19 - Persistable Adoption Reports

### Objective

Make utility-weight adoption review evidence persistable.

### Implementation

Added:

```bash
python -m reopt.adopt weights/proposed-seed.json --write-report adoption-reports/proposed-seed.md
```

### Observed Result

Adoption checklists can now be written as Markdown reports while still printing
to stdout. Tests cover report persistence with temporary files.

### Next Refinement

Generate a blocked seed adoption report from `outcomes/seed-outcomes.json` and
commit it as an example review artifact.

## 2026-09-19 - Seed Adoption Review Artifact

### Objective

Commit a concrete proposed-weight review artifact.

### Implementation

Generated:

- `weights/proposed-seed.json`
- `adoption-reports/proposed-seed.md`

### Observed Result

The proposed seed weights are blocked because tight-budget research utility
drops by `-0.029`, even though the selected strategy is unchanged. This is a
useful example of the adoption gate refusing a plausible but not-yet-approved
objective-function change.

### Next Refinement

Add a small report index that summarizes active proposed weights, clean reports,
and blocked reports.

## 2026-09-19 - Adoption Report Index

### Objective

Make proposed utility-weight review state easy to scan.

### Implementation

Added:

```bash
python -m reopt.report_index --write docs/adoption-index.md
```

The command scans `adoption-reports/*.md` and renders a table with report path,
status, weight file, and baseline.

### Observed Result

The current index shows `adoption-reports/proposed-seed.md` as `blocked`.

### Next Refinement

Add this index command to CI so adoption reports and their summary cannot drift.

## 2026-09-19 - Adoption Index CI Check

### Objective

Prevent adoption reports and their committed index from drifting.

### Implementation

Updated GitHub Actions to run:

```bash
python -m reopt.report_index --write docs/adoption-index.md
git diff --exit-code docs/adoption-index.md
```

### Observed Result

The same freshness check passes locally after regenerating the index. Future pull
requests that edit adoption reports without updating the index should fail CI.

### Next Refinement

After quota resets, add a lightweight command that explains the next best
refinement target from the iteration log and current blocked artifacts.

## 2026-09-20 - Next Target Suggestion

### Objective

Make Re-Opt resumable after a pause or quota stop.

### Implementation

Added:

```bash
python -m reopt.next_target --write docs/next-target.md
```

The command reads the iteration log and adoption index, then suggests the next
refinement target with evidence and commands.

### Observed Result

Because the current adoption index contains a blocked proposed-weight report,
the next target points at explaining and reducing blocked adoption proposals.

### Next Refinement

Generate and commit the current `docs/next-target.md`, then add a CI freshness
check so the suggestion cannot drift from current artifacts.

## 2026-09-20 - Next Target CI Check

### Objective

Keep the resume target synchronized with current artifacts.

### Implementation

Updated GitHub Actions to run:

```bash
python -m reopt.next_target --write docs/next-target.md
git diff --exit-code docs/next-target.md
```

### Observed Result

The next target points to the current blocked adoption proposal and is now
checked in CI alongside the adoption index.

### Next Refinement

Implement the suggested target: explain why the blocked proposal fails and
derive a smaller reversible experiment that may reduce the blocked utility drop.

## 2026-09-20 - Blocked Adoption Explanation

### Objective

Explain why `weights/proposed-seed.json` is blocked and derive a smaller,
reversible experiment.

### Implementation

Added:

```bash
python -m reopt.explain_adoption weights/proposed-seed.json \
  --write-report docs/adoption-analysis/proposed-seed.md \
  --write-smaller-weights weights/proposed-quality-seed.json
```

The command attributes utility deltas to each changed weight and selects a
single-weight experiment only when every seed objective stays non-negative.

### Observed Result

The original proposal improves two seed objectives but drops the tight research
objective by `-0.029`. Weight-level attribution shows `quality` alone improves
all seed objectives, while `token`, `minute`, and `missed_optional` each create
negative isolated deltas. The smaller `quality=1.05` experiment is clean:

```bash
python -m reopt.adopt weights/proposed-quality-seed.json \
  --write-report adoption-reports/proposed-quality-seed.md
```

### Next Refinement

Decide whether to adopt the clean smaller experiment into the baseline or gather
another outcome record before changing committed utility weights.

## 2026-09-20 - Adopt Quality Weight Increment

### Objective

Review the clean smaller adoption experiment and decide whether it should become
the committed baseline.

### Implementation

Adopted the smaller experiment by setting the default utility `quality` weight
to `1.05` and regenerating:

```bash
python -m reopt.snapshot benchmark-results/seed-baseline.json
python -m reopt.adopt weights/proposed-quality-seed.json \
  --write-report adoption-reports/proposed-quality-seed.md
python -m reopt.explain_adoption weights/proposed-seed.json \
  --write-report docs/adoption-analysis/proposed-seed.md
```

`reopt.adopt` now reports `status: adopted` when proposed weights match the
baseline utility weights.

### Observed Result

The quality-only experiment is now adopted with zero baseline deltas. The
remaining increments in `weights/proposed-seed.json` are all negative against
the new baseline: token, minute, and missed optional penalties no longer contain
a clean single-weight adoption step.

### Next Refinement

Gather another outcome record before proposing more utility-weight changes, so
the same tight-research outcome is not repeatedly reused to push quality upward.

## 2026-09-20 - Outcome Evidence Intake

### Objective

Turn "gather another outcome" into a concrete, reviewable artifact.

### Implementation

Added:

```bash
python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md
```

The command reads existing outcome records and the current next target, then
generates a fresh evidence request with required fields, a suggested JSON
record, commands, and an explicit "do not reuse" list.

### Observed Result

The generated intake blocks accidental reuse of the existing
`tight-research-seed/budget-pruning-v0` outcome and suggests collecting a
fresh `coding-debug-seed/critical-path-a-star-v0` observation before proposing
more utility-weight changes.

### Next Refinement

Add validation for filled outcome-intake records so placeholder values cannot be
mistaken for observed evidence.

## 2026-09-20 - Outcome Intake Validation

### Objective

Prevent placeholder or duplicated outcome records from entering calibration as
fresh evidence.

### Implementation

Extended `reopt.outcome_intake` with:

```bash
python -m reopt.outcome_intake --validate outcomes/next-outcome.json
```

Validation rejects exact reuse of existing outcome records and blocks placeholder
values such as zero observed quality, zero actual tokens, and zero actual
minutes.

### Observed Result

The generated outcome intake now includes validation before calibration. Tests
cover duplicate-record rejection and placeholder-value rejection.

### Next Refinement

Collect or simulate a filled `outcomes/next-outcome.json` record, then compare
whether the remaining blocked token, minute, and missed-optional increments are
still negative under the expanded evidence set.

## 2026-09-20 - Expanded Evidence Simulation

### Objective

Simulate a fresh outcome record and test whether the remaining blocked utility
weight increments become adoptable under expanded evidence.

### Implementation

Added:

```bash
python -m reopt.evidence_review \
  --write-simulated \
  --candidate outcomes/simulated-next-outcome.json \
  --write-weights weights/proposed-expanded-evidence.json \
  --write-report docs/outcome-evidence/simulated-next-outcome.md
```

The command writes a synthetic coding-debug outcome, validates it against the
intake gate, combines it with existing outcomes, proposes expanded-evidence
weights, and renders an adoption checklist.

### Observed Result

The synthetic outcome is validation-clean, but the expanded-evidence proposal is
still blocked: tight research drops by `-0.015`. The probe reduces the severity
of the remaining block, but it does not justify adoption because the evidence is
synthetic and the regression gate still fails.

### Next Refinement

Split or cap the remaining token, minute, and missed-optional increments before
any adoption attempt.

## 2026-09-20 - Increment Cap Search

### Objective

Find the largest reversible cap on the expanded-evidence utility-weight
increments that does not trigger the regression gate.

### Implementation

Added:

```bash
python -m reopt.increment_cap weights/proposed-expanded-evidence.json \
  --write-weights weights/proposed-capped-expanded-evidence.json \
  --write-report docs/weight-caps/expanded-evidence.md
```

The command interpolates from baseline weights to the expanded-evidence proposal
and searches for the largest clean uniform ratio.

### Observed Result

The largest clean cap is only `0.011`, producing a tiny reversible proposal:
`quality=1.050275`, `minute=0.0100042`, `missed_optional=0.2511`, and unchanged
token cost after rounding. The adoption checklist for this capped proposal is
clean, but all selected utility deltas round to `+0.000`.

### Next Refinement

Review whether the capped expanded-evidence proposal is meaningful enough to
adopt, or whether it should wait for observed evidence instead of synthetic
planning probes.

## 2026-09-22 - Capped Adoption Decision

### Objective

Decide whether the clean capped expanded-evidence proposal should actually be
adopted, rather than treating regression-clean as sufficient by itself.

### Implementation

Added:

```bash
python -m reopt.adoption_decision \
  --write-report docs/adoption-decisions/capped-expanded-evidence.md
```

The command combines the capped proposal adoption checklist, cap ratio, and
evidence source into an explicit decision report. `reopt.next_target` now reads
that report before suggesting the next refinement.

### Observed Result

The capped proposal is clean, but the largest clean cap is only `0.011`, every
seed utility delta rounds to `+0.000`, and the supporting evidence is synthetic.
The decision is therefore `defer`: wait for observed task evidence before
changing committed default weights again.

### Next Refinement

Collect a real observed outcome record, validate it through outcome intake, and
only then rerun calibration or adoption review.

## 2026-09-22 - Observed Outcome Evidence

### Objective

Replace the synthetic-only planning probe with a fresh observed outcome from the
completed capped-adoption-decision engineering loop.

### Implementation

Added:

```bash
python -m reopt.observed_evidence \
  --candidate outcomes/next-outcome.json \
  --write-weights weights/proposed-observed-evidence.json \
  --write-report docs/outcome-evidence/observed-next-outcome.md
```

The observed candidate records the `coding-debug-seed/critical-path-a-star-v0`
task shape with provenance pointing to commit `69f87f4`, passing tests, and the
regression gate. The review keeps `source: observed task run` separate from the
synthetic evidence path.

### Observed Result

The new outcome passes intake validation. Combined with the existing
tight-research outcome, it proposes the same directional weight changes as the
synthetic probe: `quality=1.075`, `token=0.0001043`, `minute=0.01038`, and
`missed_optional=0.35`. Adoption is still blocked by a tight-research utility
drop of `-0.015`.

### Next Refinement

Split or cap the observed-backed blocked increments before any adoption attempt.

## 2026-09-22 - Observed Evidence Split

### Objective

Split the observed-backed blocked utility-weight proposal into smaller,
reviewable increments.

### Implementation

Generated:

```bash
python -m reopt.explain_adoption weights/proposed-observed-evidence.json \
  --write-report docs/adoption-analysis/proposed-observed-evidence.md \
  --write-smaller-weights weights/proposed-observed-quality.json
python -m reopt.adopt weights/proposed-observed-quality.json \
  --write-report adoption-reports/proposed-observed-quality.md
python -m reopt.increment_cap weights/proposed-observed-evidence.json \
  --write-weights weights/proposed-capped-observed-evidence.json \
  --write-report docs/weight-caps/observed-evidence.md
```

### Observed Result

The full observed-evidence proposal remains blocked by a `-0.015`
tight-research utility drop. Weight attribution shows `quality` alone has
non-negative utility deltas across all seed objectives, while `token`, `minute`,
and `missed_optional` remain negative. The quality-only observed proposal is
clean; the uniform cap is also clean but only at ratio `0.011`, again too small
to show visible benchmark movement.

### Next Refinement

Review whether to adopt the clean observed quality increment, or first add
outcome-consumption tracking so the same evidence cannot repeatedly push quality
upward.

## 2026-09-22 - Outcome Consumption Guard

### Objective

Prevent the same outcome signal from repeatedly pushing the same utility weight
after it has already justified an adoption.

### Implementation

Added:

```bash
python -m reopt.outcome_consumption weights/proposed-observed-quality.json \
  --write-report docs/outcome-consumption/proposed-observed-quality.md
```

The initial consumption ledger records that the adopted
`weights/proposed-quality-seed.json` change consumed the tight-research quality
gap as evidence for the `quality` field.

### Observed Result

`weights/proposed-observed-quality.json` is regression-clean, but its only
supporting quality signal is the already-consumed tight-research outcome. The
new outcome has no quality gap, so the consumption audit blocks another quality
adoption for now.

### Next Refinement

Collect unconsumed outcome evidence before raising the quality weight again, or
extend calibration so consumed signals are excluded from repeated proposals.

## 2026-09-22 - Unconsumed Evidence Intake

### Objective

Make the next outcome request specific enough to satisfy the consumption guard:
it must collect a new quality signal that has not already been used for a
quality-weight adoption.

### Implementation

Extended `reopt.outcome_intake` so the current next target produces:

```bash
python -m reopt.outcome_intake --validate outcomes/next-outcome.json \
  --require-unconsumed-for quality
```

The rendered intake now includes a required signal: at least one new outcome must
have `observed_quality < target_quality`, and that outcome must not already be
listed as consumed for `quality` in the consumption ledger.

### Observed Result

The generated intake changed from a generic "collect another outcome" request to
`Collect unconsumed quality evidence`. Tests now cover both paths: candidates
without a new quality gap fail the field-specific validation, while a fresh
unconsumed quality-gap record passes.

### Next Refinement

Fill `outcomes/next-outcome.json` with an actual observed task run that provides
an unconsumed quality signal, then rerun observed evidence review and
consumption audit.

## 2026-09-23 - Consumption-Aware Calibration

### Objective

Avoid manufacturing a new observed quality gap when the current evidence only
shows that the old quality signal was already consumed.

### Implementation

Added consumption-aware calibration:

```bash
python -m reopt.observed_evidence \
  --candidate outcomes/next-outcome.json \
  --ledger docs/outcome-consumption/ledger.json \
  --write-weights weights/proposed-observed-consumption-aware.json \
  --write-report docs/outcome-evidence/observed-consumption-aware.md
```

The ledger-aware path excludes consumed field signals before proposing utility
weights.

### Observed Result

The consumed tight-research quality gap is excluded, so `quality` no longer
increases. The remaining token, minute, and missed-optional increments are still
blocked, and no single changed field has non-negative utility deltas. The largest
clean uniform cap is `0.000`, so there is no meaningful reversible increment to
adopt from the current evidence.

### Next Refinement

Collect fresh unconsumed token, minute, and missed-optional evidence before
changing non-quality cost weights.

## 2026-09-23 - Cost Evidence Intake

### Objective

Update the outcome intake request to match the new target: unconsumed
non-quality cost and optional-harm signals.

### Implementation

`reopt.outcome_intake` now reads the next-target suggested commands and generates
field-specific required signals for `token`, `minute`, and `missed_optional`.

### Observed Result

The generated intake now requests an outcome with token overrun, time overrun,
and missed optional harm, each checked with `--require-unconsumed-for`. The
suggested JSON record remains validation-ready for non-target fields while
making the required cost/optional signals explicit.

### Next Refinement

Fill `outcomes/next-outcome.json` with a real observed run that satisfies those
unconsumed non-quality signals, then rerun consumption-aware evidence review.

## 2026-09-23 - Outcome Provenance Gate

### Objective

Prevent suggested or copied JSON records from being mistaken for observed
evidence when the next target requires a real run.

### Implementation

Added an optional per-record `evidence_ref` field to `OutcomeRecord` and made
observed evidence review require a non-placeholder evidence pointer for each
candidate outcome. Outcome intake now renders `evidence_ref` as a required field
and includes `--require-evidence-ref` in validation commands.

### Observed Result

The historical `outcomes/next-outcome.json` now carries the provenance that was
already cited in the observed-evidence report, so existing reports remain
reproducible. The same record still fails the new token/minute/missed-optional
checks because it has no unconsumed cost or optional-harm signal, which keeps the
next target honest instead of treating provenance as enough.

### Next Refinement

Fill `outcomes/next-outcome.json` with a real observed run that has both a
non-placeholder `evidence_ref` and unconsumed token, minute, and missed-optional
signals; then rerun consumption-aware evidence review.

## 2026-09-23 - Observed Run Capture

### Objective

Make the next real outcome easier to collect without hand-entering derived token
and minute deltas.

### Implementation

Added `reopt.observed_run`, which captures an `OutcomeRecord` from before/after
token and minute counters, budgets, quality, missed optional harm, and an
`evidence_ref`. The intake document now suggests this command before validation,
so the next run can be generated from observed counters rather than copied JSON.

### Observed Result

A dry run with example counters produced `actual_tokens=13000` and
`actual_minutes=95`, matching the current required token and minute overrun
shape. The command can also write a capture report beside the outcome record.

### Next Refinement

Run `reopt.observed_run` with actual Codex goal counters from a real task turn,
then validate the resulting `outcomes/next-outcome.json` against token, minute,
missed-optional, and evidence-ref requirements.

## 2026-09-24 - Capture-Time Signal Checks

### Objective

Make `reopt.observed_run` fail fast when a captured run does not satisfy the
next target's required token, minute, or missed-optional signals.

### Implementation

Added `--require-signal token|minute|missed_optional` to `reopt.observed_run`.
The generated intake command now includes all three required signals for the
current cost/optional evidence target.

### Observed Result

A capture with token, minute, and missed-optional overrun passes. A capture with
only token overrun now exits before writing an outcome and reports the missing
minute and missed-optional signals.

### Next Refinement

Run `reopt.observed_run` with actual before/after goal counters and the required
signal flags, then use the resulting outcome to rerun consumption-aware evidence
review.

## 2026-09-24 - Goal Snapshot Capture

### Objective

Connect observed outcome capture to Codex goal counters without requiring manual
token and minute delta entry.

### Implementation

`reopt.observed_run` now accepts `--goal-before` and `--goal-after` JSON files in
the same shape returned by the Codex goal tool. It reads `tokensUsed` and
`timeUsedSeconds`, converts seconds to floor minutes, and derives the
before/after counters used for outcome capture.

### Observed Result

A fixture with `tokensUsed` moving from `1000` to `14000` and
`timeUsedSeconds` moving from `600` to `6300` produces `13000` tokens and
`95` minutes. The generated intake command now references
`docs/outcome-evidence/goal-before.json` and `goal-after.json` instead of raw
counter placeholders.

### Next Refinement

Save real `get_goal` before/after snapshots for a future task turn, run
`reopt.observed_run` from those files, and use the resulting outcome for
consumption-aware evidence review.

## 2026-09-24 - Goal Snapshot Normalization

### Objective

Make before/after goal snapshots easy to save without committing raw objective
text or unrelated goal metadata.

### Implementation

Added `reopt.goal_snapshot`, which reads a Codex `get_goal` JSON object and
writes the minimal shape needed by `reopt.observed_run`: `tokensUsed`,
`timeUsedSeconds`, `status`, and optional `updatedAt`.

### Observed Result

The intake flow now starts by normalizing `raw-goal-before.json` and
`raw-goal-after.json` into stable `goal-before.json` and `goal-after.json`
snapshots. Tests confirm that private objective text is not copied into the
normalized snapshot.

### Next Refinement

Capture actual before/after goal snapshots around a future task turn, normalize
them with `reopt.goal_snapshot`, then run `reopt.observed_run` and
consumption-aware evidence review.
