"""Search for a safe cap on proposed utility-weight increments."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .adopt import adoption_checklist
from .diff import load_export
from .export import export_seed_runs_json
from .models import UtilityWeights
from .outcomes import dump_utility_weights, load_utility_weights
from .regression import DEFAULT_BASELINE, find_regression_failures


def capped_weights(
    base: UtilityWeights,
    proposed: UtilityWeights,
    ratio: float,
) -> UtilityWeights:
    changed = {
        field: round(
            getattr(base, field) + (getattr(proposed, field) - getattr(base, field)) * ratio,
            7,
        )
        for field in base.to_dict()
        if getattr(base, field) != getattr(proposed, field)
    }
    return replace(base, **changed)


def find_largest_clean_cap(
    proposed_weights: UtilityWeights,
    baseline_path: Path = DEFAULT_BASELINE,
    *,
    step: float = 0.001,
) -> tuple[float, UtilityWeights]:
    base = _baseline_weights(load_export(baseline_path))
    best_ratio = 0.0
    best_weights = base
    steps = int(1 / step)
    for index in range(1, steps + 1):
        ratio = round(index * step, 6)
        candidate = capped_weights(base, proposed_weights, ratio)
        if _is_clean(candidate, baseline_path):
            best_ratio = ratio
            best_weights = candidate
        else:
            break
    return best_ratio, best_weights


def render_cap_report(
    proposed_path: Path,
    output_weights_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
    *,
    step: float = 0.001,
) -> str:
    proposed = load_utility_weights(proposed_path)
    base = _baseline_weights(load_export(baseline_path))
    ratio, weights = find_largest_clean_cap(proposed, baseline_path, step=step)
    dump_utility_weights(output_weights_path, weights)
    lines = [
        "# Utility Increment Cap Review",
        "",
        f"proposed_weights: {proposed_path.as_posix()}",
        f"baseline: {baseline_path.as_posix()}",
        f"capped_weights: {output_weights_path.as_posix()}",
        f"largest_clean_ratio: {ratio:.3f}",
        "",
        "Changed weights:",
        "",
        "| Weight | Baseline | Proposed | Capped |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field in base.to_dict():
        current = getattr(base, field)
        proposed_value = getattr(proposed, field)
        capped_value = getattr(weights, field)
        if current != proposed_value:
            lines.append(f"| {field} | {current} | {proposed_value} | {capped_value} |")
    lines.extend(["", adoption_checklist(output_weights_path, baseline_path).rstrip()])
    return "\n".join(lines) + "\n"


def _is_clean(weights: UtilityWeights, baseline_path: Path) -> bool:
    baseline = load_export(baseline_path)
    current: list[dict[str, Any]] = json.loads(
        export_seed_runs_json(utility_weights=weights)
    )
    failures = find_regression_failures(
        baseline,
        current,
        allow_strategy_change=False,
        allow_warning_increase=False,
    )
    return not failures


def _baseline_weights(baseline: list[dict[str, Any]]) -> UtilityWeights:
    if not baseline:
        return UtilityWeights()
    return UtilityWeights.from_dict(
        baseline[0].get("utility_weights", UtilityWeights().to_dict())
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Search for clean capped utility increments.")
    parser.add_argument("proposed_weights", type=Path)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.001,
        help="Cap-ratio grid step.",
    )
    parser.add_argument(
        "--write-weights",
        type=Path,
        default=Path("weights/proposed-capped-expanded-evidence.json"),
        help="Write the largest clean capped weights.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the cap review report.")
    args = parser.parse_args()
    report = render_cap_report(
        args.proposed_weights,
        args.write_weights,
        args.baseline,
        step=args.step,
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
