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
    evidence_review: Path = Path("docs/outcome-evidence/simulated-next-outcome.md"),
    cap_review: Path = Path("docs/weight-caps/expanded-evidence.md"),
    decision_report: Path = Path("docs/adoption-decisions/capped-expanded-evidence.md"),
    observed_review: Path = Path("docs/outcome-evidence/observed-next-outcome.md"),
    consumption_audit: Path = Path("docs/outcome-consumption/proposed-observed-quality.md"),
    consumption_aware_review: Path = Path("docs/outcome-evidence/observed-consumption-aware.md"),
    consumption_aware_cap: Path = Path("docs/weight-caps/consumption-aware.md"),
) -> NextTarget:
    log_text = iteration_log.read_text(encoding="utf-8")
    index_text = adoption_index.read_text(encoding="utf-8")
    latest_refinement = _last_next_refinement(log_text)
    blocked_reports = _reports_by_status(index_text, "blocked")
    clean_reports = _reports_by_status(index_text, "clean")
    adopted_reports = _reports_by_status(index_text, "adopted")

    if (
        blocked_reports
        and _expects_consumption_aware_review(latest_refinement)
        and _consumption_aware_cap_zero(consumption_aware_cap)
    ):
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Collect unconsumed cost and optional-harm evidence",
            rationale=(
                "Consumption-aware calibration removes the already-consumed quality "
                "signal, and the remaining token, minute, and missed-optional "
                "increments have no clean cap. The next optimization should gather "
                "fresh unconsumed evidence for those non-quality signals before "
                "changing cost weights."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"consumption_aware_cap={consumption_aware_cap.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for token --require-evidence-ref",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for minute --require-evidence-ref",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for missed_optional --require-evidence-ref",
                "python -m reopt.regression --check",
            ),
        )

    if (
        blocked_reports
        and _expects_consumption_aware_review(latest_refinement)
        and _consumption_aware_review_blocked(consumption_aware_review)
    ):
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Split consumption-aware blocked cost increments",
            rationale=(
                "Consumption-aware calibration excludes the already-used quality "
                "signal, but the remaining token, minute, and missed-optional "
                "increments are still blocked. The next optimization should split "
                "or cap those remaining non-quality increments."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"consumption_aware_review={consumption_aware_review.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.explain_adoption weights/proposed-observed-consumption-aware.json",
                "python -m reopt.increment_cap weights/proposed-observed-consumption-aware.json --write-weights weights/proposed-capped-consumption-aware.json --write-report docs/weight-caps/consumption-aware.md",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports and clean_reports and _consumption_audit_blocked(consumption_audit):
        clean_report_paths = tuple(report for report, _weights in clean_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Collect unconsumed outcome evidence before quality adoption",
            rationale=(
                "A clean observed-quality proposal exists, but the consumption "
                "audit shows its supporting quality signal has already been used "
                "for an earlier adoption. The next optimization should gather "
                "new unconsumed quality evidence before raising the quality weight again."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"clean_reports={', '.join(clean_report_paths)}",
                f"consumption_audit={consumption_audit.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json --require-unconsumed-for quality --require-evidence-ref",
                "python -m reopt.outcome_consumption weights/proposed-observed-quality.json --write-report docs/outcome-consumption/proposed-observed-quality.md",
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

    if blocked_reports and adopted_reports and _observed_review_blocked(observed_review):
        adopted_report_paths = tuple(report for report, _weights in adopted_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Split observed-backed blocked weight increments",
            rationale=(
                "A fresh observed outcome has been collected and validated, but "
                "the combined observed-evidence weight proposal is still blocked. "
                "The next optimization should split the observed-backed increments "
                "before any adoption attempt."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"adopted_reports={', '.join(adopted_report_paths)}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"observed_review={observed_review.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.explain_adoption weights/proposed-observed-evidence.json",
                "python -m reopt.increment_cap weights/proposed-observed-evidence.json --write-weights weights/proposed-capped-observed-evidence.json --write-report docs/weight-caps/observed-evidence.md",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports and adopted_reports and _decision_deferred(decision_report):
        adopted_report_paths = tuple(report for report, _weights in adopted_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Collect observed evidence before adopting capped increments",
            rationale=(
                "The capped expanded-evidence proposal is clean but too small to "
                "show a benchmark effect, and its supporting evidence is synthetic. "
                "The next optimization should collect observed task evidence before "
                "changing default utility weights again."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"adopted_reports={', '.join(adopted_report_paths)}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"decision_report={decision_report.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json",
                "python -m reopt.calibrate outcomes/next-outcome.json",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports and adopted_reports and _cap_review_clean(cap_review):
        adopted_report_paths = tuple(report for report, _weights in adopted_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Review the capped expanded-evidence proposal",
            rationale=(
                "The remaining blocked increments now have a capped clean proposal. "
                "The next optimization should decide whether this tiny reversible "
                "step is meaningful enough to adopt or should wait for observed evidence."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"adopted_reports={', '.join(adopted_report_paths)}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"cap_review={cap_review.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.adopt weights/proposed-capped-expanded-evidence.json",
                "python -m reopt.regression --check",
            ),
        )

    if blocked_reports and adopted_reports and _synthetic_review_blocked(evidence_review):
        adopted_report_paths = tuple(report for report, _weights in adopted_reports)
        blocked_report_paths = tuple(report for report, _weights in blocked_reports)
        return NextTarget(
            title="Split remaining blocked weight increments",
            rationale=(
                "A validation-clean synthetic outcome still leaves the expanded "
                "evidence proposal blocked. The next optimization should split or "
                "cap the remaining token, minute, and missed-optional increments "
                "before any adoption attempt."
            ),
            evidence=(
                f"latest_next_refinement={latest_refinement}",
                f"adopted_reports={', '.join(adopted_report_paths)}",
                f"blocked_reports={', '.join(blocked_report_paths)}",
                f"evidence_review={evidence_review.as_posix()}",
            ),
            suggested_commands=(
                "python -m reopt.evidence_review --write-simulated --candidate outcomes/simulated-next-outcome.json --write-weights weights/proposed-expanded-evidence.json --write-report docs/outcome-evidence/simulated-next-outcome.md",
                "python -m reopt.explain_adoption weights/proposed-expanded-evidence.json",
                "python -m reopt.regression --check",
            ),
        )

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
                "python -m reopt.outcome_intake --write docs/outcome-intake/next-outcome.md",
                "python -m reopt.outcome_intake --validate outcomes/next-outcome.json",
                "python -m reopt.explain_adoption weights/proposed-seed.json",
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


def _synthetic_review_blocked(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "source: synthetic simulation" in text and "status: blocked" in text


def _cap_review_clean(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "largest_clean_ratio:" in text and "status: clean" in text


def _decision_deferred(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "decision: defer" in text


def _observed_review_blocked(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "source: observed task run" in text and "status: blocked" in text


def _consumption_audit_blocked(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "status: blocked" in text


def _consumption_aware_review_blocked(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return (
        "proposed_weights: weights/proposed-observed-consumption-aware.json" in text
        and "status: blocked" in text
    )


def _consumption_aware_cap_zero(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "largest_clean_ratio: 0.000" in text


def _expects_consumption_aware_review(latest_refinement: str) -> bool:
    return (
        "consumed signals are excluded" in latest_refinement
        or "Fill `outcomes/next-outcome.json`" in latest_refinement
        or "missed-optional" in latest_refinement
        or "reopt.observed_run" in latest_refinement
        or "goal-delta.json" in latest_refinement
        or "consumption-aware evidence review" in latest_refinement
    )


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
    parser.add_argument(
        "--evidence-review",
        type=Path,
        default=Path("docs/outcome-evidence/simulated-next-outcome.md"),
        help="Expanded evidence review Markdown path.",
    )
    parser.add_argument(
        "--cap-review",
        type=Path,
        default=Path("docs/weight-caps/expanded-evidence.md"),
        help="Increment cap review Markdown path.",
    )
    parser.add_argument(
        "--decision-report",
        type=Path,
        default=Path("docs/adoption-decisions/capped-expanded-evidence.md"),
        help="Capped proposal adoption decision Markdown path.",
    )
    parser.add_argument(
        "--observed-review",
        type=Path,
        default=Path("docs/outcome-evidence/observed-next-outcome.md"),
        help="Observed outcome evidence review Markdown path.",
    )
    parser.add_argument(
        "--consumption-audit",
        type=Path,
        default=Path("docs/outcome-consumption/proposed-observed-quality.md"),
        help="Outcome-consumption audit Markdown path.",
    )
    parser.add_argument(
        "--consumption-aware-review",
        type=Path,
        default=Path("docs/outcome-evidence/observed-consumption-aware.md"),
        help="Consumption-aware observed evidence review Markdown path.",
    )
    parser.add_argument(
        "--consumption-aware-cap",
        type=Path,
        default=Path("docs/weight-caps/consumption-aware.md"),
        help="Consumption-aware cap review Markdown path.",
    )
    parser.add_argument("--write", type=Path, help="Write the suggestion to a Markdown file.")
    args = parser.parse_args()
    rendered = render_next_target(
        suggest_next_target(
            args.iteration_log,
            args.adoption_index,
            args.evidence_review,
            args.cap_review,
            args.decision_report,
            args.observed_review,
            args.consumption_audit,
            args.consumption_aware_review,
            args.consumption_aware_cap,
        )
    )
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
