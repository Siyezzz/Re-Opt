"""Seed benchmark graphs for early scheduler experiments."""

from __future__ import annotations

from .models import AgentRole, ConstraintSet, TaskGraph, TaskNode


def load_seed_benchmarks() -> list[tuple[TaskGraph, ConstraintSet]]:
    return [
        (_coding_debug_graph(), ConstraintSet(token_budget=12000, time_budget_minutes=90)),
        (_research_synthesis_graph(), ConstraintSet(token_budget=16000, time_budget_minutes=120)),
        (_tight_research_graph(), ConstraintSet(token_budget=7000, time_budget_minutes=65)),
    ]


def _coding_debug_graph() -> TaskGraph:
    graph = TaskGraph(
        graph_id="coding-debug-seed",
        title="Debug a failing feature and verify the fix",
    )
    graph.add_node(
        TaskNode(
            node_id="map",
            title="Map failing behavior",
            description="Identify symptoms, reproduction path, and affected modules.",
            token_cost=1500,
            time_cost_minutes=15,
            risk=0.55,
            value=0.8,
            uncertainty=0.75,
            preferred_roles=(AgentRole.DECOMPOSER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="inspect",
            title="Inspect implementation",
            description="Read relevant code and form a causal hypothesis.",
            token_cost=2500,
            time_cost_minutes=25,
            risk=0.65,
            value=0.9,
            uncertainty=0.6,
            dependencies=("map",),
            preferred_roles=(AgentRole.RESEARCHER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="patch",
            title="Patch implementation",
            description="Apply the smallest change that addresses the causal hypothesis.",
            token_cost=3000,
            time_cost_minutes=30,
            risk=0.7,
            value=1.0,
            uncertainty=0.45,
            dependencies=("inspect",),
            preferred_roles=(AgentRole.BUILDER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="test",
            title="Run tests and verify behavior",
            description="Run targeted checks and look for regressions.",
            token_cost=1200,
            time_cost_minutes=15,
            risk=0.8,
            value=0.95,
            uncertainty=0.35,
            dependencies=("patch",),
            preferred_roles=(AgentRole.VERIFIER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="record",
            title="Record learning",
            description="Capture task features, result, surprise, and next experiment.",
            token_cost=600,
            time_cost_minutes=5,
            risk=0.35,
            value=0.55,
            uncertainty=0.2,
            dependencies=("test",),
            preferred_roles=(AgentRole.MEMORY_CURATOR,),
            required=False,
        )
    )
    return graph


def _research_synthesis_graph() -> TaskGraph:
    graph = TaskGraph(
        graph_id="research-synthesis-seed",
        title="Research a broad question and synthesize a position",
    )
    graph.add_node(
        TaskNode(
            node_id="frame",
            title="Frame the research question",
            description="Define scope, assumptions, and success criteria.",
            token_cost=1200,
            time_cost_minutes=10,
            risk=0.5,
            value=0.8,
            uncertainty=0.75,
            preferred_roles=(AgentRole.DECOMPOSER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="search",
            title="Search evidence",
            description="Gather current or authoritative sources.",
            token_cost=3500,
            time_cost_minutes=35,
            risk=0.65,
            value=0.9,
            uncertainty=0.85,
            dependencies=("frame",),
            preferred_roles=(AgentRole.RESEARCHER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="compare",
            title="Compare candidate models",
            description="Analyze tradeoffs and identify falsifiable differences.",
            token_cost=3000,
            time_cost_minutes=30,
            risk=0.7,
            value=0.95,
            uncertainty=0.65,
            dependencies=("search",),
            preferred_roles=(AgentRole.CRITIC,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="synthesize",
            title="Synthesize final answer",
            description="Integrate findings into a coherent recommendation.",
            token_cost=2500,
            time_cost_minutes=25,
            risk=0.55,
            value=1.0,
            uncertainty=0.45,
            dependencies=("compare",),
            preferred_roles=(AgentRole.SYNTHESIZER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="record",
            title="Record learning",
            description="Capture the strategy, evidence quality, and result.",
            token_cost=700,
            time_cost_minutes=5,
            risk=0.35,
            value=0.55,
            uncertainty=0.2,
            dependencies=("synthesize",),
            preferred_roles=(AgentRole.MEMORY_CURATOR,),
            required=False,
        )
    )
    return graph


def _tight_research_graph() -> TaskGraph:
    graph = TaskGraph(
        graph_id="tight-research-seed",
        title="Answer a research question under a tight budget",
    )
    graph.add_node(
        TaskNode(
            node_id="frame",
            title="Frame the research question",
            description="Define the decision, scope, and answer format.",
            token_cost=1000,
            time_cost_minutes=8,
            risk=0.45,
            value=0.75,
            uncertainty=0.7,
            preferred_roles=(AgentRole.DECOMPOSER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="primary_search",
            title="Search primary evidence",
            description="Gather the smallest authoritative source set.",
            token_cost=2600,
            time_cost_minutes=25,
            risk=0.7,
            value=0.95,
            uncertainty=0.8,
            dependencies=("frame",),
            preferred_roles=(AgentRole.RESEARCHER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="secondary_sweep",
            title="Optional secondary sweep",
            description="Look for extra context, edge cases, and disagreement.",
            token_cost=2400,
            time_cost_minutes=25,
            risk=0.45,
            value=0.45,
            uncertainty=0.7,
            dependencies=("frame",),
            preferred_roles=(AgentRole.RESEARCHER,),
            required=False,
        )
    )
    graph.add_node(
        TaskNode(
            node_id="synthesize",
            title="Synthesize answer",
            description="Produce a concise answer with uncertainty called out.",
            token_cost=2200,
            time_cost_minutes=20,
            risk=0.6,
            value=1.0,
            uncertainty=0.4,
            dependencies=("primary_search",),
            preferred_roles=(AgentRole.SYNTHESIZER,),
        )
    )
    graph.add_node(
        TaskNode(
            node_id="record",
            title="Record learning",
            description="Record whether pruning preserved quality.",
            token_cost=600,
            time_cost_minutes=5,
            risk=0.35,
            value=0.5,
            uncertainty=0.2,
            dependencies=("synthesize",),
            preferred_roles=(AgentRole.MEMORY_CURATOR,),
            required=False,
        )
    )
    return graph
