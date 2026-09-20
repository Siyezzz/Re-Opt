"""Review proposed utility weights under expanded outcome evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from .adopt import adoption_checklist
from .outcome_intake import render_validation_report, validate_outcome_intake
from .outcomes import (
    OutcomeRecord,
    calibration_report,
    dump_outcomes,
    dump_utility_weights,
    load_outcomes,
    propose_utility_weights,
)
from .models import UtilityWeights
from .regression import DEFAULT_BASELINE


def simulated_next_outcome() -> OutcomeRecord:
    return OutcomeRecord(
        graph_id="coding-debug-seed",
        strategy="critical-path-a-star-v0",
        observed_quality=0.85,
        target_quality=0.8,
        actual_tokens=9000,
        token_budget=12000,
        actual_minutes=88,
        time_budget_minutes=90,
        missed_optional_harm=0.0,
    )


def write_simulated_outcome(path: Path) -> None:
    dump_outcomes(path, (simulated_next_outcome(),))


def review_expanded_evidence(
    candidate_path: Path,
    proposed_weights_path: Path,
    existing_path: Path = Path("outcomes/seed-outcomes.json"),
    baseline_path: Path = DEFAULT_BASELINE,
) -> str:
    existing = load_outcomes(existing_path)
    candidate = load_outcomes(candidate_path)
    ok, failures = validate_outcome_intake(candidate_path, existing_path)
    combined = existing + candidate
    proposed = propose_utility_weights(UtilityWeights(), combined)
    dump_utility_weights(proposed_weights_path, proposed)

    lines = [
        "# Expanded Outcome Evidence Review",
        "",
        f"candidate: {candidate_path.as_posix()}",
        f"existing: {existing_path.as_posix()}",
        f"proposed_weights: {proposed_weights_path.as_posix()}",
        "source: synthetic simulation",
        "",
        render_validation_report(ok, failures).rstrip(),
        "",
        calibration_report(UtilityWeights(), proposed, combined).rstrip(),
        "",
        adoption_checklist(proposed_weights_path, baseline_path).rstrip(),
        "",
        "Interpretation:",
        "",
    ]
    if ok:
        lines.append(
            "- The synthetic outcome is validation-clean, but it is not observed evidence."
        )
    else:
        lines.append("- The candidate outcome is not valid enough for calibration.")
    lines.append(
        "- Treat this review as a planning probe; do not adopt weights from synthetic evidence alone."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Review expanded outcome evidence.")
    parser.add_argument(
        "--existing",
        type=Path,
        default=Path("outcomes/seed-outcomes.json"),
        help="Existing outcome JSON path.",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("outcomes/simulated-next-outcome.json"),
        help="Candidate outcome JSON path.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument(
        "--write-simulated",
        action="store_true",
        help="Write the built-in synthetic candidate outcome before review.",
    )
    parser.add_argument(
        "--write-weights",
        type=Path,
        default=Path("weights/proposed-expanded-evidence.json"),
        help="Write proposed utility weights from combined outcomes.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the review report.")
    args = parser.parse_args()

    if args.write_simulated:
        write_simulated_outcome(args.candidate)
    report = review_expanded_evidence(
        args.candidate,
        args.write_weights,
        args.existing,
        args.baseline,
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
