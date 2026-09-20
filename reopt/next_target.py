"""Suggest the next Re-Opt refinement target from current artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NextTarget:
    title: str
    rationale: str
    evidence: tuple[str, ...]
    suggested_commands: tuple[str, ...]


def suggest_next_target(
    iteration_log: Path = Path("docs/iteration-log.md"),
    adoption_index: Path = Path("docs/adoption-index.md"),
) -> NextTarget:
    log_text = iteration_log.read_text(encoding="utf-8")
    index_text = adoption_index.read_text(encoding="utf-8")
    latest_refinement = _last_next_refinement(log_text)
    blocked_reports = _reports_by_status(index_text, "blocked")
    clean_reports = _reports_by_status(index_text, "clean")
    adopted_reports = _reports_by_status(index_text, "adopted")

    if blocked_reports and adopted_reports:
        adopted_report_paths = tuple(report for report, _weights in adopted_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Gather evidence for remaining blocked weight increments",
            rationale=(
                "A smaller utility-weight experiment has been adopted, but the "
                "larger proposal still contains blocked increments. The next "
                "optimization should collect another outcome or split the remaining "
                "increments before changing more weights."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"adopted_reports={', '.join(adopted_report_paths)}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
            ),
            suggested_commands=(
                "python -m reopt.explain_adoption weights/proposed-seed.json",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports and clean_reports:
        clean_report_paths = tuple(report for report, _weights in clean_reports)
        first_clean_weights = _portable_path(clean_reports[0][1])
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Review the clean smaller adoption experiment",
            rationale=(
                "A blocked proposal now has at least one clean smaller experiment. "
                "The next optimization should decide whether to adopt that reversible "
                "step or gather more outcome evidence before changing the baseline."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"clean_reports={', '.join(clean_report_paths)}",
            ),
            suggested_commands=(
                f"python -m reopt.adopt {first_clean_weights}",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports:
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        first_blocked_weights = _portable_path(blocked_reports[0][1])
        return NextTarget(
            title="Explain and reduce blocked adoption proposals",
            rationale=(
                "The current self-evolution loop has at least one blocked proposed "
                "weight change. The next optimization should explain why it is "
                "blocked and propose a smaller reversible experiment."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
            ),
            suggested_commands=(
                f"python -m reopt.adopt {first_blocked_weights}",
                "python -m reopt.calibrate outcomes/seed-outcomes.json",
                "python -m reopt.regression --check",
            ),
        )

    return NextTarget(
        title="Follow latest iteration-log refinement",
        rationale="No blocked adoption reports were found, so follow the latest logged refinement.",
        evidence=(f"latest_next_refinement={latest_refinement}",),
        suggested_commands=(
            "python -m unittest discover -s tests",
            "python -m reopt.regression --check",
        ),
    )


def render_next_target(target: NextTarget) -> str:
    lines = [
        "# Next Re-Opt Target",
        "",
        f"title: {target.title}",
        "",
        f"rationale: {target.rationale}",
        "",
        "Evidence:",
        "",
    ]
    for item in target.evidence:
        lines.append(f"- {item}")
    lines.extend(["", "Suggested commands:", ""])
    for command in target.suggested_commands:
        lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def _last_next_refinement(log_text: str) -> str:
    marker = "### Next Refinement"
    start = log_text.rfind(marker)
    if start == -1:
        return "No next refinement found."
    tail = log_text[start + len(marker) :].strip()
    next_heading = tail.find("\n## ")
    if next_heading != -1:
        tail = tail[:next_heading].strip()
    return " ".join(line.strip() for line in tail.splitlines() if line.strip())


def _reports_by_status(index_text: str, status: str) -> tuple[tuple[str, str], ...]:
    reports: list[tuple[str, str]] = []
    status_cell = f" | {status} | "
    for line in index_text.splitlines():
        if line.startswith("| ") and status_cell in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 3:
                reports.append((cells[0], cells[2]))
    return tuple(reports)


def _portable_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest the next Re-Opt refinement target.")
    parser.add_argument(
        "--iteration-log",
        type=Path,
        default=Path("docs/iteration-log.md"),
        help="Iteration log Markdown path.",
    )
    parser.add_argument(
        "--adoption-index",
        type=Path,
        default=Path("docs/adoption-index.md"),
        help="Adoption index Markdown path.",
    )
    parser.add_argument("--write", type=Path, help="Write the suggestion to a Markdown file.")
    args = parser.parse_args()
    rendered = render_next_target(suggest_next_target(args.iteration_log, args.adoption_index))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
