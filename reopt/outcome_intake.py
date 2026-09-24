"""Generate the next outcome-evidence intake request."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .outcome_consumption import (
    DEFAULT_LEDGER,
    consumed_outcomes,
    load_consumption_ledger,
    outcome_key,
)
from .outcomes import OutcomeRecord, load_outcomes


@dataclass(frozen=True)
class OutcomeIntakeRequest:
    title: str
    rationale: str
    avoid_reusing: tuple[str, ...]
    required_fields: tuple[str, ...]
    required_signals: tuple[str, ...]
    suggested_record: OutcomeRecord
    suggested_commands: tuple[str, ...]


def suggest_outcome_intake(
    outcomes_path: Path = Path("outcomes/seed-outcomes.json"),
    next_target_path: Path = Path("docs/next-target.md"),
) -> OutcomeIntakeRequest:
    outcomes = load_outcomes(outcomes_path)
    next_target = next_target_path.read_text(encoding="utf-8")
    avoid_reusing = tuple(_outcome_key(outcome) for outcome in outcomes)
    required_fields_for_signals = _required_unconsumed_fields(next_target)
    suggested = _suggest_record(outcomes, required_fields_for_signals)
    required_signals = tuple(
        _required_signal_text(field) for field in required_fields_for_signals
    )
    validation_commands = tuple(
        "python -m reopt.outcome_intake --validate "
        f"outcomes/next-outcome.json --require-unconsumed-for {field} "
        "--require-evidence-ref"
        for field in required_fields_for_signals
    )
    if not validation_commands:
        validation_commands = (
            "python -m reopt.outcome_intake --validate "
            "outcomes/next-outcome.json --require-evidence-ref",
        )
    return OutcomeIntakeRequest(
        title=(
            f"Collect unconsumed {', '.join(required_fields_for_signals)} evidence"
            if required_fields_for_signals
            else "Collect a new outcome before more weight changes"
        ),
        rationale=(
            "The next target asks for field-specific signals that have not already "
            "been used to justify weight adoptions. A fresh outcome should satisfy "
            "the listed unconsumed signal checks before any related weight is raised."
            if required_fields_for_signals
            else (
                "The next target asks for evidence before changing the remaining blocked "
                "weight increments. A new outcome should come from a different task shape "
                "or a fresh run, so calibration does not repeatedly consume the same "
                "tight-research observation."
            )
        ),
        avoid_reusing=avoid_reusing,
        required_fields=tuple(asdict(suggested)),
        required_signals=required_signals,
        suggested_record=suggested,
        suggested_commands=(
            _capture_command(suggested),
            *validation_commands,
            "python -m reopt.outcomes outcomes/next-outcome.json",
            "python -m reopt.calibrate outcomes/next-outcome.json",
            "python -m reopt.explain_adoption weights/proposed-seed.json",
            "python -m reopt.regression --check",
        ),
    )


def render_outcome_intake(request: OutcomeIntakeRequest) -> str:
    lines = [
        "# Outcome Evidence Intake",
        "",
        f"title: {request.title}",
        "",
        f"rationale: {request.rationale}",
        "",
        "Do not reuse:",
        "",
    ]
    if request.avoid_reusing:
        for item in request.avoid_reusing:
            lines.append(f"- {item}")
    else:
        lines.append("- _none recorded_")
    lines.extend(
        [
            "",
            "Required fields:",
            "",
        ]
    )
    for field in request.required_fields:
        lines.append(f"- {field}")
    lines.extend(["", "Required signals:", ""])
    lines.append("- Each candidate record must include a non-placeholder evidence_ref.")
    if request.required_signals:
        for signal in request.required_signals:
            lines.append(f"- {signal}")
    else:
        lines.append("- _none beyond required fields_")
    lines.extend(
        [
            "",
            "Suggested JSON record:",
            "",
            "```json",
            json.dumps([asdict(request.suggested_record)], indent=2, sort_keys=True),
            "```",
            "",
            "Suggested commands:",
            "",
        ]
    )
    for command in request.suggested_commands:
        lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def validate_outcome_intake(
    candidate_path: Path,
    existing_path: Path = Path("outcomes/seed-outcomes.json"),
    require_unconsumed_for: str | None = None,
    ledger_path: Path = DEFAULT_LEDGER,
    require_evidence_ref: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    existing = {_outcome_key(outcome) for outcome in load_outcomes(existing_path)}
    candidate = load_outcomes(candidate_path)
    failures: list[str] = []
    for index, outcome in enumerate(candidate, start=1):
        prefix = f"record {index} ({outcome.graph_id}/{outcome.strategy})"
        if _outcome_key(outcome) in existing:
            failures.append(f"{prefix}: duplicates an existing outcome record")
        if outcome.actual_tokens <= 0:
            failures.append(f"{prefix}: actual_tokens must be observed and greater than 0")
        if outcome.actual_minutes <= 0:
            failures.append(f"{prefix}: actual_minutes must be observed and greater than 0")
        if outcome.token_budget <= 0:
            failures.append(f"{prefix}: token_budget must be greater than 0")
        if outcome.time_budget_minutes <= 0:
            failures.append(f"{prefix}: time_budget_minutes must be greater than 0")
        if not 0 < outcome.target_quality <= 1:
            failures.append(f"{prefix}: target_quality must be in (0, 1]")
        if not 0 < outcome.observed_quality <= 1:
            failures.append(f"{prefix}: observed_quality must be observed and in (0, 1]")
        if outcome.missed_optional_harm < 0:
            failures.append(f"{prefix}: missed_optional_harm cannot be negative")
        if require_evidence_ref and _is_placeholder_evidence_ref(outcome.evidence_ref):
            failures.append(f"{prefix}: evidence_ref must point to the observed run evidence")
    if require_unconsumed_for:
        entries = load_consumption_ledger(ledger_path)
        consumed = consumed_outcomes(entries, require_unconsumed_for)
        supporting = tuple(
            outcome
            for outcome in candidate
            if _supports_required_field(outcome, require_unconsumed_for)
            and outcome_key(outcome) not in consumed
        )
        if not supporting:
            failures.append(
                f"no unconsumed {require_unconsumed_for} signal found in candidate outcomes"
            )
    return (not failures, tuple(failures))


def render_validation_report(ok: bool, failures: tuple[str, ...]) -> str:
    lines = ["# Outcome Intake Validation", "", f"status: {'clean' if ok else 'blocked'}"]
    if failures:
        lines.extend(["", "Failures:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _suggest_record(
    outcomes: tuple[OutcomeRecord, ...],
    required_fields: tuple[str, ...] = (),
) -> OutcomeRecord:
    used_graphs = {outcome.graph_id for outcome in outcomes}
    if "coding-debug-seed" not in used_graphs:
        return OutcomeRecord(
            graph_id="coding-debug-seed",
            strategy="critical-path-a-star-v0",
            observed_quality=0.65 if "quality" in required_fields else 0.85,
            target_quality=0.8,
            actual_tokens=13000 if "token" in required_fields else 0,
            token_budget=12000,
            actual_minutes=95 if "minute" in required_fields else 0,
            time_budget_minutes=90,
            missed_optional_harm=0.2 if "missed_optional" in required_fields else 0.0,
            evidence_ref="REPLACE_WITH_OBSERVED_RUN_POINTER",
        )
    return OutcomeRecord(
        graph_id="research-synthesis-seed",
        strategy="critical-path-a-star-v0",
        observed_quality=0.65 if "quality" in required_fields else 0.85,
        target_quality=0.8,
        actual_tokens=18000 if "token" in required_fields else 0,
        token_budget=16000,
        actual_minutes=130 if "minute" in required_fields else 0,
        time_budget_minutes=120,
        missed_optional_harm=0.2 if "missed_optional" in required_fields else 0.0,
        evidence_ref="REPLACE_WITH_OBSERVED_RUN_POINTER",
    )


def _outcome_key(outcome: OutcomeRecord) -> str:
    return (
        f"{outcome.graph_id}/{outcome.strategy}: "
        f"tokens={outcome.actual_tokens}/{outcome.token_budget}, "
        f"minutes={outcome.actual_minutes}/{outcome.time_budget_minutes}, "
        f"quality={outcome.observed_quality}/{outcome.target_quality}"
    )


def _supports_required_field(outcome: OutcomeRecord, field: str) -> bool:
    if field == "quality":
        return outcome.observed_quality < outcome.target_quality
    if field == "token":
        return outcome.actual_tokens > outcome.token_budget
    if field == "minute":
        return outcome.actual_minutes > outcome.time_budget_minutes
    if field == "missed_optional":
        return outcome.missed_optional_harm > 0
    return False


def _is_placeholder_evidence_ref(value: str) -> bool:
    stripped = value.strip()
    return not stripped or stripped == "REPLACE_WITH_OBSERVED_RUN_POINTER"


def _capture_command(outcome: OutcomeRecord) -> str:
    return (
        "python -m reopt.observed_run "
        f"--graph-id {outcome.graph_id} "
        f"--strategy {outcome.strategy} "
        f"--observed-quality {outcome.observed_quality} "
        f"--target-quality {outcome.target_quality} "
        f"--token-budget {outcome.token_budget} "
        "--goal-before docs/outcome-evidence/goal-before.json "
        "--goal-after docs/outcome-evidence/goal-after.json "
        f"--time-budget-minutes {outcome.time_budget_minutes} "
        f"--missed-optional-harm {outcome.missed_optional_harm} "
        "--evidence-ref OBSERVED_RUN_POINTER "
        f"{_capture_signal_flags(outcome)}"
        "--write outcomes/next-outcome.json "
        "--write-report docs/outcome-evidence/observed-run-capture.md"
    )


def _capture_signal_flags(outcome: OutcomeRecord) -> str:
    flags = []
    if outcome.actual_tokens > outcome.token_budget:
        flags.append("--require-signal token")
    if outcome.actual_minutes > outcome.time_budget_minutes:
        flags.append("--require-signal minute")
    if outcome.missed_optional_harm > 0:
        flags.append("--require-signal missed_optional")
    return " ".join(flags) + (" " if flags else "")


def _required_unconsumed_fields(next_target: str) -> tuple[str, ...]:
    fields = []
    for field in ("quality", "token", "minute", "missed_optional"):
        if f"--require-unconsumed-for {field}" in next_target:
            fields.append(field)
    if not fields and "unconsumed outcome evidence" in next_target:
        fields.append("quality")
    return tuple(fields)


def _required_signal_text(field: str) -> str:
    if field == "quality":
        return (
            "At least one new outcome must have observed_quality below target_quality, "
            "and that outcome must not already be consumed for quality."
        )
    if field == "token":
        return (
            "At least one new outcome must have actual_tokens above token_budget, "
            "and that outcome must not already be consumed for token."
        )
    if field == "minute":
        return (
            "At least one new outcome must have actual_minutes above time_budget_minutes, "
            "and that outcome must not already be consumed for minute."
        )
    if field == "missed_optional":
        return (
            "At least one new outcome must have missed_optional_harm above 0, "
            "and that outcome must not already be consumed for missed_optional."
        )
    raise ValueError(f"Unsupported required signal field: {field}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the next outcome intake request.")
    parser.add_argument(
        "--outcomes",
        type=Path,
        default=Path("outcomes/seed-outcomes.json"),
        help="Existing outcome JSON path.",
    )
    parser.add_argument(
        "--next-target",
        type=Path,
        default=Path("docs/next-target.md"),
        help="Current next-target Markdown path.",
    )
    parser.add_argument("--write", type=Path, help="Write the intake Markdown file.")
    parser.add_argument("--validate", type=Path, help="Validate a filled outcome JSON file.")
    parser.add_argument(
        "--require-unconsumed-for",
        choices=("quality", "token", "minute", "missed_optional"),
        help="Require a new unconsumed signal for a specific weight field.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Outcome-consumption ledger JSON path.",
    )
    parser.add_argument(
        "--require-evidence-ref",
        action="store_true",
        help="Require each candidate record to include a non-placeholder evidence_ref.",
    )
    args = parser.parse_args()
    if args.validate:
        ok, failures = validate_outcome_intake(
            args.validate,
            args.outcomes,
            args.require_unconsumed_for,
            args.ledger,
            args.require_evidence_ref,
        )
        print(render_validation_report(ok, failures))
        raise SystemExit(0 if ok else 1)

    rendered = render_outcome_intake(suggest_outcome_intake(args.outcomes, args.next_target))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
