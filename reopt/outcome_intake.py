"""Generate the next outcome-evidence intake request."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .outcomes import OutcomeRecord, load_outcomes


@dataclass(frozen=True)
class OutcomeIntakeRequest:
    title: str
    rationale: str
    avoid_reusing: tuple[str, ...]
    required_fields: tuple[str, ...]
    suggested_record: OutcomeRecord
    suggested_commands: tuple[str, ...]


def suggest_outcome_intake(
    outcomes_path: Path = Path("outcomes/seed-outcomes.json"),
    next_target_path: Path = Path("docs/next-target.md"),
) -> OutcomeIntakeRequest:
    outcomes = load_outcomes(outcomes_path)
    next_target_path.read_text(encoding="utf-8")
    avoid_reusing = tuple(_outcome_key(outcome) for outcome in outcomes)
    suggested = _suggest_record(outcomes)
    return OutcomeIntakeRequest(
        title="Collect a new outcome before more weight changes",
        rationale=(
            "The next target asks for evidence before changing the remaining blocked "
            "weight increments. A new outcome should come from a different task shape "
            "or a fresh run, so calibration does not repeatedly consume the same "
            "tight-research observation."
        ),
        avoid_reusing=avoid_reusing,
        required_fields=tuple(asdict(suggested)),
        suggested_record=suggested,
        suggested_commands=(
            "python -m reopt.outcome_intake --validate outcomes/next-outcome.json",
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
) -> tuple[bool, tuple[str, ...]]:
    existing = {_outcome_key(outcome) for outcome in load_outcomes(existing_path)}
    failures: list[str] = []
    for index, outcome in enumerate(load_outcomes(candidate_path), start=1):
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
    return (not failures, tuple(failures))


def render_validation_report(ok: bool, failures: tuple[str, ...]) -> str:
    lines = ["# Outcome Intake Validation", "", f"status: {'clean' if ok else 'blocked'}"]
    if failures:
        lines.extend(["", "Failures:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _suggest_record(outcomes: tuple[OutcomeRecord, ...]) -> OutcomeRecord:
    used_graphs = {outcome.graph_id for outcome in outcomes}
    if "coding-debug-seed" not in used_graphs:
        return OutcomeRecord(
            graph_id="coding-debug-seed",
            strategy="critical-path-a-star-v0",
            observed_quality=0.0,
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
        observed_quality=0.0,
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
    args = parser.parse_args()
    if args.validate:
        ok, failures = validate_outcome_intake(args.validate, args.outcomes)
        print(render_validation_report(ok, failures))
        raise SystemExit(0 if ok else 1)

    rendered = render_outcome_intake(suggest_outcome_intake(args.outcomes, args.next_target))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
