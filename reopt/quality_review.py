"""Score observed outcome quality from an explicit rubric."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QualityCriterion:
    name: str
    score: float
    weight: float = 1.0
    evidence: str = ""


@dataclass(frozen=True)
class QualityReview:
    graph_id: str
    strategy: str
    target_quality: float
    criteria: tuple[QualityCriterion, ...]
    evidence_ref: str


def load_quality_review(path: Path) -> QualityReview:
    data = json.loads(path.read_text(encoding="utf-8"))
    return QualityReview(
        graph_id=data["graph_id"],
        strategy=data["strategy"],
        target_quality=float(data["target_quality"]),
        criteria=tuple(
            QualityCriterion(
                name=item["name"],
                score=float(item["score"]),
                weight=float(item.get("weight", 1.0)),
                evidence=item.get("evidence", ""),
            )
            for item in data["criteria"]
        ),
        evidence_ref=data.get("evidence_ref", ""),
    )


def observed_quality(review: QualityReview) -> float:
    total_weight = sum(item.weight for item in review.criteria)
    if total_weight <= 0:
        return 0.0
    return round(
        sum(item.score * item.weight for item in review.criteria) / total_weight,
        4,
    )


def quality_review_failures(review: QualityReview) -> tuple[str, ...]:
    failures: list[str] = []
    if not review.criteria:
        failures.append("quality review must include at least one criterion")
    if not 0 < review.target_quality <= 1:
        failures.append("target_quality must be in (0, 1]")
    if not review.evidence_ref.strip():
        failures.append("evidence_ref must point to the reviewed run or artifact")
    for index, item in enumerate(review.criteria, start=1):
        prefix = f"criterion {index} ({item.name})"
        if not item.name.strip():
            failures.append(f"{prefix}: name is required")
        if not 0 <= item.score <= 1:
            failures.append(f"{prefix}: score must be in [0, 1]")
        if item.weight <= 0:
            failures.append(f"{prefix}: weight must be greater than 0")
        if not item.evidence.strip():
            failures.append(f"{prefix}: evidence is required")
    return tuple(failures)


def render_quality_review(review: QualityReview) -> str:
    quality = observed_quality(review)
    failures = quality_review_failures(review)
    lines = [
        "# Quality Review",
        "",
        f"status: {'clean' if not failures else 'blocked'}",
        f"graph_id: {review.graph_id}",
        f"strategy: {review.strategy}",
        f"observed_quality: {quality}",
        f"target_quality: {review.target_quality}",
        f"evidence_ref: {review.evidence_ref}",
        "",
        "| Criterion | Weight | Score | Evidence |",
        "| --- | ---: | ---: | --- |",
    ]
    for item in review.criteria:
        lines.append(
            f"| {item.name} | {item.weight:.3f} | {item.score:.3f} | {item.evidence} |"
        )
    if failures:
        lines.extend(["", "Failures:", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an observed outcome quality rubric.")
    parser.add_argument("review", type=Path, help="Quality review JSON file.")
    parser.add_argument("--write-report", type=Path, help="Write quality review Markdown.")
    args = parser.parse_args()

    review = load_quality_review(args.review)
    report = render_quality_review(review)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(report, encoding="utf-8")
    print(report)
    raise SystemExit(1 if quality_review_failures(review) else 0)


if __name__ == "__main__":
    main()
