"""Capture an observed run as an outcome record."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .outcomes import OutcomeRecord, dump_outcomes, load_outcomes

REQUIRED_SIGNAL_FIELDS = ("token", "minute", "missed_optional")


@dataclass(frozen=True)
class ObservedRunCounters:
    tokens_before: int
    tokens_after: int
    minutes_before: int
    minutes_after: int


def outcome_from_counters(
    graph_id: str,
    strategy: str,
    observed_quality: float,
    target_quality: float,
    token_budget: int,
    time_budget_minutes: int,
    missed_optional_harm: float,
    evidence_ref: str,
    counters: ObservedRunCounters,
) -> OutcomeRecord:
    """Build an outcome from before/after counters instead of hand-entered deltas."""
    _validate_counters(counters)
    return OutcomeRecord(
        graph_id=graph_id,
        strategy=strategy,
        observed_quality=observed_quality,
        target_quality=target_quality,
        actual_tokens=counters.tokens_after - counters.tokens_before,
        token_budget=token_budget,
        actual_minutes=counters.minutes_after - counters.minutes_before,
        time_budget_minutes=time_budget_minutes,
        missed_optional_harm=missed_optional_harm,
        evidence_ref=evidence_ref,
    )


def render_capture_report(outcome: OutcomeRecord, counters: ObservedRunCounters) -> str:
    lines = [
        "# Observed Run Capture",
        "",
        f"graph_id: {outcome.graph_id}",
        f"strategy: {outcome.strategy}",
        f"evidence_ref: {outcome.evidence_ref}",
        "",
        "Counters:",
        "",
        f"- tokens: {counters.tokens_before} -> {counters.tokens_after}",
        f"- minutes: {counters.minutes_before} -> {counters.minutes_after}",
        "",
        "Outcome:",
        "",
        f"- actual_tokens: {outcome.actual_tokens}",
        f"- token_budget: {outcome.token_budget}",
        f"- actual_minutes: {outcome.actual_minutes}",
        f"- time_budget_minutes: {outcome.time_budget_minutes}",
        f"- observed_quality: {outcome.observed_quality}",
        f"- target_quality: {outcome.target_quality}",
        f"- missed_optional_harm: {outcome.missed_optional_harm}",
    ]
    return "\n".join(lines) + "\n"


def required_signal_failures(
    outcome: OutcomeRecord,
    required_signals: tuple[str, ...],
) -> tuple[str, ...]:
    failures = []
    for signal in required_signals:
        if signal == "token" and outcome.actual_tokens <= outcome.token_budget:
            failures.append("token signal requires actual_tokens above token_budget")
        elif signal == "minute" and outcome.actual_minutes <= outcome.time_budget_minutes:
            failures.append("minute signal requires actual_minutes above time_budget_minutes")
        elif signal == "missed_optional" and outcome.missed_optional_harm <= 0:
            failures.append("missed_optional signal requires missed_optional_harm above 0")
        elif signal not in REQUIRED_SIGNAL_FIELDS:
            failures.append(f"unsupported required signal: {signal}")
    return tuple(failures)


def _validate_counters(counters: ObservedRunCounters) -> None:
    if counters.tokens_after < counters.tokens_before:
        raise ValueError("tokens_after must be greater than or equal to tokens_before")
    if counters.minutes_after < counters.minutes_before:
        raise ValueError("minutes_after must be greater than or equal to minutes_before")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture an observed run outcome.")
    parser.add_argument("--graph-id", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--observed-quality", type=float, required=True)
    parser.add_argument("--target-quality", type=float, required=True)
    parser.add_argument("--tokens-before", type=int, required=True)
    parser.add_argument("--tokens-after", type=int, required=True)
    parser.add_argument("--token-budget", type=int, required=True)
    parser.add_argument("--minutes-before", type=int, required=True)
    parser.add_argument("--minutes-after", type=int, required=True)
    parser.add_argument("--time-budget-minutes", type=int, required=True)
    parser.add_argument("--missed-optional-harm", type=float, default=0.0)
    parser.add_argument("--evidence-ref", required=True)
    parser.add_argument(
        "--require-signal",
        action="append",
        choices=REQUIRED_SIGNAL_FIELDS,
        default=[],
        help="Require the captured outcome to support a field-specific signal.",
    )
    parser.add_argument("--write", type=Path, help="Write the captured outcome JSON.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to an existing outcome JSON instead of replacing it.",
    )
    parser.add_argument("--write-report", type=Path, help="Write a capture report.")
    args = parser.parse_args()

    counters = ObservedRunCounters(
        tokens_before=args.tokens_before,
        tokens_after=args.tokens_after,
        minutes_before=args.minutes_before,
        minutes_after=args.minutes_after,
    )
    outcome = outcome_from_counters(
        graph_id=args.graph_id,
        strategy=args.strategy,
        observed_quality=args.observed_quality,
        target_quality=args.target_quality,
        token_budget=args.token_budget,
        time_budget_minutes=args.time_budget_minutes,
        missed_optional_harm=args.missed_optional_harm,
        evidence_ref=args.evidence_ref,
        counters=counters,
    )
    failures = required_signal_failures(outcome, tuple(args.require_signal))
    if failures:
        for failure in failures:
            print(f"error: {failure}")
        raise SystemExit(1)
    if args.write:
        outcomes = (outcome,)
        if args.append and args.write.exists():
            outcomes = load_outcomes(args.write) + outcomes
        dump_outcomes(args.write, outcomes)
    report = render_capture_report(outcome, counters)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
