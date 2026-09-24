"""Normalize Codex goal output for observed-run capture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def normalize_goal_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    goal = raw.get("goal", raw)
    normalized = {
        "goal": {
            "tokensUsed": int(goal["tokensUsed"]),
            "timeUsedSeconds": int(goal["timeUsedSeconds"]),
            "status": str(goal.get("status", "")),
        }
    }
    if "updatedAt" in goal:
        normalized["goal"]["updatedAt"] = int(goal["updatedAt"])
    return normalized


def render_goal_snapshot(raw_json: str) -> str:
    raw = json.loads(raw_json)
    return json.dumps(normalize_goal_snapshot(raw), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a Codex get_goal JSON snapshot.")
    parser.add_argument(
        "--input",
        type=Path,
        help="Read get_goal JSON from a file. Defaults to stdin.",
    )
    parser.add_argument("--write", type=Path, help="Write normalized snapshot JSON.")
    args = parser.parse_args()

    raw_json = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
    rendered = render_goal_snapshot(raw_json)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
