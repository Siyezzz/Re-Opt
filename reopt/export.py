"""Machine-readable exports for optimization runs."""

from __future__ import annotations

import json

from .benchmarks import load_seed_benchmarks
from .optimizer import optimization_run_to_dict, solve_optimization


def export_seed_runs_json() -> str:
    runs = [
        optimization_run_to_dict(solve_optimization(graph, constraints))
        for graph, constraints in load_seed_benchmarks()
    ]
    return json.dumps(runs, indent=2, sort_keys=True)


def main() -> None:
    print(export_seed_runs_json())


if __name__ == "__main__":
    main()
