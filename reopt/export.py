"""Machine-readable exports for optimization runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmarks import load_seed_benchmarks
from .models import UtilityWeights
from .optimizer import optimization_run_to_dict, solve_optimization
from .outcomes import load_utility_weights


def export_seed_runs_json(utility_weights: UtilityWeights | None = None) -> str:
    runs = [
        optimization_run_to_dict(
            solve_optimization(graph, constraints, utility_weights=utility_weights)
        )
        for graph, constraints in load_seed_benchmarks()
    ]
    return json.dumps(runs, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Re-Opt seed optimization runs.")
    parser.add_argument(
        "--weights",
        type=Path,
        help="Optional utility-weight JSON file.",
    )
    args = parser.parse_args()
    weights = load_utility_weights(args.weights) if args.weights else None
    print(export_seed_runs_json(utility_weights=weights))


if __name__ == "__main__":
    main()
