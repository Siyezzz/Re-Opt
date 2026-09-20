"""Core data structures for multi-agent task optimization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    DECOMPOSER = "decomposer"
    RESEARCHER = "researcher"
    BUILDER = "builder"
    CRITIC = "critic"
    VERIFIER = "verifier"
    SYNTHESIZER = "synthesizer"
    MEMORY_CURATOR = "memory_curator"


@dataclass(frozen=True)
class ConstraintSet:
    token_budget: int
    time_budget_minutes: int
    quality_target: float = 0.8
    max_parallel_agents: int = 3


@dataclass(frozen=True)
class UtilityWeights:
    quality: float = 1.05
    token: float = 0.0001
    minute: float = 0.01
    risk: float = 0.15
    missed_optional: float = 0.25
    token_overrun_multiplier: float = 4.0
    minute_overrun: float = 0.08

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "UtilityWeights":
        return cls(**data)


@dataclass(frozen=True)
class TaskNode:
    node_id: str
    title: str
    description: str
    token_cost: int
    time_cost_minutes: int
    risk: float
    value: float
    uncertainty: float
    dependencies: tuple[str, ...] = ()
    preferred_roles: tuple[AgentRole, ...] = ()
    required: bool = True

    def pressure(self) -> float:
        """Estimate how urgently this node deserves attention."""
        return self.value + self.risk + self.uncertainty


@dataclass
class TaskGraph:
    graph_id: str
    title: str
    nodes: dict[str, TaskNode] = field(default_factory=dict)

    def add_node(self, node: TaskNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node_id: {node.node_id}")
        missing = [dep for dep in node.dependencies if dep not in self.nodes]
        if missing:
            raise ValueError(f"Node {node.node_id} has unknown dependencies: {missing}")
        self.nodes[node.node_id] = node

    def dependents(self, node_id: str) -> list[str]:
        return [
            candidate.node_id
            for candidate in self.nodes.values()
            if node_id in candidate.dependencies
        ]

    def topological_layers(self) -> list[list[TaskNode]]:
        remaining = dict(self.nodes)
        completed: set[str] = set()
        layers: list[list[TaskNode]] = []

        while remaining:
            ready = [
                node
                for node in remaining.values()
                if all(dep in completed for dep in node.dependencies)
            ]
            if not ready:
                cycle = ", ".join(sorted(remaining))
                raise ValueError(f"Task graph contains a cycle or missing dependency: {cycle}")
            ready.sort(key=lambda node: node.node_id)
            layers.append(ready)
            for node in ready:
                completed.add(node.node_id)
                del remaining[node.node_id]

        return layers


@dataclass(frozen=True)
class ScheduledStep:
    node_id: str
    role: AgentRole
    priority: float
    reason: str


@dataclass(frozen=True)
class SchedulePlan:
    graph_id: str
    strategy: str
    steps: tuple[ScheduledStep, ...]
    estimated_tokens: int
    estimated_minutes: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanScore:
    graph_id: str
    strategy: str
    estimated_tokens: int
    serial_minutes: int
    parallel_minutes: int
    total_value: float
    covered_value: float
    value_coverage: float
    missed_optional_value: float
    covered_risk: float
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class OptimizationDecision:
    step: str
    choice: str
    rationale: str


@dataclass(frozen=True)
class OptimizationRun:
    run_id: str
    objective: str
    constraints: ConstraintSet
    utility_weights: UtilityWeights
    candidate_scores: tuple[PlanScore, ...]
    selected_strategy: str
    selected_reason: str
    decisions: tuple[OptimizationDecision, ...]
    next_refinement: str
