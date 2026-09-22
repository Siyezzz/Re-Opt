import unittest
import json
from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path

from reopt import (
    AgentRole,
    BudgetPruningScheduler,
    HeuristicScheduler,
    format_optimization_run,
    load_seed_benchmarks,
    solve_optimization,
)
from reopt.models import UtilityWeights
from reopt.journal import render_seed_journal
from reopt.journal import append_seed_journal
from reopt.export import export_seed_runs_json
from reopt.diff import diff_exports
from reopt.snapshot import write_seed_snapshot
from reopt.regression import check_seed_baseline, compare_seed_baseline
from reopt.adopt import adoption_checklist
from reopt.calibrate import preview_calibration
from reopt.report_index import render_adoption_index
from reopt.next_target import render_next_target, suggest_next_target
from reopt.explain_adoption import (
    explain_blocked_adoption,
    write_smaller_experiment,
)
from reopt.outcome_intake import (
    render_outcome_intake,
    render_validation_report,
    suggest_outcome_intake,
    validate_outcome_intake,
)
from reopt.evidence_review import (
    review_expanded_evidence,
    simulated_next_outcome,
    write_simulated_outcome,
)
from reopt.observed_evidence import review_observed_evidence
from reopt.increment_cap import find_largest_clean_cap, render_cap_report
from reopt.adoption_decision import decide_adoption, render_decision
from reopt.outcomes import (
    OutcomeRecord,
    calibration_report,
    dump_outcomes,
    dump_utility_weights,
    load_outcomes,
    load_utility_weights,
    propose_utility_weights,
)


