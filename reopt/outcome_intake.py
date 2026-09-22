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
    require_unconsumed_quality = "unconsumed outcome evidence" in next_target
    suggested = _suggest_record(outcomes, require_quality_gap=require_unconsumed_quality)
    required_signals = (
        (
            "At least one new outcome must have observed_quality below target_quality, "
            "and that outcome must not already be consumed for quality."
        ),
    ) if require_unconsumed_quality else ()
    validation_command = "python -m reopt.outcome_intake --validate outcomes/next-outcome.json"
    if require_unconsumed_quality:
        validation_command += " --require-unconsumed-for quality"
    return OutcomeIntakeRequest(
        title=(
            "Collect unconsumed quality evidence"
            if require_unconsumed_quality
            else "Collect a new outcome before more weight changes"
        ),
        rationale=(
            "The next target asks for a quality signal that has not already been "
            "used to justify a quality-weight adoption. A fresh outcome should "
            "show an observed quality gap before the quality weight is raised again."
            if require_unconsumed_quality
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
            validation_command,
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
    require_quality_gap: bool = False,
) -> OutcomeRecord:
    used_graphs = {outcome.graph_id for outcome in outcomes}
    if "coding-debug-seed" not in used_graphs:
        return OutcomeRecord(
            graph_id="coding-debug-seed",
            strategy="critical-path-a-star-v0",
            observed_quality=0.65 if require_quality_gap else 0.0,
            target_quality=0.8,
            actual_tokens=0,
            token_budget=12000,
            actual_minutes=0,
            time_budget_minutes=90,
            missed_optional_harm=0.0,
        )
    return OutcomeRecord(
        graph_id="research-synthesis-seed",
        strategy="critical-path-a-star-v0",
        observed_quality=0.65 if require_quality_gap else 0.0,
        target_quality=0.8,
        actual_tokens=0,
        token_budget=16000,
        actual_minutes=0,
        time_budget_minutes=120,
        missed_optional_harm=0.0,
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
    args = parser.parse_args()
    if args.validate:
        ok, failures = validate_outcome_intake(
            args.validate,
            args.outcomes,
            args.require_unconsumed_for,
            args.ledger,
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
