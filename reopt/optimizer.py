"""Meta-optimization layer for selecting and explaining scheduler choices."""

from __future__ import annotations

from dataclasses import asdict

from .evaluate import score_plan
from .models import (
    ConstraintSet,
    OptimizationDecision,
    OptimizationRun,
    PlanScore,
    TaskGraph,
)
from .scheduler import BudgetPruningScheduler, HeuristicScheduler


def solve_optimization(
    graph: TaskGraph,
    constraints: ConstraintSet,
    quality_weight: float = 1.0,
    token_weight: float = 0.0001,
    minute_weight: float = 0.01,
    risk_weight: float = 0.15,
) -> OptimizationRun:
    """Compare known strategies and select one with an explicit utility score."""
    schedulers = [HeuristicScheduler(), BudgetPruningScheduler()]
    scores = tuple(
        score_plan(graph, scheduler.build_plan(graph, constraints))
        for scheduler in schedulers
    )
    selected = max(
        scores,
        key=lambda score: _utility(
            score,
            constraints,
            quality_weight=quality_weight,
            token_weight=token_weight,
            minute_weight=minute_weight,
            risk_weight=risk_weight,
        ),
    )
    decisions = (
        OptimizationDecision(
            step="model",
            choice="task_graph",
            rationale=(
                "Represent the task as nodes, dependencies, costs, value, risk, "
                "and uncertainty so strategy comparison is inspectable."
            ),
        ),
        OptimizationDecision(
            step="generate_candidates",
            choice=", ".join(score.strategy for score in scores),
            rationale="Compare a greedy baseline against a budget-aware pruning variant.",
        ),
        OptimizationDecision(
            step="score_candidates",
            choice="utility = value - token_cost - latency_cost - risk_cost - violation_penalty",
            rationale=(
                "Budget fit matters, but dropped value and residual risk must remain visible."
            ),
        ),
        OptimizationDecision(
            step="select",
            choice=selected.strategy,
            rationale=_selection_reason(selected, constraints),
        ),
    )
    return OptimizationRun(
        run_id=f"{graph.graph_id}:{selected.strategy}",
        objective=f"Select a scheduler for: {graph.title}",
        constraints=constraints,
        candidate_scores=scores,
        selected_strategy=selected.strategy,
        selected_reason=_selection_reason(selected, constraints),
        decisions=decisions,
        next_refinement=(
            "Calibrate utility weights with observed task outcomes and add a quality "
            "penalty for missing optional evidence."
        ),
    )


def format_optimization_run(run: OptimizationRun) -> str:
    lines = [
        f"# {run.objective}",
        (
            "constraints: "
            f"tokens<={run.constraints.token_budget}, "
            f"minutes<={run.constraints.time_budget_minutes}, "
            f"quality>={run.constraints.quality_target}"
        ),
        "candidates:",
    ]
    for score in run.candidate_scores:
        lines.append(
            f"- {score.strategy}: tokens={score.estimated_tokens}, "
            f"serial={score.serial_minutes}, parallel={score.parallel_minutes}, "
            f"value={score.covered_value}, risk={score.covered_risk}, "
            f"utility={_utility(score, run.constraints):.3f}"
        )
        for warning in score.warnings:
            lines.append(f"  warning: {warning}")
    lines.extend(
        [
            f"selected: {run.selected_strategy}",
            f"reason: {run.selected_reason}",
            "decisions:",
        ]
    )
    for decision in run.decisions:
        lines.append(f"- {decision.step}: {decision.choice} | {decision.rationale}")
    lines.append(f"next_refinement: {run.next_refinement}")
    return "\n".join(lines)


def optimization_run_to_dict(run: OptimizationRun) -> dict[str, object]:
    data = asdict(run)
    data["constraints"] = asdict(run.constraints)
    return data


def _utility(
    score: PlanScore,
    constraints: ConstraintSet,
    *,
    quality_weight: float = 1.0,
    token_weight: float = 0.0001,
    minute_weight: float = 0.01,
    risk_weight: float = 0.15,
) -> float:
    token_overrun = max(0, score.estimated_tokens - constraints.token_budget)
    minute_overrun = max(0, score.parallel_minutes - constraints.time_budget_minutes)
    violation_penalty = (token_overrun * token_weight * 4) + (minute_overrun * 0.08)
    return (
        score.covered_value * quality_weight
        - score.estimated_tokens * token_weight
        - score.parallel_minutes * minute_weight
        - score.covered_risk * risk_weight
        - violation_penalty
    )


def _selection_reason(score: PlanScore, constraints: ConstraintSet) -> str:
    fits_tokens = score.estimated_tokens <= constraints.token_budget
    fits_time = score.parallel_minutes <= constraints.time_budget_minutes
    fit = "fits" if fits_tokens and fits_time else "violates"
    return (
        f"{score.strategy} {fit} hard budgets with value={score.covered_value}, "
        f"risk={score.covered_risk}, tokens={score.estimated_tokens}, "
        f"parallel_minutes={score.parallel_minutes}."
    )
