"""Outcome records and simple utility-weight calibration."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .models import UtilityWeights


@dataclass(frozen=True)
class OutcomeRecord:
    graph_id: str
    strategy: str
    observed_quality: float
    target_quality: float
    actual_tokens: int
    token_budget: int
    actual_minutes: int
    time_budget_minutes: int
    missed_optional_harm: float = 0.0


def propose_utility_weights(
    base: UtilityWeights,
    outcomes: tuple[OutcomeRecord, ...],
) -> UtilityWeights:
    """Propose conservative weight changes from observed outcomes."""
    if not outcomes:
        return base

    quality_gap = _average(
        max(0.0, outcome.target_quality - outcome.observed_quality)
        for outcome in outcomes
    )
    token_overrun = _average(
        max(0.0, outcome.actual_tokens - outcome.token_budget)
        / max(1, outcome.token_budget)
        for outcome in outcomes
    )
    time_overrun = _average(
        max(0.0, outcome.actual_minutes - outcome.time_budget_minutes)
        / max(1, outcome.time_budget_minutes)
        for outcome in outcomes
    )
    missed_optional_harm = _average(
        max(0.0, outcome.missed_optional_harm) for outcome in outcomes
    )

    return replace(
        base,
        quality=round(base.quality + quality_gap * 0.5, 4),
        token=round(base.token * (1 + token_overrun), 7),
        minute=round(base.minute * (1 + time_overrun), 5),
        missed_optional=round(base.missed_optional + missed_optional_harm * 0.5, 4),
    )


def _average(values: object) -> float:
    items = tuple(values)
    if not items:
        return 0.0
    return sum(items) / len(items)
