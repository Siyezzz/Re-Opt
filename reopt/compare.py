"""Compare scheduler strategies on seed benchmarks."""

from __future__ import annotations

from .benchmarks import load_seed_benchmarks
from .evaluate import score_plan
from .optimizer import format_optimization_run, solve_optimization
from .scheduler import BudgetPruningScheduler, HeuristicScheduler


def main() -> None:
    schedulers = [HeuristicScheduler(), BudgetPruningScheduler()]
    for graph, constraints in load_seed_benchmarks():
        print(f"# {graph.title}")
        print(
            "constraints: "
            f"tokens<={constraints.token_budget}, "
            f"minutes<={constraints.time_budget_minutes}"
        )
        for scheduler in schedulers:
            plan = scheduler.build_plan(graph, constraints)
            score = score_plan(graph, plan)
            print(
                f"- {score.strategy}: tokens={score.estimated_tokens}, "
                f"serial={score.serial_minutes}, parallel={score.parallel_minutes}, "
                f"value={score.covered_value}, risk={score.covered_risk}"
            )
            for warning in score.warnings:
                print(f"  warning: {warning}")
        print()

    print("# Optimization traces")
    for graph, constraints in load_seed_benchmarks():
        print(format_optimization_run(solve_optimization(graph, constraints)))
        print()


if __name__ == "__main__":
    main()
