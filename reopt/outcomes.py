"""Outcome records and simple utility-weight calibration."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

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
    evidence_ref: str = ""


def load_outcomes(path: Path) -> tuple[OutcomeRecord, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(OutcomeRecord(**item) for item in data)


def dump_outcomes(path: Path, outcomes: tuple[OutcomeRecord, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(outcome) for outcome in outcomes]
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_utility_weights(path: Path) -> UtilityWeights:
    data = json.loads(path.read_text(encoding="utf-8"))
    return UtilityWeights.from_dict(data)


def dump_utility_weights(path: Path, weights: UtilityWeights) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(weights.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def propose_utility_weights_with_consumption(
    base: UtilityWeights,
    outcomes: tuple[OutcomeRecord, ...],
    consumed_by_field: dict[str, set[str]],
) -> UtilityWeights:
    """Propose weight changes while excluding already-consumed field signals."""
    if not outcomes:
        return base

    quality_gap = _average(
        max(0.0, outcome.target_quality - outcome.observed_quality)
        for outcome in outcomes
        if _outcome_key(outcome) not in consumed_by_field.get("quality", set())
    )
    token_overrun = _average(
        max(0.0, outcome.actual_tokens - outcome.token_budget)
        / max(1, outcome.token_budget)
        for outcome in outcomes
        if _outcome_key(outcome) not in consumed_by_field.get("token", set())
    )
    time_overrun = _average(
        max(0.0, outcome.actual_minutes - outcome.time_budget_minutes)
        / max(1, outcome.time_budget_minutes)
        for outcome in outcomes
        if _outcome_key(outcome) not in consumed_by_field.get("minute", set())
    )
    missed_optional_harm = _average(
        max(0.0, outcome.missed_optional_harm)
        for outcome in outcomes
        if _outcome_key(outcome) not in consumed_by_field.get("missed_optional", set())
    )

    return replace(
        base,
        quality=round(base.quality + quality_gap * 0.5, 4),
        token=round(base.token * (1 + token_overrun), 7),
        minute=round(base.minute * (1 + time_overrun), 5),
        missed_optional=round(base.missed_optional + missed_optional_harm * 0.5, 4),
    )


def calibration_report(
    base: UtilityWeights,
    proposed: UtilityWeights,
    outcomes: tuple[OutcomeRecord, ...],
) -> str:
    lines = [
        "# Utility Weight Calibration",
        "",
        f"outcomes: {len(outcomes)}",
        "",
        "| Weight | Current | Proposed | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field in (
        "quality",
        "token",
        "minute",
        "risk",
        "missed_optional",
        "token_overrun_multiplier",
        "minute_overrun",
    ):
        current = getattr(base, field)
        candidate = getattr(proposed, field)
        lines.append(f"| {field} | {current} | {candidate} | {candidate - current:+.6f} |")

    lines.extend(["", "Outcome signals:", ""])
    for outcome in outcomes:
        quality_gap = max(0.0, outcome.target_quality - outcome.observed_quality)
        token_overrun = max(0, outcome.actual_tokens - outcome.token_budget)
        time_overrun = max(0, outcome.actual_minutes - outcome.time_budget_minutes)
        lines.append(
            "- "
            f"{outcome.graph_id}/{outcome.strategy}: "
            f"quality_gap={quality_gap:.3f}, "
            f"token_overrun={token_overrun}, "
            f"time_overrun={time_overrun}, "
            f"missed_optional_harm={outcome.missed_optional_harm:.3f}"
        )

    return "\n".join(lines) + "\n"


def consumption_adjusted_report(
    base: UtilityWeights,
    proposed: UtilityWeights,
    outcomes: tuple[OutcomeRecord, ...],
    consumed_by_field: dict[str, set[str]],
) -> str:
    lines = [
        calibration_report(base, proposed, outcomes).rstrip(),
        "",
        "Consumed signals excluded:",
        "",
    ]
    consumed_any = False
    for field in ("quality", "token", "minute", "missed_optional"):
        consumed = tuple(sorted(consumed_by_field.get(field, set())))
        if consumed:
            consumed_any = True
            lines.append(f"- {field}:")
            for key in consumed:
                lines.append(f"  - {key}")
    if not consumed_any:
        lines.append("- _none_")
    return "\n".join(lines) + "\n"


def _average(values: object) -> float:
    items = tuple(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _outcome_key(outcome: OutcomeRecord) -> str:
    return (
        f"{outcome.graph_id}/{outcome.strategy}: "
        f"tokens={outcome.actual_tokens}/{outcome.token_budget}, "
        f"minutes={outcome.actual_minutes}/{outcome.time_budget_minutes}, "
        f"quality={outcome.observed_quality}/{outcome.target_quality}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Propose Re-Opt utility weight updates from outcome records."
    )
    parser.add_argument("outcomes", type=Path, help="Outcome JSON file.")
    parser.add_argument(
        "--write-weights",
        type=Path,
        help="Write proposed utility weights to a JSON file.",
    )
    args = parser.parse_args()
    records = load_outcomes(args.outcomes)
    base = UtilityWeights()
    proposed = propose_utility_weights(base, records)
    if args.write_weights:
        dump_utility_weights(args.write_weights, proposed)
    print(calibration_report(base, proposed, records))


if __name__ == "__main__":
    main()
