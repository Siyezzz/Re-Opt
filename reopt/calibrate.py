"""Preview outcome-driven utility-weight changes without adopting them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .diff import diff_exports, load_export
from .export import export_seed_runs_json
from .models import UtilityWeights
from .outcomes import (
    calibration_report,
    dump_utility_weights,
    load_outcomes,
    propose_utility_weights,
)
from .regression import DEFAULT_BASELINE


def preview_calibration(
    outcomes_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
) -> str:
    outcomes = load_outcomes(outcomes_path)
    base = UtilityWeights()
    proposed = propose_utility_weights(base, outcomes)
    baseline = load_export(baseline_path)
    candidate: list[dict[str, Any]] = json.loads(
        export_seed_runs_json(utility_weights=proposed)
    )
    return (
        calibration_report(base, proposed, outcomes)
        + "\n"
        + "# Proposed Weight Regression Preview\n\n"
        + diff_exports(baseline, candidate)
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview Re-Opt benchmark effects from outcome-calibrated weights."
    )
    parser.add_argument("outcomes", type=Path, help="Outcome JSON file.")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument(
        "--write-weights",
        type=Path,
        help="Write proposed utility weights to a JSON file.",
    )
    args = parser.parse_args()
    if args.write_weights:
        outcomes = load_outcomes(args.outcomes)
        proposed = propose_utility_weights(UtilityWeights(), outcomes)
        dump_utility_weights(args.write_weights, proposed)
    print(preview_calibration(args.outcomes, args.baseline))


if __name__ == "__main__":
    main()
