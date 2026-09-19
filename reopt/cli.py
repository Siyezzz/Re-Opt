"""Command-line entry points for Re-Opt experiments."""

from __future__ import annotations

from .benchmarks import load_seed_benchmarks
from .scheduler import HeuristicScheduler


def main() -> None:
    scheduler = HeuristicScheduler()
    for graph, constraints in load_seed_benchmarks():
        plan = scheduler.build_plan(graph, constraints)
        print(f"# {graph.title}")
        print(f"strategy: {plan.strategy}")
        print(f"estimated_tokens: {plan.estimated_tokens}")
        print(f"estimated_serial_minutes: {plan.estimated_minutes}")
        for warning in plan.warnings:
            print(f"warning: {warning}")
        for step in plan.steps:
            print(
                f"- {step.node_id}: role={step.role.value}, "
                f"priority={step.priority}, reason={step.reason}"
            )
        print()


if __name__ == "__main__":
    main()