class HeuristicSchedulerTest(unittest.TestCase):
    def test_seed_benchmarks_generate_valid_plans(self) -> None:
        scheduler = HeuristicScheduler()

        for graph, constraints in load_seed_benchmarks():
            plan = scheduler.build_plan(graph, constraints)
            self.assertEqual(plan.graph_id, graph.graph_id)
            self.assertEqual(len(plan.steps), len(graph.nodes))
            if plan.estimated_tokens > constraints.token_budget:
                self.assertTrue(plan.warnings)

    def test_role_assignments_include_memory_curator(self) -> None:
        scheduler = HeuristicScheduler()
        graph, constraints = load_seed_benchmarks()[0]

        plan = scheduler.build_plan(graph, constraints)

        self.assertEqual(plan.steps[-1].role, AgentRole.MEMORY_CURATOR)

    def test_budget_pruning_drops_optional_work_under_tight_budget(self) -> None:
        scheduler = BudgetPruningScheduler()
        graph, constraints = load_seed_benchmarks()[2]

        plan = scheduler.build_plan(graph, constraints)
        planned_ids = {step.node_id for step in plan.steps}

        self.assertLessEqual(plan.estimated_tokens, constraints.token_budget)
        self.assertNotIn("secondary_sweep", planned_ids)
        self.assertIn("Dropped optional nodes", plan.warnings[0])

    def test_optimization_run_records_decision_trace(self) -> None:
        graph, constraints = load_seed_benchmarks()[2]

        run = solve_optimization(graph, constraints)
        formatted = format_optimization_run(run)

        self.assertEqual(run.selected_strategy, "budget-pruning-v0")
        self.assertGreaterEqual(len(run.decisions), 4)
        self.assertIn("decisions:", formatted)
        self.assertIn("next_refinement:", formatted)

    def test_seed_journal_renders_markdown(self) -> None:
        journal = render_seed_journal(date(2026, 9, 19))

        self.assertIn("# Optimization Run Journal", journal)
        self.assertIn("## 2026-09-19 - Seed Strategy Selection", journal)
        self.assertIn("Decision trace:", journal)
        self.assertIn("budget-pruning-v0", journal)

    def test_seed_journal_appends_to_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.md"

            append_seed_journal(path, date(2026, 9, 19))
            append_seed_journal(path, date(2026, 9, 20))
            content = path.read_text(encoding="utf-8")

        self.assertIn("## 2026-09-19 - Seed Strategy Selection", content)
        self.assertIn("## 2026-09-20 - Seed Strategy Selection", content)

    def test_seed_runs_export_as_json(self) -> None:
        data = json.loads(export_seed_runs_json())

        self.assertEqual(len(data), 3)
        self.assertIn("candidate_scores", data[0])
        self.assertIn("utility", data[0]["candidate_scores"][0])
        self.assertIn("missed_optional_value", data[0]["candidate_scores"][0])
        self.assertIn("selected_strategy", data[0])
        self.assertIn("selected_utility", data[0])
        self.assertIn("utility_weights", data[0])
        self.assertEqual(data[2]["selected_strategy"], "budget-pruning-v0")
        self.assertGreater(data[2]["candidate_scores"][1]["missed_optional_value"], 0)

    def test_export_diff_reports_strategy_and_utility_changes(self) -> None:
        left = json.loads(export_seed_runs_json())
        right = json.loads(export_seed_runs_json())
        right[2]["selected_strategy"] = "experimental-v1"
        right[2]["selected_utility"] = right[2]["selected_utility"] + 0.5

        diff = diff_exports(left, right)

        self.assertIn("budget-pruning-v0 -> experimental-v1", diff)
        self.assertIn("utility_delta: +0.500", diff)

    def test_seed_snapshot_writes_json_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshots" / "seed.json"

            write_seed_snapshot(path)
            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(len(data), 3)
        self.assertEqual(data[2]["selected_strategy"], "budget-pruning-v0")

    def test_regression_compares_current_against_baseline(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "seed-baseline.json"
            write_seed_snapshot(baseline)

            diff = compare_seed_baseline(baseline)

        self.assertIn("# Optimization Export Diff", diff)
        self.assertIn("strategy: unchanged", diff)
        self.assertIn("utility_delta: +0.000", diff)

    def test_regression_gate_passes_matching_baseline(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "seed-baseline.json"
            write_seed_snapshot(baseline)

            ok, failures, _ = check_seed_baseline(baseline)

        self.assertTrue(ok)
        self.assertEqual(failures, [])

    def test_regression_gate_fails_utility_drop(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "seed-baseline.json"
            write_seed_snapshot(baseline)
            data = json.loads(baseline.read_text(encoding="utf-8"))
            data[0]["selected_utility"] = data[0]["selected_utility"] + 0.25
            baseline.write_text(json.dumps(data), encoding="utf-8")

            ok, failures, _ = check_seed_baseline(baseline)

        self.assertFalse(ok)
        self.assertTrue(any("utility dropped" in failure for failure in failures))

    def test_outcomes_propose_conservative_weight_updates(self) -> None:
        base = UtilityWeights()
        outcome = OutcomeRecord(
            graph_id="tight-research-seed",
            strategy="budget-pruning-v0",
            observed_quality=0.7,
            target_quality=0.8,
            actual_tokens=7600,
            token_budget=7000,
            actual_minutes=70,
            time_budget_minutes=65,
            missed_optional_harm=0.4,
        )

        proposed = propose_utility_weights(base, (outcome,))

        self.assertGreater(proposed.quality, base.quality)
        self.assertGreater(proposed.token, base.token)
        self.assertGreater(proposed.minute, base.minute)
        self.assertGreater(proposed.missed_optional, base.missed_optional)

    def test_outcomes_round_trip_and_report(self) -> None:
        base = UtilityWeights()
        outcome = OutcomeRecord(
            graph_id="tight-research-seed",
            strategy="budget-pruning-v0",
            observed_quality=0.7,
            target_quality=0.8,
            actual_tokens=7600,
            token_budget=7000,
            actual_minutes=70,
            time_budget_minutes=65,
            missed_optional_harm=0.4,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "outcomes.json"

            dump_outcomes(path, (outcome,))
            loaded = load_outcomes(path)
            proposed = propose_utility_weights(base, loaded)
            report = calibration_report(base, proposed, loaded)

        self.assertEqual(loaded, (outcome,))
        self.assertIn("# Utility Weight Calibration", report)
        self.assertIn("tight-research-seed/budget-pruning-v0", report)

    def test_utility_weights_round_trip(self) -> None:
        weights = UtilityWeights(quality=1.05, missed_optional=0.45)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "weights.json"

            dump_utility_weights(path, weights)
            loaded = load_utility_weights(path)

        self.assertEqual(loaded, weights)

    def test_adoption_checklist_reports_clean_or_blocked_status(self) -> None:
        with TemporaryDirectory() as tmp:
            weights_path = Path(tmp) / "weights.json"
            baseline_path = Path(tmp) / "baseline.json"
            dump_utility_weights(weights_path, UtilityWeights(quality=1.1))
            write_seed_snapshot(baseline_path)

            checklist = adoption_checklist(weights_path, baseline_path)

        self.assertIn("# Utility Weight Adoption Checklist", checklist)
        self.assertIn("status: clean", checklist)
        self.assertIn("Required adoption steps:", checklist)

    def test_adoption_checklist_reports_adopted_status(self) -> None:
        with TemporaryDirectory() as tmp:
            weights_path = Path(tmp) / "weights.json"
            baseline_path = Path(tmp) / "baseline.json"
            report_path = Path(tmp) / "adoption.md"
            dump_utility_weights(weights_path, UtilityWeights())
            write_seed_snapshot(baseline_path)

            report = adoption_checklist(weights_path, baseline_path)
            report_path.write_text(report, encoding="utf-8")
            content = report_path.read_text(encoding="utf-8")

        self.assertIn("status: adopted", content)
        self.assertIn("# Optimization Export Diff", content)

    def test_adoption_report_index_summarizes_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "adoption-reports"
            report_dir.mkdir()
            report_path = report_dir / "proposed.md"
            report_path.write_text(
                "\n".join(
                    [
                        "# Utility Weight Adoption Checklist",
                        "",
                        "weights: weights/proposed.json",
                        "baseline: benchmark-results/seed-baseline.json",
                        "status: blocked",
                    ]
                ),
                encoding="utf-8",
            )

            index = render_adoption_index(report_dir)

        self.assertIn("# Adoption Report Index", index)
        self.assertIn("blocked", index)
        self.assertIn("weights/proposed.json", index)

    def test_next_target_prefers_blocked_adoption_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Add an adoption checklist.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )

            target = suggest_next_target(iteration_log, adoption_index)
            rendered = render_next_target(target)

        self.assertIn("blocked adoption", target.title.lower())
        self.assertIn("adoption-reports/proposed.md", rendered)
        self.assertIn("python -m reopt.adopt weights/proposed.json", rendered)

    def test_next_target_advances_to_clean_smaller_experiment(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Explain a blocked proposal.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | clean | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )

            target = suggest_next_target(iteration_log, adoption_index)
            rendered = render_next_target(target)

        self.assertIn("clean smaller", target.title.lower())
        self.assertIn("adoption-reports/proposed-quality.md", rendered)
        self.assertIn("python -m reopt.adopt weights/quality.json", rendered)

    def test_next_target_advances_after_smaller_experiment_is_adopted(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "missing.md"
            cap_review = Path(tmp) / "missing-cap.md"
            decision_report = Path(tmp) / "missing-decision.md"
            observed_review = Path(tmp) / "missing-observed.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Review a clean smaller proposal.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | adopted | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("remaining blocked", target.title.lower())
        self.assertIn("adopted_reports=adoption-reports/proposed-quality.md", rendered)
        self.assertIn("python -m reopt.outcome_intake", rendered)
        self.assertIn("--validate outcomes/next-outcome.json", rendered)
        self.assertIn("python -m reopt.explain_adoption", rendered)

    def test_next_target_advances_after_synthetic_review_stays_blocked(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "review.md"
            cap_review = Path(tmp) / "missing-cap.md"
            decision_report = Path(tmp) / "missing-decision.md"
            observed_review = Path(tmp) / "missing-observed.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Compare expanded evidence.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | adopted | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )
            evidence_review.write_text(
                "source: synthetic simulation\n\nstatus: blocked\n",
                encoding="utf-8",
            )

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("split remaining", target.title.lower())
        self.assertIn("evidence_review=", rendered)
        self.assertIn("weights/proposed-expanded-evidence.json", rendered)

    def test_next_target_advances_after_cap_review_is_clean(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "review.md"
            cap_review = Path(tmp) / "cap.md"
            decision_report = Path(tmp) / "missing-decision.md"
            observed_review = Path(tmp) / "missing-observed.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Split remaining increments.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | adopted | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )
            evidence_review.write_text(
                "source: synthetic simulation\n\nstatus: blocked\n",
                encoding="utf-8",
            )
            cap_review.write_text(
                "largest_clean_ratio: 0.011\n\nstatus: clean\n",
                encoding="utf-8",
            )

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("capped expanded-evidence", target.title.lower())
        self.assertIn("cap_review=", rendered)
        self.assertIn("weights/proposed-capped-expanded-evidence.json", rendered)

    def test_outcome_intake_requests_fresh_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            outcomes_path = Path(tmp) / "outcomes.json"
            next_target_path = Path(tmp) / "next-target.md"
            dump_outcomes(
                outcomes_path,
                (
                    OutcomeRecord(
                        graph_id="tight-research-seed",
                        strategy="budget-pruning-v0",
                        observed_quality=0.7,
                        target_quality=0.8,
                        actual_tokens=7600,
                        token_budget=7000,
                        actual_minutes=70,
                        time_budget_minutes=65,
                        missed_optional_harm=0.4,
                    ),
                ),
            )
            next_target_path.write_text(
                "# Next Re-Opt Target\n\ntitle: Gather evidence\n",
                encoding="utf-8",
            )

            request = suggest_outcome_intake(outcomes_path, next_target_path)
            rendered = render_outcome_intake(request)

        self.assertIn("Collect a new outcome", request.title)
        self.assertIn("tight-research-seed/budget-pruning-v0", rendered)
        self.assertIn('"graph_id": "coding-debug-seed"', rendered)
        self.assertIn("python -m reopt.outcome_intake --validate", rendered)
        self.assertIn("python -m reopt.calibrate outcomes/next-outcome.json", rendered)

    def test_outcome_intake_validation_blocks_placeholders_and_reuse(self) -> None:
        with TemporaryDirectory() as tmp:
            existing_path = Path(tmp) / "existing.json"
            candidate_path = Path(tmp) / "candidate.json"
            existing = OutcomeRecord(
                graph_id="tight-research-seed",
                strategy="budget-pruning-v0",
                observed_quality=0.7,
                target_quality=0.8,
                actual_tokens=7600,
                token_budget=7000,
                actual_minutes=70,
                time_budget_minutes=65,
                missed_optional_harm=0.4,
            )
            dump_outcomes(existing_path, (existing,))
            dump_outcomes(
                candidate_path,
                (
                    existing,
                    OutcomeRecord(
                        graph_id="coding-debug-seed",
                        strategy="critical-path-a-star-v0",
                        observed_quality=0.0,
                        target_quality=0.8,
                        actual_tokens=0,
                        token_budget=12000,
                        actual_minutes=0,
                        time_budget_minutes=90,
                    ),
                ),
            )

            ok, failures = validate_outcome_intake(candidate_path, existing_path)
            report = render_validation_report(ok, failures)

        self.assertFalse(ok)
        self.assertIn("duplicates an existing outcome record", report)
        self.assertIn("actual_tokens must be observed", report)
        self.assertIn("observed_quality must be observed", report)

    def test_evidence_review_keeps_synthetic_probe_separate(self) -> None:
        with TemporaryDirectory() as tmp:
            existing_path = Path(tmp) / "existing.json"
            candidate_path = Path(tmp) / "candidate.json"
            weights_path = Path(tmp) / "proposed.json"
            baseline_path = Path(tmp) / "baseline.json"
            dump_outcomes(
                existing_path,
                (
                    OutcomeRecord(
                        graph_id="tight-research-seed",
                        strategy="budget-pruning-v0",
                        observed_quality=0.7,
                        target_quality=0.8,
                        actual_tokens=7600,
                        token_budget=7000,
                        actual_minutes=70,
                        time_budget_minutes=65,
                        missed_optional_harm=0.4,
                    ),
                ),
            )
            write_simulated_outcome(candidate_path)
            write_seed_snapshot(baseline_path)

            report = review_expanded_evidence(
                candidate_path,
                weights_path,
                existing_path,
                baseline_path,
            )
            proposed = load_utility_weights(weights_path)

        self.assertIn("source: synthetic simulation", report)
        self.assertIn("status: clean", report)
        self.assertIn("do not adopt weights from synthetic evidence alone", report)
        self.assertEqual(proposed.quality, 1.075)
        self.assertEqual(proposed.missed_optional, 0.35)

    def test_increment_cap_finds_largest_clean_ratio(self) -> None:
        with TemporaryDirectory() as tmp:
            proposed_path = Path(tmp) / "proposed.json"
            capped_path = Path(tmp) / "capped.json"
            baseline_path = Path(tmp) / "baseline.json"
            write_seed_snapshot(baseline_path)
            dump_utility_weights(
                proposed_path,
                UtilityWeights(
                    quality=1.075,
                    token=0.0001043,
                    minute=0.01038,
                    missed_optional=0.35,
                ),
            )

            ratio, capped = find_largest_clean_cap(
                load_utility_weights(proposed_path),
                baseline_path,
                step=0.01,
            )
            report = render_cap_report(
                proposed_path,
                capped_path,
                baseline_path,
                step=0.01,
            )
            checklist = adoption_checklist(capped_path, baseline_path)

        self.assertGreater(ratio, 0)
        self.assertLess(ratio, 1)
        self.assertLess(capped.missed_optional, 0.35)
        self.assertIn("largest_clean_ratio:", report)
        self.assertIn("status: clean", checklist)

    def test_adoption_decision_defers_tiny_synthetic_cap(self) -> None:
        with TemporaryDirectory() as tmp:
            weights_path = Path(tmp) / "capped.json"
            cap_review_path = Path(tmp) / "cap.md"
            evidence_review_path = Path(tmp) / "evidence.md"
            baseline_path = Path(tmp) / "baseline.json"
            write_seed_snapshot(baseline_path)
            dump_utility_weights(
                weights_path,
                UtilityWeights(
                    quality=1.050275,
                    token=0.0001,
                    minute=0.0100042,
                    missed_optional=0.2511,
                ),
            )
            cap_review_path.write_text(
                "largest_clean_ratio: 0.011\n\nstatus: clean\n",
                encoding="utf-8",
            )
            evidence_review_path.write_text(
                "source: synthetic simulation\n",
                encoding="utf-8",
            )

            decision = decide_adoption(
                weights_path,
                cap_review_path,
                evidence_review_path,
                baseline_path,
            )
            rendered = render_decision(decision)

        self.assertEqual(decision.decision, "defer")
        self.assertIn("decision: defer", rendered)
        self.assertIn("all_rounded_utility_deltas_zero: True", rendered)

    def test_observed_evidence_review_keeps_source_separate(self) -> None:
        with TemporaryDirectory() as tmp:
            existing_path = Path(tmp) / "existing.json"
            candidate_path = Path(tmp) / "candidate.json"
            weights_path = Path(tmp) / "proposed.json"
            baseline_path = Path(tmp) / "baseline.json"
            dump_outcomes(
                existing_path,
                (
                    OutcomeRecord(
                        graph_id="tight-research-seed",
                        strategy="budget-pruning-v0",
                        observed_quality=0.7,
                        target_quality=0.8,
                        actual_tokens=7600,
                        token_budget=7000,
                        actual_minutes=70,
                        time_budget_minutes=65,
                        missed_optional_harm=0.4,
                    ),
                ),
            )
            dump_outcomes(
                candidate_path,
                (
                    OutcomeRecord(
                        graph_id="coding-debug-seed",
                        strategy="critical-path-a-star-v0",
                        observed_quality=0.95,
                        target_quality=0.8,
                        actual_tokens=10500,
                        token_budget=12000,
                        actual_minutes=80,
                        time_budget_minutes=90,
                        missed_optional_harm=0.0,
                    ),
                ),
            )
            write_seed_snapshot(baseline_path)

            report = review_observed_evidence(
                candidate_path,
                weights_path,
                existing_path,
                baseline_path,
                provenance="commit abc123 with passing tests",
            )

        self.assertIn("source: observed task run", report)
        self.assertIn("provenance: commit abc123 with passing tests", report)
        self.assertIn("status: clean", report)
        self.assertNotIn("synthetic simulation", report)

    def test_next_target_advances_after_capped_decision_is_deferred(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "review.md"
            cap_review = Path(tmp) / "cap.md"
            decision_report = Path(tmp) / "decision.md"
            observed_review = Path(tmp) / "missing-observed.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Review capped proposal.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | adopted | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )
            evidence_review.write_text(
                "source: synthetic simulation\n\nstatus: blocked\n",
                encoding="utf-8",
            )
            cap_review.write_text(
                "largest_clean_ratio: 0.011\n\nstatus: clean\n",
                encoding="utf-8",
            )
            decision_report.write_text("decision: defer\n", encoding="utf-8")

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("observed evidence", target.title.lower())
        self.assertIn("decision_report=", rendered)
        self.assertIn("python -m reopt.outcome_intake", rendered)

    def test_next_target_advances_after_observed_review_stays_blocked(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "review.md"
            cap_review = Path(tmp) / "cap.md"
            decision_report = Path(tmp) / "decision.md"
            observed_review = Path(tmp) / "observed.md"
            iteration_log.write_text(
                "\n".join(
                    [
                        "# Iteration Log",
                        "",
                        "### Next Refinement",
                        "",
                        "Collect a real observed outcome.",
                    ]
                ),
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-quality.md | adopted | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed.md | blocked | weights/proposed.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )
            evidence_review.write_text(
                "source: synthetic simulation\n\nstatus: blocked\n",
                encoding="utf-8",
            )
            cap_review.write_text(
                "largest_clean_ratio: 0.011\n\nstatus: clean\n",
                encoding="utf-8",
            )
            decision_report.write_text("decision: defer\n", encoding="utf-8")
            observed_review.write_text(
                "source: observed task run\n\nstatus: blocked\n",
                encoding="utf-8",
            )

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("observed-backed", target.title.lower())
        self.assertIn("observed_review=", rendered)
        self.assertIn("weights/proposed-observed-evidence.json", rendered)

    def test_next_target_prefers_clean_split_over_blocked_observed_review(self) -> None:
        with TemporaryDirectory() as tmp:
            iteration_log = Path(tmp) / "iteration-log.md"
            adoption_index = Path(tmp) / "adoption-index.md"
            evidence_review = Path(tmp) / "review.md"
            cap_review = Path(tmp) / "cap.md"
            decision_report = Path(tmp) / "decision.md"
            observed_review = Path(tmp) / "observed.md"
            iteration_log.write_text(
                "# Iteration Log\n\n### Next Refinement\n\nSplit observed increments.\n",
                encoding="utf-8",
            )
            adoption_index.write_text(
                "\n".join(
                    [
                        "# Adoption Report Index",
                        "",
                        "| Report | Status | Weights | Baseline |",
                        "| --- | --- | --- | --- |",
                        "| adoption-reports/proposed-observed-quality.md | clean | weights/quality.json | baseline.json |",
                        "| adoption-reports/proposed-observed-evidence.md | blocked | weights/full.json | baseline.json |",
                    ]
                ),
                encoding="utf-8",
            )
            evidence_review.write_text("source: synthetic simulation\n\nstatus: blocked\n", encoding="utf-8")
            cap_review.write_text("largest_clean_ratio: 0.011\n\nstatus: clean\n", encoding="utf-8")
            decision_report.write_text("decision: defer\n", encoding="utf-8")
            observed_review.write_text("source: observed task run\n\nstatus: blocked\n", encoding="utf-8")

            target = suggest_next_target(
                iteration_log,
                adoption_index,
                evidence_review,
                cap_review,
                decision_report,
                observed_review,
            )
            rendered = render_next_target(target)

        self.assertIn("clean smaller", target.title.lower())
        self.assertIn("clean_reports=adoption-reports/proposed-observed-quality.md", rendered)
        self.assertIn("python -m reopt.adopt weights/quality.json", rendered)

    def test_calibration_preview_reports_regression_diff(self) -> None:
        outcome = OutcomeRecord(
            graph_id="tight-research-seed",
            strategy="budget-pruning-v0",
            observed_quality=0.7,
            target_quality=0.8,
            actual_tokens=7600,
            token_budget=7000,
            actual_minutes=70,
            time_budget_minutes=65,
            missed_optional_harm=0.4,
        )
        with TemporaryDirectory() as tmp:
            outcomes_path = Path(tmp) / "outcomes.json"
            baseline_path = Path(tmp) / "baseline.json"
            dump_outcomes(outcomes_path, (outcome,))
            write_seed_snapshot(baseline_path)

            report = preview_calibration(outcomes_path, baseline_path)

        self.assertIn("# Proposed Weight Regression Preview", report)
        self.assertIn("utility_delta:", report)

    def test_explain_adoption_suggests_smaller_clean_experiment(self) -> None:
        with TemporaryDirectory() as tmp:
            weights_path = Path(tmp) / "proposed.json"
            smaller_path = Path(tmp) / "smaller.json"
            baseline_path = Path(tmp) / "baseline.json"
            dump_utility_weights(
                weights_path,
                UtilityWeights(
                    quality=1.05,
                    token=0.0001086,
                    minute=0.01077,
                    missed_optional=0.45,
                ),
            )
            baseline_path.write_text(
                export_seed_runs_json(UtilityWeights(quality=1.0)) + "\n",
                encoding="utf-8",
            )

            report = explain_blocked_adoption(weights_path, baseline_path)
            wrote = write_smaller_experiment(smaller_path, weights_path, baseline_path)
            smaller = load_utility_weights(smaller_path)
            checklist = adoption_checklist(smaller_path, baseline_path)

        self.assertTrue(wrote)
        self.assertIn("# Blocked Adoption Explanation", report)
        self.assertIn("| missed_optional | 0.25 | 0.45 | -0.090 | -0.090 |", report)
        self.assertEqual(smaller, UtilityWeights(quality=1.05))
        self.assertIn("status: clean", checklist)


if __name__ == "__main__":
    unittest.main()
