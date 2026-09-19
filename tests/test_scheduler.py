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
from reopt.journal import render_seed_journal
from reopt.journal import append_seed_journal
from reopt.export import export_seed_runs_json
from reopt.diff import diff_exports
from reopt.snapshot import write_seed_snapshot


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
        self.assertIn("selected_strategy", data[0])
        self.assertIn("selected_utility", data[0])
        self.assertEqual(data[2]["selected_strategy"], "budget-pruning-v0")

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


if __name__ == "__main__":
    unittest.main()
