"""Run the observed outcome capture and review pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .goal_snapshot import (
    delta_gate_failures,
    render_goal_snapshot,
    render_goal_snapshot_delta,
)
from .observed_evidence import review_observed_evidence
from .observed_run import (
    counters_from_goal_snapshots,
    outcome_from_counters,
    render_capture_report,
    required_signal_failures,
)
from .outcome_intake import validate_outcome_intake
from .outcomes import OutcomeRecord, dump_outcomes
from .regression import DEFAULT_BASELINE


def run_observed_pipeline(
    raw_goal_before: Path,
    raw_goal_after: Path,
    graph_id: str,
    strategy: str,
    observed_quality: float,
    target_quality: float,
    token_budget: int,
    time_budget_minutes: int,
    missed_optional_harm: float,
    evidence_ref: str,
    required_signals: tuple[str, ...] | None = None,
    existing_path: Path = Path("outcomes/seed-outcomes.json"),
    baseline_path: Path = DEFAULT_BASELINE,
    ledger_path: Path = Path("docs/outcome-consumption/ledger.json"),
    goal_before_path: Path = Path("docs/outcome-evidence/goal-before.json"),
    goal_after_path: Path = Path("docs/outcome-evidence/goal-after.json"),
    goal_delta_path: Path = Path("docs/outcome-evidence/goal-delta.json"),
    outcome_path: Path = Path("outcomes/next-outcome.json"),
    capture_report_path: Path = Path("docs/outcome-evidence/observed-run-capture.md"),
    proposed_weights_path: Path = Path("weights/proposed-observed-consumption-aware.json"),
    evidence_report_path: Path = Path("docs/outcome-evidence/observed-consumption-aware.md"),
) -> str:
    before_json = raw_goal_before.read_text(encoding="utf-8")
    after_json = raw_goal_after.read_text(encoding="utf-8")
    goal_before_path.parent.mkdir(parents=True, exist_ok=True)
    goal_before_path.write_text(render_goal_snapshot(before_json), encoding="utf-8")
    goal_after_path.parent.mkdir(parents=True, exist_ok=True)
    goal_after_path.write_text(render_goal_snapshot(after_json), encoding="utf-8")

    delta_report = render_goal_snapshot_delta(
        goal_before_path.read_text(encoding="utf-8"),
        goal_after_path.read_text(encoding="utf-8"),
    )
    goal_delta_path.parent.mkdir(parents=True, exist_ok=True)
    goal_delta_path.write_text(delta_report, encoding="utf-8")

    counters = counters_from_goal_snapshots(goal_before_path, goal_after_path)
    outcome = outcome_from_counters(
        graph_id=graph_id,
        strategy=strategy,
        observed_quality=observed_quality,
        target_quality=target_quality,
        token_budget=token_budget,
        time_budget_minutes=time_budget_minutes,
        missed_optional_harm=missed_optional_harm,
        evidence_ref=evidence_ref,
        counters=counters,
    )
    required = required_signals or inferred_required_signals(outcome)
    delta = json.loads(delta_report)["delta"]
    delta_failures = delta_gate_failures(
        delta,
        token_budget if "token" in required else None,
        time_budget_minutes if "minute" in required else None,
    )
    if delta_failures:
        return render_pipeline_report(
            status="blocked",
            failures=delta_failures,
            goal_delta_path=goal_delta_path,
            outcome_path=outcome_path,
            evidence_report_path=evidence_report_path,
        )

    signal_failures = required_signal_failures(
        outcome,
        required,
    )
    if signal_failures:
        return render_pipeline_report(
            status="blocked",
            failures=signal_failures,
            goal_delta_path=goal_delta_path,
            outcome_path=outcome_path,
            evidence_report_path=evidence_report_path,
        )

    dump_outcomes(outcome_path, (outcome,))
    capture_report_path.parent.mkdir(parents=True, exist_ok=True)
    capture_report_path.write_text(render_capture_report(outcome, counters), encoding="utf-8")

    validation_failures = []
    for field in required:
        ok, failures = validate_outcome_intake(
            outcome_path,
            existing_path,
            require_unconsumed_for=field,
            ledger_path=ledger_path,
            require_evidence_ref=True,
        )
        if not ok:
            validation_failures.extend(failures)
    if validation_failures:
        return render_pipeline_report(
            status="blocked",
            failures=tuple(validation_failures),
            goal_delta_path=goal_delta_path,
            outcome_path=outcome_path,
            evidence_report_path=evidence_report_path,
        )

    evidence_report = review_observed_evidence(
        outcome_path,
        proposed_weights_path,
        existing_path,
        baseline_path,
        provenance=evidence_ref,
        ledger_path=ledger_path,
    )
    evidence_report_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_report_path.write_text(evidence_report, encoding="utf-8")
    return render_pipeline_report(
        status="clean",
        failures=(),
        goal_delta_path=goal_delta_path,
        outcome_path=outcome_path,
        evidence_report_path=evidence_report_path,
    )


def inferred_required_signals(outcome: OutcomeRecord) -> tuple[str, ...]:
    signals = []
    if outcome.observed_quality < outcome.target_quality:
        signals.append("quality")
    if outcome.actual_tokens > outcome.token_budget:
        signals.append("token")
    if outcome.actual_minutes > outcome.time_budget_minutes:
        signals.append("minute")
    if outcome.missed_optional_harm > 0:
        signals.append("missed_optional")
    return tuple(signals)


def render_pipeline_report(
    status: str,
    failures: tuple[str, ...],
    goal_delta_path: Path,
    outcome_path: Path,
    evidence_report_path: Path,
) -> str:
    lines = [
        "# Observed Evidence Pipeline",
        "",
        f"status: {status}",
        f"goal_delta: {goal_delta_path.as_posix()}",
        f"outcome: {outcome_path.as_posix()}",
        f"evidence_report: {evidence_report_path.as_posix()}",
    ]
    if failures:
        lines.extend(["", "Failures:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run observed evidence capture and review.")
    parser.add_argument("--raw-goal-before", type=Path, required=True)
    parser.add_argument("--raw-goal-after", type=Path, required=True)
    parser.add_argument("--graph-id", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--observed-quality", type=float, required=True)
    parser.add_argument("--target-quality", type=float, required=True)
    parser.add_argument("--token-budget", type=int, required=True)
    parser.add_argument("--time-budget-minutes", type=int, required=True)
    parser.add_argument("--missed-optional-harm", type=float, required=True)
    parser.add_argument("--evidence-ref", required=True)
    parser.add_argument(
        "--require-signal",
        action="append",
        choices=("quality", "token", "minute", "missed_optional"),
        default=[],
        help="Require the captured outcome to support a field-specific signal.",
    )
    parser.add_argument("--existing", type=Path, default=Path("outcomes/seed-outcomes.json"))
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--ledger", type=Path, default=Path("docs/outcome-consumption/ledger.json"))
    parser.add_argument("--write-report", type=Path, help="Write pipeline report.")
    args = parser.parse_args()

    report = run_observed_pipeline(
        raw_goal_before=args.raw_goal_before,
        raw_goal_after=args.raw_goal_after,
        graph_id=args.graph_id,
        strategy=args.strategy,
        observed_quality=args.observed_quality,
        target_quality=args.target_quality,
        token_budget=args.token_budget,
        time_budget_minutes=args.time_budget_minutes,
        missed_optional_harm=args.missed_optional_harm,
        evidence_ref=args.evidence_ref,
        required_signals=tuple(args.require_signal) or None,
        existing_path=args.existing,
        baseline_path=args.baseline,
        ledger_path=args.ledger,
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
