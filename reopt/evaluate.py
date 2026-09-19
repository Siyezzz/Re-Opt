"""Plan evaluation utilities."""

from __future__ import annotations

from .models import PlanScore, SchedulePlan, TaskGraph


def score_plan(graph: TaskGraph, plan: SchedulePlan) -> PlanScore:
    planned = {step.node_id for step in plan.steps}
    parallel_minutes = 0
    for layer in graph.topological_layers():
        layer_minutes = [
            node.time_cost_minutes for node in layer if node.node_id in planned
        ]
        if layer_minutes:
            parallel_minutes += max(layer_minutes)

    covered_nodes = [graph.nodes[node_id] for node_id in planned]
    total_value = sum(node.value for node in graph.nodes.values())
    covered_value = sum(node.value for node in covered_nodes)
    missed_optional_value = sum(
        node.value
        for node in graph.nodes.values()
        if node.node_id not in planned and not node.required
    )
    return PlanScore(
        graph_id=graph.graph_id,
        strategy=plan.strategy,
        estimated_tokens=plan.estimated_tokens,
        serial_minutes=plan.estimated_minutes,
        parallel_minutes=parallel_minutes,
        total_value=round(total_value, 3),
        covered_value=round(covered_value, 3),
        value_coverage=round(covered_value / total_value, 3),
        missed_optional_value=round(missed_optional_value, 3),
        covered_risk=round(sum(node.risk for node in covered_nodes), 3),
        warnings=plan.warnings,
    )
