"""Audit whether proposed weight changes reuse already-consumed outcome evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .diff import load_export
from .outcomes import OutcomeRecord, load_outcomes, load_utility_weights
from .regression import DEFAULT_BASELINE


DEFAULT_LEDGER = Path("docs/outcome-consumption/ledger.json")


@dataclass(frozen=True)
class ConsumptionEntry:
    adoption: str
    weights: str
    consumed_fields: tuple[str, ...]
    outcomes: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class ConsumptionAudit:
    weights: Path
    status: str
    changed_fields: tuple[str, ...]
    blocked_fields: tuple[str, ...]
    warnings: tuple[str, ...]
    ledger: Path


def audit_consumption(
    weights_path: Path,
    existing_path: Path = Path("outcomes/seed-outcomes.json"),
    candidate_path: Path = Path("outcomes/next-outcome.json"),
    ledger_path: Path = DEFAULT_LEDGER,
    baseline_path: Path = DEFAULT_BASELINE,
) -> ConsumptionAudit:
    weights = load_utility_weights(weights_path)
    baseline = load_export(baseline_path)
    baseline_weights = baseline[0]["utility_weights"] if baseline else {}
    changed_fields = tuple(
        field
        for field, value in weights.to_dict().items()
        if baseline_weights.get(field) != value
    )
    outcomes = load_outcomes(existing_path) + load_outcomes(candidate_path)
    entries = load_consumption_ledger(ledger_path)
    blocked_fields: list[str] = []
    warnings: list[str] = []

    for field in changed_fields:
        supporting = tuple(
            outcome_key(outcome) for outcome in outcomes if _supports_field(outcome, field)
        )
        consumed = consumed_outcomes(entries, field)
        unconsumed = tuple(key for key in supporting if key not in consumed)
        if supporting and not unconsumed:
            blocked_fields.append(field)
            warnings.append(
                f"{field}: every supporting outcome has already been consumed for this field"
            )
        elif not supporting:
            blocked_fields.append(field)
            warnings.append(f"{field}: no outcome signal supports this changed field")
        elif consumed:
            warnings.append(
                f"{field}: {len(supporting) - len(unconsumed)} supporting outcome(s) already consumed"
            )

    return ConsumptionAudit(
        weights=weights_path,
        status="blocked" if blocked_fields else "clean",
        changed_fields=changed_fields,
        blocked_fields=tuple(blocked_fields),
        warnings=tuple(warnings),
        ledger=ledger_path,
    )


def load_consumption_ledger(path: Path) -> tuple[ConsumptionEntry, ...]:
    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        ConsumptionEntry(
            adoption=item["adoption"],
            weights=item["weights"],
            consumed_fields=tuple(item["consumed_fields"]),
            outcomes=tuple(item["outcomes"]),
            rationale=item["rationale"],
        )
        for item in data
    )


def consumed_outcomes(entries: tuple[ConsumptionEntry, ...], field: str) -> set[str]:
    consumed: set[str] = set()
    for entry in entries:
        if field in entry.consumed_fields:
            consumed.update(entry.outcomes)
    return consumed


def render_consumption_audit(audit: ConsumptionAudit) -> str:
    lines = [
        "# Outcome Consumption Audit",
        "",
        f"weights: {audit.weights.as_posix()}",
        f"ledger: {audit.ledger.as_posix()}",
        f"status: {audit.status}",
        "",
        "Changed fields:",
        "",
    ]
    if audit.changed_fields:
        for field in audit.changed_fields:
            lines.append(f"- {field}")
    else:
        lines.append("- _none_")
    lines.extend(["", "Blocked fields:", ""])
    if audit.blocked_fields:
        for field in audit.blocked_fields:
            lines.append(f"- {field}")
    else:
        lines.append("- _none_")
    lines.extend(["", "Warnings:", ""])
    if audit.warnings:
        for warning in audit.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- _none_")
    return "\n".join(lines) + "\n"


def outcome_key(outcome: OutcomeRecord) -> str:
    return (
        f"{outcome.graph_id}/{outcome.strategy}: "
        f"tokens={outcome.actual_tokens}/{outcome.token_budget}, "
        f"minutes={outcome.actual_minutes}/{outcome.time_budget_minutes}, "
        f"quality={outcome.observed_quality}/{outcome.target_quality}"
    )


def _supports_field(outcome: OutcomeRecord, field: str) -> bool:
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
    parser = argparse.ArgumentParser(description="Audit outcome consumption for a weight proposal.")
    parser.add_argument("weights", type=Path, help="Proposed utility-weight JSON file.")
    parser.add_argument(
        "--existing",
        type=Path,
        default=Path("outcomes/seed-outcomes.json"),
        help="Existing outcome JSON path.",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("outcomes/next-outcome.json"),
        help="Candidate outcome JSON path.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Outcome-consumption ledger JSON path.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the audit to Markdown.")
    args = parser.parse_args()
    rendered = render_consumption_audit(
        audit_consumption(
            args.weights,
            args.existing,
            args.candidate,
            args.ledger,
            args.baseline,
        )
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
