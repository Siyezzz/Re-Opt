"""Compare current seed optimization output against a committed baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .diff import diff_exports, load_export
from .export import export_seed_runs_json

DEFAULT_BASELINE = Path("benchmark-results/seed-baseline.json")


def compare_seed_baseline(baseline_path: Path = DEFAULT_BASELINE) -> str:
    baseline = load_export(baseline_path)
    current: list[dict[str, Any]] = json.loads(export_seed_runs_json())
    return diff_exports(baseline, current)


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
    args = parser.parse_args()
    print(compare_seed_baseline(args.baseline))


if __name__ == "__main__":
    main()
