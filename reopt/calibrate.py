"""Preview outcome-driven utility-weight changes without adopting them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .diff import diff_exports, load_export
from .export import export_seed_runs_json
from .models import UtilityWeights
from .outcome_consumption import (
    consumed_outcomes,
    load_consumption_ledger,
)
from .outcomes import (
    calibration_report,
    consumption_adjusted_report,
    dump_utility_weights,
    load_outcomes,
    propose_utility_weights,
    propose_utility_weights_with_consumption,
)
from .regression import DEFAULT_BASELINE


def preview_calibration(
    outcomes_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
    ledger_path: Path | None = None,
) -> str:
    outcomes = load_outcomes(outcomes_path)
    base = UtilityWeights()
    if ledger_path:
        consumed_by_field = {
            field: consumed_outcomes(load_consumption_ledger(ledger_path), field)
            for field in ("quality", "token", "minute", "missed_optional")
        }
        proposed = propose_utility_weights_with_consumption(base, outcomes, consumed_by_field)
        report = consumption_adjusted_report(base, proposed, outcomes, consumed_by_field)
    else:
        proposed = propose_utility_weights(base, outcomes)
        report = calibration_report(base, proposed, outcomes)
    baseline = load_export(baseline_path)
    candidate: list[dict[str, Any]] = json.loads(
        export_seed_runs_json(utility_weights=proposed)
    )
    return (
        report
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
    parser.add_argument(
        "--ledger",
        type=Path,
        help="Outcome-consumption ledger. When set, consumed signals are excluded.",
    )
    args = parser.parse_args()
    if args.write_weights:
        outcomes = load_outcomes(args.outcomes)
        if args.ledger:
            consumed_by_field = {
                field: consumed_outcomes(load_consumption_ledger(args.ledger), field)
                for field in ("quality", "token", "minute", "missed_optional")
            }
            proposed = propose_utility_weights_with_consumption(
                UtilityWeights(),
                outcomes,
                consumed_by_field,
            )
        else:
            proposed = propose_utility_weights(UtilityWeights(), outcomes)
        dump_utility_weights(args.write_weights, proposed)
    print(preview_calibration(args.outcomes, args.baseline, args.ledger))


if __name__ == "__main__":
    main()
