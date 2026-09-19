"""Heuristic schedulers for Re-Opt."""

from __future__ import annotations

from .models import AgentRole, ConstraintSet, ScheduledStep, SchedulePlan, TaskGraph, TaskNode


class HeuristicScheduler:
    """A first-pass A*-like scheduler with critical-path pressure."""

    strategy_name = "critical-path-a-star-v0"

    def build_plan(self, graph: TaskGraph, constraints: ConstraintSet) -> SchedulePlan:
        steps: list[ScheduledStep] = []
        estimated_tokens = 0
        estimated_minutes = 0
        warnings: list[str] = []

        for layer in graph.topological_layers():
            ranked_layer = sorted(
                layer,
                key=lambda node: self._priority(graph, node),
                reverse=True,
            )
            for node in ranked_layer:
                role = self._choose_role(node)
                priority = self._priority(graph, node)
                steps.append(
                    ScheduledStep(
                        node_id=node.node_id,
                        role=role,
                        priority=round(priority, 3),
                        reason=self._reason(graph, node, role),
                    )
                )
                estimated_tokens += node.token_cost
                estimated_minutes += node.time_cost_minutes

        if estimated_tokens > constraints.token_budget:
            warnings.append(
                f"Estimated tokens {estimated_tokens} exceed budget {constraints.token_budget}."
            )
        if estimated_minutes > constraints.time_budget_minutes:
            warnings.append(
                "Serial estimated minutes "
                f"{estimated_minutes} exceed budget {constraints.time_budget_minutes}; "
                "parallel execution or pruning is required."
            )

        return SchedulePlan(
            graph_id=graph.graph_id,
            strategy=self.strategy_name,
            steps=tuple(steps),
            estimated_tokens=estimated_tokens,
            estimated_minutes=estimated_minutes,
            warnings=tuple(warnings),
        )

    def _priority(self, graph: TaskGraph, node: TaskNode) -> float:
        blocking_score = len(graph.dependents(node.node_id)) * 0.35
        cost_penalty = (node.token_cost / 4000) + (node.time_cost_minutes / 120)
        return node.pressure() + blocking_score - cost_penalty

    def _choose_role(self, node: TaskNode) -> AgentRole:
        if node.preferred_roles:
            return node.preferred_roles[0]
        if node.uncertainty >= 0.65:
            return AgentRole.RESEARCHER
        if node.risk >= 0.7:
            return AgentRole.CRITIC
        if "verify" in node.title.lower() or "test" in node.title.lower():
            return AgentRole.VERIFIER
        if "synthesize" in node.title.lower() or "integrate" in node.title.lower():
            return AgentRole.SYNTHESIZER
        return AgentRole.BUILDER

    def _reason(self, graph: TaskGraph, node: TaskNode, role: AgentRole) -> str:
        dependents = len(graph.dependents(node.node_id))
        signals = [
            f"value={node.value}",
            f"risk={node.risk}",
            f"uncertainty={node.uncertainty}",
            f"blocks={dependents}",
        ]
        return f"{role.value} selected from " + ", ".join(signals)


class BudgetPruningScheduler(HeuristicScheduler):
    """A budget-aware variant that removes optional low-priority work first."""

    strategy_name = "budget-pruning-v0"

    def build_plan(self, graph: TaskGraph, constraints: ConstraintSet) -> SchedulePlan:
        selected_ids = set(graph.nodes)
        base_plan = super().build_plan(graph, constraints)

        while (
            base_plan.estimated_tokens > constraints.token_budget
            or base_plan.estimated_minutes > constraints.time_budget_minutes
        ):
            removable = [
                graph.nodes[step.node_id]
                for step in base_plan.steps
                if not graph.nodes[step.node_id].required
            ]
            if not removable:
                break
            drop = min(removable, key=lambda node: self._priority(graph, node))
            selected_ids.remove(drop.node_id)
            base_plan = self._build_filtered_plan(graph, constraints, selected_ids)

        return base_plan

    def _build_filtered_plan(
        self, graph: TaskGraph, constraints: ConstraintSet, selected_ids: set[str]
    ) -> SchedulePlan:
        steps: list[ScheduledStep] = []
        estimated_tokens = 0
        estimated_minutes = 0
        warnings: list[str] = []

        for layer in graph.topological_layers():
            ranked_layer = sorted(
                [node for node in layer if node.node_id in selected_ids],
                key=lambda node: self._priority(graph, node),
                reverse=True,
            )
            for node in ranked_layer:
                role = self._choose_role(node)
                priority = self._priority(graph, node)
                steps.append(
                    ScheduledStep(
                        node_id=node.node_id,
                        role=role,
                        priority=round(priority, 3),
                        reason=self._reason(graph, node, role),
                    )
                )
                estimated_tokens += node.token_cost
                estimated_minutes += node.time_cost_minutes

        dropped = sorted(set(graph.nodes) - selected_ids)
        if dropped:
            warnings.append(f"Dropped optional nodes to fit budget: {', '.join(dropped)}.")
        if estimated_tokens > constraints.token_budget:
            warnings.append(
                f"Estimated tokens {estimated_tokens} exceed budget {constraints.token_budget}."
            )
        if estimated_minutes > constraints.time_budget_minutes:
            warnings.append(
                "Serial estimated minutes "
                f"{estimated_minutes} exceed budget {constraints.time_budget_minutes}; "
                "parallel execution or scope reduction is still required."
            )

        return SchedulePlan(
            graph_id=graph.graph_id,
            strategy=self.strategy_name,
            steps=tuple(steps),
            estimated_tokens=estimated_tokens,
            estimated_minutes=estimated_minutes,
            warnings=tuple(warnings),
        )
