"""Compare JSON optimization exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def diff_exports(left_runs: list[dict[str, Any]], right_runs: list[dict[str, Any]]) -> str:
    left_by_objective = {run["objective"]: run for run in left_runs}
    right_by_objective = {run["objective"]: run for run in right_runs}
    objectives = sorted(set(left_by_objective) | set(right_by_objective))
    lines = ["# Optimization Export Diff", ""]

    for objective in objectives:
        left = left_by_objective.get(objective)
        right = right_by_objective.get(objective)
        lines.append(f"## {objective}")
        if left is None:
            lines.extend(["", "Added in right export.", ""])
            continue
        if right is None:
            lines.extend(["", "Removed from right export.", ""])
            continue

        left_strategy = left["selected_strategy"]
        right_strategy = right["selected_strategy"]
        left_utility = float(left.get("selected_utility", 0.0))
        right_utility = float(right.get("selected_utility", 0.0))
        delta = round(right_utility - left_utility, 3)
        strategy_change = (
            "unchanged"
            if left_strategy == right_strategy
            else f"{left_strategy} -> {right_strategy}"
        )
        lines.extend(
            [
                "",
                f"- strategy: {strategy_change}",
                f"- utility_delta: {delta:+.3f}",
                f"- warning_delta: {_warning_delta(left, right):+d}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def load_export(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Re-Opt JSON exports.")
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    print(diff_exports(load_export(args.left), load_export(args.right)))


def _warning_delta(left: dict[str, Any], right: dict[str, Any]) -> int:
    left_count = sum(len(score.get("warnings", [])) for score in left["candidate_scores"])
    right_count = sum(len(score.get("warnings", [])) for score in right["candidate_scores"])
    return right_count - left_count


if __name__ == "__main__":
    main()
