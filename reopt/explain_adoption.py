"""Explain blocked utility-weight adoption proposals."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .diff import load_export
from .export import export_seed_runs_json
from .models import UtilityWeights
from .outcomes import dump_utility_weights, load_utility_weights
from .regression import DEFAULT_BASELINE, find_regression_failures


def explain_blocked_adoption(
    weights_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
) -> str:
    baseline = load_export(baseline_path)
    base_weights = _baseline_weights(baseline)
    proposed_weights = load_utility_weights(weights_path)
    proposed = _export_with_weights(proposed_weights)
    failures = find_regression_failures(
        baseline,
        proposed,
        allow_strategy_change=False,
        allow_warning_increase=False,
    )
    changed_fields = _changed_fields(base_weights, proposed_weights)
    field_deltas = {
        field: _selected_utility_deltas(
            baseline,
            _export_with_weights(
                replace(base_weights, **{field: getattr(proposed_weights, field)})
            ),
        )
        for field in changed_fields
    }
    experiment = propose_smaller_experiment(base_weights, proposed_weights, baseline)

    lines = [
        "# Blocked Adoption Explanation",
        "",
        f"weights: {_portable(weights_path)}",
        f"baseline: {_portable(baseline_path)}",
        f"status: {'blocked' if failures else 'clean'}",
        "",
    ]
    if failures:
        lines.extend(["Blocking regression signals:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
        lines.append("")
    lines.extend(
        [
            "Weight-level attribution:",
            "",
            "| Weight | Baseline | Proposed | Worst utility delta | Total utility delta |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for field in changed_fields:
        deltas = field_deltas[field]
        lines.append(
            f"| {field} | {getattr(base_weights, field)} | {getattr(proposed_weights, field)} | "
            f"{min(deltas.values()):+.3f} | {sum(deltas.values()):+.3f} |"
        )

    lines.extend(["", "Smaller reversible experiment:", ""])
    if experiment:
        field, weights = experiment
        lines.extend(
            [
                f"- Adopt only `{field}` first.",
                (
                    "- This keeps every seed utility delta non-negative while "
                    "preserving the best isolated improvement signal."
                ),
                "- Re-run adoption and regression before replacing the current baseline.",
                "",
                "Proposed smaller weights:",
                "",
            ]
        )
        for key, value in weights.to_dict().items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append(
            "- No single changed weight has non-negative utility deltas across all seed objectives."
        )
    return "\n".join(lines) + "\n"


def propose_smaller_experiment(
    base_weights: UtilityWeights,
    proposed_weights: UtilityWeights,
    baseline: list[dict[str, Any]],
) -> tuple[str, UtilityWeights] | None:
    candidates: list[tuple[float, str, UtilityWeights]] = []
    for field in _changed_fields(base_weights, proposed_weights):
        weights = replace(base_weights, **{field: getattr(proposed_weights, field)})
        deltas = _selected_utility_deltas(baseline, _export_with_weights(weights))
        if all(delta >= 0 for delta in deltas.values()):
            candidates.append((sum(deltas.values()), field, weights))
    if not candidates:
        return None
    _score, field, weights = max(candidates)
    return field, weights


def write_smaller_experiment(
    output_path: Path,
    weights_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
) -> bool:
    baseline = load_export(baseline_path)
    experiment = propose_smaller_experiment(
        _baseline_weights(baseline),
        load_utility_weights(weights_path),
        baseline,
    )
    if not experiment:
        return False
    _field, weights = experiment
    dump_utility_weights(output_path, weights)
    return True


def _selected_utility_deltas(
    baseline: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
) -> dict[str, float]:
    baseline_by_objective = {run["objective"]: run for run in baseline}
    return {
        run["objective"]: round(
            float(run["selected_utility"])
            - float(baseline_by_objective[run["objective"]]["selected_utility"]),
            3,
        )
        for run in candidate
        if run["objective"] in baseline_by_objective
    }


def _changed_fields(
    base_weights: UtilityWeights,
    proposed_weights: UtilityWeights,
) -> tuple[str, ...]:
    return tuple(
        field
        for field in base_weights.to_dict()
        if getattr(base_weights, field) != getattr(proposed_weights, field)
    )


def _baseline_weights(baseline: list[dict[str, Any]]) -> UtilityWeights:
    if not baseline:
        return UtilityWeights()
    return UtilityWeights.from_dict(
        baseline[0].get("utility_weights", UtilityWeights().to_dict())
    )


def _export_with_weights(weights: UtilityWeights) -> list[dict[str, Any]]:
    return json.loads(export_seed_runs_json(utility_weights=weights))


def _portable(path: Path) -> str:
    return path.as_posix()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explain blocked Re-Opt utility-weight adoption proposals."
    )
    parser.add_argument("weights", type=Path, help="Proposed utility-weight JSON file.")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON snapshot path.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the explanation report.")
    parser.add_argument(
        "--write-smaller-weights",
        type=Path,
        help="Write the smaller reversible experiment weights when one exists.",
    )
    args = parser.parse_args()

    report = explain_blocked_adoption(args.weights, args.baseline)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    if args.write_smaller_weights:
        args.write_smaller_weights.parent.mkdir(parents=True, exist_ok=True)
        if not write_smaller_experiment(
            args.write_smaller_weights,
            args.weights,
            args.baseline,
        ):
            raise SystemExit("No smaller reversible experiment found.")
    print(report)


if __name__ == "__main__":
    main()
