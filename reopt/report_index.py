"""Index Re-Opt adoption reports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AdoptionReportSummary:
    path: Path
    status: str
    weights: str
    baseline: str


def summarize_adoption_report(path: Path) -> AdoptionReportSummary:
    status = "unknown"
    weights = ""
    baseline = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status: "):
            status = line.removeprefix("status: ").strip()
        elif line.startswith("weights: "):
            weights = line.removeprefix("weights: ").strip()
        elif line.startswith("baseline: "):
            baseline = line.removeprefix("baseline: ").strip()
    return AdoptionReportSummary(
        path=path,
        status=status,
        weights=weights,
        baseline=baseline,
    )


def render_adoption_index(report_dir: Path) -> str:
    reports = sorted(report_dir.glob("*.md"))
    lines = [
        "# Adoption Report Index",
        "",
        "This index summarizes proposed utility-weight adoption reviews.",
        "",
        "| Report | Status | Weights | Baseline |",
        "| --- | --- | --- | --- |",
    ]
    if not reports:
        lines.append("| _none_ |  |  |  |")
    for report in reports:
        summary = summarize_adoption_report(report)
        lines.append(
            f"| {summary.path.as_posix()} | {summary.status} | "
            f"{summary.weights} | {summary.baseline} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an adoption report index.")
    parser.add_argument(
        "--reports",
        type=Path,
        default=Path("adoption-reports"),
        help="Directory containing adoption report Markdown files.",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write the rendered index to a Markdown file.",
    )
    args = parser.parse_args()
    rendered = render_adoption_index(args.reports)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
