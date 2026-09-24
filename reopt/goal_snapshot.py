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


def goal_snapshot_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    before_goal = normalize_goal_snapshot(before)["goal"]
    after_goal = normalize_goal_snapshot(after)["goal"]
    token_delta = int(after_goal["tokensUsed"]) - int(before_goal["tokensUsed"])
    seconds_delta = int(after_goal["timeUsedSeconds"]) - int(before_goal["timeUsedSeconds"])
    if token_delta < 0:
        raise ValueError("after tokensUsed must be greater than or equal to before tokensUsed")
    if seconds_delta < 0:
        raise ValueError(
            "after timeUsedSeconds must be greater than or equal to before timeUsedSeconds"
        )
    return {
        "tokensUsedDelta": token_delta,
        "timeUsedSecondsDelta": seconds_delta,
        "timeUsedMinutesDelta": seconds_delta // 60,
    }


def render_goal_snapshot_delta(before_json: str, after_json: str) -> str:
    before = json.loads(before_json)
    after = json.loads(after_json)
    delta = goal_snapshot_delta(before, after)
    return json.dumps({"delta": delta}, indent=2, sort_keys=True) + "\n"


def delta_gate_failures(
    delta: dict[str, int],
    token_budget: int | None = None,
    time_budget_minutes: int | None = None,
) -> tuple[str, ...]:
    failures = []
    if token_budget is not None and delta["tokensUsedDelta"] <= token_budget:
        failures.append("token delta must be above token budget")
    if (
        time_budget_minutes is not None
        and delta["timeUsedMinutesDelta"] <= time_budget_minutes
    ):
        failures.append("minute delta must be above time budget")
    return tuple(failures)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a Codex get_goal JSON snapshot.")
    parser.add_argument(
        "--input",
        type=Path,
        help="Read get_goal JSON from a file. Defaults to stdin.",
    )
    parser.add_argument("--write", type=Path, help="Write normalized snapshot JSON.")
    parser.add_argument("--before", type=Path, help="Normalized or raw goal snapshot before a run.")
    parser.add_argument("--after", type=Path, help="Normalized or raw goal snapshot after a run.")
    parser.add_argument(
        "--require-token-over",
        type=int,
        help="Require tokensUsedDelta to exceed this token budget.",
    )
    parser.add_argument(
        "--require-minute-over",
        type=int,
        help="Require timeUsedMinutesDelta to exceed this minute budget.",
    )
    args = parser.parse_args()

    if args.before or args.after:
        if not (args.before and args.after):
            raise SystemExit("error: --before and --after must be provided together")
        before_json = args.before.read_text(encoding="utf-8")
        after_json = args.after.read_text(encoding="utf-8")
        rendered = render_goal_snapshot_delta(before_json, after_json)
        delta = json.loads(rendered)["delta"]
        failures = delta_gate_failures(
            delta,
            args.require_token_over,
            args.require_minute_over,
        )
        if failures:
            for failure in failures:
                print(f"error: {failure}")
            raise SystemExit(1)
        if args.write:
            args.write.parent.mkdir(parents=True, exist_ok=True)
            args.write.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return

    raw_json = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
    rendered = render_goal_snapshot(raw_json)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
