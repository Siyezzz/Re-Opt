"""Review utility-weight proposals from a fresh observed outcome."""

from __future__ import annotations

import argparse
from pathlib import Path

from .adopt import adoption_checklist
from .outcome_intake import render_validation_report, validate_outcome_intake
from .outcomes import (
    calibration_report,
    dump_utility_weights,
    load_outcomes,
    propose_utility_weights,
)
from .models import UtilityWeights
from .regression import DEFAULT_BASELINE


def review_observed_evidence(
    candidate_path: Path,
    proposed_weights_path: Path,
    existing_path: Path = Path("outcomes/seed-outcomes.json"),
    baseline_path: Path = DEFAULT_BASELINE,
    provenance: str = "manual observed task review",
) -> str:
    existing = load_outcomes(existing_path)
    candidate = load_outcomes(candidate_path)
    ok, failures = validate_outcome_intake(candidate_path, existing_path)
    combined = existing + candidate
    proposed = propose_utility_weights(UtilityWeights(), combined)
    dump_utility_weights(proposed_weights_path, proposed)

    lines = [
        "# Observed Outcome Evidence Review",
        "",
        f"candidate: {candidate_path.as_posix()}",
        f"existing: {existing_path.as_posix()}",
        f"proposed_weights: {proposed_weights_path.as_posix()}",
        "source: observed task run",
        f"provenance: {provenance}",
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
            "- The candidate outcome is validation-clean and can be used as observed calibration evidence."
        )
    else:
        lines.append("- The candidate outcome is not valid enough for calibration.")
    lines.append(
        "- Adoption still depends on the regression checklist; observed evidence is not automatic approval."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Review observed outcome evidence.")
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
        help="Candidate observed outcome JSON path.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument(
        "--write-weights",
        type=Path,
        default=Path("weights/proposed-observed-evidence.json"),
        help="Write proposed utility weights from combined observed outcomes.",
    )
    parser.add_argument(
        "--provenance",
        default="manual observed task review",
        help="Short evidence pointer for the observed outcome.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the review report.")
    args = parser.parse_args()

    report = review_observed_evidence(
        args.candidate,
        args.write_weights,
        args.existing,
        args.baseline,
        args.provenance,
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
