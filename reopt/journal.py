"""Markdown journal generation for optimization runs."""

from __future__ import annotations

from datetime import date

from .benchmarks import load_seed_benchmarks
from .optimizer import solve_optimization


def render_seed_journal(run_date: date | None = None) -> str:
    current_date = run_date or date.today()
    lines = [
        "# Optimization Run Journal",
        "",
        (
            "This journal records how Re-Opt solves each task as an optimization "
            "problem: objective, constraints, candidate strategies, selection "
            "logic, observed result, and next refinement."
        ),
        "",
        f"## {current_date.isoformat()} - Seed Strategy Selection",
        "",
    ]
    for graph, constraints in load_seed_benchmarks():
        run = solve_optimization(graph, constraints)
        lines.extend(
            [
                f"### {graph.title}",
                "",
                f"Objective: {run.objective}",
                "",
                (
                    "Constraints: "
                    f"tokens<={constraints.token_budget}, "
                    f"parallel_minutes<={constraints.time_budget_minutes}, "
                    f"quality>={constraints.quality_target}"
                ),
                "",
                "| Strategy | Tokens | Serial min | Parallel min | Value | Risk | Warnings |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for score in run.candidate_scores:
            warnings = "; ".join(score.warnings) if score.warnings else ""
            lines.append(
                f"| {score.strategy} | {score.estimated_tokens} | "
                f"{score.serial_minutes} | {score.parallel_minutes} | "
                f"{score.covered_value} | {score.covered_risk} | {warnings} |"
            )
        lines.extend(
            [
                "",
                f"Selected: `{run.selected_strategy}`",
                "",
                f"Reason: {run.selected_reason}",
                "",
                "Decision trace:",
                "",
            ]
        )
        for decision in run.decisions:
            lines.append(
                f"- `{decision.step}` -> `{decision.choice}`: {decision.rationale}"
            )
        lines.extend(["", f"Next refinement: {run.next_refinement}", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    print(render_seed_journal())


if __name__ == "__main__":
    main()
