"""Compare current seed optimization output against a committed baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .diff import diff_exports, load_export
from .export import export_seed_runs_json

DEFAULT_BASELINE = Path("benchmark-results/seed-baseline.json")


def compare_seed_baseline(baseline_path: Path = DEFAULT_BASELINE) -> str:
    baseline = load_export(baseline_path)
    current: list[dict[str, Any]] = json.loads(export_seed_runs_json())
    return diff_exports(baseline, current)


def check_seed_baseline(
    baseline_path: Path = DEFAULT_BASELINE,
    *,
    allow_strategy_change: bool = False,
    allow_warning_increase: bool = False,
) -> tuple[bool, list[str], str]:
    baseline = load_export(baseline_path)
    current: list[dict[str, Any]] = json.loads(export_seed_runs_json())
    diff = diff_exports(baseline, current)
    failures = _find_failures(
        baseline,
        current,
        allow_strategy_change=allow_strategy_change,
        allow_warning_increase=allow_warning_increase,
    )
    return (not failures, failures, diff)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare current Re-Opt seed runs against a baseline snapshot."
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 on unapproved strategy changes, utility drops, or warning increases.",
    )
    parser.add_argument(
        "--allow-strategy-change",
        action="store_true",
        help="Do not fail --check when the selected strategy changes.",
    )
    parser.add_argument(
        "--allow-warning-increase",
        action="store_true",
        help="Do not fail --check when candidate warning count increases.",
    )
    args = parser.parse_args()
    if args.check:
        ok, failures, diff = check_seed_baseline(
            args.baseline,
            allow_strategy_change=args.allow_strategy_change,
            allow_warning_increase=args.allow_warning_increase,
        )
        print(diff)
        if failures:
            print("Regression gate failures:")
            for failure in failures:
                print(f"- {failure}")
        sys.exit(0 if ok else 1)

    print(compare_seed_baseline(args.baseline))


def _find_failures(
    baseline: list[dict[str, Any]],
    current: list[dict[str, Any]],
    *,
    allow_strategy_change: bool,
    allow_warning_increase: bool,
) -> list[str]:
    failures: list[str] = []
    baseline_by_objective = {run["objective"]: run for run in baseline}
    current_by_objective = {run["objective"]: run for run in current}

    for objective in sorted(set(baseline_by_objective) | set(current_by_objective)):
        left = baseline_by_objective.get(objective)
        right = current_by_objective.get(objective)
        if left is None:
            failures.append(f"{objective}: new objective added")
            continue
        if right is None:
            failures.append(f"{objective}: objective removed")
            continue

        if (
            left["selected_strategy"] != right["selected_strategy"]
            and not allow_strategy_change
        ):
            failures.append(
                f"{objective}: strategy changed from "
                f"{left['selected_strategy']} to {right['selected_strategy']}"
            )

        utility_delta = float(right["selected_utility"]) - float(left["selected_utility"])
        if utility_delta < 0:
            failures.append(f"{objective}: utility dropped by {utility_delta:.3f}")

        warning_delta = _warning_count(right) - _warning_count(left)
        if warning_delta > 0 and not allow_warning_increase:
            failures.append(f"{objective}: warnings increased by {warning_delta}")

    return failures


def _warning_count(run: dict[str, Any]) -> int:
    return sum(len(score.get("warnings", [])) for score in run["candidate_scores"])


if __name__ == "__main__":
    main()
