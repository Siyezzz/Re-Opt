"""Generate an adoption checklist for proposed utility weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .diff import diff_exports, load_export
from .export import export_seed_runs_json
from .outcomes import load_utility_weights
from .regression import DEFAULT_BASELINE, find_regression_failures


def adoption_checklist(
    weights_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
) -> str:
    weights = load_utility_weights(weights_path)
    baseline = load_export(baseline_path)
    candidate: list[dict[str, Any]] = json.loads(
        export_seed_runs_json(utility_weights=weights)
    )
    failures = find_regression_failures(
        baseline,
        candidate,
        allow_strategy_change=False,
        allow_warning_increase=False,
    )
    status = "blocked" if failures else "clean"
    lines = [
        "# Utility Weight Adoption Checklist",
        "",
        f"weights: {weights_path}",
        f"baseline: {baseline_path}",
        f"status: {status}",
        "",
    ]
    if failures:
        lines.extend(["Blocking regression signals:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
        lines.append("")
    lines.extend(
        [
            "Required adoption steps:",
            "",
            "- Review the calibration report and regression preview.",
            "- Confirm strategy changes, utility drops, and warning changes are intended.",
            "- Commit the proposed weights only with an updated baseline snapshot.",
            "- Record the adoption rationale in the iteration log and SEA.",
            "",
            diff_exports(baseline, candidate).rstrip(),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a checklist for adopting proposed Re-Opt utility weights."
    )
    parser.add_argument("weights", type=Path, help="Proposed utility-weight JSON file.")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    args = parser.parse_args()
    print(adoption_checklist(args.weights, args.baseline))


if __name__ == "__main__":
    main()
