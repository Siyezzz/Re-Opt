"""Decide whether a clean capped proposal is meaningful enough to adopt."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from .adopt import adoption_checklist


@dataclass(frozen=True)
class AdoptionDecision:
    decision: str
    weights_path: Path
    cap_review_path: Path
    evidence_review_path: Path
    cap_ratio: float | None
    status: str
    evidence_source: str
    all_rounded_deltas_zero: bool
    rationale: tuple[str, ...]


def decide_adoption(
    weights_path: Path = Path("weights/proposed-capped-expanded-evidence.json"),
    cap_review_path: Path = Path("docs/weight-caps/expanded-evidence.md"),
    evidence_review_path: Path = Path("docs/outcome-evidence/simulated-next-outcome.md"),
    baseline_path: Path = Path("benchmark-results/seed-baseline.json"),
) -> AdoptionDecision:
    checklist = adoption_checklist(weights_path, baseline_path)
    cap_text = cap_review_path.read_text(encoding="utf-8") if cap_review_path.exists() else ""
    evidence_text = (
        evidence_review_path.read_text(encoding="utf-8")
        if evidence_review_path.exists()
        else ""
    )
    cap_ratio = _extract_cap_ratio(cap_text)
    status = _extract_status(checklist)
    evidence_source = _extract_evidence_source(evidence_text)
    all_rounded_deltas_zero = _all_rounded_deltas_zero(checklist)

    if (
        status == "clean"
        and cap_ratio is not None
        and cap_ratio < 0.05
        and all_rounded_deltas_zero
        and evidence_source == "synthetic simulation"
    ):
        decision = "defer"
        rationale = (
            "The proposal is regression-clean, but the largest clean cap is below the review threshold.",
            "Every seed utility delta rounds to +0.000, so the change has no visible benchmark effect.",
            "The supporting outcome is synthetic, so this should wait for observed task evidence.",
        )
    elif status == "clean":
        decision = "candidate_for_adoption"
        rationale = (
            "The proposal is regression-clean and has enough signal to review for adoption.",
        )
    else:
        decision = "blocked"
        rationale = (
            "The proposal is not regression-clean and should not be adopted.",
        )

    return AdoptionDecision(
        decision=decision,
        weights_path=weights_path,
        cap_review_path=cap_review_path,
        evidence_review_path=evidence_review_path,
        cap_ratio=cap_ratio,
        status=status,
        evidence_source=evidence_source,
        all_rounded_deltas_zero=all_rounded_deltas_zero,
        rationale=rationale,
    )


def render_decision(decision: AdoptionDecision) -> str:
    cap_ratio = "unknown" if decision.cap_ratio is None else f"{decision.cap_ratio:.3f}"
    lines = [
        "# Capped Proposal Adoption Decision",
        "",
        f"weights: {decision.weights_path.as_posix()}",
        f"cap_review: {decision.cap_review_path.as_posix()}",
        f"evidence_review: {decision.evidence_review_path.as_posix()}",
        f"decision: {decision.decision}",
        "",
        "Decision signals:",
        "",
        f"- adoption_status: {decision.status}",
        f"- largest_clean_ratio: {cap_ratio}",
        f"- evidence_source: {decision.evidence_source}",
        f"- all_rounded_utility_deltas_zero: {decision.all_rounded_deltas_zero}",
        "",
        "Rationale:",
        "",
    ]
    for item in decision.rationale:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _extract_cap_ratio(text: str) -> float | None:
    match = re.search(r"^largest_clean_ratio:\s*([0-9.]+)\s*$", text, re.MULTILINE)
    if not match:
        return None
    return float(match.group(1))


def _extract_status(text: str) -> str:
    match = re.search(r"^status:\s*(\w+)\s*$", text, re.MULTILINE)
    if not match:
        return "unknown"
    return match.group(1)


def _extract_evidence_source(text: str) -> str:
    match = re.search(r"^source:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return "unknown"
    return match.group(1)


def _all_rounded_deltas_zero(text: str) -> bool:
    deltas = re.findall(r"utility_delta:\s*([+-]\d+\.\d+)", text)
    return bool(deltas) and all(float(delta) == 0 for delta in deltas)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decide whether a capped utility-weight proposal should be adopted."
    )
    parser.add_argument(
        "weights",
        nargs="?",
        type=Path,
        default=Path("weights/proposed-capped-expanded-evidence.json"),
        help="Capped proposed weights JSON path.",
    )
    parser.add_argument(
        "--cap-review",
        type=Path,
        default=Path("docs/weight-caps/expanded-evidence.md"),
        help="Increment cap review Markdown path.",
    )
    parser.add_argument(
        "--evidence-review",
        type=Path,
        default=Path("docs/outcome-evidence/simulated-next-outcome.md"),
        help="Evidence review Markdown path.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("benchmark-results/seed-baseline.json"),
        help="Baseline export path.",
    )
    parser.add_argument("--write-report", type=Path, help="Write the decision to Markdown.")
    args = parser.parse_args()

    rendered = render_decision(
        decide_adoption(args.weights, args.cap_review, args.evidence_review, args.baseline)
    )
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
