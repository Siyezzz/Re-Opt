"""Write benchmark export snapshots."""

from __future__ import annotations

import argparse
from pathlib import Path

from .export import export_seed_runs_json


def write_seed_snapshot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(export_seed_runs_json() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Re-Opt benchmark snapshots.")
    parser.add_argument(
        "path",
        type=Path,
        help="Destination JSON path, for example benchmark-results/seed-current.json.",
    )
    args = parser.parse_args()
    write_seed_snapshot(args.path)
    print(f"wrote optimization snapshot to {args.path}")


if __name__ == "__main__":
    main()
